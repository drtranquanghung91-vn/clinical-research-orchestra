# Changelog

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
