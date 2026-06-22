"""graph.py — LangGraph lesson-generation workflow with stateful memory.

Replaces the single LangChain chain that used to live in core.generate_lesson()
with a multi-node graph that threads a shared ``LessonState`` through:

    planner -> part1 -> part2 -> part3 -> summary -> evaluation
            -> (revision -> evaluation)*  -> export

Design notes
------------
* Each node updates the shared state and returns only the keys it changed.
* Later nodes are fed **summaries** (engage/pre-explore/explain summaries) rather
  than full text, to keep prompts small and focused.
* planner / part1 / part2 / part3 / evaluation each run inside their own Phoenix
  span; the LLM calls nested under them are auto-traced by OpenInference.
* The revision node regenerates only the failing section (readability / vocab /
  NGSS) instead of the whole lesson, up to MAX_REVISIONS times.
* ChromaDB memory (memory.py) is optional — calls degrade to no-ops if absent.

Two compiled graphs are exposed:
* generation graph  (planner..summary)  -> generate_content(): text only, used
  for backward-compatible core.generate_lesson().
* full graph        (..export)          -> run_lesson_graph(): generate, evaluate,
  revise and export end-to-end.
"""

from __future__ import annotations

import contextlib
import os
import re
from typing import TypedDict

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, StateGraph

import core
import evals
import memory

MAX_REVISIONS = int(os.environ.get("MAX_REVISIONS", "1"))

# Tracer provider captured once per process so the evaluation node can log scores.
_TRACER_PROVIDER = None


# --------------------------------------------------------------------------- #
# State
# --------------------------------------------------------------------------- #
class LessonState(TypedDict, total=False):
    lesson: dict

    big_idea: str
    essential_questions: list[str]
    vocabulary_terms: list[str]
    smart_objectives: list[str]

    engage_activity: str
    pre_explore_summary: str

    explain_content: str

    assessment_content: str
    extend_content: str

    lesson_summary: str

    final_lesson_content: str

    evaluation_results: dict

    # internal bookkeeping (not part of the lesson, kept on the state for routing)
    provider: str
    run_eval: bool
    revision_count: int
    export_path: str


# --------------------------------------------------------------------------- #
# Tracing helpers — one span per major node
# --------------------------------------------------------------------------- #
def _ensure_tracing():
    """Set up Phoenix tracing once and cache the tracer provider."""
    global _TRACER_PROVIDER
    if _TRACER_PROVIDER is None:
        _TRACER_PROVIDER = core.setup_tracing()
    return _TRACER_PROVIDER


@contextlib.contextmanager
def _span(name: str, kind: str = "CHAIN"):
    """Open a named span if tracing is active; otherwise a no-op context."""
    try:
        from opentelemetry import trace

        tracer = trace.get_tracer("alphachem.graph")
    except Exception:
        tracer = None
    if tracer is None:
        yield None
        return
    with tracer.start_as_current_span(name) as span:
        span.set_attribute("openinference.span.kind", kind)
        yield span


# --------------------------------------------------------------------------- #
# LLM helpers
# --------------------------------------------------------------------------- #
GEN_SYSTEM = (
    "You are a chemistry textbook writer for ages 14-15 (USA school grade 9). "
    "Write clearly and simply, targeting a Flesch Reading Ease of 70 or higher. "
    "Make the writing feel human-authored and tie every concept to the lesson's "
    "real-world phenomenon and storyline."
)

PLANNER_SYSTEM = (
    "You are an NGSS instructional designer. You produce a concise lesson-planning "
    "skeleton and respond using only the exact labeled format requested."
)


def _llm(state: LessonState):
    return core.build_llm(state.get("provider"))


def _run(llm, system: str, human: str, variables: dict) -> str:
    chain = ChatPromptTemplate.from_messages(
        [("system", system), ("human", human)]
    ) | llm | StrOutputParser()
    return chain.invoke(variables)


def _summarize(llm, text: str, words: int = 300) -> str:
    """Produce a compact structured summary used as context for later nodes."""
    if not text:
        return ""
    system = "You summarize chemistry lesson sections faithfully and concisely."
    human = (
        f"Summarize the section below in about {words} words as short bullet points. "
        "Preserve the key concepts, vocabulary, worked examples and storyline.\n\n"
        "SECTION:\n{text}"
    )
    return _run(llm, system, human, {"text": text})


