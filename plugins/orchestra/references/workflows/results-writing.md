# Results writing: full workflow

For thesis Chapter 3 (Kết quả nghiên cứu) and manuscript Results. Wording and sentence templates:
`${CLAUDE_PLUGIN_ROOT}/references/writing/results-writing.md`; Vietnamese Chapter 3 layout:
`${CLAUDE_PLUGIN_ROOT}/references/writing/vn-chapter3.md`; reporting guidelines:
`${CLAUDE_PLUGIN_ROOT}/references/reporting-guidelines/index.md`. Scripts are in
`${CLAUDE_PLUGIN_ROOT}/scripts/`; run them from the project folder.

## Core rule

No number is typed by hand. Every result is a `{{R-…}}` placeholder from `ledgers/results-ledger.json`
(`{{R-A1-001}}`, `.ci`, `.p`, `.n`, `.count`, `.full`; `.count` is the integer count of a percent record,
0 decimals, for the n in "n (%)" cells). Use a placeholder whenever one exists; a derived comment is the
last resort. A number computed from results carries `<!-- derived: EXPR[, free note] -->` right after it:
EXPR is the text up to the first `,` or `;`, and it must name the ledger ids it uses, each with an optional
part `.value|.n|.count|.p|.lo|.hi` (no part = `.value`; `.lo`/`.hi` are the CI bounds), e.g.
`<!-- derived: R-A1-002 - R-A1-003, risk difference -->`. A pure formula (ids, numbers, `+ - * / ( )`) is
evaluated and compared with the number at its printed decimals (a mismatch blocks); other text that names
ids only warns "derived formula not evaluated"; a comment that names no id blocks. A number that is not a
result (cut-off, eligibility limit, ward code) carries `<!-- not-a-result: <reason> -->`. Both go right
after the number. The scripts measure; the agent writes.

## 1. Preconditions

1. `python "${CLAUDE_PLUGIN_ROOT}/scripts/gate.py" check . G3` exits 0. Exit 1: stop. If it lists changed
   files, tell the author which ones and that the analysis must be re-run or re-imported and G3 locked
   again (`statistical-analysis`); if G3 was never locked, ask the author to review the analysis report
   and lock it. Never lock or open a gate here. A `WAIVE G3:` line in `decisions.md` also gives exit 0: the
   text then comes from an unlocked ledger, and the hand-off (section 8) says so explicitly.
2. `ledgers/results-ledger.json` has results and `05_analysis/output/results.json` lists the tables.
3. Read `project.yaml` (`type`, `design`, `reporting_guideline`, `language.output`), the objectives in
   `01_question/`, the register in `03_protocol/sap.md`, `decisions.md` (`POST-HOC`/`DEVIATION` lines) and
   `05_analysis/analysis-report.md`.
4. Set `STATUS.md` row `6 Writing` to `doing`. If the G3 check passes because the author locked it and
   row `5 Analysis` is not `done`, set row 5 to `done` (the author locks G3 outside any skill).

## 2. Mode and file

| Project `type` | Output | .docx |
|---|---|---|
| `thesis-*`, `de-tai-co-so` | `06_writing/thesis/ch3-results.md` | `out/ch3-results.docx` |
| `manuscript` (or the author asks for a paper) | `06_writing/manuscript/results.md` | `out/results.docx` |

Write in `project.yaml → language.output`. A thesis author who also wants a manuscript gets two files from
the same ledger. An English manuscript inside a `language.output: vi` project: add `--lang en` to
`render_results.py` and `check_numbers.py` (otherwise it renders and is checked with decimal commas).

## 3. Outline

Order: the Results items of the reporting guideline the project uses (`project.yaml → reporting_guideline`;
records in `${CLAUDE_PLUGIN_ROOT}/references/reporting-guidelines/guidelines.json`, summary in `index.md`).
Take the item numbers from that guideline version: use the Skill tool with `guideline-check` for the item
list, never numbers from memory (example: STROBE (2007) items 13–17). Map them onto the register:
1. Participants and flow (screened, eligible, excluded with reasons, analysed; missing data per key
   variable). The flow figure is P3 (`research-figures`, not available yet): leave a placeholder line.
2. Table 1 (`A0`). In an RCT, no baseline p-values.
3. Primary analysis (register `primary`), crude then adjusted.
4. Secondary analyses, one subsection each, in register order.
5. Post-hoc analyses and deviations: own subsection, heading labelled ("Exploratory post-hoc analyses" /
   "Phân tích thăm dò (hậu kiểm)"), each quoting its `decisions.md` line. A failed model is reported as
   failed with its reason.

Thesis: sections by objective (`vn-chapter3.md`). Manuscript: short subsections, key estimates in the text,
details in the tables; do not repeat a table in prose.

## 4. Tables from CSV

For each table in `results.json → tables` that the outline uses:
1. Open `05_analysis/output/tables/<T…>.csv` for the layout (rows, columns, order).
2. Find the result records with `table == "<T…>"` in `results.json`; match each CSV cell to a record by
   `label` (Table 1 rows: `<variable> [<group>]`; subgroup rows start with `<subgroup label>: `, e.g.
   `sex = female: …`) and `kind`.
3. Write a pipe table with the same layout, every number replaced by its placeholder: n (%) → `.full` of
   the `percent` record, or `.count` and the value in separate cells (`.full` of a percent record that has
   a CI gives the CI form, so take the count from `.count`; `.n` is the group size), mean ± SD → `.full` of the `mean` record, estimate
   (CI) → `{{R-…}} ({{R-….ci}})`, p → `.p`. A cell with no record (reference category, "1 (reference)")
   is text; `1` passes the number check as an integer 0–10, and integers 1900–2100 are treated as years and
   not checked, so write a cohort size in that range (for example 2015 patients) as a placeholder.
