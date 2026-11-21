# Data preparation: full workflow

Defaults here (IQR × 1.5 for outliers) are defaults the author may override, not standards
(`${CLAUDE_PLUGIN_ROOT}/references/judgement-defaults.md`); record an override in `decisions.md`.

## Codebook template (`04_data/codebook.md`)

| Variable | Type | Unit | Coding | Source column | Notes |
|---|---|---|---|---|---|
| sbp_adm | numeric | mmHg | continuous | Huyết áp tâm thu | measured at admission |

## Cleaning-log template (`04_data/cleaning-log.md`)

| Date | Rule | Variable | Rows affected | Reason | Reversible? |
|---|---|---|---|---|---|
| 2026-11-21 | set to missing when sbp_adm < 40 or > 300 | sbp_adm | 2 | impossible value (typing error) | yes, raw file unchanged |

Each rule is a sentence another person can re-apply to the raw file. Reversible means the original
value can be recovered from `00_inputs/`.

## Vendored library and audit script skeleton

Projects carry their own copy of the library so scripts rerun without the plugin. If
`05_analysis/crostats.py` is absent, copy `${CLAUDE_PLUGIN_ROOT}/scripts/crostats.py` there and make
its first line (version from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`):

```
# copied from clinical-research-orchestra <version> on <date>; do not edit
```

`05_analysis/audit.py`:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import crostats

df = crostats.load_data("04_data/study.deid.csv")  # refuses anything but *.deid.csv
a = crostats.audit(df)
print(f"rows {a['rows']}  duplicate rows {a['duplicates']}")
print("variable | missing | outliers (IQR x 1.5)")
for col, miss in a["missing"].items():
    print(f"{col} | {miss} | {a['outliers'].get(col, '')}")
```

Run it from the project folder.

## Missing data

Describe the pattern only: count and percent per variable, whether missingness clusters by group or
time, and what the codebook says a blank means. Never impute here. Imputation is a method choice that
belongs to the SAP (`03_protocol/sap.md`); if the SAP is silent, report the pattern and let the
author decide in `decisions.md`. Do not drop rows or variables because they are incomplete.

## Excel and SPSS exports

- Excel: File → Save as → CSV UTF-8 (comma delimited), one sheet per file, header in one row.
  Title rows above the header are tolerated by `deidentify-data` (`--header-row N` if needed).
- SPSS: File → Export → CSV; keep the data as numeric codes and export the value labels as a separate
  list, then copy them into the codebook `Coding` column.
- R and other tools: write CSV UTF-8, no row names.

## Privacy reminders

- Key files (`<stem>.key.csv`, `<stem>.key-episodes.csv`) and everything in `00_inputs/` never leave
  this machine and are never committed; the project `.gitignore` template excludes them and versions
  only `04_data/*.deid.csv`, `codebook.md` and `cleaning-log.md`.
- The codebook and cleaning log must carry no identifiers; scan them with `phi_scan.py --file`
  before saving the step as done.
- Detection in `deidentify-data` is heuristic: free-text columns need a human check.
