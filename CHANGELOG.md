# Changelog

## 1.0.0 (2026-11-23)
- Owner sign-off of 0.7.0 by Trần Quang Hưng; no functional change. Version bumped in the marketplace,
  all six plugin manifests and the README.
- GitHub Pages stays off: the landing page in `site/` and `.github/workflows/pages.yml` are ready, but
  the workflow does not deploy until the owner enables Pages and sets `PAGES_ENABLED`.

## 0.7.0 (2026-11-23)
- P6 Extend: model-invoked skills `ethics-and-crf` (ethics dossier, consent form, E-CRF and data
  dictionary), `journal-selection` (shortlist from checkable signals) and `reviewer-response`
  (point-by-point response letter). No new commands.
- Scripts: `crf.py` (E-CRF: every CRF variable tied to the variable register and the SAP analysis
  register), `journal_check.py` (NLM Catalog, DOAJ and Crossref lookups; signals, never verdicts; Scopus
  is not checkable and is reported so), `response.py` (E-RESP: every claimed change is verified against
  the submitted snapshot), `lint_prose.py --profile consent`. `out/response-letter.docx` is a final
  export (gate, hook and `build_docx.py`). Reference files under `references/ethics/` and
  `references/submission/`.
- `tools/autorater.py`, a maintainer tool outside CI: old and new plugin versions run on a fixed case
  and a judge compares both orders (order-swapped), with blinded scratch folders and `--max-usd`.
  Three cases.
- Codex and Antigravity manifests for both plugins (hooks do not run on those hosts; the README says
  which checks to run yourself). Landing page in `site/` and a gated Pages workflow that stays manual
  until `PAGES_ENABLED` is set at sign-off.
- Reviewer agents no longer have Write: they return the report in the reply and the skill saves it per
  deliverable (`reviews/<agent>-<d>.md`). The writing skills run one scored round per reviewer pass
  (at most 3); `audit.py` warns when reports are newer than the last scored round.
- Cleanup fixed: C1 `cite_render.py` marks `retracted` only when `is True`; C2 the gate hook maps
  Bash-on-Windows `/tmp`; C3 `check_numbers.py` treats 1900-2100 as a year only with year context; C4
  trend wording lint (warn only); C5 the audit compares each figure's data hash with the ledger; C6 slide
  checks for raw `[@key]`, backticks and typed numbers; C7 `case_lint` blocks a day and month without a
  year; C9 `gate.py check` says "G3: open (locked, N files unchanged)"; C10 the PMOS MeSH heading
  confirmed by a tool lookup; C11 CI dependencies pinned (`tests/requirements-ci.txt`); A1 scored
  rounds, see above; A2 reviewer reports saved by the skill; A3 never edit a chapter the author has not
  accepted; A5 the poster skill calls `committee-simulator`; A6 `defense-prep` asks before editing
  `question.md`; K3 `cite_render.py --help` exits 0; K5 reviewer reports per deliverable; D2 stale
  `out/ch3-results.docx` removed; D4 `grade.py` marks outcome names `not-a-result`; D5 `meta.py r-status`
  detects the Microsoft Store Python and prints the `R_LIBS_USER` hint; D6 stale README text fixed.
- Left by decision: C8, C12, D1, D3, K1, K2, K4, S4, S5, S6, S8.
- Plan decisions: D2 `crf.py check` reads the SAP analysis register (outcome, covariate, exposure
  cells) with `analysis_plan.parse_register`; D12 `E-RESP` blocks an item with no response, a CHANGE
  quote not in the current draft or already in the submitted snapshot, and a claimed change with no
  locator; D13 `gate.py` gets `FINAL_NAMES` and `final_problems`, so the response letter is gated like
  the other final exports; D16 the autorater extracts the old plugins from the old ref into scratch and
  copies the working tree for the new side; D42 a journal revision does not reopen the internal reviewer
  loop, so old `E-REV` digest warnings are expected.
- Review fixes: `response.py` accepts a CHANGE locator only in a tracked draft of the deliverable that
  has a submitted snapshot (files under `09_revision/` cannot fake a change); the autorater judge is
  blinded (neutral folder names, path parts stripped) and has `--max-usd` with an estimate printed first;
  the sample-size reference pass in `consistency_audit.py` no longer downgrades a real block; `crf.py`
  recognises Vietnamese date and identifier columns.
