# P4 Write: design

Date: 22 Nov 2026. Owner: Trần Quang Hưng. Parent spec: `2026-11-20-clinical-research-orchestra-design.md`
(sections 6.3, 7, 9, 10.1, 10.2, 12, 16). Written without an approval stop, at the owner's request
("tự làm spec, plan, code"); the decisions taken alone are listed in section 12.

## 1. Goal

Turn a project whose results are locked (G3) into a complete thesis and a journal manuscript, reviewed
by independent read-only agents, checked by one audit command, and exported only when the audit is clean
(G4).

Done when:

- The fictional cohort yields `out/thesis.docx` (Đặt vấn đề, Chương 1–4, Kết luận, Kiến nghị, Tài liệu tham
  khảo, Phụ lục) and `out/manuscript.docx`, both exported through gate G4 after `/orchestra:audit` reports
  0 blocking findings.
- Both come with `out/ai-use-disclosure.md` and `out/author-decisions.md`.
- The four P4 scenarios (section 10) are GREEN; unit suite and CI green on ubuntu/windows × Python
  3.10/3.12.

## 2. Non-goals (moved to later phases)

- `case-report`, `systematic-review` (`/orchestra:sr`) and `literature-review` mode (c) move to a new
  **P5 Reviews and case reports**. The old P5 Extend becomes **P6 Extend**. Reason: each is a pipeline of
  its own (CARE template, PRISMA screening and meta-analysis) with no part needed for the P4 done-when.
- Institution-specific reference ordering (for example Vietnamese authors first, alphabetical). P4 renders
  `vn-thesis` as numbered by first citation (current `cite_render.py`), Vietnamese author names written in
  full; an institution that sorts differently is a known limitation.
- APA rendering.
- Item checklists for guidelines other than STROBE (the format takes any guideline; only STROBE ships).
- Journal-specific formatting beyond word limit, abstract structure and reference style.

## 3. Users and flow

The user is the student or doctor who owns the project; Claude orchestrates in the main thread (subagents
cannot spawn subagents). Both pipelines share one engine:

1. **Check**: `gate.py check . G3` must be open. If not, stop and say why (no drafting of results-based
   text).
2. **Outline**: `ledgers/outline.json` `section_plan` lists each section, its source files and the
   results ids it may use. The author confirms the outline before drafting (one question, not a form).
3. **Draft** each missing section with its role brief (section 5). Existing accepted chapters (for example
   Chapter 1 and Chapter 3 from P1/P2) are reused, not rewritten.
4. **Review in parallel**: `citation-verifier`, `statistical-reviewer`, `reporting-guideline-checker`,
   `scientific-editor`, `consistency-auditor`.
5. **Revise loop**, at most 3 rounds, scored with `worklog.py` (section 7): higher keeps, lower reverts and
   stops, equal with a sub-score loss reverts and stops. Requests for new analyses go to
   `out/author-decisions.md`, never into the text.
6. **Humanize** with `prose-humanizer` (invariants per paragraph), after the last content round.
7. **Assemble** with `assemble.py` (section 6): render placeholders, number citations once across the
   whole document, check caption numbering, build the .docx draft.
8. **Audit** with `/orchestra:audit` → `reviews/audit.md` + `reviews/audit.json`.
9. **G4**: the author opens G4 (`gate.py open . G4 --by NAME`), which succeeds only on a fresh clean audit;
   then `assemble.py --final` writes `out/<deliverable>.docx`. The hook denies `--final` while G4 is
   closed.
10. Draft `out/ai-use-disclosure.md` and `out/author-decisions.md`; update `STATUS.md` row 6.

## 4. Skills, commands, agents

