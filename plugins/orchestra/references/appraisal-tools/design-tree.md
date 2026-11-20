# Design tree: find the real design

Methods content by Amelia Le (co-author), adapted for clinical-research-orchestra. Source: `critical-appraisal-vi` v3.

Use this tree on what the study actually did, never on the name the authors gave it. Then take the
tool from `tools-by-design.md`.

```
Does the study synthesise other studies?
├─ Yes → systematic search plus selection criteria?
│        ├─ Yes → Systematic review (± meta-analysis) [qualitative: qualitative evidence synthesis]
│        └─ No  → Narrative review (low-level appraisal: SANRA if needed)
└─ No (primary study)
   ├─ Data are narratives or text, analysed for themes or meaning → Qualitative (± mixed methods if numbers are added)
   ├─ Aim is the accuracy of a test against a reference standard → Diagnostic accuracy
   ├─ Aim is to build or validate a risk prediction model → Prediction model
   ├─ Aim is to compare costs and outcomes → Economic evaluation
   └─ Does the investigator DECIDE who receives the intervention?
       ├─ Yes → randomly allocated?
       │       ├─ Yes → RCT (individual / cluster / crossover / stepped-wedge)
       │       └─ No  → Non-randomised intervention study (concurrent control / before–after / interrupted time series)
       └─ No (observational) → is there a comparison group?
               ├─ No  → Case series / case report / descriptive cross-sectional (prevalence)
               └─ Yes → how were participants selected?
                       ├─ By outcome (diseased vs not) → Case-control
                       ├─ By exposure or treatment, followed to the outcome → Cohort (prospective / retrospective)
                       │    (two treatments chosen by clinicians → comparative-treatment cohort, appraised with ROBINS-I)
                       └─ Exposure and outcome measured at the same time → Analytical cross-sectional
```

## Common misidentifications
- An "interventional study" in which the clinician chose the regimen is really a cohort.
- A "case-control" study that samples first and splits by outcome afterwards is really cross-sectional.
- A "cohort" measured only once is really cross-sectional.
- An "RCT" allocated by odd or even day is quasi-random: treat it as a non-randomised intervention study.
- "Prospective" or "retrospective" describes timing, not design: it does not mean cohort.

One paper can hold results of different designs (an RCT with an observational secondary analysis):
appraise each result the decision relies on with its own tool.
