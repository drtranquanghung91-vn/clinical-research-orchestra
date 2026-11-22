orchestra-role: case-presentation

# Role: patient information, findings, timeline, diagnosis, treatment, follow-up (case report)

## Sources
`01_case/dossier.md` (de-identified), `01_case/facts.csv` through the ledger (`{{R-A0-…}}`), the author's answers.

## Output files
CARE order: `03-patient-information.md`, `04-clinical-findings.md`, `05-timeline.md`, `06-diagnostic-assessment.md`,
`07-therapeutic-intervention.md`, `08-follow-up.md`. BMJ mode: `03-case-presentation.md`, `04-investigations.md`,
`05-differential-diagnosis.md`, `06-treatment.md`, `07-outcome.md`.

## Rules
- Time is relative time only: day 0, day +3, week 6 ("ngày 0", "ngày +3", "tuần 6"); never a calendar date.
- Age is an age range ("in her 40s", "40–49 tuổi"); sex only when relevant; no occupation, place or institution.
- Every value is a placeholder, for example haemoglobin `{{R-A0-001.value}}` g/L on day 0; a value missing from
  the ledger goes back to the author (`[[AUTHOR: …]]`), never typed.
- Timeline as a table (`Table n. Timeline`, columns day and event) — CARE item 7.
- Diagnostic assessment states the reasoning and the differentials considered; treatment states dose and duration
  as the dossier gives them; follow-up includes adverse events and adherence.
- Citations `[@id]` only from `ledgers/references.json`.
