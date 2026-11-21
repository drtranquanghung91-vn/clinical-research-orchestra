# Appraisal tool by design

Methods content by Amelia Le (co-author), adapted for clinical-research-orchestra. Source: `critical-appraisal-vi` v3.

The **main tool** appraises how well the study was done. The **reporting standard** only checks that
the paper reports enough to be appraised; it is never a quality score.

| Real design | Main appraisal tool | Alternative / addition | Reporting standard (to check completeness) |
|---|---|---|---|
| Individual RCT | **RoB 2** (Sterne 2019) | JBI RCT (2023 version); CASP RCT | CONSORT 2025 |
| Cluster RCT | RoB 2 cluster version (adds a domain on recruitment after randomisation) | none | CONSORT cluster extension |
| Crossover RCT | RoB 2 crossover version (adds carry-over) | none | CONSORT crossover extension |
| Non-randomised intervention; comparative-treatment cohort | **ROBINS-I V2** (2025; includes immortal time bias) | JBI quasi-experimental | TREND; STROBE |
| Cohort / case-control on an **exposure** (not a treatment) | **ROBINS-E** (Higgins 2024) | Newcastle–Ottawa (NOS); JBI cohort / case-control; CASP cohort / case-control | STROBE |
| Analytical cross-sectional | **AXIS** (Downes 2016) | JBI analytical cross-sectional | STROBE |
| Descriptive cross-sectional (prevalence) | **JBI prevalence** | AXIS | STROBE (± STROBE EPIC) |
| Case series / case report | JBI case series / case report | none | CARE |
| Qualitative | **CASP Qualitative** | JBI qualitative | SRQR, COREQ |
| Mixed methods | **MMAT** (Hong 2018) | none | GRAMMS |
| Diagnostic accuracy | **QUADAS-3** (Whiting 2026) | QUADAS-2 | STARD 2015 |
| Prediction model / AI | **PROBAST+AI** (Moons 2025) | PROBAST 2019 | TRIPOD+AI |
| SR/MA of interventions or observational studies | **AMSTAR 2** (Shea 2017) | ROBIS | PRISMA 2020 (+ PRISMA-S) |
| Economic evaluation | CHEC list / Drummond checklist | none | CHEERS 2022 |
| Clinical guideline | AGREE II | none | RIGHT |
| Body of quantitative evidence | **GRADE** (Guyatt 2008) | none | none |
| Body of qualitative evidence | **GRADE-CERQual** (Lewin 2018) | none | ENTREQ |

The official question forms are on the developers' sites (riskofbias.info, CASP, JBI, AMSTAR, QUADAS,
PROBAST). `tool-domains.md` only summarises the domains to orient the reader. When the user needs a
submission-grade appraisal (systematic review, thesis), tell them to download the correct official
version and record the version used.
