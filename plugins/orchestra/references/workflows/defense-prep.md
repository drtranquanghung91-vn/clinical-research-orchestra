# Defence preparation: full workflow

For a thesis or dissertation defence. Slide rules: `${CLAUDE_PLUGIN_ROOT}/references/presenting/defense-rules.md`;
spec format: `${CLAUDE_PLUGIN_ROOT}/references/presenting/pptx-spec.md`; figures:
`${CLAUDE_PLUGIN_ROOT}/references/presenting/figures-spec.md`; question bank:
`${CLAUDE_PLUGIN_ROOT}/references/presenting/committee-questions.md`. Scripts are in
`${CLAUDE_PLUGIN_ROOT}/scripts/`; run them from the project folder.

## 1. Preconditions

1. `python "${CLAUDE_PLUGIN_ROOT}/scripts/gate.py" check . G3` exits 0. Exit 1: stop and send the author to
   `statistical-analysis`. A `WAIVE G3:` line also exits 0; say so in the hand-off.
2. `ledgers/results-ledger.json` has results; thesis chapters exist in `06_writing/thesis/`.
3. Read `project.yaml` (language, type), the objectives in `01_question/`, `decisions.md`. Never edit `01_question/` or the protocol without the author's yes to that exact change.

## 2. Consistency audit (always first)

1. `python "${CLAUDE_PLUGIN_ROOT}/scripts/consistency_audit.py" . 06_writing/thesis/*.md 07_present/abstract.md`
   (drop the abstract if it does not exist). Exit 0: no block. Exit 1: findings. Exit 2: usage error, stop.
2. Agent `consistency-auditor` (Agent tool, by name). It returns its report; save it to `reviews/consistency.md`. It covers what the
   script cannot compare: renamed quantities, other roundings, objectives worded differently.
3. Fix each block in the thesis text itself, with the author, then re-run until exit 0. A slide that repeats
   a wrong thesis number only moves the problem to the committee. Warnings: decide one by one, note the
   decision in `decisions.md`.
4. Typical blocks (see the rules file): `≈26` where the formula gave 26.65 (write 27); a study end date
   that differs between abstract and methods; 85% in one place and 86,3% in another.

## 3. Plan the deck

1. Count the minutes: ask for the committee's limit (default 18-20). Plan about one slide per minute; the
   backup slides sit after the closing slide and do not count.
2. Outline: title, outline, problem and objectives, methods (design, sample size, outcomes), flow, Table 1,
   one slide per objective result, discussion, limitations, conclusion tied to the objectives, thanks,
   backup (sensitivity analyses, definitions, references).
3. Write `07_present/defense/deck.json`. Every title is a sentence that states the finding. Every slide has
   `notes` (what to say, the number to read, the transition). Numbers are placeholders. Figures:
   `chart` slides with `"data": "../figures/F<n>.data.json"`; a missing figure goes through `research-figures`.
4. If the author gave the faculty's template file, set `"template"` and `"layouts"`; copy the template
   under `07_present/theme/` first.

## 4. Build and check

1. If the Skill tool lists `grand-rounds:medical-deck`, hand the plan (deck.json, time budget, template) to it.
2. Else: `pptx_from_spec.py 07_present/defense/deck.json 07_present/defense/deck.pptx --project .`
   (exit 2: read stderr; an unknown placeholder lists the known ids).
3. `check_pptx.py 07_present/defense/deck.pptx`: exit 1 means off-slide, may-overflow or tiny-text; fix the
   spec and rebuild.
4. `lint_prose.py --slides 07_present/defense/deck.pptx`: S17 topic title, S20 explaining the obvious, S21
   hype without hedge. Fix by rewriting the title or sentence.
5. Run `consistency_audit.py .` once more; it reads the strings in `deck.json`.

## 5. Rehearsal

Agent `committee-simulator` (Agent tool, by name), deliverable `defense`. Save its reply to
`reviews/committee-defense.md`. Go through the weak points with the author: post-hoc results, deviations,
wide intervals, claims stronger than the design.

## 6. Hand-off

List: `07_present/defense/deck.json`, `07_present/defense/deck.pptx`, `reviews/consistency.md`,
`reviews/committee-defense.md`. Set `STATUS.md` row `7 Present` to `doing` if it exists. Never lock a gate.
