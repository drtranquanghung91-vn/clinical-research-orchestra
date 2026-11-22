---
name: thesis-writing
description: 'Use when the user wants the thesis written, finished, reviewed or assembled from locked results. Triggers: "viết luận văn", "viết tiếp luận văn", "viết chương 2 sau khi khoá kết quả", "chương 4 bàn luận", "viết bàn luận", "kết luận và kiến nghị", "đặt vấn đề luận văn", "ghép luận văn", "xuất file luận văn", "write my thesis", "discussion chapter", "assemble the thesis", "thesis docx".'
---

# Thesis writing

Writes the thesis from locked results, has it reviewed by read-only agents and exports it only through gate G4.
Detail: `${CLAUDE_PLUGIN_ROOT}/references/workflows/thesis.md`;
structure: `${CLAUDE_PLUGIN_ROOT}/references/writing/vn-thesis.md`.

## 1. Gate
Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/gate.py" check . G3`. Not `G3: open` → stop: draft nothing, explain
that the thesis is written from results the author has accepted and locked, and give the lock step: the author
reads `05_analysis/analysis-report.rendered.md`, then runs `gate.py lock . G3 --by "<name>" --files …` (see
`statistical-analysis`). Never lock it yourself.

## 2. Outline
Add one `section_plan` entry per thesis section to `ledgers/outline.json` (`deliverable: thesis`, `file`, `role`,
`sources`, `results`, `status`). Reuse Chương 1 and Chương 3 only when `STATUS.md` or `decisions.md` records the author's acceptance;
otherwise ask about them inside the one outline confirmation question.

## 3. Draft
Before each section read `${CLAUDE_PLUGIN_ROOT}/references/writing/roles/<role>.md`. Draft in this thread, or
brief a general-purpose subagent with the whole role brief at the top of its prompt (its first line
`orchestra-role: <role>` is how the gate hook checks G3). Files in `06_writing/thesis/`: `00-dat-van-de.md`,
`ch2-methods.md`, `ch4-discussion.md`, `05-ket-luan.md`, `06-kien-nghi.md`, `90-phu-luc.md`. Numbers only as
`{{R-…}}` placeholders, `<!-- derived: … -->` or `<!-- not-a-result: … -->`; citations only `[@id]` from `ledgers/references.json`;
captions "Bảng c.n." above tables, "Hình c.n."/"Biểu đồ c.n." below figures. Never type a number or a reference
from memory; author-only facts go in `[[TÁC GIẢ: …]]`; ask the author to fill each, never fill them yourself. Never run a new
analysis.

## 4. Review and revise (at most 3 rounds)
Each round, in parallel, dispatch `citation-verifier`, `statistical-reviewer`, `reporting-guideline-checker`,
`scientific-editor` and `consistency-auditor` with the project, the deliverable `thesis` and no role brief, then
run `python "${CLAUDE_PLUGIN_ROOT}/scripts/worklog.py" score . thesis --round N`; its last line decides. Exit 2:
read stderr, rerun the named reviewer (or the guideline checker for a missing checklist), score the same N again;
never raise N after a failed score.
- `KEEP`: fix the findings, next round.
- `REVERT`: `python "${CLAUDE_PLUGIN_ROOT}/scripts/worklog.py" revert . thesis`; the loop stops.
- `STOP`: the loop stops.
A request for a new analysis (`NEW-ANALYSIS:`) never enters the text: it goes to `out/author-decisions.md`.
Findings on reused chapters: fix only mechanical E-FMT/E-NUM issues; send the rest to the author.

## 5. Humanize
After the last content round use the Skill tool with `prose-humanizer` on each section you drafted (not reused ones).

## 6. Assemble, audit, export
1. `python "${CLAUDE_PLUGIN_ROOT}/scripts/assemble.py" . thesis`; fix every block.
2. `python "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" . thesis`; explain each block, fix, rerun. Never change a
   reference status or a ledger to pass.
3. With 0 blocks, only the author opens G4: `gate.py open . G4 --by "<name>"` (the deliverable comes from the
   audit). Run it only when the author says so in this conversation and gives the name. Never write a `WAIVE` line.
4. `python "${CLAUDE_PLUGIN_ROOT}/scripts/assemble.py" . thesis --final` → `out/thesis.docx`.

## 7. Close
Draft `out/ai-use-disclosure.md` from `${CLAUDE_PLUGIN_ROOT}/references/writing/ai-disclosure.md` (never marked
final), run `python "${CLAUDE_PLUGIN_ROOT}/scripts/worklog.py" decisions .` (writes `out/author-decisions.md`), update `STATUS.md` row 6. Report
the paths and the open questions in the user's language.
