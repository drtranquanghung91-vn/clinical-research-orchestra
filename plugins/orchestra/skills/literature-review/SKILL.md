---
name: literature-review
description: 'Use when literature must be written up as prose: thesis Chapter 1 (tổng quan tài liệu), the background or introduction of a paper, or a narrative review. Triggers: "tổng quan tài liệu", "viết tổng quan", "chương 1 tổng quan", "tổng quan y văn", "viết phần đặt vấn đề", "viết phần mở đầu bài báo", "background", "introduction section", "literature review", "narrative review", "viết bài tổng quan".'
---

# Literature review

Write synthesis, not a catalogue. Every sentence that carries a citation is supported by the cited
record's abstract or full text in the ledger.

## Before writing
1. Require verified evidence: `ledgers/references.json` checked by `verify_refs.py`, an evidence table
   with risk of bias and certainty, and `02_evidence/gaps.md`. If missing, use the Skill tool with
   `literature-search` first.
2. Choose the mode:
   - **a. Thesis Chapter 1** (`06_writing/thesis/ch1-literature-review.md`): structure from
     `${CLAUDE_PLUGIN_ROOT}/references/literature/vn-chapter1.md`, including studies in Vietnam and abroad.
   - **b. Manuscript background** (`06_writing/manuscript/background.md`): 3–5 paragraphs, funnel from
     burden to gap to aim.
   - Scoping or systematic reviews are separate study types (phase P3); say so if asked.
3. Plan in `ledgers/outline.json → section_plan`: one claim per paragraph, its supporting reference ids,
   the certainty from the evidence table.

## Writing rules (detail: `${CLAUDE_PLUGIN_ROOT}/references/literature/review-writing.md`)
- Organise by theme or question, never paper by paper.
- Compare: where studies agree, where they disagree, and why (design, population, risk of bias, measurement).
- Claim strength follows certainty: high → "reduces"; low → "may reduce"; very low → "it is uncertain whether".
- Cite with `[@id]`; only ids that exist in the ledger.
- End on the gap that justifies this study (mode a and b).
- Write in `project.yaml → language.output`. Vietnamese text follows Vietnamese academic conventions.

## Checks before handing back
1. `python "${CLAUDE_PLUGIN_ROOT}/scripts/review_lint.py" <file>`: must not block (E-LIT). Rewrite
   flagged paragraphs thematically and re-run.
2. `python "${CLAUDE_PLUGIN_ROOT}/scripts/verify_refs.py" <project> --cite <file>`: no E-REF findings.
3. For a thesis or any output that needs numbered references, run `python "${CLAUDE_PLUGIN_ROOT}/scripts/cite_render.py" <project> <file> <out.md>` (add `--start-marker` when tables precede the review); never number references by hand.
4. Add a claims row for each substantive claim to `ledgers/claims.json` (`kind: background`, status from
   reading level).
5. Report to the author what was checked and anything that could not be verified.
