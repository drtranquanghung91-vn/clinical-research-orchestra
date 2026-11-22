STATUS: PASS

Round 3 (final round). `drafts-digest` is unchanged from round 2
(`f242ce1e24d735a5c8891b68fa491e4872f7f0c7260670d9e3285767c80aa340`), confirming no manuscript draft
was edited since the last pass. Re-ran all checks fresh rather than relying on the prior report.

`worklog.py digest . manuscript` exited 0. `analysis_plan.py register .` returned A0–A5; `decisions.md`
has exactly one unregistered analysis, `POST-HOC A6:` (HbA1c-group × age interaction on 1-year
readmission, requested by the author 2026-11-21), and no `DEVIATION A<n>:` line. `analysis_plan.py
check . --text` on `01-abstract.md 04-results.md 05-discussion.md 06-conclusion.md` returned 0 block,
0 warn.

`03-methods.md` matches the SAP: logistic regression for the primary outcome (3-group HbA1c, <7%
reference) and Cox for the time-to-event secondary outcome with the Schoenfeld-residual PH check; the
four pre-specified covariates (age, sex, DM duration, comorbidity); insulin use and length of stay
correctly excluded as suspected mediators; the ≤5%-missing complete-case rule (27 patients, 2.5%,
missing DM duration); the no-multiplicity-correction rule for exploratory secondary outcomes; and the
unregistered POST-HOC A6 analysis stated plainly with its scope and covariates.

Results-bearing sections (abstract, results, discussion, conclusion): every OR/HR carries its 95% CI
via `.full`/`.ci` placeholders (no S-CI); p is never reported as the effect size and the CI-crosses-1
primary finding is worded "chưa được chứng minh có ý nghĩa thống kê" / "ước lượng chưa chính xác", not
"không khác biệt" (no S-PVAL); the secondary tests (A2–A5) and A6 are repeatedly and explicitly
labelled exploratory/post-hoc, not hidden (no S-MULT, no S-POSTHOC — A6 also reports the interaction
test, not a bare subgroup split); the ordered-group pattern in the results text is paired with an
explicit disclaimer that no trend test was registered, so no unsupported dose-response claim is made
(no S-TREND); design is `project.yaml → design: cohort` (observational) and only association language
("liên quan", "đi kèm", "cùng chiều") is used throughout, no causal verb (no S-CAUSAL).

No request in the brief or draft text calls for an analysis outside the register that the text then
answers itself.

FINDINGS
| code | location (file:line) | fix |
|---|---|---|
| none | — | — |

GAPS      None — `worklog.py digest`, `analysis_plan.py register`, and `analysis_plan.py check --text`
all exited 0; methods and every results-bearing manuscript file were read in full against
`03_protocol/sap.md` and `decisions.md`.
CONFLICTS  None.
NEW-ANALYSIS: none
drafts-digest: manuscript f242ce1e24d735a5c8891b68fa491e4872f7f0c7260670d9e3285767c80aa340
```scores
{"deliverable": "manuscript", "statistics": 2}
```
