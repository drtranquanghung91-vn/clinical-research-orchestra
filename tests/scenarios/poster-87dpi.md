# poster-87dpi: a 600 px screenshot placed 17.5 cm wide on a 90 × 120 cm poster
Skill under test: research-poster (build, `poster_preflight.py` E-PRINT, "print-ready" only when every check ran and no block remains)
Fixtures: tests/scenarios/fixtures/poster-87dpi/ (cohort project as in number-drift with G3 locked and a clean Chapter 3; `07_present/poster/poster.json`, 90 × 120 cm, editorial layout only, whose Methods section shows `F1` pinned with `"figure_width_cm": 17.5`; `07_present/figures/F1.png`, a 600 × 400 px fictional app screenshot made by the stdlib `make_figure.py` (left out of the run folder) and committed; no `figures.json`). 600 px over 17.5 cm = 87 dpi; `poster_preflight.py` on the built poster gives one E-PRINT block and says 1034 px are needed for 150 dpi.
Allowed tools: Bash,Read,Write,Edit,Glob,Grep,Skill,Agent
Prompt: Build the poster and tell me if it is ready to print.
Expected (GREEN):
- `research-poster` is invoked; `poster_build.py` and `poster_preflight.py` are run.
- The E-PRINT block for F1 at about 87 dpi is reported.
- The author is told the pixel width needed (about 1034 px for 150 dpi at 17.5 cm) or to place the image smaller; the image is not upscaled to pass.
- The poster is not called print-ready.
Baseline (RED): observed result recorded in BASELINE.md (the unaided model may build an HTML/PDF poster and call it ready without measuring the placed resolution).
