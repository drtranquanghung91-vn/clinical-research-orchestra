# Workflow: reviewer response

Detail for the `reviewer-response` skill. Run from the project folder. `<d>` is `manuscript`, `case-report` or
`review` (`response.py init --deliverable`).

## 1. Init
Paste the decision letter into `09_revision/comments-received.md` (fictional examples are labelled). Then
`response.py . init 09_revision/comments-received.md --deliverable <d>`: items `E1…`, `R1.1…` in
`09_revision/comments.json`; the submitted drafts copied to `09_revision/submitted/` with their sha256. It needs G4
open for `<d>` (the drafts are the approved, submitted version); `--unapproved` only on the author's word.

## 2. response.md
```
# Response to reviewers

## R1.1
> The exclusion criteria are unclear.

We have clarified the exclusion criteria in the Methods.
[[CHANGE: 06_writing/manuscript/03-methods.md | "Patients transferred from another hospital were excluded."]]

## R1.2
> Please add a subgroup analysis by sex.

NEW-ANALYSIS: subgroup analysis of A1 by sex, requested by Reviewer 1
```
The quote in a CHANGE locator is the exact new text (whitespace may differ). Numbers only as `{{R-…}}`.

## 3. Check rules (E-RESP)
Block: an item without a response; an id not in comments.json; a CHANGE file not in the project; a quote not in the
current draft; a quote already in the submitted snapshot; "we have revised/added/clarified …" without a locator; an
open `NEW-ANALYSIS:` line. E-NUM block: a number not in the results ledger (item ids and page/line references are
ignored). Warn: no change and no "no change because …".

## 4. New analyses
A reviewer's request for an analysis never runs during the response. The author decides: accepted → `POST-HOC
A<n>: <what>, requested by Reviewer <n>, <date>` in `decisions.md`, then `statistical-analysis` and the ledger;
the response cites the new `{{R-A<n>-…}}`. Declined → "No change because …" with the reason (for example not
pre-specified, underpowered).

## 5. Export
`assemble.py . <d>`, `audit.py . <d>` to 0 blocks (no internal reviewer round: the worklog keeps the submitted
version's rounds, and the E-REV warnings that the agents saw that version are expected), the author opens G4,
`assemble.py . <d> --final`, then `response.py . build` → `out/response-letter.docx` (comments, responses, each
change with its section name). The hook and `build_docx.py` refuse `out/response-letter.docx` while G4 is closed or
`response.py check` has a block.
