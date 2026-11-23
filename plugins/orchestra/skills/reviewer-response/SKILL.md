---
name: reviewer-response
description: 'Use when a manuscript, case report or review came back from a journal with editor or reviewer comments and the author needs a revised version and a response letter. Triggers: "trả lời phản biện", "thư trả lời phản biện", "sửa bài theo phản biện", "nhận xét của reviewer", "tạp chí yêu cầu chỉnh sửa", "major revision", "minor revision", "response to reviewers", "rebuttal letter", "reviewer comments", "revise and resubmit".'
---

# Reviewer response

Splits the comments, revises the drafts, writes a response whose every claimed change is checked against the text,
and exports `out/response-letter.docx` only through G4. Detail:
`${CLAUDE_PLUGIN_ROOT}/references/workflows/reviewer-response.md`.

## 1. Start
Save the pasted comments to `09_revision/comments-received.md`, then
`python "${CLAUDE_PLUGIN_ROOT}/scripts/response.py" . init 09_revision/comments-received.md --deliverable manuscript`
(or `case-report`, `review`). Exit 1 because G4 is not open: ask whether these drafts are exactly what was
submitted, and add `--unapproved` only on the author's yes. Never init twice.

## 2. Plan with the author
List the items of `09_revision/comments.json`, each with a proposed answer: a change, no change (with the reason),
or a new analysis. A requested new analysis (subgroup, new model, new outcome) becomes a
`NEW-ANALYSIS: <what and why>` line under its item; never run it. If the author accepts it, it takes the P2 route
(`POST-HOC A<n>:` in `decisions.md`, then `statistical-analysis`); if not, write "No change because …".

## 3. Revise and respond
Edit the drafts in `06_writing/<d>/` (numbers only as `{{R-…}}`, citations only `[@id]` from the ledger). Write
`09_revision/response.md`: per item `## <id>`, the comment quoted with `>`, the response, and for each change
`[[CHANGE: 06_writing/<d>/<file> | "<exact new text>"]]`. Never claim a change you did not make ("we have
revised …" needs a locator), and never reword a claim away to pass the check: make the change, or say why not.

## 4. Check
`python "${CLAUDE_PLUGIN_ROOT}/scripts/response.py" . check` until no block: an item without a response, a change
that is not in the draft or was already in the submitted version, a claim without a locator, an open
`NEW-ANALYSIS:` line, a number not in the results ledger (E-NUM).

## 5. Audit and export
`python "${CLAUDE_PLUGIN_ROOT}/scripts/assemble.py" . <d>` and `python "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" . <d>`
until 0 blocks. The internal reviewer loop is not rerun: the journal's reviewers are this round's reviewers, so
E-REV warnings that the agents saw the submitted version are expected; say so. Only the author opens G4 (`gate.py open . G4 --by "<name>"`, run when the author says so and gives
the name). Then `python "${CLAUDE_PLUGIN_ROOT}/scripts/assemble.py" . <d> --final` and
`python "${CLAUDE_PLUGIN_ROOT}/scripts/response.py" . build` write the revised document and
`out/response-letter.docx`. Never submit anything; report the paths in the user's language.
