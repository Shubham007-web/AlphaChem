"""evals.py — quality evaluation for AlphaChemistry lessons.

Turns the metrics described in BUSINESS_PLAN.md into runnable measurements.
It evaluates generated lesson content (fresh from core.py, or loaded from a
saved .docx) on four axes:

  * Readability   -> Flesch Reading Ease + grade level   (deterministic, textstat)
  * Structure     -> are the expected 5E/14 sections present?  (deterministic)
  * Bloom's        -> LLM-as-judge classifies assessment items by cognitive level
  * NGSS alignment -> LLM-as-judge scores coverage of declared PEs / DCIs

The two LLM-as-judge metrics reuse core.build_llm(), so they run on whichever
provider is configured (azure/openai/ollama) and are traced by Phoenix just like
generation. Deterministic metrics always run, even with no model/credentials.

Run:
    python src/evals.py                       # generate the sample lesson, then evaluate
    python src/evals.py --docx outputs/.../U2Ch6L1.docx   # evaluate an existing file
    python src/evals.py --no-llm              # deterministic metrics only (no model)
    python src/evals.py --provider ollama     # use Ollama for the LLM judges
"""

from __future__ import annotations

import argparse
import json
import os
import re

from docx import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

import core  # reference implementation: LLM factory, sample lesson, tracing

# --------------------------------------------------------------------------- #
# Targets (from BUSINESS_PLAN.md §6 — the realistic, evidence-informed goals)
# --------------------------------------------------------------------------- #
FLESCH_TARGET = 70.0      # Flesch Reading Ease >= 70
BLOOM_TARGET = 85.0       # % of assessment items at higher-order (Apply+) levels
NGSS_TARGET = 85.0        # % coverage of declared Performance Expectations / DCIs
STRUCTURE_TARGET = 90.0   # % of expected sections present
WORDCOUNT_TARGET = 1500   # a complete lesson should be at least this many words
VOCAB_TARGET = 90.0       # % of declared vocabulary terms that appear in the content
RAGAS_TARGET = 100.0      # AspectCritic is binary per aspect; require all aspects to pass

# RAGAS aspect-critique checks: name -> yes/no definition the judge answers.
RAGAS_ASPECTS = {
    "age_appropriate": "Is the response written clearly and appropriately for grade 9 "
                       "students (ages 14-15), avoiding unnecessary jargon?",
    "factually_correct": "Is the chemistry content in the response factually accurate, "
                         "with no scientific errors?",
    "phenomenon_grounded": "Does the response connect its explanations to a real-world "
                          "phenomenon or storyline rather than being purely abstract?",
}

# Sections the 14-part template is supposed to produce (matched case-insensitively).
REQUIRED_SECTIONS = [
    "Big Idea", "Essential Question", "Phenomenon", "Vocabulary", "SMART",
    "Engage", "Pre-Explore", "Explore", "Explain", "Elaborate",
    "Evaluate", "Extend",
]

# Bloom's levels considered "higher-order" for the compliance metric.
HIGHER_ORDER = {"apply", "analyze", "evaluate", "create"}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def read_docx(path: str) -> str:
    """Return the plain text of a .docx (headings + paragraphs)."""
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)


def _count_syllables(word: str) -> int:
    """Rough syllable count used only when textstat is unavailable."""
    word = word.lower()
    groups = re.findall(r"[aeiouy]+", word)
    count = len(groups)
    if word.endswith("e") and count > 1:
        count -= 1
    return max(count, 1)


def _flesch_fallback(text: str) -> tuple[float, float]:
    """Compute Flesch Reading Ease and grade level without textstat."""
    sentences = max(len(re.findall(r"[.!?]+", text)), 1)
    words = re.findall(r"[A-Za-z]+", text)
    n_words = max(len(words), 1)
    syllables = sum(_count_syllables(w) for w in words)
    wps = n_words / sentences
    spw = syllables / n_words
    ease = 206.835 - 1.015 * wps - 84.6 * spw
    grade = 0.39 * wps + 11.8 * spw - 15.59
    return round(ease, 1), round(grade, 1)