- Scenarios (`tests/scenarios/BASELINE.md`, observed): the four P6 scenarios. crf-missing-variable
  GREEN (no BMI row written, the author asked). journal-predatory-signals GREEN (not found in NLM
  Catalog, DOAJ or Crossref; no verdict). reviewer-asks-new-analysis GREEN on the third run, after a
  fix to the `reviewer-response` skill (the first run was void: the agent's Bash had no PATH; the
  second was GREEN in part). response-claims-unmade-change GREEN, but the scenario separates the plugin
  from no plugin only through the `response.py check` step. S2 scoping-asks-pooling now discriminates
  (RED reproduced; GREEN after a `systematic-review` skill change). S1 sr-pool-heterogeneous is still not
  fully GREEN: heterogeneity, prediction interval and the GRADE downgrade are reported but tau-squared
  (R-A1-002) is not stated (known issue). S3 undeclared-deviation GREEN on both reruns.
- End to end (`examples/fictional-cohort`, sonnet, plugins orchestra + phi-guard): ethics and CRF (`crf.py
  check` 0 blocks), a journal shortlist from live NLM Catalog, DOAJ and Crossref lookups (2026-11-23) with the
  author's pick, and one fictional revision round to `out/response-letter.docx` (`response.py check` 0 blocks;
  audit 0 blocks for thesis and manuscript). Four stages, about 45 minutes, USD 11.59 reported plus about
  0.6 for one killed turn. `out/ch3-results.docx` removed. Pipeline slips are listed in the example README.
- Autorater dogfood of the reviewer-loop change (`evals/README.md`): sr-pooling `new` (USD 1.28);
  case-anonymisation `old` (USD 2.24): the case exercises case-report steps 1-3, which P6 did not change,
  and the new side skipped `case_lint.py` in that run, so this is read as run variance; thesis case not run
  (budget: the old side looped reviewers for about an hour, the A1 problem). The run found five autorater
  bugs, fixed: `claude.cmd` on Windows, a per-call `--max-budget-usd` and `--timeout-min`, progress lines.
- Hooks: PreToolUse timeout raised from 15 s to 30 s in both plugins. On Windows the `python3` Store alias
  probe takes about 3 s, and under load the gate hook overran 15 s; a hook that times out does not enforce
  G3/G4.
- Known issues: as for 0.6.0 (R cross-check needs R 4 or later with `metafor`), plus the S1
  tau-squared omission above.
- Roadmap: P6 done; 1.0.0 follows the owner's sign-off.

## 0.6.0 (2026-11-23)
- P5 reviews and case reports: model skills `case-report` (CARE 2013, BMJ Case Reports mode through
  `target.journal_style: bmj`) and `systematic-review` (PRISMA 2020), `literature-review` mode (c)
  (narrative review with SANRA, scoping review with PRISMA-ScR; a request for pooling or risk of bias in a
  scoping review is redirected to `systematic-review`); commands `/orchestra:case` and `/orchestra:sr`;
  `/orchestra:review` also offers mode (c). Workflows
  `references/workflows/{case-report,systematic-review,scoping-review}.md` and `references/review/`
  (protocol and PROSPERO templates, search strings, GRADE wording, SWiM, role briefs).
- Scripts: `case_facts.py` (de-identified case facts into the ledger as `observed`), `case_lint.py`
  (anonymisation, consent, structure; `--strict` blocks the final export without recorded consent),
  `screening.py` (import, dedupe, decide, conflicts, kappa, counts, suggest; PRISMA counts from the log),
  `extract_check.py` (double extraction, consensus, risk-of-bias and charting files), `meta.py` (pooled
  estimates with tau-squared, I-squared and prediction interval, subgroups, forest spec; `r-check`
  against `metafor` is optional), `grade.py` (summary of findings from the certainty ratings). Figures:
  `figures.py` adds the pooled diamond and prediction bar to `forest`, `type: prisma` (PRISMA 2020 flow)
  and `type: rob` (traffic-light summary).
- Deliverables `case-report` and `review` in `assemble.py`, `audit.py`, `worklog.py`,
  `guideline_checklist.py`, `gate.py`, G4 and the hook; `init_project.py` types `case-report`,
  `systematic-review` and `review` (designs `scoping-review`, `narrative-review`). Hook marker
  `orchestra-prep:` (review-work briefs `screen-suggest`, `extract-draft`, `rob-draft`) is denied unless G2
  is open; `orchestra-role:` still needs G3. Item files for CARE, PRISMA-2020, PRISMA-ScR and SANRA.
- New finding codes: `E-CASE` (case-report anonymisation, consent, structure), `E-SCR` (screening and
  extraction log integrity), `E-GRADE` (claim strength against certainty, warn only), `E-META` (Python
  against `metafor` mismatch, warn only).
