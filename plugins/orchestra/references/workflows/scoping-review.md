# Workflow: scoping review (PRISMA-ScR)

Steps 1–8 of `systematic-review.md` with a PCC question and a register holding only A0. Then:

1. Charting: one reviewer charts into `04_data/sr/charting.csv` (columns from the protocol plus `extracted_by`,
   `verified_by`), a second verifies; `python "${CLAUDE_PLUGIN_ROOT}/scripts/extract_check.py" .` until no block.
2. No risk of bias, no pooling: `meta.py` refuses a scoping review. A request for either is answered: scoping
   reviews map evidence; a pooled estimate needs a systematic review protocol (offer to convert, with a new G2).
3. Figures: PRISMA flow (`type: prisma`, same counts); concept tables.
4. G3 by the author (`gate.py lock . G3 --by "<name>" --files ledgers/results-ledger.json 02_evidence/sr/screening.csv 04_data/sr/charting.csv`),
   drafting with `review-scoping`, review rounds, `audit.py . review` (E-SCR), G4 by the author, `assemble.py . review --final`.
