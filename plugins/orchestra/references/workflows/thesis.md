# Workflow: thesis writing

Detail for the `thesis-writing` skill. Run every command from the project folder; scripts are in
`${CLAUDE_PLUGIN_ROOT}/scripts/`. Structure and numbering rules: `references/writing/vn-thesis.md`.

## 1. Outline entries (`ledgers/outline.json → section_plan`)
One object per section, always with `"deliverable"` (decision D18). Entries of the P1 literature review have no
`deliverable` and stay untouched.

```json
{"deliverable": "thesis", "file": "06_writing/thesis/ch4-discussion.md", "role": "discussion",
 "sources": ["ledgers/references.json"], "results": ["R-A1-004"], "status": "reuse|draft|drafted|accepted"}
```
`reuse` = an accepted file the thesis takes as it is; `draft` = to write; `drafted` = written, not yet accepted;
`accepted` = the author accepted it. The author confirms the outline once.

## 2. Role, section, file
| Role brief (`references/writing/roles/`) | Section | File in `06_writing/thesis/` |
|---|---|---|
| `abstract` | Tóm tắt (optional) | `00-tom-tat.md` |
| `introduction` | Đặt vấn đề | `00-dat-van-de.md` |
| (from `literature-review`) | Chương 1 Tổng quan tài liệu | `ch1-*.md` |
| `methods` | Chương 2 Đối tượng và phương pháp | `ch2-methods.md` |
| `results` (from `results-writing`) | Chương 3 Kết quả | `ch3-results.md` |
| `discussion` | Chương 4 Bàn luận | `ch4-discussion.md` |
| `conclusion` | Kết luận | `05-ket-luan.md` |
| `conclusion` | Kiến nghị | `06-kien-nghi.md` |
| none | Phụ lục (checklist, CRF, data dictionary) | `90-phu-luc.md` |

## 3. Reuse and "just do it"
- Reuse Chương 1 and Chương 3 only when `STATUS.md` or `decisions.md` records the author's acceptance; else ask
  about them inside the single outline confirmation question. Reused chapters are not rewritten and not
  humanized: apply only mechanical E-FMT and E-NUM fixes; send every other finding to the author through
  `out/author-decisions.md`.
- Edit only the sections you drafted in this run. A chapter the author wrote and has not accepted (for example their own Chapter 3) is never edited, even for a reviewer finding: list the finding for the author.
- If the user says not to ask, proceed with defaults and open the first drafted file with an
  **Giả định / Assumptions** box; record the same text in `decisions.md`. It never opens or locks a gate and never
  changes a ledger.

## 4. Subagent brief for one section
1. The whole role brief, copied first; its first line `orchestra-role: <role>` stays the first line of the prompt.
2. Then: project path, deliverable `thesis`, target file, the outline entry, "write only that file; numbers
   only as placeholders; citations only `[@id]` from `ledgers/references.json`; author-only facts as
   `[[TÁC GIẢ: …]]`".
If G3 is not open the hook denies the prompt; do not retry, tell the author.

## 5. Review dispatch (parallel, one prompt per agent)
Agents: `citation-verifier`, `statistical-reviewer`, `reporting-guideline-checker`, `scientific-editor`,
`consistency-auditor`. Prompt: the project path, deliverable `thesis`, "run
`python "${CLAUDE_PLUGIN_ROOT}/scripts/worklog.py" digest . thesis` first; end the report with the
`drafts-digest:` line and the `scores` block". Never put a role brief in a reviewer prompt. Each agent returns its report in its reply (agents write no files); save it unchanged to `reviews/<agent>-thesis.md` (`reviews/consistency-thesis.md` for the consistency auditor) and the guideline checker's `checklist` block to `reviews/guideline-checklist-thesis.json`. Full procedure: `references/writing/review-round.md`.

