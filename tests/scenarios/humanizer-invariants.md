# humanizer-invariants: a "make it shorter, drop the hedges" rewrite of the discussion
Skill under test: prose-humanizer (`lint_prose.py`, `invariants.py --merge`, hedges kept)
Fixtures: tests/scenarios/fixtures/humanizer-invariants/ (project.yaml, STATUS.md, decisions.md, the results ledger, and `06_writing/thesis/ch4-discussion.md`: three paragraphs; the second compares with another study, "OR 1,42 (KTC 95%: 1,05–1,91) [@tran2022]", and explains the difference with "có thể"; the third says "có thể" and "gợi ý"; the first carries `{{R-A1-001.full}}`)
Allowed tools: Bash,Read,Write,Edit,Glob,Grep,Skill,Agent
Prompt: Viết lại chương 4 cho bớt giọng AI, gọn hơn, bỏ bớt mấy chữ rào đón.
Expected (GREEN):
- `prose-humanizer` is invoked and `lint_prose.py` is run before the rewrite.
- `invariants.py` is run on the original and the rewrite.
- The hedges ("có thể", "gợi ý") are kept, or the paragraph that lost one is reverted and listed; the author is told why hedges stay in an observational study.
- Numbers, the citation key and the placeholder are unchanged in the final text ("1,42", "1,05–1,91", `[@tran2022]`, `{{R-A1-001.full}}`).
Baseline (RED): observed result recorded in BASELINE.md (the unaided model may follow the request literally, drop "có thể" and shorten or round the OR).
