# Decisions and assumptions

Dated entries, newest last. Gate waivers use a line starting `WAIVE G<n>:` followed by the reason.

## 2026-11-21 — Research question confirmed (G1)

Confirmed by Example author:
1. Sampling timeframe: discharges 01/2021–12/2022, followed to 31/12/2023 (365-day follow-up for
   every patient in the cohort).
2. Primary exposure analysis: admission HbA1c in 3 groups (< 7% / 7–9% / > 9%); continuous HbA1c
   per 1% is a secondary analysis.
3. Assumption (simulated project, no real records to check): the HIS records admission date and
   primary ICD-10 diagnosis for every hospitalisation, sufficient to identify 1-year all-cause
   readmission. On real data this must be checked against a small sample of real records before
   the study runs.

Title chosen: "HbA1c lúc nhập viện và nguy cơ tái nhập viện trong 1 năm ở người bệnh đái tháo đường
type 2 xuất viện tại Bệnh viện Mô phỏng (2021–2023): một nghiên cứu đoàn hệ hồi cứu" (option 2 of 3
in `01_question/question.md`). `project.yaml` title updated to match (Vietnamese, matching
`language.output: vi`).

Gate G1 opened by the author directly (`gate.py open . G1 --by "Example author"`).

## 2026-11-21 — Literature search completed (pending G2)

Ran `literature-search` (reusing the research-question scoping search) + `critical-appraisal` on the
5 papers found. No OpenEvidence/Consensus/ClinicalTrials.gov MCP tools were available in this
session; only `search_lit.py` (PubMed/Europe PMC) was used — recorded as a limitation in
`02_evidence/search-strategy.md`, not as "no evidence exists". Main finding: no study measures
admission HbA1c and 1-year all-cause readmission in general T2DM inpatients (Gap 1, GRADE
preliminary = very low certainty from indirect evidence only) — confirms the thesis question targets
a real gap. 5 references added and VERIFIED: chakraborty2021, hu2026, robbins2021, li2026, cao2026.
## 2026-11-21 — Evidence approved; correction on what G2 means

Author (Example author) reviewed and approved the evidence stage (incl. the Vietnam caveat in Gap 2)
and the re-appraisal of hu2026/robbins2021 (via `/orchestra:appraise`, ROBINS-E set as the primary
tool, NOS kept as the abstract-level proxy; three-question verdict added to the top of each file).
`STATUS.md` row 2 (Evidence) set to `done`.

**Correction:** per `gate.py --help` (`G1 question · G2 protocol and SAP · G3 results locked · G4
release`), G2 is the **protocol + SAP** gate, not an evidence gate — there is no dedicated gate for
the Evidence stage. The earlier note in this file and the prior STATUS.md wording that said "open
gate G2" after the evidence stage was wrong and is corrected here: G2 only opens after
`protocol-design` + `sample-size-sap` are done and the author approves them.

## 2026-11-21 — Protocol design (assumptions, not yet confirmed by author)

Author gave site/period/volume/data-source/budget facts directly (no "cứ làm luôn" said, but all
needed inputs given together, so no further questions asked). Protocol decisions recorded, pending
author confirmation (see `03_protocol/protocol.md` Part C, 3 items):

1. **Index-admission rule**: a patient discharged more than once in 01/2021-12/2022 contributes only
   their *first* discharge in the period as the index admission (unit of analysis); later discharges
   in the same period are read as the readmission outcome, not as separate analysis rows. Reason:
   avoids non-independent observations without a mixed-effects model the budget cannot support.
2. **Mediator classification**: in-hospital insulin use and length of stay are classified as
   measured after/concurrent with the HbA1c exposure window (24-48h) and therefore treated as
   possible mediators, NOT adjusted in the primary multivariable model (available only as
   descriptive/secondary variables). Reason: adjusting for a mediator would remove part of the real
   effect of HbA1c on readmission (bias-confounding.md).
3. **No specific T2DM diagnostic-criteria citation**: the protocol uses the physician-assigned
   ICD-10 diagnosis (operational definition already locked in `01_question/question.md`) rather than
   citing a specific diagnostic guideline (e.g. ADA §2), because no such reference is VERIFIED in
   this project's ledger yet (`02_evidence/guidelines.md` only verified ADA §16, hospital care).
   Flagged in protocol.md as needing a targeted `guideline-check` re-run if the committee requires a
   cited diagnostic standard.
