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
1. Copy nothing out of `00_inputs/`. Use the Skill tool with `deidentify-data` (plugin `phi-guard`) to
   write `04_data/<name>.deid.csv` and the key files. Keys stay on this machine, out of git.
2. Codebook `04_data/codebook.md` from `variables.md` and the data: type, unit, coding, source column.
3. Audit with `crostats.audit` in a short script under `05_analysis/`: rows, duplicates, missing, and
   outliers by IQR × 1.5 (a default, `${CLAUDE_PLUGIN_ROOT}/references/judgement-defaults.md`).
   Outliers are flagged, never removed.
4. Cleaning rules only for impossible values, coding errors and documented duplicates. Log each in
   `04_data/cleaning-log.md` with rows affected. Ambiguous coding: ask once, then write the answer in
   the codebook.
5. Scan the two documents with the `phi-guard` plugin's script:
   `python "<phi-guard>/scripts/phi_scan.py" --file 04_data/codebook.md 04_data/cleaning-log.md`
   (exit 1 means a strong identifier: remove it and rerun).
6. Never look at outcome-by-exposure results here; that belongs to the SAP and
   `statistical-analysis`.
7. Set `STATUS.md` row 4 (`4 Data`) to `done` after the author confirms, then hand off to
   `statistical-analysis`.

## 4. "Just do it" rule
If the user says not to ask, do not ask. Open with an **Assumptions / Giả định** box listing the
coding and cleaning choices made, and record it in `decisions.md`. It never opens a gate.

## 5. Output
`04_data/<name>.deid.csv`, `04_data/codebook.md`, `04_data/cleaning-log.md`, in
`project.yaml → language.output`. Only these three are versioned; keys and raw data are not.

## 6. Workflow
`${CLAUDE_PLUGIN_ROOT}/references/workflows/data-preparation.md`