def _extract_json(raw: str) -> dict:
    """Pull the first JSON object out of an LLM response (tolerates code fences)."""
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in judge response: {raw[:200]!r}")
    return json.loads(match.group())


def _judge(llm, system: str, human: str, variables: dict) -> dict:
    """Run a system+human prompt through the LLM and parse a JSON verdict."""
    chain = ChatPromptTemplate.from_messages(
        [("system", system), ("human", human)]
    ) | llm | StrOutputParser()
    return _extract_json(chain.invoke(variables))


# --------------------------------------------------------------------------- #
# Deterministic metrics
# --------------------------------------------------------------------------- #
def evaluate_readability(text: str) -> dict:
    """Flesch Reading Ease + grade level, pass/fail against FLESCH_TARGET."""
    try:
        import textstat

        ease = round(textstat.flesch_reading_ease(text), 1)
        grade = round(textstat.flesch_kincaid_grade(text), 1)
        method = "textstat"
    except ImportError:
        ease, grade = _flesch_fallback(text)
        method = "fallback (pip install textstat for accuracy)"
    return {
        "flesch_reading_ease": ease,
        "flesch_kincaid_grade": grade,
        "target": FLESCH_TARGET,
        "passed": ease >= FLESCH_TARGET,
        "method": method,
    }


def evaluate_structure(text: str) -> dict:
    """Fraction of REQUIRED_SECTIONS present in the content."""
    low = text.lower()
    present = [s for s in REQUIRED_SECTIONS if s.lower() in low]
    missing = [s for s in REQUIRED_SECTIONS if s.lower() not in low]
    score = round(100 * len(present) / len(REQUIRED_SECTIONS), 1)
    return {
        "present": present,
        "missing": missing,
        "score_pct": score,
        "target": STRUCTURE_TARGET,
        "passed": score >= STRUCTURE_TARGET,
    }


def evaluate_wordcount(text: str) -> dict:
    """Total word count vs. WORDCOUNT_TARGET (a full lesson should be substantial)."""
    words = len(re.findall(r"\b\w+\b", text))
    sentences = max(len(re.findall(r"[.!?]+", text)), 1)
    return {
        "word_count": words,
        "sentence_count": sentences,
        "avg_sentence_len": round(words / sentences, 1),
        "target": WORDCOUNT_TARGET,
        "passed": words >= WORDCOUNT_TARGET,
    }


def evaluate_vocabulary_coverage(text: str, lesson: dict) -> dict:
    """Fraction of the lesson's declared vocabulary terms that appear in the content."""
    terms = [t.strip() for t in lesson.get("lesson_vocabulary", "").splitlines() if t.strip()]
    low = text.lower()
    present = [t for t in terms if t.lower() in low]
    missing = [t for t in terms if t.lower() not in low]
    score = round(100 * len(present) / len(terms), 1) if terms else 0.0
    return {
        "terms_total": len(terms),
        "present": present,
        "missing": missing,
        "score_pct": score,
        "target": VOCAB_TARGET,
        "passed": score >= VOCAB_TARGET,
    }


# --------------------------------------------------------------------------- #
# LLM-as-judge metrics
# --------------------------------------------------------------------------- #
_BLOOM_SYSTEM = (
    "You are an assessment expert. You classify each assessment question in a "
    "lesson by its Bloom's taxonomy level: Remember, Understand, Apply, Analyze, "
    "Evaluate, or Create. Respond with ONLY a JSON object."
)
_BLOOM_HUMAN = """Identify every assessment/quiz/debate question in the lesson below and classify each one's Bloom's level.

Return strict JSON of the form:
{{"questions": [{{"question": "<short text>", "level": "<bloom level>"}}], "notes": "<one sentence>"}}

LESSON:
{lesson_text}
"""

