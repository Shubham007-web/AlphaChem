# AlphaChemistry Content Generator — Business Plan (Internal Strategy)


>
> This is an internal strategy document. Numbers labeled **Target** are objectives, **not** results we have achieved or instrumented yet. Keeping this distinction honest is what makes the plan executable.

---

## 1. Executive Summary

AlphaChemistry Content Generator is an AI-powered system that turns a curriculum specification (learning objectives + NGSS metadata) into structured, standards-aligned, grade-appropriate high-school chemistry lessons delivered as versioned Word documents.

The thesis: **manual curriculum authoring is slow, expensive, and inconsistent.** A subject-matter expert (SME) can spend many hours per lesson and still produce content that drifts from NGSS alignment, Bloom's-taxonomy coverage, and target reading level. Our system generates a high-quality first draft in minutes, with standards and readability constraints baked into the generation step — shifting the SME's role from *author* to *reviewer*.

Today we have a working prototype (LLM + LangChain → versioned `.docx`). The strategy in this document is to harden that prototype into a measurable product: build the retrieval pipeline that grounds content in source material, and—critically—**instrument the quality metrics we currently only assert**.

---

## 2. Problem Statement

Producing a full chemistry curriculum (Units → Chapters → Lessons, each with explanations and assessments) is bottlenecked by five pains:

