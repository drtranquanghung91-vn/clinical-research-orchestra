# Bias and confounding by design

Methods content by Amelia Le (co-author), adapted for clinical-research-orchestra. Source:
`protocol-design-vi` v3 (20 Nov 2026), `reference/bias-confounding.md`. Numbers marked **default** are
defaults the author may override (`${CLAUDE_PLUGIN_ROOT}/references/judgement-defaults.md`), not standards.

List the biases **for the chosen design**, never a generic list. For each source of bias give the
control at the design stage and at the analysis stage.

## Common biases by design

| Design | Main biases | Control at design | Control at analysis |
|---|---|---|---|
| Cross-sectional | Selection (hospital sample ≠ community; non-responders); information (recall, interviewer); time order cannot be established | Consecutive or probability sampling; standardised tools; interviewer training; pilot-tested questionnaire | Multivariable regression; report the non-response rate; compare participants with non-participants |
| Case-control | **Reverse causation** when the exposure is a behaviour that can change after diagnosis (diet, activity, medicines); control selection; recall bias; interviewer aware of disease status | Controls from the same source population; matching; exposure data from records made before diagnosis; blind the interviewer | Conditional logistic regression (if matched); multivariable logistic regression |
| Prospective cohort | Loss to follow-up; outcome assessed with knowledge of exposure; confounding; **detection bias** (a group that stays longer in hospital or returns more often is examined more and so has more outcomes detected) | Retention procedures; blind the outcome assessor; measure confounders at baseline | Multivariable Cox or Poisson; sensitivity analysis for loss to follow-up; multiple imputation |
| Retrospective cohort | Missing or inconsistent data; confounding by indication; immortal time bias | Clear abstraction criteria; one shared definition of time zero; two people abstract part of the records independently | Propensity score; landmark analysis; sensitivity analysis |
| Uncontrolled before–after | Regression to the mean; secular trend; Hawthorne; season | Several measurements before the intervention; a concurrent control group if possible | Interrupted time series (segmented regression) |
| Non-randomised intervention | Confounding by indication; selection bias | Objective group-assignment criteria set in advance; record the reason for each assignment | Multivariable adjustment; propensity score |
| AI model development or validation | **Data leakage** (images or frames from the same patient in both the training and the validation set); overfitting to the validation set; spectrum bias (only "clean" cases chosen); inconsistent reference labels; device or centre differences (dataset shift) | Split by patient and centre before training; lock the validation set and evaluate it once under a SAP written in advance; consecutive cases, report excluded cases; label dictionary + κ + adjudication; external validation | Cluster-adjusted CI (bootstrap by patient); report by subgroup (centre, device, disease severity); calibration for prediction models |
| Behavioural, lifestyle or educational intervention RCT | **Contamination** (the control group learns the intervention: same doctor, same waiting room); co-intervention from background treatment; participants cannot be blinded; waning effect over time (adherence falls) | Cluster randomisation (clinic, doctor) when contamination risk is high, or separate staff and appointment times; one shared background-treatment protocol; blinded outcome assessor and objective outcomes; measure adherence (sessions attended, diaries, devices) and follow up long enough (**default** ≥ 12 months to speak of maintenance) | ITT; analysis by adherence only as secondary (CACE); clusters → mixed model or GEE and sample size multiplied by the design effect |
| RCT | Allocation not concealed; no blinding; protocol violations; loss to follow-up | Randomisation by a third party or sealed numbered envelopes; blind patient, treating clinician and assessor | ITT as main analysis; per-protocol as sensitivity analysis |
| Diagnostic | Spectrum bias; verification bias (only test-positive patients get the reference standard); test read with knowledge of the reference result | Consecutive suspected patients; reference standard for every patient; blinded reading | Report by STARD; subgroup analysis by severity |

Other biases to consider (Nguyễn Văn Tuấn 2018, chapters on study models and on interpreting results):
- **Survival (prevalent-user) bias**: selecting people who already have the disease or have used the
  drug for a long time misses those who died or stopped early → prefer incident cases and new users.
- **Ecological fallacy**: an association at group or area level cannot be applied to individuals.
- **Regression to the mean**: people selected for a high value (blood pressure, glucose, BMI) show a
  lower value on re-measurement even without intervention → concurrent control group, baseline measured
  twice.
- **Hawthorne effect**: people who are observed change behaviour → control group with the same amount of
  contact, objective outcome measures.
- **Confounding by indication**: doctors choose treatment by disease severity → RCT design, or
  adjustment or propensity score; no causal conclusion from crude comparisons.

Controlling detection bias: assess the outcome on a **fixed schedule counted from time zero**, the same
for every group (for example days 3, 7 and 30 after surgery, a phone call or visit after discharge),
by an assessor who does not know the group.

## Time zero and the exposure window (cohort comparing treatments)

1. **Time zero** = the moment a participant is eligible and could start any of the treatment options
   (for example the end of surgery). Outcome follow-up starts here for every group.
2. **Exposure** is defined within a short grace period set in advance (for example an antibiotic order
   within the first 24 hours after surgery). Never assign groups by what happens later (for example
   "received the full 3 days"): this causes immortal time bias, because only people without an early
   event can "complete" the course.
3. Variables that occur **before** the exposure is defined (patient characteristics, intra-operative
   factors) are candidate confounders. Variables that occur **after** the exposure and lie on the
   causal path are mediators: do not adjust for them.
4. Write in the target trial emulation frame: eligibility, treatment strategies, assignment, time zero,
   outcome, estimand, analysis; for each item give "the ideal trial" and "how observational data
   emulate it".

## Classifying third variables (use a DAG)

| Type | Definition | Handling |
|---|---|---|
| Confounder | Associated with the exposure, a cause (or proxy of a cause) of the outcome, and **not** on the exposure → outcome path | Adjust |
| Mediator | Exposure → this variable → outcome | Do not adjust when estimating the total effect |
| Collider | Affected by both exposure and outcome | Do not adjust, and do not select the sample on it |
| Effect modifier | The effect of the exposure differs by level of this variable | Subgroup analysis or interaction term, declared in advance |

Draw a text DAG when there are **default** 3 or more variables.

## Text DAG (example)

```
Age ─────────────┬──────────────► Postoperative delirium
                 ▼                     ▲
Dexmedetomidine ───────────────────────┤
                 ▲                     │
EuroSCORE II ────┴─────────────────────┘
Dexmedetomidine ──► Ventilation time ──► Postoperative delirium   (mediator: do not adjust)
```

Confounders to adjust for: age, EuroSCORE II. Mediator: ventilation time.

## Rules for choosing confounders for the model

1. Take the list from the literature (with citations) plus clinical knowledge, declared **before** data
   collection.
2. Never select confounders by p < 0.05 in univariable analysis or by stepwise selection.
3. The number of variables in the model is limited by the number of events (**default** about 10 events
   per parameter) → with many confounders use a propensity score or fewer variables; the calculation
   belongs to `sample-size-sap` (events per variable for regression).
