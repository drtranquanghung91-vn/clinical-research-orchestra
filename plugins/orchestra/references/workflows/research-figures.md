# Research figures: full workflow

Spec and `figures.json` format: `${CLAUDE_PLUGIN_ROOT}/references/presenting/figures-spec.md`. Scripts are
in `${CLAUDE_PLUGIN_ROOT}/scripts/`; run them from the project folder.

## 1. Preconditions
1. `python "${CLAUDE_PLUGIN_ROOT}/scripts/gate.py" check . G3` exits 0 (or a `WAIVE G3:` line exists:
   say so in the hand-off). Exit 1: stop and use the Skill tool with `statistical-analysis`.
2. `ledgers/results-ledger.json` has results; de-identified data for KM is `04_data/*.deid.csv`.
3. `python -m pip install matplotlib` if `figures.py` exits 2 for a missing module.

## 2. Figure plan
From `03_protocol/sap.md` and `05_analysis/analysis-report.md`: primary and adjusted estimates to a
forest plot, a time-to-event outcome to KM, group rates to a rates chart, selection counts to a flow
diagram. Show the plan (id, type, source table) to the author before drawing.

## 3. Write figures.json
`07_present/figures/figures.json`. Every estimate is a ledger id; every flow box `n` is a ledger ref or a
formula over refs. For KM give `time`, `event`, `group`, `order`, `max_time`, and `at_risk` times; the
default at-risk times are every quarter of `max_time`. Set `style` once: colour per group, filled
marker or bar for an event or positive result, outlined for none (`"filled": false` per row).
Output language follows `project.yaml → language.output` (vi uses a decimal comma).

## 4. Draw and inspect
`python "${CLAUDE_PLUGIN_ROOT}/scripts/figures.py" . --only F1,F2 --dpi 300`. Exit 2 names the figure and
the problem. Then open each PNG or SVG: labels readable, CI whiskers present, null line, group colours as
in `style`, no clipped text.

## 5. Checks
`check_numbers.py` does not run on figures. Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/consistency_audit.py" .`:
it reads the strings of every `07_present/**/*.json`, so a figure value that contradicts the text is
caught. A figure number with no ledger id is a defect: fix the ledger, not the figure.

## 6. Where outputs go
| Target | File |
|---|---|
| Word, thesis | `F<n>.svg` or `F<n>.pdf` (vector) |
| Slides | native chart built from `F<n>.data.json` (`chart` key) |
| Poster | `F<n>.svg` |
| Quick look, web | `F<n>.png` (300 dpi) |

Caption above the figure, source line below ("Nguồn: Bảng 3.3", or the KM "Vẽ lại từ" note).

## 7. Hand-off
List figure ids, types, source ledger ids or files, and the checks run. The author reads each figure.
Leave the thesis chapter's "Biểu đồ 3.n" notes in place until the author accepts the figures.
