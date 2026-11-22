STATUS: FINDINGS

Round 3 (final round), end-to-end re-check. `sap.md` register A0-A6 (A6 via `POST-HOC A6:` in
`decisions.md`) read again; `ch2-methods.md` still matches it exactly: model, covariates (tuổi, giới,
thời gian mắc ĐTĐ, bệnh đồng mắc), missing-data rule (≤5% complete-case, 2.5% actual), multiplicity
rule (exploratory secondaries/post-hoc, no correction, only A1 confirmatory), and both deviations
(Fine-Gray dropped; A6 age post-hoc) stated — no S-SAP.

`analysis_plan.py check . --text` on `ch3-results.md`, `ch4-discussion.md`, `05-ket-luan.md`,
`06-kien-nghi.md` -> 0 block, 0 warn (confirmed independently, matches the task's account). The
round-2 E-STAT warning on `ch4-discussion.md`'s §4.8 single-site/administrative-data sentence is gone:
the reworded lines (ch4-discussion.md:131-137) now state the ascertainment bias's two possible
directions on the observed rate ("có thể gần 1 hơn" / "có thể thấp hơn giá trị thật theo chiều khác")
with no "làm giảm" and no HbA1c-to-readmission causal verb — correctly a false-positive fix, not a
content change. `ch4-discussion.md`, `05-ket-luan.md`, `06-kien-nghi.md` were re-read in full: every
effect estimate carries its `.full`/`.ci`, A2-A6 stay labelled exploratory/post-hoc, no p-used-as-effect-
size or "no difference"-from-p>0.05 wording, and `project.yaml -> design: cohort` is never given a
causal verb (consistently "có liên quan với").

The one open item is unchanged and was not touched this round, as instructed: `ch3-results.md:42` and
`:113` still carry an ordered/dose-response claim ("tăng dần theo nhóm HbA1c", "có xu hướng ngắn hơn ở
nhóm HbA1c cao hơn") with no trend test registered in `sap.md` §16. `decisions.md`'s 2026-11-22 "Thesis
drafting round 1" entry records this as the author's final call on a reused/frozen chapter (mechanical-
only fixes permitted) — carried forward unchanged through rounds 1-3.

| code | location (file:line) | fix |
|---|---|---|
| S-TREND (warn) | ch3-results.md:42 | "tỷ lệ này tăng dần theo nhóm HbA1c" — ordered/dose-response wording with no trend test in the sap.md §16 register; author decision on record (decisions.md, 2026-11-22) to leave this reused chapter as-is for this final round |
| S-TREND (warn) | ch3-results.md:113 | "có xu hướng ngắn hơn ở nhóm HbA1c cao hơn" — same issue, same reused-chapter decision |

GAPS: `ch1-literature-review.md`, `00-dat-van-de.md`, `90-phu-luc.md` are not results-bearing per this
round's scope and were not checked for S-codes. `00-tom-tat.md` does not exist (not requested this
round, consistent with prior rounds).

CONFLICTS: whether `ch3-results.md:42`/`:113` should eventually be reworded to match Chapter 4's more
cautious language is the author's call; already decided in `decisions.md` to leave as-is for this
(final) round.

NEW-ANALYSIS: none

drafts-digest: thesis eefc31e42500dbe9cf9594a32c21bbe771bc320b20a6124018556b0aa0834608
```scores
{"deliverable": "thesis", "statistics": 0}
```
