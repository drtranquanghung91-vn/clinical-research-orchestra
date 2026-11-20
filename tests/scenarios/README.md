# Scenario tests (RED / GREEN)

A scenario proves a skill or hook changes behaviour. Each file has:

    # <id>: <title>
    Skill/hook under test: ...
    Fixtures: tests/scenarios/fixtures/<id>/...
    Prompt (paste into `claude -p`): ...
    Expected (GREEN): observable outcomes, each checkable from the transcript or files
    Baseline (RED): what happens without the plugin; recorded in BASELINE.md

Procedure
1. RED: in a temp folder with only the fixtures, run the prompt with the plugin NOT installed:
   `claude -p "<prompt>" --output-format text > red.txt`. Record the failure in BASELINE.md.
2. GREEN: install from this checkout (`claude --plugin-dir plugins/orchestra --plugin-dir plugins/phi-guard -p "<prompt>"`)
   and confirm every Expected line. Record date, model and result in BASELINE.md.
3. A skill edit that no scenario exercises is an untested change.
