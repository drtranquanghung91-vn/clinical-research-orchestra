# Workflow: ethics dossier, CRF and consent form

Detail for the `ethics-and-crf` skill. Run every command from the project folder; scripts are in
`${CLAUDE_PLUGIN_ROOT}/scripts/`. Inputs: G2 open; `03_protocol/protocol.md`, `03_protocol/variables.md`,
`03_protocol/sap.md`. Outputs in `03_protocol/ethics/`; Word copies in `out/ethics/`.

## 1. The variables table crf.py reads
Every Markdown table in `variables.md` with a variable (or code) column and a type column, Vietnamese or English
headers: Biến / Variable, Mã biến / Code, Loại / Type, Giá trị / đơn vị / Values / unit, Khoảng / Range,
Nguồn / Source, Vai trò / Role, Mục tiêu / Objective, Biểu mẫu / Form / Visit, Bắt buộc / Required,
Lý do thu thập / Need. Types are read from the type cell (liên tục, nhị giá, thứ tự, phân loại, thời gian đến sự
kiện, ngày tháng, văn bản, or their English names). A Code column gives stable short names; without it the code is
a slug of the label. A Form column gives one CRF section per visit or form; without it there is one form, `main`.
Any identifier (name, address, phone, national ID, date of birth, record number) needs a Need cell.

## 2. Build and check
1. `crf.py . build` → `crf.md`, `data-dictionary.csv` (`variable,label,type,unit,values,range,source_form,required`).
2. `crf.py . check` → E-CRF. Blocks: not built; a row without a type; a coded variable without values; CRF and
   dictionary differing; a term of the SAP register (Outcome, Covariates, Exposure, Factor; A0 skipped) matching
   no variable. Warns: a field no objective or analysis uses; an identifier without a need; the dossier missing or
   incomplete.
3. A missing variable is the author's: ask for its definition, type, unit and values. The author changes
   `variables.md` (a protocol change: amend, then re-lock G2), and you rebuild. A term that names an existing
   variable in other words goes in `crf-map.csv` (`term,variable`); `check` blocks a map line that names no
   dictionary variable.

## 3. Consent form
From `references/ethics/consent-elements.md`, in the output language. Order and headings follow the committee's
template when the author gives one. Plain words; one idea per sentence; every technical term explained in
brackets the first time; active voice ("you sign", "the study team keeps"). Every institution-specific item is
`[[AUTHOR: …]]`. `lint_prose.py --profile consent consent-form.md`: CF01 long sentence, CF02 unexplained jargon,
CF03 passive obligation; all warns. Record-only studies: ask whether the committee waives consent; the author
records the decision in `decisions.md`.

## 4. Dossier and Word files
`dossier.md` from `references/ethics/dossier-template.md`; statuses drafted / author to supply / author reviewed /
approved (approved only by the author). `build_docx.py 03_protocol/ethics/<doc>.md out/ethics/<doc>.docx --project .`
for `crf`, `consent-form`, `dossier`. These are not final exports: no gate beyond G2.

## Common failures
| Failure | Fix |
|---|---|
| A covariate in the SAP has no CRF field | ask the author; never add a field with an invented definition |
| Consent form fills the committee's name or a phone number | `[[AUTHOR: …]]`; only the author fills it |
| A regulation quoted from memory | remove it; cite only what a tool lookup or the author gave |
| Identifier collected "just in case" | ask for the need or drop it (data minimisation) |
