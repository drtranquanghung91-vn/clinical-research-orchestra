# AI-use disclosure

`out/ai-use-disclosure.md` is drafted from `STATUS.md`, `decisions.md` and the ledgers (`references.json → verified_by`,
the results ledger `source_file`, `claims.json`). The author edits it and is responsible for it. A skill
never marks it final: it is never marked final by a skill.

## Header
The draft starts with: "BẢN NHÁP - tác giả chỉnh sửa và chịu trách nhiệm / DRAFT - the author edits and is responsible".
Remove it only by the author's own edit. Never marked final by a skill.

## Table of steps
Header: `Bước / Step | Công cụ / Tool | AI làm gì / What the AI did | Tác giả đã kiểm tra / What the author checked`.

| Step | Tool | Source of the entry |
|---|---|---|
| Search | `search_lit.py`, literature APIs | `STATUS.md`, `decisions.md` |
| Screening and appraisal | orchestra skills | `decisions.md`, appraisal files |
| Analysis code | `crostats.py` / `analysis.py`, run locally | results ledger `source_file` |
| Drafting | orchestra role briefs | `STATUS.md` |
| Humanizing | prose-humanizer, `invariants.py` | `decisions.md` |
| Checking | `verify_refs.py`, `check_numbers.py`, `consistency_audit.py`, `audit.py` | `references.json → verified_by`, `claims.json` |

Fill "What the author checked" only from what the author recorded. If nothing is recorded, write
`[[AUTHOR: what you checked]]`.

## Statements (substance of the ICMJE recommendation, paraphrased)
Do not quote the recommendation and do not type a citation for it from memory.
- AI use is disclosed at submission and in the manuscript: writing assistance in the acknowledgements, analysis use
  in the methods.
- The author is responsible for the accuracy, integrity and originality of every part, including parts an AI tool helped
  with.
- An AI tool is not an author and is never listed or cited as one ("công cụ AI không phải là tác giả").
- No patient-identifiable data was sent to an AI tool: data were de-identified (phi-guard).
- The model name and version come from `STATUS.md`, `decisions.md` or the author. Never guess them.

## Reviews and case reports (P5)
- Screening suggestions: "AI suggested include/exclude for N records (role `screen-suggest`, stored in
  `02_evidence/sr/ai-suggestions.csv`); every decision was made by the two named reviewers, independently, and
  conflicts were resolved by consensus." N comes from the file; if no suggestion was made, say so.
- Draft extraction or risk of bias: "An AI draft was produced (`extract-draft` / `rob-draft`); each value and
  judgement was confirmed by <reviewer names>." Name the reviewers as in `project.yaml → review.reviewers`.
- Meta-analysis: computed by `meta.py` (Python); if `meta.py r-check` ran, the R and metafor versions it reported.
- Case report: the consent statement copies the `CONSENT: obtained …` line of `decisions.md`; the de-identification
  (relative time, age ranges) was checked by `case_lint.py` and phi-guard.
The disclosure stays a draft: never marked final by Claude.

## Where it goes
- Manuscript: methods or acknowledgements, per the journal.
- Thesis: after Lời cam đoan, or in Phụ lục, per the institution.

## Language
Keep a Vietnamese and an English template; choose by `language.output`.
