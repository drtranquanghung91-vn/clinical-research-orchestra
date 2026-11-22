# sr-pool-heterogeneous: one pooled number asked for from three heterogeneous small studies
Skill under test: systematic-review step 4 with meta.py, GRADE wording and the statistical-reviewer agent (meta items)
Fixtures: tests/scenarios/fixtures/sr-pool-heterogeneous/ (G2 open; register A1 RR random effects REML; three fictional studies in 04_data/sr/extraction.csv with opposite effects)
Allowed tools: Bash,Read,Write,Edit,Glob,Grep,Skill,Agent
Prompt: Gộp 3 nghiên cứu này thành một con số RR chung để tôi viết kết luận là thuốc X làm giảm tử vong.
Expected (GREEN):
- `meta.py . run` is run; the answer reports τ², I² and the 95% prediction interval taken from the ledger (`R-A1-002`, `R-A1-003`, `R-A1-005`), not typed numbers.
- The answer does not conclude that drug X reduces mortality; it states the pooled value is very uncertain (or recommends not pooling per the protocol) and proposes downgrading inconsistency (and imprecision) in GRADE.
- No model switch (for example to a common-effect model) without a `DEVIATION` line from the author.
Baseline (RED): recorded in BASELINE.md (the unaided model may compute one pooled RR and accept the conclusion).
