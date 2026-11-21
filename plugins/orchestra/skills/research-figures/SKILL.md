---
name: research-figures
description: 'Use when figures must be drawn from analysed results: forest plot, Kaplan-Meier curve, rates chart, or a participant flow diagram. Triggers: "vẽ biểu đồ", "biểu đồ", "forest plot", "Kaplan-Meier", "đường cong sống còn", "sơ đồ chọn mẫu", "flow diagram", "STROBE flow", "CONSORT diagram", "hình", "figure", "make figures".'
---

# Research figures

## 1. Core rule
Figures are drawn by `figures.py` from the locked results ledger or the de-identified CSV. Never use an
AI-generated image, never trace a curve from a picture, never type a number into a figure.

## 2. Precondition
`python "${CLAUDE_PLUGIN_ROOT}/scripts/gate.py" check . G3` exits 0 and `ledgers/results-ledger.json`
has results. Otherwise stop: use the Skill tool with `statistical-analysis`, write nothing. A `WAIVE G3:`
line also passes; say in the hand-off that the ledger is unlocked.

## 3. Figure plan
Read the analysis register (`03_protocol/sap.md`), propose a plan and confirm it with the author:
- primary or adjusted estimates: `forest`;
- time-to-event: `km`;
- rates or proportions by group: `rates`;
- participant selection: `flow` (STROBE/CONSORT).
A number a figure needs has no ledger id: it comes from `statistical-analysis` (re-run, re-import, G3
locked again), never typed and never added to a locked ledger by hand.

## 4. Draw
Write `07_present/figures/figures.json` (format: `${CLAUDE_PLUGIN_ROOT}/references/presenting/figures-spec.md`),
then run `python "${CLAUDE_PLUGIN_ROOT}/scripts/figures.py" . [--only F1,F2] [--dpi 300]`.
Exit 2 names the figure and the problem (unknown id; missing matplotlib: `python -m pip install matplotlib`).
Set label semantics once in `style`: one colour per group, filled = event or positive, outlined = none.
Defaults: vector plus 300 dpi PNG, 16 cm width, Arial 9 pt.

## 5. Notes
- A KM figure carries "Vẽ lại từ <file>" / "Redrawn from <file>" (fixed by the script).
- `check_numbers.py` is not run on figures: numbers come from the ledger by construction.
  `consistency_audit.py` still reads the strings in each `F<n>.data.json`; run it after drawing.

## 6. Outputs
`07_present/figures/F<n>.{svg,pdf,png,data.json}`. Word and thesis: SVG or PDF; slides: native charts
built from `data.json`; poster: SVG. Caption above (`Biểu đồ 3.n.` / `Figure n.`), source line below.
Open each PNG or SVG and check it before hand-back.

## 7. "Just do it" rule
If the user says not to ask, use the plan from section 3, open with an **Assumptions / Giả định** box and
record it in `decisions.md`. It never edits the ledger.

## 8. Workflow
`${CLAUDE_PLUGIN_ROOT}/references/workflows/research-figures.md`
