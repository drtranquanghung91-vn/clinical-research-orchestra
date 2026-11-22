STATUS: PASS

FINDINGS
| code | location (file:line) | fix |
|---|---|---|

No findings. Fresh full structural/claim-scope/limitations pass on all nine draft files
(`06_writing/review/00-title.md` through `07-other-information.md`, plus `sof.md`), with focused re-check of the
trimmed `01-abstract.md` (246/250 words, `lint_prose.py --count-words`) against `04-results.md`, `05-discussion.md`
and `06-conclusion.md`.

Structure: order still matches `manuscript.md` IMRaD skeleton plus the PRISMA additions in
`roles/review-systematic.md` (title, abstract, introduction with one objective, methods following PRISMA 2020
items, results with flow/characteristics/RoB/synthesis/publication-bias/GRADE, discussion in the six-part order
of `roles/discussion.md`, one-paragraph conclusion with its `<!-- results: R-A1-001, R-A1-005, R-A3-001..005 -->`
comment one-to-one with the single PICO objective in `03_protocol/sr-protocol.md` §2.2, declarations in
`07-other-information.md`). The abstract edit touched only `01-abstract.md`; no section was added, removed or
reordered.

Abstract-trim check (the point of this pass): the two added sentences and the trims are faithful to the full
text, nothing lost or overstated.
- Added search-source sentence ("Nguồn tìm kiếm duy nhất: một tệp xuất mô phỏng ('Simulated database'), chạy một
  lần.") matches `03-methods.md` §"Nguồn thông tin và chiến lược tìm kiếm" (single source, run once, date in
  `search-log.csv`) — no new claim, correctly scoped.
- Added limitations clause ("Hạn chế: ít thử nghiệm, nguồn tìm kiếm duy nhất, không đánh giá được sai lệch công
  bố.") reproduces three of the limitations stated with direction in `05-discussion.md` "Hạn chế" (small k,
  single-source search, Egger/funnel not run below k≥10 threshold) — an accurate, proportionate compression, not
  a new or stronger claim; the fictional-evidence caveat (the discussion's lead limitation) is carried separately
  in the preceding sentence of the Kết luận paragraph of the abstract.
- All six abstract placeholders (`R-A0-010`, `R-A1-001.n/.full`, `R-A1-003.value`, `R-A1-005.ci`, `R-A2-001.p`)
  are the same ledger ids used in `04-results.md`; none invented, none dropped that would change the magnitude or
  direction of the headline estimate.
- Trimmed Kết quả sentence keeps the pooled RR, I², prediction interval crossing the null, sensitivity
  instability and the significant RoB-subgroup difference — the same five facts that anchor
  `05-discussion.md` "Kết quả chính"/"So sánh" and `06-conclusion.md`; dropping τ² from the abstract (kept in the
  methods promise and in `sof.md`/`04-results.md`) is a size cut, not a scope change.
- Kết luận wording ("có thể làm giảm … mức chắc chắn thấp") is unchanged in substance and still matches GRADE
  "Thấp" (`sof.md`) and the rubric's "low → may" rule; registration and funding lines are unchanged.

Claim scope: certainty is GRADE "Thấp" (`sof.md`) and every claim of effect in the abstract, discussion and
conclusion is hedged with "có thể" (may); no causal verb, no generalisation beyond the five simulated
populations, no claim stronger than the evidence table.

Limitations (`05-discussion.md`, "Hạn chế"): all five mandatory elements (selection/publication bias,
confounding, information bias, missing data, generalisability) are present, each with a stated direction, as in
the prior round; unchanged by this edit cycle, which touched only the abstract.

GAPS
`01_question/question.md` and `02_evidence/evidence-table.md` do not exist in this project (systematic-review
layout uses `03_protocol/sr-protocol.md` §2.2 for the PICO objective and `06_writing/review/sof.md` for the GRADE
certainty instead); both were read in their place.

CONFLICTS
None.

NEW-ANALYSIS: none
drafts-digest: review f97145f453e6a4d170cab9c7038c97c7c27a490bbe6b61ade01123dd564914d0
```scores
{"deliverable": "review", "structure": 2, "claim_scope": 2, "limitations": 2}
```