def _extract_block(text: str, label: str) -> str:
    """Pull the text under an ALLCAPS label up to the next label (robust to local LLMs)."""
    pattern = rf"{label}\s*:?\s*(.*?)(?=\n[A-Z][A-Z_ ]{{2,}}:|\Z)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""


def _to_list(block: str) -> list[str]:
    items = []
    for line in block.splitlines():
        cleaned = line.strip().lstrip("-*•").strip()
        cleaned = re.sub(r"^\d+[.)]\s*", "", cleaned).strip()
        if cleaned:
            items.append(cleaned)
    return items


def _join(items, bullet: str = "- ") -> str:
    if isinstance(items, str):
        return items
    return "\n".join(f"{bullet}{i}" for i in (items or []))


# --------------------------------------------------------------------------- #
# Prompt templates
# --------------------------------------------------------------------------- #
PLANNER_HUMAN = """Create the planning skeleton for the lesson "{lesson_name}" in Chapter "{chapter_name}", Unit "{unit_name}".

Lesson objective:
{lesson_objective}

Suggested vocabulary:
{lesson_vocabulary}

Essential question:
{essential_question}

Context from earlier lessons (may be empty):
{prior_context}

Respond EXACTLY in this labeled format and nothing else:

BIG_IDEA: <one sentence>
ESSENTIAL_QUESTIONS:
- <question>
- <question>
VOCABULARY:
- <term>
- <term>
SMART_OBJECTIVES:
- <measurable objective>
- <measurable objective>
"""

PART1_HUMAN = """For the lesson "{lesson_name}" (Unit "{unit_name}", Chapter "{chapter_name}"), write the opening sections, grounded in this phenomenon:
{phenomenon}

Big Idea: {big_idea}
Essential Questions:
{essential_questions}

Respond EXACTLY in this labeled format and nothing else:

ENGAGE: <a phenomenon-based hook with one short hands-on experiment (step-by-step) and 2-3 follow-up questions>
PRE_EXPLORE: <about 200 words of direct-instruction background that links the phenomenon to the key concepts>
"""

PART2_HUMAN = """Write the EXPLAIN (Lightbulb) section for the lesson "{lesson_name}".
Aim for comprehensive, simple core content (1500+ words, Flesch >= 70) tied to the storyline.

Use this context:
- Big Idea: {big_idea}
- Essential Questions:
{essential_questions}
- Vocabulary to define and use: {vocabulary_terms}
- SMART Objectives:
{smart_objectives}
- Engage activity (summary): {engage_activity}
- Pre-Explore (summary): {pre_explore_summary}

Requirements:
- Define and use every vocabulary term listed above.
- For each main concept, include one solved example, then one practice question.
- Keep sentences short and the language accessible for 14-15 year olds.
"""

PART3_HUMAN = """Write the closing sections for the lesson "{lesson_name}".

Context (summaries only):
- Engage: {engage_activity}
- Pre-Explore: {pre_explore_summary}
- Explain (summary): {explain_summary}
- Vocabulary: {vocabulary_terms}
- Performance Expectations: {performance_expectations}
- Disciplinary Core Ideas: {disciplinary_core_ideas}

Respond EXACTLY in this labeled format and nothing else:

ASSESSMENT: <Evaluate: 3 scaffolded questions (DOK 1-3) with answers. Elaborate: mini-tasks / open-ended questions. Final Evaluation: 1 debate question plus 8 assessment questions = 4 MCQs (with options and correct answers) and 4 long-answer questions (with answers).>
EXTEND: <Beyond-the-lesson tasks, readings and spaced-practice opportunities.>
"""

REVISION_HUMAN = """Rewrite ONLY the EXPLAIN section for the lesson "{lesson_name}" to fix these problems:
{fix_instructions}

Keep it aligned to:
- Big Idea: {big_idea}
- Vocabulary to define and use: {vocabulary_terms}
- Performance Expectations: {performance_expectations}
- Disciplinary Core Ideas: {disciplinary_core_ideas}

Write the improved EXPLAIN section as plain prose (no labels).
"""


