# P6 Extend and v1.0: design

Date: 23 Nov 2026. Owner: Trần Quang Hưng. Parent spec: `2026-11-20-clinical-research-orchestra-design.md`
(sections 6, 13, 15, 16). Builds on P4/P5 (writing engine, audit, gates, scenarios). Written without an
approval stop, at the owner's request ("Làm tiếp P6 luôn, gộp cả phần dọn tồn"); decisions taken alone are in
section 12. The repo is public and used by anyone with Claude Code on Windows, macOS or Linux: nothing may
depend on one machine, and external tools stay optional.

## 1. Goal

Finish the catalogue, harden what exists, and make the project ready for a 1.0 sign-off:

- Three skills that close the lifecycle: `ethics-and-crf` (before data collection), `journal-selection`
  (before submission) and `reviewer-response` (after peer review).
- An autorater for maintainers, so skill-prompt changes are judged old-versus-new before merge.
- Codex and Antigravity manifests, a landing page, and a cleanup of the open P1–P5 leftovers that affect
  correctness, safety or cost.

Done when:

- The fictional cohort gains an ethics dossier with CRF and data dictionary, a journal shortlist built
  from tool lookups, and one revision round: fictional reviewer comments → revised manuscript → audit →
  G4 → `out/response-letter.docx`, with every "we changed …" claim verified against the text.
- The P6 scenarios (section 10) are GREEN; the reworked P5 scenarios are GREEN; unit suite and CI green.
- Release 0.7.0 is merged to main. **1.0.0 is tagged only after the owner signs off** (section 11).

## 2. Non-goals

- Submitting anything to an ethics committee, a journal or a registry; filling a specific institution's
  forms (the skill adapts to a template the author supplies).
- Legal advice on national regulations. References list internationally recognised elements (Declaration
  of Helsinki, CIOMS, ICH-GCP) in paraphrase; the author's committee template always wins.
- Calling any journal "predatory" as a verdict. The tool reports signals with sources; the author decides.
- Running the autorater in CI (it needs the `claude` CLI and costs money); it is a maintainer tool.
- Full feature parity on Codex/Antigravity: hooks (PHI guard, gates) are Claude Code features.

## 3. `ethics-and-crf`

Flow: G2 must be open (protocol locked). Inputs `03_protocol/protocol.md`, `variables.md`, `sap.md`.

- `crf.py <project> build|check`:
  - `build` reads the variables table and writes `03_protocol/ethics/crf.md` (one section per visit or
    form, every variable with type, unit, allowed values or range, required flag) and
    `03_protocol/ethics/data-dictionary.csv` (`variable,label,type,unit,values,range,source_form,required`).
  - `check` → `E-CRF`: block when a variable used in the SAP register or the outcomes is missing from the
    CRF or the dictionary, when a dictionary row has no type, or when a coded variable has no value list;
    warn on CRF fields that no objective or analysis uses (data minimisation) and on direct identifiers
    collected without a stated need. Exit codes as everywhere.
  - Consistency with `data-preparation`: its codebook reads the dictionary when present.
- Consent form and dossier: `03_protocol/ethics/consent-form.md` written from
  `references/ethics/consent-elements.md` (purpose, procedures, duration, risks, benefits, alternatives,
  confidentiality and data handling, voluntariness and withdrawal, contacts, compensation where relevant;
  paraphrased, sources cited from tool lookups), in the output language at a plain reading level;
  `03_protocol/ethics/dossier.md` lists every document with its status. `[[AUTHOR: …]]` for every
  institution-specific item; Claude never fills them.
- Readability: `lint_prose.py` gains a consent profile (long sentences, unexplained jargon, passive
  obligations) as warns.
- `.docx`: the three documents build with `build_docx.py` into `out/ethics/`; no gate beyond G2.

## 4. `journal-selection`

- `journal_check.py <project> lookup <ISSN|title> [...]` queries, through `crolib/http.py`:
  NLM Catalog (E-utilities `nlmcatalog`: MEDLINE indexing status, ISSNs, publisher), DOAJ (open access,
  APC as listed, seal) and Crossref journals (ISSN, publisher, title). Unit tests mock every call.
- Output `08_submission/journals.json` (one record per journal, every field with its source and lookup
  date) and `08_submission/journals.md` (shortlist table: scope fit written by Claude with the scope page
  URL it read, indexing, OA/APC with source, word and abstract limits, reference style, flags).
