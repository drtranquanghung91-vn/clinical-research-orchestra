# Example: a fictional case report (P5)

A case report written with the `orchestra` plugin from the author's notes to an exported
`out/case-report.docx` through gate G4, in CARE order, in English, with the chat in Vietnamese (plan
decision D29).

**Everything clinical in this folder is fictional.** The patient, the hospital, the city, the dates, the
record number and every clinical value were invented for this example. The author's raw notes
(`00_inputs/case-notes.md`, labelled "Ca bệnh hư cấu") are excluded by the project `.gitignore` and are not
in the repository; they had a full fictional name, an exact age, calendar dates, a record number and a
fictional hospital (`institution.name` "Bệnh viện Đa khoa Thiên Phúc", `institution.city` "Phố Lam" in
`project.yaml`) so that de-identification was exercised. The consent line in `decisions.md` and the
patient's perspective are scripted author inputs for a patient who does not exist.

**The references are real.** The nine records in `ledgers/references.json` were found by the agent with
`search_lit.py` during the run and checked by `verify_refs.py` against PubMed and Crossref (`verified_by`
ends with `VERIFIED` for all nine); none was typed from memory. Four of them are the published cases in
`01_case/similar-cases.csv` (Table 2 of the report):

| id | PMID | DOI | Used for |
|---|---|---|---|
| kardaun2013 | 23855313 | 10.1111/bjd.12501 | RegiSCAR, DRESS features |
| goncalo2013 | 23600531 | 10.1111/bjd.12389 | HLA-B*58:01 risk |
| stamp2012 | 22488501 | 10.1002/art.34488 | allopurinol starting dose |
| bathini2022 | 35644439 | 10.1053/j.ajkd.2022.04.006 | starting dose and chronic kidney disease |
| xiao2018 | 30406757 | 10.1684/ejd.2018.3378 | HHV-6 reactivation |
| ahmed2026 | 42499701 | 10.1159/000552298 | similar case |
| aatif2018 | 30647505 | 10.4103/ijn.IJN_166_17 | similar case |
| shinde2026 | 42656939 | 10.7759/cureus.113430 | similar case |
| ferrie2026 | 41578361 | 10.1186/s13256-025-05817-8 | similar case |

## What is here

| Path | Content |
|---|---|
| `01_case/dossier.md` | de-identified dossier: relative days (day 0 = admission), "in his 50s", no names, places, record number or dates |
| `01_case/facts.csv` | 43 reportable values (`id,label,value,unit,day,source`) |
| `01_case/similar-cases.csv` | four verified published cases |
| `05_analysis/output/case-facts.json`, `case-facts-log.txt` | output of `case_facts.py` |
| `ledgers/results-ledger.json` | `R-A0-001` … `R-A0-043`, `analysis_id` A0, `status` observed |
| `06_writing/case-report/00-title.md` … `11-consent.md` | the CARE sections, values as `{{R-A0-…}}`, citations as `[@id]` |
| `06_writing/case-report/case-report.assembled.md`, `case-report.draft.docx` | the assembled draft |
| `reviews/` | the five reviewer reports, `guideline-checklist-case-report.json` (CARE), `worklog.json`, the one kept round `rounds/case-report/r1/`, `audit.md`, `audit.json` |
| `gates/state.json` | G1, G3 and G4 opened by "Example author" |
| `out/case-report.docx` | the final export (`assemble.py --final`) |
| `out/ai-use-disclosure.md` | the disclosure draft (marked draft, three kinds of `[[AUTHOR: …]]` left open) |
| `out/author-decisions.md` | `worklog.py decisions .` (no requests, assumptions or waivers) |

## How it was produced (23 November 2026)

Isolated recipe of `tests/scenarios/README.md` in a fresh folder outside the repository: Claude Code 2.1.226,
`claude -p … --model sonnet` (init event: `claude-sonnet-5`), `--plugin-dir` for `orchestra` and `phi-guard`
only, `--allowedTools "Bash,Read,Write,Edit,Glob,Grep,Skill,Agent"`, `--setting-sources ""`,
`--strict-mcp-config` with an empty MCP config, `--no-chrome`, network on for the literature lookups, one
transcript per turn outside the run folder, `--resume <session_id>` for every later turn (one conversation).
Every init event showed `mcp_servers: []` and exactly the two plugins. No phi-guard or hook denial occurred.

    python plugins/orchestra/scripts/init_project.py <scratch>/fictional-case \
      --title "Drug reaction with eosinophilia after a urate-lowering drug: a case report (fictional)" \
      --type case-report --design case-report --output-lang en --chat-lang vi

The scripts used were those of the P5 branch after review fix waves B and C (`audit.json`, the G4 opening
and both exports were made with the fix-wave-C scripts; the final export is byte-identical when rerun).

