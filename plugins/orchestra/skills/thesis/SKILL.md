---
name: thesis
description: 'Write, review and export the thesis of the current project from locked results (viết luận văn).'
disable-model-invocation: true
---

From the project folder run `python "${CLAUDE_PLUGIN_ROOT}/scripts/gate.py" check . G3`. If it does not print
`G3: open`, stop: show the line, explain in the user's language that the thesis is written only from results the
author has reviewed and locked, and give the lock step (the author reads
`05_analysis/analysis-report.rendered.md`, then runs `gate.py lock . G3 --by "<name>" --files …` as recorded in
`STATUS.md` row 5; see `statistical-analysis`). Otherwise use the Skill tool with `thesis-writing`. Finish in the user's language with the
paths it reports.