# --------------------------------------------------------------------------- #
# Assembly
# --------------------------------------------------------------------------- #
def _assemble(state: LessonState) -> str:
    """Build the full lesson markdown from the per-section state fields."""
    lesson = state["lesson"]
    parts = [
        f"# {lesson.get('lesson_name', '')}",
        f"## {lesson.get('unit_name', '')} — {lesson.get('chapter_name', '')}",
        "\n### Big Idea\n" + state.get("big_idea", ""),
        "\n### Essential Questions\n" + _join(state.get("essential_questions", [])),
        "\n### Vocabulary\n" + _join(state.get("vocabulary_terms", [])),
        "\n### SMART Objectives\n" + _join(state.get("smart_objectives", [])),
        "\n### Engage (Ignite)\n" + state.get("engage_activity", ""),
        "\n### Pre-Explore\n" + state.get("pre_explore_summary", ""),
        "\n### Explain (Lightbulb)\n" + state.get("explain_content", ""),
        "\n### Evaluate / Elaborate / Final Evaluation\n" + state.get("assessment_content", ""),
        "\n### Extend (Beyond the Lesson)\n" + state.get("extend_content", ""),
    ]
    return "\n".join(parts)


# --------------------------------------------------------------------------- #
# Nodes
# --------------------------------------------------------------------------- #
def planner_node(state: LessonState) -> dict:
    """Extract Big Idea, Essential Questions, Vocabulary and SMART Objectives."""
    lesson, llm = state["lesson"], _llm(state)
    with _span("planner"):
        prior_context = memory.retrieve_previous_chapter_context(lesson)
        related = memory.retrieve_related_lessons(lesson.get("essential_question", ""), 2)
        prior_blob = "\n".join(
            [prior_context] + [r.get("summary", "") for r in related]
        ).strip() or "(none)"

        raw = _run(llm, PLANNER_SYSTEM, PLANNER_HUMAN, {
            "lesson_name": lesson.get("lesson_name", ""),
            "chapter_name": lesson.get("chapter_name", ""),
            "unit_name": lesson.get("unit_name", ""),
            "lesson_objective": lesson.get("lesson_objective", ""),
            "lesson_vocabulary": lesson.get("lesson_vocabulary", ""),
            "essential_question": lesson.get("essential_question", ""),
            "prior_context": prior_blob,
        })

    return {
        "big_idea": _extract_block(raw, "BIG_IDEA") or lesson.get("lesson_name", ""),
        "essential_questions": (_to_list(_extract_block(raw, "ESSENTIAL_QUESTIONS"))
                                or [lesson.get("essential_question", "")]),
        "vocabulary_terms": (_to_list(_extract_block(raw, "VOCABULARY"))
                             or _to_list(lesson.get("lesson_vocabulary", ""))),
        "smart_objectives": (_to_list(_extract_block(raw, "SMART_OBJECTIVES"))
                             or _to_list(lesson.get("lesson_objective", ""))),
    }


def part1_node(state: LessonState) -> dict:
    """Generate Phenomenon-grounded Engage + Pre-Explore; store their summaries."""
    lesson, llm = state["lesson"], _llm(state)
    with _span("part1"):
        raw = _run(llm, GEN_SYSTEM, PART1_HUMAN, {
            "lesson_name": lesson.get("lesson_name", ""),
            "unit_name": lesson.get("unit_name", ""),
            "chapter_name": lesson.get("chapter_name", ""),
            "phenomenon": lesson.get("phenomenon", ""),
            "big_idea": state.get("big_idea", ""),
            "essential_questions": _join(state.get("essential_questions", [])),
        })
        engage = _extract_block(raw, "ENGAGE")
        pre_explore = _extract_block(raw, "PRE_EXPLORE")
    return {"engage_activity": engage, "pre_explore_summary": pre_explore}


