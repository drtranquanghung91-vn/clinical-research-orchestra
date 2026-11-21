# number-drift: a typed number in Chapter 3 differs from the locked ledger
Skill under test: results-writing (step 8 checks, `check_numbers.py`, placeholders)
Fixtures: tests/scenarios/fixtures/number-drift/ (cohort project as in posthoc-fishing plus `05_analysis/output/results.json` and `analysis.log`, `ledgers/results-ledger.json` (5 results, R-A0-003 = 85.0 %, "no readmission"), gate G3 locked, and `06_writing/thesis/ch3-results.md` that uses placeholders except for one typed "86,3%" in 3.1)
Allowed tools: Bash,Read,Write,Edit,Glob,Grep,Skill
Prompt: Kiểm tra lại chương 3 trước khi nộp.
Expected (GREEN):
- `render_results.py` and `check_numbers.py` are run on the chapter.
- `check_numbers.py` reports E-NUM for "86,3%" (not in the results ledger).
- The typed number is replaced by its placeholder `{{R-A0-003}}` (ledger value 85.0), not by a retyped number.
- `check_numbers.py` on the re-rendered chapter exits 0, and the ledger and `results.json` are untouched.
Baseline (RED): observed result recorded in BASELINE.md (the unaided model may proofread the prose and never compare the number with the ledger).
