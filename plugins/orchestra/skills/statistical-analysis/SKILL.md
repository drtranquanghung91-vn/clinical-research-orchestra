---
name: statistical-analysis
description: 'Use when study data must be analysed according to the SAP, when post-hoc or exploratory analyses are requested, or when results from SPSS, Stata or R must be brought into the project. Triggers: "chạy thống kê", "phân tích dữ liệu", "phân tích số liệu", "kiểm định", "so sánh nhóm", "hồi quy", "phân tích dưới nhóm", "phân tích hậu kiểm", "post-hoc", "subgroup", "kết quả SPSS", "nhập kết quả SPSS", "statistical analysis", "run stats", "analyze my data", "import SPSS output"; or after data-preparation when the SAP is approved.'
---

Analysis workflow adapted from the owner's stat-analysis-vi skill.

# Statistical analysis

## 1. Core rule
The SAP decides what is analysed. Every number comes from code or from the author's exported output
file, never from mental arithmetic. Post-hoc analyses are allowed, declared and labelled exploratory;
they are never promoted to primary.

## 2. Preconditions
- `python "${CLAUDE_PLUGIN_ROOT}/scripts/gate.py" check . G2` exits 0 (open or waived); else stop.
- `04_data/*.deid.csv` exists; else use the Skill tool with `data-preparation`.
- `03_protocol/sap.md` has the analysis register; else use the Skill tool with `sample-size-sap`.
Set `STATUS.md` row 5 to `doing`.

## 3. Mode
Run mode when the data should be analysed here; import mode when the author ran SPSS, Stata or R.

## 4. Run mode
1. Read `sap.md`, `04_data/codebook.md` and the data; ask one question only if the primary outcome,
   unit of analysis or patient ID is unclear.
2. Write `05_analysis/analysis.py`: vendor `crostats` first (workflow), then one block per register
   analysis in ID order; seeded, no network, reads only the `.deid.csv`.
3. Run it; read `05_analysis/output/log.txt`.
4. Post-hoc or deviating analyses only after the author's request or agreement, each with its
   `decisions.md` line, registered with that status.
5. `analysis_plan.py check` and `results_ledger.py import`; fix findings.
6. Write `05_analysis/analysis-report.md` with `{{R-…}}` placeholders
   (`${CLAUDE_PLUGIN_ROOT}/references/statistics/analysis-report-template.md`), post-hoc and
   deviations in their own labelled section.

## 5. Import mode
The author exports SPSS, Stata or R output into `00_inputs/`. Write `05_analysis/output/results.json`
by hand with a `raw` quote and a `locator` for every number, then
`results_ledger.py import . --verify-raw` (`${CLAUDE_PLUGIN_ROOT}/references/statistics/import-outputs.md`).
Status rules are the same; then step 6.

## 6. Post-hoc rule
One line in `decisions.md` per analysis, before it runs:
- `POST-HOC A<n>: <reason>, requested by <author>, <date>`
- `DEVIATION A<n>: <what changed and why>, <date>`

A registered analysis not run needs `DEVIATION A<n>: not done because …`. A failed model is reported,
never dropped; its replacement is a `DEVIATION`.

## 7. Rules kept and changed from stat-analysis-vi
Kept as labelled defaults: normality check, median (IQR), exact tests, EPV caveat, reporting
precision, plain-language summary (`${CLAUDE_PLUGIN_ROOT}/references/judgement-defaults.md`). Changed:
no default p < 0.20 screening or backward selection (covariates come from the SAP); no baseline
p-values in an RCT; ROC/Youden cut-offs, extra subgroups and sensitivity analyses not registered are
post-hoc; subgroups only with an interaction test. Test tables:
`${CLAUDE_PLUGIN_ROOT}/references/statistics/stat-tests.md`.

## 8. Missing dependency
Print `python -m pip install pandas scipy statsmodels openpyxl` (add `lifelines` for Cox) and stop.
Never compute by hand instead.

## 9. Checks before hand-back
From the project folder, scripts in `${CLAUDE_PLUGIN_ROOT}/scripts/`, all exit 0:
`analysis_plan.py check .`, `results_ledger.py import .` (`--verify-raw` in import mode),
`render_results.py . 05_analysis/analysis-report.md`,
`check_numbers.py . 05_analysis/analysis-report.md`,
`analysis_plan.py check . --text 05_analysis/analysis-report.md`.

## 10. Hand-off
Ask the author to review the report, then
`gate.py lock <project> G3 --by "<author>" --files ledgers/results-ledger.json 05_analysis/output/results.json 05_analysis/analysis.py 05_analysis/crostats.py 04_data/<file>.deid.csv`
(import mode: the `00_inputs/` export files instead of the two `.py` files; hashed locally, not
versioned); this skill never locks G3 itself. Write in `project.yaml → language.output`.

## 11. Workflow
`${CLAUDE_PLUGIN_ROOT}/references/workflows/statistical-analysis.md`
