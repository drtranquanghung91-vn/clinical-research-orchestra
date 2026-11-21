# Judgement defaults

These are defaults from experience, not standards. The author may override any of them; record the
override in decisions.md. Each number is a practical default set by the reviewer; it sits inside
guidance from a source, but the number itself can be adjusted. Skills must say "default" when they
apply one.

| Threshold | Default | Used by | Why it is only a default |
|---|---|---|---|
| Premature review | Fewer than 5 studies or fewer than 300 participants | Literature review, research-gap check | Ogden names the bias but gives no cut-off |
| Infeasible target sample | n above about 3 × feasible recruitment | Sample-size planning | DELTA2 says the target must be realistic; the multiplier is a rule of thumb |
| Common outcome | Outcome in 10% or more of the population: prefer cross-sectional or cohort over case-control | Protocol design | The rare-disease assumption for OR ≈ RR is usually below 10%; the exact cut-off is a convention |
| Qualitative interviews | 12–20 interviews | Protocol design, sample-size planning | Rounded up from Hennink & Kaiser's 9–17 to allow stratification |
| Questionnaire pilot | Pilot a new questionnaire on 10–20 people | Protocol design | Common practice; not from a specific text |
| Illustrative clinical thresholds | RR ≤ 0.90 or ≥ 1.10 | Reading confidence intervals against clinical thresholds | Illustration only; clinicians must set it per outcome |
| Normality check | Shapiro–Wilk when n < 50; \|skewness\| < 1 when n ≥ 50 | Statistical analysis | Visual checks and context may override |
| Summary statistic | mean (SD) if normal and n ≥ 30, else median (IQR) | Statistical analysis | Convention from `stat-analysis-vi` |
| Exact tests | Fisher/exact when any expected cell < 5 or n < 20 per group | Statistical analysis | Cochran's rule of thumb |
| Outliers | flagged when outside quartiles ± IQR × 1.5; never removed automatically | Data preparation | Tukey's convention |
| Events per variable | EPV < 10 → model reported as exploratory with a caveat | Statistical analysis | Peduzzi; newer work suggests context-specific limits |
| Overdispersion | Pearson χ²/df > 2 → negative binomial | Statistical analysis | Rule of thumb from `stat-analysis-vi` |
| Reporting precision | OR/RR/HR/RD/MD/β and CI 2 decimals; p 3 decimals or < 0.001; % 1 decimal; mean/SD/median/IQR 1 decimal; AUC 3 decimals | Results writing | ICMJE/STROBE practice; journals may differ |
| Number check scope | integers 0–10 and years are not checked by `check_numbers.py` | Results writing | Small counts in prose ("3 nhóm") are usually not results |
| Thesis .docx layout | A4, Times New Roman 13 pt, line spacing 1.5, margins top 2, bottom 2, left 3, right 2 cm | build_docx.py | Common Vietnamese university rules; the institution's rule wins |
