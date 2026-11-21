---
name: analyze
description: 'Run the statistical analysis for the current project per its SAP (chạy phân tích thống kê theo đề cương).'
disable-model-invocation: true
---

For the project in the current folder: if `04_data/` has no `*.deid.csv`, use the Skill tool with
`data-preparation` first. Then use the Skill tool with `statistical-analysis`. Finish with the
analysis_plan and results_ledger results and the next step (lock G3, then `/orchestra:results`), in the
user's language.
