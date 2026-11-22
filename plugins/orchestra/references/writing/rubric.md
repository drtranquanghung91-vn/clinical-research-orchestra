# Writing rubric (revise loop)

Eight criteria, each scored 0, 1 or 2 (maximum 16). Agents score the judged criteria; `worklog.py` measures
the formula criteria and its value wins over anything a reviewer writes.

## 1. Criteria and anchors

| Criterion | Source | 2 | 1 | 0 |
|---|---|---|---|---|
| `citations` | citation-verifier | Every `[@id]` is VERIFIED (or MANUAL with `seen_in`) and every citing sentence is supported by the stored abstract. | All verified, but 1-2 sentences claim more than the source (scope, direction, certainty) or cannot be checked (no abstract). | Any missing, unverified or retracted citation, a sentence the source contradicts, or 3 or more overstated sentences. |
| `statistics` | statistical-reviewer | Methods match the SAP register and `decisions.md`; every effect has its CI; no p-value or trend overclaim; multiplicity addressed; post-hoc work and deviations labelled. | Minor slips: one effect without CI, "no difference" read from p > 0.05, multiplicity not discussed. | An `analysis_plan.py` block, a causal or trend claim without support, a number not in the ledger, or methods that contradict the SAP. |
| `guideline` | formula, from `reviews/guideline-checklist-<d>.json` | No absent item. | 3 or fewer absent. | More than 3 absent. Items missing from the checklist count as absent. |
| `structure` | scientific-editor | Sections and their order as in `vn-thesis.md` / `manuscript.md` and the role briefs; one point per paragraph; the text answers each objective. | One section out of order, repetitive, or missing a required element. | A required section is missing or an objective is not answered. |
| `claim_scope` | scientific-editor | Every claim stays within the design (association for observational designs), the studied population and the evidence table's certainty. | One or two overreaching sentences. | A causal claim from an observational design, a generalisation beyond the population, or a conclusion with no ledger support. |
| `limitations` | scientific-editor | A limitations part names selection, information and confounding bias, missing data and generalisability, each with its likely direction. | Present but generic. | Absent. |
| `consistency` | formula (`consistency_audit.py`) | No E-CONS finding. | Warnings only. | Any block. |
| `prose` | formula (`lint_prose.py`) | No P00 block and at most 1 hit per 200 words. | No P00 block. | A P00 block. |

The guideline score is never a summed compliance percentage. It counts absent items only; the checklist
carries one status per item with its reason.

## 2. Report tail every reviewer writes

At the end of each report:

1. `NEW-ANALYSIS: <what and why>` lines, only when an analysis is missing. They go to
   `out/author-decisions.md`, never into the text.
2. The line `drafts-digest: <deliverable> <sha256>`, copied from `worklog.py digest . <deliverable>`.
3. A fenced block whose info string is `scores`, holding
   `{"deliverable": "<d>", "<criterion>": <0|1|2>, ...}` with the criteria of that agent.

Reviewer to criteria: citation-verifier `citations`; statistical-reviewer `statistics`;
reporting-guideline-checker `guideline`; scientific-editor `structure`, `claim_scope`, `limitations`;
consistency-auditor `consistency`. A stale digest or a missing block is refused (exit 2).

## 3. Decision rules

- Higher total than the kept round: KEEP.
- Lower total: REVERT, and the loop stops.
- Equal total with a lost criterion: REVERT, and the loop stops.
- Equal total with no loss: STOP.
- A total of 16, or round 3: STOP.
- At most 3 rounds. Formula criteria are measured by `worklog.py`, not by the reviewers.

## 4. Snapshots and the log

`reviews/rounds/<d>/r<N>/` holds the draft files and `order.txt`; `r<N>/reviews/` holds the report files and
`guideline-checklist.json` (the copy of that round's `reviews/guideline-checklist-<d>.json`). `worklog.py revert` restores the kept round exactly and deletes tracked files
that are absent from it (they stay in the later round's snapshot).

`reviews/worklog.json`: `{"rounds": [{"deliverable", "round", "at", "scores", "total", "max": 16, "decision",
"kept", "compared_with", "compared_total", "drafts_digest", "files_changed", "requests": [{"agent", "text"}],
"notes"}], "events": [...], "decisions_sha256": "..."}`.