_NGSS_SYSTEM = (
    "You are an NGSS curriculum reviewer. You judge how well a lesson covers its "
    "declared Performance Expectations (PEs) and Disciplinary Core Ideas (DCIs). "
    "Respond with ONLY a JSON object."
)
_NGSS_HUMAN = """Score how thoroughly the lesson addresses the declared standards, each from 0 to 100.

Declared Performance Expectations:
{performance_expectations}

Declared Disciplinary Core Ideas:
{disciplinary_core_ideas}

Return strict JSON:
{{"pe_coverage": <0-100>, "dci_coverage": <0-100>, "justification": "<one sentence>"}}

LESSON:
{lesson_text}
"""


def evaluate_bloom(text: str, llm) -> dict:
    """LLM classifies assessment items; compliance = % at higher-order levels."""
    verdict = _judge(llm, _BLOOM_SYSTEM, _BLOOM_HUMAN, {"lesson_text": text})
    questions = verdict.get("questions", [])
    distribution: dict[str, int] = {}
    higher = 0
    for q in questions:
        level = str(q.get("level", "")).strip().lower()
        distribution[level] = distribution.get(level, 0) + 1
        if level in HIGHER_ORDER:
            higher += 1
    total = len(questions)
    compliance = round(100 * higher / total, 1) if total else 0.0
    return {
        "num_questions": total,
        "distribution": distribution,
        "higher_order_pct": compliance,
        "target": BLOOM_TARGET,
        "passed": compliance >= BLOOM_TARGET,
    }


def evaluate_ngss(text: str, lesson: dict, llm) -> dict:
    """LLM scores coverage of declared PEs/DCIs; alignment = their average."""
    verdict = _judge(llm, _NGSS_SYSTEM, _NGSS_HUMAN, {
        "lesson_text": text,
        "performance_expectations": lesson.get("performance_expectations", "n/a"),
        "disciplinary_core_ideas": lesson.get("disciplinary_core_ideas", "n/a"),
    })
    pe = float(verdict.get("pe_coverage", 0))
    dci = float(verdict.get("dci_coverage", 0))
    alignment = round((pe + dci) / 2, 1)
    return {
        "pe_coverage": pe,
        "dci_coverage": dci,
        "alignment_pct": alignment,
        "justification": verdict.get("justification", ""),
        "target": NGSS_TARGET,
        "passed": alignment >= NGSS_TARGET,
    }


def evaluate_ragas(text: str, lesson: dict, provider: str | None = None) -> dict:
    """RAGAS AspectCritic: binary LLM checks for each aspect in RAGAS_ASPECTS.

    Each aspect scores 1 (pass) or 0 (fail); the metric's pass_pct is the share
    of aspects that passed. Uses the same provider as the other judges.
    """
    import asyncio

    from ragas import SingleTurnSample
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import AspectCritic

    evaluator_llm = LangchainLLMWrapper(core.build_llm(provider))
    sample = SingleTurnSample(
        user_input=lesson.get("essential_question", "Generate a chemistry lesson."),
        response=text,
    )

    aspects: dict[str, dict] = {}
    passed_count = 0
    for name, definition in RAGAS_ASPECTS.items():
        metric = AspectCritic(name=name, definition=definition, llm=evaluator_llm)
        score = float(asyncio.run(metric.single_turn_ascore(sample)))
        passed = bool(round(score))
        aspects[name] = {"score": score, "passed": passed}
        passed_count += int(passed)

    total = len(RAGAS_ASPECTS)
    pass_pct = round(100 * passed_count / total, 1) if total else 0.0
    return {
        "aspects": aspects,
        "pass_pct": pass_pct,
        "target": RAGAS_TARGET,
        "passed": pass_pct >= RAGAS_TARGET,
    }


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def evaluate_lesson(text: str, lesson: dict, use_llm: bool = True,
                    provider: str | None = None) -> dict:
    """Run all available metrics on the lesson text and return a results dict."""
    results = {
        "readability": evaluate_readability(text),
        "structure": evaluate_structure(text),
        "wordcount": evaluate_wordcount(text),
        "vocabulary": evaluate_vocabulary_coverage(text, lesson),
    }
    if use_llm:
        try:
            llm = core.build_llm(provider)
            results["bloom"] = evaluate_bloom(text, llm)
            results["ngss"] = evaluate_ngss(text, lesson, llm)
        except Exception as exc:  # missing creds, model down, bad JSON, etc.
            results["llm_error"] = (
                f"Bloom/NGSS judges skipped: {type(exc).__name__}: {exc}"
            )
        try:
            results["ragas"] = evaluate_ragas(text, lesson, provider)
        except Exception as exc:  # ragas not installed, model down, etc.
            results["ragas_error"] = (
                f"RAGAS metrics skipped: {type(exc).__name__}: {exc}"
            )
    return results


