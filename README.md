# clinical-research-orchestra

Evidence-first Claude Code plugins for clinical research, from bedside question to podium.
For medical students, residents, doctors and other healthcare professionals. Works in
Vietnamese and English.

> Status: P0 foundation (0.1.0). Not yet for general use.

## Install (Claude Code)

    /plugin marketplace add drtranquanghung91-vn/clinical-research-orchestra
    /plugin install phi-guard@clinical-research-orchestra
    /plugin install orchestra@clinical-research-orchestra

## What works in 0.1.0
- `/orchestra:start`, `/orchestra:status`: create or resume a project folder with ledgers and gates.
- `phi-guard`: blocks patient identifiers in outbound tool calls; `deidentify-data` skill.
- Scripts: `search_lit.py`, `verify_refs.py`, `init_project.py`, `gate.py`, `ledgers.py check`.

## Authors

Trần Quang Hưng, with Amelia Le (co-author of the research-methods skills). See CONTRIBUTORS.md
and NOTICE.md. Inspired by PaperOrchestra (Google Research) and built on the harness of
grand-rounds.

## License

MIT
