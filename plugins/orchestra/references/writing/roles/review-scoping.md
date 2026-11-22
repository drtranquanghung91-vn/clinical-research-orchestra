orchestra-role: review-scoping

# Role: methods and results of a scoping review (PRISMA-ScR)

## Sources
The locked protocol (PCC), strings and search log, the PRISMA counts (`R-A0-…`), `04_data/sr/charting.csv`,
`ledgers/references.json`.

## Output files
`06_writing/review/03-methods.md`, `04-results.md`.

## Rules
- Methods: protocol and registration, eligibility (PCC), sources and dates, full strings, selection by two
  reviewers, charting by one reviewer verified by a second (`verified_by`), data items, how charted data were
  summarised. Critical appraisal is optional in PRISMA-ScR; this project does none: no risk of bias.
- Results: the flow with counts `{{R-A0-001.value}}` …, characteristics of sources, charted data organised by
  the review questions (tables of concepts, settings, designs), citations `[@id]`.
- no pooled estimate, no effect size, no certainty rating: a request for them is a systematic review question
  (tell the author; offer to convert the protocol).