4. **NLR/SII/SIRI as exploratory-only**: feasible without new tests (routine CBC differential) but
   not included in the primary confounder model until the author checks the real missing-data rate
   against a threshold (confirm item #1 in protocol.md).

Gate G2 not opened yet — protocol.md and variables.md are drafts awaiting author review; `sap.md` and
`sample-size.md` (from `sample-size-sap`) are still needed before G2 can open.

## 2026-11-21 — Protocol confirm items resolved by the author

1. **NLR/SII/SIRI missing-data threshold**: > 20% of records missing the differential WBC count →
   drop NLR/SII/SIRI entirely; ≤ 20% → exploratory/secondary analysis only, not the primary model.
2. **Mortality ascertainment**: HIS only captures in-hospital death, not out-of-hospital death. The
   "1-year mortality" secondary outcome is therefore "in-hospital death within 365 days" only, not
   true all-cause mortality. Fine-Gray (death as competing risk) is a sensitivity analysis only; the
   main time-to-first-readmission analysis uses plain Cox regression, treating unobserved
   out-of-hospital deaths as censored — stated as a limitation (possible non-informative-censoring
   violation if death is related to HbA1c).
3. **Ethics approval path**: submit to Bệnh viện Mô phỏng's own biomedical research ethics committee;
   request waiver of individual informed consent (retrospective, de-identified data, ~1,200 patients
   already discharged) — final decision rests with that committee, not pre-decided here.

`03_protocol/protocol.md` and `03_protocol/variables.md` updated accordingly.

## 2026-11-21 — Sample size / SAP (ASSUMPTION parameters, per author's explicit "làm luôn" instruction)

Author said explicitly: "Tham số nào không có nguồn thì ghi GIẢ ĐỊNH và làm luôn, không cần hỏi lại."
Ran `sample-size-sap` without further questions. Two parameters have no VERIFIED source in this
project (Gap 1 — no study measures 1-year readmission or a direct HbA1c effect at 1 year) and are
recorded as **ASSUMPTION**, not fabricated citations:
1. 1-year all-cause readmission rate in the HbA1c <7% reference group = **20% (ASSUMPTION)**.
2. Expected OR, HbA1c >9% vs <7% at 1 year = **1.5 (ASSUMPTION)** — chosen as a DELTA2-style cautious
   value, deliberately lower than the ~1.75-2.0 a naive log-linear extrapolation of hu2026's aOR 1.15
   per 1% (30-day outcome) would give across the ~4-5 percentage-point HbA1c gap between groups.

Sample size result: n required = 1,070 total (535 per extreme HbA1c group) via two-proportions
(conservative proxy for the adjusted model, per test-selection.md); EPV rule (6 model parameters)
needs only 300-600 total. Available pool ~1,200 before exclusions. **Risk flagged, not resolved**:
whether the <7% and >9% groups each reach 535 depends on the real HbA1c distribution, which is
unknown at planning stage — the study may be underpowered for the 3-group comparison even though it
is comfortably sized for the regression model's stability (EPV) and for Objective 1 (descriptive).
This is the riskiest assumption carried into `03_protocol/sample-size.md` §10 for the author to check
against a small real-chart sample before finalizing.

Gate G2 NOT opened by the assistant (per this skill's own hand-off rule: only the author opens it,
after approving protocol.md + sample-size.md + sap.md together).

## 2026-11-21 — Protocol + SAP approved; gate G2 opened

Author (Example author) approved `03_protocol/protocol.md`, `03_protocol/sample-size.md` and
`03_protocol/sap.md` together, and explicitly accepted the power risk flagged in `sample-size.md`
§4/§10 (required n = 1,070 for the HbA1c <7% vs >9% comparison vs ~1,200 available before
exclusions; actual power depends on the real HbA1c group distribution, unknown at planning stage).
Author opened gate G2 themselves: `gate.py open . G2 --by "Example author"`. `STATUS.md` row 3 set
to `done`.

## 2026-11-21 — SAP amended: analysis register

SAP amended 2026-11-21 to add the analysis register before any outcome data were analysed (no data existed).
SAP 1.1 (`03_protocol/sap.md` §15–16): register A0–A5 (A0 descriptive, A1 primary, A2–A5 secondary as
in SAP §7–9); Fine-Gray sensitivity analysis removed (in-hospital death after discharge can only follow
a readmission, so it is not a competing risk); analysis software Python with the vendored `crostats.py`.

## 2026-11-21 — Data preparation (codebook, audit, cleaning log) — pending author confirmation

Ran `data-preparation` on the existing `04_data/cohort.deid.csv` (SIMULATED, 1,070 rows, generated
by `tools/simulate_cohort.py`, seed 20261121 — author confirmed no raw file exists in `00_inputs/`
and `deidentify-data` is not needed since the extract was simulated already de-identified: study-id
`pid`, no dates). No raw data file to copy from, so step 1 of the skill (run `deidentify-data`) was
skipped as instructed.

1. **Codebook** (`04_data/codebook.md`): built from `03_protocol/variables.md` matched against the
   16 actual CSV columns. Noted explicitly: NLR, SII/SIRI and the nutritional-risk variable
   (`variables.md` §5, exploratory/conditional) have **no corresponding column** in this simulated
   extract — `simulate_cohort.py` does not generate them. This is not missing data on a collected
   variable; it is a variable not extracted in this demonstration dataset. `comorb_any` (≥1 of
   htn/ckd/cvd) is documented as a derived variable computed at analysis time, not stored as its own
   column (avoids adding a column to the data file).
2. **Audit** (`05_analysis/audit.py`, using vendored `05_analysis/crostats.py` v0.2.0): 1,070 rows, 0
   duplicate rows, 0 duplicate `pid`. Missing only in `dm_duration_years` (27/1,070 = 2.5%, matches
   the simulator's fixed 2% MAR rate). Tukey IQR×1.5 outliers flagged (not removed) in `age` (7),
   `hba1c` (6), `los_days` (29), `dm_duration_years` (0 technically — see log), and
   `time_to_readmit_days` (224 — a structural artefact of the 365-day censoring spike, not a data
   error). Manual logic checks (hba1c vs hba1c_group consistency, readmit_dm_1y only when
   readmit_1y=1, time_to_readmit_days=365 iff readmit_1y=0, death_inhosp_1y only when readmit_1y=1,
   binary columns restricted to 0/1, sex restricted to Nam/Nữ, age/hba1c/los_days ranges clinically
   plausible): **0 violations** found.
3. **Cleaning log** (`04_data/cleaning-log.md`): no cleaning rule was applied — no impossible value or
   coding error was found. The missingness pattern for `dm_duration_years` is described only (no
   imputation); `03_protocol/sap.md` does not yet state a missing-data method for this variable — if
   the author wants something other than complete-case, that choice belongs in the SAP before
   `statistical-analysis` runs.
4. `phi_scan.py --file 04_data/codebook.md 04_data/cleaning-log.md` → exit 0 (no identifier found).

Original data file (`04_data/cohort.deid.csv`) was not modified at any point in this stage, per the
skill's core rule.

## 2026-11-21 — Data stage closed (author confirmation)

Author (Example author) reviewed and confirmed `04_data/codebook.md` and `04_data/cleaning-log.md`.
Two open points resolved by the author, citing the SAP directly (no new assumption invented):
1. **`dm_duration_years` missing (2.5%)**: SAP §11 already specifies ≤5% missing on an adjustment
   variable → complete-case analysis, no imputation. 2.5% ≤ 5%, so complete-case applies; no
   imputation method needed.
2. **NLR/SII/SIRI and the nutrition-risk variable**: not extracted in this dataset (confirmed in the
   codebook's "absent variables" note) → dropped from the analysis entirely per SAP §10's own rule
   for this condition, not a new decision.

`STATUS.md` row 4 set to `done`. Next: `statistical-analysis` on the SAP §15–16 analysis register
A0–A5.

## 2026-11-21 — Data stage closed by author; statistical analysis run (A0–A5)

Author (Example author) closed the Data stage (STATUS.md row 4 → `done`): confirmed
`04_data/codebook.md` and `04_data/cleaning-log.md`; resolved the two open points by citing the SAP
directly — `dm_duration_years` missing 2.5% → complete-case per SAP §11 (≤5% threshold on an
adjustment variable), no imputation; NLR/SII/SIRI and the nutrition-risk variable not extracted →
dropped per SAP §10's own rule for that condition.

Ran `statistical-analysis` (run mode) on `04_data/cohort.deid.csv` for the SAP §16 register A0–A5:
1. `05_analysis/analysis.py` written and run: A0 (Table 1 + readmission/mortality proportions, Wilson
   CI), A1 (primary, crude + adjusted logistic OR, VIF, quadratic-term linearity check for age and
   dm_duration_years — Box-Tidwell not used because dm_duration_years has 0.0 values and ln(0) is
   undefined), A2 (continuous HbA1c OR), A3 (readmit_dm_1y OR), A4 (Cox HR, crude + adjusted,
   Schoenfeld PH test), A5 (in-hospital mortality, descriptive only, no model, per SAP §9). 0 models
   failed; every HbA1c group had ≥5 readmission events so the SAP §8 fallback-test rule was not
   triggered. In-memory-only derived columns (never written to the CSV): `comorb_any` (htn|ckd|cvd,
   the variables.md §3 confounder) and `hba1c_grp3` (relabelled group strings so crostats's
   lexicographic level sort shows clinical order `<7%` → `7-9%` → `>9%` instead of ASCII order
   `7-9 < <7 < >9`) — a presentation choice, not a SAP deviation; documented in the report §6.
2. `analysis_plan.py check .` and `results_ledger.py import .`: 0 block, 0 warn, 112 results imported.
3. `05_analysis/analysis-report.md` written per the template (every number a `{{R-…}}` placeholder or
   an explicitly marked `derived`/`not-a-result` literal); `render_results.py`, `check_numbers.py`,
   and `analysis_plan.py check --text` all exit 0.

No post-hoc or deviation analyses were run; A0–A5 match the register exactly. Main finding: both
primary adjusted estimates (A1: OR 7-9% vs <7% and >9% vs <7%) point in the hypothesised direction but
their 95% CIs include 1 — consistent with the power risk the author already accepted at G2
(`sample-size.md` §4/10). `STATUS.md` row 5 set to `doing` (not `done`) — the author must review
`05_analysis/analysis-report.rendered.md` and lock gate G3 themselves; this skill never locks G3.

## 2026-11-21 — Post-hoc subgroup by age (A6)

POST-HOC A6: author wants to see whether the HbA1c-group effect on 1-year all-cause readmission
differs by age (< 65 vs ≥ 65) — not registered in sap.md §16, requested because the thesis committee
may ask about older patients and no age-stratified result has been looked at yet, requested by Example
author, 2026-11-21.

Scope agreed with the author: this one subgroup only (age < 65 / ≥ 65), same covariates as A1 (age,
sex, dm_duration_years, comorb_any — age kept as a continuous covariate inside each stratum, per the
author's explicit "cùng biến hiệu chỉnh như A1"), plus the HbA1c-group × age-group interaction test.
Status `posthoc` throughout; reported in analysis-report.md §5 (post-hoc section) only, labelled
exploratory, never promoted to a primary or secondary finding. No other subgroup is added.

**Run:** `05_analysis/analysis.py` amended (age_grp derived in-memory column; A6 block: fit_logistic
in each age stratum with A1's covariates, then `crostats.interaction` for the HbA1c-group × age-group
likelihood-ratio p). 0 models failed. p-interaction = 0.835 (2 df) — no evidence the HbA1c-group
effect differs by age at this sample size; both age strata have wide CIs including 1.
`analysis_plan.py check` (0/0) and `results_ledger.py import` (127 results, A6 all status=posthoc,
correctly matched to this POST-HOC A6 line) both exit 0. Also fixed footnote ¹ under Table 3.1 in
`analysis-report.md` (author found it unclear) to state directly "27 người bệnh thiếu thời gian mắc
ĐTĐ ... n = 1043" instead of the earlier "tổng trừ n" phrasing.
`render_results.py`, `check_numbers.py`, `analysis_plan.py check --text` all exit 0 (1 warning: the
causal-wording checker flags "all-cause" inside the verbatim POST-HOC quote above — a false positive
on the English epidemiological term "all-cause readmission", not a causal claim; left as a warning,
not fixed, since the quote must stay verbatim per the report template).

## 2026-11-21 — Analysis report approved by author (pending gate G3)

Author (Example author) read `05_analysis/analysis-report.rendered.md` in full, including §5
(POST-HOC A6, age-subgroup analysis and its interaction test), and accepts the analysis results as
reported — both the registered A0–A5 findings and the post-hoc A6 finding (no evidence of effect
modification by age, p-interaction = 0.835). `STATUS.md` row 5 set to `done`.

Author will lock gate G3 themselves (not opened by this skill):
`gate.py lock . G3 --by "Example author" --files ledgers/results-ledger.json 05_analysis/output/results.json 05_analysis/analysis.py 05_analysis/crostats.py 04_data/cohort.deid.csv`.
No files were rerun or edited in this step (author instruction: no rerun of `analysis.py`, no edits to
the files about to be locked) — only `STATUS.md` and this `decisions.md` entry were touched.

## 2026-11-21 — Thesis Chapter 3 (Kết quả nghiên cứu) written from the locked ledger

Author confirmed gate G3 locked (`gates/state.json`: G3 recorded with 5 file hashes — ledger,
results.json, analysis.py, crostats.py, cohort.deid.csv). Ran `results-writing` (thesis mode,
`project.yaml → type: thesis-masters`).

Wrote `06_writing/thesis/ch3-results.md`: §3.1 đặc điểm chung + tỷ lệ tái nhập viện (A0, Mục tiêu 1),
§3.2 phân tích chính thô/hiệu chỉnh (A1, Mục tiêu 2), §3.3 các phân tích phụ theo thứ tự đăng ký (A2
HbA1c liên tục, A3 tái nhập viện liên quan ĐTĐ, A4 Cox, A5 tử vong mô tả), §3.4 phân tích thăm dò
(hậu kiểm A6, quoting its `POST-HOC A6:` line). Order follows STROBE (2007) Results items 13–17 (the
example already cited in this plugin's own results-writing workflow). Participant-flow figure left as
a placeholder line (`research-figures`/P3 not available yet); noted plainly that this simulated
dataset has no separate pre-exclusion screening counts (it was generated directly at the final
analytic-population size).

Every number is a `{{R-…}}` placeholder from the locked `ledgers/results-ledger.json`, or carries a
`derived`/`not-a-result` marker (same convention as `analysis-report.md`). Fixed one wording issue
while drafting: "p = {{R-A3-002.p}}" would have rendered "p = < 0,001" (R-A3-002's p is 4.5e-05); wrote
"p {{R-A3-002.p}}" instead so it reads "p < 0,001".

Checks, in order, all exit 0: `render_results.py` → `06_writing/thesis/ch3-results.rendered.md`;
`check_numbers.py` on the rendered file → 0 findings; `analysis_plan.py check . --text` on the
placeholder file → 0 block, 0 warn (every post-hoc A6 citation labelled "hậu kiểm"/"thăm dò" in its
own paragraph); `build_docx.py` → `out/ch3-results.docx`. Added 10 rows to `ledgers/claims.json`
(`ch3-…`, `status: unverified`, each citing its `R-…` ids); `crolib/ledgers.py check .` → 0 problems.

`STATUS.md` row 6 kept at `doing` (not `done`): Chapter 1 still needs the author's review and more
sources for §1.1–1.3, and the author has not yet read/accepted this Chapter 3 draft. No gate opened or
locked by this step; `results.json` and the ledger were not edited.

## 2026-11-21 — Chapter 3 wording/formatting fixes (author read-through)

Author read `ch3-results.rendered.md` and `out/ch3-results.docx` and asked for two fixes, no data
change: (1) `build_docx.py`'s supported Markdown subset does not include blockquotes (`>`) or inline
code spans (backticks) — its docstring lists only headings, bold/italic, bullets, numbered lines,
tables and `\newpage` — so the simulated-data note and the inline file-name mentions (protocol.md,
decisions.md, 05_analysis/analysis.py, tools/simulate_cohort.py) showed their raw markup in the .docx.
Rewrote all of them as plain prose sentences (no `>` blockquote, no backtick spans) in
`06_writing/thesis/ch3-results.md`. (2) "tỷ lệ nữ là 536 (50,1%)" read awkwardly (mixing "tỷ lệ" with
a count+percent pair) — changed to "trong đó nữ chiếm 536 (50,1%)".

No ledger, results.json or locked G3 file was touched; only wording/Markdown syntax changed, same
placeholders and numbers. Re-ran all 4 checks: `render_results.py`, `check_numbers.py` (0 findings),
`analysis_plan.py check . --text` (0 block, 0 warn), `build_docx.py` → `out/ch3-results.docx`, all
exit 0.
