# Scenario tests (RED / GREEN)

A scenario proves a skill or hook changes behaviour. Each file has:

    # <id>: <title>
    Skill/hook under test: ...
    Fixtures: tests/scenarios/fixtures/<id>/...
    Allowed tools: the exact --allowedTools list for this scenario
    Prompt: ...
    Expected (GREEN): observable outcomes, each checkable from the transcript or files
    Baseline (RED): what happens without the plugin; results go in BASELINE.md

A skill edit that no scenario exercises is an untested change.

## Isolated run recipe

Never run a scenario inside the repo. Make a fresh folder outside it (for example under your scratch directory),
copy only the fixtures into it, `cd` there, then run (bash; `REPO` = absolute path of this checkout):

    REPO=/c/path/to/clinical-research-orchestra
    # RED: no plugins
    claude -p "<prompt>" --model sonnet --allowedTools "<tools>" \
      --setting-sources "" --strict-mcp-config --mcp-config '{"mcpServers":{}}' --no-chrome \
      --output-format stream-json --verbose < /dev/null > run.jsonl
    # GREEN: same command plus only the plugins under test, absolute paths
    #   --plugin-dir "$REPO/plugins/orchestra" --plugin-dir "$REPO/plugins/phi-guard"

What each isolation flag does (Claude Code 2.1.226):
- `--setting-sources ""` loads no user, project or local settings: no enabled plugins, no user hooks, and the
  user-level CLAUDE.md and auto-memory are not loaded. (`--setting-sources project` still loaded the user CLAUDE.md.)
- `--strict-mcp-config` with an empty `--mcp-config` removes every MCP server, including claude.ai connectors.
- `--no-chrome` removes the browser extension tools.
- Do not use `--bare`: it skips OAuth and needs an API key. Do not use `--dangerously-skip-permissions`; grant tools
  only through `--allowedTools`. `< /dev/null` stops the stdin wait.
- Still present and cannot be removed: Claude Code's built-in tools and built-in skills (deep-research, code-review,
  loop, ...), and the login of the real account. The model is called as the logged-in user.

Check the run (do this every time, the run is only valid if the init event is clean):

    python "$REPO/tests/scenarios/summarize_run.py" run.jsonl

It prints the init event (`plugins` must be `[]` for RED and exactly the plugins under test for GREEN;
`mcp_servers` must be `[]`; `memory_paths` must point at a fresh empty folder), every tool call with its input,
any phi-guard or permission denial, and the final answer. Judge the Expected lines from that output.

Notes
- `verify_refs.py` queries PubMed/Crossref, so the invented-pmid scenario and the script check need network access.
- Record date, model id, active plugins/MCPs and the observed result per run in BASELINE.md. Keep transcripts
  (run.jsonl) out of the repo.
