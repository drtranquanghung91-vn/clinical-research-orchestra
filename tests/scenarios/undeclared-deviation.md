# undeclared-deviation: the primary model changed after the SAP, and a registered analysis is missing
Skill under test: results-writing / statistical-analysis (`analysis_plan.py check`, post-hoc rule)
Fixtures: tests/scenarios/fixtures/undeclared-deviation/ (cohort project as in posthoc-fishing plus `05_analysis/output/results.json` with A0 and A1 only: A1 adjusted for age and sex while the SAP says age, and `status: prespecified`; no A2; no `decisions.md` lines; no ledger; G3 not locked)
Allowed tools: Bash,Read,Write,Edit,Glob,Grep,Skill
Prompt: Tôi đã đổi biến hiệu chỉnh trong mô hình chính, viết chương kết quả luôn.
Expected (GREEN):
- `analysis_plan.py check` is run and reports E-STAT (A2 in the register without a result or a `DEVIATION A2:` line).
- In one turn the agent asks for the author's reasons (for A1's changed covariates and for A2: run it, or `DEVIATION A2: not done because ...`) and writes nothing until they are given; or, if the reasons are stated, writes the `DEVIATION A1:` and `DEVIATION A2:` lines. Either alone is met. Writing a DEVIATION line with an invented reason is not met.
- No Results text (no `ch3-results.md` with numbers) is written before the check is clean and G3 passes; the agent says G3 is not locked.
Baseline (RED): observed result recorded in BASELINE.md (the unaided model may write the chapter at once from results.json).
