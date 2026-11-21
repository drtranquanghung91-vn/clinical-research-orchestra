# reverse-causation: a diet → PCOS case-control is challenged
Skill under test: protocol-design (step 6, reverse causation in bias-confounding.md)
Fixtures: none (no project; the skill answers in chat)
Allowed tools: Bash,Read,Write,Edit,Glob,Grep,Skill
Prompt: Tôi muốn làm nghiên cứu bệnh chứng: chế độ ăn nhiều đường có làm tăng nguy cơ PCOS không? Thiết kế giúp tôi.
Expected (GREEN):
- protocol-design warns that diet measured after diagnosis may change because of the diagnosis (reverse causation).
- It proposes measuring pre-diagnosis diet (or incident cases) or a cohort design.
- The limitation is recorded in the design output.
Baseline (RED): accepts the case-control design without the warning.
