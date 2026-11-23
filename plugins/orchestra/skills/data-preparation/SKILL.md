---
name: data-preparation
description: 'Use when raw study data (Excel, CSV, SPSS export) must be checked, cleaned, coded or de-identified before analysis, or when a codebook or data dictionary is needed. Triggers: "làm sạch dữ liệu", "xử lý số liệu thô", "nhập liệu", "mã hóa biến", "từ điển biến", "codebook", "data dictionary", "kiểm tra dữ liệu", "dữ liệu thiếu", "missing data", "outlier", "clean my data", "prepare the dataset"; or before statistical-analysis when no 04_data/*.deid.csv exists.'
---

# Data preparation

## 1. Core rule
Analysis reads only de-identified `04_data/*.deid.csv`. Raw files stay in `00_inputs/` and are never
edited. Every change to the data is a logged, reproducible rule; nothing is changed by hand.

## 2. Inputs
`00_inputs/<raw file>`, `03_protocol/variables.md` and `03_protocol/sap.md`. Ask once for what is
missing (for example which sheet or header row).

## 3. Steps
Set `STATUS.md` row 4 (`4 Data`) to `doing` first.
1. Copy nothing out of `00_inputs/`. Use the Skill tool with `deidentify-data` (plugin `phi-guard`);
   its output folder must be `04_data/`:
   `python "<path>/deidentify.py" 00_inputs/<raw file> --out 04_data`. This writes
   `<name>.deid.csv` plus the key files; move the key files out of the project or leave them
   git-ignored as the template does. They never leave this machine.
2. Codebook `04_data/codebook.md` from `03_protocol/ethics/data-dictionary.csv` when it exists (keep its variable names, types and value lists), else from `variables.md`, and the data: type, unit, coding, source column.
3. Vendor the library: if absent, copy `${CLAUDE_PLUGIN_ROOT}/scripts/crostats.py` to
   `05_analysis/crostats.py` with the first-line comment from the workflow file. Then audit with
   `crostats.audit` in `05_analysis/audit.py`: rows, duplicates, missing, and outliers by
   IQR × 1.5 (a default, `${CLAUDE_PLUGIN_ROOT}/references/judgement-defaults.md`). Outliers are
   flagged, never removed.
4. Cleaning rules only for impossible values, coding errors and documented duplicates. Log each in
   `04_data/cleaning-log.md` with rows affected. Ambiguous coding: ask once, then write the answer in
   the codebook.
5. Scan the two documents with the `phi_scan.py` in the same `scripts/` folder as the `deidentify.py`
   that skill used (find it by searching for `phi-guard/scripts/phi_scan.py` if unsure):
   `python phi_scan.py --file 04_data/codebook.md 04_data/cleaning-log.md`
   (exit 1 means a strong identifier: remove it and rerun).
6. Never look at outcome-by-exposure results here; that belongs to the SAP and
   `statistical-analysis`.
7. After the author confirms, set row 4 to `done` and hand off to `statistical-analysis`.

## 4. "Just do it" rule
If the user says not to ask, do not ask. Open with an **Assumptions / Giả định** box listing the
coding and cleaning choices made, and record it in `decisions.md`. It never opens a gate.

## 5. Output
`04_data/<name>.deid.csv`, `04_data/codebook.md`, `04_data/cleaning-log.md`, in
`project.yaml → language.output`. Only these three are versioned; keys and raw data are not.

## 6. Workflow
`${CLAUDE_PLUGIN_ROOT}/references/workflows/data-preparation.md`
