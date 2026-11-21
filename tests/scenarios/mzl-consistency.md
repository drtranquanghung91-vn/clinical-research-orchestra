# mzl-consistency: a defence deck is asked for while the thesis contradicts itself
Skill under test: defense-prep (step 1 consistency audit before slides, `consistency_audit.py`, `consistency-auditor` agent)
Fixtures: tests/scenarios/fixtures/mzl-consistency/ (cohort project as in number-drift, gate G3 locked over the ledger, results.json, analysis.py and the data; `06_writing/thesis/abstract.md` (study window "tháng 01/2024 đến tháng 12/2025", "Tỷ lệ không tái nhập viện là 85%"), `ch2-methods.md` (window "tháng 01/2024 đến tháng 06/2025", formula result 26,65 written as "≈26 bệnh nhân"), `ch3-results.md` and its `ch3-results.rendered.md` ("Tỷ lệ không tái nhập viện là 86,3%"); no `07_present/defense/`). The three planted errors are the MZL-session lessons (main spec §11.2); `consistency_audit.py .` on the fixture gives exactly 3 E-CONS blocks.
Allowed tools: Bash,Read,Write,Edit,Glob,Grep,Skill,Agent
Prompt: Làm slide bảo vệ luận văn cho tôi.
Expected (GREEN):
- `defense-prep` is invoked and `consistency_audit.py` is run on the project before any slide is planned.
- All three E-CONS blocks are reported to the author: 85% vs 86,3% for the same rate, the sample size "≈26" (26,65 must be rounded up to 27), and the end date 12/2025 vs 06/2025.
- The thesis fix is proposed or asked for (which value and which end date are right; the rate should come from the ledger, R-A0-003 = 85.0), and no value is invented for what only the author knows (the true end date).
- `07_present/defense/deck.json` is not written while a block stands.
Baseline (RED): observed result recorded in BASELINE.md (the unaided model may plan or build the slides straight from the chapters and carry the contradictions into the deck).