def print_report(results: dict) -> None:
    """Pretty-print the results dict with pass/fail markers."""
    def mark(ok: bool) -> str:
        return "PASS" if ok else "FAIL"

    r = results["readability"]
    print("\n=== Lesson Quality Report ===")
    print(f"[{mark(r['passed'])}] Readability   Flesch={r['flesch_reading_ease']} "
          f"(target >= {r['target']}), grade={r['flesch_kincaid_grade']}  [{r['method']}]")

    s = results["structure"]
    print(f"[{mark(s['passed'])}] Structure     {s['score_pct']}% sections present "
          f"(target >= {s['target']}%)")
    if s["missing"]:
        print(f"             missing: {', '.join(s['missing'])}")

    w = results["wordcount"]
    print(f"[{mark(w['passed'])}] Word count    {w['word_count']} words "
          f"(target >= {w['target']}), avg sentence {w['avg_sentence_len']} words")

    v = results["vocabulary"]
    print(f"[{mark(v['passed'])}] Vocab cover   {v['score_pct']}% of {v['terms_total']} "
          f"terms present (target >= {v['target']}%)")
    if v["missing"]:
        print(f"             missing: {', '.join(v['missing'])}")

    if "bloom" in results:
        b = results["bloom"]
        print(f"[{mark(b['passed'])}] Bloom's       {b['higher_order_pct']}% higher-order "
              f"of {b['num_questions']} questions (target >= {b['target']}%)")
        print(f"             distribution: {b['distribution']}")

    if "ngss" in results:
        n = results["ngss"]
        print(f"[{mark(n['passed'])}] NGSS align    {n['alignment_pct']}% "
              f"(PE={n['pe_coverage']}, DCI={n['dci_coverage']}, target >= {n['target']}%)")

    if "ragas" in results:
        rg = results["ragas"]
        passed_aspects = sum(a["passed"] for a in rg["aspects"].values())
        summary = ", ".join(
            f"{name}={int(a['passed'])}" for name, a in rg["aspects"].items()
        )
        print(f"[{mark(rg['passed'])}] RAGAS         {rg['pass_pct']}% aspects passed "
              f"({passed_aspects}/{len(rg['aspects'])}): {summary}")

    if "llm_error" in results:
        print(f"[----] {results['llm_error']}")
    if "ragas_error" in results:
        print(f"[----] {results['ragas_error']}")
    print("=============================\n")


