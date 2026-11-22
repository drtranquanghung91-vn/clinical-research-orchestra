# scoping-asks-pooling: a scoping review author asks for risk of bias and a pooled estimate
Skill under test: literature-review mode (c) scoping; meta.py refusal for scoping reviews
Fixtures: tests/scenarios/fixtures/scoping-asks-pooling/ (type review, design scoping-review, PCC protocol with only A0, charting.csv verified)
Allowed tools: Bash,Read,Write,Edit,Glob,Grep,Skill,Agent
Prompt: Đánh giá nguy cơ sai lệch các nghiên cứu và gộp kết quả HbA1c thành một ước lượng chung cho tổng quan phạm vi này.
Expected (GREEN):
- The answer explains that scoping reviews chart and summarise evidence, do not rate risk of bias or pool (PRISMA-ScR), and offers to convert to a systematic review protocol (new G2) with the systematic-review skill.
- No `04_data/sr/rob.csv` is written and no pooled estimate appears in any file or in the answer; `meta.py`, if run, is refused.
Baseline (RED): recorded in BASELINE.md.
