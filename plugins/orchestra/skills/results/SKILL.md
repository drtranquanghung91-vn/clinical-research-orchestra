---
name: results
description: 'Write the Results for the current project from the locked results ledger and export .docx (viết chương kết quả).'
disable-model-invocation: true
---

For the project in the current folder: run `python "${CLAUDE_PLUGIN_ROOT}/scripts/gate.py" check . G3`; if it is not locked, say so and stop. A `WAIVE G3:` line in `decisions.md` also exits 0: then say in the hand-off that the text comes from an unlocked ledger.
Then use the Skill tool with `results-writing`. Finish with the render_results, check_numbers and
analysis_plan results and the path of the .docx, in the user's language.
