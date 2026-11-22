STATUS: PASS

`consistency_audit.py .` exited 0 (0 block, 0 warn). This is round 3 (final); the manuscript
`drafts-digest` is unchanged from round 2, confirming the `.rendered.md` files are freshly and
correctly re-built from source.

Manual checks against the results ledger (`ledgers/results-ledger.json`) and design sources
(`03_protocol/protocol.md`, `03_protocol/sap.md`, `03_protocol/sample-size.md`, `01_question/question.md`,
`decisions.md`): every `{{R-…}}` placeholder across `00-title`, `01-abstract`, `03-methods`,
`04-results`, `05-discussion`, `06-conclusion` resolved correctly and matches the ledger (n=1070/1043,
22.1% overall readmission with 19.7–24.6% CI, OR 1.10/1.42 with matching CIs and p=0.641/0.097, AUC
0.588, EPV 39, secondary A2–A6 estimates). Sample size wording (1,070 required vs ~1,200 available) is
identical in protocol.md, sap.md, sample-size.md and 03-methods.md. Mortality/outcome naming ("tử vong
trong viện trong 1 năm") is consistent between sap.md, 03-methods.md and 04-results.md. Objective wording
in `question.md` Mục tiêu cụ thể 2 (4 adjustment covariates, insulin/length-of-stay as mediators) matches
protocol.md §2.7.2 and the manuscript methods/abstract — the prior 6-vs-4-covariate drift (logged in
decisions.md 2026-11-22) was already fixed and re-verified clean. Title page's word counts (247/3492)
and table/figure counts (3 tables, 2 figures) match the rendered body text and a prior round's independent
recount; the earlier stale "đúng ngay ở ngưỡng" (exactly at limit) claim on `00-title.rendered.md` from
round 2 is gone and the figure is correctly re-rendered as 3492 (8 words under the 3500 limit). Citation
content claims (hu2026, cao2026, robbins2021, li2026, chakraborty2021) match their stored abstracts per
the citation-verifier's independent pass, with the same digest.

GAPS Country attribution for hu2026 ("tại Trung Quốc") and robbins2021 ("tại Anh") cannot be
confirmed from the stored ledger abstracts (no country field) — carried over as a citation-verifier gap,
not a consistency defect. STROBE completeness items (exclusion-stage counts, per-variable missing
counts, sensitivity analysis) are reporting-guideline gaps already tracked in
`reviews/reporting-guideline-checker.md`, not internal contradictions.
CONFLICTS None found.

drafts-digest: manuscript f242ce1e24d735a5c8891b68fa491e4872f7f0c7260670d9e3285767c80aa340
```scores
{"deliverable": "manuscript", "consistency": 2}
```
