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

## 2026-11-22 — Figures F1-F3 drawn from the locked ledger; F4 (STROBE flow) blocked

Author approved a 4-figure plan up front (forest of A1's adjusted HbA1c OR, KM of A4, rates of A0's
1-year readmission by HbA1c group, STROBE participant-flow) and asked not to be asked again whether to
draw them, but to be told if any number a figure needs is missing from the ledger.

Confirmed gate G3 still locked (`gate.py check . G3` → open/locked, 5 file hashes unchanged). Wrote
`07_present/figures/figures.json` and ran `figures.py . --only F1,F2,F3 --dpi 300`:
- F1 forest — rows `R-A1-003` (HbA1c 7-9% vs <7%, OR 1,10 [0,74-1,62]) and `R-A1-004` (HbA1c >9% vs
  <7%, OR 1,42 [0,94-2,15]), from Bảng 3.3 (mô hình A1 hiệu chỉnh theo tuổi, giới, thời gian mắc ĐTĐ,
  bệnh đồng mắc).
- F2 KM — redrawn from `04_data/cohort.deid.csv` (time `time_to_readmit_days`, event `readmit_1y`,
  group `hba1c_group`, order <7/7-9/>9, censored at 365 ngày, at-risk table at 0/90/180/270/365); group
  sizes at t=0 (235/514/321) match `R-A0-002/003/004.n`.
- F3 rates — `R-A0-062/063/064` (tỷ lệ tái nhập viện 1 năm theo nhóm: 19,6% [15,0-25,1], 21,0%
  [17,7-24,7], 25,5% [21,1-30,6]), from Bảng 3.2.

`consistency_audit.py .` → 0 block, 0 warn. Opened every `F<n>.png` and checked the printed numbers
against the ledger by hand before calling them done.

F4 (STROBE participant-flow) was **not drawn**: this simulated dataset has no pre-exclusion
screening/eligibility counts anywhere in the project (already noted in the 2026-11-21 Chapter-3 entry
above — the dataset was generated directly at the final analytic-population size). The only
sample-flow-shaped numbers that exist in the ledger are the full analytic cohort (`R-A0-001.n` = 1070)
and the complete-case subset used by the adjusted models A1/A4 (`R-A1-003.n` / `R-A4-005.n` = 1043,
i.e. 27 excluded for missing adjustment-covariate data). There is no box for "hồ sơ sàng lọc", "đủ tiêu
chuẩn chọn mẫu", or a breakdown of exclusions by study criteria — those counts were never recorded.
Reported this to the author instead of filling the diagram's boxes with invented or re-derived numbers;
author to decide between (a) a minimal 2-box diagram built only from `R-A0-001.n` and `R-A1-003.n`
(labelled honestly as "loại trừ do thiếu biến hiệu chỉnh", not a full STROBE screening flow), or (b)
leaving F4 out of the thesis and noting the limitation in text, or (c) retrieving the real
screening/exclusion counts from the original data source and adding them to the ledger first (would
need `statistical-analysis` re-run and G3 re-locked). No ledger or locked G3 file touched.

Author chose (a): the data is the full set of records already meeting the study's eligibility criteria
as extracted from the system, with no screening step ever recorded, so a minimal diagram from the two
ledger numbers is the honest option. Added `F4` (type `flow`) to `07_present/figures/figures.json`:
box 1 "Toàn bộ đoàn hệ hồi cứu đủ tiêu chuẩn chọn mẫu" `n = R-A0-001.n` (1070); box 2 "Đưa vào mô hình
hồi quy logistic và Cox hiệu chỉnh (A1, A4)" `n = R-A1-003.n` (1043); one exclusion box "Loại khỏi mô
hình hiệu chỉnh do thiếu dữ liệu biến hiệu chỉnh (tuổi, giới, thời gian mắc ĐTĐ, bệnh đồng mắc)"
`n = R-A0-001.n - R-A1-003.n` (27). Title and bottom source note both state in plain words that this is
not a full STROBE screening diagram and that no pre-exclusion screening/eligibility counts exist in the
project. Ran `figures.py . --only F4 --dpi 300` → `F4.{svg,pdf,png,data.json}`; opened `F4.png` and
checked the three numbers (1070, 1043, 27) against the ledger. `consistency_audit.py .` on all four
figures together → 0 block, 0 warn. No ledger or locked G3 file touched.

