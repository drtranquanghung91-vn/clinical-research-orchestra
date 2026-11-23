# Fictional systematic review: drug X and 30-day mortality (P5)

**Everything in this folder is fictional and was made to demonstrate the software.** Drug X, the five
randomised trials, their authors, journal and numbers, the two reviewers ("Reviewer A", "Reviewer B"), the
author ("Example author"), the "Bệnh viện Mô phỏng" affiliation and the database export do not exist. No patient
data was entered or used at any point. The fictional trials are never attributed to a real paper.
The background and methods references (PRISMA 2020, RoB 2, GRADE, I², prediction intervals, between-study
variance estimators) are real records that the agent found with `search_lit.py` during the run and that
`verify_refs.py` marked VERIFIED.

The project is a Vietnamese systematic review with meta-analysis: *Thuốc X và tử vong 30 ngày ở người lớn nhập
viện: tổng quan hệ thống và phân tích gộp (hư cấu)* (drug X versus placebo and all-cause mortality at 30 days in
adults admitted to hospital with an acute medical illness). Type and design `systematic-review`, output and chat
language `vi`, reporting guideline PRISMA 2020, reviewers in `project.yaml → review.reviewers`.

## The fictional design

- **Simulated export.** `02_evidence/sr/exports/simulated-export.ris` holds 24 records, every title starting
  "Fictional", 4 of them duplicates (same title, year and first author). It stands in for the database exports a
  real author would run; the author's log line is `Simulated database,fictional,2026-11-23,S1,24,exports/simulated-export.ris`
  in `02_evidence/sr/search-log.csv`. No real database was searched for studies.
- **Flow.** 20 records screened, 13 excluded at title and abstract, 7 full texts assessed, 2 excluded with
  reasons from the protocol list, 5 trials included. One deliberate disagreement at title/abstract (rec-0011,
  outpatients: A include, B exclude) and one at full text (rec-0007, 90-day outcomes: A include, B exclude with
  a reason), each settled by a `consensus` row recorded only after both reviewers had decided.
- **Included trials.** `varrow2017`, `quellin2019`, `tamsett2020`, `orbeck2021`, `lindqvar2022`: manual records
  in `ledgers/references.json` (`source: manual`, `seen_in` = the simulated export, titles starting
  "Fictional trial").
- **Extraction.** Two extraction files with one deliberate differing cell (placebo deaths in `tamsett2020`,
  A 26, B 25), settled in `04_data/sr/extraction.csv` with a `consensus_note`. `extract_check.py` lists the
  difference as a warning, which is expected.
