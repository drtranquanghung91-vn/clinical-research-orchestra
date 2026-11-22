---
name: conference-abstract
description: 'Use when a conference abstract must be written or checked: submission text with a word limit. Triggers: "tóm tắt hội nghị", "abstract hội nghị", "gửi abstract", "conference abstract", "abstract submission", "báo cáo hội nghị", "tóm tắt báo cáo"; or after results-writing when the author plans to present.'
---

# Conference abstract

## 1. Core rule
No number is typed by hand: every result is a `{{R-…}}` placeholder from the locked ledger. Estimates
come with their 95% CI. Post-hoc results are labelled exploratory. No causal wording for observational
designs. Detail: `${CLAUDE_PLUGIN_ROOT}/references/workflows/conference-abstract.md`.

## 2. Precondition
`python "${CLAUDE_PLUGIN_ROOT}/scripts/gate.py" check . G3` exits 0 (a `WAIVE G3:` line also passes; say in
the hand-off that the ledger is unlocked). Otherwise stop: use the Skill tool with `statistical-analysis`;
write no abstract text.

## 3. Conference rules, asked once
Ask once: word limit, headings, language, structured or not. Defaults when the author does not know
(`${CLAUDE_PLUGIN_ROOT}/references/judgement-defaults.md`): 250 words; Background/Objective, Methods,
Results, Conclusion. The venue's limit wins. Record the answers in `decisions.md`.

## 4. Write
`07_present/abstract.md` with placeholders only. The primary result comes first; every estimate has its
CI; the conclusion answers the objective and goes no further than the data. Describe an ordered trend
("tăng dần theo", "increases with", "dose-response") only when the results ledger holds a trend test
supporting it; otherwise give the group values and say the CIs include 1.

## 5. Checks
Scripts in `${CLAUDE_PLUGIN_ROOT}/scripts/`, from the project folder, in order; fix every block:
1. `render_results.py . 07_present/abstract.md` writes `abstract.rendered.md`.
2. `check_numbers.py . 07_present/abstract.rendered.md`.
3. `analysis_plan.py check . --text 07_present/abstract.md`.
4. `consistency_audit.py . 07_present/abstract.rendered.md 06_writing/thesis/ch3-results.rendered.md`
   (drop the second file when it does not exist; say so).
5. `lint_prose.py --count-words 07_present/abstract.rendered.md`: at or under the limit.
6. `lint_prose.py 07_present/abstract.rendered.md`.
Report each script's last line. A check that did not run is reported as not run, never as passed.

## 6. Hand-off
Offer the agent `committee-simulator` (deliverable `abstract`) for review questions. A .docx only when asked:
`build_docx.py 07_present/abstract.rendered.md out/abstract.docx --project .`. Ask the author to read the
rendered file before submission.

## 7. Workflow
`${CLAUDE_PLUGIN_ROOT}/references/workflows/conference-abstract.md`
