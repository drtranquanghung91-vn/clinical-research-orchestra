# Working on clinical-research-orchestra

Read `docs/superpowers/specs/2026-11-20-clinical-research-orchestra-design.md` first.

## Conventions
- Skill folders are kebab-case; frontmatter `name` equals the folder name.
- Model-invoked skills: frontmatter `name` and `description` only. The description starts
  "Use when", lists triggers only (Vietnamese and English phrases), never the workflow.
- User-invoked skills (slash commands) add `disable-model-invocation: true` and call
  model-invoked skills, never the reverse.
- Skill bodies are English and at most 500 words; detail goes to `references/`.
- Refer to another skill as "use the Skill tool with `<name>`", never by relative path.
- Shared scripts and references live once at plugin level, reached via `${CLAUDE_PLUGIN_ROOT}`.
- Never write inside `${CLAUDE_PLUGIN_ROOT}` (or `plugins/` in this repo) at run time. Intermediate
  files go to `<project>/reviews/tmp/` or the session scratch folder; run scripts from the project folder.
- "The agent reasons; scripts measure." Anything a script can check is checked by a script.
- Privacy: nothing leaves the machine except literature-API queries; never the user's name or
  email; never patient data.
- Every change to a skill ships with a scenario in `tests/scenarios/` or a note why none applies.

## CLI conventions
- Exit codes for every script: 0 = ok / clean; 1 = findings, listed (for `gate.py check`: the gate
  is closed); 2 = usage error, missing or unreadable input, network/API error or internal error.
- Results go to stdout; errors and warnings go to stderr. Never print patient data cell values.
- A wrong path (missing project, no `ledgers/` folder, missing file) is an error (2), never an
  empty clean result. Network failures are 2, never "verified" or "not found".
- Scripts that print Vietnamese call `sys.stdout.reconfigure(encoding="utf-8")` inside `try/except`.

## Commands
- Tests: `python -m unittest discover -s tests/unit -v`
- Skill lint: `python tools/lint_skills.py`
