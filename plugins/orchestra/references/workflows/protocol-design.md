# Protocol design: full workflow

Methods content by Amelia Le (co-author), adapted for clinical-research-orchestra. Source: her
`protocol-design-vi` v3 (20 Nov 2026) and its two change notes (18 Nov, 20 Nov). Where the v3 text and
the 18 Nov notes differ, v3 is followed. Thresholds are **defaults** the author may override, not
standards (`${CLAUDE_PLUGIN_ROOT}/references/judgement-defaults.md`); record an override in
`decisions.md`.

Design library: `${CLAUDE_PLUGIN_ROOT}/references/design/design-selection.md`,
`${CLAUDE_PLUGIN_ROOT}/references/design/bias-confounding.md`,
`${CLAUDE_PLUGIN_ROOT}/references/design/protocol-template.md`. Tool procedures and reference
verification: `${CLAUDE_PLUGIN_ROOT}/references/evidence-policy.md`.

## Core rule

The design comes from the question, not from habit ("our department always does cross-sectional").
Every methods decision (design, eligibility, variables, confounder control) must answer **"why this
choice, and what does it cost?"** Write the reason and the limitation into the protocol itself; that is
exactly where the committee will ask.

## Scope

This skill does **not** calculate sample size (use the `sample-size-sap` skill) and does not draft the
ethics file or the detailed CRF (the `ethics-and-crf` skill, phase P4). It builds the frame those steps
need: the variables table becomes the CRF and data dictionary; the hand-off block feeds the sample size.

## Inputs

- Read if present: `01_question/question.md` (question, objectives, hypotheses) and `02_evidence/*`
  (evidence table, evidence map, gaps, appraisals).
- No clear question, or objectives that contradict the design → run steps 1–4 of the
  `research-question` skill briefly first.
- No evidence review → still proceed, but the steps that need literature (outcome definitions,
  confounders) use quick lookups as in §Evidence lookups.
- Ask **once** for whatever is missing: site, data collection period, expected patients per month,
  whether intervention or randomisation is allowed, what retrospective data exist, budget and which
  tests can be done.
