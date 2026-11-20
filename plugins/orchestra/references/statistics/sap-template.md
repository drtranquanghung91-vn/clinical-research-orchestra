# Statistical Analysis Plan (SAP) template

Methods content by Amelia Le (co-author), adapted for clinical-research-orchestra. Source: her
`sample-size-planning-vi` v3 (20 Nov 2026), `reference/sap-template.md`. The `sample-size-sap` skill fills
it into `03_protocol/sap.md`.

Based on ICH E9, the ICH E9(R1) estimand framework, SPIRIT 2013 item 20 (SPIRIT 2025: the statistical
methods items and SAP sharing; Chan 2025, cited in `${CLAUDE_PLUGIN_ROOT}/references/design/protocol-template.md`)
and Gamble 2017 (JAMA SAP guideline). Fill every section; for a section that does not apply, write "Not
applicable" with the reason. Write in `project.yaml → language.output`; when that is Vietnamese, keep the
English statistical term in brackets at its first use.

## 1. Administrative information
- Study title, code, SAP version, date, author / statistician, status (before data lock?).

## 2. Objectives and hypotheses
- Research question (PICO/PECO).
- Primary hypothesis: H₀ / H₁, type (superiority / non-inferiority / equivalence), one- or two-sided.
- Secondary and exploratory objectives.

## 3. Study design
- Design type, allocation, randomisation (method, blocks, stratification), blinding.
- Measurement times, follow-up duration.

## 4. Outcomes and estimands (ICH E9 R1)
For the primary outcome (and each key secondary):
- Variable (measurement definition, time point).
- Population.
- Handling of intercurrent events (treatment policy / hypothetical / composite / while-on-treatment /
  principal stratum).
- Population-level summary (mean difference / ARR / RR / OR / HR / RMST difference).

## 5. Sample size
- Copy the "Sample size justification" paragraph from `03_protocol/sample-size.md` (template in
  `sample-size-formulas.md`) unchanged, with the sourced parameter table and the sensitivity table.
- Under hierarchical testing, add the power for the key secondary outcome at the primary's analysed n.

## 6. Analysis populations
- ITT / mITT / per-protocol / safety – defined clearly; which population is used for the main analysis,
  and which for non-inferiority (needs both ITT and PP).

## 7. Descriptive statistics
- Table 1, baseline by group: mean (SD) or median (IQR); n (%). **No** P values comparing baseline in an
  RCT (CONSORT).

## 8. Primary outcome analysis
- Main test / model (per `test-selection.md`), adjustment covariates (declared in advance, usually the
  stratification variables), estimand + 95% CI, significance level.
- Assumption checks and the rule for switching to the alternative test.

## 9. Secondary outcome analyses
- For each outcome: test, estimand, CI.
- Multiplicity strategy (Bonferroni / Holm / hierarchical / exploratory without adjustment).

## 10. Supplementary and subgroup analyses
- Subgroups declared in advance + interaction test; forest plot; cautious interpretation.
- Sensitivity analyses (per-protocol, other missing-data handling, other models).

## 11. Missing data
- Expected mechanism (MCAR / MAR / MNAR), main method (multiple imputation / mixed model), sensitivity
  (tipping-point, worst-case).

## 12. Interim analysis and early stopping (if any)
- Number, timing, boundaries (O'Brien–Fleming / Haybittle–Peto), DSMB, α adjustment.

## 13. Safety
- AE/SAE tables by group, frequencies; no inferential tests unless pre-specified.

## 14. Software and reporting
- Software + version, seed, code kept.
- Reporting standard: CONSORT / STROBE / STARD / TRIPOD by design; number of decimals; how P is shown
  (p < 0.001).

## 15. Changes from the protocol
- Table of changes, reasons, dates, and whether each happened before or after unblinding.

## Sources named
ICH E9; ICH E9(R1); SPIRIT 2013 and SPIRIT 2025; Gamble 2017 (JAMA); CONSORT. None is cited in a project
without an identifier verified through `search_lit.py add` and `verify_refs.py`
(`${CLAUDE_PLUGIN_ROOT}/references/evidence-policy.md`).