def part2_node(state: LessonState) -> dict:
    """Generate the Explain section using planner + part1 context (summaries)."""
    lesson, llm = state["lesson"], _llm(state)
    with _span("part2"):
        explain = _run(llm, GEN_SYSTEM, PART2_HUMAN, {
            "lesson_name": lesson.get("lesson_name", ""),
            "big_idea": state.get("big_idea", ""),
            "essential_questions": _join(state.get("essential_questions", [])),
            "vocabulary_terms": ", ".join(state.get("vocabulary_terms", [])),
            "smart_objectives": _join(state.get("smart_objectives", [])),
            "engage_activity": state.get("engage_activity", ""),
            "pre_explore_summary": state.get("pre_explore_summary", ""),
        })
    return {"explain_content": explain}


def part3_node(state: LessonState) -> dict:
    """Generate Evaluate/Elaborate/Final Evaluation + Extend from part1+part2 context."""
    lesson, llm = state["lesson"], _llm(state)
    with _span("part3"):
        explain_summary = _summarize(llm, state.get("explain_content", ""), words=200)
        raw = _run(llm, GEN_SYSTEM, PART3_HUMAN, {
            "lesson_name": lesson.get("lesson_name", ""),
            "engage_activity": state.get("engage_activity", ""),
            "pre_explore_summary": state.get("pre_explore_summary", ""),
            "explain_summary": explain_summary,
            "vocabulary_terms": ", ".join(state.get("vocabulary_terms", [])),
            "performance_expectations": lesson.get("performance_expectations", ""),
            "disciplinary_core_ideas": lesson.get("disciplinary_core_ideas", ""),
        })
        assessment = _extract_block(raw, "ASSESSMENT")
        extend = _extract_block(raw, "EXTEND")
    return {"assessment_content": assessment, "extend_content": extend}


def lesson_summary_node(state: LessonState) -> dict:
    """Assemble the full lesson and produce a 300-word structured summary."""
    llm = _llm(state)
    final_content = _assemble(state)
    summary = _summarize(llm, final_content, words=300)
    return {"final_lesson_content": final_content, "lesson_summary": summary}


def evaluation_node(state: LessonState) -> dict:
    """Run the full evals pipeline; store results in state and log scores to Phoenix."""
    if not state.get("run_eval", True):
        return {"evaluation_results": {}}
    lesson = state["lesson"]
    content = state.get("final_lesson_content") or _assemble(state)
    with _span("evaluation", kind="EVALUATOR") as span:
        results = evals.evaluate_lesson(
            content, lesson, use_llm=True, provider=state.get("provider")
        )
        if span is not None and _TRACER_PROVIDER is not None:
            try:
                span_id = format(span.get_span_context().span_id, "016x")
                evals.log_scores_to_phoenix(span_id, results, _TRACER_PROVIDER)
            except Exception as exc:  # logging must never break the run
                print(f"[graph] score logging skipped: {type(exc).__name__}: {exc}")
    return {"evaluation_results": results}


def revision_node(state: LessonState) -> dict:
    """Regenerate ONLY the Explain section to fix failing metrics, then reassemble."""
    lesson, llm = state["lesson"], _llm(state)
    results = state.get("evaluation_results", {})
    fixes = []
    if not results.get("readability", {}).get("passed", True):
        fixes.append("- Use shorter sentences and simpler everyday words to raise the "
                     "Flesch Reading Ease to 70 or above.")
    if not results.get("vocabulary", {}).get("passed", True):
        missing = results.get("vocabulary", {}).get("missing", [])
        fixes.append("- Explicitly define and use these missing vocabulary terms: "
                     + ", ".join(missing) + ".")
    if not results.get("ngss", {}).get("passed", True):
        fixes.append("- Strengthen coverage of the Performance Expectations and "
                     "Disciplinary Core Ideas listed below.")

    with _span("revision"):
        new_explain = _run(llm, GEN_SYSTEM, REVISION_HUMAN, {
            "lesson_name": lesson.get("lesson_name", ""),
            "fix_instructions": "\n".join(fixes) or "- Improve overall clarity.",
            "big_idea": state.get("big_idea", ""),
            "vocabulary_terms": ", ".join(state.get("vocabulary_terms", [])),
            "performance_expectations": lesson.get("performance_expectations", ""),
            "disciplinary_core_ideas": lesson.get("disciplinary_core_ideas", ""),
        })

    merged = {**state, "explain_content": new_explain}
    return {
        "explain_content": new_explain,
        "final_lesson_content": _assemble(merged),
        "revision_count": state.get("revision_count", 0) + 1,
    }


