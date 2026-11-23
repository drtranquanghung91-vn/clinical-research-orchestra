# Review round (writing skills)

Used by `thesis-writing`, `manuscript-writing`, `case-report` and `systematic-review`; `<d>` is the deliverable
(`thesis`, `manuscript`, `case-report`, `review`). One round costs five agent runs; a pass that is not scored is
wasted, and the audit warns about every report newer than the last scored round.

## One round
1. `python "${CLAUDE_PLUGIN_ROOT}/scripts/worklog.py" digest . <d>` must exit 0.
2. Dispatch in parallel, one Agent call each and no role brief: `citation-verifier`, `statistical-reviewer`,
   `reporting-guideline-checker`, `scientific-editor`, `consistency-auditor`. Prompt: the project path, the
   deliverable `<d>`, "run `worklog.py digest . <d>` first; end the report with the `drafts-digest:` line and the
   `scores` block; return everything in your reply and write no file".
3. Save each reply unchanged, from its `STATUS:` line to the closing fence of its `scores` block, to
   `reviews/<agent>-<d>.md` (the consistency auditor: `reviews/consistency-<d>.md`). The guideline checker's reply
   starts with a ```` ```checklist ```` block: save that JSON to `reviews/guideline-checklist-<d>.json` and the rest
   to `reviews/reporting-guideline-checker-<d>.md`. The agents have no write access (the checker validates its
   checklist with `guideline_checklist.py . --deliverable <d> --stdin`); you write these files and change nothing
   in them.
4. Exactly one `python "${CLAUDE_PLUGIN_ROOT}/scripts/worklog.py" score . <d> --round N`, before any fix.
   Exit 2 (nothing recorded): read stderr, rerun only the named reviewer (a missing checklist: the guideline
   checker), save its reply, score the same N again. Never raise N after a failed score, and never rerun all five
   reviewers without scoring the round.

## Decisions

| Last line of the score | Action |
|---|---|
| `KEEP` | fix the findings in the sections you may edit (below), then round N + 1 |
| `REVERT` | `worklog.py revert . <d>` restores the last kept round exactly; the loop stops |
| `STOP` | the loop stops |

At most 3 rounds; never a round 4. After the last round, `prose-humanizer` may change wording: the reviewers then
saw an earlier version (E-REV warns); do not start another round for that.

## What you may edit
- Sections you drafted in this run: fix the findings.
- A reused section the author accepted (outline status `reuse` or `accepted`): mechanical E-FMT and E-NUM fixes only.
- Any other file the author wrote and has not accepted (for example the author's own Chapter 3): never edit it;
  list its findings for the author in your answer and in `out/author-decisions.md`.
- `NEW-ANALYSIS:` requests go to `out/author-decisions.md`, never into the text; never run a new analysis.

## Cost
One scored round per reviewer pass keeps a deliverable at three passes of five agents at most. If an agent gives
no reply for a long time, stop the round, tell the author, and do not start a new pass on your own.
