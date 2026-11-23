---
name: journal-selection
description: 'Use when the author is choosing where to submit a manuscript, case report or review, or asks whether a journal is indexed, open access or trustworthy. Triggers: "chọn tạp chí", "nộp bài ở đâu", "tạp chí nào phù hợp", "tạp chí này có uy tín không", "tạp chí săn mồi", "tạp chí có trong MEDLINE không", "phí đăng bài", "email mời nộp bài", "which journal", "where should I submit", "journal shortlist", "is this journal indexed", "predatory journal", "APC".'
---

# Journal selection

Builds a shortlist from tool lookups, reports signals with their sources and records the author's choice. Never
submits anything. Detail: `${CLAUDE_PLUGIN_ROOT}/references/workflows/journal-selection.md` and
`${CLAUDE_PLUGIN_ROOT}/references/submission/journal-selection.md`.

## 1. Candidates
Journals that published the studies the manuscript cites (`ledgers/references.json`), the author's suggestions,
and any invitation the author received. Never a journal, or a fact about one, from memory.

## 2. Look up
`python "${CLAUDE_PLUGIN_ROOT}/scripts/journal_check.py" . lookup <ISSN or title> --claim medline --open-access --concern "<text>"`
with `--claim medline` or `--claim scopus` only when the journal or an invitation claims that indexing,
`--open-access` when it presents itself as open access, one `--concern` per concern the author states. Exit 2 = a
source could not be reached: say so and retry later; never fill the gap from memory.

## 3. The journal's own pages
Read the aims-and-scope and instructions-for-authors pages, then
`python "${CLAUDE_PLUGIN_ROOT}/scripts/journal_check.py" . note <key> --source-url <URL> --scope "<one line>" --scope-url <URL> --words N --abstract N --ref-style "<style>"`
with only what the pages state. A limit you did not find is not noted.

## 4. Present
`python "${CLAUDE_PLUGIN_ROOT}/scripts/journal_check.py" . table` writes `08_submission/journals.md`. Show it in
the user's language: indexing, open access and APC as looked up (source and date), limits, reference style, one
sentence on scope fit, and every signal with its source. Signals are facts to weigh, not a verdict: never call a
journal predatory, fake or a scam, in any language, even when asked; point to Think. Check. Submit.
(https://thinkchecksubmit.org/) and say the decision is the author's.

## 5. The author picks
Only after the author names the journal:
`python "${CLAUDE_PLUGIN_ROOT}/scripts/journal_check.py" . pick <key> --by "<author name>"` (writes
`target.journal`, `target.word_limit`, `target.text_words`). Never pick for the author, even when told to just
choose; never edit `project.yaml` by hand. Then tell the author the limits `manuscript-writing` will now use and
the journal's reference style.

## Rules
- ISSN, indexing, APC and publisher only from `journal_check.py` records, never typed.
- Never submit, register or email anything.