| Item | Kind | Purpose |
|---|---|---|
| `thesis` | skill (model) | Vietnamese thesis by default; section list from `references/writing/vn-thesis.md` |
| `manuscript` | skill (model) | IMRaD article; journal rules from `project.yaml` `target` and the author |
| `/orchestra:thesis` | command skill | gate check G3, then the Skill tool with `thesis` |
| `/orchestra:manuscript` | command skill | gate check G3, then the Skill tool with `manuscript` |
| `/orchestra:audit` | command skill | runs `audit.py`, explains blocks in the user's language, never fixes silently |
| `citation-verifier` | agent | each citation exists in `references.json` (VERIFIED) and the claim fits the stored abstract |
| `statistical-reviewer` | agent | methods vs SAP and `analysis_plan.py`, effect sizes with CIs, multiplicity, p-value and trend overclaiming |
| `reporting-guideline-checker` | agent | writes `reviews/guideline-checklist-<deliverable>.json` item by item with locations; never a summed score (one file per deliverable since the Task 11 fix wave; the single `reviews/guideline-checklist.json` is still read when it is for that deliverable) |
| `scientific-editor` | agent | structure, argument, claim scope vs design and population, limitations present |

Agents: frontmatter `tools: Read, Grep, Glob, Bash, Write`, `disallowedTools: Edit, NotebookEdit`,
`model: sonnet`; Write only into `reviews/`; report shape `STATUS / FINDINGS (code | file:line | fix) /
GAPS / CONFLICTS`, at most ~200 words plus the findings file `reviews/<agent>.md`. The two P3 agents
(`consistency-auditor`, `committee-simulator`) gain `disallowedTools` too.

Each reviewer also gives sub-scores 0–2 on its rubric criteria (section 7) in a fenced `scores` JSON block
at the end of its findings file, so `worklog.py` can read them.

Model skills stay under 500 words; detail goes to `references/workflows/{thesis,manuscript}.md` and
`references/writing/`.

## 5. Sections and role briefs (`references/writing/roles/`)

Worker roles are files the orchestrator reads before drafting a section or briefing a general-purpose
subagent. Every role brief starts with the marker line `orchestra-role: <name>` (the hook keys on it,
section 8).

| Role | Thesis section | Manuscript section | Source of truth |
|---|---|---|---|
| `introduction` | Đặt vấn đề | Introduction | `01_question/question.md` (objectives verbatim), Chapter 1 gap, `references.json` |
| `methods` | Chương 2 | Methods | `03_protocol/protocol.md` (Part B only), `sap.md`, `sample-size.md`, `analysis_plan.py` deviations |
| `results` | Chương 3 | Results | existing `results-writing` skill (ledger placeholders only) |
| `discussion` | Chương 4 | Discussion | results ledger placeholders, `references.json`, evidence table |
| `conclusion` | Kết luận, Kiến nghị | Conclusion | one conclusion per objective, from ledger values only |
| `abstract` | Tóm tắt (optional) | Abstract | the finished sections; structured; word limit from `target.word_limit` |

Rules carried by the briefs:

- **Methods** turns the protocol into past tense and states every deviation and post-hoc analysis that
  `analysis_plan.py register` lists; Part A ("quick summary") and Part C (handoff) of the protocol are not
  copied.
- **Discussion** order: principal finding (placeholders), comparison with studies in `references.json`
  (agreement and disagreement explained by design, population, bias), possible mechanisms (hedged, cited),
  strengths, limitations (mandatory), implications. No causal verbs for observational designs, no ordered
  trend unless a ledger row reports a trend test, no generalisation beyond the studied population, no
  claim stronger than the evidence table's certainty.
- **Conclusion** maps one-to-one onto the objectives in `01_question/question.md`; each conclusion cites
  the ledger ids it rests on in an HTML comment `<!-- results: R-A1-004 -->`.
- Every number from results is a `{{R-…}}` placeholder or carries `<!-- derived: … -->`; every citation is
  `[@id]` from `references.json`; nothing is typed from memory.
- Drafts live in `06_writing/thesis/` (`00-dat-van-de.md`, `ch1-…`, `ch2-methods.md`, `ch3-results.md`,
  `ch4-discussion.md`, `05-ket-luan.md`, `06-kien-nghi.md`, `90-phu-luc.md`) and `06_writing/manuscript/`
  (`00-title.md`, `01-abstract.md`, `02-introduction.md`, `03-methods.md`, `04-results.md`,
  `05-discussion.md`, `06-conclusion.md`).

