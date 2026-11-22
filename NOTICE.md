# Notices

This repository is MIT-licensed (see LICENSE). It includes or adapts the following work.

| Item | Origin | License | Use |
|---|---|---|---|
| Research-methods skills and references | Amelia Le, version 3 of 20 Nov 2026 (supersedes 18 Nov) | contributed under MIT | ported to English, restructured |
| `litapi.py`, `verify_refs.py`, `phi_scan.py` patterns, slop catalog | grand-rounds by Trần Quang Hưng (github.com/drtranquanghung91-vn/grand-rounds, commit 506dd9c) | MIT | copied and adapted |
| Prose-pattern catalog and `prose-humanizer` method | `humanizer` skill v4.0.0 | MIT | adapted to academic writing, Vietnamese set added |
| Design patterns (outline-as-plan, two-stage citation verification, reviewer accept/revert loop) | PaperOrchestra, Google Research (github.com/google-research/paper-orchestra) | Apache-2.0 | inspiration only; no code or prompt text copied |
| `cite_render.py` numbering logic | Amelia Le, version 3 | contributed under MIT | adapted to the reference ledger (`[@id]` keys) |
| `samplesize.py` | Amelia Le, version 3 | contributed under MIT | unchanged |
| Statistical-analysis workflow (`statistical-analysis`, `crostats.py` test choices and reporting defaults) | `stat-analysis-vi` skill by Trần Quang Hưng (repository owner) | MIT | ported to English, adapted (SAP register, post-hoc rules) |
| `build_docx.py` | Amelia Le, `md2docx.py` (v3, 20 Nov 2026) | contributed under MIT | approach adapted (WordprocessingML written directly; Markdown subset, numbered tables) |
| `pptx_from_spec.py`, `check_pptx.py` | grand-rounds 0.2.0 (Trần Quang Hưng) | MIT | adapted: placeholders, km/forest charts, poster size |
| STROBE item list (`references/reporting-guidelines/items/STROBE.json`, read by `guideline_checklist.py`) | STROBE Statement 2007 (strobe-statement.org) | none needed (ids and order only) | item ids and order only; every item text (34 items) is our own paraphrase in ≤ 12 words, no official wording |
| CARE item list (`references/reporting-guidelines/items/CARE.json`, read by `guideline_checklist.py`) | CARE checklist (care-statement.org) | none needed (ids and order only) | item ids and order only; every item text (30 items) is our own paraphrase in ≤ 12 words, no official wording |
| PRISMA-2020 item list (`references/reporting-guidelines/items/PRISMA-2020.json`, read by `guideline_checklist.py`) | PRISMA 2020 statement (prisma-statement.org) | none needed (ids and order only) | item ids and order only; every item text (42 items; the PRISMA 2020 for Abstracts checklist is not included) is our own paraphrase in ≤ 12 words, no official wording |
| PRISMA-ScR item list (`references/reporting-guidelines/items/PRISMA-ScR.json`, read by `guideline_checklist.py`) | PRISMA-ScR checklist (prisma-statement.org) | none needed (ids and order only) | item ids and order only; every item text (22 items: 20 essential, 2 optional) is our own paraphrase in ≤ 12 words, no official wording |
| SANRA item list (`references/reporting-guidelines/items/SANRA.json`, read by `guideline_checklist.py`) | SANRA scale (Baethge et al. 2019, Research Integrity and Peer Review) | none needed (item names only) | the 6 item names only, each as our own paraphrase in ≤ 12 words; no anchor definitions or scoring text |
| metafor goldens (`tests/unit/fixtures/meta/metafor-goldens.json`) | values computed once with the R package metafor (Viechtbauer) from its example datasets `dat.bcg` and `dat.normand1999` | metafor is GPL and is not included; only computed numbers and the example inputs are stored | test oracle only |
