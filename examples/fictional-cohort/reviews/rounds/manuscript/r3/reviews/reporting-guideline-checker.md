STATUS: FINDINGS

FINDINGS
| code | location (file:line) | fix |
|---|---|---|
| 12e | 03-methods.md: no sensitivity analysis described | Add a sensitivity analysis to Methods/Results (for example: re-fit the adjusted model excluding the complete-case drop, or with an alternative missing-data approach) and label it as a sensitivity check, distinct from the secondary/exploratory analyses already listed. |
| 13a | 04-results.md:12 | State, if the data allow, the count at each stage from the ~1,200 patients available before exclusion criteria to the final analytic sample, or explicitly note in Methods why only two counts (descriptive sample, adjusted-model sample) can be reconstructed. |
| 13b | 03-methods.md:12 | Report, if recoverable from the extraction log, how many patients were excluded for each listed criterion (death, type 1/gestational/secondary diabetes, missing valid HbA1c, duplicate admission); currently only the 27-patient (2.5%) missing-covariate exclusion has a count. |
| 13c | 04-results.md:10 | Keep the simplified diagram but add the eligible/screened counts if they can be reconstructed, or keep the explicit caveat (already present) as the final reporting choice. |
| 14b | 04-results.md:7 | Add missing-value counts for the other Table 1 variables (age, sex, comorbidity, insulin use, length of stay), not only for duration of diabetes. |
| 14c | 03-methods.md:7 | Report a summary follow-up statistic in Results (e.g., median follow-up time or total person-time before censoring), not only the fixed 365-day design description in Methods. |

This is the final round of the revise loop. The drafts digest is identical to round 2 (f242ce1e...a340), confirming no edits were made to 06_writing/manuscript/ since that review. All 32 STROBE items were re-verified independently against the current non-rendered drafts; every quote and line for the present/na items (1a, 1b, 2, 3, 4, 5, 6a, 7, 8, 9, 10, 11, 12a, 12b, 12c, 14a, 15, 16a, 16b, 16c, 17, 18, 19, 20, 21, 22) still matches, and guideline_checklist.py returns no quote-window block. The one absent item (12e) and five partial items (13a, 13b, 13c, 14b, 14c) are unchanged from round 2 and remain unresolved at this final round.

NEW-ANALYSIS: add a labelled sensitivity analysis for the adjusted model (item 12e), for example re-fitting with an alternative missing-data rule or excluding the complete-case drop, to show the main OR is robust.
NEW-ANALYSIS: tabulate exclusion counts per criterion (death, type 1/gestational/secondary diabetes, missing HbA1c, duplicate admission) from the screening log, if still available, for items 13a/13b.
NEW-ANALYSIS: compute missing-value counts for each Table 1 variable (age, sex, comorbidity, insulin use, length of stay), for item 14b.
NEW-ANALYSIS: compute a summary follow-up statistic (median follow-up time or total person-time before censoring) for item 14c.

GAPS      None of the 32 STROBE items could not be checked; all were located in the non-rendered drafts under 06_writing/manuscript/. Item 6b (matching) was scored na because this is an unmatched single-cohort design. Item 12d (loss to follow-up handling) was scored na because the design uses passive administrative follow-up via the hospital HIS rather than active prospective follow-up.
CONFLICTS Whether to invest in reconstructing exclusion-stage counts (13a/13b) when the original screening log may no longer separate reasons is an author decision, not a reporting defect per se. Whether to add a formal sensitivity analysis (12e) given the already-small effective sample and multiple exploratory secondary analyses already reported is also for the author to weigh against further multiplicity.
drafts-digest: manuscript f242ce1e24d735a5c8891b68fa491e4872f7f0c7260670d9e3285767c80aa340
```scores
{"deliverable": "manuscript", "guideline": 1}
```
