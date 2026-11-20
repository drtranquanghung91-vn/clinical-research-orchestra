---
name: status
description: 'Show where the current research project stands: stages, gates, ledger problems and the next action (xem tiến độ dự án).'
disable-model-invocation: true
---

Use the Skill tool with `orchestra:research-project-setup` in Resume mode for the project in the current folder
(or the one the user names). Do not change any file. Reply with a short table of stages and gates,
then one line: the next action.
If no `project.yaml` is found, say so and suggest /orchestra:start.