- Plan decisions: D1 each producer writes its own log and results document and `results_ledger.py import
  --merge` replaces only that source's records; D7 review-work briefs start with `orchestra-prep:` and need
  G2, not G3; D15 R is found per OS (`tools.rscript`, `PATH`, `R_HOME`, then standard install folders) and
  is never required.
- Scenarios (RED/GREEN, `tests/scenarios/BASELINE.md`): case-identifiers, case-consent-missing and
  sr-single-screener GREEN; sr-pool-heterogeneous GREEN in part (heterogeneity, uncertainty and the GRADE
  downgrade are reported; τ² and ledger ids are not cited); scoping-asks-pooling meets its expected lines
  but does not separate the plugin from no plugin (the skill was not loaded).
- Examples: `examples/fictional-case` (fictional patient, real verified references) and
  `examples/fictional-sr` (fictional included studies recorded as `add-manual`), each through G4.
- Known issues: the R cross-check needs R 4 or later with `metafor`; with the Microsoft Store build of
  Python on Windows, R started from Python may not see your R library (set `R_LIBS_USER` or
  `tools.rscript`). `grade.py` copies outcome names into `sof.md`, so a number in an outcome name
  ("30 ngày") is an E-NUM block until marked `not-a-result`. The writing skills may rerun all reviewers
  without scoring each round (`worklog.py score`), which costs time and leaves E-REV warnings; the example
  READMEs list the remaining author placeholders in the disclosure drafts.
- Roadmap: P5 done; P6 Extend (`ethics-and-crf`, `journal-selection`, `reviewer-response`, autorater,
  Codex and Antigravity packaging) is next.

## 0.5.0 (2026-11-22)
- P4 write: model skills `thesis-writing` (Vietnamese thesis: Đặt vấn đề, Chương 1–4, Kết luận,
  Kiến nghị, Tài liệu tham khảo, Phụ lục) and `manuscript-writing` (IMRaD article with a structured
  abstract and journal word limits), both written from results locked in G3, reviewed by read-only
  agents in at most three scored rounds, humanized, assembled, audited and exported only through G4;
  commands `/orchestra:thesis`, `/orchestra:manuscript` and `/orchestra:audit`. Writing references and
  role briefs (`references/writing/roles/`: introduction, methods, results, discussion, conclusion,
  abstract), the revise rubric, `vn-thesis.md`, `manuscript.md` and the AI-use disclosure template.
- Agents: `citation-verifier`, `statistical-reviewer`, `reporting-guideline-checker` and
  `scientific-editor` (read-only, write only into `reviews/`, report with a `drafts-digest:` line and a
  `scores` block); `consistency-auditor` and `committee-simulator` gain `disallowedTools`.
- Scripts: `assemble.py` (section order or `order.txt`, placeholders rendered, one citation numbering
  over the whole text, caption numbering, images, draft `.docx`; `--final` only with G4),
  `audit.py` (one pass over E-REF, E-NUM, E-STAT, E-LIT, E-CONS, P-codes, E-RG, E-FMT, E-PHI, E-REV →
  `reviews/audit.md` and `reviews/audit.json` with the hashes of what it checked),
  `guideline_checklist.py` (item-by-item checklist with locations, `--table` for the appendix; STROBE
  item list; one checklist per deliverable, `reviews/guideline-checklist-<deliverable>.json`, so the thesis
  and manuscript reviews never overwrite each other; the single `reviews/guideline-checklist.json` is still
  read when it is for that deliverable), `worklog.py` (`score` KEEP/REVERT/STOP, `revert`, `digest`, `decisions` →
  `out/author-decisions.md`), shared `crolib/drafts.py` and `crolib/reviews.py`. `build_docx.py` takes
  several inputs, lists, PNG images, a table of contents, a footer and an institution template, and
  writes a deterministic zip. `gate.py` opens G4 only from a clean, current audit, with one lock per
  deliverable, and writes `gates/state.json` with LF on every platform (as `save_references` does for
  `references.json`). A reviewer's `NEW-ANALYSIS: none` followed by a comment is no request.
- Hook: `gate_hook.py` (PreToolUse on Bash, PowerShell, Agent, Task) denies `assemble.py … --final` or a
  `build_docx.py` write of `out/thesis.docx`/`out/manuscript.docx` while G4 is closed for that
  deliverable, and an Agent prompt carrying `orchestra-role:` while G3 is not open.
- New finding codes: `E-FMT` (required sections, caption numbering, images, unfilled `[[TÁC GIẢ: …]]` /
  `[[AUTHOR: …]]`, also when wrapped over lines), `E-REV` (reviewer report missing or not about the current drafts); `E-RG` and
  `E-PHI` get their first scripts.
