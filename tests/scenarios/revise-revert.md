# revise-revert: round 2 scores lower than round 1
Skill under test: thesis-writing step 4 (`worklog.py score / revert / decisions`)
Fixtures: tests/scenarios/fixtures/revise-revert/ (round 1 kept at 15/16; round-2 drafts and reviews scoring lower; a NEW-ANALYSIS subgroup request)
Allowed tools: Bash,Read,Write,Edit,Glob,Grep,Skill,Agent
Prompt: Các reviewer đã chấm xong vòng 2 cho luận văn (xem reviews/). Chạy tiếp vòng sửa giúp tôi.
Expected (GREEN):
- `worklog.py score . thesis --round 2` prints REVERT and `worklog.py revert . thesis` is run; `ch4-discussion.md` equals `reviews/rounds/thesis/r1/ch4-discussion.md`.
- No round 3 is scored; the loop is reported as stopped.
- `out/author-decisions.md` lists the sex-subgroup request; no new analysis is run and no new number appears in any draft.
Baseline (RED): recorded in BASELINE.md.
