# Research poster: workflow

Scripts are in `${CLAUDE_PLUGIN_ROOT}/scripts/`; run them from the project folder. Spec:
`${CLAUDE_PLUGIN_ROOT}/references/presenting/poster-spec.md`; rules:
`${CLAUDE_PLUGIN_ROOT}/references/presenting/poster-rules.md`.

## 1. Preconditions
`gate.py check . G3` exits 0 or a `WAIVE G3:` line exists. Ledger has results.

Source mode (poster from a published paper, thesis or case): the source sits in `00_inputs/`; numbers go
into `05_analysis/output/results.json` by hand with `raw` and `locator`, then
`results_ledger.py import --verify-raw`; `WAIVE G1:` / `WAIVE G2:` lines and the author's G3 lock follow.
The poster text then uses placeholders as usual.

## 2. Content plan
One key message (the test is in poster-rules.md). Then sections: question, methods, results, meaning. Pick
the layout by story: editorial (text and figures balanced), pathway (a sequence), figure-led (one
dominant figure; needs a figure). Lab values in `lab_table`, criteria in `checklist`.

## 3. Figures
`figures.json` entries for the figures, then `figures.py . --profile poster` (writes `F<n>.poster.*`).
Place each at its own width. Re-run after every change to the figure spec.

## 4. Build and check, in order
1. `consistency_audit.py .`; fix blocks.
2. `poster_build.py .` (or `--layout L`). Exit 2: bad spec, placeholder problem, or no browser. Without a
   browser there is no PDF: say preflight did not run and the poster is not print-ready.
3. `poster_preflight.py . --layout L` for every layout (E-PRINT; exit 1 = block). Low dpi: ask the author for
   an image of 150 dpi or more, or shrink the image; never upscale.
4. `check_pptx.py 07_present/poster/L.pptx --poster`; without python-pptx, report "not run".
5. `lint_prose.py --slides 07_present/poster/L.html`.
6. Look at each `L.png`.

## 5. Rehearsal and send-off
Required: agent `committee-simulator`, deliverable `poster` (8-12 questions, weak points); save its reply to `reviews/committee-poster.md`; the hand-off says whether it ran. Give the print note. Say a PNG was checked only after opening it with the Read tool.
Print-ready is said only when steps 1-5 all ran for the chosen layout and no block remains.
