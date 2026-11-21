# Analysis report template (`05_analysis/analysis-report.md`)

Adapted from the eight output sections of the owner's `stat-analysis-vi` skill. Written in
`project.yaml → language.output`: a Vietnamese report uses the headings in brackets. The report is for the
author and supervisor; the thesis chapter or manuscript Results section is written later by
`results-writing` from the same ledger.

Rules for the whole report:
- Every number is a placeholder: `{{R-A1-001}}` (value), `{{R-A1-001.ci}}`, `{{R-A1-001.p}}`,
  `{{R-A1-001.n}}`, `{{R-A1-001.full}}`. `render_results.py` formats them (precision by `kind`, decimal comma
  for `vi`, CI with an en dash); `check_numbers.py` blocks any literal result number that is not in the
  ledger. A number derived from ledger values carries `<!-- derived: <formula from ledger ids> -->`.
- Tables come from `05_analysis/output/tables/<T…>.csv`; give each a caption line (`Table 3.1. …` /
  `Bảng 3.1. …`) above and notes below.
- No figures (figures belong to P3). No colour or bold emphasis on p < 0.05.
- Results with status `posthoc` or `deviation` appear only in section 5, labelled exploratory.
- If the data are simulated, say so in a note under the title.

## Title block [Thông tin chung]
Study title, design (`project.yaml → design`), data file and its SHA-256 (from `results.json`), number of
participants analysed, date of the analysis run (`run_at`), engine line, mode (run or import).

## 1. Data audit [Kiểm tra chất lượng dữ liệu]
Summary from `04_data/cleaning-log.md` and the audit: rows, duplicates, missing values per key variable,
outliers flagged (IQR × 1.5, default; never removed), cleaning rules applied. One short comment.

## 2. Study population, Table 1 [Đặc điểm đối tượng nghiên cứu]
Table 1 (`A0`): overall and by the main exposure or group; continuous variables as mean ± SD or median
(Q1–Q3) by the normality rule; categorical as n (%). No baseline p-values in an RCT (CONSORT;
`table1(..., show_p=False)`). Key observations as short bullets.

## 3. Primary analysis [Phân tích chính]
3.1 Crude comparison: values by group, crude effect (MD, OR, RR or RD) with 95% CI and p.
3.2 Adjusted model, if registered: adjusted estimate per term with 95% CI and p; last line the diagnostics
(EPV, AUC, Hosmer–Lemeshow, R², dispersion, proportional hazards as applicable). A failed model is reported
here as failed, with its reason from the log (`MODEL FAILED A<n>: …`); never dropped silently.

## 4. Secondary analyses [Phân tích kết cục phụ]
Same layout as section 3, one subsection per registered secondary analysis, interpreted more cautiously
and with the multiplicity rule from the SAP.

## 5. Post-hoc analyses and deviations [Phân tích hậu kiểm và sai lệch so với đề cương]
Opens with: "These analyses were not pre-specified in the SAP; they are exploratory and
hypothesis-generating." / "Các phân tích sau không có trong kế hoạch phân tích; mang tính thăm dò, tạo giả
thuyết." One subsection per `A<n>`, each quoting its `POST-HOC A<n>:` or `DEVIATION A<n>:` line from
`decisions.md`. Typical content:
- univariable screening (all variables, sorted by p) and data-driven selection, only when the author asked;
- ROC/AUC with the Youden cut-off, sensitivity and specificity;
- sensitivity analyses (alternative cut-offs or definitions): estimate per alternative;
- subgroups: the effect per subgroup with the p for interaction, never a separate significance claim;
- replacement models after a failed model (Firth, exact, merged categories).

## 6. Test choice and assumptions [Lý do chọn phép kiểm và giả định]
One table, then short notes only where needed (assumption wording: `stat-tests.md` §8):

| Analysis | Test | Reason | Key assumption (checked how) |
|---|---|---|---|
| Summary of continuous variables | mean ± SD or median (IQR) | normality rule (default) | Shapiro–Wilk n < 50; skewness n ≥ 50 |
| Two-group continuous | Welch t or Mann–Whitney U | as above | independence; normality for t |
| Categorical | chi-square, Fisher, Monte Carlo exact | expected counts, group size (default) | independence |
| Crude OR | Woolf CI | 2×2 table | Haldane correction if a zero cell |
| Regression | logistic / linear / Poisson / Cox | outcome type, SAP | EPV ≥ 10 (default); residuals, PH, dispersion |
| ROC and Youden | AUC, Youden J | post-hoc unless registered | how the AUC is read |
| Sensitivity analyses | as above | purpose and conclusion | — |
| Multiplicity | SAP rule | SAP's multiplicity column | — |

The table covers the source's items 7.1–7.10 (median vs mean, Mann–Whitney vs t, chi-square vs Fisher,
Woolf OR, regression assumptions with the EPV caveat, ROC/Youden, sensitivity analyses, multiplicity,
summary table; limitations move to section 7). Assumptions inferred without asking the author are listed
here.

## 7. Limitations [Hạn chế về phương pháp]
Missing data handling, EPV caveats, failed or replaced models, residual confounding for observational
designs, post-hoc results, small groups with wide CIs.

## 8. Plain-language summary [Tóm tắt cho người đọc phổ thông]
Simple words, no technical terms. Four parts:
- "What did we do?" [Chúng tôi đã làm gì?]: one paragraph.
- "What did we find?" [Chúng tôi tìm thấy gì?]: 2–4 bullets with the main results.
- "What could this mean?" [Điều này có ý nghĩa gì?]: one paragraph, possible clinical meaning.
- "What we do not know yet" [Những gì chúng tôi chưa biết / hạn chế]: 2–3 bullets.

Banned terms in this section: "odds ratio", "p-value", "logistic regression", "multivariate", "AUC", "CI".
Use instead: "khả năng" (likelihood), "xác suất" (probability), "có sự khác biệt đáng kể" (a clear
difference), "mô hình phân tích" (analysis model), "độ chính xác dự đoán" (prediction accuracy). Post-hoc
results are described as worth checking in future studies, never as findings.
