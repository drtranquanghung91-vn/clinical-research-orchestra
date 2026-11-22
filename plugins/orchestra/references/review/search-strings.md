# Search strings and the search log (PRISMA-S)

`02_evidence/sr/strings.md` has one block per source: heading `## <database> (<platform>)`, string id (`S1`, `S2`,
…), the full string, limits, and the date it was last run. Build the concepts from the nomenclature check of the
`literature-search` skill (current and older terms, MeSH and free text).

- PubMed: run with `search_lit.py` (the only source a tool runs); MeSH `[mh]`, free text `[tiab]`.
- Embase (Ovid), CENTRAL, Scopus, Web of Science, CINAHL, ClinicalTrials.gov, WHO ICTRP: write the string in that
  platform's syntax (Ovid `exp …/`, `.ti,ab.`; Scopus `TITLE-ABS-KEY()`; Web of Science `TS=`; CINAHL `MH`,
  `TI`/`AB`). The tools never run subscription databases; the author runs them and exports RIS or CSV.
- `02_evidence/sr/search-log.csv`: `database,platform,date_run,string_id,hits,export_file`, one row per run. The
  hits must equal the records `screening.py import` reads from that export (E-SCR warn otherwise).
- Report in the methods: every source with platform and date, the full strings (appendix), limits, and the count
  per source (PRISMA-S; the counts come from the ledger, `{{R-A0-021}}` onward).
