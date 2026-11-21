# Decisions and assumptions

Dated entries, newest last. Gate waivers use a line starting `WAIVE G<n>:` followed by the reason.

## 2026-11-21 — Research question confirmed (G1)

Confirmed by Example author:
1. Sampling timeframe: discharges 01/2021–12/2022, followed to 31/12/2023 (365-day follow-up for
   every patient in the cohort).
2. Primary exposure analysis: admission HbA1c in 3 groups (< 7% / 7–9% / > 9%); continuous HbA1c
   per 1% is a secondary analysis.
3. Assumption (simulated project, no real records to check): the HIS records admission date and
   primary ICD-10 diagnosis for every hospitalisation, sufficient to identify 1-year all-cause
   readmission. On real data this must be checked against a small sample of real records before
   the study runs.

Title chosen: "HbA1c lúc nhập viện và nguy cơ tái nhập viện trong 1 năm ở người bệnh đái tháo đường
type 2 xuất viện tại Bệnh viện Mô phỏng (2021–2023): một nghiên cứu đoàn hệ hồi cứu" (option 2 of 3
in `01_question/question.md`). `project.yaml` title updated to match (Vietnamese, matching
`language.output: vi`).

Gate G1 opened by the author directly (`gate.py open . G1 --by "Example author"`).

## 2026-11-21 — Literature search completed (pending G2)

Ran `literature-search` (reusing the research-question scoping search) + `critical-appraisal` on the
5 papers found. No OpenEvidence/Consensus/ClinicalTrials.gov MCP tools were available in this
session; only `search_lit.py` (PubMed/Europe PMC) was used — recorded as a limitation in
`02_evidence/search-strategy.md`, not as "no evidence exists". Main finding: no study measures
admission HbA1c and 1-year all-cause readmission in general T2DM inpatients (Gap 1, GRADE
preliminary = very low certainty from indirect evidence only) — confirms the thesis question targets
a real gap. 5 references added and VERIFIED: chakraborty2021, hu2026, robbins2021, li2026, cao2026.
## 2026-11-21 — Evidence approved; correction on what G2 means

Author (Example author) reviewed and approved the evidence stage (incl. the Vietnam caveat in Gap 2)
and the re-appraisal of hu2026/robbins2021 (via `/orchestra:appraise`, ROBINS-E set as the primary
tool, NOS kept as the abstract-level proxy; three-question verdict added to the top of each file).
`STATUS.md` row 2 (Evidence) set to `done`.

**Correction:** per `gate.py --help` (`G1 question · G2 protocol and SAP · G3 results locked · G4
release`), G2 is the **protocol + SAP** gate, not an evidence gate — there is no dedicated gate for
the Evidence stage. The earlier note in this file and the prior STATUS.md wording that said "open
gate G2" after the evidence stage was wrong and is corrected here: G2 only opens after
`protocol-design` + `sample-size-sap` are done and the author approves them.

## 2026-11-21 — Protocol design (assumptions, not yet confirmed by author)

Author gave site/period/volume/data-source/budget facts directly (no "cứ làm luôn" said, but all
needed inputs given together, so no further questions asked). Protocol decisions recorded, pending
author confirmation (see `03_protocol/protocol.md` Part C, 3 items):

1. **Index-admission rule**: a patient discharged more than once in 01/2021-12/2022 contributes only
   their *first* discharge in the period as the index admission (unit of analysis); later discharges
   in the same period are read as the readmission outcome, not as separate analysis rows. Reason:
   avoids non-independent observations without a mixed-effects model the budget cannot support.
2. **Mediator classification**: in-hospital insulin use and length of stay are classified as
   measured after/concurrent with the HbA1c exposure window (24-48h) and therefore treated as
   possible mediators, NOT adjusted in the primary multivariable model (available only as
   descriptive/secondary variables). Reason: adjusting for a mediator would remove part of the real
   effect of HbA1c on readmission (bias-confounding.md).
3. **No specific T2DM diagnostic-criteria citation**: the protocol uses the physician-assigned
   ICD-10 diagnosis (operational definition already locked in `01_question/question.md`) rather than
   citing a specific diagnostic guideline (e.g. ADA §2), because no such reference is VERIFIED in
   this project's ledger yet (`02_evidence/guidelines.md` only verified ADA §16, hospital care).
   Flagged in protocol.md as needing a targeted `guideline-check` re-run if the committee requires a
   cited diagnostic standard.
