---
name: systematic-review
description: 'Use when the user wants a systematic review or meta-analysis planned, screened, extracted, pooled, graded or written. Triggers: "tổng quan hệ thống", "phân tích gộp", "gộp các nghiên cứu", "gộp thành một con số RR/OR chung", "pooled estimate", "sàng lọc bài báo", "trích xuất dữ liệu", "risk of bias cho tổng quan hệ thống", "systematic review", "meta-analysis", "PRISMA", "PROSPERO", "meta-analysis forest plot", "forest plot gộp", "GRADE summary of findings", "bảng tóm tắt kết quả GRADE".'
---

# Systematic review

Protocol first, two human reviewers, every number from a script, export only through G4. Detail:
`${CLAUDE_PLUGIN_ROOT}/references/workflows/systematic-review.md`. Not covered: network meta-analysis, IPD,
diagnostic-accuracy pooling, meta-regression beyond one factor, Bayesian models; refer to a statistician.

## 1. Protocol (G2)
Write `03_protocol/sr-protocol.md` from `${CLAUDE_PLUGIN_ROOT}/references/review/sr-protocol-template.md` with the
analysis register (the author chooses the model now; random effects with REML by default), the PROSPERO draft
`03_protocol/prospero.md` and the strings `02_evidence/sr/strings.md`. Ask for the two human reviewers and write
them in `project.yaml → review.reviewers`. The author opens G2
(`gate.py open . G2 --by "<name>" --files 03_protocol/sr-protocol.md …`); run
`python "${CLAUDE_PLUGIN_ROOT}/scripts/gate.py" check . G2` before any screening step.

## 2. Search and screening
- PubMed through the Skill tool `literature-search`; the author runs the other databases and logs every run in
  `02_evidence/sr/search-log.csv`.
- `screening.py . import`, then `dedupe`, `sheet`, `decide`, `conflicts`, `kappa` and `counts` as in the workflow.
- You are never a reviewer. Asked to screen alone or to "just include" studies, refuse that part: offer labelled
  suggestions (brief `${CLAUDE_PLUGIN_ROOT}/references/review/roles/screen-suggest.md`, saved with
  `python "${CLAUDE_PLUGIN_ROOT}/scripts/screening.py" . suggest --stage ta --from reviews/tmp/ai-suggestions.ta.csv`)
  and say the two reviewers decide. Never write `screening.csv` or run `decide` for anyone.

## 3. Extraction and risk of bias
Two extraction files, a consensus file and `rob.csv` confirmed by both reviewers (AI drafts only through the
`extract-draft` and `rob-draft` briefs); `python "${CLAUDE_PLUGIN_ROOT}/scripts/extract_check.py" .` until no block.

## 4. Synthesis
- `python "${CLAUDE_PLUGIN_ROOT}/scripts/meta.py" . run`, then `meta.py . forest-spec`. Report every pooled
  estimate with τ², I² and the prediction interval. Never switch model after seeing results; a switch is a
  `DEVIATION A<n>:` line the author writes.
- High heterogeneity, or a protocol that forbids pooling: say the pooled value is uncertain or do not pool, and
  write a SWiM synthesis (`${CLAUDE_PLUGIN_ROOT}/references/review/swim.md`).
- R is optional: `python "${CLAUDE_PLUGIN_ROOT}/scripts/meta.py" . r-status`; offer `r-check` only when it reports
  R and metafor. You never install software.
- GRADE in `05_analysis/meta/grade.json` with the author, then `python "${CLAUDE_PLUGIN_ROOT}/scripts/grade.py" . run`.

## 5. Lock, write, export
The author locks G3. Draft with `${CLAUDE_PLUGIN_ROOT}/references/writing/roles/review-systematic.md` and the P4
roles; reviewers, then `python "${CLAUDE_PLUGIN_ROOT}/scripts/worklog.py" score . review --round N`;
`python "${CLAUDE_PLUGIN_ROOT}/scripts/assemble.py" . review`; `python "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" . review`;
the author opens G4; `python "${CLAUDE_PLUGIN_ROOT}/scripts/assemble.py" . review --final`. Then the disclosure (AI
suggestions counted) and `python "${CLAUDE_PLUGIN_ROOT}/scripts/worklog.py" decisions .`.
E-REF is the author's call: verify, replace or record manually; never delete or reword the citing sentence, nor edit a reference status or ledger to pass. In drafts, ask the author to fill each `[[AUTHOR: …]]`/`[[TÁC GIẢ: …]]`, never fill them yourself.
