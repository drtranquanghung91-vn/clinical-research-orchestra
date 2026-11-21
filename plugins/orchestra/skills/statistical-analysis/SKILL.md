---
name: statistical-analysis
description: 'Use when study data must be analysed according to the SAP, when post-hoc or exploratory analyses are requested, or when results from SPSS, Stata or R must be brought into the project. Triggers: "chạy thống kê", "phân tích dữ liệu", "phân tích số liệu", "kiểm định", "so sánh nhóm", "hồi quy", "phân tích dưới nhóm", "phân tích hậu kiểm", "post-hoc", "subgroup", "tìm phân nhóm có p < 0.05", "p-hacking", "kết quả SPSS", "nhập kết quả SPSS", "statistical analysis", "run stats", "analyze my data", "import SPSS output"; or after data-preparation when the SAP is approved.'
---

Analysis workflow adapted from the owner's stat-analysis-vi skill.

# Statistical analysis

## 1. Core rule
The SAP decides what is analysed. Every number comes from code or the author's exported output, never
mental arithmetic. Post-hoc analyses are declared, labelled exploratory, never promoted.

## 2. Preconditions
- `python "${CLAUDE_PLUGIN_ROOT}/scripts/gate.py" check . G2` exits 0 (open or waived); else stop.
- `04_data/*.deid.csv` exists; else use the Skill tool with `data-preparation`.
- `03_protocol/sap.md` has the analysis register; else use the Skill tool with `sample-size-sap`.
Set `STATUS.md` row 5 `doing`.

## 3. Run mode
1. Read `sap.md`, `04_data/codebook.md` and the data; ask one question only if outcome, exposure, unit
   of analysis or patient ID is unclear.
2. Write `05_analysis/analysis.py`: vendor `crostats` first (workflow), then one block per register
   analysis in ID order; seeded, no network, reads only the `.deid.csv`; set each reference level to the
   SAP's (`order=[…]`, `C(x, Treatment(reference=…))`).
3. Run it; read the log.
4. Post-hoc or deviating analyses only at the author's request (section 5).
5. `analysis_plan.py check` and `results_ledger.py import . --verify-raw`; fix findings. If import lists
   relabelled ids after a re-run, fix the placeholders, then `--accept-relabel`.
6. Write `05_analysis/analysis-report.md` with `{{R-…}}` placeholders (`.count` for counts;
   `${CLAUDE_PLUGIN_ROOT}/references/statistics/analysis-report-template.md`), post-hoc and deviations in
   their own labelled section.

## 4. Import mode
The author exports SPSS, Stata or R output into `00_inputs/`. Write `05_analysis/output/results.json`
by hand, a `raw` quote and `locator` per number, then
`results_ledger.py import . --verify-raw` (`${CLAUDE_PLUGIN_ROOT}/references/statistics/import-outputs.md`).
Leading-dot p values (`.032`) are accepted. Status rules are the same; then step 6.

## 5. Post-hoc rule
One line in `decisions.md` per analysis, before it runs:
- `POST-HOC A<n>: <reason>, requested by <author>, <YYYY-MM-DD>`
- `DEVIATION A<n>: <what and why>, <YYYY-MM-DD>`; label its results as deviations

Asked for a significant subgroup: explain multiplicity first; use this route; never choose by p.
A registered analysis not run needs `DEVIATION A<n>: not done because …`. A failed model (`MODEL
FAILED`; `interaction` gives `nan`, not a p) is reported, never dropped; replacing it is a `DEVIATION`.

## 6. Rules kept and changed from stat-analysis-vi
Kept as labelled defaults: normality check, median (IQR), exact tests, EPV caveat, reporting
precision, plain-language summary (`${CLAUDE_PLUGIN_ROOT}/references/judgement-defaults.md`). Changed:
no p < 0.20 screening or backward selection (covariates come from the SAP); no baseline p-values in an
RCT; unregistered ROC/Youden cut-offs, subgroups and sensitivity analyses are post-hoc; subgroups get
per-subgroup effects plus an interaction test (`${CLAUDE_PLUGIN_ROOT}/references/statistics/stat-tests.md`).

## 7. Missing dependency
Print `python -m pip install pandas scipy statsmodels openpyxl` (`lifelines` for Cox); stop.

## 8. Checks before hand-back
From the project folder, scripts in `${CLAUDE_PLUGIN_ROOT}/scripts/`, all exit 0:
`analysis_plan.py check .`, `results_ledger.py import . --verify-raw`,
`render_results.py . 05_analysis/analysis-report.md`,
`check_numbers.py . 05_analysis/analysis-report.rendered.md`,
`analysis_plan.py check . --text 05_analysis/analysis-report.md`.

## 9. Hand-off
After the author's review:
`gate.py lock <project> G3 --by "<author>" --files ledgers/results-ledger.json 05_analysis/output/results.json 05_analysis/analysis.py 05_analysis/crostats.py 03_protocol/sap.md 04_data/<file>.deid.csv`
(import mode: the `00_inputs/` exports instead of the two `.py` files; hashed, not versioned); never lock G3 here. Write in `project.yaml → language.output`.

## 10. Workflow
`${CLAUDE_PLUGIN_ROOT}/references/workflows/statistical-analysis.md`