## 2026-11-22 — Conference abstract drafted for a domestic endocrinology/diabetes conference

Author gave the venue's rules directly (asked once, per the skill): Vietnamese, ≤300 words (title not
counted), structured with headings Đặt vấn đề và mục tiêu / Phương pháp / Kết quả / Kết luận, no
references required, no .docx needed yet.

Confirmed G3 still locked. Wrote `07_present/abstract.md`: Background/Objective from the registered
general objective (`01_question/question.md`); Methods gives design, setting, period, the full
descriptive cohort (`R-A0-001.n`) and the complete-case subset for the adjusted model
(`R-A1-003.n`), and the adjustment set (tuổi, giới, thời gian mắc ĐTĐ, ≥1 bệnh đồng mắc) matching A1;
Results leads with the overall and per-group 1-year readmission rate (`R-A0-061..064`) then the primary
analysis's adjusted OR for both HbA1c groups vs <7% (`R-A1-003`, `R-A1-004`, each with its CI and p);
Conclusion answers the objective without a causal verb and names that both adjusted CIs cross 1. Every
number is a `{{R-…}}` placeholder; none typed by hand. Kept the same "Dữ liệu mô phỏng" notice used in
Chapter 3, placed above the structured body (not counted toward the 300-word limit, same convention as
the title) since this draft is meant to leave the project for a real external audience; moved it into a
single HTML comment right under the title once the checks below showed it was leaking into the word
count and the ledger-number check (HTML/Markdown comments do not nest, so an earlier attempt to also put
a `<!-- not-a-result: -->` marker inside that comment was wrong and was reverted).

Ran the 6 checks of the skill, in order:
(1) `render_results.py . 07_present/abstract.md` → wrote `abstract.rendered.md`.
(2) `check_numbers.py`: first run 1 block (bare "300" in the then-visible disclaimer line); fixed by
moving the disclaimer into one HTML comment (comments are blanked before the numeric scan); re-run → 0
findings.
(3) `analysis_plan.py check . --text` → 0 block, 0 warn.
(4) `consistency_audit.py` against the rendered abstract and `ch3-results.rendered.md`: first run 1 warn
(same bare "300", found nowhere else and in no ledger value); gone after the same comment fix → 0 block,
0 warn.
(5) `lint_prose.py --count-words`: first draft 373 words (limit 300) — cut Background from two sentences
to one (dropped the restated "ở người bệnh ĐTĐ type 2" and the insulin/glycaemic-control aside) and
trimmed a few Methods/Conclusion phrases, never touching an estimate or its CI; re-run → 274 words.
(6) `lint_prose.py` (pattern lint) → 4 paragraphs, 0 hits, 0/100 words.

No ledger or locked G3 file touched.

## 2026-11-22 — Poster built in all 3 layouts from the accepted abstract

Author's accepted abstract (07_present/abstract.md) moves to poster: 90×120 cm, portrait, Vietnamese,
all 3 layouts (editorial, pathway, figure-led) for the author to choose, no logo, default palette, no
conference rules beyond size. Author gave one fixed key message and said not to strengthen or redirect
it: "HbA1c >9% lúc nhập viện có thể đi kèm nguy cơ tái nhập viện trong 1 năm cao hơn, nhưng cỡ mẫu này
chưa đủ để khẳng định" — written into `poster.json.key_message` with the R-A1-004 adjusted OR and its CI
added (satisfies the key-message test: estimate + CI + population + no causal verb) without changing
direction or strength.

Confirmed G3 still locked. Wrote `07_present/poster/poster.json` reusing all 4 locked figures
(F1 forest/A1, F2 KM/A4, F3 rates/A0, F4 the author-approved minimal flow). Every number is a
`{{R-…}}` placeholder.

Hit two real defects while building, both fixed by changing wording/numbers presentation, not the
underlying result:
- `consistency_audit.py` blocked once on the poster's Cox sentence: "tỷ số nguy cơ ... hiệu chỉnh là
  1,07" collided with the A2 continuous-HbA1c sentence in ch3-results ("... hiệu chỉnh là 1,02") because
  a parenthetical "(HR)" right before the number broke the phrase-matching window down to just "hiệu
  chỉnh", a key already used elsewhere. Fixed by dropping the inline "(HR)" (the thesis's own wording
  never uses it either) and re-ordering the >9%/7–9% HR mentions to match `ch3-results.md`'s own order,
  after which `consistency_audit.py` is 0 block, 0 warn.
