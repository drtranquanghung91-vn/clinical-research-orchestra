# Statistical tests for the analysis: decision tables and crostats calls

Adapted from the owner's `stat-analysis-vi` skill (`references/stat_tests.md`), translated and rewired to
`crostats`. Used by `statistical-analysis`. Design-level choices (which test the SAP names, test per
outcome × comparison, SAP writing rules) are in Amelia Le's
`${CLAUDE_PLUGIN_ROOT}/references/statistics/test-selection.md`; this file does not repeat them. The SAP
decides; these tables decide only what the SAP leaves to the data (for example mean or median). Every
threshold below is a **default** (`${CLAUDE_PLUGIN_ROOT}/references/judgement-defaults.md`).

`crostats` lives in `05_analysis/crostats.py` (vendored copy). A method `crostats` does not cover is written
in `analysis.py` with scipy or statsmodels, its choice and reason logged with `rec.log(...)` and each
number recorded with `rec.add(...)`. Nothing is computed by hand.

## Variable types

| Type | Examples |
|---|---|
| Continuous | age, BMI, HbA1c, laboratory values |
| Binary | yes/no, positive/negative, 0/1 |
| Ordinal | grade 1–4; mild/moderate/severe |
| Nominal | blood group, ethnicity, drug class |
| Count | number of admissions, number of exacerbations |
| Time to event | survival, follow-up time |

## 1. Two independent groups

| Outcome | Distribution | Test | Effect estimate | crostats |
|---|---|---|---|---|
| Continuous | normal in both groups and n ≥ 30 | Welch t-test | mean difference (95% CI) | `compare_two` |
| Continuous | skewed, or n < 30 | Mann–Whitney U | median (IQR) per group; Hodges–Lehmann shift (95% CI) as the estimate; p | `compare_two` (p only; Hodges–Lehmann not computed by crostats yet) |
| Binary | every expected count ≥ 5 and both groups n ≥ 20 | Pearson chi-square, no Yates correction | OR / RR / RD (95% CI) | `compare_props` + `crude_effect` |
| Binary | any expected count < 5, or a group n < 20 | Fisher exact | OR / RR / RD (95% CI) | `compare_props` + `crude_effect` |
| Ordinal | — | Mann–Whitney U | p | scipy `mannwhitneyu` in `analysis.py` (`compare_two` would pick Welch t for a score that looks normal) |
| Count / rate | Poisson | Poisson regression; negative binomial when overdispersed | IRR (95% CI) | `fit_poisson` (negative binomial: statsmodels in `analysis.py`) |

Normality rule (default): Shapiro–Wilk when n < 50, |skewness| < 1 when n ≥ 50; mean (SD) only when normal
and n ≥ 30, otherwise median (IQR). `crostats.describe` applies it and `compare_two` / `table1` follow it.
The source also listed standardised effect sizes (Cohen's d, rank-biserial r, Cramér's V); report them only
when the SAP names them, computed in `analysis.py` and recorded with kind `other`. The main result is the
effect estimate with its 95% CI (test-selection.md, "Estimation before testing"). For Mann–Whitney the
estimate is the Hodges–Lehmann shift (median of all pairwise differences) with its 95% CI: `crostats` does
not compute it yet, so compute it in `analysis.py` with numpy/scipy (Moses CI, or a seeded bootstrap) and
`rec.add` it with kind `md`, or report its absence as a limitation.

## 2. Three or more groups

| Outcome | Distribution | Overall test | Pairwise follow-up | crostats |
|---|---|---|---|---|
| Continuous | normal | one-way ANOVA; Welch ANOVA when Levene p < 0.05 | Tukey HSD after classic ANOVA; Games–Howell after Welch ANOVA | `compare_k` (the log says which ANOVA it chose) |
| Continuous | skewed | Kruskal–Wallis | Dunn test (Bonferroni) | `compare_k` |
| Binary | — | chi-square (Monte Carlo exact when any expected count < 5) | pairwise Fisher exact | `compare_props` |
| Ordinal | — | Kruskal–Wallis | Dunn test | scipy `kruskal` in `analysis.py` (`compare_k` may pick ANOVA) |

Pairwise follow-up tests are pre-specified only when the SAP lists them; otherwise they are post-hoc
analyses with their own ID and `POST-HOC` line. Tukey, Games–Howell and Dunn are written in `analysis.py`;
read the `compare_k` log line first to pick Tukey (classic ANOVA) or Games–Howell (Welch ANOVA).

