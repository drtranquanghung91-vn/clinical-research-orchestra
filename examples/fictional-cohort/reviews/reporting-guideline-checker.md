STATUS: FINDINGS
FINDINGS
| code | location (file:line) | fix |
|---|---|---|
| 13a | 06_writing/thesis/ch3-results.md:11 | Flow figure (Biểu đồ 3.1) only has 2 counts (eligible cohort, analysed-after-adjustment); add screening/eligibility-stage numbers if the simulated HIS/EMR extraction ever records them, or keep the existing explicit caveat that this is not a full STROBE flow diagram. |
| 13b | 06_writing/thesis/ch3-results.md:13 | Only the reason for the adjusted-model exclusion (27 missing duration-of-diabetes) is given; no reason is given for any screening-stage drop-out because that count was never captured — note this limitation explicitly in 2.1 or the figure caption rather than leaving it implicit. |
| 13c | 06_writing/thesis/ch3-results.md:9 | Figure F4 is a simplified 2-box diagram, not a full STROBE participant-flow diagram; author already flags this in the caption (line 11) — no action needed beyond keeping the caveat if the figure is not upgraded. |

This is a mechanical checklist refresh, not a new scored revise-loop round (the thesis's own revise loop
stopped at its round 3 on 2026-11-22). The live `reviews/guideline-checklist.json` had been overwritten by
the separate manuscript deliverable's own review rounds after the thesis was closed; this refresh restores
an accurate thesis checklist against the CURRENT drafts, after the author's final fixes (`00-tom-tat.md`
added, the funding placeholder in `ch2-methods.md` filled). Items 1a, 1b, 11 and 22 — previously flagged
absent/mismatched in a stale round-3 snapshot — are now confirmed present: 1a/1b via `00-tom-tat.md`'s
structured abstract naming the design; 11 via `ch2-methods.md`'s HbA1c grouping description and
`ch1-literature-review.md`'s rationale for the operational cut-off; 22 via the filled funding statement.

GAPS      none — every item had drafts text to check.
CONFLICTS none — all partial items (13a–13c) are explained as inherent to the simulated dataset (no
screening-stage counts were ever extracted); only the author can decide whether to attempt a fuller flow
diagram or accept the simplified one.
drafts-digest: thesis 977ad27e37c05190c88e1914f977fd95f1e5336510b394cf28502217c2ae0a64
```scores
{"deliverable": "thesis", "guideline": 2}
```
