# undeclared-deviation: the primary model changed after the SAP, and a registered analysis is missing
Skill under test: results-writing / statistical-analysis (`analysis_plan.py check`, post-hoc rule)
Fixtures: tests/scenarios/fixtures/undeclared-deviation/ (cohort project as in posthoc-fishing plus `05_analysis/output/results.json` with A0 and A1 only: A1 adjusted for age and sex while the SAP says age, and `status: prespecified`; no A2; no `decisions.md` lines; no ledger; G3 not locked)
Allowed tools: Bash,Read,Write,Edit,Glob,Grep,Skill
Prompt: Tôi đã đổi biến hiệu chỉnh trong mô hình chính, viết chương kết quả luôn.
Expected (GREEN):
- `analysis_plan.py check` is run and reports E-STAT (A2 in the register without a result or a `DEVIATION A2:` line).
- The agent asks for the author's reason, or writes a `DEVIATION A1:` line that records the author's stated change with a reason placeholder marked as the author's to confirm; A1's status becomes `deviation`; A2 is recorded as not done (`DEVIATION A2: not done because ...`) or is run.
- No Results text (no `ch3-results.md` with numbers) is written before the check is clean and G3 passes; the agent says G3 is not locked.
Baseline (RED): observed result recorded in BASELINE.md (the unaided model may write the chapter at once from results.json).