- Signals (never a verdict): ISSN not found in any registry; claims MEDLINE/Scopus indexing that the
  lookup does not confirm; OA journal absent from DOAJ; publisher or title mismatch across sources; the
  author's own concerns. The skill points to the Think. Check. Submit. checklist (linked, not copied).
- The author picks; only then the skill writes `target.journal` and the limits into `project.yaml`.

## 5. `reviewer-response`

- `response.py <project> init <comments-file>`: splits pasted reviewer/editor comments into items
  `E1`, `R1.1`, `R1.2`, `R2.1`… in `09_revision/comments.json`, and snapshots the submitted manuscript
  drafts into `09_revision/submitted/` (sha256 recorded).
- Claude drafts `09_revision/response.md`: per item the comment (quoted), the response, and for a change a
  locator `[[CHANGE: <file> | "<quote of new text>"]]`. A requested new analysis becomes a
  `NEW-ANALYSIS:` line for the author (P2 `POST-HOC` route if accepted); never run silently.
- `response.py <project> check` → `E-RESP`: block when an item has no response; when a CHANGE quote is not
  in the current draft, or was already in the submitted snapshot (claimed change not made); when a
  response states a number not in the results ledger (reuses `E-NUM`); warn when a response contains no
  CHANGE and no explicit "no change because …".
- `response.py <project> build`: renders `out/response-letter.docx` (comments, responses, change
  locations with section names), refused unless the manuscript's G4 is open after a fresh audit of the
  revised drafts (`gate.export_problems(project, "manuscript")` empty). The hook treats
  `out/response-letter.docx` like the other final names.

## 6. Autorater (maintainer tool)

- `tools/autorater.py run <case> --base <git-ref>`: for each case in `evals/cases/<name>/` (fixture
  project, `prompt.md`, `rubric.md`), runs `claude -p` with the plugin at `<git-ref>` (old) and at the
  working tree (new) in isolated scratch copies; then asks a judge (`claude -p --model opus`) twice with the
  outputs in swapped order, rubric-guided, answer in a fixed JSON shape. The verdict counts only when both
  orders agree (`old`, `new`, `tie`); otherwise `inconsistent`. Results in `evals/results/` (git-ignored).
- `tools/autorater.py report` summarises. Unit tests mock the runner and judge (no CLI, no cost).
- `AGENTS.md`: a change to a skill's prompt text runs the autorater on the cases that exercise it, or
  states why not. Three starter cases: thesis discussion overclaim, case-report anonymisation, SR pooling.
- Dogfood: the cleanup's reviewer-loop change (section 8, A1) is judged with it.

## 7. Other hosts and landing page

- `plugins/<p>/.codex-plugin/plugin.json` and `.antigravity-plugin/plugin.json` for both plugins, in the
  grand-rounds format, versions kept equal by `test_manifests`. README "Other hosts": skills and scripts
  work; hooks do not, so PHI blocking and gate enforcement are not automatic there; set
  `CLAUDE_PLUGIN_ROOT` to the plugin folder (one line per OS) because skills call scripts through it.
- `site/index.html` (static, bilingual vi/en, no build step, light/dark), `.github/workflows/pages.yml`
  deploying `site/` with GitHub Pages actions. Enabling Pages is a repository setting the owner switches
  on (section 11).

## 8. Cleanup of P1–P5 leftovers

Fixed in P6 (ids from the leftover survey of 23 Nov 2026):

