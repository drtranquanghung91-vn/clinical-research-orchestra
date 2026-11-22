STATUS: FINDINGS

Round 3 (final round, re-run). Same 6 cited keys ([@hu2026], [@cao2026], [@li2026], [@robbins2021],
[@chakraborty2021], [@american2026]) across `00-dat-van-de.md`, `ch1-literature-review.md` and
`ch4-discussion.md` (the only drafts with `[@id]` citations) still exist in `ledgers/references.json`,
are not retracted, and carry `verified_by: "verify_refs.py 2026-11-21 VERIFIED"` with a stored
abstract. No E-REF findings. Diffed every draft against the round-2 snapshot
(`reviews/rounds/thesis/r2/`): the only change since my last report is a non-causal reword in
`ch4-discussion.md`'s limitations section (§4.x bias-direction wording), which does not touch any
`[@id]` marker or the sentence around one. `ch1-literature-review.md` is byte-identical to round 2
(frozen/reused chapter), so the contradiction below is unchanged and reported one final time.

FINDINGS
| code | location (file:line) | fix |
|---|---|---|
| C-SUPPORT | 06_writing/thesis/ch1-literature-review.md:71-72 | Unchanged since round 1/2. The abstract of [@chakraborty2021] reports "the reduction in hospital LOS ranged from 0.5 to 0.8 of a day" and "there were no significant changes in hospital readmission rates" — a quantitative (if null) finding on readmission. The sentence "không cung cấp bằng chứng định lượng" is contradicted by this. Reword to "không báo cáo số liệu gộp cho riêng kết cục tái nhập viện" or similar, closer to what the abstract supports. |

GAPS
- Same as prior rounds: "tại Trung Quốc"/"tại Anh" country attributions (hu2026, robbins2021) and
  whether hu2026's HbA1c was measured specifically "lúc nhập viện" are not stated in the stored
  abstracts; cannot confirm/refute from the ledger alone. Does not change direction, population or
  strength.

CONFLICTS
- `ch1-literature-review.md:71-72` (chakraborty2021 contradiction) is recorded in `decisions.md`
  (2026-11-22, "Thesis drafting round 1") as a reused-chapter finding left for the author to resolve,
  since this skill may not rewrite that chapter. This is the final revise-loop round; the finding is
  confirmed still present and unresolved. Listed above as a block finding because the contradiction
  remains in the thesis text, not because the author's choice to defer it was wrong — the decision to
  defer is the author's to make, not this reviewer's.

drafts-digest: thesis eefc31e42500dbe9cf9594a32c21bbe771bc320b20a6124018556b0aa0834608
```scores
{"deliverable": "thesis", "citations": 0}
```
