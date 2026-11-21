# Statistical analysis: full workflow

Analysis workflow adapted from the owner's `stat-analysis-vi` skill. Thresholds are **defaults** the
author may override (`${CLAUDE_PLUGIN_ROOT}/references/judgement-defaults.md`); record an override in
`decisions.md`. Test tables: `${CLAUDE_PLUGIN_ROOT}/references/statistics/stat-tests.md`; design-level test
choice: `${CLAUDE_PLUGIN_ROOT}/references/statistics/test-selection.md`; report:
`${CLAUDE_PLUGIN_ROOT}/references/statistics/analysis-report-template.md`; import mode:
`${CLAUDE_PLUGIN_ROOT}/references/statistics/import-outputs.md`.

## Core rule

The SAP decides what is analysed. Every number comes from code (`05_analysis/analysis.py`) or from the
author's exported output file, never from mental arithmetic. Post-hoc analyses are allowed when the author
asks or agrees; they are declared in `decisions.md`, carry status `posthoc`, are labelled exploratory in
every document, and are never promoted to primary or reported without their label.

## Preconditions

1. `python "${CLAUDE_PLUGIN_ROOT}/scripts/gate.py" check . G2` exits 0 (open, or waived by a `WAIVE G2:`
   line in `decisions.md`). Closed: stop and ask the author to approve the protocol and SAP.
2. `04_data/*.deid.csv` exists; otherwise use the Skill tool with `data-preparation`.
3. `03_protocol/sap.md` has `## Analysis register` (check with
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/analysis_plan.py" register .`); otherwise use the Skill tool with
   `sample-size-sap`. `A0` is reserved for Table 1; IDs are never reused.
4. Set `STATUS.md` row `5 Analysis` to `doing`.

## Mode

- **Run mode**: the data are in the project and the author wants the analysis run here.
- **Import mode**: the author ran SPSS, Stata or R; follow `import-outputs.md`, then continue at step 5.

## Run mode

1. **Read** `sap.md` (register, covariates, multiplicity), `project.yaml` (design, `language.output`),
   `04_data/codebook.md` and the data's columns. From them take design, primary outcome and its type,
   exposure, covariates and unit of analysis. Ask **one question only**, and only when the primary
   outcome, the unit of analysis or the patient ID for repeated measures cannot be identified
   (`stat-tests.md` §10). Everything else: infer and list the assumption in the report's test-choice
   section.
2. **Vendor the library.** If absent, copy `${CLAUDE_PLUGIN_ROOT}/scripts/crostats.py` to
   `05_analysis/crostats.py` (a single self-contained file) with the first line
   `# copied from clinical-research-orchestra <version> on <date>; do not edit` (version from
   `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`), unless `data-preparation` already copied it.
3. **Write `05_analysis/analysis.py`** (skeleton below): one block per register row in ID order, each
   headed `# A<n> <objective>`, with the register's method and covariates exactly. Seeded (`crostats` seeds
   its permutations); no network; reads only the `.deid.csv`. Methods `crostats` lacks are written with
   scipy or statsmodels: `rec.log` the choice and its reason, `rec.add` each number.
4. **Run** from the project folder: `python 05_analysis/analysis.py`. On `ImportError` print
   `python -m pip install pandas scipy statsmodels openpyxl` (add `lifelines` when the SAP has a Cox model)
   and stop; never fall back to computing by hand. Read `05_analysis/output/log.txt` for every test choice,
   warning and `MODEL FAILED` line.
5. **Checks**: `python "${CLAUDE_PLUGIN_ROOT}/scripts/analysis_plan.py" check .` then
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/results_ledger.py" import .` (import mode: add `--verify-raw`).
   Fix every block finding; in run mode never edit `results.json` by hand (fix and rerun the script).
6. **Report** `05_analysis/analysis-report.md` per the template, numbers as `{{R-…}}`, then run
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/render_results.py" . 05_analysis/analysis-report.md`,
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/check_numbers.py" . 05_analysis/analysis-report.md` and
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/analysis_plan.py" check . --text 05_analysis/analysis-report.md`.
   All exit 0 before hand-back. A Word copy for the supervisor, if asked:
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/build_docx.py" 05_analysis/analysis-report.rendered.md out/analysis-report.docx --project .`

## `analysis.py` skeleton

Column names, groups and IDs are examples; take them from the register and the codebook.