4. **NLR/SII/SIRI as exploratory-only**: feasible without new tests (routine CBC differential) but
   not included in the primary confounder model until the author checks the real missing-data rate
   against a threshold (confirm item #1 in protocol.md).

Gate G2 not opened yet — protocol.md and variables.md are drafts awaiting author review; `sap.md` and
`sample-size.md` (from `sample-size-sap`) are still needed before G2 can open.

## 2026-11-21 — Protocol confirm items resolved by the author

1. **NLR/SII/SIRI missing-data threshold**: > 20% of records missing the differential WBC count →
   drop NLR/SII/SIRI entirely; ≤ 20% → exploratory/secondary analysis only, not the primary model.
2. **Mortality ascertainment**: HIS only captures in-hospital death, not out-of-hospital death. The
   "1-year mortality" secondary outcome is therefore "in-hospital death within 365 days" only, not
   true all-cause mortality. Fine-Gray (death as competing risk) is a sensitivity analysis only; the
   main time-to-first-readmission analysis uses plain Cox regression, treating unobserved
   out-of-hospital deaths as censored — stated as a limitation (possible non-informative-censoring
   violation if death is related to HbA1c).
3. **Ethics approval path**: submit to Bệnh viện Mô phỏng's own biomedical research ethics committee;
   request waiver of individual informed consent (retrospective, de-identified data, ~1,200 patients
   already discharged) — final decision rests with that committee, not pre-decided here.

`03_protocol/protocol.md` and `03_protocol/variables.md` updated accordingly.

## 2026-11-21 — Sample size / SAP (ASSUMPTION parameters, per author's explicit "làm luôn" instruction)

Author said explicitly: "Tham số nào không có nguồn thì ghi GIẢ ĐỊNH và làm luôn, không cần hỏi lại."
Ran `sample-size-sap` without further questions. Two parameters have no VERIFIED source in this
project (Gap 1 — no study measures 1-year readmission or a direct HbA1c effect at 1 year) and are
recorded as **ASSUMPTION**, not fabricated citations:
1. 1-year all-cause readmission rate in the HbA1c <7% reference group = **20% (ASSUMPTION)**.
2. Expected OR, HbA1c >9% vs <7% at 1 year = **1.5 (ASSUMPTION)** — chosen as a DELTA2-style cautious
   value, deliberately lower than the ~1.75-2.0 a naive log-linear extrapolation of hu2026's aOR 1.15
   per 1% (30-day outcome) would give across the ~4-5 percentage-point HbA1c gap between groups.

Sample size result: n required = 1,070 total (535 per extreme HbA1c group) via two-proportions
(conservative proxy for the adjusted model, per test-selection.md); EPV rule (6 model parameters)
needs only 300-600 total. Available pool ~1,200 before exclusions. **Risk flagged, not resolved**:
whether the <7% and >9% groups each reach 535 depends on the real HbA1c distribution, which is
unknown at planning stage — the study may be underpowered for the 3-group comparison even though it
is comfortably sized for the regression model's stability (EPV) and for Objective 1 (descriptive).
This is the riskiest assumption carried into `03_protocol/sample-size.md` §10 for the author to check
against a small real-chart sample before finalizing.

Gate G2 NOT opened by the assistant (per this skill's own hand-off rule: only the author opens it,
after approving protocol.md + sample-size.md + sap.md together).

## 2026-11-21 — Protocol + SAP approved; gate G2 opened

Author (Example author) approved `03_protocol/protocol.md`, `03_protocol/sample-size.md` and
`03_protocol/sap.md` together, and explicitly accepted the power risk flagged in `sample-size.md`
§4/§10 (required n = 1,070 for the HbA1c <7% vs >9% comparison vs ~1,200 available before
exclusions; actual power depends on the real HbA1c group distribution, unknown at planning stage).
Author opened gate G2 themselves: `gate.py open . G2 --by "Example author"`. `STATUS.md` row 3 set
to `done`.
