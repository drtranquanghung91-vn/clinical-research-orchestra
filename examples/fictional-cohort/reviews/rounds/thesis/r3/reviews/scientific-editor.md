STATUS: FINDINGS

Round-3 (final-round) re-verification. Diffed every drafted file in `06_writing/thesis/` against the
round-2 snapshot (`reviews/rounds/thesis/r2/`): the only change anywhere is in `ch4-discussion.md`
§4.8, single-site limitation item — the causal-wording regex fix reworded "sai lệch này làm giảm...
và có thể kéo OR về gần 1" / "sai lệch này có thể làm OR quan sát được thấp hơn" to a non-causal
"tỷ lệ tái nhập viện quan sát được ... và OR có thể gần 1 hơn giá trị thật" / "OR quan sát được có thể
thấp hơn giá trị thật theo chiều khác". Content unchanged: both directions of bias are still named,
still correctly hedged, still ends "Không thể phân biệt hai khả năng này với dữ liệu hiện có." No
scope or claim change — resolved as described.

Re-checked both round-2 items directly: §4.3 "Cơ chế có thể" still non-causal ("có thể liên quan với"),
§4.8 residual-confounding, HbA1c-missingness and single-site items all still state a bidirectional
direction and "không thể xác định chiều nào chiếm ưu thế" / "không thể phân biệt". Kết luận
(`05-ket-luan.md`) still one-to-one with the 2 objectives in `01_question/question.md`, each point
carrying its `<!-- results: R-… -->` comment and no causal/trend verb. No other file changed since
round 2, so no new W-STRUCT/W-ARG/W-OBJ/W-SCOPE/W-LIMIT finding elsewhere.

The two carried-over `ch3-results.md` items (reused/frozen chapter, per `decisions.md`
2026-11-22 "Thesis outline confirmed...") are confirmed unchanged at lines 42 and 113 and are kept in
the table below only as a record, per instruction that they will not be fixed this round.

FINDINGS
| code | location (file:line) | fix |
|---|---|---|
| W-SCOPE | ch3-results.md:42 | Drop "tăng dần" (implies a monotonic trend); state only the two reported group values and that the 3 CIs overlap widely, without a trend claim. |
| W-SCOPE | ch3-results.md:113 | Drop "có xu hướng ngắn hơn" (implies an untested trend across groups); report the two adjusted HRs and that both CIs include 1, without a directional-trend phrase. |

GAPS none — all mandatory thesis files, the role briefs, question.md, project.yaml and the evidence
table were read; no file was unreadable.
CONFLICTS none newly raised this round. The two findings above are already recorded in `decisions.md`
(2026-11-22) as author-owned, left unfixed on `ch3-results.md` because it is a reused/frozen chapter;
this is the author's call, not an open question for this review.
drafts-digest: thesis eefc31e42500dbe9cf9594a32c21bbe771bc320b20a6124018556b0aa0834608
```scores
{"deliverable": "thesis", "structure": 2, "claim_scope": 1, "limitations": 2}
```
