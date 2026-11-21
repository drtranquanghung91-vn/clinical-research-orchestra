# Poster spec

`poster_build.py PROJECT [SPEC] [--layout editorial|pathway|figure-led] [--browser PATH] [--no-pptx] [--pptx-required]`
reads `07_present/poster/poster.json` (or SPEC) and writes, per layout, into `07_present/poster/`:

| file | what |
|------|------|
| `<layout>.html` | self-contained page: CSS and `preflight.js` inlined, figure SVGs inlined, PNGs referenced relative |
| `<layout>.pdf` | print file at the poster size plus bleed (headless Chrome or Edge) |
| `<layout>.png` | preview, long side about 2000 px |
| `<layout>.dom.html` | DOM after `preflight.js`: `data-overflow`, placed and natural image sizes (read by `poster_preflight.py`) |
| `<layout>.spec.json` | the fixed-grid canvas the PPTX is built from (rectangles, text, tables, figure PNGs, in cm) |
| `<layout>.pptx` | one editable slide at the poster size; needs python-pptx |

Without Chrome or Edge the HTML and PPTX are still written and the exit code is 2. Browser lookup: `--browser`, then
`msedge`, `chrome`, `google-chrome`, `google-chrome-stable`, `chromium`, `chromium-browser` on PATH, then the usual
Windows and macOS install paths. Without python-pptx the PPTX is skipped with a note (exit 2 only with `--pptx-required`).
Placeholders `{{R-A1-003}}`, `.ci`, `.p`, `.n`, `.count`, `.full` are rendered from the results ledger in every string of
the spec (vi uses the decimal comma); an unknown id exits 2 and nothing is written.

## `poster.json`

```json
{
  "size_cm": [90, 120],
  "bleed_mm": 3,
  "lang": "vi",
  "font": "Arial, \"Liberation Sans\", sans-serif",
  "layouts": ["editorial", "pathway", "figure-led"],
  "title": "HbA1c lúc nhập viện và tái nhập viện trong 1 năm ở người bệnh đái tháo đường type 2",
  "authors": "Nguyễn Văn A, Trần Thị B",
  "affiliation": "Bệnh viện Mô phỏng",
  "logo": "00_inputs/logo.png",
  "key_message": "HbA1c >9% đi kèm nguy cơ tái nhập viện vì đái tháo đường gấp {{R-A3-002}} lần (KTC 95% {{R-A3-002.ci}}).",
  "hero": "F2",
  "colors": {"accent": "#1f4e79", "tint": "#e3ebf3"},
  "sections": [
    {"heading": "Đặt vấn đề", "body": "Đoạn văn với **chữ đậm**.\n\n- mục một\n- mục hai"},
    {"heading": "Phương pháp", "body": "Hồi cứu {{R-A0-001.n}} hồ sơ.",
     "checklist": [{"text": "Báo cáo theo STROBE", "checked": true}, "Kiểm tra giả định"]},
    {"heading": "Thời gian đến tái nhập viện", "body": "Mô tả ngắn.",
     "figure": {"id": "F2", "caption": "**Hình 1.** Kaplan–Meier.", "alt": "Đường Kaplan–Meier ba nhóm HbA1c"}},
    {"heading": "Kết quả hiệu chỉnh",
     "body": "OR {{R-A1-003}}.\n\n| Chỉ số | Giá trị |\n|---|---|\n| AUC | {{R-A1-009}} |",
     "figure": {"id": "F1", "caption": "**Hình 2.** OR hiệu chỉnh.", "alt": "Biểu đồ rừng"}},
    {"heading": "Xét nghiệm", "lab_table": [
      {"test": "HbA1c", "value": "9,4", "unit": "%", "flag": "high"},
      {"test": "Hemoglobin", "value": "10,8", "unit": "g/dL", "flag": "low"}]},
    {"heading": "Kết luận", "body": "Một hai câu."}
  ],
  "references": ["Tài liệu 1.", "Tài liệu 2."],
  "contact": "Liên hệ: nhom@example.org"
}
```

