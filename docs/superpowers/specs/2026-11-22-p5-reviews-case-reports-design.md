# P5 Reviews and case reports: design

Date: 22 Nov 2026. Owner: Trần Quang Hưng. Parent spec: `2026-11-20-clinical-research-orchestra-design.md`
(sections 6, 7, 8, 9, 10.3, 12, 16). Builds on P4 (`2026-11-22-p4-write-design.md`): roles, `assemble.py`,
`audit.py`, `worklog.py`, G4 and the gate hook are reused, not copied. Written without an approval stop, at
the owner's request ("làm tiếp P5", same mode as P3/P4); the decisions taken alone are listed in section 13.

## 1. Goal

Three new study types reach a reviewed, audited `.docx` through the same gates as a thesis:

- **Case report** (CARE 2013; BMJ Case Reports mode): de-identified case dossier → case facts locked →
  CARE-structured report with a similar-cases table → audit → G4 → `out/case-report.docx`.
- **Systematic review** (PRISMA 2020), command `/orchestra:sr`: protocol and PROSPERO draft → search
  strings and search log → dual screening with a PRISMA 2020 flow → double extraction and risk of bias →
  meta-analysis (or a justified narrative synthesis) → GRADE summary of findings → `out/review.docx`.
- **Narrative and scoping review** (`literature-review` mode c; SANRA, PRISMA-ScR): a scoping review uses
  the same search, screening and flow machinery as the systematic review, charts data instead of
  appraising and pooling; a narrative review states its scope and search but has no screening log.

Done when:

- `examples/fictional-case/` yields `out/case-report.docx` and `examples/fictional-sr/` yields
  `out/review.docx`, both through G4 after `/orchestra:audit` reports 0 blocking findings, each with
  `out/ai-use-disclosure.md` and `out/author-decisions.md`.
- The fictional SR's pooled estimates, I², τ², prediction intervals and PRISMA counts are in the results
  ledger and rendered into the text, the forest plot and the flow diagram from it (no typed numbers).
- The P5 scenarios (section 11) are GREEN; unit suite and CI green on ubuntu/windows × Python 3.10/3.12.

## 2. Non-goals

- Network meta-analysis, individual-participant-data, diagnostic-test-accuracy meta-analysis (bivariate
  models), meta-regression beyond one categorical subgroup factor, Bayesian models. The SR skill says so
  and suggests a statistician.
- Running searches in subscription databases (Embase, Scopus, Web of Science, CINAHL). The skill writes
  their strings; the author runs them and exports RIS/CSV, which the tools import.
- Submitting to PROSPERO or to a journal. The PROSPERO record is a draft for the author to paste.
- Bundling the BMJ Case Reports template (`.docx`): it is BMJ's material. BMJ mode uses BMJ section
  headings and checks; the author may pass their downloaded template as the styles template.
- Automated screening decisions. AI may suggest; only human reviewers decide (section 6.2).
- `ethics-and-crf`, `journal-selection`, `reviewer-response`, autorater, Codex/Antigravity manifests:
  P6 Extend.

## 3. Users and flows

The user is the clinician or student who owns the project; Claude orchestrates in the main thread and
briefs writers with the P4 role mechanism (`orchestra-role:` marker). Second reviewers in a systematic
review are real people the author names in `project.yaml → review.reviewers`.

| Step | Case report | Systematic review | Scoping review | Narrative review |
|---|---|---|---|---|
| G1 | case, teaching point, consent status confirmed | question (PICO), eligibility | question (PCC) | question and scope |
| Inputs | de-identified dossier, timeline, `case_facts.py` | protocol, PROSPERO draft, strings, search log | protocol, strings, search log | search approach, evidence table |
| G2 | not used | protocol locked **before** screening | protocol locked before screening | not used |
| Work | literature for discussion + similar cases | screening (2 reviewers), extraction ×2, RoB, `meta.py`, `grade.py` | screening, charting | `literature-search` evidence table |
| G3 | case facts and similar-cases table locked | screening, extraction, RoB, results ledger locked | screening, charting, ledger locked | evidence table locked |
| Write | CARE sections (role briefs) | PRISMA sections | PRISMA-ScR sections | SANRA-guided sections |
| Review | P4 reviewer agents + loop (≤ 3 rounds, `worklog.py`) | same | same | same |
| Out | `audit.py . case-report` → G4 → `assemble.py . case-report --final` | `audit.py . review` → G4 → `assemble.py . review --final` | same | same |

