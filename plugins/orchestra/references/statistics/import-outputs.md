# Importing results from SPSS, Stata or R (import mode)

Used by `statistical-analysis` when the author ran the analysis outside this project. The rules of run
mode still apply: the SAP decides, every number is traceable to a file, and post-hoc or deviating analyses
need their `POST-HOC A<n>:` / `DEVIATION A<n>:` line in `decisions.md`. The agent never retypes a number
that is not in an exported file and never recomputes one by hand.

## 1. Ask the author to export

Exports go into `00_inputs/` (a copy; the original stays where it is). Text, CSV and Excel `.xlsx` can be
checked by `results_ledger.py --verify-raw`; PDF and `.spv`/`.smcl` files cannot, so ask for one of the
three.

| Software | How to export |
|---|---|
| SPSS | Output viewer → File → Export → type "Excel" (`.xlsx`) or "Text" (`.txt`); export all visible objects of the analysis. Syntax users: `OUTPUT EXPORT /XLSX DOCUMENTFILE='…'.` |
| Stata | `log using "00_inputs/a1-logistic.log", text replace` before the commands and `log close` after; for model tables `esttab using "00_inputs/a1.csv", csv ci eform replace` (package `estout`) |
| R | `write.csv(broom::tidy(model, conf.int = TRUE, exponentiate = TRUE), "00_inputs/a1.csv", row.names = FALSE)` for models; `sink("00_inputs/a1-output.txt")` … `sink()` for printed output |

Each export file name starts with the analysis ID it serves (`a1-…`), so the author and the reviewer can
match files to the register. Ask the author also for the de-identified data file the software read; it
must be `04_data/<name>.deid.csv` (else use the Skill tool with `data-preparation` first).

## 2. Write `05_analysis/output/results.json` by hand

Same contract as run mode (spec §6.1):
- top level: `engine` (software and version, as the author reports it), `data_file`
  (`04_data/<name>.deid.csv`), `data_sha256` (compute it:
  `python -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" 04_data/<name>.deid.csv`),
  `run_at` (date of the author's run), `results`, `tables`;
- one record per number that the report or Results will cite: `id` `R-A<n>-<3 digits>`, `analysis_id`,
  `status` (`prespecified`, `posthoc`, `deviation`), `label`, `value`, `kind`, optional `ci`, `p`, `n`,
  `unit`, `table`;
- **`source_file`** (the export in `00_inputs/`), **`locator`** (`line N` for text and CSV, counted from 1;
  `Sheet!A1` for an `.xlsx` cell) and **`raw`** (the exact text found there, copied character for
  character). `value` must appear in `raw` at its printed precision. Copy `ci` and `p` from the same line.

Then run, from the project folder:

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/results_ledger.py" import . --verify-raw
python "${CLAUDE_PLUGIN_ROOT}/scripts/analysis_plan.py" check .
```

`--verify-raw` fails (exit 1, nothing written) when `raw` is not at `locator` or `value` is not in
`raw`; fix the record, never the export file.

## 3. Worked example (synthetic)

`00_inputs/a1-spss-logistic.txt`, exported from SPSS as text (synthetic numbers):

```
Variables in the Equation: B  S.E.  Wald  df  Sig.  Exp(B)  95% CI Lower  Upper
hba1c_high  .610  .213  8.201  1  .004  1.840  1.212  2.794
age  .021  .009  5.444  1  .020  1.021  1.003  1.039
```

Its two records in `results.json`:

```json
{"id": "R-A1-001", "analysis_id": "A1", "status": "prespecified", "label": "adjusted OR, HbA1c ≥ 8% vs < 8%",
 "value": 1.84, "ci": [1.212, 2.794], "p": 0.004, "kind": "or", "table": "T3.2",
 "source_file": "00_inputs/a1-spss-logistic.txt", "locator": "line 2",
 "raw": "hba1c_high  .610  .213  8.201  1  .004  1.840  1.212  2.794"},
{"id": "R-A1-002", "analysis_id": "A1", "status": "prespecified", "label": "adjusted OR, age per year",
 "value": 1.021, "ci": [1.003, 1.039], "p": 0.02, "kind": "or", "table": "T3.2",
 "source_file": "00_inputs/a1-spss-logistic.txt", "locator": "line 3",
 "raw": "age  .021  .009  5.444  1  .020  1.021  1.003  1.039"}
```

SPSS prints `Sig.` as `.004`; write `p` as `0.004`. `Exp(B)` is the OR; `B` is not recorded unless the
report cites it. A `value` of `1.85` here would fail `--verify-raw` because `1.85` is not in `raw`.

## 4. Status and tables

- A result the SAP's register lists is `prespecified`; anything else the author ran is `posthoc` or
  `deviation` and needs its line in `decisions.md` before import.
- Tables: write the table the report needs as `05_analysis/output/tables/<T…>.csv` from the export
  (copy, do not recompute) and list it under `tables` with its `analysis_ids`.
- The report, checks and hand-off are the same as run mode (`analysis-report-template.md`).
