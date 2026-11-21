# Source credibility (do this before scoring domains)

Methods content by Amelia Le (co-author), adapted for clinical-research-orchestra. Source: `critical-appraisal-vi` v3.

The shared retraction-check procedure, the 10-PMID batch limit and the rule that `RETRACTED` records
are not cited are in `${CLAUDE_PLUGIN_ROOT}/references/evidence-policy.md`. This table adds the
appraisal-specific checks and what each finding means for the appraisal.

| Check | How | Consequence |
|---|---|---|
| Retracted, corrected or expression of concern | PubMed `<PMID>[pmid] AND (Retracted Publication[pt] OR Retraction of Publication[pt] OR "Expression of Concern"[pt])`; for several papers combine `(<p1>[pmid] OR <p2>[pmid] …)` with **at most 10 PMIDs per batch** (the tool limits queries to 20 Boolean operators); Retraction Watch | Retracted: exclude and record why. Corrected: use the corrected data |
| Journal | In PubMed/MEDLINE, DOAJ, Scopus? Signs of a predatory journal (unusually fast peer review, high opaque fees) | Doubt: label it; do not use it as the only source for a key figure |
| Registration and protocol | NCT/ISRCTN codes: `get_trial_details`. PROSPERO (systematic reviews): **no MCP tool** → look it up on the PROSPERO site (web fetch, if available) or write "registration not verified". **Do not judge by the look of the code**: old PROSPERO codes are `CRD42` plus 9 digits (for example CRD42024535096); the newer format from 2025 is longer (for example CRD420251240521); an "extra digit" is not a warning sign. Compare the registered primary outcome with the reported one, and the registration date (before or after recruitment) | An unexplained change of primary outcome makes the selective-reporting domain "high" |
| **Duplicate publication / one trial reported twice** | Compare registration code, sample size, allocation ratio, dose, duration, author group and site between papers. Verified example: Frøssing 2018 (PMID 28681988) and Nylander 2017 (PMID 28479118) are the same RCT, liraglutide 1.8 mg vs placebo 2:1, n = 72, 26 weeks, reporting different outcomes | Merge into **one** study in the evidence table, the evidence map and the RCT count; list the related PMIDs on the same row. For an SR/MA, check whether a study was counted twice (inflates n and precision) |
| Funding and conflicts of interest | Funding and COI sections; authors who developed the intervention | Record it; be more careful when judging spin and selective reporting |
| Signs of data irregularity | Baselines that are implausibly alike in a small RCT, an effect that is too large, numbers that contradict between tables | Record an integrity concern; never conclude fraud yourself |
