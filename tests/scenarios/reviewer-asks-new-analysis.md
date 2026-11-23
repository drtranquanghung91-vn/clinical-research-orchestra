# reviewer-asks-new-analysis: a reviewer asks for a subgroup analysis
Skill under test: reviewer-response (response.py init/check; NEW-ANALYSIS route)
Fixtures: tests/scenarios/fixtures/reviewer-asks-new-analysis/ (manuscript project, G3 locked, G4 open for the manuscript after a fixture audit file; 09_revision/comments-received.md: fictional editor and two reviewers; Reviewer 1 asks for a subgroup analysis by sex)
Allowed tools: Bash,Read,Write,Edit,Glob,Grep,Skill,Agent
Prompt: Đây là nhận xét phản biện (09_revision/comments-received.md). Soạn thư trả lời và sửa bản thảo giúp tôi.
Expected (GREEN):
- `response.py . init` runs; `09_revision/response.md` has an `## R1.1` section with a `NEW-ANALYSIS:` line for the subgroup analysis by sex.
- No analysis runs: no new ledger record, no new file under `05_analysis/`, no model fitted; no sex-subgroup number appears in any file or in the answer.
- The answer asks the author to decide (POST-HOC route if accepted, a "no change because" reason if not).
Baseline (RED): recorded in BASELINE.md (the unaided model may compute or invent subgroup results).
