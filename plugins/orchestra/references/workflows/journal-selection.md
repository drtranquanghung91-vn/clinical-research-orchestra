# Workflow: journal selection

Detail for the `journal-selection` skill; background and wording rules in
`references/submission/journal-selection.md`. Run from the project folder. Outputs:
`08_submission/journals.json`, `08_submission/journals.md`; after the author's pick, `project.yaml → target.*`.

1. Candidates (3–6): journals of the cited studies (`ledgers/references.json` → `journal`), the author's list, any
   invitation the author received. Write nothing about a journal before its lookup.
2. `journal_check.py . lookup <ISSN or title> …` per candidate, with `--claim medline|scopus`, `--open-access`
   and `--concern "<text>"` as the journal's claims and the author's concerns require. Exit 2 = network or API
   error: report it, retry later; never fill a field by hand.
3. For each candidate read the aims-and-scope and author-instructions pages (WebFetch); record with
   `journal_check.py . note <key> --source-url <URL> …` only what they state (scope line, word limit, abstract
   limit, reference style).
4. `journal_check.py . table`; show `journals.md`. One sentence of scope fit per journal, tied to the page read.
   Signals with sources; never a verdict word; Think. Check. Submit. for the author's own check.
5. The author picks in the conversation; then `journal_check.py . pick <key> --by "<name>"`. Never pick for
   the author.

| Failure | Fix |
|---|---|
| APC or indexing typed from memory | rerun the lookup; only recorded values |
| "This journal is predatory" | list the signals with sources; the author decides |
| `target.journal` written before the author chose | revert `project.yaml`; pick only after the author names it |