## 3. Paired or matched data

| Outcome | Test |
|---|---|
| Continuous, normal | paired t-test |
| Continuous, skewed | Wilcoxon signed-rank |
| Binary | McNemar test |

Not in `crostats`: scipy `ttest_rel`, `wilcoxon`; statsmodels `mcnemar`.

## 4. Correlation

| Pair of variables | Test |
|---|---|
| Continuous × continuous, normal | Pearson r |
| Continuous × continuous, skewed | Spearman ρ |
| Ordinal × ordinal | Spearman ρ or Kendall τ |
| Binary × continuous | point-biserial r (Pearson on 0/1) |
| Binary × binary | phi coefficient |

Collinearity flag (default): |Spearman ρ| > 0.70 between two covariates is reported; the SAP's model is
still fitted. Dropping a covariate is a `DEVIATION`.

## 5. Regression model

| Outcome | Model | Link | Report | crostats |
|---|---|---|---|---|
| Binary | logistic | logit | adjusted OR (95% CI) | `fit_logistic` |
| Continuous, normal residuals | linear (OLS) | identity | β (95% CI), R² | `fit_linear` |
| Continuous, strongly skewed | quantile regression (median); or OLS on the log scale | — | median difference (quantile regression); ratio of geometric means, exp(β) (log-OLS) | statsmodels `quantreg` or `ols` in `analysis.py` |
| Count, overdispersed | negative binomial | log | IRR | statsmodels in `analysis.py` |
| Count, not overdispersed | Poisson | log | IRR | `fit_poisson` |
| Time to event | Cox proportional hazards | — | HR (95% CI) | `fit_cox` (needs lifelines) |
| Ordinal | proportional-odds logistic | logit | generalised OR | statsmodels `OrderedModel` in `analysis.py` |
| Binary outcome in an RCT | log-binomial | log | RR (95% CI) | statsmodels GLM in `analysis.py` |

Covariates come from the SAP. Univariable screening at p < 0.20 and backward selection are **post-hoc
only**: run them only when the author asks, with their own `A<n>`, status `posthoc` and a `POST-HOC` line;
they never choose the adjustment set of a pre-specified model.

## 6. Model diagnostics

| Model | Diagnostics | Where |
|---|---|---|
| Logistic | AUC; Hosmer–Lemeshow (10 groups); EPV = min(events, non-events) / parameters, default ≥ 10 for a confirmatory model | `fit_logistic` returns `auc`, `hl_p`, `epv` |
| Linear | R²; Shapiro–Wilk on residuals; Breusch–Pagan for heteroscedasticity | `fit_linear` returns `r2`, `resid_shapiro_p`, `bp_p` |
| Cox | proportional hazards by Schoenfeld residuals (rank time transform) | `fit_cox` returns `ph_min_p` |
| Poisson | dispersion = Pearson χ² / residual df; > 2 → negative binomial | `fit_poisson` returns `dispersion` |

On separation, non-convergence or collinearity a model records nothing and logs `MODEL FAILED A<n>: …`:
`fit_logistic` / `fit_linear` / `fit_poisson` / `fit_cox` return `{"failed": True, ...}`; `interaction`
returns `nan`. A `nan` interaction p means "model failed, see the log": report it as failed, never as a
p-value. See "Common errors".

## 7. From the source's Python templates to crostats

| Source template | crostats call | Status |
|---|---|---|
| Crude OR with Woolf CI (returned nothing on a zero cell) | `crostats.crude_effect(a, b, c, d)` → OR (Woolf), RR, RD with 95% CI; Haldane 0.5 correction on a zero cell, `corrected` = True; record each with `rec.add(..., kind="or")`; p from `compare_props` | as registered |
| Mann–Whitney U + rank-biserial r | `crostats.compare_two(df, outcome, group, rec, "A<n>")` (Welch t or Mann–Whitney by the normality rule) | as registered |
| Chi-square vs Fisher auto-select | `crostats.compare_props(df, outcome, group, rec, "A<n>")` | as registered |
| Univariable logistic screening, sorted by p | a loop of `crostats.fit_logistic(df, outcome, [x], rec, "A<n>", status="posthoc")` | **post-hoc only** |
| ROC + Youden cut-off | `r = crostats.roc_youden(y, score, rec=rec, analysis_id="A<n>", status=..., label="AUC …")` records the AUC and logs cut-off, Se, Sp; `rec.add` the cut-off (kind `other`) and Se/Sp (kind `percent`) only if the report cites them | post-hoc unless registered |
| Sensitivity analysis over cut-offs | a loop over cut-offs with `crude_effect` + `rec.add` | post-hoc unless registered |
| Subgroup effect | the model (e.g. `fit_logistic`) fitted in each subgroup level with the register's status, plus `p = crostats.interaction(df, outcome, exposure, modifier, covariates, family, rec=rec, analysis_id="A<n>", status=...)`, which records the p itself; `nan` = model failed | post-hoc unless registered |

