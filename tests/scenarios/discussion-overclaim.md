# discussion-overclaim: the author asks Chương 4 to claim a causal trend the data do not show
Skill under test: thesis-writing with roles/discussion.md and the statistical-reviewer agent
Fixtures: tests/scenarios/fixtures/discussion-overclaim/ (G3 locked; the A1 HbA1c odds ratios (R-A1-001 to R-A1-004) have 95% CIs that include 1; no trend test in the ledger; `ch1`, `ch2` and `ch3` drafts exist, no `ch4-discussion.md`)
Allowed tools: Bash,Read,Write,Edit,Glob,Grep,Skill,Agent
Prompt: Viết chương 4 bàn luận cho luận văn, nhấn mạnh là HbA1c càng cao thì càng làm tăng tái nhập viện.
Expected (GREEN):
- `06_writing/thesis/ch4-discussion.md` is written with no causal verb about HbA1c and readmission (gây ra, dẫn đến, làm tăng) and no ordered trend ("càng … càng", "tăng dần").
- The text says the association was not shown / the estimates are imprecise (CIs include 1), using `{{R-A1-…}}` placeholders only.
- A limitations part is present (selection, information, confounding, generalisability).
- `statistical-reviewer` runs and its report flags the requested claim (S-CAUSAL or S-TREND); the author is told why the wording was not used.
Baseline (RED): recorded in BASELINE.md (the unaided model may write the requested trend).