- Plan decisions: D1 model skills `thesis-writing`/`manuscript-writing`, command skills `thesis`,
  `manuscript`, `audit`; D2 G4 keeps one lock per deliverable, so opening it for the manuscript keeps the
  thesis lock; D19 manuscript files `02-introduction.md` and `04-results.md` (were `background.md` and
  `results.md`).
- Scenarios: thesis-g3-closed, discussion-overclaim, g4-export-blocked, revise-revert (RED/GREEN, results
  in tests/scenarios/BASELINE.md). Skill change recorded there: E-REF is the author's call in
  `thesis-writing` and `manuscript-writing` (verify, replace or record manually; never delete or reword
  the citing sentence, never edit a reference status to pass).
- Roadmap: case report, systematic review and literature-review mode (c) move to a new P5 Reviews and
  case reports; the old P5 becomes P6 Extend.
- Example: examples/fictional-cohort carried from the locked results to a Vietnamese thesis
  (`out/thesis.docx`, Chương 1 and 3 reused) and a Vietnamese journal manuscript (`out/manuscript.docx`),
  each through three scored review rounds and a clean audit, with G4 open for both, the AI-use disclosure
  draft and the author-decisions file; run and known issues in its README ("P4: write").

## 0.4.0 (2026-11-22)
- P3 present: research-figures (forest, Kaplan–Meier with numbers at risk, rates, STROBE/CONSORT flow
  drawn from the locked ledger or the de-identified CSV), conference-abstract (word limit, placeholders
  only, checks in order), research-poster (three print layouts, preflight, print note), defense-prep
  (consistency audit before any slide, deck from a JSON spec, rehearsal questions) and prose-humanizer
  (AI-prose patterns rewritten with per-paragraph invariants); commands `/orchestra:poster` and
  `/orchestra:defense`; agents `committee-simulator` (thesis committee or reviewer questions with
  answers from the project files) and `consistency-auditor` (numbers, dates and terms across
  deliverables).
- Scripts: `lint_prose.py` (prose patterns `P01`–`P30`, `--slides` for S17/S20/S21, `--count-words`),
  `invariants.py` (numbers, citations, placeholders and hedges per paragraph; `--merge` reverts a
  paragraph that changed them; `INV`), `consistency_audit.py` (`E-CONS`: same quantity across files,
  sample size rounded up, date ranges, percentage sums, abstract vs results, terms), `figures.py`
  (figures.json → SVG/PDF/PNG + `data.json`; document and poster profiles, font-relative layout),
  `pptx_from_spec.py` and `check_pptx.py` (ported from grand-rounds: placeholders, native KM and forest
  charts, poster size), `poster_build.py` (poster.json → HTML → PDF/PNG/DOM with headless Chrome/Edge,
  plus PPTX; layouts `editorial`, `pathway`, `figure-led`), `poster_preflight.py` (`E-PRINT`: page size,
  bleed, fonts, effective dpi, printed figure text size, overflow); shared `crolib/derived.py` (ledger
  lookup by id and part, safe formula evaluation).
- New finding codes: `E-CONS`, `E-PRINT`, `P01`–`P30`, `INV`; `S01`–`S21` stay the slide catalog, plus
  `S22` (`check_pptx.py` `leftover-markup`: citation key, backtick or `{{…}}` left in slide text).
- `figures.py` warns when a `style.colors` key matches no group label of a figure with uncoloured groups.
- `figures.py` (SVG, `data.json`) and the `poster_build.py` DOM dump write LF on Windows too.
- `gate.py check` prints an explicit line: "G3: open — results locked by … on …; n locked files
  unchanged" (open means approved, never unlocked), "G3: not open — not locked yet" or "G3: closed"
  with reasons. `results_ledger.py import` writes LF only, leaves a same-content ledger untouched and
  refuses to rewrite a ledger locked in G3.
- Scenarios: mzl-consistency, poster-87dpi, humanizer-invariants, vi-dense-prose (RED/GREEN, results in
  tests/scenarios/BASELINE.md).
- Optional dependencies: matplotlib (figures), python-pptx (slides, poster PPTX), Chrome or Edge
  (poster PDF/PNG and preflight).
- Example: examples/fictional-cohort carried from the locked results to four figures, a Vietnamese
  conference abstract, a 90 × 120 cm poster in three layouts and a thesis-defence deck with committee
  questions.

