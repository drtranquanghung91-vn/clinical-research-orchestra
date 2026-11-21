# Figures spec

`figures.py PROJECT [--only F1,F2] [--dpi 300]` reads `07_present/figures/figures.json` and writes, per figure,
`F<n>.svg`, `F<n>.pdf` (vector, editable text), `F<n>.png` (`--dpi`, default 300) and `F<n>.data.json` into
`07_present/figures/`. It needs matplotlib (`python -m pip install matplotlib`); without it the exit code is 2.

## Rules

- Every plotted estimate comes from the results ledger by id (`result`, or `"R-…"` inside a flow formula). The script
  never accepts a typed number for forest, rates or flow. An unknown id, a part that is not allowed (`.ci`), or a missing
  value exits 2 with the figure id in the message.
- Kaplan–Meier curves are computed from the de-identified CSV (`04_data/*.deid.csv` inside the project; anything else
  is refused) with a stdlib product-limit estimator. Never trace a curve from a picture and never use an AI-generated image.
- The KM source note is fixed: "Vẽ lại từ <file>" (vi) / "Redrawn from <file>" (en). A typed `source` is ignored for `km`.
  The file's SHA-256 is stored in `data.json`.
- Label semantics are set once per project in `style` and applied to every figure: colour per group, filled marker or bar =
  event or positive result, outlined = no event or negative (a row may carry `"filled": false`).
- Numbers printed in text columns use `crolib.numfmt` in the project output language (vi decimal comma, half-up rounding,
  same precision per result kind as the results document).
- A figure with no ledger id for a number it prints is a defect. Put the number in the ledger first (`results_ledger.py`).

## `figures.json`

```json
{"style": {"colors": {"<7": "#1f4e79", "7-9": "#c0504d"}, "font": "Arial", "font_size": 9, "width_cm": 16},
 "figures": [
  {"id": "F1", "type": "forest", "title": "…", "rows": [{"label": "HbA1c 7–9% vs <7%", "result": "R-A1-003"}],
   "null": 1, "log_scale": true, "x_label": "OR (KTC 95%)", "source": "Bảng 3.3"},
  {"id": "F2", "type": "km", "data": "04_data/cohort.deid.csv", "time": "time_to_readmit_days", "event": "readmit_1y",
   "group": "hba1c_group", "order": ["<7", "7-9", ">9"], "at_risk": [0, 90, 180, 270, 365], "max_time": 365,
   "time_unit": "ngày", "x_label": "…", "y_label": "…"},
  {"id": "F3", "type": "rates", "unit": "%", "rows": [{"label": "<7%", "result": "R-A0-062"}]},
  {"id": "F4", "type": "flow", "boxes": [{"text": "Hồ sơ đủ tiêu chuẩn", "n": "R-A0-001.n"}],
   "exclusions": [{"text": "Loại trừ", "n": "R-A0-001.n - R-A0-002.n", "after": 1}]}]}
```

- `style`: `colors` (group label to colour; unlisted groups take the default palette), `font` (default Arial, with
  DejaVu Sans as fallback), `font_size` (pt, default 9), `width_cm` (default 16; a figure may override it).
- `id`: letters, digits, `-`, `_`; unique. Output names are `<id>.*`.
- `forest`: rows need a whole result id with `value` and `ci`. Log x-axis when `log_scale`. Null line at `null` (default 1).
  Right-hand column "est (lo–hi)".
- `km`: columns `time`, `event` (1/0), `group`. `order` lists the group levels to draw; without it levels are sorted and a
  warning goes to stderr. Times above `max_time` are censored at `max_time`. `at_risk` lists the times of the table under
  the axis (default five evenly spaced). Rows with a blank time, event or group are skipped with a warning.
- `rates`: horizontal bars of `value` with CI whiskers when the record has `ci`; `unit` labels the axis.
- `flow`: boxes top to bottom; `n` is a ledger ref (`R-A0-001.n`) or a formula over ledger refs (same rules as
  `<!-- derived: -->`: numbers, ids, + - * / and parentheses). Each exclusion is a side box on the arrow after box `after`
  (1-based; default the position in the list).

## `F<n>.data.json`

Every number drawn, each with its ledger id or derivation, plus the chart description slides use to build native
PowerPoint charts. Top-level keys: `id`, `type`, `source`, `values`, `chart`, and for `km` also `data_file`, `data_sha256`.
Estimates are the raw ledger values; `text` is what the figure prints.

```json
{"id": "F1", "type": "forest", "source": "Bảng 3.3",
 "values": [{"label": "…", "ref": "R-A1-003", "est": 1.0975, "lo": 0.7423, "hi": 1.6228, "text": "1,10 (0,74–1,62)"}],
 "chart": {"kind": "forest", "log": true, "null": 1, "x_label": "…",
           "rows": [{"label": "…", "est": 1.0975, "lo": 0.7423, "hi": 1.6228}]}}
```

- `km`: `values` has one entry per group (`label`, `n`, `events`, `derivation`);
  `chart` = `{"kind": "km", "time_unit", "x_label", "y_label", "series": [{"name", "points": [[t, S], …]}],
  "at_risk": {"times": [...], "rows": [{"name", "n": [...]}]}}`. `points` is the step path (vertical drops are two points
  at the same time), survival rounded to 6 decimals. Number at risk at `t` = subjects with follow-up time ≥ `t`.
- `rates`: `chart` = `{"kind": "bar", "unit", "categories": […], "series": [{"name", "values": […]}], "labels": ["21,1% (16,1–27,1)", …]}`.
- `flow`: `chart` = `{"kind": "diagram", "nodes": [{"id", "text", "x", "y", "w", "h"}], "edges": [{"from", "to"}]}`;
  coordinates are fractions (0–1) of the content box, y from the top (the grand-rounds `diagram` slide format).
  Main boxes are `n1…`, exclusion boxes `x1…`; exclusion edges add `from_side: 2`, `to_side: 1`.
  `values` lists each box's `n` with its ref or formula.