- If the user says not to ask ("cứ làm luôn", "just do it"): do not ask. Open the answer with an
  **Assumptions / Giả định** box listing every assumption made, put the riskiest one in the
  confirmation list (§Output, Part C), and record the box in `decisions.md`. This never opens a gate:
  `gate.py open` runs only after the author approves in chat (a gate is the author's act).

## Gate G1

Before drafting, run `python "${CLAUDE_PLUGIN_ROOT}/scripts/gate.py" check <project> G1`. Exit 0 = open
(or waived): continue. Exit 1 = closed: tell the user the question is not yet approved, list the
reasons the script prints, and stop; offer the `research-question` skill. Continue only if the author
waives G1 (a `WAIVE G1:` line in `decisions.md`, written only after the author agrees). Exit 2 = error:
report it. Without a project folder there is no gate; work in chat (§Output).

## Step 1 – Design on two axes

Follow `design/design-selection.md`: type of question → best design in theory → adjust for
constraints (ethics, time, disease frequency, resources). Present the chosen design, **one**
alternative, the reasons and the main limitation. Name the design in full on two axes: **time
direction** (retrospective / prospective / mixed) and **design type** (cross-sectional / cohort /
case-control / interventional …). "Prospective" does not mean "cohort". Decide observational versus
interventional by asking who decides what each participant receives.

## Step 2 – Diagnostic criteria with citations

Define the disease in the inclusion criteria by a specific, cited diagnostic standard (examples from
the source: ADA Standards of Care, KDIGO, DSM-5; the source names ADA 2026). Confirm the **current
version** with the `guideline-check` skill (output `02_evidence/guidelines.md`) or a lookup under
§Evidence lookups; never cite a guideline year, PMID or DOI from memory.

## Step 3 – Population, eligibility, sampling

- Target population → study population (place, time) → sample.
- **Inclusion criteria**: disease by the cited criteria (step 2), age, time point, consent.
- **Exclusion criteria**: people who *meet* the inclusion criteria but have features that would distort
  the result, cause harm, or make the outcome unmeasurable. Never restate inclusion criteria in the
  negative ("under 18 years").
- Stopping or withdrawal criteria (prospective and interventional studies).
- **Sampling method**: census (all) / consecutive / convenience / simple random / systematic /
  stratified / multistage cluster. Name the method actually used; "convenience" is never called
  "random". State what it means for representativeness.
- Representativeness is **critical only when the aim is to estimate a proportion for a defined
  population**. For analytic or causal aims, internal validity (standard measurement, confounder control)
  comes before representativeness, and generalisation rests on biology and replication in other
  populations (Nguyễn Văn Tuấn 2018, chapter on representativeness). Do not downgrade a good
  clinic-based analytic study for an "unrepresentative sample".
- When comparing strata (age, BMI), equal sample size per stratum is usually more efficient than
  allocation proportional to the population.
- Interventional: randomisation method (block, stratified), allocation concealment, who is blinded.

## Step 4 – Outcomes and the variables table

**Outcomes**: a table of primary and secondary outcomes with definition, measurement tool (is the scale
or questionnaire validated in Vietnamese? if not, a forward translation – back translation – pilot
procedure is needed), time of measurement, who measures, unit or categories. Define outcomes the way
studies on the same topic did, so results can be compared (ClinicalTrials.gov `analyze_endpoints` or
PubMed when needed).

**Variables table** (example in `design/protocol-template.md`), written to `03_protocol/variables.md`:
each variable has name, definition, type (continuous / binary / categorical / ordinal / time to event),
unit or values, collection method and **role** (outcome / exposure–intervention / confounder / effect
modifier / mediator / descriptive). Every specific objective must have variables that serve it; a
variable that serves no objective is dropped (extra variables lengthen the CRF and add missing data).
This table is the input for the CRF and data dictionary later (`ethics-and-crf`).

## Step 5 – Measurement and questionnaires

- Each key variable: **conceptual definition** → **operational definition** (how it is measured) →
  instrument, with the reliability and validity of the Vietnamese version; prefer standard measurement
  methods (measurement decides internal validity).
- Self-reported variables (diet, physical activity, adherence): state the risk of social desirability
  bias, recall bias and the Hawthorne effect and how it is reduced (independent interviewer, short
  recall window, an additional objective tool).
- Collect continuous variables in raw form (date of birth, not age group; weight, not "overweight
  yes/no").
- Self-written questionnaires (Tuấn 2018, chapter on questionnaire design): each item one dimension and
  simple; avoid leading, vague, threatening, double-barrelled, complex and negative items and long
  branching chains; Likert scales with a clear midpoint; pilot on **default** 10–20 people before use
  (`judgement-defaults.md`; common practice, not from Tuấn's text).

## Step 6 – Bias, confounding, reverse causation

Follow `design/bias-confounding.md`.
- List selection bias, information bias, confounding and loss to follow-up **for the chosen design**,
  not a generic list.
- Confounders: take factors related to both exposure and outcome from the evidence table or literature
  (cited). Classify: confounder to adjust / mediator (do not adjust) / collider (do not adjust). Draw a
  text DAG when there are **default** 3 or more variables.
- Each source of bias → its control at design (restriction, matching, randomisation, blinding,
  standardised tools, training) and at analysis (stratification, multivariable regression, propensity
  score).
- **Reverse causation**: a behavioural exposure (diet, activity) with a common outcome (**default**
  ≥ 10%, `judgement-defaults.md`) → prefer cohort or cross-sectional; case-control only if exposure was
  measured before diagnosis. Flag it explicitly when the user proposes such a case-control (test case:
  diet → PCOS).
- Causal discussion from observational data: check the Bradford Hill criteria
  (`design/design-selection.md`, last section).

**Study procedure**: a flow diagram of the steps (screening → consent → baseline → intervention or
follow-up → outcome measurement), with the collection schedule counted from the **same time zero** for
every group. Cohort comparing treatments: define time zero and the exposure window as in
`design/bias-confounding.md`. Retrospective: record source, ICD-10 codes used to filter (the ICD-10 MCP
holds the US ICD-10-CM; Vietnam uses WHO ICD-10, so check codes with the hospital planning department,
phòng Kế hoạch tổng hợp), and how incomplete records are handled.

## Step 6b – Drug or device intervention checklist (only when there is one)

Check before fixing the design; put anything missing into the confirmation list.
- **Regulatory**: does the drug have a marketing authorisation number in Vietnam; does the registered
  indication match the study use (for example a GLP-1 RA registered for type 2 diabetes but used for
  weight loss → off-label)? Off-label use or an unlicensed drug → a clinical drug-trial dossier under
  Ministry of Health rules, not only the institutional ethics committee. Never write a decision or
  circular number from memory: write `[unverified – user must check the original document / chưa xác
  minh – người dùng cần kiểm tra bản gốc]`.
- **Drug source and cost**: who supplies the drug; can it be blinded (is placebo or double-dummy
  available)? If not, blind the outcome assessor, the laboratory and the statistician.
- **Women of reproductive age**: pregnancy test at screening and at each visit; acceptable
  contraception (watch drug interactions with oral contraceptives, and hormonal contraceptives that may
  confound endocrine outcomes); washout period before pregnancy; procedure for an unplanned pregnancy.
- **Washout at enrolment**: prior medicines that affect the outcome (for example contraceptives,
  anti-androgens, metformin in an endocrine–metabolic study) → a predefined washout period in the
  exclusion criteria.
- **Biochemical or hormonal outcomes**: assay method (for example testosterone in women: LC-MS/MS or
  immunoassay), same laboratory and same lot, sampling time (hour, fasting, menstrual cycle phase),
  sample storage so baseline and end samples run in the same batch.
- **Dose escalation and safety**: escalation schedule, criteria for dose reduction or stopping,
  drug-class-specific adverse events to monitor, whether a DSMB is needed.

## Step 6c – Phase label and background therapy (every interventional trial)

- **Phase labels (I–IV) are only for drug or biologic development.** Behavioural, lifestyle,
  educational, surgical or care-process interventions are registered on ClinicalTrials.gov as
  "Phase: Not Applicable"; call them a "confirmatory RCT" or "pragmatic RCT", never "phase III". A
  licensed drug used within its indication in a strategy comparison is usually phase IV. If the user
  writes the wrong label, correct it and explain in one sentence.
- **Add-on trials on top of current treatment**: describe the background therapy and **one shared
  dose-adjustment protocol** for every arm (for example an insulin titration algorithm by fasting
  glucose), rescue (treatment-escalation) criteria, and record changes in background medication as a
  secondary outcome. Without a shared protocol, differences in dose adjustment between arms are a
  **co-intervention** that confounds the result.
- The outcome may be "compensated" by background therapy (for example doctors raising insulin in the
  control group so HbA1c converges): consider a composite or secondary outcome (insulin dose, rate of
  rescue) and a suitable estimand (treatment policy versus hypothetical, ICH E9(R1)).

## Step 7 – Intervention reporting, analysis direction, reporting guideline

- Behavioural or lifestyle interventions: describe with **TIDieR**; exercise with **CERT**. Observational
  studies with a health-equity aim: add **STROBE-Equity** (2025). Check the EQUATOR Network for the
  current version and the right extension.
- Choose the reporting guideline from the start: STROBE (observational), CONSORT (RCT), TREND
  (non-randomised intervention), STARD (diagnostic), TRIPOD (prediction model), SPIRIT (trial
  protocol), SRQR or COREQ (qualitative); TRIPOD+AI, STARD-AI or CLAIM for AI models.
- State the main analysis for each objective; the detailed SAP belongs to `sample-size-sap`
  (`03_protocol/sap.md`). The analysis plan is written before data collection and run with reproducible
  scripts (R, Stata), not Excel.
- Similar studies are appraised later with the `critical-appraisal` skill, for example ROBINS-I V2 for
  non-randomised interventions.

## Step 8 – Qualitative protocol essentials

A qualitative arm needs all 8 items in `design/design-selection.md` (approach, purposive sampling,
sample size with stopping rule, guide, language, analysis, reflexivity, trustworthiness). "In-depth
interviews, content analysis" alone is not a protocol. Qualitative sample size: information power and
saturation evidence, via `sample-size-sap`.

## Step 9 – SPIRIT 2025 and CONSORT 2025

Trial protocols follow SPIRIT 2025 (34 items); trial reports CONSORT 2025 (30 items). Both add items on
open science (registration, public protocol and SAP, data sharing), patient and public involvement,
harms, and description of the intervention and comparator. The template's SPIRIT column uses 2013
numbering; **the full SPIRIT 2013 → 2025 numbering map is unverified**, so say so in the protocol and
check against the 2025 checklist itself before submission (`design/protocol-template.md`). Never use
SPIRIT 2013 or CONSORT 2010 as the current standard.

## Step 10 – Dummy tables and the draft

Write the draft by `design/protocol-template.md` (Vietnamese frame mapped to SPIRIT), with **dummy
tables** for each objective (at least one per objective; numbers empty, statistic named) and the sample
size section left empty with the list of parameters to be calculated.

## Evidence lookups (when a design decision needs evidence)

Tool rules: `${CLAUDE_PLUGIN_ROOT}/references/evidence-policy.md`.
- Current diagnostic criteria or definitions → OpenEvidence, or PubMed `practice guideline[pt]`; for a
  versioned guideline use `guideline-check`.
- How similar studies defined outcomes, eligibility, follow-up time → ClinicalTrials.gov
  (`search_trials`, `analyze_endpoints`, or `search_lit.py trial <NCT>`), PubMed RCTs or cohorts on the
  same topic.
- Known confounders → Consensus, or PubMed "risk factors" for the outcome.
- Vietnamese-validated instruments → PubMed `{scale name} AND (Vietnam OR Vietnamese) AND (validation OR
  reliability)`.

Cite only papers whose PMID or DOI was verified in this session; every reference goes through
`search_lit.py add` and `verify_refs.py`.

## Output (in this order)

**Part A – Design decision** (short, for a quick author review):
1. **Design summary**: one paragraph (design, population, site, period, intervention or exposure,
   primary outcome).
2. **Why this design**, the alternative, the limitations.

**Part B – Draft Chapter 2 / protocol** by the Vietnamese frame in `design/protocol-template.md`. Each
table appears **once**, in its section: eligibility and sampling (2.1, 2.3), outcome table (2.5), study
procedure and flow diagram (2.6), bias and confounding table + DAG (2.7), dummy tables (Chapter 3). The
full variables table lives in `03_protocol/variables.md`; section 2.5 points to it rather than copying
it. Section 2.3.2 Sample size stays empty with the note "calculated at the next step".

**Part C – Closing**:
3. **Sample-size hand-off**: primary outcome, variable type, design, main comparison, expected number of
   confounders to adjust for, parameters still to find → `sample-size-sap`.
4. **Items for the user to confirm**: at most 3 main items (**default**); each may hold a few related
   points.
5. **References**: cite as `[@id]` from `ledgers/references.json` (`evidence-policy.md` §Citing
   sources), check with `verify_refs.py <project> --cite 03_protocol/protocol.md`; the numbered Vancouver
   list comes only from `cite_render.py` (a `.numbered.md` view, or the assembled thesis in one pass).
   NCT numbers and Ministry of Health documents enter the ledger as in `evidence-policy.md`.

**Where it goes**: in a project, write `03_protocol/protocol.md` and `03_protocol/variables.md` in
`project.yaml → language.output` (chat follows the user) and set `STATUS.md` row 3 to `doing`. Without a
project folder, answer in chat and ask in one line at the end whether to save it (saving needs a project:
`research-project-setup`). When the draft is stable, offer a Word file with the `docx` skill if it is
installed; a built-in Markdown → Word exporter is planned for a later release.

## Hand-off and gate G2

Next: use the Skill tool with `sample-size-sap`, which fills section 2.3.2 and writes
`03_protocol/sample-size.md` and `03_protocol/sap.md`. Gate G2 (protocol and SAP) is opened by the
author after both are approved: `python "${CLAUDE_PLUGIN_ROOT}/scripts/gate.py" open <project> G2 --by
"<author>"`; then set `STATUS.md` row 3 to `done`.

## Common errors

| Error | Fix |
|---|---|
| Calling it an "intervention study" when the treating doctor chooses the regimen and the researcher only records | It is a cohort comparing treatments (observational); see `design-selection.md` |
| Assigning groups by what happens after time zero ("received the full 3 days") | Assign by the prescription order within a short predefined grace period; avoids immortal time bias |
| The group that stays longer in hospital is examined for the outcome more often | Fixed outcome-assessment schedule from time zero, the same for every group |
| "Prospective study" with no design named | Write it in full: "prospective cohort", "prospective cross-sectional", "prospective controlled intervention" |
| Exclusion criteria are the negation of inclusion criteria | Exclusion = people who meet inclusion but have a factor that distorts results or causes harm |
| Outcome built into the inclusion criteria (selecting patients who already have the complication, then looking for "risk" factors) | Select by exposure or the whole population; selecting by outcome makes it a case-control study |
| Case-control with controls from a different source population | Controls from the same source population, same period |
| "Confounders" list includes mediators (adjusting removes the real effect) | Separate confounder, mediator and collider with a DAG |
| Confounders chosen by p < 0.05 in univariable analysis | Choose from literature + DAG, declared in advance in the protocol |
| Convenience sample described as "random" | Use the right name; acknowledge the limit on representativeness |
| Retrospective, but key outcomes or confounders are not in the medical records | Check **default** 10–20 sample records first; if missing, change the design or the variable |
| Foreign scale used in a home-made translation | Use a validated version (cited) or add forward–back translation and piloting |
| Uncontrolled before–after intervention concluding "effective" | State the limits (regression to the mean, secular trend); consider a concurrent control or interrupted time series |
| Variable that serves no objective | Drop it; extra variables lengthen the CRF and increase missing data |
| No dummy tables | At least one expected-results table per objective |
| Using SPIRIT 2013 / CONSORT 2010 | Use SPIRIT 2025 / CONSORT 2025; lifestyle interventions add TIDieR (+ CERT) |
| Drug RCT with no statement on whether the drug is licensed and used within its registered indication in Vietnam | Step 6b: check registration number, indication, drug-trial dossier |
| Lifestyle, behavioural or surgical trial labelled "phase III" | Step 6c: "Phase: Not Applicable"; call it a confirmatory or pragmatic RCT |
| Add-on trial with no shared background-therapy adjustment protocol | Step 6c: shared dose-adjustment algorithm, rescue criteria, record background-medication changes |
| Drug trial in women of reproductive age with no pregnancy test, contraception or washout | Step 6b: add to inclusion, exclusion and stopping criteria and the follow-up schedule |
| Endocrine outcome measured by different methods or laboratories across visits | Same method, same laboratory, same lot; baseline and end samples run in the same batch |
| Adjusting for a mediator (for example weight loss) when estimating a drug's total effect on hormones | DAG: weight loss is a mediator; use it only in a predeclared mediation analysis |
| Case-control for a behavioural exposure with a common disease, exposure measured after diagnosis | Prefer cross-sectional or cohort, or measure exposure before diagnosis; state reverse causation |
| Qualitative protocol says only "in-depth interviews, content analysis" | All 8 qualitative essentials (approach, sampling, sample size, guide, language, analysis, reflexivity, trustworthiness) |
| Downgrading an analytic study because the "sample is not representative" | Representativeness is critical only for prevalence estimates; analytic studies put internal validity first |
| Self-written questionnaire with leading or double-barrelled items | Apply the item-writing rules; pilot first |
| A rough sample size calculated inside the protocol | Leave the sample size section empty; hand off to `sample-size-sap` |
| Qualitative arm with no justified sample size (18 Nov test run) | Information power + saturation evidence, via `sample-size-sap` |
| Diet → PCOS case-control accepted with no reverse-causation warning (18 Nov test run) | Reverse-causation rule; prefer cohort or cross-sectional |

## Why these rules (change history)

18 Nov 2026 (11 edits to the skill and its three reference files):
- SPIRIT 2025 (34 items) and CONSORT 2025 (30 items) replace SPIRIT 2013: journals and registries now
  expect the 2025 checklists (Chan 2025; Hopewell 2025; citations in `design/protocol-template.md`).
- The template's SPIRIT column is flagged as 2013 numbering rather than renumbered: the full 2025 map was
  not verified, and a wrong map is worse than a clearly flagged old one (a conservative judgement).
- TIDieR (+ CERT for exercise) and STROBE-Equity, with EQUATOR for versions: lifestyle interventions are
  often described too vaguely to replicate ("dietary counselling") (EQUATOR Network; Slade 2016 for
  CERT; STROBE-Equity 2025).
- Qualitative essentials (8 items): qualitative design used to be one table row; SRQR and COREQ require
  these elements, and a clinician interviewing her own patients invites socially desirable answers.
- Reverse causation for behavioural exposures: in a test run a diet → PCOS case-control passed without
  comment, although women change diet after diagnosis (Ogden 2019, ch. 7).
- Representativeness mainly for prevalence aims; internal validity first for analytic studies; equal
  strata: otherwise good clinic-based analytic studies are wrongly downgraded (Tuấn 2018).
- Measurement quality (concept → operational definition → instrument; Vietnamese-validated tools;
  self-report biases; continuous variables kept continuous): diet and activity are self-reported, so
  social desirability and recall are the main threats (Tuấn 2018).
- Questionnaire-writing rules: many Vietnamese theses use self-written questionnaires, and poor items give
  unusable data (Tuấn 2018).
- Extra biases (survival / prevalent-user, ecological fallacy, regression to the mean, Hawthorne,
  confounding by indication): regression to the mean matters especially in weight-loss studies that
  recruit people with high BMI (Tuấn 2018).
- Bradford Hill, analysis plan before data collection, reproducible scripts: structured causal reasoning
  and no data-driven analysis choices (Tuấn 2018; Ogden 2019).
- Five new error rows record these failure modes.

20 Nov 2026 (v3): step 6b drug or device checklist and 4 error rows; the AI model design row and AI
bias row (data leakage, overfitting to the validation set, spectrum bias, dataset shift) after a test
case on an AI-integrated cardiac surgical robot; step 6c phase label and background therapy, 2 error
rows, the behavioural or lifestyle RCT bias row (contamination, co-intervention, waning effect,
adherence, CACE) and the "behavioural intervention added to standard care" design row after a test case
on metformin + insulin + GLP-1 RA ± lifestyle in type 2 diabetes.

Sources named: Nguyễn Văn Tuấn (2018), chapters on representativeness, questionnaire design, study
models and interpreting results; Ogden (2019); Amelia Le's course slides; SRQR; COREQ; EQUATOR Network;
ICH E9(R1). None of these is cited in a project without a verified identifier.
