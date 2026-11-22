---
name: case-report
description: 'Use when the user wants a clinical case report written, de-identified, checked against CARE or BMJ Case Reports, or exported. Triggers: "báo cáo ca bệnh", "viết case report", "ca lâm sàng hiếm", "báo cáo ca lâm sàng", "ca bệnh để đăng báo", "case report", "BMJ Case Reports", "CARE checklist", "write up this case", "similar cases table".'
---

# Case report

A de-identified case, its facts locked in the results ledger, written in CARE order (or BMJ headings), reviewed,
audited and exported only through G4 with consent recorded. Detail:
`${CLAUDE_PLUGIN_ROOT}/references/workflows/case-report.md`.

## 1. Gate and consent
G1: the case, the teaching point and the consent status, confirmed by the author. Ask once whether written consent
was obtained and who signed. Only the author writes `CONSENT: obtained <form, who signed>` in `decisions.md`; never
write it yourself. Without it you may draft, but say the final export is refused.

## 2. Dossier and facts
- Write `01_case/dossier.md` from the author's notes in relative time (day 0, day +3) and age ranges ("in her
  40s"), with no names, places, institution, record numbers or calendar dates. Never put an identifier, an exact
  age or a date into a literature query or any tool input.
- One row per reportable value in `01_case/facts.csv`, then `python "${CLAUDE_PLUGIN_ROOT}/scripts/case_facts.py" .`.
- Discussion literature and similar cases with the Skill tool `literature-search`; only verified records go into
  `01_case/similar-cases.csv`.
- `python "${CLAUDE_PLUGIN_ROOT}/scripts/case_lint.py" .` until no block; fix by rewriting, never by deleting facts.

## 3. Lock
The author locks the facts (`gate.py lock . G3 --by "<name>" --files ledgers/results-ledger.json 01_case/facts.csv 01_case/similar-cases.csv`).
Never lock it yourself. Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/gate.py" check . G3` before drafting.

## 4. Draft
Before each part read its role brief: `${CLAUDE_PLUGIN_ROOT}/references/writing/roles/case-front.md`,
`${CLAUDE_PLUGIN_ROOT}/references/writing/roles/case-presentation.md`,
`${CLAUDE_PLUGIN_ROOT}/references/writing/roles/case-discussion.md` (a subagent gets the whole brief first; its first
line is how the hook checks G3). Files `06_writing/case-report/NN-*.md`; BMJ mode (`target.journal_style: bmj`)
uses BMJ headings and 3–5 learning points. Values only as `{{R-A0-…}}`; citations only `[@id]`; author-only facts as
`[[AUTHOR: …]]`.

## 5. Review, assemble, audit, export
- Reviewer agents in parallel (deliverable `case-report`), then
  `python "${CLAUDE_PLUGIN_ROOT}/scripts/worklog.py" score . case-report --round N` (at most 3 rounds; KEEP, REVERT
  and STOP as in `thesis-writing`).
- `python "${CLAUDE_PLUGIN_ROOT}/scripts/assemble.py" . case-report`, then
  `python "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" . case-report`; report each block, fix mechanical ones.
- With 0 blocks and consent recorded, only the author opens G4 (`gate.py open . G4 --by "<name>"`); then
  `python "${CLAUDE_PLUGIN_ROOT}/scripts/assemble.py" . case-report --final` writes `out/case-report.docx`.
- Draft `out/ai-use-disclosure.md` from `${CLAUDE_PLUGIN_ROOT}/references/writing/ai-disclosure.md` (never marked
  final), run `python "${CLAUDE_PLUGIN_ROOT}/scripts/worklog.py" decisions .`, and report in the user's language.
