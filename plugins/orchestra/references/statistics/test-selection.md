# Choosing the statistical test

Methods content by Amelia Le (co-author), adapted for clinical-research-orchestra. Source: her
`sample-size-planning-vi` v3 (20 Nov 2026), `reference/test-selection.md`. Used by the `sample-size-sap`
skill (step 7) and by the SAP template (`sap-template.md`, sections 8–9).

General rule: **the test used to calculate the sample size must be the test used in the main analysis**
(the SAP must be consistent with the sample size). If the main analysis is an adjusted regression model,
calculate n for the matching simple test and state the adjusted model in the SAP (adjustment usually
increases power, so this is conservative).

## Test by outcome × comparison

| Primary outcome | Comparison | Normal distribution / large n | Non-normal / small n | With covariate adjustment |
|---|---|---|---|---|
| Continuous | 2 independent groups | Welch t-test (default; Student t if SDs are similar) | Mann–Whitney U (report Hodges–Lehmann) | ANCOVA (baseline as covariate – preferred for RCTs that measure baseline) / linear regression |
| Continuous | 2 paired groups / before–after | Paired t-test | Wilcoxon signed-rank | Mixed model if several time points |
| Continuous | ≥ 3 independent groups | One-way ANOVA + post-hoc (Tukey) | Kruskal–Wallis + Dunn | ANCOVA / linear regression |
| Continuous | ≥ 3 time points in the same individuals | Repeated-measures ANOVA | Friedman | Linear mixed-effects model (MMRM) – preferred because it handles missing data |
| Binary | 2 independent groups | χ² test | Fisher exact (expected count < 5) | Logistic regression (OR) / log-binomial or robust Poisson (RR) |
| Binary | Paired | McNemar | Exact McNemar | Conditional logistic regression |
| Binary | ≥ 3 groups | χ² (r×c) | Fisher–Freeman–Halton | Logistic regression |
| Ordinal | 2 groups | Mann–Whitney U / χ² for trend (Cochran–Armitage) | as left | Ordinal (proportional-odds) logistic regression |
| Count | 2 groups | Poisson regression | Negative binomial (overdispersion) | Poisson / NB regression with offset |
| Time to event | 2 groups | Log-rank test + Kaplan–Meier | — (log-rank is non-parametric) | Cox proportional hazards (check PH with Schoenfeld residuals); competing risks → Fine–Gray |
| Correlation of 2 continuous variables | — | Pearson r | Spearman ρ | Linear regression |
| Diagnostic accuracy | — | Se, Sp, PPV, NPV, LR± with 95% CI (Wilson); AUC (DeLong) | — | Comparing 2 AUCs: DeLong test |
| Agreement | — | Cohen κ (binary/categorical), ICC (continuous), Bland–Altman | — | — |
| Clusters / multicentre | any | GEE or mixed model with a random effect for cluster | — | required – ignoring clustering gives wrong CIs |

## Check assumptions before choosing

- Normality: Shapiro–Wilk (n < 50) or Q-Q plot; with n ≥ 30 per group the central limit theorem is
  usually enough for a t-test.
- Equal variances: Levene → unequal variances, use Welch.
- Proportional hazards: Schoenfeld residuals, log(−log S) plot → if violated, RMST or time-varying Cox.
- Expected cell counts: < 5 in > 20% of cells → Fisher exact.

## Rules for writing the SAP

- **Estimation before testing** (Nguyễn Văn Tuấn 2018): the effect size + 95% CI is the main result;
  declare in advance the thresholds of clinical importance (benefit / harm) so the CI can be read by
  zones: benefit / negligible / harm / inconclusive. Do not write "no difference" just because
  p > 0.05; do not compare the size of effects by their P values. Illustrative thresholds such as
  RR ≤ 0.90 or ≥ 1.10 are defaults for illustration only; clinicians set them per outcome
  (`${CLAUDE_PLUGIN_ROOT}/references/judgement-defaults.md`).
- Multiple tests: the probability of at least one false-positive result = 1 − (1 − α)^k; declare the
  primary outcome, secondary outcomes and the adjustment strategy before data exist; subgroups are
  declared in advance and tested by interaction.
- Analyse with reproducible scripts (R or a Stata do-file), keeping the code and software version; never
  run inferential analysis in Excel.
- State the main test for the primary outcome + the estimand (mean difference / ARR / RR / OR / HR) +
  95% CI. A P value never stands alone.
- State the rule for switching to the alternative test (for example: "if the distribution is clearly
  skewed, use Mann–Whitney; decided before unblinding").
- State the multiplicity strategy for secondary outcomes (Bonferroni / Holm / hierarchical, or
  "exploratory, not adjusted").
- State how missing data are handled: ITT / mITT / per-protocol, multiple imputation, sensitivity
  analysis.
- Subgroups: declared in advance, analysed with an interaction test; no conclusions from subgroups.