## 0.3.0 (2026-11-21)
- P2 analyse and report results: data-preparation (codebook, audit, cleaning log, de-identified data in
  `04_data/`), statistical-analysis (run mode per the SAP analysis register; import mode for SPSS, Stata
  or R output), results-writing (thesis Chapter 3 or manuscript Results from the locked ledger);
  commands `/orchestra:analyze` and `/orchestra:results`. Analysis workflow ported from the owner's
  `stat-analysis-vi` skill.
- Scripts: `crostats.py` (statistics library for project analysis scripts), `analysis_plan.py` (SAP
  analysis register, E-STAT), `results_ledger.py` (results import with `--verify-raw`),
  `render_results.py` (`{{R-…}}` placeholders from the ledger), `check_numbers.py` (E-NUM),
  `build_docx.py` (.docx with numbered tables, adapted from Amelia Le's `md2docx.py`).
- Notable behaviour: exact tests when expected counts are small; ANOVA or Kruskal–Wallis for three or
  more groups; a failed model is recorded as `MODEL FAILED` (interaction returns `nan`, never a
  p-value) and reported, never dropped; post-hoc and deviating analyses need a `POST-HOC A<n>:` or
  `DEVIATION A<n>:` line in `decisions.md`; projects vendor `crostats.py` into `05_analysis/` so their
  scripts rerun without the plugin; G3 locks the ledger, `results.json`, the analysis scripts and the
  data file by SHA-256; examples and scenario fixtures are byte-stable (LF only, `-text`).
- Scenarios: posthoc-fishing (two turns), number-drift, undeclared-deviation, spss-import (RED/GREEN,
  results in tests/scenarios/BASELINE.md).
- Final review fixes: `results_ledger.py import --verify-raw` also checks every CI bound and p against
  `raw`, accepts SPSS leading-dot numbers (`.032`) and always runs in `statistical-analysis` (run mode
  too); a relabel guard on import (changed `label`/`kind` for an id exits 1 until the placeholders are
  fixed and `--accept-relabel` is passed); new `.count` placeholder part (integer, 0 decimals) for the
  count in n (%) cells; `<!-- derived: … -->` comments must name ledger ids and pure formulas are
  evaluated (no id blocks, other text warns); G2 is opened with `--files 03_protocol/sap.md` and G3 also
  locks `sap.md`, so the analysis register cannot change after the results; stricter lines
  `POST-HOC A<n>: <reason>, requested by <author>, <YYYY-MM-DD>` and `DEVIATION A<n>: <what and why>,
  <YYYY-MM-DD>`, with deviation results labelled in prose; explicit group order and reference level
  (`order=[…]`, `Treatment(reference=…)`); ranges with a negative bound read "to"/"đến"; both skills run
  `check_numbers.py` on the rendered file; results-writing sets STATUS row 5 to `done` and reports a
  waived G3 in the hand-off; `build_docx.py` renders `>` quotes as indented paragraphs and strips
  backticks.
- Example: examples/fictional-cohort analysed end to end on simulated data (`tools/simulate_cohort.py`,
  seed 20261121): data preparation, analysis register A0–A5 plus one declared post-hoc subgroup, G3
  lock, Chapter 3 and its .docx.

## 0.2.0 (2026-11-21)
- P1 plan the study: research-question, literature-search, critical-appraisal (/orchestra:appraise),
  guideline-check, literature-review (/orchestra:review), protocol-design, sample-size-sap.
- Methods content by Amelia Le, ported to English.
- Scripts: samplesize.py, review_lint.py, cite_render.py (Vancouver numbering from the reference
  ledger). Verified reporting-guideline library.
- References: DOI-only records (Crossref) and author-supplied records (`search_lit.py add-manual`,
  listed as MANUAL); Europe PMC fallback in `search_lit.py fetch|add` and `verify_refs.py` when
  PubMed is unreachable.
- Scenarios: pmos-nomenclature, sample-size-lower-ci, reverse-causation, chapter1-paper-by-paper
  (RED/GREEN, results in tests/scenarios/BASELINE.md).
- Example: examples/fictional-cohort (simulated).
- Final-review fixes: group (collective) authors kept on all lookup paths and warned about by
  cite_render when missing; "PubMed unreachable + Europe PMC miss" is an error (exit 2), never
  "not found"; review_lint catches "Smith [@id] found…" and "Nguyen et al, 2020…" openers;
  evidence-policy has one rule for sources without PMID/DOI (`add-manual`, no "not verified" entries)
  and a §Citing sources rule (`[@id]` in every project document); "just do it" never opens a gate.

## 0.1.0 (2026-11-20)
- P0 foundation: marketplace, `orchestra` and `phi-guard` plugins, project skeleton, ledgers,
  literature lookup, reference verification, gates, PHI hook, de-identification, CI.
