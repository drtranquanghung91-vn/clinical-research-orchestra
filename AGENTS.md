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
- "The agent reasons; scripts measure." Anything a script can check is checked by a script.
- Privacy: nothing leaves the machine except literature-API queries; never the user's name or
  email; never patient data.
- Every change to a skill ships with a scenario in `tests/scenarios/` or a note why none applies.

## Commands
- Tests: `python -m unittest discover -s tests/unit -v`
- Skill lint: `python tools/lint_skills.py`