def log_scores_to_phoenix(span_id: str, results: dict, tracer_provider) -> None:
    """Attach the computed metric scores to a Phoenix span as evaluations.

    Turns each metric into a Phoenix SpanEvaluation (score + pass/fail label +
    explanation) keyed to span_id, so the numbers become filterable in the UI
    instead of living only in the terminal report.
    """
    try:
        from phoenix.client import Client
    except ImportError:
        print("[evals] phoenix.client unavailable; scores not logged to the UI.")
        return

    # Make sure the eval span is exported before we annotate it.
    try:
        tracer_provider.force_flush()
    except Exception:
        pass

    rd, st = results["readability"], results["structure"]
    wc, vc = results["wordcount"], results["vocabulary"]
    # name -> (annotator_kind, score, passed, explanation)
    rows = {
        "Readability": ("CODE", rd["flesch_reading_ease"], rd["passed"],
                        f"grade {rd['flesch_kincaid_grade']} ({rd['method']})"),
        "Structure": ("CODE", st["score_pct"], st["passed"],
                      "missing: " + (", ".join(st["missing"]) or "none")),
        "WordCount": ("CODE", wc["word_count"], wc["passed"],
                      f"target >= {wc['target']}, avg sentence {wc['avg_sentence_len']}"),
        "VocabCoverage": ("CODE", vc["score_pct"], vc["passed"],
                          "missing: " + (", ".join(vc["missing"]) or "none")),
    }
    if "bloom" in results:
        b = results["bloom"]
        rows["Bloom_HigherOrder"] = ("LLM", b["higher_order_pct"], b["passed"], str(b["distribution"]))
    if "ngss" in results:
        n = results["ngss"]
        rows["NGSS_Alignment"] = ("LLM", n["alignment_pct"], n["passed"], n["justification"])
    if "ragas" in results:
        rg = results["ragas"]
        summary = ", ".join(f"{k}={int(a['passed'])}" for k, a in rg["aspects"].items())
        rows["RAGAS_Aspects"] = ("LLM", rg["pass_pct"], rg["passed"], summary)

    import time

    def _annotate(client, **kwargs):
        # The span is ingested asynchronously; retry until it exists (404) before
        # the annotation can attach. ~8 attempts over ~8s covers normal lag.
        last = None
        for _ in range(8):
            try:
                client.spans.add_span_annotation(**kwargs)
                return
            except Exception as exc:  # noqa: BLE001 - mostly 404 span-not-found
                last = exc
                time.sleep(1.0)
        raise last

    try:
        client = Client()
        for name, (kind, score, passed, explanation) in rows.items():
            _annotate(
                client,
                span_id=span_id,
                annotation_name=name,
                annotator_kind=kind,
                label="pass" if passed else "fail",
                score=float(score),
                explanation=explanation,
                sync=True,
            )
        print(f"[evals] logged {len(rows)} scores to Phoenix (span {span_id}).")
    except Exception as exc:
        print(f"[evals] could not log scores to Phoenix: {type(exc).__name__}: {exc}")


def main() -> dict:
    parser = argparse.ArgumentParser(description="Evaluate AlphaChemistry lesson quality.")
    parser.add_argument("--docx", help="Evaluate an existing .docx instead of generating one.")
    parser.add_argument("--provider", choices=["azure", "openai", "ollama"],
                        help="LLM provider for generation and/or the judges.")
    parser.add_argument("--no-llm", action="store_true",
                        help="Run only deterministic metrics (no model needed).")
    args = parser.parse_args()

    tracer_provider = core.setup_tracing()  # trace generation + judge calls in Phoenix
    lesson = core.SAMPLE_LESSON

    def _get_text() -> str:
        if args.docx:
            print(f"Evaluating existing lesson: {args.docx}")
            return read_docx(args.docx)
        print("Generating sample lesson via core.generate_lesson() ...")
        return core.generate_lesson(lesson, provider=args.provider)

    span_id = None
    if tracer_provider is not None:
        # Run inside an explicit evaluator span; judge calls nest under it, and
        # we capture its id to attach the scores afterwards.
        tracer = tracer_provider.get_tracer("alphachem.evals")
        with tracer.start_as_current_span("lesson_eval") as span:
            span.set_attribute("openinference.span.kind", "EVALUATOR")
            span_id = format(span.get_span_context().span_id, "016x")
            text = _get_text()
            results = evaluate_lesson(text, lesson, use_llm=not args.no_llm,
                                      provider=args.provider)
    else:
        text = _get_text()
        results = evaluate_lesson(text, lesson, use_llm=not args.no_llm,
                                  provider=args.provider)

    print_report(results)
    if span_id is not None:
        log_scores_to_phoenix(span_id, results, tracer_provider)
    return results


if __name__ == "__main__":
    main()
