# Slide spec for `pptx_from_spec.py`

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/pptx_from_spec.py" SPEC OUT [--project DIR]
python "${CLAUDE_PLUGIN_ROOT}/scripts/check_pptx.py" OUT [--min-body 18] [--min-any 10] [--poster]
```

Both need `python-pptx` (`python -m pip install python-pptx`; missing → hint and exit 2).
Exit codes: `pptx_from_spec.py` 0 built, 2 any error (bad spec, unreadable file, unknown placeholder).
`check_pptx.py` 0 clean or only advisory findings, 1 serious findings (`off-slide`, `may-overflow`,
`tiny-text`), 2 unreadable file. Advisory: `small-body`, `no-alt-text`, `no-notes`.

The spec is a JSON file, for example `07_present/defense/deck.json`. Paths in it (`image`, `data`,
`template`) are relative to the spec's folder.

## Top level

```json
{
  "lang": "vi",
  "size_cm": [90, 120],
  "template": "../theme/template.pptx",
  "layouts": {"title": "Title Slide", "content": "Title Only", "closing": "Title Slide"},
  "theme": {
    "fonts": {"heading": "Arial", "body": "Arial"},
    "colors": {"primary": "#09B1BE", "ink": "#1A1A1A", "muted": "#666666", "line": "#D9D9D9",
               "intervention": "#D7262E", "control": "#5B6B82", "title_text": "#FFFFFF"},
    "type_pt": {"title": 32, "body": 20, "small": 14, "footer": 11}
  },
  "styles": {
    "title": {"size": 38, "bold": true, "color": "#FFFFFF", "caps": true, "align": "center"},
    "title_slide": {"size": 32, "bold": true, "color": "#E8141B", "caps": true},
    "subtitle": {"size": 22, "bold": true, "italic": true, "color": "#002060"}
  },
  "cite": "Source line shown in every slide footer",
  "page_numbers": true,
  "slides": [ ]
}
```

- `lang` (`vi` or `en`): language of built-in labels (the at-risk table header) and of placeholder
  rendering. Default: the project's `language.output` when `--project` is given, else `en`.
- `size_cm` `[width, height]`: slide size in centimetres, for a one-slide poster. Default 16:9
  (33.87 × 19.05 cm). Margins, font sizes and line widths scale with the width (1.0 at 13.333 in),
  so a 90 cm poster gets body text of about 53 pt. It overrides the size of a `template`. Each side is at most 142 cm (PowerPoint's limit); more exits 2.
- Leave out `template` for a clean deck drawn from `theme`. `layouts` maps slide kinds to the
  template's layouts, by name or, when two masters share a name, by part (`"slideLayout13"`). A slide
  may set `"layout"` to override.
- `styles` formats the template's placeholders when its own slides were formatted by hand. Keys:
  `title` (content slides), `title_slide`, `subtitle`. Each takes `size`, `bold`, `italic`, `color`,
  `caps`, `align`, `font`, `anchor` (`top`/`middle`/`bottom`) and `box_in` (`[left, top, width,
  height]` in inches).

## Placeholders (`--project`)

With `--project DIR`, every string in the spec is rendered before building: `{{R-A1-001}}`,
`{{R-A1-001.ci}}`, `.p`, `.n`, `.count`, `.full`, formatted from `DIR/ledgers/results-ledger.json`
with the project's reporting precision and, for `vi`, the decimal comma (`1,84`). An unknown id or a
part the record lacks exits 2, names where it occurs on stderr and lists the known ids; no file is
written. Without `--project`, strings are left as they are and a warning on stderr lists any `{{R-…}}`
placeholders still in the spec (exit code unchanged).

## Slide types

| type | fields |
|------|--------|
| `title`, `closing` | `title`, `subtitle`, `presenter` |
| `bullets` | `title`, `bullets`: strings or `{"text", "level", "bold", "color"}` |
| `figure` | `title`, `image` (PNG/JPG), `alt`, `credit`; optional `labels` (`[{"text", "at": [x, y], "side"}]`), `margin`, `label_pt` |
| `figure-text` | `title`, `image`, `alt`, `credit`, `bullets`, `split` (0–1, image share) |
| `big-number` | `title`, `numbers`: `[{"value", "label", "color"}]` (1–3), optional `bullets` |
| `table` | `title`, `columns`, `rows`, optional `col_widths` |
| `diagram` | `title`, then either `nodes` + `edges` or `data` (a `F<n>.data.json` whose `chart.kind` is `diagram`) |
| `chart` | `title`, `chart` (`bar`, `column`, `line`, `km`, `forest`), `credit`, `alt`; see below |
| `references` | `title`, `items` (formatted strings) |

Type names accept `-` or `_` (`big-number`, `big_number`). Every slide can carry `notes` (speaker
notes) and `cite` (overrides the deck footer).

### Chart slides

`bar`, `column`, `line` take `categories`, `series` (`[{"name", "values", "color"}]`), `number_format`
(default `0.0`). `bar` may instead take `"data": "figures/F3.data.json"`, which supplies
`chart.categories`, `chart.series` and `chart.labels`; `labels` (one text per category, e.g.
`"21,1% (16,1–27,1)"`) become custom data labels on the first series.

`km` and `forest` need `"data": "<path to F<n>.data.json>"`, the file `figures.py` writes; the slide
reads its `chart` object (format in `figures-spec.md`).

- `km`: native XY scatter chart with straight lines and no markers (`XY_SCATTER_LINES_NO_MARKERS`),
  one series per group, the y-axis 0–1 (0–100 % with `"percent": true`) and the x-axis from 0 to the
  largest time. When `chart.at_risk` exists, a native table sits under the chart: header row
  "Số người còn nguy cơ" (vi) or "Number at risk" (en) then one column per time, one row per group.
- `forest`: native XY scatter: an estimate series (square markers, first row at the top), one two-point
  line per confidence interval, a dashed vertical line at `null`. With `"log": true` the x-axis is
  logarithmic base 10 (`c:logBase`). Row labels are a native text column at left and
  "est (lo–hi)" a text column at right, both aligned to the plot area. The right column prints the
  figure's own text (`chart.rows[i].text`, else `values[i].text`), so the slide shows the ledger's
  precision and units; only when neither exists is the estimate re-formatted with 2 decimals.
- The `km` plot area is fixed (legend in a strip above it) so each at-risk column is centred under its
  time on the axis: the label column plus half of the first time column ends at the axis origin. The
  table is compact (0.28 in rows, 12 pt, no fill) and sits between the chart and the source note.
  `x_label` / `y_label` on the slide override the data file's axis titles.

When `credit` is not set on a chart slide, the figure's `source` (from the data file) is used.
All charts stay editable in PowerPoint (right-click, Edit Data).

### Diagram coordinates

`x, y, w, h` are fractions (0–1) of the content area below the title. `style` is `default`,
`int` (intervention arm), `ctl` (control arm), `primary` (filled, white text) or `muted`. `shape` may
be `circle`. Boxes are square-cornered; `"rounded": true` (on the slide or on a node) opts in. A node's `text` is a string (newlines start new lines) or a list of lines; the first
line is bold. Connector sides: 0 top, 1 left, 2 bottom, 3 right; the default runs from the right
side of `from` to the left side of `to`. Edges that come from a figure `data.json` carry no usable
sides (figures.py numbers them differently), so the sides are inferred from the node geometry: a
target to the right or left of the source is joined side to side (elbow when the rows differ),
otherwise bottom to top (target below) or top to bottom. Sides written in the spec are kept.

## Checks (`check_pptx.py`)

`off-slide` (a shape beyond the slide edge), `may-overflow` (estimated text taller than its box),
`tiny-text` (below `--min-any`, default 10 pt), `small-body` (a `Body` text box below `--min-body`,
default 18 pt), `no-alt-text` (picture without a description), `no-notes` (no speaker notes).
`--poster` scales both floors by the slide width, 24 pt body at 90 cm wide (so about 13 pt for any
text), and skips the notes check. `--render DIR` exports PNGs through PowerPoint or LibreOffice where
installed (not needed for the checks).

## Defence deck example

Placeholders resolve from the project ledger; figures come from `figures.py`.

```json
{
  "lang": "vi",
  "cite": "Nguyễn Văn A. Luận văn bác sĩ nội trú, 2026",
  "slides": [
    {"type": "title", "title": "Yếu tố liên quan đến biến chứng sau mổ",
     "subtitle": "Bảo vệ luận văn bác sĩ nội trú", "presenter": "Nguyễn Văn A",
     "notes": "Chào hội đồng; nêu tên đề tài và người hướng dẫn."},
    {"type": "bullets", "title": "Nội dung trình bày",
     "bullets": ["Đặt vấn đề và mục tiêu", "Đối tượng và phương pháp", "Kết quả", "Bàn luận và kết luận"],
     "notes": "Bốn phần, khoảng 15 phút."},
    {"type": "bullets", "title": "Mục tiêu nghiên cứu",
     "bullets": ["Mô tả tỷ lệ biến chứng: {{R-A0-001}}", "Xác định yếu tố liên quan"],
     "notes": "Đọc mục tiêu đúng như trong đề cương."},
    {"type": "chart", "chart": "km", "title": "Tỷ lệ không biến chứng theo nhóm",
     "data": "../figures/F2.data.json", "percent": true,
     "notes": "Log-rank p {{R-A2-001.p}}; đọc số người còn nguy cơ ở các mốc."},
    {"type": "chart", "chart": "forest", "title": "Yếu tố liên quan (OR hiệu chỉnh)",
     "data": "../figures/F1.data.json",
     "notes": "Tuổi: OR {{R-A1-001}} (KTC 95% {{R-A1-001.ci}})."},
    {"type": "table", "title": "Đặc điểm mẫu", "columns": ["Đặc điểm", "n (%)"],
     "rows": [["Nữ", "{{R-A0-002.full}}"], ["Tuổi ≥ 65", "{{R-A0-003.full}}"]],
     "notes": "Bảng 1 của luận văn."},
    {"type": "big_number", "title": "Kết quả chính",
     "numbers": [{"value": "{{R-A0-001}}", "label": "tỷ lệ biến chứng"},
                 {"value": "{{R-A1-001}}", "label": "OR hiệu chỉnh"}],
     "notes": "Một câu cho mỗi số."},
    {"type": "references", "title": "Tài liệu tham khảo",
     "items": ["Tác giả A, et al. Tên bài. Tạp chí. 2024;12:34-45."], "notes": "Không đọc."},
    {"type": "closing", "title": "Xin cảm ơn hội đồng", "notes": "Sẵn sàng trả lời câu hỏi."}
  ]
}
```

Build and check:

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/pptx_from_spec.py" 07_present/defense/deck.json 07_present/defense/deck.pptx --project .
python "${CLAUDE_PLUGIN_ROOT}/scripts/check_pptx.py" 07_present/defense/deck.pptx
```

A poster is one slide of the same spec with `"size_cm": [90, 120]`; check it with `--poster`.

## Figures for PPTX

python-pptx cannot embed SVG. Prefer native `chart` and `diagram` slides (editable); for a picture,
use the PNG that `figures.py` writes at 300 dpi.
