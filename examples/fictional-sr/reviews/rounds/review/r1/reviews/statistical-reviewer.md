STATUS: FINDINGS

| code | location (file:line) | fix |
|---|---|---|
| S-HET | 06_writing/review/04-results.md:57-60 (and sof.md footnote; abstract line 16-17) | The A2 subgroup pool for `rob_overall = low` (R-A2-011, k=3) reports only τ² and I², no 95% prediction interval, although `03_protocol/sr-protocol.md` §3.8 requires the PI "khi số nghiên cứu gộp k ≥ 3" without limiting the rule to the primary pool (A1). Either rerun `meta.py` to add the PI for this subgroup, or add a `DEVIATION A2:` line in `decisions.md` narrowing §3.8 to A1 only, then update the text. |

GAPS      none — `worklog.py digest`, `analysis_plan.py register` and `analysis_plan.py check` (on 01-abstract.md, 04-results.md, sof.md, 05-discussion.md, 06-conclusion.md) all ran to completion (0 block, 0 warn).

CONFLICTS §3.8 of sr-protocol.md does not state whether the k≥3 prediction-interval rule applies only to the primary pooled estimate (A1) or to every pooled subgroup estimate (A2 low-RoB arm, k=3). Only the author can narrow the rule (via a dated `DEVIATION` line) or choose to compute the subgroup PI.

NEW-ANALYSIS: re-run meta.py for the A2 rob_overall=low subgroup (k=3) to add the 95% prediction interval that sr-protocol.md §3.8 appears to require, feeding 04-results.md:57, sof.md and the abstract — contingent on resolving the CONFLICTS entry above.
drafts-digest: review f97145f453e6a4d170cab9c7038c97c7c27a490bbe6b61ade01123dd564914d0
```scores
{"deliverable": "review", "statistics": 1}
```