- **Risk of bias.** RoB 2 per trial, judged by both reviewers (`reviewer` = "Reviewer A; Reviewer B"); three trials
  low, two "some concerns"; the overall row is the worst domain (the tool's algorithm).
- **Counts chosen** so that the registered A1 pool (RR, random effects, REML, no HKSJ) has k = 5: a prediction
  interval is reported, Egger's test is not (k < 10), and heterogeneity is moderate. A2 is a subgroup analysis by
  `rob_overall`, A3 leave-one-out.

## How it was produced (23 November 2026)

The project was created outside the repository with `init_project.py` (the command in the P5 plan, Task 14) and
driven with non-interactive Claude Code runs, then copied here without the transcripts:

```bash
claude -p "<author's turn>" [--resume <session_id>] --model sonnet \
  --plugin-dir "$REPO/plugins/orchestra" --plugin-dir "$REPO/plugins/phi-guard" \
  --allowedTools "Bash,Read,Write,Edit,Glob,Grep,Skill,Agent" --setting-sources "" --strict-mcp-config \
  --mcp-config '{"mcpServers":{}}' --no-chrome --output-format stream-json --verbose < /dev/null > ../stage-N.jsonl
```

Claude Code 2.1.226, model `sonnet` (init event: `claude-sonnet-5`), network on. Every init event was clean
(`plugins: orchestra, phi-guard`; `mcp_servers: []`; a fresh memory folder), checked with
`tests/scenarios/summarize_run.py`; no phi-guard or permission denials. Two conversations: stages 1–5 in one,
stages 6–8 in another, every author answer sent with `--resume`.

| Stage | Author's turn (short form) | Skill or agent used | Turns, minutes, USD | Files written |
|---|---|---|---|---|
| 1 | `/orchestra:sr` with the PICO, the two reviewers, the analysis register (A0–A3, values given verbatim), the three full-text exclusion reasons, "the only study source is a simulated export"; stop for approval | sr, systematic-review | 15, 3.2, 0.62 | `03_protocol/sr-protocol.md`, `prospero.md` ("not registered"), `02_evidence/sr/strings.md` |
| 2 | "Tôi là Example author, đồng ý đề cương" and the answers to the ten `[[AUTHOR: …]]` items (dates, contact, run date, hits, export file) | systematic-review | 5, 0.6, 0.17 | same three files, placeholders filled |
| 3 | G1 and G2 opened; export placed; import, dedupe, optional labelled AI suggestions, reviewer sheets | systematic-review (brief `screen-suggest`) | 11, 2.0, 0.47 | `records.csv`, `ai-suggestions.csv` (20 suggestions), `reviews/tmp/` sheets |
| 4 | reviewers have decided; conflicts, kappa, counts, `extract_check.py`, `meta.py run`, `forest-spec`, `r-status`, GRADE draft | systematic-review | 14, 4.0, 0.75 | PRISMA counts and meta results in the ledger, `05_analysis/output/*`, draft `grade.json` |
| 5 | the author's GRADE decisions (risk of bias −1, imprecision −1, others 0; comparator risk 0.18, the median placebo risk of the five trials); `grade.py run`, figures, checks | systematic-review (`grade.py`, `figures.py`) | 18, 2.9, 0.93 | `grade.json`, `06_writing/review/sof.md`, `07_present/figures/` (F-PRISMA, F-A1, F-ROB) |
| 6 | `/orchestra:sr` after G3: draft with `review-systematic` and the P4 roles (outline pre-approved), real background references, review rounds, assemble, audit; list author items | systematic-review, the five reviewers | 132 main turns, 77.9, 44.37 | `06_writing/review/00-…07-*.md`, `review.assembled.md`, `review.draft.docx`, `reviews/*`, 6 real references; audit 7 blocks left for the author |
| 7 | the author's text for the four `[[TÁC GIẢ: …]]`, "no new analysis" for the subgroup prediction interval, keep PRISMA items 3 and 7, a `not-a-result` note in `sof.md`, update checklist item 26 | systematic-review, reporting-guideline-checker | 8, 8.0, 5.98 | audit 0 block, 15 warn; `decisions.md` entry; `out/author-decisions.md` |
| 8 | "Tôi là Example author, mở G4"; `assemble.py . review --final`, disclosure, `worklog.py decisions .`, `STATUS.md` | systematic-review | 16, 6.0, 2.57 | `out/review.docx`, `out/ai-use-disclosure.md`, `STATUS.md` |

Total: about 1 hour 45 minutes and USD 55.85.

### Human acts (scripted inputs, never the agent)

Every human act was performed by the controller from the command line, as the fictional person concerned:

- **Example author:** the answers in the table; `gate.py open . G1 --by "Example author"`;
  `gate.py open . G2 --by "Example author" --files 03_protocol/sr-protocol.md 03_protocol/prospero.md 02_evidence/sr/strings.md`
  before any screening step; the export and the search-log line; the five `search_lit.py add-manual` records
  (the author holds the fictional full texts); `gate.py lock . G3 --by "Example author" --files ledgers/results-ledger.json 02_evidence/sr/screening.csv 04_data/sr/extraction.csv 04_data/sr/rob.csv 05_analysis/meta/grade.json`;
  `gate.py open . G4 --by "Example author"` after the clean audit; `project.yaml → review.reviewers`.
- **Reviewer A and Reviewer B:** the sheets written by `screening.py sheet` were filled with prepared decisions
  and recorded with `screening.py decide --stage ta|ft --reviewer "Reviewer A|Reviewer B" --file <sheet>`; the two
  consensus rows with `--reviewer consensus`, after both reviewers had decided. The two extraction files,
  `extraction.csv` and `rob.csv` were prepared by the controller and placed before stage 4.

The agent made 20 title/abstract suggestions through `screening.py suggest` (`02_evidence/sr/ai-suggestions.csv`);
they are labelled AI suggestions, never decisions, and the disclosure counts them. Agreement (κ, printed by
`screening.py kappa`, not a ledger record): 0.89 at title/abstract (20 records), 0.59 at full text (7 reports).

### R cross-check

`meta.py . r-status` found R 4.6.1 but reported metafor not installed (exit 2), so `r-check` was not run (it is
optional; every ledger value comes from the Python engine). `05_analysis/meta/metafor.R` was written afterwards by
the controller with `meta.py . r-script`, so a reader with R and metafor can run the cross-check. No E-META result
is recorded.

## Checks (run from the repository root)

| Command | Exit | Result |
|---|---|---|
| `python plugins/orchestra/scripts/gate.py check examples/fictional-sr G2`, in a fresh clone | 0 | G2: open (locked, 3 files unchanged) — approved by Example author on 2026-11-23 |
| `python plugins/orchestra/scripts/gate.py check examples/fictional-sr G3`, in a fresh clone | 0 | G3: open (locked, 5 files unchanged) — results locked by Example author on 2026-11-23 |
| `python plugins/orchestra/scripts/gate.py check examples/fictional-sr G4 --deliverable review`, in a fresh clone | 0 | G4: open — approved after a clean audit by Example author on 2026-11-23; 20 locked files unchanged |
| `python plugins/orchestra/scripts/screening.py examples/fictional-sr check` | 0 | `screening: 0 block, 0 warn` |
| `python plugins/orchestra/scripts/extract_check.py examples/fictional-sr` | 0 | 0 block, 1 warn (the deliberate differing cell) |
| `python plugins/orchestra/scripts/audit.py <copy of examples/fictional-sr> review` | 0 | `audit: review — 0 block, 15 warn` (on a copy, so the committed `reviews/audit.json` stays as G4 locked it) |
| `python plugins/orchestra/scripts/meta.py <copy> run` | 0 | 22 results; `ledgers/results-ledger.json` byte-identical, G3 still open |
| `python plugins/orchestra/scripts/assemble.py <copy> review --final` | 0 | `out/review.docx` byte-identical to the committed one |

The 15 audit warnings: the extraction difference (E-SCR); four E-GRADE notes on paragraphs that report the
low-certainty pooled result (the conclusion itself says "có thể" and "mức chắc chắn thấp"); PRISMA items 2, 3 and
7 partly reported (E-RG; items 3 and 7 kept by the author's decision); E-PHI "full date" on the search date (not a
patient date); five E-REV notes (see Known issues).

## Edits made by the controller after the run

- `decisions.md`, `STATUS.md` and the project's ignore file came out with CRLF line endings and were converted to
  LF while copying (none of them is locked by a gate).
- Not copied: `reviews/tmp/` (screening sheets and the agent's suggestion file before `suggest`), and a scratch
  `out.txt` the agent left in the project root while reading abstracts.

## Known issues

- **Seven review passes, one scored round.** The agent ran the five reviewers seven times while fixing findings
  but called `worklog.py score . review --round 1` once (13/16, KEEP), so only `reviews/rounds/review/r1/` exists
  and the audit warns (E-REV) that the reviewer reports describe an earlier draft. Stage 6 alone cost USD 44.
- **A digit in the GRADE outcome name.** `grade.py` copies the outcome name from `grade.json`
  ("… (30 ngày)") into `sof.md`, where `check_numbers.py` blocks the "30" (E-NUM). `grade.json` is locked at G3
  and a label change is refused, so the author let the agent add `<!-- not-a-result: … -->` after the two "30"s
  in `sof.md`. `grade.py` could mark such words itself.
- **`worklog.py decisions .`** would not overwrite `out/author-decisions.md` once the author's answer had been
  written into it; the agent kept the edited file.
- **The disclosure is a draft.** `out/ai-use-disclosure.md` leaves `[[TÁC GIẢ: …]]` items (what the author checked,
  model name and version) for the author, as in the P4 example.
- **Plugin code changed during the run.** The P5 fix wave C (hook, `build_docx.py` self-check, audit inputs,
  review design guard) was merged into the plugin copy while stage 6 was running; the audits of stages 6–7 and
  the final export used the new code, and the final `.docx` rebuilt with it is byte-identical.
