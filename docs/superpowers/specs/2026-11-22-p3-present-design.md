# P3 Present: design

Date: 2026-11-22. Phase P3 of `2026-11-20-clinical-research-orchestra-design.md` (§16 roadmap row "P3 Present").
Status: approved by delegation. Trần Quang Hưng asked on 22 Nov 2026 for spec, plan and code without review
stops ("tôi không cần phải vào xem approve"). Decisions he would normally have been asked about are listed in §11.

## 1. Goal

Turn locked results (G3) into the things a researcher presents. The deliverables are figures, a conference
abstract, a print poster and a thesis-defence deck. Every number on them traces to the results ledger, the
same quantity has the same value everywhere, and print problems are caught before printing.

Done when (from the roadmap):
- `examples/fictional-cohort` gets figures, a conference abstract, a poster in 3 layouts (PPTX, PDF, PNG)
  and a defence deck (PPTX with speaker notes) plus committee questions, all built from its locked P2
  results by the plugin.
- Four scenarios are GREEN: `mzl-consistency`, `poster-87dpi`, `humanizer-invariants` and `vi-dense-prose`
  (the last two are the humanizer rows of the main spec §13).

## 2. Non-goals

- Manuscript and thesis assembly (P4); P3 only reads the Chapter 3 that P2 writes.
- AI-generated images of data, ever. Illustrations (icons, schematics) are out of scope too.
- Institution templates beyond what `pptx_from_spec.py` already supports (a `.pptx` template file).
- Printing or uploading anything. The poster skill hands the author files and a print note.

## 3. Users and flow

```
G3 locked (or WAIVE G3 for a published paper)
  └─ research-figures ── 07_present/figures/F<n>.{svg,pdf,png} + F<n>.data.json
       ├─ conference-abstract ── 07_present/abstract.md (+ .rendered.md, .docx)
       ├─ research-poster ── 07_present/poster/<layout>.{html,pdf,png,pptx}  (/orchestra:poster)
       └─ defense-prep ── 07_present/defense/deck.json → deck.pptx           (/orchestra:defense)
prose-humanizer: any prose file, before the format pass; invariants.py guards each rewrite
committee-simulator (agent): questions for a poster session or a defence
consistency-auditor (agent) + consistency_audit.py: before any slide or poster is built
```

All P3 outputs live in `07_present/` (already in the project template). Results text keeps `{{R-…}}`
placeholders; every build step renders them from the ledger (`render_results.py` for Markdown; the same
code for JSON specs).

## 4. Skills, commands and agents

| Name | Kind | Does |
|---|---|---|
| `research-figures` | skill | figure plan → `07_present/figures/figures.json` → `figures.py`; forest, Kaplan–Meier with numbers at risk, rates with CI, flow diagram; native PPTX chart data for slides |
| `conference-abstract` | skill | structured abstract (Background/Objective, Methods, Results, Conclusion) within the conference word limit, placeholders, numbers checked, prose linted |
| `research-poster` | skill | content plan with one key message, 3 layouts, build, preflight, print note, poster questions |
| `defense-prep` | skill | consistency audit first, slide plan with action titles and time budget, native charts, deck build and check, committee questions |
| `prose-humanizer` | skill | rewrites AI-sounding academic prose per paragraph, keeps academic exceptions, `invariants.py` reverts any paragraph whose numbers, citations, placeholders or hedges changed |
| `/orchestra:poster` | command | `research-poster` |
| `/orchestra:defense` | command | `defense-prep` |
| `committee-simulator` | agent | read-only; likely questions with answers grounded in project files and the weak points; writes `reviews/committee-<deliverable>.md` |
| `consistency-auditor` | agent | read-only; runs `consistency_audit.py`, then judges what a script cannot (same quantity named differently); writes `reviews/consistency.md` |

Agents live in `plugins/orchestra/agents/` (new folder) with `tools: Read, Grep, Glob, Bash, Write` and the
report shape of the main spec §6.3. They write only into `reviews/`.

Preconditions shared by the four presenting skills: `gate.py check . G3` exits 0 (locked, or `WAIVE G3:`
in `decisions.md`). Otherwise stop and use the Skill tool with `statistical-analysis` (or, for a published
paper, the source mode in §6.3).

## 5. Figures (`research-figures`, `figures.py`)

### 5.1 Spec `07_present/figures/figures.json`

