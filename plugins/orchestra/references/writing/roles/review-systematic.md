orchestra-role: review-systematic

# Role: methods and results of a systematic review (PRISMA 2020)

Introduction, discussion, conclusion and abstract use the P4 roles (`introduction`, `discussion`, `conclusion`,
`abstract`) with the review's PICO.

## Sources
`03_protocol/sr-protocol.md` (locked at G2), `02_evidence/sr/strings.md`, `search-log.csv`, the results ledger
(`R-A0-…` PRISMA counts; `R-A<n>-…` meta-analysis and GRADE), `04_data/sr/rob.csv`, `06_writing/review/sof.md`,
`ledgers/references.json` (included studies and methods references).

## Output files
`06_writing/review/03-methods.md`, `04-results.md`. `sof.md` is written by `grade.py`; do not edit its numbers.

## Methods (PRISMA 2020 items 5–15)
Eligibility; sources with platforms and last search dates; full strings in an appendix; selection by two
independent reviewers with consensus (kappa may be reported from `python "${CLAUDE_PLUGIN_ROOT}/scripts/screening.py" . kappa --stage ta` with
`<!-- not-a-result: screening agreement -->`); AI suggestions, if used, described as such; extraction by two
extractors; RoB 2 / ROBINS-I; effect measures; model as registered (random effects, REML; HKSJ if registered);
heterogeneity as τ², I² and the prediction interval; subgroup and sensitivity analyses as registered; Egger only
when k ≥ 10; GRADE. Deviations from the protocol are stated with their `DEVIATION` lines.

## Results
- Study selection with the flow figure; every count a placeholder: `{{R-A0-001.value}}` records identified …
  `{{R-A0-010.value}}` studies included; exclusion reasons `{{R-A0-051.value}}` onward.
- Study characteristics table and risk of bias (figure `type: rob`) with citations `[@id]`.
- Each synthesis: pooled estimate `{{R-A1-001.full}}`, τ² `{{R-A1-002.value}}`, I² `{{R-A1-003.value}}`, the
  prediction interval `{{R-A1-005.ci}}` (k ≥ 3), the forest plot; subgroup and leave-one-out results as registered.
- Certainty from GRADE; wording follows `references/review/grade-wording.md` (low → "may"; very low → "very
  uncertain").
- An analysis with fewer than 2 studies or one the protocol says not to pool: a structured narrative synthesis
  following `references/review/swim.md` (SWiM), no pooled number.
- Never type a number; never run or change an analysis.