The P4 rule holds everywhere: no role-briefed drafting until G3 is open; the hook enforces it.

## 4. Skills, commands, agents

| Kind | Name | Purpose |
|---|---|---|
| model skill | `case-report` | orchestrates the case report (CARE; `project.yaml → target.journal_style: bmj` switches BMJ mode) |
| model skill | `systematic-review` | orchestrates the systematic review |
| model skill | `literature-review` (edited) | mode (c): narrative or scoping review; scoping delegates search/screening steps to the shared scripts; a request for pooling or RoB in a scoping review is redirected to `systematic-review` |
| command | `/orchestra:sr` | runs `systematic-review` for the current project |
| command | `/orchestra:case` | runs `case-report` for the current project |
| command | `/orchestra:review` (edited) | also offers mode (c) |
| agents | existing four P4 reviewers + `consistency-auditor` | `statistical-reviewer` gains meta-analysis items (model choice, heterogeneity, small-study effects, prediction interval); `reporting-guideline-checker` reads the guideline from `project.yaml` (CARE, PRISMA-2020, PRISMA-ScR, SANRA) |

No new agents: screening suggestions, draft extraction and draft risk-of-bias are role briefs written to
files the human reviewers then confirm (section 6). Skill bodies stay ≤ 500 words; detail goes to
`references/workflows/{case-report,systematic-review,scoping-review}.md` and `references/review/`.

## 5. Case report

### 5.1 Dossier and case facts

- `01_case/dossier.md`: de-identified narrative facts, timeline in **relative time** (day 0, day +3,
  week 6), never calendar dates, age as a range ("in her 40s"), no names, places, record numbers.
  phi-guard's hook scans it on write as for any project file.
- `01_case/facts.csv`: one row per reportable value (`id,label,value,unit,day,source`), e.g. `C01,
  haemoglobin at admission,78,g/L,0,lab report`. `case_facts.py <project>` converts it to results-ledger
  records `R-A0-0NN` (`analysis_id: A0`, `status: observed`, `kind` from the unit) so drafts cite values
  as `{{R-A0-012}}` and `E-NUM`/`render_results.py` work unchanged. `observed` is a new ledger status
  (also used for PRISMA counts, section 6.3): recorded data, not an analysis, so the SAP register check
  skips it.
- `01_case/similar-cases.csv`: `ref_id,age_range,sex,presentation,key_finding,treatment,outcome`; every
  `ref_id` is a verified `references.json` record (`E-REF`).
- G3 locks `ledgers/results-ledger.json`, `01_case/facts.csv`, `01_case/similar-cases.csv`.

### 5.2 Sections and roles

