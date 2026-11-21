# Choosing the study design

Methods content by Amelia Le (co-author), adapted for clinical-research-orchestra. Source:
`protocol-design-vi` v3 (20 Nov 2026), `reference/design-selection.md`. Numbers marked **default** are
defaults the author may override (`${CLAUDE_PLUGIN_ROOT}/references/judgement-defaults.md`), not standards.

Order of work: type of question → best design in theory (step 1) → adjust for constraints such as
ethics, time, disease frequency and resources (step 2) → write the full design name (step 3).

## Step 1 – Best design for each type of question

| Type of question | Best design | Acceptable design under constraints |
|---|---|---|
| Prevalence, characteristics | Descriptive cross-sectional, probability sampling | Cross-sectional with consecutive sampling in hospital (state the limit on representativeness) |
| Incidence, natural history | Prospective cohort | Retrospective cohort from records or follow-up registers |
| Associated factors (common exposure, common outcome) | Cohort | Analytic cross-sectional (say "associated with" only) |
| Risk factors when the outcome is rare or the induction period long | Case-control (controls from the same source population) | Hospital case-control, matched on age and sex |
| Rare exposure | Cohort selected by exposure | Retrospective cohort from a registry |
| Comparing two regimens **both already used in practice**, chosen by the treating doctor, not allocated by the researcher | Pragmatic RCT (if permitted) | **Cohort** (prospective or retrospective) comparing treatments, written in the target trial emulation frame; main analysis adjusted (propensity score IPTW or matching, or multivariable regression). This is an **observational** study; never call it "interventional" |
| Effect of a behavioural or lifestyle intervention added to standard care | Individually randomised RCT (low contamination risk) or cluster RCT (high contamination risk) | Non-randomised controlled intervention between sites; register as "Phase: Not Applicable" |
| Effect of an intervention | RCT | Non-randomised controlled intervention; interrupted time series; before–after (weakest); retrospective cohort comparing two regimens with adjustment or propensity score |
| Non-inferiority or equivalence | Non-inferiority or equivalence RCT | Another design is rarely acceptable |
| Intervention at organisation level (ward, health station, school) | Cluster RCT, stepped-wedge | Cluster-level controlled intervention |
| Diagnostic accuracy | Cross-sectional, consecutive suspected patients, every patient gets both the index test and the reference standard | Diagnostic case-control (overestimates accuracy; state the limit) |
| Prognosis, prediction model | Prospective cohort | Retrospective cohort; needs external validation or bootstrap |
| Developing or validating an AI model (images, video, signals, records) | Consecutive multicentre data; split by patient and by centre **before** training; external validation at a separate centre or period; reference labels by **default** at least 2 independent raters | Single centre with a temporal split; k-fold by patient (state the limit: optimistic estimate). This is an accuracy or prediction study and does **not** prove clinical benefit (that needs a later IDEAL stage or an RCT). Report with TRIPOD+AI, STARD-AI or CLAIM |
| Reliability or validity of a measurement tool | Validation study (forward–back translation, test–retest, CFA) | — |
| Experiences, barriers | Qualitative (in-depth interviews, focus groups) | Mixed methods |
| Behavioural or lifestyle factors (diet, physical activity) and a **common** disease (**default** ≥ 10%) | Cohort, or analytic cross-sectional | Case-control only if exposure was measured **before diagnosis** (existing records) or cases are newly diagnosed; otherwise **reverse causation** (patients change lifestyle after learning the diagnosis) |

**Observational or interventional?** Ask: *who decides what each participant receives?* If the
researcher decides (by protocol, randomised or not), it is an interventional study. If the treating
doctor decides as in routine practice and the researcher only records, it is observational (cohort),
even when data are collected prospectively.

**Non-inferiority question when an RCT is not possible**: use a cohort comparing treatments, declare
the non-inferiority margin in advance and adjust the analysis; conclude only "no inferiority beyond
the margin was observed in observational data", and state residual confounding. Put this in the list
of items the user must confirm.

## Qualitative study: required content in the protocol (SRQR / COREQ)

1. Approach and why: qualitative description, reflexive thematic analysis, IPA or grounded theory.
2. Purposive sampling (maximum variation across the strata that matter), how participants are
   approached and who invites them.
3. Sample size: expected range plus a stopping rule (information power and saturation evidence; use
   `sample-size-sap`, qualitative section). **Default** range 12–20 interviews
   (`${CLAUDE_PLUGIN_ROOT}/references/judgement-defaults.md`).
4. Semi-structured guide built on a theoretical frame (for example COM-B or TDF for behaviour change);
   pilot it in **default** 1–2 interviews.
5. Language: interviews in Vietnamese, audio-recorded, transcribed verbatim; quotations translated into
   English with back-checking.
6. Analysis: who codes, partial independent double coding, software, how consensus is reached.
7. Reflexivity and the researcher's position: a doctor interviewing her own patients invites answers
   that please her; reduce this with an independent interviewer and interviews outside the clinic.
8. Trustworthiness: credibility, dependability, confirmability, transferability; never claim
   statistical representativeness.

## Step 2 – Adjusting for constraints

| Constraint | Consequence |
|---|---|
| Data collection period shorter than **default** 6 months | A prospective cohort is feasible only if the outcome occurs early (in hospital, 30 days); otherwise use a retrospective or cross-sectional design |
| Rare outcome (**default** < 5%) | Case-control, or a retrospective cohort on large data; a small prospective cohort will not have enough events |
| Randomisation not allowed (ethics, ward policy) | Non-randomised intervention with a concurrent control is better than before–after; state confounding by indication |
| Intervention is already standard practice | No placebo-controlled RCT; compare regimens or study implementation in practice |
| Graduation thesis for general medicine (BS đa khoa) or specialist level I (CK1) | Prefer cross-sectional, retrospective cohort or small before–after designs; an RCT is rarely feasible |
| Data exist only in medical records | Retrospective; check completeness of the key variables before deciding |

## Step 3 – Full design name (written in the protocol)

`{time direction} + {design type} + {features}`. Examples (Vietnamese form in brackets, for protocols
written in Vietnamese):
- "Analytic descriptive cross-sectional study" ("Nghiên cứu cắt ngang mô tả có phân tích")
- "Retrospective cohort study" ("Nghiên cứu cohort hồi cứu")
- "Randomised controlled clinical trial, single-blind, two parallel groups" ("Nghiên cứu can thiệp lâm
  sàng ngẫu nhiên có đối chứng, mù đơn, hai nhóm song song")
- "Uncontrolled intervention study, before–after comparison" ("Nghiên cứu can thiệp không đối chứng, so
  sánh trước–sau")
- "Case-control study, matched on age and sex, ratio 1:2" ("Nghiên cứu bệnh–chứng, bắt cặp theo tuổi và
  giới tỷ lệ 1:2")

"Prospective" is a time direction, not a design: "prospective" does not mean "cohort".

## Strength of causal inference (for the limitations section)

RCT > prospective cohort > retrospective cohort > case-control > analytic cross-sectional >
uncontrolled before–after > case series. A lower design is not worthless, but the discussion must use
matching language ("associated with", not "causes"). When discussing causation from observational data,
check the 9 Bradford Hill criteria: strength, consistency, specificity, temporality (required),
dose–response, biological plausibility, coherence, experiment, analogy.
