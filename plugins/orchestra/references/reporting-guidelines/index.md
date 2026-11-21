# Reporting guideline library

Every citation below is a record in `guidelines.json` that `verify_refs.py` marked VERIFIED against a live
lookup. Item counts and versions come from each record's abstract or title, or from a full-text lookup.

| Code | Full name | Version/year | Designs | Items | Citation (from guidelines.json) |
|---|---|---|---|---|---|
| CONSORT-2025 | Consolidated Standards of Reporting Trials 2025 | 2025 | rct | 30 | Hopewell S et al.. CONSORT 2025 statement: updated guideline for reporting randomised trials. BMJ 2025;389:e081123. doi:10.1136/bmj-2024-081123 (PMID 40228833) |
| SPIRIT-2025 | Standard Protocol Items: Recommendations for Interventional Trials 2025 | 2025 | rct | 34 | Chan AW et al.. SPIRIT 2025 statement: updated guideline for protocols of randomised trials. BMJ 2025;389:e081477. doi:10.1136/bmj-2024-081477 (PMID 40294953) |
| STROBE | Strengthening the Reporting of Observational Studies in Epidemiology | 2007 | cohort, case-control, cross-sectional | 22 | von Elm E et al.. The Strengthening the Reporting of Observational Studies in Epidemiology (STROBE) statement: guidelines for reporting observational studies. PLoS Med 2007;4:e296. doi:10.1371/journal.pmed.0040296 (PMID 17941714) |
| STARD-2015 | Standards for Reporting of Diagnostic Accuracy Studies 2015 | 2015 | diagnostic-accuracy | 30 | Bossuyt PM et al.. STARD 2015: an updated list of essential items for reporting diagnostic accuracy studies. BMJ 2015;351:h5527. doi:10.1136/bmj.h5527 (PMID 26511519) |
| TRIPOD+AI | Transparent Reporting of a multivariable prediction model for Individual Prognosis Or Diagnosis, with AI | 2024 | prediction-model | 27 | Collins GS et al.. TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use regression or machine learning methods. BMJ 2024;385:e078378. doi:10.1136/bmj-2023-078378 (PMID 38626948) |
| PRISMA-2020 | Preferred Reporting Items for Systematic reviews and Meta-Analyses 2020 | 2020 | systematic-review | 27 | Page MJ et al.. The PRISMA 2020 statement: an updated guideline for reporting systematic reviews. BMJ 2021;372:n71. doi:10.1136/bmj.n71 (PMID 33782057) |
| PRISMA-ScR | PRISMA extension for Scoping Reviews | 2018 | scoping-review | 20 | Tricco AC et al.. PRISMA Extension for Scoping Reviews (PRISMA-ScR): Checklist and Explanation. Ann Intern Med 2018;169:467-473. doi:10.7326/M18-0850 (PMID 30178033) |
| PRISMA-S | PRISMA extension for reporting literature searches | 2021 | systematic-review, scoping-review | 16 | Rethlefsen ML et al.. PRISMA-S: an extension to the PRISMA Statement for Reporting Literature Searches in Systematic Reviews. Syst Rev 2021;10:39. doi:10.1186/s13643-020-01542-z (PMID 33499930) |
| CARE | CAse REport guidelines | 2013 | case-report | 13 | Gagnier JJ et al.. The CARE guidelines: consensus-based clinical case reporting guideline development. J Med Case Rep 2013;7:223. doi:10.1186/1752-1947-7-223 (PMID 24228906) |
| SRQR | Standards for Reporting Qualitative Research | 2014 | qualitative | 21 | O'Brien BC et al.. Standards for reporting qualitative research: a synthesis of recommendations. Acad Med 2014;89:1245-51. doi:10.1097/ACM.0000000000000388 (PMID 24979285) |
| COREQ | COnsolidated criteria for REporting Qualitative research (interviews and focus groups) | 2007 | qualitative | 32 | Tong A et al.. Consolidated criteria for reporting qualitative research (COREQ): a 32-item checklist for interviews and focus groups. Int J Qual Health Care 2007;19:349-57. doi:10.1093/intqhc/mzm042 (PMID 17872937) |
| GRAMMS | Good Reporting of A Mixed Methods Study | 2008 | mixed | not confirmed | O'Cathain A et al.. The quality of mixed methods studies in health services research. J Health Serv Res Policy 2008;13:92-8. doi:10.1258/jhsrp.2007.007074 (PMID 18416914) |
| SANRA | Scale for the Assessment of Narrative Review Articles (a quality scale) | 2019 | narrative-review | 6 | Baethge C et al.. SANRA-a scale for the quality assessment of narrative review articles. Res Integr Peer Rev 2019;4:5. doi:10.1186/s41073-019-0064-8 (PMID 30962953) |
| CHEERS-2022 | Consolidated Health Economic Evaluation Reporting Standards 2022 | 2022 | economic-evaluation | 28 | Husereau D et al.. Consolidated Health Economic Evaluation Reporting Standards 2022 (CHEERS 2022) statement: updated reporting guidance for health economic evaluations. BMJ 2022;376:e067975. doi:10.1136/bmj-2021-067975 (PMID 35017145) |
| TIDieR | Template for Intervention Description and Replication | 2014 | rct, intervention-description | 12 | Hoffmann TC et al.. Better reporting of interventions: template for intervention description and replication (TIDieR) checklist and guide. BMJ 2014;348:g1687. doi:10.1136/bmj.g1687 (PMID 24609605) |
| CERT | Consensus on Exercise Reporting Template | 2016 | rct, exercise-intervention | 16 | Slade SC et al.. Consensus on Exercise Reporting Template (CERT): Explanation and Elaboration Statement. Br J Sports Med 2016;50:1428-1437. doi:10.1136/bjsports-2016-096651 (PMID 27707738) |
| STROBE-Equity | STROBE extension for health equity | 2025 | cohort, case-control, cross-sectional | 10 | Dewidar O et al.. Improving the reporting on health equity in observational research (STROBE-Equity): extension checklist and elaboration. BMJ 2025;390:e083882. doi:10.1136/bmj-2024-083882 (PMID 40903054) |

Notes on the item counts:
- PRISMA-ScR: 20 essential items plus 2 optional items (the count shown is the essential items).
- STROBE-Equity: 10 equity-specific items added to the 22 STROBE items (full text of the dewidar2025 record).
- SANRA: a 6-item quality scale for narrative reviews, not a reporting checklist; use it to self-check a narrative review.
- GRAMMS: item count not confirmed. The 2008 abstract in the record does not state a count, so it is left empty
  rather than filled from memory.
- Version/year for guidelines without a year in the title is the publication year of the cited record.

## How to use
- The reporting guideline is chosen from the design in `project.yaml` (`reporting_guideline` holds the code above).
  Companion guidelines apply on top: PRISMA-S for the search of a systematic or scoping review, TIDieR or CERT
  for the description of an intervention, CHEERS-2022 for an economic evaluation, STROBE-Equity when equity is a focus.
- Fill the checklist as a table of item, page or section where it is reported, and `present / absent / not applicable`.
  Give the location, not only a tick.
- A checklist is never summed into a score or a percentage. It shows what is missing so the authors can report it.