1. **Cost** — SME + instructional-designer time is the dominant expense per lesson.
2. **Speed** — hand-authoring a single standards-aligned lesson takes hours to days.
3. **Consistency** — every requirement (NGSS, Bloom's, DOK, reading level) depends on an individual author remembering and applying it uniformly across hundreds of lessons.
4. **Accuracy** — chemistry is factual; content must be correct, not plausible-sounding.
5. **Scale** — covering an entire course multiplies all of the above.

---

## 3. Solution Overview

### What exists today (Implemented)
- **LLM-driven lesson generation** via OpenAI / Azure OpenAI, orchestrated in Jupyter notebooks ([Final_Lesson_14Oct.ipynb](Final_Lesson_14Oct.ipynb), [LangChain_Lesson_Generator.ipynb](LangChain_Lesson_Generator.ipynb), [Large_Content.ipynb](Large_Content.ipynb)).
- **Structured prompt design** producing the 5E-style flow (Engage / Explain / Elaborate / Evaluate / Extend) plus an assessment block (prompts request 8 Bloom-aligned questions).
- **Versioned `.docx` output** with an automatic `Unit/Chapter/Lesson` folder hierarchy (`generate_lesson_content()`, `save_lesson_content_to_docx()`, `find_next_version_file_name()`).
- **Readability constraint** enforced through the prompt (see §6 for the Flesch inconsistency we resolve here).
- **API key hygiene** via gitignored `.env` ([openAI_API.py](openAI_API.py), [azure_llm.py](azure_llm.py)).

### What the product needs to become (Planned)
- A real **retrieval-augmented generation (RAG)** pipeline (FAISS index over source texts) — the README describes this, but **no index or ingestion code exists in the repo yet**.
- An **automated quality-evaluation layer** that measures the metrics in §6 instead of asserting them.
- A non-notebook **runnable pipeline / service** so generation is repeatable outside an interactive session.

---

## 4. Inputs

| Input | Status | Reality in the codebase |
|---|---|---|
| Learning objectives + NGSS metadata | **Implemented** | [AlphaChem_LOs.csv](AlphaChem_LOs.csv): Unit, Chapter, Lesson, Vocabulary, Essential Question, Learning Objective, **Performance Expectations**, **Disciplinary Core Ideas** (the latter two are literal NGSS components). |
| SME-authored reference lessons | **Implemented** | Exemplar `.docx` files (e.g. [Cleaned_U2Ch3L1.docx](Cleaned_U2Ch3L1.docx), [U2Ch3L1.docx](U2Ch3L1.docx)) used as style/structure references. |
| Curriculum frameworks (NGSS, Bloom's, DOK) | **Implemented (as prompt rules)** | Embedded in prompt instructions, not as a separate ingested dataset. |
| Chemistry textbooks / source corpus | **Planned** | Referenced conceptually; **no ingested corpus or FAISS index in the repo**. Required for the RAG pipeline. |
| ~~Assessment banks~~ | **Reframed** | Assessments are an **output**, not an input. There is no assessment bank consumed by the system. |

**Canonical input statement:** *the LO/NGSS spreadsheet + SME exemplars today; plus a curated chemistry source corpus once RAG is built.*

---

## 5. Outputs

| Output | Status | Reality in the codebase |
|---|---|---|
| Structured lesson plans (5E flow) | **Implemented** | `generate_lesson_content()` and the structured prompts. |
| Assessments (Bloom-aligned questions) | **Implemented** | Prompts explicitly request 8 assessment questions aligned to Bloom's levels. |
| Word documents with versioning | **Implemented** | `save_lesson_content_to_docx()` + `find_next_version_file_name()` (V1, V2, …) into the `Unit/Chapter/Lesson` tree. |
| Capstone / project-based assessments | **Planned** | Not present anywhere in the codebase today. Roadmap item. |

---

## 6. Metrics & KPIs

**Important:** These are **evidence-informed projections**, not yet measured on our own output. The original round numbers (50% / 35% / 95% / 90%) were aspirational; the figures below are **defensible ranges** grounded in how comparable LLM content-generation systems actually score, each anchored to a **baseline** so the gain is measurable rather than asserted. We commit to the *conservative* end externally and treat the upper end as a stretch.

| Metric | Eval method | Baseline (manual / un-tuned LLM) | Realistic target | Stretch | Basis for the estimate |
|---|---|---|---|---|---|
| Content production time reduction | Production-time tracker: generation time + logged SME review/edit time vs. a manual-authoring baseline. | ~6–8 hrs/lesson fully manual | **40–50%** (≈3.5–4.5 hrs/lesson) | 55–60% | Human-in-the-loop draft+review workflows typically save ~40–55% net; first-draft-only saving is higher but SME review claws some back. |
| Learner engagement increase | Downstream **LMS data** (time-on-task, completion, quiz attempts) — external dependency, A/B vs. legacy content. | Current course engagement | **+8–15%** | +20% | EdTech studies on higher-quality/structured content show modest single-to-low-double-digit lifts; +35% is an outlier, not a planning number. |
| Readability (Flesch Reading Ease) | Post-generation `textstat` Flesch score; % of lessons passing the gate. | Un-tuned GPT chemistry ≈ 50–60 Flesch | **≥ 70**, with **~75–85% first-pass** rate | ~95% pass after one auto-revise loop | Canonical target Flesch ≥ 70 (resolves the README 70 vs. notebook 80 conflict). Technical chemistry vocabulary caps how high Flesch can realistically go. |
| Bloom's taxonomy compliance | LLM-as-judge classifies each assessment item's cognitive level vs. the intended rubric; report % match. | Un-prompted ≈ 60–70% | **80–88%** | ~90% | LLM-judge / classifier agreement on Bloom level typically lands mid-to-high 80s; 95% exceeds realistic inter-rater agreement. Report with a human spot-check on ~15% of items. |
| NGSS alignment | LLM-as-judge scores coverage of the LO row's `Performance Expectations` & `Disciplinary Core Ideas`. | Un-grounded ≈ 65–75% | **82–88% coverage** | ~92% | Rubric-based coverage scoring on grounded content lands mid-to-high 80s; improves once the RAG pipeline (P1) supplies source text. |

### Evaluation methodology (how the numbers become trustworthy)
- **Sample:** evaluate each metric on a held-out set of **30–50 generated lessons** per release, not cherry-picked examples.
- **Human calibration:** SME spot-checks **~15%** of the LLM-judge verdicts (Bloom & NGSS) to estimate judge reliability; report agreement alongside the score.
- **Baseline discipline:** every percentage is reported **vs. its baseline** above, with the sample size — a bare "88%" is meaningless without the comparison set.
- **Cadence:** re-run the full metric suite on every prompt/model change so quality regressions are caught before release.
- **Reporting honesty:** until the suite has run on a real sample, these stay labeled **Projection**; once measured, they graduate to **Measured (n=…)**.

---

## 7. Instrumentation Roadmap (making the metrics real)

The credibility gap is that four of five headline metrics are uninstrumented. Closing it:

1. **Readability scorer** — add `textstat`-based Flesch + Flesch-Kincaid scoring as a post-generation gate; standardize on Flesch ≥ 70; fail/flag and (optionally) auto-revise low-scoring lessons.
2. **Bloom's classifier** — classify each generated assessment item by cognitive level (LLM-as-judge or a trained classifier); report the distribution vs. the target rubric → produces the "compliance %".
3. **NGSS alignment checker** — given a lesson + its source LO row, score coverage of declared Performance Expectations and Disciplinary Core Ideas (LLM-as-judge with a structured rubric) → produces the "alignment %".
4. **Production-time tracker** — log generation time + SME review/edit time per lesson; maintain a manual-authoring baseline for the reduction comparison.
5. **Engagement (dependency)** — define the LMS/event-data integration needed; flagged as **out of scope for the generator** and dependent on a deployment partner.

All four scorers should write a per-lesson **quality report** alongside the `.docx`, so every output carries its own metrics.

---

## 8. Product Roadmap

| Phase | Goal | Key work |
|---|---|---|
| **P0 — Harden the generator** | Repeatable generation outside notebooks. | Extract notebook logic into a runnable module/CLI; centralize prompts; resolve Flesch 70-vs-80. |
| **P1 — Real RAG pipeline** | Ground content in source material to cut hallucination. | Build the curated chemistry corpus, FAISS index, and retrieval step the README promises. |
| **P2 — Metrics instrumentation** | Make §6 metrics measured, not asserted. | Ship the four scorers + per-lesson quality report from §7. |
| **P3 — Expansion** | Beyond pilot scope. | More subjects/grade levels, capstone/project generation, diagrams/visuals (per README "Future Enhancements"). |

---

## 9. Market & Positioning

- **Target buyers:** EdTech publishers, curriculum-development teams, and schools/districts producing or customizing chemistry curriculum.
- **Value proposition:** standards-aligned, readability-guaranteed, fact-grounded lesson drafts at a fraction of manual authoring time/cost — with a human SME in the loop as reviewer rather than author.
- **Differentiator:** standards and readability constraints enforced *and measured* at generation time, not bolted on after.

---

## 10. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| **LLM hallucination** (incorrect chemistry) | Build the RAG pipeline (P1) to ground output; keep SME human-in-the-loop review. |
| **Metrics seen as marketing, not real** | Ship the instrumentation in P2 before quoting the numbers externally; label status honestly until then. |
| **Standards drift** (NGSS/Bloom requirements change) | Keep frameworks as versioned, editable prompt/rubric assets; re-run the alignment checker on changes. |
| **Content quality variance** | Mandatory SME review gate + automated quality report per lesson. |
| **Cost per generation** at scale | Track token/cost per lesson; tune model choice (e.g., reserve top models for hard sections). |
| **Vendor/API lock-in** | Already abstracted across OpenAI and Azure; keep the model layer swappable. |

---

## 11. Success Criteria (internal)

The strategy is "working" when:
- Generation runs as a repeatable pipeline (not just interactive notebooks).
- Every generated lesson ships with an automated **quality report** (Flesch, Bloom distribution, NGSS coverage).
- The four Target metrics are **measured** against a documented baseline — at which point they graduate from **Target** to reported results.
- A single canonical readability target (Flesch ≥ 70) is enforced consistently across code and docs.
