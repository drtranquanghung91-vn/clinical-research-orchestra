orchestra-prep: screen-suggest

# Brief: screening suggestions (AI, never a reviewer)

You suggest; two human reviewers decide. Nothing you write is a screening decision.

## Input
- `02_evidence/sr/records.csv`: only records without `duplicate_of`; at full text, only the records the reviewers
  included at title/abstract (`screening.py . sheet --stage ft --reviewer "<name>"` lists them).
- The eligibility criteria of the locked protocol `03_protocol/sr-protocol.md`.

## Output
- One file: `reviews/tmp/ai-suggestions.<stage>.csv` with `rec_id,suggestion,reason`; suggestion include,
  exclude or maybe; reason at most 20 words naming the criterion.
- The main thread then runs `screening.py . suggest --stage <stage> --from reviews/tmp/ai-suggestions.<stage>.csv`,
  which writes `02_evidence/sr/ai-suggestions.csv` (shown to reviewers as a separate column).

## Rules
- Never write `02_evidence/sr/screening.csv`, never run `screening.py decide`, never use a reviewer's name.
- Unsure → maybe. Title and abstract only at stage ta; full text only from the text you are given.
- Records are published studies; no patient data. Report how many suggestions you made: the disclosure counts them.