With `rec=rec, analysis_id=...`, `roc_youden` (AUC) and `interaction` (p) record their own results: never
`rec.add` them again. `crude_effect` records nothing, so the script records its estimates with `rec.add`.
Subgroups are reported as the effect in each subgroup plus the interaction p, never as separate
significance claims per subgroup.

## 8. Assumption templates (report section on test choice)

Adapt to the tests actually used. In a Vietnamese report use the quoted wording; in an English report use
the gloss.

- Mann–Whitney U instead of t-test: "Biến liên tục được mô tả bằng trung vị (IQR) thay vì trung bình (SD)
  vì [lý do: n nhỏ / phân phối lệch / Shapiro–Wilk p < 0,05]. So sánh hai nhóm độc lập dùng Mann–Whitney U
  test (Wilcoxon rank-sum), không yêu cầu phân phối chuẩn." Gloss: median (IQR) because of small n, skew or
  Shapiro–Wilk p < 0.05; Mann–Whitney U needs no normal distribution. If an effect size is reported:
  rank-biserial |r| < 0.3 small, 0.3–0.5 medium, > 0.5 large.
- Fisher exact instead of chi-square: "Fisher exact test được áp dụng thay Chi-square khi bất kỳ ô nào
  trong bảng có tần số kỳ vọng < 5 (quy tắc Cochran, 1954) hoặc một nhóm có n < 20. Fisher exact cho
  p-value chính xác hơn với small-count cells và bảo thủ hơn (conservative) về type I error." Gloss:
  exact p for small expected counts; conservative for type I error.
- EPV < 10: "Mô hình đa biến có [N] tham số với [M] biến cố → EPV = [M/N], chưa đạt ngưỡng mặc định
  EPV ≥ 10. Ước lượng hiệu chỉnh cần diễn giải thận trọng, xem là thăm dò, cần xác nhận trên mẫu lớn
  hơn." Gloss: below the default EPV, adjusted estimates are exploratory.
- No multiplicity adjustment: "Nghiên cứu có một câu hỏi chính được xác định trước. Các phân tích thứ cấp
  và hậu kiểm mang tính tạo giả thuyết; không hiệu chỉnh đa kiểm định theo SAP; xác suất dương tính giả
  tăng theo số phép kiểm." Gloss: one pre-specified primary question; secondary and post-hoc results are
  hypothesis-generating. Use only when the SAP's multiplicity column says "none".

## 9. Common errors

| Error | Cause | Handling |
|---|---|---|
| `AttributeError: HosmerLemeshowTest` | old statsmodels | not applicable: `fit_logistic` computes Hosmer–Lemeshow itself |
| statsmodels model cannot be pickled | patsy frame | not applicable: `Recorder` stores numbers as JSON |
| singular matrix in logistic regression | perfect separation or collinear terms | `MODEL FAILED`; report it; Firth or exact logistic, or removing a term, only as a `DEVIATION` |
| zero cells in a cross-table | rare category | Haldane correction for OR/RR (`crude_effect`), Fisher for p; merging categories or "descriptive only" is a `DEVIATION` |
| convergence warning in logistic regression | low EPV, starting values | `MODEL FAILED`; more iterations or fewer terms only as a `DEVIATION` |

## 10. When to ask the author before analysing

Ask **one question only**, and only if:
1. the primary outcome is unclear ("Biến kết cục chính là gì?" / "Which variable is the primary outcome?");
2. the unit of analysis is unclear ("Đơn vị phân tích là bệnh nhân hay lần đo?" / "Is the unit the patient
   or the measurement?");
3. there are repeated measures without an ID to link them ("Có biến ID để phân biệt bệnh nhân không?" / "Is
   there a patient ID?").

Everything else: infer, and write the assumption in the report's test-choice section.
