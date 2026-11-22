orchestra-role: case-discussion

# Role: discussion, learning points, patient perspective, consent (case report)

## Sources
The case facts (`{{R-A0-…}}`), `01_case/similar-cases.csv` (every `ref_id` a verified record), `ledgers/references.json`.

## Output files
CARE: `09-discussion.md`, `10-patient-perspective.md`, `11-consent.md`. BMJ mode: `08-discussion.md`,
`09-learning-points.md`, `10-patient-perspective.md`, `11-consent.md`.

## Rules
- Discussion: strengths and limitations of the management, the literature with `[@id]`, the similar-cases table
  (`Table n. Similar published cases`, built from `similar-cases.csv`, one row per case with its citation), the
  rationale for conclusions (causality hedged; one case shows possibility, not frequency), the take-away.
- Learning points (BMJ mode): 3–5 bullets, each a lesson a reader can act on.
- Patient perspective: the patient's own words only when the author supplies them; otherwise exactly
  `[[AUTHOR: patient perspective — ask the patient or state that it was not obtained]]`.
- Consent: one sentence that written informed consent was obtained, in the words of the `CONSENT: obtained …` line
  of `decisions.md`; if that line is missing, write `[[AUTHOR: consent statement]]` and tell the author the final
  export is refused without it.
- Numbers only as placeholders; no names, places, dates or exact ages.