4. Caption line directly above the table: `Bảng 3.n. <title>` / `Table n. <title>`. `Nguồn:`,
   `Ghi chú:`, `Note:` lines directly below, no blank line. Escape `|` in a cell as `\|`, `*` as `\*`.
5. If a cell number has no record, do not type it: ask whether the analysis must record it
   (`statistical-analysis`), or leave the cell out.

`build_docx.py` turns each Markdown line into one paragraph: write every paragraph on one line. A `>` line
becomes an indented paragraph without the marker, and backticks are removed.

## 5. Text

One paragraph per analysis: what was compared in whom; estimate and CI, then p; at most one sentence on
direction and precision. Use the templates and the CI wording table in `results-writing.md`. A
post-hoc result is labelled in every paragraph that uses it ("exploratory", "post-hoc", "thăm dò",
"hậu kiểm"); a deviation result is labelled as a deviation in prose and tables ("deviation", "protocol
change", "thay đổi so với SAP", "sai lệch đề cương"), never reported as the primary result without it. No interpretation, mechanisms or literature: that is the Discussion (thesis Chapter 4).

## 6. Claims rows

For every substantive sentence add one row to `ledgers/claims.json` (`claims` list). `text` is the sentence
with its placeholders, so the row stays true if the analysis is re-run:

```json
{"id": "ch3-3.2-R-A1-001", "file": "06_writing/thesis/ch3-results.md",
 "location": "3.2, Nhận xét Bảng 3.2, câu 2",
 "text": "Sau hiệu chỉnh theo tuổi và giới, HbA1c ≥ 8% liên quan với tỷ số chênh tái nhập viện cao hơn (OR {{R-A1-001}}; KTC 95%: {{R-A1-001.ci}}; p = {{R-A1-001.p}}).",
 "kind": "observed", "refs": [], "results": ["R-A1-001"], "status": "unverified"}
```

`status` is `unverified`: the `verified-*` values record how a literature source was read, and a results
claim is checked by the scripts against the ledger instead. Check the ledgers with
`python "${CLAUDE_PLUGIN_ROOT}/scripts/crolib/ledgers.py" check .` (expected: `ledgers: 0 problems`).

## 7. Checks before hand-back

In this order; a `block` stops hand-back until fixed (exit 1 = findings, 2 = usage or file error).

| Step | Command | Expected when clean |
|---|---|---|
| 1 | `python "${CLAUDE_PLUGIN_ROOT}/scripts/render_results.py" . 06_writing/thesis/ch3-results.md` | `render_results: wrote 06_writing/thesis/ch3-results.rendered.md`, exit 0 |
| 2 | `python "${CLAUDE_PLUGIN_ROOT}/scripts/check_numbers.py" . 06_writing/thesis/ch3-results.rendered.md` | `check_numbers: 0 findings`, exit 0 |
| 3 | `python "${CLAUDE_PLUGIN_ROOT}/scripts/analysis_plan.py" check . --text 06_writing/thesis/ch3-results.md` | `analysis_plan: 0 block, 0 warn`, exit 0 |
| 4 | `python "${CLAUDE_PLUGIN_ROOT}/scripts/build_docx.py" 06_writing/thesis/ch3-results.rendered.md out/ch3-results.docx --project .` | `build_docx: wrote out/ch3-results.docx`, exit 0 |

Manuscript: the same with `06_writing/manuscript/results.md` and `out/results.docx`. Step 3 reads the
placeholder file (it finds post-hoc ids through the placeholders); steps 2 and 4 read the rendered file.

Findings and fixes:
- `E-NUM block <file>:<line>: {{R-…}} is not in the results ledger` (step 1): wrong id or part; check
  `results.json`. Malformed placeholders are blocked the same way. Nothing is written until fixed.
- `E-NUM block <file>:<line>: 31.6% is not in the results ledger` (step 2): a typed number. Replace it with
  its placeholder; mark a computed number `derived`, a cut-off `not-a-result`.
- `E-STAT block …: post-hoc result R-A3-001 is not labelled …` (step 3): add the label to that paragraph.
- `E-STAT warn …: causal wording "leads to" with an observational design`: rewrite as association.

Example: the "before" text in `results-writing.md`, checked as English (`language.output: en` or
`--lang en`), gives two E-NUM blocks (`31.6%`, `8%`), one E-STAT block (unlabelled `R-A3-001`) and one
causal-wording warning; checked as Vietnamese it gives three E-NUM blocks (`31`, `6%`, `8%`), because the
decimal point is not a Vietnamese decimal separator. The "after" text (`--lang en`) and the
`vn-chapter3.md` example give 0 findings at every step.

## 8. Hand-off

Report to the author, in the user's language: the last line of each check, the .docx path, any assumption
made, and, if G3 was waived (`WAIVE G3:` in `decisions.md`), that the text comes from an unlocked ledger.
Ask them to read the rendered file and the .docx. Figures go to `research-figures`, the assembled
thesis to `thesis`, the full paper to `manuscript`; these P3/P4 skills are not available yet, so say so.
When the author accepts the text, set `STATUS.md` row 6 to `done` for this part.

## 9. "Just do it" rule

If the user says not to ask ("cứ làm luôn", "just do it"): write with the defaults above, open the reply
with an **Assumptions / Giả định** box (sections chosen, tables included, post-hoc placement) and record
it in `decisions.md`. It never opens or locks a gate, never edits the ledger or `results.json`, and never
skips the checks.