```json
{"figures": [
  {"id": "F1", "type": "forest", "title": "…", "rows": [{"label": "HbA1c 7–9% vs <7%", "result": "R-A1-003"}],
   "null": 1, "log_scale": true, "x_label": "OR (95% CI)", "source": "Bảng 3.3"},
  {"id": "F2", "type": "km", "data": "04_data/cohort.deid.csv", "time": "time_to_readmit_days",
   "event": "readmit_1y", "group": "hba1c_group", "order": ["<7", "7-9", ">9"], "at_risk": [0, 90, 180, 270, 365],
   "max_time": 365, "time_unit": "ngày", "source": "redrawn from 04_data (A4)"},
  {"id": "F3", "type": "rates", "rows": [{"label": "<7%", "result": "R-A0-062"}], "unit": "%"},
  {"id": "F4", "type": "flow", "boxes": [{"text": "Hồ sơ đủ tiêu chuẩn", "n": "R-A0-001.n"}], "exclusions": []}
]}
```

- Every plotted estimate comes from a ledger id (`result`, or `"R-…​.part"`); `figures.py` never takes a typed
  number for forest, rates or flow. Flow boxes may take `{"n": "<derived formula>"}` with the same formula
  rules as `<!-- derived: -->` (P2 contract), evaluated by the same code.
- Kaplan–Meier is computed from the de-identified data file (product-limit estimator, stdlib), never from a
  picture. Numbers at risk are printed under the axis at the `at_risk` times. The source note says "redrawn
  from <data file>" and the data file's SHA-256 is stored in the figure's data file.
- Label semantics are fixed per project: `07_present/figures/figures.json → "style"` (colours per group,
  filled = event/positive, outlined = no event/negative), applied to every figure.

### 5.2 Outputs

`07_present/figures/F<n>.svg`, `.pdf` (vector, for print and Word), `.png` (300 dpi, for preview and as a
fallback), and `F<n>.data.json`: every number drawn, each with its ledger id or derivation, plus the
native-chart series used by slides (§7.2). `figures.py` needs matplotlib; missing → install hint, exit 2.

## 6. Poster (`research-poster`, `poster_build.py`, `poster_preflight.py`)

### 6.1 Spec `07_present/poster/poster.json`

Size (`size_cm`, default `[90, 120]` portrait), optional `bleed_mm` (0, or 3–5), `lang`, `title`, `authors`,
`affiliations`, `key_message` (one sentence, may hold placeholders), `sections` (each `heading`, `text`
in the Markdown subset of `build_docx.py`, optional `figure` id, `table` (`T3.n` CSV with placeholders
rendered), `checklist` items, `lab_table` rows with arrows), `references` (keys from `references.json`),
`qr` (optional text). `layouts`: subset of `["editorial", "pathway", "figure-led"]`, default all three.

### 6.2 Build

`poster_build.py <project> 07_present/poster/poster.json` for each layout:
1. Renders placeholders from the ledger, then fills `templates/poster/<layout>.html` + `poster.css`
   (CSS page size = poster size + bleed; sizes in cm; system fonts, default Arial).
2. Headless Chrome or Edge (found on PATH or standard install paths, or `--browser`) prints
   `<layout>.pdf` and a preview `<layout>.png` (about 2000 px on the long side) and dumps the rendered DOM
   to `<layout>.dom.html`. The template's script writes, for every image, its natural size and placed
   size, and flags every box whose content overflows.
3. Writes `<layout>.pptx` (one slide at the poster size) through `pptx_from_spec.py` with native tables
   and the figure images. No browser found → PDF/PNG skipped with exit 2 and a message; PPTX still built.

Layouts: **editorial** (three text-led columns), **pathway** (numbered steps along the reading path, key
message band), **figure-led** (one dominant figure with the key message, text around it). No decorative
cards, gradients or rounded boxes by default (IVLBCL rules); lab values as tables with arrows; criteria as
check lists.

### 6.3 Source mode (published paper)

For a poster from a published paper, thesis or case: the author puts the source in `00_inputs/`; numbers
enter `05_analysis/output/results.json` by hand with `raw` and `locator` (import mode of P2) and
`results_ledger.py import --verify-raw`; `WAIVE G1:`/`WAIVE G2:` lines and the author's G3 lock follow.
No new script.

### 6.4 Preflight (`poster_preflight.py <project> <layout>`; `E-PRINT`)

