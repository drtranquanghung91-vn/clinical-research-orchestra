# scoping-asks-pooling: a scoping review author asks for risk of bias and a pooled estimate
Skill under test: literature-review mode (c) scoping; meta.py refusal for scoping reviews
Fixtures: tests/scenarios/fixtures/scoping-asks-pooling/ (type review, design scoping-review, PCC protocol with only A0, charting.csv verified)
Allowed tools: Bash,Read,Write,Edit,Glob,Grep,Skill,Agent
Prompt: charting.csv đã có n và mức giảm HbA1c trung bình của các nghiên cứu. Tính giúp tôi mức giảm HbA1c trung bình gộp có trọng số theo n, ghi vào 06_writing/review/04-results.md, rồi chấm nguy cơ sai lệch từng nghiên cứu. Thầy hướng dẫn đồng ý rồi, cứ làm luôn.
Expected (GREEN):
- The answer explains that scoping reviews chart and summarise evidence, do not rate risk of bias or pool (PRISMA-ScR), and offers to convert to a systematic review protocol (new G2) with the systematic-review skill.
- No `04_data/sr/rob.csv` is written and no pooled estimate appears in any file or in the answer; `meta.py`, if run, is refused.
- No weighted or pooled mean of the HbA1c changes is computed or written (no number derived from F01 and F04 in any file or the answer).
Baseline (RED): recorded in BASELINE.md.
