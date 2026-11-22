# vi-dense-prose: a Vietnamese discussion paragraph dense with stock patterns
Skill under test: prose-humanizer (`lint_prose.py` before and after, `invariants.py`)
Fixtures: tests/scenarios/fixtures/vi-dense-prose/ (project.yaml, STATUS.md, decisions.md, the results ledger, and `06_writing/thesis/ch4-discussion.md` with one paragraph: "Trong bối cảnh…" (P03), "ngày càng" twice (P04), "đóng vai trò quan trọng/then chốt" three times (P02), "không chỉ… mà còn…" twice (P01), "góp phần" twice (P05), "Tóm lại," (P06), plus `{{R-A0-002}}` and one "có thể"). `lint_prose.py` on it: 11 hits, 7.9/100 words, P00 block, exit 1.
Allowed tools: Bash,Read,Write,Edit,Glob,Grep,Skill,Agent
Prompt: Đoạn này đọc như máy viết, sửa giúp tôi. (then a blank line and the paragraph of section 4.3 pasted verbatim from the fixture, as an author pastes it in chat; the first runs sent the sentence alone and both RED and GREEN only asked for the paragraph)
Expected (GREEN):
- `prose-humanizer` is invoked; `lint_prose.py` is run before and after the rewrite, and the after count is lower (no P00 block).
- `invariants.py` on the original and the rewrite reports no failure (the placeholder and the hedge "có thể" kept).
- The meaning is kept: follow-up after discharge, earlier detection of complications, adherence, the readmission rate placeholder, care coordination, cost; no new claim.
Baseline (RED): observed result recorded in BASELINE.md (the unaided model may rewrite by taste, swap one stock phrase for another, and never measure).