| Check | Severity |
|---|---|
| PDF page size ≠ poster size (+ 2 × bleed when requested), tolerance 1 mm | block |
| image effective dpi at placed size < 100 | block |
| image effective dpi < 150 | warn |
| a font in the PDF not embedded | block |
| bleed requested but missing from page size | block |
| a box overflows (from the DOM dump) | block |
| an image without alt text, text below 24 pt at 90 × 120 cm (scaled by poster width) | warn |

Effective dpi = image natural pixels ÷ placed width in inches. A check that cannot run (no DOM dump, a
PDF the parser cannot read) is reported as "not checked by script", never as passed.

## 7. Defence deck (`defense-prep`)

### 7.1 Order
1. `consistency_audit.py` over Chapter 3, the abstract and any thesis files in `06_writing/thesis/`, then
   the `consistency-auditor` agent. Every block is fixed in the thesis before slides are planned.
2. Slide plan `07_present/defense/deck.json` (grand-rounds spec format, §7.2): action titles (a sentence
   that states the finding), one message per slide, a time budget (default 18–20 minutes, about one
   slide per minute) and speaker notes on every slide; numbers as placeholders.
3. Charts native: forest and Kaplan–Meier as native XY charts from `F<n>.data.json`; numbers at risk as a
   native table under the KM chart; source note "redrawn from …".
4. Build: if the `grand-rounds` plugin is installed, hand the plan to `grand-rounds:medical-deck`
   (thesis-defence recipe); otherwise `pptx_from_spec.py <project-rendered spec> 07_present/defense/deck.pptx`,
   then `check_pptx.py` and `lint_prose.py --slides`.
5. `committee-simulator`: 15–25 likely questions with answers grounded in the thesis files and the weak
   points to prepare → `reviews/committee-defense.md`.

### 7.2 `pptx_from_spec.py` and `check_pptx.py`

Copied from grand-rounds 0.2.0 (same owner, MIT; NOTICE row) and adapted:
- `--project <dir>` renders `{{R-…}}` placeholders in all spec strings from the ledger before building.
- Chart kinds `km` (XY scatter with straight lines, steps drawn by doubling points, one series per group)
  and `forest` (one XY series of point estimates plus one two-point line series per CI, log axis when
  asked), both fed from a figure's `data.json`.
- Spec `size_cm` for a single-slide poster.

## 8. Text checks

### 8.1 `consistency_audit.py <project> [files…]` (`E-CONS`)

Default files: `06_writing/**/*.md` and `07_present/**/*.md` (rendered versions preferred), plus string
values in `07_present/**/*.json`. Checks:

| Check | Rule | Severity |
|---|---|---|
| same quantity | a number keyed by the 2–4 content words before it (lower-cased, stop words and "là/=/:/was/of" dropped) has the same unit and a different value in another place (85% vs 86,3%) | block |
| sample size | `≈`, `~`, `khoảng`, `about` before a participant count, or a decimal participant count | block |
| date ranges | two ranges with the same start and different ends, or the same end and different starts | block |
| abstract vs results | a number in an abstract (`*abstract*.md`) that appears in no results file and not in the ledger | warn |
| percentages sum | a table with a `Tổng`/`Total`/`Tổng cộng` row at 100% whose percentage column does not sum to 100 within 0.5 (an overall-rate row such as `Chung` is not a total) | warn |
| terms | a variant from `project.yaml → terms` (preferred: [variants]) or the built-in list (HbA1c/HbA1C, đái tháo đường/tiểu đường) | warn |

Escape: `<!-- cons-ok: <reason> -->` on the line. Placeholders are rendered first, so ledger numbers
compare as printed.

### 8.2 `lint_prose.py <files> --lang vi|en` (`P` codes)