| Turn | Prompt (author's words, short form) | Skills and agents | Turns, minutes, USD | Result |
|---|---|---|---|---|
| 1 | `/orchestra:case`; notes in `00_inputs/case-notes.md`; G1 answer "Tôi là Example author. Xác nhận ca bệnh, điểm dạy học: phản ứng thuốc muộn có tăng bạch cầu ái toan; bệnh nhân đã ký giấy đồng ý bằng văn bản."; the author has opened G1 and written the consent line; dossier, facts, literature and at least 3 verified similar cases, `case_lint.py` clean; stop before G3 | case-report, literature-search | 39, 8, 1.79 | dossier, 43 facts, 9 verified references, 4 similar cases, `case_lint` 0 block |
| 2 | "Tôi là Example author. Tôi đã tự khoá G3"; draft every CARE section with the timeline and similar-cases tables, review rounds, humanize, assemble, audit to 0 block, do not open G4; the author's verbatim texts (patient perspective, consent statement, funding, competing interests, ethics, author) | prose-humanizer, the five reviewer agents (two passes, 10 agent calls) | 13, 26, 13.36 | 12 sections, worklog round 1 16/16 STOP, audit 0 block 0 warn |
| 3 | author's correction: the CRP sentence said "peaked at 64 mg/L on day +4" after 86 mg/L on day 0; reword, reassemble, reaudit, do not open G4 | — | 6, 1, 2.05 | one sentence changed, audit 0 block 5 warn (E-REV) |
| 4 | "Tôi là Example author, mở G4" (the controller had run `gate.py open`); `--final`, disclosure draft, `worklog.py decisions .`, `STATUS.md` | — | 10, 2, 1.11 | `out/case-report.docx`, disclosure, author decisions, STATUS |

Total: four turns of one conversation, 68 main-thread turns, about 36 minutes, USD 18.31. No stage stalled
and none was rerun.

### Author inputs (D30)

Every human act was performed by the controller as the scripted "Example author", outside the agent, or
given as the author's words in a prompt. The agent never opened or locked a gate and never wrote the consent
line (checked in the transcripts).

| Act | How |
|---|---|
| G1 | `gate.py open . G1 --by "Example author"` before turn 1, plus the G1 answer in the turn 1 prompt |
| Consent | the controller appended `CONSENT: obtained written consent form for publication, signed by the patient (fictional)` to `decisions.md` before turn 1 |
| G3 | after turn 1: `gate.py lock . G3 --by "Example author" --files ledgers/results-ledger.json 01_case/facts.csv 01_case/similar-cases.csv` |
| `[[AUTHOR: …]]` in the report | none left: the author supplied the patient perspective, consent statement, funding, competing interests, ethics and authorship verbatim in turn 2 |
| `[[AUTHOR: …]]` in `out/ai-use-disclosure.md` | left open on purpose (model name and version, what the author checked, where the disclosure goes); the disclosure is a draft |
| E-REF | no E-REF finding reached the author: one appeared inside turn 1 (`ferrie2026` cited before it was added to the ledger) and the agent added and verified the record before G3 |
| Draft correction | turn 3 (the CRP wording) |
| E-REV warns | accepted by the author in turn 4; the reviewers were not rerun after the one-sentence correction |
| G4 | after the turn 3 audit: `gate.py open . G4 --by "Example author"` |

### Checks (repository root)

| Command | Exit | Result |
|---|---|---|
| `python plugins/orchestra/scripts/audit.py <copy of examples/fictional-case> case-report` | 0 | `audit: case-report — 0 block, 5 warn` (the five E-REV warns; run on a copy so the committed `reviews/audit.json` stays as written in the run) |
| `python plugins/orchestra/scripts/gate.py check examples/fictional-case G3`, in a fresh clone | 0 | G3: open — results locked by Example author on 2026-11-23; 3 locked files unchanged |
| `python plugins/orchestra/scripts/gate.py check examples/fictional-case G4 --deliverable case-report`, in a fresh clone | 0 | G4: open — approved after a clean audit by Example author on 2026-11-23; 17 locked files unchanged |
| `python plugins/orchestra/scripts/case_lint.py examples/fictional-case --strict` | 0 | `case_lint: 0 block, 0 warn` |
| `assemble.py <copy> case-report --final` | 0 | `out/case-report.docx` byte-identical to the committed file |

### Edits made by hand (controller)

- `decisions.md`, `STATUS.md` and `project.yaml` came out of `init_project.py` with CRLF line endings on the
  Windows checkout used (the template files were checked out with CRLF); they were converted to LF in the run
  folder after turn 1, before G3 and the audit. Every committed text file is LF.
- `00_inputs/` and the empty `.gitkeep` placeholders were not copied back. Only round 1 exists, so
  `reviews/rounds/case-report/r1/` is both the kept and the last round.

## Known issues

- **Review loop recorded as one round.** The five reviewer agents ran twice (once on the first drafts, once
  after the fixes), but `worklog.py score` was run once, after the fixes, as round 1 (16/16, STOP). `STATUS.md`
  says "2 rounds"; `reviews/worklog.json` has one.
- **Reviewer report files.** The reviewer subagents tried to write their reports to `reviews/` and Claude Code
  refused ("Subagents should return findings as text"); the main agent wrote the reports from the agents'
  replies.
- **A wrong trend word passed the review and the audit.** "peaked at 64 mg/L" after 86 mg/L was caught only
  by the author (turn 3). No script checks words such as "peaked", "rose" or "fell" against the values.
- **Humanizer.** The prose-humanizer step found 0 pattern hits and rewrote nothing.
- **A non-author note in `decisions.md`.** In turn 2 the agent added a dated "drafting assistant" note saying
  the patient-perspective quotation was supplied verbatim by the author. It records no decision and was kept.
- **E-REV warns.** The reviewer reports describe the drafts before the turn 3 correction (five warns).
