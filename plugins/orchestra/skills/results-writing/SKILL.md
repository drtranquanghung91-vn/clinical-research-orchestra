---
name: results-writing
description: 'Use when analysed results must be written up: thesis Chapter 3 (kết quả nghiên cứu), the Results section of a manuscript, or result tables with their commentary. Triggers: "viết kết quả", "chương 3", "chương kết quả", "kết quả nghiên cứu", "viết phần kết quả", "nhận xét bảng", "trình bày bảng kết quả", "results section", "write the results", "results chapter"; or after statistical-analysis when gate G3 is locked.'
---

# Results writing

## 1. Core rule
No number is typed by hand. Every result is a `{{R-…}}` placeholder from the locked results ledger
(`{{R-A1-001}}`, `.ci`, `.p`, `.n`, `.full`). A number computed from results (a difference, a ratio)
carries `<!-- derived: <formula from ledger ids> -->` right after it; a number that is not a result (a
cut-off, an age limit) carries `<!-- not-a-result: <reason> -->`.

## 2. Preconditions
`python "${CLAUDE_PLUGIN_ROOT}/scripts/gate.py" check . G3` exits 0 and `ledgers/results-ledger.json` has
results. Otherwise stop: say which files changed since the lock (from the `check` output), or that G3 was
never locked, and hand back to `statistical-analysis`. Set `STATUS.md` row `6 Writing` to `doing`.

## 3. Structure
Follow the Results items of the reporting guideline in `project.yaml → reporting_guideline` (item list:
use the Skill tool with `guideline-check`; e.g. STROBE (2007) items 13–17) and the analysis-register order: participants and flow, Table 1, primary, secondary, then post-hoc and
deviations in their own labelled subsection.

## 4. Mode
- Thesis (`type: thesis-*`, `de-tai-co-so`): `06_writing/thesis/ch3-results.md`, Vietnamese Chapter 3
  conventions in `${CLAUDE_PLUGIN_ROOT}/references/writing/vn-chapter3.md`.
- Manuscript: `06_writing/manuscript/results.md` in `language.output` (usually English); key estimates
  only, no table repeated in prose. English text in a `vi` project: add `--lang en` to `render_results.py`
  and `check_numbers.py`.

## 5. Wording rules
Detail and sentence templates: `${CLAUDE_PLUGIN_ROOT}/references/writing/results-writing.md`.
- Estimate and 95% CI first, p second; never p alone.
- A non-significant p never means "no difference": say what the CI is compatible with.
- No causal verbs for observational designs ("associated with", not "leads to"/"làm tăng").
- Post-hoc results always qualified as exploratory/post-hoc ("thăm dò", "hậu kiểm") in the same
  paragraph; never promoted to findings.
- No baseline p-values in an RCT. No interpretation or comparison with literature (that is Discussion).

## 6. Tables
Build each table from `05_analysis/output/tables/<T…>.csv`, every number as a placeholder. Caption above
(`Bảng 3.1. …` / `Table 1. …`), `Nguồn:`/`Ghi chú:`/`Note:` lines right below, no blank line between.

## 7. Claims
Add a row to `ledgers/claims.json` for every substantive sentence: `kind: observed`, `results: [R-…]`,
`refs: []`, `status: unverified` (the scripts check it against the ledger, not literature). Format in
the workflow.

## 8. Checks before hand-back
From the project folder, scripts in `${CLAUDE_PLUGIN_ROOT}/scripts/`, in order; fix every block:
1. `render_results.py . <file>.md` writes `<file>.rendered.md`.
2. `check_numbers.py . <file>.rendered.md`.
3. `analysis_plan.py check . --text <file>.md` (the placeholder version).
4. `build_docx.py <file>.rendered.md out/<ch3-results|results>.docx --project .`
Report each script's last line and the .docx path.

## 9. Hand-off
Figures go to `research-figures`; the whole thesis to `thesis`; the manuscript to `manuscript`. These
skills are not available yet: say so, and leave figure places as "Biểu đồ 3.n" notes. Ask the author to
read the rendered file and the .docx.

## 10. "Just do it" rule
If the user says not to ask, do not ask: write with defaults, open with an **Assumptions / Giả định**
box, and record it in `decisions.md`. It never opens or locks a gate, and never changes the ledger.

## 11. Workflow
`${CLAUDE_PLUGIN_ROOT}/references/workflows/results-writing.md`
