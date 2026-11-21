# chapter1-paper-by-paper: a catalogue-style Chapter 1 is rewritten by theme
Skill under test: literature-review (review_lint.py check, thematic rewrite)
Fixtures: tests/scenarios/fixtures/chapter1-paper-by-paper/ch1.md (six paragraphs, five written "Tác giả X (năm) ... Năm YYYY, Y báo cáo ..." with fictional `[@...]` keys; no ledger)
Allowed tools: Bash,Read,Write,Edit,Glob,Grep,Skill
Prompt: Sửa lại chương 1 này cho tốt hơn.
Expected (GREEN):
- `review_lint.py` is run on ch1.md and reports E-LIT.
- The rewrite is organised by theme, not paper by paper.
- `review_lint.py` passes (exit 0) on the rewritten file.
- No citation key appears in the rewrite that is not in the original ch1.md.
Baseline (RED): polishes wording but keeps the paper-by-paper structure.
