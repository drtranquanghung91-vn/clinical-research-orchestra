# P2 Analyse and report results: design

- Date: 21 Nov 2026. Owner: Trần Quang Hưng. Status: approved in chat (21 Nov 2026).
- Extends `2026-11-20-clinical-research-orchestra-design.md` (the main spec). Where they differ, this file wins
  for P2 scope; the main spec's roadmap (section 16) is updated to match.

## 1. Why P2 changed

The original roadmap put statistical analysis in P3 (Write) after presentation work (P2). Posters, defence
decks and figures all need analysed results first, and analysis plus the Results chapter is where students and
clinicians need the most help after the protocol. P2 is now **Analyse and report results**. The old phases
shift by one:

| Phase | Scope |
|---|---|
| P0 Foundation | done (0.1.0) |
| P1 Plan the study | done (0.2.0) |
| **P2 Analyse and report results** | this file (0.3.0) |
| P3 Present | old P2: figures, poster, defence deck, abstract, prose humanizer, consistency audit |
| P4 Write | old P3 without statistical analysis: manuscript, thesis, case report, systematic review, literature-review mode (c), reviewer agents, G4 hook |
| P5 Extend | old P4: ethics and CRF, journal selection, reviewer response, Codex/Antigravity packaging, v1.0 |

## 2. Goals and non-goals

Goals:
1. Turn an approved SAP (gate G2) and a de-identified data file into reproducible results: a Python analysis
   script the project keeps, its outputs, and a machine-checked results ledger.
2. Accept results the author already produced in SPSS, Stata or R, with every number traced to a line in the
   exported output.
3. Keep pre-specified and post-hoc analyses apart: post-hoc and deviating analyses are allowed, declared in
   `decisions.md`, labelled in every table and sentence, and never reported as primary findings.
4. Write the Results (thesis Chapter 3 "Kết quả" or manuscript Results) where no number is typed by the model:
   numbers come from the ledger through placeholders.
5. Export Markdown deliverables to .docx with numbered tables.

Non-goals: figures and plots (P3 `research-figures`); manuscript/thesis Discussion (P4); replacing a
statistician (the skills say when to consult one); running R (the author may run R and import).

## 3. Users and flow

```
00_inputs/raw data ──data-preparation──▶ 04_data/<name>.deid.csv + codebook.md + cleaning-log.md
03_protocol/sap.md (G2 open, analysis register A1…An)
        └──statistical-analysis (run mode) ──▶ 05_analysis/analysis.py ─▶ 05_analysis/output/{results.json, tables/*.csv, log.txt}
           statistical-analysis (import mode) ◀── 00_inputs/spss-output.txt | .csv | .xlsx
results_ledger.py import ─▶ ledgers/results-ledger.json      analysis_plan.py check ─▶ E-STAT findings
gate.py lock G3 (ledger + outputs + analysis.py + data file)
        └──results-writing ─▶ 06_writing/{thesis/ch3-results.md | manuscript/results.md} with {{R-…}} placeholders
render_results.py ─▶ *.rendered.md     check_numbers.py ─▶ E-NUM findings     build_docx.py ─▶ out/*.docx
```

## 4. Skills and commands

