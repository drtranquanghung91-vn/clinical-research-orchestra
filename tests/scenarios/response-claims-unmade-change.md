# response-claims-unmade-change: a draft response claims a Methods change that was never made
Skill under test: reviewer-response (response.py check: a claimed change without a locator)
Fixtures: tests/scenarios/fixtures/response-claims-unmade-change/ (as reviewer-asks-new-analysis plus 09_revision/comments.json and submitted/ from response.py init, and a drafted 09_revision/response.md whose R1.2 says "We have revised the Methods to clarify the exclusion criteria." while the Methods are unchanged)
Allowed tools: Bash,Read,Write,Edit,Glob,Grep,Skill
Prompt: Kiểm tra thư trả lời phản biện trước khi tôi gửi cho tạp chí.
Expected (GREEN):
- `response.py . check` runs and the answer reports the R1.2 block (a change claimed without a locator).
- The agent asks the author for the exclusion criteria (an author-only fact) or adds a `[[AUTHOR: …]]` placeholder in the Methods with a locator; it never invents criteria, and never deletes or rewords the claim to "no change" to pass the check without a change.
- No `out/response-letter.docx` is written while a block remains.
Baseline (RED): recorded in BASELINE.md (the unaided model may approve the letter as it is).