Prose-pattern catalog `references/writing/prose-patterns.md`: patterns from `humanizer` v4 (MIT) adapted to
academic writing, plus a Vietnamese set ("không chỉ… mà còn…", "đóng vai trò quan trọng", "trong bối
cảnh…", "ngày càng…", "góp phần…", "Tóm lại,", dash overuse, one-line closers, forced triads). Codes
`P01`–`P30`. Counts per paragraph; a paragraph whose hits per 100 words exceed the threshold
(`judgement-defaults.md`, default 3) is a `warn`; the document density above 2 per 100 words is a
`block`. Academic exceptions are never counted: passive voice, hedges ("may", "suggest", "có thể",
"gợi ý"), reporting-guideline wording, standard headings, defined abbreviations. `--slides` lints PPTX or
HTML text with the grand-rounds S-catalog rows that apply to text (S17 topic titles, S20, S21), ported
into the same script. `--count-words` prints the word count of a structured abstract (headings excluded,
a placeholder counts as one word).

### 8.3 `invariants.py before.md after.md [--merge out.md]`

Paragraphs are paired by position (blank-line separated). For each pair: the multiset of numbers, citation
keys (`[@id]`), `{{R-…}}` placeholders and `derived`/`not-a-result` comments must be equal, and the count
of hedge words must not drop. A failing paragraph is listed (`INV block after.md:<line>: …`) and, with
`--merge`, restored from `before`. Different paragraph counts → every paragraph is compared by content
hash and the whole file is reported as structure-changed (block, exit 1). Exit 1 when any paragraph failed.

## 9. Error handling and conventions

Exit codes, finding lines and UTF-8 console handling as in AGENTS.md. Optional dependencies:
`matplotlib` (`figures.py`), `python-pptx` (`pptx_from_spec.py`, `check_pptx.py`, `poster_build.py`'s
PPTX step, `lint_prose.py --slides` on PPTX), a Chrome or Edge browser (poster PDF/PNG). Missing → an
install hint and exit 2 for that step; checks that did not run are reported as not checked. CI installs
`matplotlib python-pptx`; browser-dependent tests skip when no browser is found.

## 10. Testing and release

- Unit tests for every new script and for the adapted `pptx_from_spec.py`/`check_pptx.py` (offline, small
  fixtures; the browser test builds a 20 × 30 cm poster when a browser exists).
- Scenarios (RED without the plugin, GREEN with it), fixtures under `tests/scenarios/fixtures/<id>/`:
  - `mzl-consistency`: a fictional thesis whose abstract says 85% and Chapter 3 says 86,3% for the same
    rate, methods give "≈26" patients for a formula result of 26.65, and the study end date differs
    between abstract and methods; prompt asks for a defence deck. GREEN: all three found as `E-CONS`,
    thesis fixed (with the author) before any slide is planned.
  - `poster-87dpi`: a poster spec whose figure is a 600 px image placed 17.5 cm wide (87 dpi). GREEN:
    preflight `E-PRINT` reported, author told to supply a ≥ 150 dpi image or shrink it, nothing sent to print.
  - `humanizer-invariants`: a paragraph that a rewrite would tempt to round "OR 1,42" or drop "có thể".
    GREEN: `invariants.py` run, the failing paragraph reverted and listed.
  - `vi-dense-prose`: a Vietnamese discussion paragraph dense with "không chỉ… mà còn…", "đóng vai trò
    quan trọng". GREEN: `lint_prose.py` before and after, patterns reduced, invariants clean, meaning kept.
- End to end: `examples/fictional-cohort` through figures, abstract, poster (3 layouts) and defence deck
  with `claude -p` and the plugin, from its locked G3. Outputs committed (PDF/PNG/PPTX small enough:
  PNG previews about 2000 px, figures 300 dpi).
- Release 0.4.0: versions, CHANGELOG, README (skills table, status, install of optional dependencies),
  NOTICE rows (grand-rounds scripts, humanizer v4), main spec §6.1, §9.1, §9.2, §13 and §16 updated.

## 11. Decisions taken without review (22 Nov 2026)

1. P3 scope is the roadmap row plus `consistency-auditor` (§11.2 of the main spec needs it for the defence).
2. Prose codes are `P01`–`P30`; `S01`–`S21` stay the grand-rounds slide catalog (main spec §9.2 amended).
3. 87 dpi is below 100 dpi, so `E-PRINT` blocks (the main spec §11.1 thresholds win over "warning" in §13).
4. Figures: matplotlib vector + PNG for print and documents; native PPTX charts for slides. No R.
5. Poster PDF through a headless Chrome/Edge (no playwright); overflow and placed image size come from a
   DOM dump written by the template's own script.
6. Kaplan–Meier is drawn from the de-identified data (read-only, hash recorded), the only figure not built
   from ledger values; its numbers at risk are data-derived and labelled so.
7. Same-quantity matching in `consistency_audit.py` keys on the words before a number; false positives are
   escaped with `cons-ok` and triaged by the `consistency-auditor` agent.
8. `pptx_from_spec.py` and `check_pptx.py` are copied into this repo (main spec §3 already lists them).
