---
name: research-project-setup
description: Use when a user starts or resumes a research project, thesis, manuscript, review, case report or poster and no project folder exists yet, or asks where their project stands. Triggers: "bắt đầu nghiên cứu", "tạo dự án nghiên cứu", "làm luận văn", "đề tài cơ sở", "làm tiếp đề tài", "start a research project", "set up my thesis", "where am I in my project".
---

# Research project setup

Every orchestra skill reads and writes one project folder. Create it once, then keep `STATUS.md` true.

## Create
1. Ask in one message, in the user's language, only what is missing: working title; project type
   (thesis-ckii, thesis-masters, thesis-phd, de-tai-co-so, manuscript, review, systematic-review,
   case-report, poster-only); study design; output language (vi/en); folder location.
   If the user says "cứ làm luôn"/"just do it", choose sensible defaults and write them as an
   **Assumptions / Giả định** box, then record it in `decisions.md`.
2. Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/init_project.py" <dest> --title "<title>" --type <type> --design <design> --output-lang <vi|en> --chat-lang <vi|en>`.
   Use `python3` if `python` is not found.
3. Ask the user to copy their existing files into `00_inputs/` (protocol, data, outputs, PDFs,
   institution template, journal or conference rules). Do not read patient data files; route them to
   the `phi-guard:deidentify-data` skill.

## Resume
1. Read `project.yaml`, `STATUS.md`, `decisions.md` and run
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/gate.py" check <project> G<n>` for G1–G4.
2. Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/crolib/ledgers.py" check <project>`.
3. Report in the user's language: current stage, open gates, ledger problems, the next action.
   If a script exits 2 or prints an error, report it as blocked; never guess the state.

## Entry points
Map the user's goal to the first stage still `todo`, unless they enter mid-way (for example a poster
from a finished thesis): then record `WAIVE G<n>: <reason>` lines in `decisions.md` for the gates that
no longer apply, and continue.

## Keep STATUS.md true
After every stage change update the row: state, last action, next action. Never mark a stage done
when a check it depends on was not run; write `blocked` with the reason instead.