## 6. Assembly and .docx (`assemble.py`, `build_docx.py`)

### 6.1 `assemble.py <project> thesis|manuscript [--final] [--lang vi|en]`

1. Reads the section order: `06_writing/<deliverable>/order.txt` if present, else the default order of
   section 5 (files that do not exist are skipped with a warning; a missing required section — Chương 2/3/4,
   Kết luận for a thesis; Introduction/Methods/Results/Discussion for a manuscript — is a block).
2. Renders each file's `{{R-…}}` placeholders (`render_results.py` logic, imported, not shelled).
3. Concatenates into `06_writing/<deliverable>/<deliverable>.assembled.md` with `\newpage` between
   chapters, then runs `cite_render` once over the whole text (one numbering across all chapters) and
   appends the reference list under "Tài liệu tham khảo" / "References".
4. Checks captions (`E-FMT`): tables "Bảng c.n" / "Table n", figures "Hình c.n" / "Biểu đồ c.n" /
   "Figure n". Per chapter the numbers start at 1 and have no gaps or duplicates; every "Bảng 3.2"-style
   mention in the text points to an existing caption; manuscripts number across the paper. Findings use
   the shared format `E-FMT <block|warn> <file>:<line>: <msg>`.
5. Builds `06_writing/<deliverable>/<deliverable>.draft.docx` with `build_docx.py` (draft watermark
   paragraph on the first page). With `--final`, requires `gate.py check . G4` open and the audit digest
   to match (section 8) and writes `out/<deliverable>.docx` without the watermark.

Exit codes: 0 written; 1 blocking findings (nothing written); 2 usage, I/O or missing dependency.

### 6.2 `build_docx.py` additions (stdlib only, as now)

- Several inputs: `build_docx.py a.md [b.md …] out.docx`.
- Headings down to `####`; real list numbering for `- ` and `1. ` lines.
- Images: a line `![Hình 3.1. Caption](path.png)` inserts the PNG (width fitted to the text block,
  aspect kept, read from the PNG header) with the caption below; captions of tables stay above.
- Caption styles for Bảng/Table and Hình/Biểu đồ/Figure.
- A table of contents field (`{TOC}` line; Word fills it on open, "Update field") and a page-number footer.
- `institution.template`: a .docx whose `styles.xml` and page setup (`sectPr`) replace the defaults;
  content still comes from the markdown. Without it, the defaults and `templates/thesis/README.md`
  explain how to add one.

## 7. Revise loop (`worklog.py`, `references/writing/rubric.md`)

Rubric criteria, each scored 0–2 by the named source:

| Criterion | Scored by |
|---|---|
| citations supported | citation-verifier |
| statistics reported and interpreted correctly | statistical-reviewer |
| guideline items present | reporting-guideline-checker (from the checklist: 2 = no absent item, 1 = ≤ 3 absent, 0 = more) |
| structure and argument | scientific-editor |
| claim scope (design, population, certainty) | scientific-editor |
| limitations | scientific-editor |
| consistency | consistency-auditor (2 = no E-CONS block, 1 = warns only, 0 = any block) |
| prose | `lint_prose.py` (2 = no P00 block and ≤ 1 hit per 200 words, 1 = no P00 block, 0 = P00 block) |

`worklog.py score <project> <deliverable> --round N` reads the reviewers' `scores` blocks and the lint
results, sums them, compares with the previous kept round and prints `KEEP`, `REVERT` or `STOP` (STOP after
round 3 or when nothing is left to fix). It snapshots the drafts to `reviews/rounds/<deliverable>/r<N>/`
before each round so a revert restores files exactly (`worklog.py revert`). Every round appends to
`reviews/worklog.json`: round, scores, total, decision, files changed, reviewer requests for new analyses.
`worklog.py decisions <project>` writes `out/author-decisions.md` from those requests, the `Giả định /
Assumptions` entries and any `WAIVE` lines in `decisions.md`.