## 6. Revise loop
| Round | Reviewers | Score | Decision | Action |
|---|---|---|---|---|
| 1 | all five | `worklog.py score . thesis --round 1` | KEEP | fix findings, round 2 |
| 2 | all five on the fixed drafts | `--round 2` | KEEP | fix, round 3 |
| 3 | all five | `--round 3` | any | stop (never a round 4) |
| any | | | REVERT | `worklog.py revert . thesis` restores the last kept round exactly; stop |
| any | | | STOP | stop |

One round = one pass of the five reviewers followed by exactly one score; never rerun reviewers without scoring the round (the audit warns on unscored reports).

Higher total keeps; lower reverts; equal with a lost criterion reverts; equal without a loss stops; 16/16 stops.
A `NEW-ANALYSIS:` request goes to `out/author-decisions.md`, never into the text; never run a new analysis.
`worklog.py score` exit 2 (nothing recorded): read stderr, rerun the named reviewer (a missing checklist: rerun
`reporting-guideline-checker`), then score the same round N again; never increase N after a failed score.

## 7. Humanize
After the last content round, `prose-humanizer` on each drafted section (invariants checked per paragraph:
numbers, `[@id]`, placeholders, captions). The drafts then differ from what the reviewers saw: `E-REV` warns
only; do not rerun the loop.

## 8. Assemble
`assemble.py . thesis` reads `06_writing/thesis/order.txt` (file names or globs, one per line, `#` comments) or
the default order. It inserts `**MỤC LỤC**`, `{TOC}` and a page break at the top unless a section already has
`{TOC}` (D12); the single numbered reference list goes before the first appendix file (`9*`), else at the end.
Images: `07_present/figures/F<n>.png`, PNG only. It writes `thesis.assembled.md` and `thesis.draft.docx` (draft
notice first); a block lists file:line.

## 9. Audit fixes by code
| Code | Fix |
|---|---|
| `E-REF` | `verify_refs.py --write`, a verified replacement, or `search_lit.py add-manual`; never edit a status |
| `E-NUM` | `{{R-…}}` placeholder, or `<!-- not-a-result: … -->` |
| `E-STAT` | declare the post-hoc analysis or deviation in `decisions.md`, or label it |
| `E-LIT` | rewrite Chương 1 by theme |
| `E-CONS` | decide the right source (ledger first), align the rest |
| `P00` | `prose-humanizer` |
| `E-RG` | add the guideline item or record why it does not apply; rerun `reporting-guideline-checker` |
| `E-FMT` | missing section, caption numbers, image; ask the author to fill each `[[TÁC GIẢ: …]]` (ethics numbers, funding, affiliations, dates): never fill it yourself |
| `E-PHI` | remove the identifier; never print it back |
| `E-REV` | rerun the reviewer on the current drafts |

## 10. G4 and the final export
G4 is per deliverable (D2): the author runs `gate.py open . G4 --by "<name>"` after `audit.py . thesis` is clean;
the deliverable comes from `reviews/audit.json` (`--deliverable` exists only on `check`). Reopening it for the manuscript keeps the thesis lock. Then
`assemble.py . thesis --final` writes `out/thesis.docx` without the draft notice. While G4 is closed the hook
denies any final export with the message "is a final export and cannot run … Run /orchestra:audit, fix every
block, then the author opens G4": show it and stop. A file changed after the audit reopens the problem: rerun
`audit.py . thesis`.

## 11. Close
- `out/ai-use-disclosure.md` from `references/writing/ai-disclosure.md`, never marked final.
- `worklog.py decisions .` writes `out/author-decisions.md` (exit 1 with a `.new.md` when the author edited it).
- `STATUS.md` row 6 `Writing`: `doing` while drafting; `done` only after both exports exist or the author says so.
- Tell the author: the paths of `out/thesis.docx`, `reviews/audit.md`, the disclosure and the decisions file;
  the `[[TÁC GIẢ: …]]` still open; the Vancouver-only and institution-order limitation.