```python
"""Analysis for this project: every analysis in the SAP register (03_protocol/sap.md), in ID order.
Reads only 04_data/cohort.deid.csv; writes 05_analysis/output/{results.json, log.txt, tables/}.
Run from the project folder: python 05_analysis/analysis.py
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # the vendored 05_analysis/crostats.py
try:
    import crostats
except ImportError as e:
    sys.exit(f"{e}\nInstall: python -m pip install pandas scipy statsmodels openpyxl (and lifelines for Cox)")

PROJECT = HERE.parent
DATA = "04_data/cohort.deid.csv"
df = crostats.load_data(PROJECT / DATA)
rec = crostats.Recorder(PROJECT, DATA)

# A0 descriptive statistics (Table 1); show_p=False in an RCT
crostats.table1(df, ["age", "sex", "egfr", "hba1c"], "hba1c_high", rec, "T3.1", "Baseline characteristics")

# A1 primary: readmission by HbA1c group, crude then adjusted (covariates from the register)
crostats.compare_props(df, "readmit", "hba1c_high", rec, "A1", table="T3.2")
d = df.dropna(subset=["readmit", "hba1c_high"])
a = int(((d.hba1c_high == 1) & (d.readmit == 1)).sum()); b = int(((d.hba1c_high == 1) & (d.readmit == 0)).sum())
c = int(((d.hba1c_high == 0) & (d.readmit == 1)).sum()); e = int(((d.hba1c_high == 0) & (d.readmit == 0)).sum())
ce = crostats.crude_effect(a, b, c, e)  # records nothing itself
rec.log(f"A1 crude OR: Woolf CI; Haldane correction {'applied' if ce['corrected'] else 'not needed'}")
est, lo, hi = ce["or"]
rec.add("A1", "prespecified", "crude OR, HbA1c >= 8% vs < 8%", est, "or", ci=[lo, hi], n=a + b + c + e, table="T3.2")
m = crostats.fit_logistic(df, "readmit", ["hba1c_high", "age", "C(sex)", "egfr"], rec, "A1", table="T3.2")
if m["failed"]:
    print(f"A1 model failed: {m['reason']} (report it; a replacement is a DEVIATION A1 analysis)")

# A2 key secondary: length of stay, difference stated as "1 − 0"
crostats.compare_two(df, "los", "hba1c_high", rec, "A2", order=(1, 0))

# A7 POST-HOC (decisions.md: "POST-HOC A7: <reason>, requested by <author>, <date>")
r = crostats.roc_youden(df["readmit"], df["hba1c"])  # records nothing itself
rec.log("A7 ROC of hba1c for readmit (post-hoc): Youden cut-off over unique values")
rec.add("A7", "posthoc", "AUC, HbA1c for readmission", r["auc"], "auc", n=int(df[["readmit", "hba1c"]].dropna().shape[0]))
rec.add("A7", "posthoc", "Youden cut-off, HbA1c", r["cutoff"], "other", unit="%")
rec.add("A7", "posthoc", "sensitivity at the cut-off", 100 * r["sens"], "percent")
rec.add("A7", "posthoc", "specificity at the cut-off", 100 * r["spec"], "percent")

# A8 POST-HOC subgroup: the interaction p, never a significance claim per subgroup
p_int = crostats.interaction(df, "readmit", "hba1c_high", "sex", ["age", "egfr"], family="logit")
rec.add("A8", "posthoc", "p for interaction, HbA1c group x sex", p_int, "p")

print(rec.save())
```

`compare_two`, `compare_k`, `compare_props`, `table1` and `fit_logistic` / `fit_linear` / `fit_poisson` /
`fit_cox` record their own results; `crude_effect`, `roc_youden` and `interaction` do not, so the script
calls `rec.add` itself (OR kind `or`, AUC kind `auc`, interaction p kind `p`).

## Post-hoc and deviating analyses

- Allowed only after the author asks or agrees. Before running, add one line to `decisions.md`:
  `POST-HOC A<n>: <reason>, requested by <author>, <date>` or
  `DEVIATION A<n>: <what changed and why>, <date>` (optionally preceded by `- `). A new post-hoc analysis
  takes the next unused `A<n>`; a deviation keeps the registered ID.
- Status `posthoc` or `deviation` in every `rec.add` and `crostats` call of that block.
- Post-hoc unless registered: univariable screening (p < 0.20), backward or other data-driven selection,
  ROC/Youden cut-offs, extra subgroups, sensitivity analyses. They never change the covariates of a
  pre-specified model.
- A registered analysis that is not run needs `DEVIATION A<n>: not done because <reason>, <date>`.
- No baseline p-values in an RCT (CONSORT; `sap-template.md` §7): `table1(..., show_p=False)`.
- Subgroups: interaction test only.
- A request to "find a subgroup with p < 0.05": explain the multiplicity risk; run only what the author
  then confirms, as post-hoc.

## Model failure (spec §8)

A `crostats` model that meets separation, non-convergence or collinearity returns `{"failed": True,
"reason": …}`, records nothing and logs `MODEL FAILED A<n>: <reason>; <advice>`. Then:
1. Never drop the analysis silently: report it as failed in its section, with the reason.
2. Ask the author whether to replace it. A replacement (Firth or exact logistic, Firth-penalised Cox,
   merged sparse categories, fewer terms) is a `DEVIATION A<n>:` analysis with status `deviation`, written
   in `analysis.py` (Firth and exact methods need a package outside `crostats`; log its name and version).
3. If it is not replaced: `DEVIATION A<n>: not done because <reason>, <date>`.

EPV < 10 (default) does not fail a model: report the adjusted estimates as exploratory with the EPV caveat.

## Traceability

- `results.json` carries the data file's SHA-256; `gate.py check` reports a changed file after G3: rerun,
  re-import, re-lock.
- Each run-mode result's `raw` is its log line and its `locator` is `line <k>` of
  `05_analysis/output/log.txt`.
- The script, the vendored library and the data file are locked with the ledger at G3.

## Hand-off

Show the author the rendered report. After review, the author locks G3:
`python "${CLAUDE_PLUGIN_ROOT}/scripts/gate.py" lock . G3 --by "<author>" --files ledgers/results-ledger.json 05_analysis/output/results.json 05_analysis/analysis.py 05_analysis/crostats.py 04_data/<file>.deid.csv`

Import mode locks the files actually used:
`python "${CLAUDE_PLUGIN_ROOT}/scripts/gate.py" lock . G3 --by "<author>" --files ledgers/results-ledger.json 05_analysis/output/results.json 00_inputs/<export file> … 04_data/<file>.deid.csv`
(one entry per export file the records cite). The `00_inputs/` exports are hashed locally by `gate.py` but
not versioned (git ignores `00_inputs/`). This skill never locks G3 itself. Set `STATUS.md` row 5 to `done` once the author accepts the report; the next step
is `/orchestra:results` (`results-writing`).