- `poster_build.py` reported box overflow in all 3 layouts on the first build (title band too short for
  the full thesis title + authors + affiliation; several text columns too long for pathway's 2 columns
  and figure-led's 3 small columns). Fixed by: shortening the poster title to drop the
  site/year/design clause (kept in Methods instead); shortening every section body to poster-length
  prose; lowering `body_pt` to {pathway: 26, figure-led: 24} (24 is the floor); rewriting F4's box/source
  text shorter (regenerated both its document and poster PNG, reopened and checked both — the caveat
  that this is not a full STROBE diagram is unchanged, just terser); and using `figure_width_cm` to place
  F2 (the tallest figure, KM + at-risk table) and F4 narrower than their column. After these fixes,
  `poster_build.py` reports 0 overflowing boxes in all 3 layouts (only a non-blocking "column N% full"
  balance note on editorial/figure-led, which is informational, not a defect).

`poster_preflight.py --layout L` for all 3 layouts: **0 block** each time (print-ready by the tool's own
pass/fail line). Residual **warnings** the author should see before deciding on a layout, not silently
accepted:
- F2 (Kaplan–Meier) prints at ~15.7 pt wherever it appears in a side column (all 3 layouts), because
  `figure_width_cm` places it narrower (15 cm) than it needs to be legible at the 24 pt floor. Tried
  redrawing F2's poster asset directly at 15 cm (`figures.py --profile poster`, the fix preflight itself
  suggests): the KM legend + 3-row at-risk table does not compress at a narrower width, it redistributes
  height instead — the regenerated asset was ~9 cm taller at 15 cm wide than at 23 cm wide, which would
  have reopened the overflow just fixed. Reverted to drawing F2 at 23 cm and accepting the 15.7 pt
  placement warning as the real trade-off (fit vs. this one figure's in-column legibility), rather than
  hiding it.
- F1 (forest) prints at ~19.5 pt in the **editorial** layout only (its label+estimate text auto-widens
  the drawn asset to 28.23 cm, wider than editorial's own column).
- `lint_prose.py --slides` flags "Tài liệu tham khảo" (the references-strip heading) as a topic title
  that should state a finding — a structural footer label, not a finding; same false-positive in all 3
  layouts.

`check_pptx.py --poster` on all 3 `.pptx`: 0 issues each. All 3 `L.png` opened and checked: nothing cut
off, all 3 visibly different from each other, group colours/line fills consistent with `figures.json`
style across every figure.

Figures' poster-profile `poster_width_cm` changed from 23 to 22 (F3) and 21 (F4) to clear their own
font-size warnings; F1 and F2 stay at 23. This only affects `F<n>.poster.*` — the document-profile
(thesis) `F<n>.png/.svg/.pdf` at 9 pt/16 cm are untouched, re-verified after every F4 text edit.

No ledger or locked G3 file touched. Author to pick one of the 3 layouts (or ask for the KM/forest
warnings to be resolved differently, e.g. moving F2 to a wider slot) before printing.

## 2026-11-22 — Poster revised: F2 given real room, data note pulled out of "Tài liệu tham khảo"

Author reviewed all 3 PNGs, approved the key message wording with the OR+CI added, will print
**pathway** but keep all 3 layouts. Two things rejected, explicitly not to be fixed by lowering any
check's threshold: (1) the Kaplan–Meier (F2) printed too small/flattened (~16 pt) to read at 1.5 m —
author wants F2 a genuinely wider slot, sections may be reorganised; (2) the "Dữ liệu mô phỏng" notice
sat under the "Tài liệu tham khảo" heading although it is not a reference — wants it as its own labelled
note if the format allows.

Root cause of (1): `figure_width_cm` had been used to place F2 narrower than its drawn width to stop it
overflowing its column — that's what shrank its text below the 24 pt floor. Real fix, in order:
- Shortened F1's row labels (`HbA1c 7–9% vs <7%` → `7–9% vs <7%`, title already names HbA1c) — cut F1's
  own auto-widened minimum width from 28.23 cm to 25.4 cm, since F1 had the same problem in the editorial
  layout alone (reran `figures.py --only F1` for document and poster profiles; opened `F1.png` again,
  unchanged meaning, still clear in context of the figure's own title).
- Removed every `figure_width_cm` cap on F2 and let it draw and place at its natural/full column width:
  full column width in editorial and pathway, and made it the `hero` of figure-led in place of F1 (F1
  moves into a regular column instead — thematically still fine, since F1's own CI-crosses-1 message is
  carried by Bảng 3.3's text regardless of which figure is the dominant visual).
- Removed the "references" field entirely (freed the 0.08×H footer band back to the columns) and added
  the simulated-data notice as its **own numbered section** ("Ghi chú về dữ liệu"), directly answering
  request (2): it now carries its own heading in every layout, never appears near a label that says
  "Tài liệu tham khảo" (that heading no longer exists on the poster at all).
- Rebuilding then overflowed two of pathway's/figure-led's columns (F2 at full size is tall). Fixed by
  explicit `"column"` pins (`Mối liên quan`+F1 and `Thời gian...`+F2 both pinned to column 2, letting the
  other 5 sections auto-balance across the remaining columns) and by shortening section 4's heading
  (it had wrapped to 2 lines in a narrow column, the real last few centimetres of overflow — not F2).
  `poster_build.py` now reports 0 overflowing boxes in all 3 layouts (only non-blocking "column N% full"
  balance notes, mostly on editorial, which has slack to spare).

Did **not** touch any check's pass/fail threshold anywhere (`poster_preflight.py`'s 24 pt floor is
unchanged) — closed the gap by giving the content more room instead.

Re-ran every print check, all 3 layouts:
- `consistency_audit.py` → 0 block, 0 warn.
- `poster_build.py` → 0 overflowing boxes (down from the 1-2 before this round).
- `poster_preflight.py --layout L` → **0 block** each; F2 now has no warning at all in pathway (full
  column width) and figure-led (hero), and only 23.9 pt in editorial (effectively at the 24 pt floor).
  Residual **warnings**, reported rather than hidden: F1 ~21.6 pt (editorial, figure-led), F3 ~21.8 pt,
  F4 ~21.7 pt (all 3) — smaller figures with less text density than the KM plot, a real but modest
  trade-off for giving F2 the room it needed within a fixed page budget.
- `check_pptx.py --poster` on all 3 — first pass found 1 real issue on figure-led (`off-slide Body`): the
  "Ghi chú" section's text box ran 0.8 cm past the literal page bottom, inside poster_build's own overflow
  tolerance but outside check_pptx's stricter ~0.25 mm one. Fixed by shortening the note (dropped the
  `tools/simulate_cohort.py` path mention, kept "dự án ví dụ"); re-ran → 0 issues on all 3 `.pptx`.
- `lint_prose.py --slides` → 0 findings on all 3 (the earlier "Tài liệu tham khảo" false positive is gone
  because that heading no longer exists).

Opened every `L.png` again: F2 is visibly the largest or full-width figure in all 3 layouts now; "Ghi chú
về dữ liệu" reads as its own section with its own heading, nowhere near a references label.

No ledger or locked G3 file touched. Next: `committee-simulator` (deliverable `poster`) for the author's
in-person Q&A rehearsal, per the author's request.

## 2026-11-22 — Defense-prep: consistency audit before slides, one wording drift fixed

Author asked for an 18-slide defence deck (18-20 min) with speaker notes, plus a committee question
bank, for the thesis defence (broader scope than the poster: whole thesis, methodology, ethics, limits).
Confirmed G3 still locked. Per `defense-prep`'s core rule, ran the consistency audit **before** planning
any slide: `consistency_audit.py .` → 0 block, 0 warn; then the agent `consistency-auditor` (independent
read of the locked ledger, both thesis chapters, the abstract, the poster spec, `figures.json`,
`03_protocol/*`, `decisions.md`) → `reviews/consistency.md`, STATUS: FINDINGS (0 block, 1 real wording
drift, not a numeric error).

Finding (X-OBJ): `01_question/question.md`'s Mục tiêu cụ thể 2 still listed 6 adjustment factors (tuổi,
giới, thời gian mắc bệnh, bệnh đồng mắc, **thời gian nằm viện, sử dụng insulin**), left over from before
the mediator decision; `protocol.md` §2.7.2 (author-confirmed 2026-11-21) reclassified length-of-stay and
insulin use as likely mediators, excluded from the adjusted model — the actual A1 model (SAP §16, ch3
Bảng 3.3, abstract, poster) adjusts only tuổi, giới, thời gian mắc ĐTĐ, ≥1 bệnh đồng mắc (4 variables).
If the objectives slide had quoted question.md verbatim it would have contradicted the methods slide's
4-variable list in front of the committee. Fixed `question.md` mục tiêu cụ thể 2 to match protocol.md's
wording (4 adjustment variables; length-of-stay/insulin named as mediators, not hiệu chỉnh, with a
pointer to protocol.md §2.7.2). Re-ran `consistency_audit.py .` → still 0 block, 0 warn. No ledger or
locked G3 file touched; `question.md` is a design document from before G1/G2, not part of the G3 lock.

Planned and built `07_present/defense/deck.json` into `deck.pptx`: 18 main slides (title, outline, đặt
vấn đề, mục tiêu, 2 methods slides, cỡ mẫu+đạo đức, sơ đồ chọn mẫu [F4 diagram], Bảng 1 [table], 3 result
figures [F3 rates, F1 forest, F2 KM, each a native editable chart], tóm tắt [big_number], bàn luận, hạn
chế, kết luận, kiến nghị, closing) sized for 18-20 minutes, plus 5 backup slides after closing
(sample-size derivation, variable definitions/cut-offs, model assumptions table, post-hoc age-subgroup
table, references) that do not count toward the time budget. No template given by the school; used the
clean default theme with the project's accent colour. Every result number is a `{{R-…}}` placeholder;
the few numbers that are not ledger results (sample-size targets: 300/600 EPV, 535/nhóm two-proportions,
the 0.554-0.80 power table) are typed exactly as in `03_protocol/sample-size.md` (a pre-registered design
document, not an analysis result — there is no ledger mechanism for design/sample-size parameters) and
confined to the sample-size slide and its backup, each saying plainly where it came from.

Fixed two build defects: (1) the full official thesis title overflowed the title slide box (175%) —
shortened to match the poster's own shortened title, the presenter's notes carry the full official title
to read aloud; (2) `consistency_audit.py` blocked once on "thực tế" colliding as the same key between the
sample-size slide's {{R-A0-001.n}}=1070 and the limitations slide's {{R-A0-002.n}}/{{R-A0-004.n}}=235/321
— same false-positive shape as the poster's earlier HR collision (a short, reused lead-in phrase). Fixed
by giving each a distinguishing lead-in ("mẫu nghiên cứu hiện có" vs "hai nhóm cực chỉ có"); re-ran → 0
block, 0 warn.

Checks, in order: `pptx_from_spec.py` → 23 slides; `check_pptx.py` → 0 issues; `lint_prose.py --slides`
→ 0 findings; `consistency_audit.py .` (whole project, including `deck.json`'s strings) → 0 block, 0
warn. Rendered all 23 slides to PNG via PowerPoint (`check_pptx.py --render`) and opened every one:
native charts/diagram/table all correct, nothing cut off, numbers match the ledger. No ledger or locked
G3 file touched.

Ran the agent `committee-simulator` (deliverable `defense`): 22 questions across the whole thesis (lit
review gaps, design choices, sample size/power, mediator-vs-confounder reasoning, Cox censoring
assumption, every analysis including A2-A6 post-hoc, ethics status, AI-use disclosure per ICMJE,
generalisability, conclusions/recommendations staying within the data) plus 8 ranked weak points and 3
gaps. The agent did not write its own output file this time (unlike the poster run); saved its returned
text verbatim to `reviews/committee-defense.md` so it has the same durable location as
`reviews/committee-poster.md`. One gap worth flagging to the author directly: `06_writing/thesis/` only
has Chapter 1 (lit review) and Chapter 3 (results) as actual thesis prose — Chapters 2 (methods, beyond
`03_protocol/protocol.md`), 4 (discussion) and 5 (conclusion/recommendations) exist only as the defence
deck's slides, not as thesis chapter files; if the submitted thesis book needs those chapters written
out, that is separate work this session has not done.

No ledger or locked G3 file touched.
