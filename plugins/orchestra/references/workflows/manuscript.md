# Workflow: manuscript writing

Detail for the `manuscript-writing` skill. Run every command from the project folder; scripts are in
`${CLAUDE_PLUGIN_ROOT}/scripts/`. Structure and declarations: `references/writing/manuscript.md`.

## 1. Outline entries (`ledgers/outline.json → section_plan`)
One object per section, always with `"deliverable"` (decision D18); P1 entries without it stay untouched.

```json
{"deliverable": "manuscript", "file": "06_writing/manuscript/05-discussion.md", "role": "discussion",
 "sources": ["ledgers/references.json"], "results": ["R-A1-004"], "status": "reuse|draft|drafted|accepted"}
```
The author confirms the outline once.

## 2. Role, section, file
| Role brief (`references/writing/roles/`) | Section | File in `06_writing/manuscript/` |
|---|---|---|
| none | Title page | `00-title.md` |
| `abstract` (written last) | Structured abstract | `01-abstract.md` |
| `introduction` (or `literature-review` mode b) | Introduction | `02-introduction.md` |
| `methods` | Methods | `03-methods.md` |
| `results` (or `results-writing`) | Results | `04-results.md` |
| `discussion` | Discussion | `05-discussion.md` |
| `conclusion` | Conclusion | `06-conclusion.md` |

## 3. Title page, journal questions, word counts
- `00-title.md`: title naming the design, running title, keywords; authors, affiliations, corresponding author,
  funding and the declarations as `[[AUTHOR: …]]` placeholders. Never invent them.
- Ask the author once: target journal, abstract headings, word limits, limit on tables and figures, reference
  style. This pipeline renders Vancouver only; another style is reported as a limitation.
- Count with `python "${CLAUDE_PLUGIN_ROOT}/scripts/lint_prose.py" --count-words <file>`: the abstract against
  `target.word_limit` (default 250), the main text against `target.text_words` (null or missing: ask the author once, D20). Write the numbers in the title
  page as plain text only after counting.

## 4. Reuse and "just do it"
- Reuse `02-introduction.md` (`literature-review`) and `04-results.md` (`results-writing`) only when `STATUS.md` or
  `decisions.md` records acceptance; else ask inside the single outline confirmation. Reused files are not
  rewritten or humanized: apply only mechanical E-FMT and E-NUM fixes; other findings go to the author through
  `out/author-decisions.md`.
- If the user says not to ask, proceed with defaults, open the first drafted file with a
  **Giả định / Assumptions** box and record it in `decisions.md`. It never opens or locks a gate or changes a ledger.

## 5. Subagent brief for one section
1. The whole role brief first; its first line `orchestra-role: <role>` stays the first line of the prompt.
2. Then: project path, deliverable `manuscript`, target file, the outline entry, "write only that file; numbers
   only as placeholders; citations only `[@id]`; author-only facts as `[[AUTHOR: …]]`".
If G3 is not open the hook denies the prompt; do not retry, tell the author.

## 6. Review dispatch (parallel, one prompt per agent)
Agents: `citation-verifier`, `statistical-reviewer`, `reporting-guideline-checker`, `scientific-editor`,
`consistency-auditor`. Prompt: the project path, deliverable `manuscript`, "run
`python "${CLAUDE_PLUGIN_ROOT}/scripts/worklog.py" digest . manuscript` first; end the report with the
`drafts-digest:` line and the `scores` block". Never put a role brief in a reviewer prompt. Reports land in
`reviews/<agent>.md` (consistency: `reviews/consistency.md`); the guideline checker also writes
`reviews/guideline-checklist.json`.

## 7. Revise loop
| Round | Reviewers | Score | Decision | Action |
|---|---|---|---|---|
| 1 | all five | `worklog.py score . manuscript --round 1` | KEEP | fix findings, round 2 |
| 2 | all five on the fixed drafts | `--round 2` | KEEP | fix, round 3 |
| 3 | all five | `--round 3` | any | stop (never a round 4) |
| any | | | REVERT | `worklog.py revert . manuscript` restores the last kept round exactly; stop |
| any | | | STOP | stop |

A `NEW-ANALYSIS:` request goes to `out/author-decisions.md`, never into the text; never run a new analysis.
`worklog.py score` exit 2: read stderr, rerun the named reviewer (a missing checklist: rerun
`reporting-guideline-checker`), then score the same round N again; never increase N after a failed score.

## 8. Humanize
After the last content round, `prose-humanizer` on each drafted section (invariants per paragraph). Reviewers'
digest then differs: `E-REV` warns only. Recount the words afterwards.

## 9. Assemble
`assemble.py . manuscript` reads `06_writing/manuscript/order.txt` or the default order. Tables and figures are
numbered across the paper ("Table 1", "Figure 1"; Bảng 1, Hình 1 in Vietnamese). Page breaks only after the
title page, after the abstract and before References, which close the text (D12). Images:
`07_present/figures/F<n>.png`. English text in a `vi` project: `target.language: en` and
`assemble.py . manuscript --lang en`.

## 10. Audit fixes by code
| Code | Fix |
|---|---|
| `E-REF` | `verify_refs.py --write`, a verified replacement, or `search_lit.py add-manual` |
| `E-NUM` | `{{R-…}}` placeholder, or `<!-- not-a-result: … -->` |
| `E-STAT` | declare in `decisions.md` or label as post-hoc / deviation |
| `E-LIT` | rewrite the Introduction by theme |
| `E-CONS` | decide the right source (ledger first), align the rest |
| `P00` | `prose-humanizer` |
| `E-RG` | add the guideline item or record why it does not apply |
| `E-FMT` | missing section, caption numbers, image; ask the author to fill each `[[AUTHOR: …]]` (ethics numbers, funding, affiliations, dates): never fill it yourself |
| `E-PHI` | remove the identifier; never print it back |
| `E-REV` | rerun the reviewer on the current drafts |

## 11. G4 and the final export
The author runs `gate.py open . G4 --by "<name>"` after `audit.py . manuscript` has 0 blocks (the deliverable
comes from `reviews/audit.json`; `--deliverable` exists only on `check`); the thesis lock is kept (D2). Then `assemble.py . manuscript --final` writes `out/manuscript.docx`. While
G4 is closed the hook denies the export with "is a final export and cannot run … the author opens G4": show it and
stop. A change after the audit needs `audit.py . manuscript` again.

## 12. Close
- `out/ai-use-disclosure.md` from `references/writing/ai-disclosure.md`, never marked final; the journal's own
  AI-use statement is the author's call.
- `worklog.py decisions .` writes `out/author-decisions.md`.
- `STATUS.md` row 6 `Writing`: `done` only after both exports exist or the author says so.
- Tell the author: the paths, the open `[[AUTHOR: …]]` declarations, the journal limits not met, and the
  Vancouver-only limitation.
