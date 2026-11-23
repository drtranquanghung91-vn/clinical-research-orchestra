---
name: research-poster
description: 'Use when a scientific poster must be made: content, figures, print layouts, preflight. Triggers: "poster", "áp phích", "làm poster", "poster khoa học", "poster hội nghị", "in poster", "research poster", "e-poster"; or after results-writing or conference-abstract when the author will present a poster.'
---

# Research poster

## 1. Core rule
Every number is a `{{R-…}}` placeholder from the ledger. A poster is never called print-ready when a
check did not run or a block remains; a missing browser, python-pptx or preflight is reported as
"not run", never as passed. Rules and print note: `${CLAUDE_PLUGIN_ROOT}/references/presenting/poster-rules.md`.

## 2. Precondition
`python "${CLAUDE_PLUGIN_ROOT}/scripts/gate.py" check . G3` exits 0 (a `WAIVE G3:` line also passes; say the
ledger is unlocked). Otherwise stop and use the Skill tool with `statistical-analysis`. Poster from a
published paper, thesis or case: source mode in `${CLAUDE_PLUGIN_ROOT}/references/workflows/research-poster.md`.

## 3. Plan
Ask once: poster size, orientation, language, logo and colours, conference rules. Write one key message:
the one sentence a passer-by remembers (test in poster-rules.md). Then `07_present/poster/poster.json` in
the format of `${CLAUDE_PLUGIN_ROOT}/references/presenting/poster-spec.md`.

Poster text: print a citation as short text resolved from the project's reference library ("Hu và cs.,
2026" / "Hu et al., 2026"), never `[@key]`. Never print file paths, backticks, ledger ids (`R-…`) or
thesis table numbers ("Bảng 3.2") that are not on the poster. Describe an ordered trend ("tăng dần
theo", "increases with", "dose-response") only when the results ledger holds a trend test supporting
it; otherwise give the group values and say the CIs include 1.

## 4. Figures
Use the Skill tool with `research-figures`, then run
`python "${CLAUDE_PLUGIN_ROOT}/scripts/figures.py" . --profile poster` before every build.

## 5. Audit and build
Scripts in `${CLAUDE_PLUGIN_ROOT}/scripts/`, from the project folder:
1. `consistency_audit.py .`; fix every block before building.
2. `poster_build.py .` (exit 2: read why; no browser means no PDF, so no preflight).
3. For every layout built: `poster_preflight.py . --layout <L>`. Fix each block: an 87 dpi image means ask
   the author for a 150 dpi or better image, or shrink it; never upscale an image to pass.
4. `check_pptx.py 07_present/poster/<L>.pptx --poster` on each PPTX.
5. `lint_prose.py --slides 07_present/poster/<L>.html`.

## 6. Rehearsal and print note
Required: call the agent `committee-simulator` with the Agent tool, deliverable `poster`; save its reply to
`reviews/committee-poster.md` and show the weak points to the author. Give the print note (100 %, bleed, fonts,
paper). Ask the author to look at every layout PNG.

## 7. Hand-off
List the files, each check's last line, which checks did not run, and whether `committee-simulator` ran. Say you
looked at a PNG only if you opened it with the Read tool. Say "print-ready" only when every check ran and no block
remains.

## 8. Workflow
`${CLAUDE_PLUGIN_ROOT}/references/workflows/research-poster.md`
