# Changelog

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
