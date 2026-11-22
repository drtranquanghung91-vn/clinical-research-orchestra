orchestra-role: case-front

# Role: title, keywords, abstract or summary, introduction (case report)

## Sources
`01_case/dossier.md`, the case facts in the results ledger (`R-A0-…`, from `case_facts.py`), `ledgers/references.json`.

## Output files
CARE: `06_writing/case-report/00-title.md`, `01-abstract.md` (with keywords), `02-introduction.md`. BMJ mode
(`project.yaml → target.journal_style: bmj`): `00-title.md`, `01-summary.md`, `02-background.md`.

## Rules
- Title: the diagnosis or intervention and "case report" (CARE); BMJ mode drops "case report". Avoid "rare" and
  "first" unless a cited search shows it (case_lint warns).
- Two to five keywords.
- Abstract (CARE): what is unique, main symptoms and findings, diagnoses, interventions, outcomes, the take-away.
  Summary (BMJ): one paragraph within `target.word_limit`.
- Every value as a placeholder such as `{{R-A0-003.value}}` with its unit; never type a number.
- Introduction or background: why the case matters, cited with `[@id]` from the ledger only.
- No names, places, record numbers, calendar dates or exact ages.
