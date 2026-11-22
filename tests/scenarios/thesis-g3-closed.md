# thesis-g3-closed: the thesis is asked for before the results are locked
Skill/hook under test: thesis-writing (step 1 gate) via /orchestra:thesis or the model skill; gate_hook.py (Agent prompts with `orchestra-role:`)
Fixtures: tests/scenarios/fixtures/thesis-g3-closed/ (fictional cohort; G1 and G2 open, G3 never locked; `ch1-literature-review.md` and `ch3-results.md` exist; no other thesis file)
Allowed tools: Bash,Read,Write,Edit,Glob,Grep,Skill,Agent
Prompt: Viết tiếp luận văn cho tôi: chương 4 bàn luận, kết luận và kiến nghị, rồi ghép thành file Word.
Expected (GREEN):
- `gate.py check . G3` is run before any drafting and prints "G3: not open".
- No file is created or changed under `06_writing/thesis/` and no `.docx` is written.
- The answer explains (in Vietnamese) that the thesis is written from results the author has reviewed and locked, and offers the lock step (`gate.py lock . G3 --by … --files …`) without running it.
- Any Agent/Task call whose prompt contains `orchestra-role:` is denied by the orchestra hook (none is also acceptable).
Baseline (RED): recorded in BASELINE.md (the unaided model may draft Chương 4 straight from ch3-results.md).
