---
name: sr
description: 'Run the systematic review of the current project: protocol, screening, extraction, meta-analysis, GRADE and write-up (tổng quan hệ thống).'
disable-model-invocation: true
---

From the project folder run `python "${CLAUDE_PLUGIN_ROOT}/scripts/gate.py" check . G2`. If the protocol is not
locked, say that screening waits for the author's locked protocol and continue only with protocol work. Use the
Skill tool with `systematic-review`. Finish in the user's language with the stage reached and the paths.
