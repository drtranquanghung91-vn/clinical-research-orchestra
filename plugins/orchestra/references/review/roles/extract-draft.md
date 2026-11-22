orchestra-prep: extract-draft

# Brief: draft data extraction (AI, never an extractor)

## Input
The protocol's data items and extraction form (`03_protocol/sr-protocol.md`), the included studies' full text the
author provides, and the columns `study_id,outcome,timepoint,group,n,events,mean,sd,es,se` plus the protocol's own.

## Output
- One file: `reviews/tmp/extraction-draft.csv` with those columns and a `quote` column: the exact sentence or
  table cell with its page (`p. 5, Table 2`).
- Never write `04_data/sr/extraction-<reviewer>.csv` or `04_data/sr/extraction.csv`: each human extractor fills
  their own file independently, and may look at the draft only after their own pass if the protocol allows it.

## Rules
- Copy numbers exactly as printed; never compute, convert or impute. A value not reported is left blank with
  "not reported" in `quote`.
- One row per study, outcome, timepoint and group.
