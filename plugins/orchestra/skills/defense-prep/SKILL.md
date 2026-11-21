---
name: defense-prep
description: 'Use when a thesis or dissertation defence must be prepared: slide deck, time budget, rehearsal questions. Triggers: "bảo vệ luận văn", "bảo vệ luận án", "slide bảo vệ", "trình chiếu bảo vệ", "chuẩn bị bảo vệ", "hội đồng", "thesis defense", "defence slides", "viva"; or after results-writing when the thesis chapters are drafted.'
---

# Defence preparation

## 1. Core rule
The audit and the thesis fixes come before any slide is planned. A slide never carries a number that
is not a `{{R-…}}` placeholder from the ledger. Rules and the real-defence lessons:
`${CLAUDE_PLUGIN_ROOT}/references/presenting/defense-rules.md`.

## 2. Precondition
`python "${CLAUDE_PLUGIN_ROOT}/scripts/gate.py" check . G3` exits 0 (a `WAIVE G3:` line also passes; say in
the hand-off that the ledger is unlocked). Otherwise stop: use the Skill tool with `statistical-analysis`,
plan nothing.

## 3. Step 1: consistency audit (before slides)
From the project folder run `python "${CLAUDE_PLUGIN_ROOT}/scripts/consistency_audit.py" .` over
`06_writing/thesis/` and the abstract. Then call the agent `consistency-auditor` with the Agent tool (not
the Skill tool). Fix every block in the thesis with the author: unrounded sample size, end date that
differs between sections, one rate printed two ways. Re-run until the exit code is 0. Do not plan slides
while a block stands.

## 4. Step 2: plan
Write `07_present/defense/deck.json` in the format of
`${CLAUDE_PLUGIN_ROOT}/references/presenting/pptx-spec.md`: action titles (a sentence that states the
finding), one message per slide, a time budget (18-20 minutes, about one slide a minute; ask the
author for the committee's limit), speaker notes on every slide. Charts come from
`07_present/figures/F<n>.data.json` (use the Skill tool with `research-figures` when one is missing). If
the author gave an institution template, set `template` in the spec.

## 5. Step 3: build and check
- If the Skill tool lists `grand-rounds:medical-deck`, hand it the plan.
- Otherwise: `pptx_from_spec.py 07_present/defense/deck.json 07_present/defense/deck.pptx --project .`,
  then `check_pptx.py 07_present/defense/deck.pptx` and `lint_prose.py --slides 07_present/defense/deck.pptx`.
Fix every serious finding; report each script's last line. Missing python-pptx: install hint, stop.

## 6. Step 4: rehearsal
Call the agent `committee-simulator` with the Agent tool: deliverable `defense`, this project. It writes
`reviews/committee-defense.md` (15-25 questions, weak points). Show the weak points to the author.

## 7. Hand-off
List `07_present/defense/deck.json`, `deck.pptx`, `reviews/consistency.md`, `reviews/committee-defense.md`.
Ask the author to read every slide aloud once against the time budget.

## 8. Workflow
`${CLAUDE_PLUGIN_ROOT}/references/workflows/defense-prep.md`
