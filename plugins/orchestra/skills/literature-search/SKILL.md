---
name: literature-search
description: 'Use when a research question or topic needs its literature found, verified and organised: search strategy, evidence table, evidence map, research gaps, or "what have previous studies done". Triggers: "tìm tài liệu cho đề tài", "tìm y văn", "chiến lược tìm kiếm", "bảng tổng hợp nghiên cứu", "evidence table", "bản đồ bằng chứng", "evidence map", "research gap", "khoảng trống nghiên cứu", "các nghiên cứu trước đã làm gì", "search strategy", "find studies on"; or after the research question is approved and before the protocol.'
---

Methods content by Amelia Le (co-author), adapted for clinical-research-orchestra.

# Literature search

## 1. Core rule
Every claim about the literature traces to a PMID or DOI that a tool returned in this session
(`${CLAUDE_PLUGIN_ROOT}/references/evidence-policy.md`). Never write one from memory.

## 2. Scope
A structured narrative or scoping evidence synthesis, not a systematic review. A true systematic
review needs a PROSPERO protocol, two independent screeners and PRISMA 2020: say so, and point to
`systematic-review` (phase P3).

## 3. Steps
Inputs: `01_question/question.md` (PICO/PECO). Detail for every step is in the workflow file.
0. Nomenclature check (renamed conditions, new criteria, MeSH lag) before any query. Record in
   `02_evidence/search-strategy.md` which MeSH heading, if any, the new-name papers carry (checked by
   a tool, never from memory) and whether the population block relies on `[tiab]` alone.
1. Search plan, targeted or exploratory, in `02_evidence/search-strategy.md`
   (`${CLAUDE_PLUGIN_ROOT}/references/literature/search-strategy.md`).
2. Run `search_lit.py search`; also ClinicalTrials.gov filtered by the study country (the
   counter-check for a population gap). Add chosen records with `search_lit.py add <project> <pmid-or-doi>...`; a source the author holds
   with neither goes in only via `add-manual ... --seen-in <document>` (ask for the document).
3. `verify_refs.py <project> --write`.
4. Evidence table with a risk-of-bias column. 4b: source credibility (retractions in batches,
   predatory journals, COI, duplicate publications of one trial). 4c: appraise key studies with the
   Skill tool `critical-appraisal`.
5. GRADE or GRADE-CERQual certainty per main outcome, marked preliminary.
6. Apples versus pears: I² and prediction interval before reading a pooled estimate.
7. Read confidence intervals by clinical importance, never "no difference" from p > 0.05.
8. Evidence map and gaps (each gap needs a counter-check). Number references with
   `cite_render.py`, never by hand.
9. Report PRISMA-S fields and the ICMJE AI-use note. For AI or engineering topics add the default
   limitation "IEEE/arXiv not searched" unless they were.

## 4. "Just do it" rule
If the user says not to ask, do not ask. Open with an **Assumptions / Giả định** box, put the
riskiest assumption in the confirmation list, and record the box in `decisions.md`.

## 5. Output
Write in `project.yaml → language.output`: `02_evidence/search-strategy.md`,
`02_evidence/evidence-table.md`, `02_evidence/evidence-map.md`, `02_evidence/gaps.md`,
`02_evidence/appraisal/<ref-id>.md`. Set `STATUS.md` row 2 to `doing`, then `done` after the
author approves. Templates: `${CLAUDE_PLUGIN_ROOT}/references/literature/evidence-output-template.md`.

## 6. Workflow
`${CLAUDE_PLUGIN_ROOT}/references/workflows/literature-search.md`

Writing the review as prose is out of scope here. To write Chapter 1 or a background section, use the Skill tool with `literature-review`.