def export_node(state: LessonState) -> dict:
    """Save the final lesson to a versioned .docx and store it in memory."""
    lesson = state["lesson"]
    path = core.save_lesson_to_docx(
        lesson["unit_name"], lesson["chapter_name"], lesson["lesson_name"],
        state["final_lesson_content"],
    )
    memory.save_lesson_memory(
        lesson, state["final_lesson_content"],
        summary=state.get("lesson_summary", ""),
        evaluation=state.get("evaluation_results", {}),
    )
    return {"export_path": path}


# --------------------------------------------------------------------------- #
# Routing
# --------------------------------------------------------------------------- #
def _route_after_eval(state: LessonState) -> str:
    """Revise the failing section, or export, based on the eval results."""
    if state.get("revision_count", 0) >= MAX_REVISIONS:
        return "export"
    results = state.get("evaluation_results", {})
    failing = (
        not results.get("readability", {}).get("passed", True)
        or not results.get("vocabulary", {}).get("passed", True)
        or not results.get("ngss", {}).get("passed", True)
    )
    return "revise" if failing else "export"


# --------------------------------------------------------------------------- #
# Graph construction (compiled once, reused)
# --------------------------------------------------------------------------- #
def build_generation_graph():
    """planner -> part1 -> part2 -> part3 -> summary -> END (text only)."""
    g = StateGraph(LessonState)
    g.add_node("planner", planner_node)
    g.add_node("part1", part1_node)
    g.add_node("part2", part2_node)
    g.add_node("part3", part3_node)
    g.add_node("summary", lesson_summary_node)
    g.set_entry_point("planner")
    g.add_edge("planner", "part1")
    g.add_edge("part1", "part2")
    g.add_edge("part2", "part3")
    g.add_edge("part3", "summary")
    g.add_edge("summary", END)
    return g.compile()


def build_full_graph():
    """Generation + evaluation + conditional revision + export."""
    g = StateGraph(LessonState)
    g.add_node("planner", planner_node)
    g.add_node("part1", part1_node)
    g.add_node("part2", part2_node)
    g.add_node("part3", part3_node)
    g.add_node("summary", lesson_summary_node)
    g.add_node("evaluation", evaluation_node)
    g.add_node("revision", revision_node)
    g.add_node("export", export_node)
    g.set_entry_point("planner")
    g.add_edge("planner", "part1")
    g.add_edge("part1", "part2")
    g.add_edge("part2", "part3")
    g.add_edge("part3", "summary")
    g.add_edge("summary", "evaluation")
    g.add_conditional_edges("evaluation", _route_after_eval,
                            {"revise": "revision", "export": "export"})
    g.add_edge("revision", "evaluation")
    g.add_edge("export", END)
    return g.compile()


_GEN_GRAPH = None
_FULL_GRAPH = None


def _gen_graph():
    global _GEN_GRAPH
    if _GEN_GRAPH is None:
        _GEN_GRAPH = build_generation_graph()
    return _GEN_GRAPH


def _full_graph():
    global _FULL_GRAPH
    if _FULL_GRAPH is None:
        _FULL_GRAPH = build_full_graph()
    return _FULL_GRAPH


# --------------------------------------------------------------------------- #
# Public entry points
# --------------------------------------------------------------------------- #
def generate_content(lesson: dict | None = None, provider: str | None = None) -> str:
    """Run the generation-only graph and return the assembled lesson text.

    Backs the backward-compatible core.generate_lesson(); does not evaluate,
    revise or export.
    """
    _ensure_tracing()
    lesson = lesson or core.SAMPLE_LESSON
    state = _gen_graph().invoke({
        "lesson": lesson, "provider": provider, "revision_count": 0,
    })
    return state["final_lesson_content"]


def run_lesson_graph(lesson: dict | None = None, provider: str | None = None,
                     run_eval: bool = True) -> LessonState:
    """Run the full graph: generate, evaluate, revise and export. Returns the state."""
    _ensure_tracing()
    lesson = lesson or core.SAMPLE_LESSON
    return _full_graph().invoke({
        "lesson": lesson, "provider": provider,
        "run_eval": run_eval, "revision_count": 0,
    })
