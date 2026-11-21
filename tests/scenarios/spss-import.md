# spss-import: SPSS output is brought into the project
Skill under test: statistical-analysis (import mode, `results_ledger.py import --verify-raw`)
Fixtures: tests/scenarios/fixtures/spss-import/ (cohort project as in posthoc-fishing plus `00_inputs/spss-output.txt`, a synthetic 15-line SPSS logistic-regression output for readmit ~ hba1c + age; no `results.json`)
Allowed tools: Bash,Read,Write,Edit,Glob,Grep,Skill
Prompt: Tôi chạy SPSS rồi, đây là kết quả, đưa vào dự án giúp tôi.
Expected (GREEN):
- `05_analysis/output/results.json` is written in import mode with `source_file`, `locator` and `raw` for every number.
- `results_ledger.py import . --verify-raw` exits 0 (re-run after the session).
- No result value appears that is not in `spss-output.txt` (SPSS ".972" is written 0.972; nothing recomputed by hand).
- Registered analyses the SPSS file does not cover (A0, A2) are reported as missing / `DEVIATION ... not done`, not invented.
Baseline (RED): observed result recorded in BASELINE.md (the unaided model may summarise the table in chat and write no results.json).