## 8. Audit, G4 and the gate hook

### 8.1 `audit.py <project> [thesis|manuscript] [--online] [--json]`

Runs, over the deliverable's drafts (or every deliverable when none is named):

| Check | Code | Block when |
|---|---|---|
| ledgers valid (`crolib/ledgers.py`) | E-REF | schema errors |
| citations: every `[@id]` in `references.json`, status VERIFIED (or MANUAL with `seen_in`), not retracted; `--online` reruns `verify_refs.py` | E-REF | missing, retracted, unverified |
| results numbers (`check_numbers.py` on rendered text) | E-NUM | any finding |
| analysis declarations (`analysis_plan.py check --text`) | E-STAT | any block |
| literature synthesis (`review_lint.py` on Chương 1 / Introduction) | E-LIT | any block |
| cross-document consistency (`consistency_audit.py`) | E-CONS | any block |
| prose density (`lint_prose.py`) | P00 | P00 block (single-pattern hits are warns) |
| guideline checklist (`guideline_checklist.py`) | E-RG | absent item without NA reason; a "present" item whose quoted text is not at its location |
| caption numbering (`assemble.py` checks) | E-FMT | any block |
| identifiers (phi-guard `phi_scan.py --file`) | E-PHI | strong finding; not run → warn |
| reviewer reports present (`reviews/<agent>.md` with a `scores` block and a `drafts-digest:` line from `worklog.py digest`) | E-REV | report missing; a digest that differs from the current drafts is a warn (humanizing changes drafts after review) |

phi-guard is found at `../phi-guard/scripts/` (repo layout) or `../../phi-guard/*/scripts/` (plugin cache);
absent → one warn, the rest of the audit still runs. Output: `reviews/audit.md` (summary table, then
every finding in the shared format) and `reviews/audit.json` (`{"deliverable", "at", "blocks", "warns",
"files": {relpath: sha256}}` over the drafts and ledgers it read). Exit 0 no block, 1 blocks, 2 error.

### 8.2 `guideline_checklist.py <project> [--guideline STROBE]`

Item lists ship as `references/reporting-guidelines/items/<code>.json` (`{"code", "version", "items":
[{"id": "1a", "section", "text"}]}`; item text paraphrased in a few words, never copied). The checker reads
`reviews/guideline-checklist-<deliverable>.json` (changed in the Task 11 fix wave from one shared
`reviews/guideline-checklist.json`, which the thesis and manuscript reviews overwrote; that file is still read
when its `deliverable` matches or is missing) (`{"guideline", "items": {"1a": {"status": "present|partial|absent|na",
"file", "line", "quote", "reason"}}}`), and reports `E-RG`: an item of the guideline missing from the file
(block), `absent` (block), `na` without reason (block), `partial` (warn), `present` whose quote is not
found within ±3 lines of `file:line` (block). `--table` prints the checklist as a markdown table for the
appendix. The guideline comes from `project.yaml` `reporting_guideline`.

### 8.3 G4 in `gate.py`

- `gate.py open <project> G4 --by NAME` refuses (exit 1, reason printed) unless `reviews/audit.json`
  exists, has 0 blocks, and every file hash in it still matches. On success it stores those hashes as G4's
  locked files.
- `gate.py check <project> G4`: open and unchanged → exit 0; a locked file changed → "G4: closed — <file>
  changed since the audit" (exit 1). A `WAIVE G4:` line in `decisions.md` still counts as open (existing
  rule); `worklog.py decisions` copies the waiver text into `out/author-decisions.md`.

### 8.4 Hook (`plugins/orchestra/hooks/hooks.json`, `scripts/gate_hook.py`)

A `PreToolUse` hook on `Bash|PowerShell|Agent|Task`:

- A command running `assemble.py … --final` or `build_docx.py` with an output under `out/` named
  `thesis.docx` or `manuscript.docx` → deny unless `gate.py check <project> G4` passes. The project is the
  `<project>` argument, else the working directory.
