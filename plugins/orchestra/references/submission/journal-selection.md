# Journal selection: facts, signals and the author's choice

Used by the skill `journal-selection`. Nothing here is a fact about any journal: facts come from
`journal_check.py` lookups (NLM Catalog, DOAJ, Crossref) and from the journal's own pages, each recorded with
its URL and date in `08_submission/journals.json`.

## Building the shortlist
1. Candidates: journals that published the studies the manuscript cites (from `ledgers/references.json`), the
   author's suggestions, and journals named in an invitation the author received. Never a journal "known" from
   memory without a lookup.
2. `journal_check.py . lookup <ISSN or title> …` for each. Add `--claim medline` or `--claim scopus` when the
   journal's site or an invitation claims that indexing, `--open-access` when it presents itself as open access,
   and `--concern "<text>"` for each concern the author states.
3. Read each journal's own aims-and-scope and instructions-for-authors pages (WebFetch). Record what was read
   with `journal_check.py . note <key> --source-url <URL> [--scope "<one line>" --scope-url <URL>] [--words N]
   [--abstract N] [--ref-style "<style>"]`. A limit not found on the page is not noted (never guessed).
4. `journal_check.py . table` rewrites `08_submission/journals.md`. The "Scope fit" column is one sentence by
   Claude, tied to the scope page it read.

## Signals, not verdicts
A signal is a fact with a source that deserves the author's attention: an ISSN no registry knows, an invalid
check digit, a claimed MEDLINE indexing the NLM Catalog does not confirm, a Scopus claim these open sources cannot
check, an open-access journal missing from DOAJ, publisher or title disagreeing across sources, or the author's
own concern. Report each with its source. Never call a journal predatory, fake or a scam, in any language; point
the author to the Think. Check. Submit. checklist (https://thinkchecksubmit.org/) and let them decide.

## Picking
Only the author picks. After the author names the journal in the conversation, run
`journal_check.py . pick <key> --by "<author name>"`: it writes `target.journal`, `target.word_limit` (abstract)
and `target.text_words` (main text) in `project.yaml`. The reference style is shown in `journals.md`; changing
`citation_style` is a separate decision the author makes. Never pick for the author, even when asked to "just
choose": present the table and ask.
