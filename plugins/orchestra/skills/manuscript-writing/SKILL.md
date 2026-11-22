---
name: manuscript-writing
description: 'Use when the user wants a journal article written, reviewed or assembled from locked results. Triggers: "viết bài báo", "bản thảo bài báo", "gửi tạp chí", "bài báo khoa học", "tóm tắt có cấu trúc cho bài báo", "IMRaD", "write the manuscript", "journal article", "structured abstract", "submit to a journal", "paper draft".'
---

# Manuscript writing

Writes a journal manuscript from locked results; read-only agents review it; export only through gate G4.
See `${CLAUDE_PLUGIN_ROOT}/references/workflows/manuscript.md` and `references/writing/manuscript.md`.

## 1. Gate
Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/gate.py" check . G3`. Not `G3: open` → stop: draft nothing, explain
that the article is written from results the author accepted and locked, and give the lock step: the author
reads `05_analysis/analysis-report.rendered.md`, then runs `gate.py lock . G3 --by "<name>" --files …`. Never lock it yourself.

## 2. Journal and outline
Ask the author once: abstract headings, word limits (also when `target.text_words` is null or missing), reference
style (Vancouver only; anything else is a limitation); read `target.journal`. Add a `section_plan` entry per section to
`ledgers/outline.json` (`deliverable: manuscript`) and ask the author to confirm, including reuse of `02-introduction.md`/`04-results.md`.

## 3. Draft
Before each section read `${CLAUDE_PLUGIN_ROOT}/references/writing/roles/<role>.md`. Draft in this thread, or
brief a general-purpose subagent with the whole role brief at the top of its prompt (its first line
`orchestra-role: <role>` is how the gate hook checks G3). Files in `06_writing/manuscript/`: `00-title.md`,
`01-abstract.md`, `02-introduction.md`, `03-methods.md`, `04-results.md`, `05-discussion.md`,
`06-conclusion.md`. Reuse `02-introduction.md` (`literature-review` mode b) and `04-results.md` (`results-writing`) only when
`STATUS.md` or `decisions.md` records acceptance. Abstract last. Numbers only as `{{R-…}}`
placeholders, `<!-- derived: … -->` or `<!-- not-a-result: … -->`; citations only `[@id]`; declarations as
`[[AUTHOR: …]]`, which the author fills, never you. Never run a new analysis.
Count words with `python "${CLAUDE_PLUGIN_ROOT}/scripts/lint_prose.py" --count-words <file>` against
`target.word_limit` and `target.text_words`.

## 4. Review and revise (at most 3 rounds)
Each round, in parallel, dispatch `citation-verifier`, `statistical-reviewer`, `reporting-guideline-checker`,
`scientific-editor` and `consistency-auditor` with the project, the deliverable `manuscript` and no role brief,
then run `python "${CLAUDE_PLUGIN_ROOT}/scripts/worklog.py" score . manuscript --round N`; its last line decides.
Exit 2: read stderr, rerun the named reviewer, score the same N again; never raise N after a failed score.
- `KEEP`: fix the findings, next round.
- `REVERT`: `python "${CLAUDE_PLUGIN_ROOT}/scripts/worklog.py" revert . manuscript`; the loop stops.
- `STOP`: the loop stops.
A `NEW-ANALYSIS:` request goes to `out/author-decisions.md`, not the text. On reused sections fix only E-FMT/E-NUM
issues; send the rest to the author.

## 5. Humanize
After the last content round run `prose-humanizer` (Skill tool) on each section you drafted (not reused).

## 6. Assemble, audit, export
English in a `vi` project: `target.language: en` and `--lang en` on `assemble.py`.
1. `python "${CLAUDE_PLUGIN_ROOT}/scripts/assemble.py" . manuscript`; fix every block.
2. `python "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" . manuscript`; report each block, fix mechanical ones, rerun.
   E-REF is the author's call: verify, replace or record manually; never delete or reword the citing sentence,
   nor edit a reference status or ledger to pass.
3. With 0 blocks, only the author opens G4: `gate.py open . G4 --by "<name>"` (the deliverable comes from the
   audit). Run it only when the author says so and gives the name. Never write a `WAIVE` line.
4. `python "${CLAUDE_PLUGIN_ROOT}/scripts/assemble.py" . manuscript --final` → `out/manuscript.docx`.

## 7. Close
Draft `out/ai-use-disclosure.md` from `${CLAUDE_PLUGIN_ROOT}/references/writing/ai-disclosure.md` (never marked
final), run `python "${CLAUDE_PLUGIN_ROOT}/scripts/worklog.py" decisions .`, update `STATUS.md` row 6. Report paths and open questions in the user's language.