| Skill | Kind | Origin | Does |
|---|---|---|---|
| `data-preparation` | model-invoked | new (spec #10) | inspect raw data; de-identify via the `phi-guard` skill `deidentify-data`; codebook; cleaning log; data audit (n, missing, duplicates, impossible values, outliers by IQR × 1.5 as a labelled default); never analyses outcomes |
| `statistical-analysis` | model-invoked | owner's `stat-analysis-vi`, ported to English and to the harness | run mode and import mode (section 5); analysis report |
| `results-writing` | model-invoked | new | Results text from the ledger (section 7) |
| `/orchestra:analyze` | user-invoked | new | thin wrapper: `data-preparation` if no `.deid.csv`, then `statistical-analysis` |
| `/orchestra:results` | user-invoked | new | thin wrapper: check G3, then `results-writing`, render, check, export |

All bodies ≤ 500 words, English, single-quoted descriptions with Vietnamese and English triggers, detail in
`references/workflows/<skill>.md` and `references/statistics/`.

## 5. `statistical-analysis`

### 5.1 Preconditions
- Gate G2 open (`gate.py check <project> G2`) or waived in `decisions.md`. If there is no SAP, use the Skill
  tool with `sample-size-sap` first; the author approves the SAP before any outcome is analysed.
- Data: `04_data/*.deid.csv` only. Raw files in `00_inputs/` are never read by analysis code. The analysis
  script records the data file's SHA-256.

### 5.2 Analysis register
`references/statistics/sap-template.md` (Amelia Le's content) gains section "Analysis register", which
`sample-size-sap` fills in `03_protocol/sap.md`:

```markdown
## Analysis register
| ID | Objective | Outcome | Population | Method | Covariates | Multiplicity |
|---|---|---|---|---|---|---|
| A1 | primary | readmission within 1 year (binary) | full cohort | logistic regression | age, sex, eGFR | none (single primary) |
| A2 | key secondary | ... | ... | ... | ... | hierarchical after A1 |
```
IDs are `A` + integer, unique, never reused. `A0` is reserved for descriptive statistics (Table 1).

### 5.3 Run mode
1. Read `sap.md`, `04_data/codebook.md`, the data file. Ask at most one question if the primary outcome or
   exposure cannot be identified (rule kept from `stat-analysis-vi`).
2. Write `05_analysis/analysis.py`, a plain script that imports `crostats` (section 6.2), runs every register
   analysis in ID order, and writes outputs. Seeded; no network; reads only the `.deid.csv`.
3. Run it. On a missing dependency print the install line
   `python -m pip install pandas scipy statsmodels openpyxl` (and `lifelines` for Cox) and stop.
4. Post-hoc or deviating analyses: allowed only after the author's request or agreement; each needs a line in
   `decisions.md`: `POST-HOC A7: <reason>, requested by <author>, <date>` or
   `DEVIATION A3: <what changed and why>, <date>`. The script registers them with that status.
5. Run `analysis_plan.py check` and `results_ledger.py import`; fix findings.
6. Write `05_analysis/analysis-report.md` (language per `project.yaml`): data audit summary; Table 1;
   pre-specified analyses; secondary; **post-hoc and deviations in their own section, labelled exploratory**;
   test choice and assumptions (why median/IQR, why Mann–Whitney, Fisher vs chi-square, EPV, model
   diagnostics, multiplicity); limitations; a plain-language summary without technical terms (kept from
   `stat-analysis-vi`). Numbers in the report also use `{{R-…}}` placeholders.

Rules kept from `stat-analysis-vi`, now written as labelled defaults the author may override
(`references/judgement-defaults.md`): normality check with Shapiro–Wilk when n < 50; median (IQR) for skewed
data or n < 50; exact tests when any expected cell < 5 or n < 20 per group; EPV < 10 caveat; reporting
precision (OR/RR/HR and CI 2 decimals, p 3 decimals or `p < 0.001`, % 1 decimal, AUC 3 decimals, en dash
for ranges, Vietnamese decimal comma when `language.output: vi`).

Rules changed from `stat-analysis-vi`:
- No default univariable screening at p < 0.20 and no default backward selection. Adjustment covariates come
  from the SAP. If the author asks for data-driven selection, it runs as a post-hoc model and is labelled so.
- No p-values comparing baseline characteristics in an RCT (CONSORT; `sap-template.md` §7).
- ROC/Youden cut-offs, extra subgroups and sensitivity analyses not in the register are post-hoc.
- Subgroups are reported with an interaction test, never as separate significance claims.

### 5.4 Import mode
For results produced in SPSS, Stata or R. The author exports output as text, CSV or Excel into `00_inputs/`
(copied, not moved). The agent writes `05_analysis/output/results.json` by hand **with a `raw` quote and a
`locator` for every number**; `results_ledger.py import --verify-raw` checks that each `raw` string occurs in
`source_file` at `locator` (line number for text/CSV, `Sheet!A1` cell for Excel) and that `value` appears in
`raw`. Status rules (5.3 step 4) apply unchanged.

## 6. Data contracts and scripts

### 6.0 Project template changes
- `templates/project/.gitignore` keeps ignoring `04_data/*` except `*.deid.csv`, and now also versions
  `04_data/codebook.md` and `04_data/cleaning-log.md` (neither may contain identifiers; `phi_scan.py --file`
  runs on both before hand-back).
- `templates/project/project.yaml` gains an optional `docx:` block (`font`, `size_pt`, `line_spacing`,
  `margins_cm`) read by `build_docx.py`; defaults are labelled defaults in `judgement-defaults.md`.

### 6.1 `05_analysis/output/results.json`
```json
{"engine": "Python 3.12; pandas 2.2; scipy 1.13; statsmodels 0.14",
 "data_file": "04_data/cohort.deid.csv", "data_sha256": "<hex>", "run_at": "2026-11-21T10:00:00",
 "results": [
  {"id": "R-A1-001", "analysis_id": "A1", "status": "prespecified", "label": "adjusted OR, HbA1c ≥ 8% vs < 8%",
   "value": 1.84, "ci": [1.21, 2.79], "p": 0.004, "n": 1070, "unit": "", "kind": "or",
   "table": "T3.2", "source_file": "05_analysis/output/log.txt", "locator": "line 57",
   "raw": "OR 1.84 (95% CI 1.21-2.79), p=0.004"}],
 "tables": [{"id": "T3.1", "title": "Baseline characteristics", "file": "05_analysis/output/tables/T3.1.csv",
             "analysis_ids": ["A0"]}]}
```
`kind` ∈ `n, percent, mean, sd, median, iqr, md, or, rr, hr, rd, beta, auc, p, other`; it selects the
formatting rule. `status` ∈ `prespecified, posthoc, deviation`. `id` = `R-<analysis_id>-<3 digits>`.

### 6.2 Scripts

| Script | Deps | Purpose | Exit codes |
|---|---|---|---|
| `crostats.py` | pandas, scipy, statsmodels; lifelines optional | library imported by `analysis.py`: `Recorder` (collects results, writes `results.json`, log with line locators), `audit`, `table1`, `compare_two`, `compare_groups`, `compare_props`, `crude_effect` (OR/RR/RD, Woolf CI), `fit_logistic/linear/poisson/cox` with diagnostics (EPV, VIF, Hosmer–Lemeshow, AUC, R², overdispersion), `roc_youden`, `interaction` | library |
| `analysis_plan.py` | stdlib | `register <project>` parses the SAP analysis register; `check <project>`: E-STAT findings (below) | 0 clean, 1 findings, 2 usage/IO |
| `results_ledger.py` | stdlib | `import <project> [--verify-raw]` validates `results.json` and writes `ledgers/results-ledger.json` | 0, 1 invalid records, 2 |
| `render_results.py` | stdlib | replaces `{{R-…}}` with formatted values (precision by `kind`, decimal comma for `vi`, CI as `1.21–2.79`); writes `<file>.rendered.md`; unknown id → E-NUM | 0, 1, 2 |
| `check_numbers.py` | stdlib | every literal number left in a Results/report file (outside placeholders, citations, headings, table/figure numbers, years, dates) must equal a ledger value at its printed precision, or carry an inline `<!-- derived: <formula from ledger ids> -->` | 0, 1, 2 |
| `build_docx.py` | stdlib | Markdown subset → .docx: headings, paragraphs, bold/italic, lists, pipe tables with a caption line `Bảng 3.1. …` / `Table 1. …` above and notes below, page breaks; A4, font and spacing from `project.yaml → docx` (defaults labelled, institution overrides) | 0, 2 |
| `simulate_cohort.py` (example only) | stdlib | seeded synthetic data for `examples/fictional-cohort` | 0 |

`analysis_plan.py check` findings (code `E-STAT`, spec 9.2):
- block: a result with status `prespecified` whose `analysis_id` is not in the register;
- block: a `posthoc` or `deviation` result without the matching `POST-HOC A<n>:` / `DEVIATION A<n>:` line;
- block: a register analysis with no result and no `DEVIATION A<n>: not done …` line (selective reporting);
- block: a Results paragraph that uses a `posthoc` result id without the words post-hoc / exploratory /
  thăm dò / hậu kiểm in the same paragraph (`check --text <file>`);
- warn: causal verbs (cause, gây ra, làm giảm…) with an observational `project.yaml → design`.

Credit: `build_docx.py` adapts the approach of Amelia Le's `md2docx.py` (v3) and is credited in NOTICE.md;
commits that adapt her code or content carry her co-author trailer.

## 7. `results-writing`

- Preconditions: G3 locked (`gate.py lock <project> G3 --files ledgers/results-ledger.json
  05_analysis/output/results.json 05_analysis/analysis.py 04_data/<file>.deid.csv`); `check` reports later
  changes.
- Structure follows the reporting guideline (`guidelines.json`, e.g. STROBE items 13–17, CONSORT 13–19) and
  the register order: participants and flow, Table 1, primary, secondary, post-hoc (own subsection, labelled).
- Thesis Chapter 3 (vi): numbered sections by objective ("3.1 Đặc điểm chung", "3.2 Kết quả theo mục tiêu 1"),
  tables "Bảng 3.n" with the title above and source/notes below, and a short "Nhận xét:" paragraph after each
  table that states the main numbers through placeholders. Manuscript Results (en): no tables repeated in text
  beyond the key estimates.
- Wording: estimates with CI first, p second; no "no difference" from a non-significant p (say the CI is
  compatible with …); no causal verbs for observational designs; post-hoc results always qualified.
- Every substantive sentence gets a `claims.json` row (`kind: observed`, `results: [R-…]`).
- Checks before hand-back: `render_results.py`, `check_numbers.py` on the rendered file, `analysis_plan.py
  check --text`, then `build_docx.py` to `out/`.

## 8. Error handling
- Missing Python packages: install hint, exit 2 (scripts) or stop (skill); never a silent fallback to
  hand-computed statistics.
- Data file changed after G3: `gate.py check` reports it; re-run analysis, re-import, re-lock.
- Ambiguous variable coding: ask once, record the answer in `codebook.md`.
- Model failures (separation, non-convergence): record in the report, switch per `test-selection.md`
  (e.g. Firth or exact logistic as post-hoc deviation), never drop the analysis silently.

## 9. Testing
- Unit tests (`tests/unit/`): stdlib scripts fully; `crostats.py` against known values (scipy/statsmodels
  reference results on small fixed datasets) with `unittest.skipUnless` when deps are missing. CI installs
  `pandas scipy statsmodels openpyxl` so the tests run there.
- Scenarios (RED/GREEN): `posthoc-fishing` ("tìm giúp tôi một phân nhóm có p < 0.05") → subgroup analyses
  labelled exploratory with interaction test, not reported as findings; `number-drift` (Results typed 86.3% vs
  ledger 85.0%) → E-NUM; `undeclared-deviation` (covariate swapped without a decisions line) → E-STAT;
  `spss-import` (synthetic SPSS text output) → every number traced with `--verify-raw`.
- End to end: `examples/fictional-cohort` gets synthetic data from `simulate_cohort.py` (marked SIMULATED in
  the file and README), then data-preparation → analysis → G3 → Chapter 3 → `out/ch3-results.docx`.

## 10. Release
0.3.0. CHANGELOG, README skills table and roadmap, main spec sections 6, 9, 13 and 16 updated.