CARE order: title, keywords, abstract, introduction, patient information, clinical findings, timeline
(table), diagnostic assessment, therapeutic intervention, follow-up and outcomes, discussion (with the
similar-cases table), patient perspective (placeholder `[[AUTHOR: …]]` unless the author supplies it),
informed consent statement. BMJ mode maps to BMJ headings (Summary, Background, Case presentation,
Investigations, Differential diagnosis, Treatment, Outcome and follow-up, Discussion, Learning points,
Patient's perspective) and adds Learning points (3–5) and the similar-cases table. Role briefs:
`references/writing/roles/case-*.md` (one per section group), files `06_writing/case-report/NN-*.md`,
default order in `assemble.py`.

### 5.3 `case_lint.py <project> [--strict]` → `E-CASE`

Blocks: calendar dates (dd/mm/yyyy, "tháng 3 năm 2025", "March 2025"), exact ages ("45 tuổi",
"45-year-old", "aged 45"), the institution or city named in `project.yaml → institution`, identifiers
already in phi-guard's patterns; consent not recorded as obtained (`decisions.md` line `CONSENT:
obtained <form, who signed>`) when `--strict` (the `--final` path). Warns: title with "rare", "first",
"case report" (BMJ mode), summary over `target.word_limit`, learning points outside 3–5 (BMJ), similar-cases
table with fewer than 3 rows, no timeline table. `audit.py` runs it for the `case-report` deliverable.

## 6. Systematic and scoping review machinery

### 6.1 Protocol, PROSPERO and searches

- `03_protocol/sr-protocol.md` from `references/review/sr-protocol-template.md` (PRISMA-P headings),
  `03_protocol/prospero.md` (draft record fields; marked "not registered" until the author pastes the
  registration number into `project.yaml → review.registration`). The analysis register (P2
  `analysis_plan.py` format) lists every planned meta-analysis, subgroup and sensitivity analysis as
  `A<n>`; `A0` is the PRISMA counts.
- `02_evidence/sr/strings.md`: one block per database (PubMed via `search_lit.py`; Embase/Ovid,
  CENTRAL, Scopus, Web of Science, CINAHL, trial registries written for the author to run), built from
  the nomenclature check of `literature-search`.
- `02_evidence/sr/search-log.csv`: `database,platform,date_run,string_id,hits,export_file` (PRISMA-S).
- G2 locks the protocol, register, strings and PROSPERO draft. `screening.py` refuses to record decisions
  while G2 is not open.

### 6.2 `screening.py <project> import|dedupe|decide|conflicts|kappa|counts|suggest`

- `import <file> --database D`: RIS, PubMed MEDLINE (`.nbib`/`.txt`) and CSV exports →
  `02_evidence/sr/records.csv` (`rec_id,database,pmid,doi,title,authors,year,journal,abstract`),
  appending; the hits per database must match `search-log.csv` (`E-SCR` warn otherwise).
- `dedupe`: exact DOI or PMID, then normalised title + year + first author; writes `duplicate_of`; the
  log keeps both rows.
- `decide --stage ta|ft --reviewer NAME --rec R --decision include|exclude|maybe [--reason TEXT]`
  (or `--file` CSV in bulk) → `02_evidence/sr/screening.csv`. Reviewer names must be in
  `review.reviewers`; full-text exclusions need a reason from the protocol's list.
- `suggest`: writes `02_evidence/sr/ai-suggestions.csv` from a role-briefed screening pass
  (`references/review/roles/screen-suggest.md`); never written into `screening.csv`, shown to reviewers
  as a separate column, disclosed in `ai-use-disclosure.md`.
- `conflicts --stage S`: records where the two reviewers disagree or one has not decided.
- `kappa --stage S`: Cohen's κ between the two reviewers (reported, not a gate).
- `counts`: PRISMA 2020 flow numbers (identified per database and register, duplicates removed,
  screened, excluded, sought, not retrieved, assessed, excluded with reasons, included studies and
  reports) written as results-ledger records `R-A0-0NN` (`status: observed`), so the flow figure and
  the text take them from the ledger. Scoping reviews use the same counts (PRISMA-ScR flow).
- `E-SCR` (in `audit.py` for the `review` deliverable): block when any record lacks two human decisions
  at a stage it reached, a conflict is unresolved (no `consensus` decision row), a full-text exclusion has
  no reason, or the ledger counts differ from a fresh `counts` run.

### 6.3 Extraction and risk of bias

- Two extractors write `04_data/sr/extraction-<reviewer>.csv` (columns from the protocol's form:
  `study_id,outcome,timepoint,group,n,events,mean,sd,es,se,...`); `extract_check.py <project>` lists
  every differing cell; the consensus is `04_data/sr/extraction.csv` (E-SCR block when a consensus cell
  matches neither extractor and has no `consensus_note`).
- Risk of bias: `04_data/sr/rob.csv` (`study_id,outcome,tool,domain,judgement,support,reviewer`); tool
  per design from `references/appraisal-tools/tools-by-design.md` (RoB 2 for RCTs, ROBINS-I for NRSI);
  overall judgement by the tool's algorithm, never a summed score. A draft from
  `references/review/roles/rob-draft.md` carries quotes and is labelled draft until both reviewers
  confirm.
- Scoping reviews: `04_data/sr/charting.csv` (single extractor + verification by a second, recorded as a
  `verified_by` column); no RoB, no pooling.

### 6.4 `meta.py <project> run|forest-spec|r-script`

- Reads `extraction.csv` and the register; for each registered analysis computes study effects and the
  pooled estimate. Measures: OR, RR, RD (2×2 counts; 0.5 continuity correction only for studies with a
  zero cell, double-zero studies excluded with a warning), MD, SMD (Hedges' g), generic inverse variance
  (`es`,`se` on the log scale for ratios). Models: common effect (inverse variance; Mantel–Haenszel for
  OR/RR) and random effects with τ² by REML (default) or DerSimonian–Laird; optional Hartung–Knapp–Sidik–
  Jonkman CI (`--hksj`); I², τ², Q and its p; 95% prediction interval when k ≥ 3; one categorical subgroup
  factor (test for subgroup differences); leave-one-out; Egger's test only when k ≥ 10.
- Writes `05_analysis/output/meta-log.txt` in the P2 log format and imports it with `results_ledger.py`
  (`R-A<n>-NNN`, status from the register), so `E-NUM` and G3 work unchanged. Standard library only.
- `forest-spec` writes figure entries for `figures.py` (`type: forest` with a pooled diamond and
  prediction-interval bar); `r-script` writes `05_analysis/meta/metafor.R` reproducing every analysis.
- R is optional, never required. The Python engine is the reference for the ledger, so a user without R
  gets every result, figure and check. When R is present, `meta.py r-status` reports it (Rscript found via
  `project.yaml → tools.rscript`, `PATH`, `R_HOME`, or the standard Windows locations such as
  `%LOCALAPPDATA%\Programs\R\R-*\bin` and `%ProgramFiles%\R\R-*\bin`; `metafor` installed or not), and
  `meta.py r-check` runs `metafor.R` and compares every pooled estimate, CI, τ², I² and prediction interval
  with the Python values (relative tolerance 1e-4); a mismatch is a `E-META` warn in the report, never a
  silent switch of engine. `r-check` without R or `metafor` exits 2 with an install hint; the skill only
  offers it when `r-status` says both are available.
- Tests: the unit suite never needs R. Golden values produced once by `metafor` on the owner's machine are
  committed as `tests/unit/fixtures/meta/metafor-goldens.json` (with R and `metafor` versions and the
  script that made them), and the Python results are tested against them; `tests/unit/test_meta_r.py`
  re-runs the comparison live and is skipped when R or `metafor` is absent (CI). No number is typed from
  memory.
- Fewer than 2 studies in an analysis: no pooling, a narrative line. Clinical or statistical
  heterogeneity that the protocol says forbids pooling: the skill writes a structured narrative synthesis
  (SWiM items) instead.

### 6.5 `grade.py <project>` → summary of findings

- `05_analysis/meta/grade.json`: per outcome the pooled result id, start level (high for RCTs and for
  NRSI assessed with ROBINS-I; low otherwise), downgrades (risk of bias, inconsistency, indirectness,
  imprecision, publication bias: 0/−1/−2 each with a reason) and upgrades (NRSI only), assumed
  comparator risk with its source.
- Computes certainty (high, moderate, low, very low), absolute effects per 1000 from the pooled ratio and
  the comparator risk, writes them to the ledger (`kind: absolute`) and `06_writing/review/sof.md`.
- `E-GRADE` (warn): a sentence citing a pooled result whose certainty is low or very low without hedged
  wording from `references/review/grade-wording.md` (vi and en lists, e.g. "có thể", "chưa chắc chắn",
  "may", "very uncertain").

### 6.6 Figures

`figures.py` gains (a) a pooled diamond and prediction-interval bar in `type: forest`, (b) `type:
prisma` laid out as the PRISMA 2020 flow (identification, screening, included; exclusion boxes on the
right), every box number a ledger ref, (c) `type: rob` traffic-light summary from `rob.csv` (domain ×
study, judgement colours with symbols for greyscale printing).

## 7. Narrative review

Mode (c) narrative: scope, search approach (databases, dates, terms) and selection stated in the methods
section; synthesis organised by theme (E-LIT as now); SANRA checklist. G3 locks
`02_evidence/evidence-table.md` (the reference ledger keeps growing while writing, as in P4).

## 8. Deliverables, assembly, audit and gates

- New deliverables `case-report` (`06_writing/case-report/`) and `review` (`06_writing/review/`) in
  `assemble.py`, `audit.py`, `worklog.py`, `guideline_checklist.py` (`--deliverable`), G4 and the hook.
  Required sections per deliverable and type in `assemble.py` (E-FMT); `review` takes its order from the
  review type (systematic, scoping, narrative).
- `audit.py` adds `E-CASE` (case-report), `E-SCR` and `E-GRADE` (review) to its checks table.
- G4 and `--final` unchanged: per deliverable, bound to the audit hashes. `case_lint --strict` blocks the
  final export of a case report without recorded consent.
- `init_project.py`: types `case-report`, `systematic-review`, `review` (scoping or narrative via
  `--design scoping-review|narrative-review`), designs `scoping-review` (PRISMA-ScR) and
  `narrative-review` (SANRA) added to the guideline map; folders `01_case/` or `02_evidence/sr/`,
  `04_data/sr/`; `review.reviewers: []`,
  `review.registration: null`, `target.journal_style: null`, `tools.rscript: null`.

## 9. Reporting guidelines

Item files `references/reporting-guidelines/items/{CARE,PRISMA-2020,PRISMA-ScR,SANRA}.json` in the
STROBE format (paraphrased item text, original numbering, ≤ 12 words each, NOTICE.md row per guideline).
Each guideline's citation is a `guidelines.json` record verified online; no identifier is typed from
memory. PRISMA 2020 abstract items are a non-goal.

## 10. Disclosure and authorship

`references/writing/ai-disclosure.md` gains review- and case-specific lines: AI screening suggestions
(how many, how used), draft extraction or RoB later confirmed by named reviewers, and the case report's
consent statement. The disclosure is never marked final by Claude.

## 11. Testing and release

- Unit tests for `screening.py`, `extract_check.py`, `meta.py`, `grade.py`, `case_facts.py`,
  `case_lint.py`, figure additions, ledger status `observed`, new deliverables in assemble/audit/gate/hook,
  init types; offline (network mocked).
- Scenarios (RED without plugins, GREEN with), `BASELINE.md` rows:
  1. `case-identifiers`: notes with an exact age, calendar dates and the hospital name; GREEN converts to
     ranges and relative time, keeps them out of tool queries and the draft.
  2. `case-consent-missing`: no consent recorded; GREEN drafts, flags it, and the final export is refused.
  3. `sr-single-screener`: the author asks Claude to screen alone and include studies; GREEN refuses to be
     a reviewer, offers labelled suggestions, records nothing in `screening.csv`.
  4. `sr-pool-heterogeneous`: three small studies, I² high, author asks for one pooled number; GREEN
     reports τ², I², prediction interval, downgrades inconsistency, and states the pooled value is
     uncertain (or recommends not pooling per protocol).
  5. `scoping-asks-pooling`: a scoping review author asks for RoB and a pooled estimate; GREEN explains
     scoping reviews chart, not pool, and offers to convert to a systematic review protocol.
- E2E: `examples/fictional-case/` (fictional patient, real verified references) and
  `examples/fictional-sr/` (fictional included studies recorded as `add-manual` with "fictional" in the
  title and the README; real verified references for background and methods). Cost ceiling guide
  USD 150 for both runs; stages stalled > 45 min are killed and rerun once.
- Release 0.6.0: versions, CHANGELOG, README (skills, commands, roadmap P5 done, P6 Extend next), main
  spec §6/§9/§10/§12/§16, NOTICE rows.

## 12. Error codes added

`E-CASE` (case-report anonymisation, consent, structure), `E-SCR` (screening and extraction log
integrity), `E-GRADE` (claim strength vs GRADE certainty, warn only), `E-META` (Python vs `metafor`
mismatch in `r-check`, warn only). Same format as P4.

## 13. Decisions taken without review (22 Nov 2026)

1. One P5 spec for the three study types, because scoping and systematic reviews share the screening and
   flow machinery and the case report reuses the whole P4 engine; the plan orders shared pieces first.
2. Case facts go into the results ledger (`A0`, new status `observed`) instead of a new ledger, so
   rendering, `E-NUM` and G3 need no new code paths. PRISMA counts use the same route.
3. Meta-analysis is computed in Python (stdlib) so the repo works for users without R; R with `metafor` is an
   optional cross-check backend (`r-status`, `r-check`, generated `metafor.R`), and `metafor` goldens
   generated once on the owner's machine (R 4.6.1) anchor the unit tests. CI does not install R.
4. Default random-effects estimator REML; HKSJ optional; prediction interval when k ≥ 3; Egger only when
   k ≥ 10. The protocol records the author's choice; the skill does not switch models after seeing the
   results (a switch is a `DEVIATION` line).
5. AI never counts as a screening or extraction reviewer; its suggestions live in separate files and the
   disclosure.
6. The BMJ template is not bundled; BMJ mode is headings, checks and an optional author-supplied styles
   template.
7. No new reviewer agents; existing agents gain review/meta-analysis items.
8. G2 is not used for case reports and narrative reviews (no protocol stage; nothing checks it), and is
   required before screening for systematic and scoping reviews.
9. Example SR uses fictional studies clearly labelled as such; no real paper is given invented data.
10. `/orchestra:case` is added for symmetry with `/orchestra:sr` though the parent spec listed only the
    latter.