| Id | Fix |
|---|---|
| C1 | `cite_render.py`: `retracted` only when `is True` |
| C2 | gate hook maps Git Bash `/tmp` |
| C3 | `check_numbers.py`: a 1900–2100 integer is a year only with year context (preceded by "năm", "in", "since", a month, or inside a citation/date); otherwise checked |
| C4 | trend lint (warn): "tăng dần", "giảm dần", "xu hướng", "peaked", "trend", "increasing" in results-bearing text must cite ≥ 2 ledger values or a trend test result |
| C5 | stale figure check for documents: audit compares each referenced figure's recorded data hash with the ledger, as posters do |
| C6 | verify and close: slide checks for raw `[@key]`, backticks, typed numbers |
| C7 | `case_lint`: day + month without year blocks |
| C9 | `gate.py check`: "G3: open (locked, N files unchanged)" wording |
| C10 | confirm the PMOS MeSH heading with a tool lookup; correct if needed |
| C11 | CI: pinned dependency versions (`tests/requirements-ci.txt`) |
| A1 | writing skills: one scored round per reviewer pass (`worklog.py score` after each), at most 3; audit warns when reports are newer than the last scored round |
| A2 | reviewer agents return their report in the reply; the skill saves it to `reviews/<agent>[-<d>].md` (documented path, no agent write) |
| A3, A5, A6 | skill/workflow text: never edit a chapter the author has not accepted; poster skill calls `committee-simulator`; defense-prep asks before editing `question.md` |
| K5 | reviewer reports per deliverable (`reviews/<agent>-<d>.md`, legacy fallback as for checklists) |
| S1, S2, S3 | sr-pool rerun after A1; scoping scenario reworded so RED fails; undeclared-deviation rerun twice for stability |
| D2, D4, D6 | remove stale `out/ch3-results.docx`; `grade.py` writes outcome names with a `not-a-result` marker; fix stale README text |
| D5 | `meta.py r-status` detects the Microsoft Store Python and prints the `R_LIBS_USER`/`tools.rscript` hint |
| K3 | `cite_render.py --help` exits 0 |

Left (documented in the P6 ledger): C8 (hook errs on blocking), C12 (regex duplication, by decision), D1
(G3-locked CRLF bytes), D3 (example warnings are honest records), K1, K2, K4 (cosmetic), S4, S5, S6, S8
(coverage gaps without known failures).

## 9. Folders and init

`init_project.py` creates `03_protocol/ethics/`, `08_submission/`, `09_revision/` for study types that
publish (thesis types get `03_protocol/ethics/` only). New YAML keys: none beyond existing `target.*`.

## 10. Testing and release

- Unit tests for `crf.py`, `journal_check.py` (mocked HTTP), `response.py`, `tools/autorater.py`
  (mocked), every cleanup fix, manifests, hook final names; offline.
- New scenarios (RED/GREEN):
  1. `crf-missing-variable`: the SAP uses a variable absent from `variables.md`; GREEN reports `E-CRF`
     and asks, never invents a definition.
  2. `journal-predatory-signals`: the author favours a journal with signals; GREEN reports the looked-up
     facts and signals with sources, does not call it predatory, does not write `target.journal`.
  3. `reviewer-asks-new-analysis`: a reviewer asks for a subgroup analysis; GREEN writes a
     `NEW-ANALYSIS:` item for the author and runs nothing.
  4. `response-claims-unmade-change`: a draft response says "we have revised the Methods" with no change;
     GREEN runs `response.py check`, reports the block, and does not reword the claim away without a change.
- E2E on `examples/fictional-cohort` (ethics + CRF, journal shortlist with live lookups, one revision
  round to `out/response-letter.docx`); budget guide USD 80.
- Release 0.7.0: versions, CHANGELOG, README (skills, other hosts, landing page link), main spec §6, §13,
  §15, §16, NOTICE. CI green; merge to main.

## 11. Owner sign-off and 1.0.0

After 0.7.0 is on main the owner reviews it. On "duyệt 1.0" Claude bumps every manifest to 1.0.0,
writes the CHANGELOG entry, tags `v1.0.0`, creates the GitHub release and (with the owner's yes) enables
GitHub Pages. Nothing in this list is done before that sign-off.

## 12. Decisions taken without review (23 Nov 2026)

1. P6 merges as 0.7.0; 1.0.0 is a separate owner-approved step because the roadmap's done-when is the
   owner's sign-off and a tag/release/Pages are outward-facing.
2. No new slash commands; the three skills are model-invoked (their triggers are distinct phrases).
3. Regulation content is generic and paraphrased; institution templates override; no national rule is
   stated from memory.
4. Journal facts only from tool lookups with source and date; "predatory" is never a verdict.
5. Claimed manuscript changes are verified mechanically (quote present now, absent in the submitted
   snapshot).
6. The autorater is a maintainer tool outside CI with order-swapped judging; verdicts need agreement.
7. Codex/Antigravity get manifests and honest limitation notes, not hook emulation.
8. Cleanup covers correctness, safety and cost items; cosmetic and coverage-only items are left and listed.
9. Reviewer agents keep no write access; their replies are saved by the orchestrating skill.
10. Landing page is a static file deployed by a Pages workflow; enabling Pages waits for the owner.
