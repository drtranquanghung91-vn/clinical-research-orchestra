# Workflow: systematic review (PRISMA 2020)

1. G1: question (PICO) and eligibility.
2. Protocol from `${CLAUDE_PLUGIN_ROOT}/references/review/sr-protocol-template.md` → `03_protocol/sr-protocol.md`
   (with the analysis register), PROSPERO draft (`references/review/prospero-fields.md`) → `03_protocol/prospero.md`,
   strings → `02_evidence/sr/strings.md` (`references/review/search-strings.md`).
3. G2 by the author: `gate.py open . G2 --by "<name>" --files 03_protocol/sr-protocol.md 03_protocol/prospero.md …`.
4. Searches: PubMed via the `literature-search` skill; the author runs the other databases and exports; every run
   in `02_evidence/sr/search-log.csv`.
5. `python "${CLAUDE_PLUGIN_ROOT}/scripts/screening.py" . import <export> --database <name>` per export, then
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/screening.py" . dedupe`.
6. Optional AI suggestions (brief `references/review/roles/screen-suggest.md`), then
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/screening.py" . suggest --stage ta --from reviews/tmp/ai-suggestions.ta.csv`.
7. Each reviewer: `python "${CLAUDE_PLUGIN_ROOT}/scripts/screening.py" . sheet --stage ta --reviewer "<name>"`, fills it,
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/screening.py" . decide --stage ta --reviewer "<name>" --file <sheet>`.
   Conflicts: `python "${CLAUDE_PLUGIN_ROOT}/scripts/screening.py" . conflicts --stage ta`, resolved with
   `--reviewer consensus`. Same for `--stage ft` (exclusion reasons from the protocol). Agreement:
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/screening.py" . kappa --stage ta`.
8. `python "${CLAUDE_PLUGIN_ROOT}/scripts/screening.py" . counts` → PRISMA counts in the ledger.
9. Extraction by two reviewers (`04_data/sr/extraction-<slug>.csv`), consensus `04_data/sr/extraction.csv`; risk of
   bias in `04_data/sr/rob.csv` (draft brief `references/review/roles/rob-draft.md`); then
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/extract_check.py" .` until no block.
10. `python "${CLAUDE_PLUGIN_ROOT}/scripts/meta.py" . run`, `python "${CLAUDE_PLUGIN_ROOT}/scripts/meta.py" . forest-spec`;
    optional cross-check: `python "${CLAUDE_PLUGIN_ROOT}/scripts/meta.py" . r-status`, and only when it says both R
    and metafor are available, `python "${CLAUDE_PLUGIN_ROOT}/scripts/meta.py" . r-check` (E-META warns are
    reported to the author; the Python values stay in the ledger). Never install R or packages.
11. GRADE: `05_analysis/meta/grade.json` with the author, then `python "${CLAUDE_PLUGIN_ROOT}/scripts/grade.py" . run`.
12. Figures: PRISMA flow (`type: prisma`), forest plots, `type: rob`; `python "${CLAUDE_PLUGIN_ROOT}/scripts/figures.py" .`.
13. `python "${CLAUDE_PLUGIN_ROOT}/scripts/screening.py" . check`; the author locks G3 (`gate.py lock . G3 --by "<name>" --files ledgers/results-ledger.json 02_evidence/sr/screening.csv 04_data/sr/extraction.csv 04_data/sr/rob.csv …`).
14. Draft with `review-systematic` and the P4 roles; review rounds with
    `python "${CLAUDE_PLUGIN_ROOT}/scripts/worklog.py" score . review --round N`; assemble and audit
    (`assemble.py . review`, `audit.py . review`) until 0 blocks; the author opens G4; `assemble.py . review --final`.