- An `Agent`/`Task` prompt containing `orchestra-role:` → deny unless G3 is open for the project in the
  working directory.
- Anything else, or no `project.yaml` found → allow silently. Python missing → `ask` with a reason (same
  pattern as phi-guard). The hook never blocks on its own errors: exit 0 with `ask` and the error text.

The hook is a safety net; the skills check gates themselves first.

## 9. Disclosure (`references/writing/ai-disclosure.md`)

`out/ai-use-disclosure.md` is drafted from `STATUS.md`, `decisions.md` and the ledgers: which tool did
which step (search, screening, appraisal, analysis code, drafting, humanizing, checking), what the author
checked, and that the author takes responsibility and AI is not an author. It follows the ICMJE
recommendation on AI-assisted technology in substance (paraphrased, no quotation, no citation typed from
memory) and has a Vietnamese and an English version according to the output language. The author edits
it; the skills never mark it final.

## 10. Testing and release

- Unit tests per new script: `assemble.py`, `audit.py`, `guideline_checklist.py`, `worklog.py`,
  `gate_hook.py`; extended tests for `build_docx.py` (multi-input, image, TOC, footer, template styles) and
  `gate.py` G4. Hooks tested by feeding stdin JSON, like phi-guard.
- Scenarios (`tests/scenarios/`, same format, RED baseline then GREEN):
  - `thesis-g3-closed`: G3 not locked; asked to write the thesis → refuses to draft results-based
    sections, explains, offers the lock step; the hook denies a writer-role dispatch.
  - `discussion-overclaim`: CIs include 1, no trend test; asked for Chương 4 that "shows HbA1c increases
    readmission" → no causal or trend claim; limitations present; statistical-reviewer flags the request.
  - `g4-export-blocked`: an unverified citation in Chương 4 → audit blocks, `--final` denied; the skill
    explains the fix and does not edit `references.json` to fake a status.
  - `revise-revert`: round 2 scores lower → `REVERT` applied, loop stops; a reviewer's request for a new
    subgroup analysis lands in `out/author-decisions.md`, no new number appears in the text.
- End to end: the fictional cohort runs `/orchestra:thesis` then `/orchestra:manuscript` with `claude -p`
  stages (author answers scripted in the prompts); outputs copied back; `audit.py` 0 blocks for both;
  `gate.py check G4` passes in a fresh clone.
- Release 0.5.0: versions, CHANGELOG, README (skills table, commands, agents, roadmap), main spec §6, §9,
  §10, §12, §16 (P4 done; new P5 Reviews and case reports; P6 Extend), example README "P4: write".

## 11. Error codes added

`E-FMT` (caption numbering and required sections), `E-REV` (reviewer report missing or stale). `E-RG` and
`E-PHI` get their first scripts. All use `<CODE> <block|warn> <file>:<line>: <msg>`.

## 12. Decisions taken without review (22 Nov 2026)

1. Case report, systematic review and literature-review mode (c) moved out of P4 into a new P5; old P5
   becomes P6.
2. Roles are shared reference files, not per-skill folders, because thesis and manuscript use the same
   roles (plugin-level shared files rule).
3. Caption numbers are typed by the writer and checked (`E-FMT`), not generated: drafts stay readable and
   the P2 chapter needs no change.
4. `vn-thesis` = numbered by first citation; institution sort orders are a documented limitation.
5. Only STROBE item lists ship in P4; the checker is generic.
6. The checklist is written by an agent and verified by a script (quote at location), so a hallucinated
   "present" is caught.
7. The audit is offline by default (ledger statuses); `--online` reruns identifier checks.
8. G4 binds to the audit's file hashes, so editing a draft after the audit closes G4 again.
9. The hook keys on `orchestra-role:` markers and `--final`/`out/*.docx` exports; it cannot see text the
   main thread writes directly, which is why the skills check gates first.
10. The fictional-cohort manuscript is in Vietnamese (the project's output language) for a domestic
    journal; English manuscripts use the same engine with `--lang en`.
