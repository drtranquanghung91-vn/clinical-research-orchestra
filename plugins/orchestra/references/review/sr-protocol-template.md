# Systematic or scoping review protocol (template)

Copy to `03_protocol/sr-protocol.md`, fill every `[[AUTHOR: …]]`, and have the author lock it with G2 before any
screening decision (`gate.py open . G2 --by "<name>" --files 03_protocol/sr-protocol.md …`). Headings follow
PRISMA-P 2015. A scoping review keeps the headings, writes the question as PCC (population, concept, context),
does not assess risk of bias and does not pool: its register has only A0.

## 1. Administrative information
### 1.1 Title (identify the report as a protocol of a systematic or scoping review)
### 1.2 Registration (PROSPERO number, or "not registered"; draft in `03_protocol/prospero.md`)
### 1.3 Authors, contact and contributions
### 1.4 Amendments (every change after G2 is a `DEVIATION A<n>:` line in `decisions.md`, with its date)
### 1.5 Support (sources, sponsor and the sponsor's role)

## 2. Introduction
### 2.1 Rationale
### 2.2 Objectives (PICO for a systematic review; PCC for a scoping review)

## 3. Methods
### 3.1 Eligibility criteria (designs, participants, interventions or concept, comparators, outcomes, setting, languages, years)
### 3.2 Information sources (databases with platform, trial registries, other sources; planned search dates)
### 3.3 Search strategy (`02_evidence/sr/strings.md`, one block per database; the full PubMed string here)
### 3.4 Study records
- Data management: `02_evidence/sr/records.csv`, `screening.csv`, `search-log.csv`.
- Selection: two reviewers named in `project.yaml → review.reviewers` screen titles/abstracts and full texts
  independently; disagreements are resolved by consensus (a `consensus` row). AI suggestions, if used, stay in
  `ai-suggestions.csv` and are never a decision.
- Data collection: two independent extractors (`04_data/sr/extraction-<reviewer>.csv`), a consensus file
  `04_data/sr/extraction.csv`; how missing data are requested from study authors.
### 3.5 Data items
### 3.6 Outcomes and prioritisation
### 3.7 Risk of bias in individual studies
RoB 2 for randomised trials, ROBINS-I for non-randomised studies of interventions, per outcome; the overall
judgement follows the tool's algorithm, never a summed score. Scoping reviews: not assessed.
### 3.8 Data synthesis
Effect measure per outcome; model (random effects with REML unless justified; HKSJ yes/no); heterogeneity as τ²,
I² and a 95% prediction interval when k ≥ 3; when pooling is not appropriate, a structured narrative synthesis
(SWiM). Scoping reviews: charting and a descriptive summary only.
### 3.9 Meta-bias (Egger's test and a funnel plot only when k ≥ 10)
### 3.10 Confidence in cumulative evidence (GRADE, summary of findings)

## Full-text exclusion reasons
- [[AUTHOR: reason, e.g. wrong population]]
- [[AUTHOR: reason, e.g. wrong study design]]

## Analysis register

| ID | Type | Outcome | Timepoint | Measure | Model | HKSJ | Experimental | Comparator | Factor |
|---|---|---|---|---|---|---|---|---|---|
| A0 | counts | PRISMA flow | | | | | | | |
| A1 | pool | [[AUTHOR: outcome]] | [[AUTHOR: timepoint]] | RR | RE-REML | no | [[AUTHOR: group]] | [[AUTHOR: group]] | |

- Type: `pool`, `subgroup` (Factor = an extraction column, one factor only), `leave-one-out`. A0 = PRISMA counts.
- Measure: OR, RR, RD, MD, SMD, GEN, GEN-OR, GEN-RR, GEN-HR. Model: RE-REML, RE-DL, CE-IV, CE-MH (OR, RR).
- Experimental and Comparator are the `group` values used in the extraction files.
- The author chooses the model before seeing results; a later change is a `DEVIATION A<n>:` line, never a silent
  switch. Network meta-analysis, IPD, diagnostic accuracy and meta-regression beyond one factor need a statistician.