- `size_cm` (default `target.poster_size_cm` in `project.yaml`, else 90 × 120; at most 142 per side), `bleed_mm` (default 3; 0 for none),
  `lang` (default `language.output`), `font` (CSS font-family list; default Arial with Liberation Sans fallback),
  `body_pt` (body size at 90 cm: a number, or `{"editorial": 50, "pathway": 42, "figure-led": 34}`; default per layout, at least 18; all sizes scale with `min(width / 90, height / 120)`), `colors`
  (`accent`, `tint`, `ink` as `#rrggbb`), `layouts` (default all three).
- `title`, `sections` required. `key_message` is one sentence (see the key-message test in `poster-rules.md`).
- A section has `heading` and any of: `body` (Markdown subset: `#` headings, paragraphs, `**bold**`, `*italic*`, `-`/`1.` lists,
  pipe tables), `figure` (`"F1"` or `{id, caption, alt}`; the files come from `07_present/figures/<id>.svg|png`, so run
  `figures.py` first; `F<n>.poster.svg|png`, from `figures.py --profile poster`, is used when it exists), `lab_table`, `checklist`, `column` (1-based, to force a column when the automatic balance is off).
- `lab_table` rows: `{"test", "value", "unit", "flag": "high|low|normal"}`; a `high` row shows an up arrow, `low` a down arrow,
  both coloured. Lab values go in a table, never in a sentence.
- `checklist` items: a string (unchecked) or `{"text", "checked"}`; they print as ☐ and ☑. Criteria go in a checklist.
- Every figure needs `alt` (or a `caption`, used as the alt text).

## Layouts

- **editorial**: title band, three columns with thin rules, key message as a ruled pull-quote at the top of column 1,
  references strip at the foot. Sections flow in reading order, balanced by weight across the columns.
- **pathway**: title band, key-message band, then numbered steps in reading order (down column 1, then column 2). Use it when the
  poster tells a sequence: question, method, result, meaning.
- **figure-led**: title band, one dominant figure (the `hero`, default the first figure) in a box that it fills edge to edge, and the key
  message in a solid block. A very wide figure takes the full width with the key message above it; otherwise the figure sits beside the
  key message. The box height follows the figure's aspect ratio, so the hero is the largest element on the poster. Other sections go in
  three small text columns under it, so keep their text short. It needs a figure: without one the layout is skipped with a warning.

All three: no rounded boxes, no gradients, no shadows (a test greps `poster.css`). Body text is 38 pt (editorial), 36 pt (pathway) or 30 pt (figure-led) at 90 cm, never below 24 pt,
headings 50 pt, captions 26 pt, references 24 pt; `body_pt` overrides the body size.

## Figures at poster size

A figure scales as one piece: its type ends up at `font_size x placed width / width_cm`. `figures.py` lays rows and labels out in
cm for 9-10 pt type at 16 cm, and clips its text columns when the type is raised relative to the width, so draw poster figures
with `"style": {"width_cm": 16, "font_size": 10}` and place them wide: about 16 pt in an editorial column (26 cm), 22 pt in a
pathway step (36 cm), 35 pt in the figure-led hero (58 cm). Do not put a dense forest plot in a narrow column; prefer the pathway
or figure-led layout for it. SVG is inlined, so it stays vector in the PDF; the PNG sizes the check for effective dpi
(`data-raster`).

## IVLBCL rules (from the poster session)

- Label semantics are the same on every figure (filled marker or bar = positive or event, outlined = negative; one colour per group).
- Lab values are tables with arrows. Criteria are check lists.
- No decorative cards, gradients, shadows or rounded boxes.
- Every number comes from the results ledger by placeholder; spell-check the terminology.
- Look at the PNG of every layout before sending: nothing cut off (the build warns when a box overflows), text readable from
  1.5 m, layouts visibly different.
- Print note for the author: print at 100 %, request the bleed, make sure the printer has the font (or use the PDF, which embeds it).

## Checks the build prints

`poster_build.py` reads the DOM dump: `box(es) overflow` (text or a figure is cut off) and `col-N is only X % full` (a column below 75 %:
raise `body_pt`, add text or force a section into another column with `column`). Both are warnings; fix them before sending the PDF.
Invalid values in `poster.json` (`body_pt`, `colors`, `size_cm`, a lab `flag` other than high, low or normal) exit 2 with a message.
In Markdown, `2023. text` at the start of a line stays a paragraph; a list needs `1.` to `99.` followed by a space. A `|` inside a table cell is not supported.
