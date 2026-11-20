---
name: research-project-setup
description: 'Use when a user starts or resumes a research project, thesis, manuscript, review, case report or poster or an existing project needs resuming, asks where their project stands, or asks whether the citations or references of a draft are correct. Triggers: "bắt đầu nghiên cứu", "tạo dự án nghiên cứu", "làm luận văn", "đề tài cơ sở", "làm tiếp đề tài", "kiểm tra trích dẫn", "trích dẫn có đúng không", "kiểm tra tài liệu tham khảo", "start a research project", "set up my thesis", "where am I in my project", "check my citations", "verify references".'
---

# Research project setup

Every orchestra skill reads and writes one project folder. `<project>` below means the project folder path (the one containing `project.yaml`). Create it once, then keep `STATUS.md` true.

## Create
1. Ask in one message, in the user's language, only what is missing: working title; project type
   (thesis-ckii, thesis-masters, thesis-phd, de-tai-co-so, manuscript, review, systematic-review,
   case-report, poster-only); study design; output language (vi/en); folder location.
   If the user says "cứ làm luôn"/"just do it", choose sensible defaults and write them as an
   **Assumptions / Giả định** box, then record it in `decisions.md`.
2. Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/init_project.py" <dest> --title "<title>" --type <type> --design <design> --output-lang <vi|en> --chat-lang <vi|en>`.
   Use `python3` if `python` is not found. `--chat-lang` is the language the user is writing in.
   Put the title in double quotes and escape any `\"`, `$` or backtick in it.
   If it exits 2, show its message, fix the arguments or destination, and do not say the project was created.
3. Ask the user to copy their existing files into `00_inputs/` (protocol, data, outputs, PDFs,
   institution template, journal or conference rules). Do not read patient data files; route them to
   the `phi-guard:deidentify-data` skill.
   The project's `.gitignore` already keeps `00_inputs/`, `*.key.csv` and non-de-identified `04_data/` files
   out of git. If the folder is synced (OneDrive, Google Drive...), exclude them from sync before any data is copied.

## Resume
1. Read `project.yaml`, `STATUS.md`, `decisions.md` and run
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/gate.py" check <project> G<n>` for G1–G4.
2. Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/crolib/ledgers.py" check <project>`.
3. Report in the user's language: current stage, open gates, ledger problems, the next action.
   `gate.py check`: 0 = open, 1 = closed (normal; report it), 2 = error. `ledgers.py check`: 0 = clean, 1 = problems found (list them). Only exit 2, a crash or no output means blocked; never guess the state.

## Check citations
When asked whether citations or references are correct, and before any draft leaves the project:
1. Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/verify_refs.py" <project or references.json> --cite <draft.md ...>`.
2. Report every reference that is not VERIFIED (NOT_FOUND, MISMATCH, RETRACTED, NO_IDENTIFIER) and every
   E-REF line (a cited `[@id]` missing from the ledger or retracted), with the script's notes.
3. Exit 0 = all verified; 1 = findings, report them; 2 = not checked (wrong path, unreadable file,
   network error): say so and never call the references verified.
4. Never invent, guess or substitute a PMID, DOI or reference. Replacements come only from a live
   lookup (`search_lit.py`), and the user decides.

## Entry points
Map the user's goal to the first stage still `todo`. If they enter mid-way (for example a poster
from a finished thesis), propose the waivers (which gate, why). Only after the user agrees, record
`WAIVE G<n>: <reason> (confirmed by <user>)` in `decisions.md`, then continue.

## Keep STATUS.md true
After every stage change update the row: state, last action, next action. Never mark a stage done
when a check it depends on was not run; write `blocked` with the reason instead.
