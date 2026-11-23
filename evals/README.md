# Autorater cases

`tools/autorater.py` judges a change to a skill's or agent's prompt text: the same case runs with the plugins at a
base git ref (old) and with the working tree (new), then a judge model compares the two attempts against the
case's rubric twice: both orders are judged (old as A, then new as A). Only a verdict both orders agree on counts (`old`, `new`, `tie`);
anything else is `inconsistent`. It is a maintainer tool: it needs a logged-in `claude` CLI, costs money and never
runs in CI. Results go to `evals/results/` (git-ignored).
`--max-usd` (default 20) stops new runs once the reported cost reaches the cap.

    python tools/autorater.py list --skill thesis-writing
    python tools/autorater.py run thesis-discussion-overclaim --base main
    python tools/autorater.py report

A case is `evals/cases/<name>/` with `case.json` (`fixture`: a repo-relative fixture folder, usually a scenario
fixture; `allowed_tools`; `max_turns`; `skills` it exercises), `prompt.md` and `rubric.md`. Fixtures are
fictional, like every scenario fixture.

## Dogfood

Runs on this repository (one row per case and run): date, base, head, case, verdict, cost (USD), note.

| Date | Base | Head | Case | Verdict | Cost | Note |
|---|---|---|---|---|---|---|
