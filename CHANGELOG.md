# Changelog

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

## 0.1.0 (2026-11-20)
- P0 foundation: marketplace, `orchestra` and `phi-guard` plugins, project skeleton, ledgers,
  literature lookup, reference verification, gates, PHI hook, de-identification, CI.
