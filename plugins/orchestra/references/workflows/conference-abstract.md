# Conference abstract: workflow

Scripts are in `${CLAUDE_PLUGIN_ROOT}/scripts/`; run them from the project folder.

1. Gate: `gate.py check . G3` exits 0, or a `WAIVE G3:` line exists (say so in the hand-off).
2. Ask once for the venue's rules: word limit, headings, language, structured or free. Defaults are in
   `${CLAUDE_PLUGIN_ROOT}/references/judgement-defaults.md` (250 words; Background/Objective, Methods,
   Results, Conclusion). Note the answers in `decisions.md`.
3. Draft `07_present/abstract.md`. Background: one or two sentences and the objective. Methods: design,
   setting, sample (placeholder `.n`), main outcome and analysis. Results: primary result with estimate and
   95% CI by placeholder, then at most two secondary. Conclusion: answers the objective, no causal verb for
   an observational design, post-hoc results labelled exploratory, limits named.
4. Run the six checks of the skill in order. Count words on the rendered file, never on the placeholders.
   Over the limit: cut Background first, never a CI.
5. Typical findings: an abstract number found nowhere else in the thesis (warn): re-derive it from the
   ledger; a rate printed two ways (block): use the placeholder in both places.
6. Optional: `build_docx.py` for a .docx; agent `committee-simulator` (deliverable `abstract`, 8-10 questions); save its
   reply to `reviews/committee-abstract.md` (the agent writes no file).
