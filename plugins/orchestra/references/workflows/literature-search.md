# Literature search: full workflow

Methods content by Amelia Le (co-author), adapted for clinical-research-orchestra. Source: her
`literature-evidence-research-vi` v3 (20 Nov 2026) and its two change notes (18 Nov, 20 Nov). Where
the v3 text and the 18 Nov notes differ, v3 is followed. Thresholds below are **defaults** the
author may override, not standards.

Tool procedures (PubMed, Consensus, OpenEvidence, ClinicalTrials.gov), the verification table and the
evidence hierarchy live in `${CLAUDE_PLUGIN_ROOT}/references/evidence-policy.md`; read it before
calling a tool. Query building, the nomenclature check and the search log:
`${CLAUDE_PLUGIN_ROOT}/references/literature/search-strategy.md`. Output shapes:
`${CLAUDE_PLUGIN_ROOT}/references/literature/evidence-output-template.md`.

## Why this skill exists (core rule)
- Every claim about the literature traces to a paper with a PMID or DOI that a tool returned **in this
  session**. No exception for "common knowledge", "the classic paper everyone knows", or a slow MCP.
- A fabricated reference, or a wrong year or journal, is the most serious error for a thesis author:
  the committee can check it and the author carries the responsibility.
- This is a structured narrative or scoping evidence synthesis, **not** a systematic review. Say so in
  the methods. If the user needs a true SR/MA: it needs a PROSPERO protocol, at least two independent
  screeners and PRISMA 2020 reporting; state this, do the preparation (question, search strategy) and
  point to `systematic-review` (phase P3). Never call this output a "systematic review".

## Inputs and questions
- Inputs: the research question and its PICO/PECO frame, read from `01_question/question.md`.
- If the user gives only a vague topic, force a quick PICO/PECO (state the assumptions) and search; if
  the topic is too vague to search, use the Skill tool with `research-question` first.
- Ask once, and only for what is missing: purpose (thesis literature chapter, article background, or
  finding gaps), desired length, year limit, output language (default follows
  `project.yaml → language.output`; English terms stay in brackets in Vietnamese text).
- The user said not to ask ("cứ làm luôn", "just do it"): do not ask. Open the answer with an
  **Assumptions / Giả định** box listing every assumption, put the riskiest in the confirmation list,
  and record the box in `decisions.md`.

## Step 0 – Nomenclature and current definition check
Before building any query: was the condition or concept renamed, does it have new diagnostic
criteria, or is MeSH out of date? If so, add old and new names with `[tiab]` to the P block and note
it in the search log. Full procedure, the PCOS → PMOS case (the 2026 PLoS Med meta-analysis indexed
under "Metabolic Syndrome" is missed by the standard PCOS query) and the missed-papers measurement:
`search-strategy.md` §Nomenclature check. Why it exists: in the test run the most relevant 2026 review
was invisible to the skill's own search, which makes a search invalid and not reproducible over time.

## Step 1 – Search plan
Break the PICO/PECO into concept blocks (MeSH plus free text, OR inside, AND between). Write the full
PubMed query and 3–5 English questions for Consensus/OpenEvidence, each aimed at one sub-topic
(epidemiology, mechanism, effectiveness, associated factors, Vietnam/Asia context, guideline).
Mark each search targeted (one named primary source) or exploratory (ranked list for context). Write
the plan to `02_evidence/search-strategy.md` with the PRISMA-S fields.

## Step 2 – Search several sources
Log every query: date, source, query, filters, number of results, number kept.
- PubMed (`search_lit.py search`, or a PubMed MCP): main query; SR/MA query; RCT query (intervention
  questions); Vietnam query. More than 500 results → narrow; fewer than 10 → widen (synonyms, drop the
  least important block).
- Consensus: sub-topic questions, at most 3 in parallel.
- OpenEvidence, if `oe_auth_status` is OK: 1–2 synthesis questions ("what is known / what are the gaps
  / guideline recommendations"). Blocked (geo-restriction) → tell the user a VPN is needed and carry on
  with PubMed and Consensus; do not stop and wait.
- ClinicalTrials.gov (when a tool is available, for intervention questions): trials running or
  finished but unpublished. **Always add one pass filtered by the study country** (for Vietnam,
  `location="Vietnam"` or read the site list). A registered trial with no publication is the most
  important counter-check for a population gap (verified example: NCT05952882 at Mỹ Đức Hospital, no
  PubMed paper). `search_lit.py trial <NCT>` fetches a trial already named.
- For key papers (newest SR, large RCT) run `find_related_articles` to catch missed papers.
- At least PubMed plus Consensus; OpenEvidence when reachable. One source alone is a listed error.
- Add chosen records with `search_lit.py add <project> <pmid-or-doi> [...]`: PMIDs go to PubMed (Europe
  PMC when NCBI is unreachable), DOIs to Crossref; a doi.org URL prefix is stripped and a work already in
  the ledger is not added twice. A Vietnamese journal article, thesis or Ministry of Health document
  with neither identifier is added only when the author holds it:
  `search_lit.py add-manual <project> --title T --authors "Surname AB; Surname CD" --journal J --year YYYY
  --seen-in "00_inputs/file.pdf p. 45"`. Ask the author for the document; never fill it in from memory
  or a search snippet. `verify_refs.py` lists these as MANUAL (not machine-verifiable, exit code
  unaffected); they may be cited, and the limitation is stated.

## Step 3 – Screening and selection
Read titles and abstracts through the metadata call. Keep papers that answer the PICO directly;
prefer higher in the hierarchy (`evidence-policy.md` §Evidence hierarchy), newer, and nearer the
user's population. Targets (**default**): 15–40 papers for a thesis chapter, 8–15 for an article
background. Record, per query, `total_count` → number screened (for example "first 30 by relevance")
→ number kept. If not everything was screened, write "screened the first N by relevance" in the
limitations and never present the review as if all results were read.

## Step 4 – Verification
Every kept paper has a PMID or DOI through the procedure in `evidence-policy.md` §Verifying
references, then run `verify_refs.py <project> --write`. A paper that cannot be verified is dropped, or
kept tagged `[chưa xác minh trên PubMed]` (`[not verified in PubMed]` in English output) when it is a
domestic journal or a guideline with a URL. A Consensus paper without PMID/DOI is verified in PubMed
(`[ti]` words + `[au]` + `[dp]`) first.

## Step 4b – Source credibility (CARS; *Choosing & Using Sources* ch. 6)
- (a) Retractions: `(<pmid1>[pmid] OR …) AND (Retracted Publication[pt] OR Retraction of Publication[pt]
  OR "Expression of Concern"[pt])`, **at most 10 PMIDs per batch** (the tool allows 20 Boolean
  operators). A retracted paper is removed and the reason logged. A retracted paper still has a PMID,
  so existence is not credibility.
- (a2) Duplicate publications: two papers with the same registration number, or the same n, dose,
  duration and author group, are one study: one row in the table and the map.
- (b) Journal with predatory signs (not in DOAJ/Scopus, unusual peer review): tag it; never the only
  source of a key figure.
- (c) Record funding and conflicts of interest when the abstract or full text states them.
- Journal prestige does not replace appraisal of content.

## Step 4c – Critical appraisal
Use the Skill tool with `critical-appraisal` (design tree, tool per real design, forms and summary
table, GRADE/CERQual). If the skill is not available, tell the user in one sentence ("critical-appraisal
is needed"), continue with the summary below, and list this in the limitations.
Tool by real design (not the authors' own label): RCT → RoB 2; non-randomised intervention or
comparative cohort of treatments → ROBINS-I V2 (2025); exposure (cohort, case-control) → ROBINS-E or
NOS; cross-sectional → AXIS or JBI; qualitative → CASP or JBI; mixed methods → MMAT; SR/MA → AMSTAR 2;
diagnostic accuracy → QUADAS-3; prediction model → PROBAST+AI. Abstract only → write "preliminary
appraisal from abstract"; what the paper does not report is "Unclear". Separate serious flaws from
minor ones; never add checklist scores into one number. Why: a poorly run RCT can be weaker than a good
cohort, and a hierarchy alone ranks papers the wrong way round. Per-paper forms go to
`02_evidence/appraisal/<ref-id>.md`.

## Step 5 – Extraction into the evidence table
Columns are in the output template: author–year, country, **real design**, n, population,
intervention/exposure, comparator, outcome, main result **with numbers (effect and 95% CI, or
proportion)**, main limitation, **risk of bias (tool: low / moderate / high / unclear)**. The risk
column makes the appraisal visible to a committee and feeds GRADE. Numbers come only from abstracts or
full texts actually retrieved; where the abstract gives none, write "not reported in the abstract",
never fill in.

## Step 6 – Evidence map
A two-way matrix; each cell is a count plus citations [n].
- Rows: components of the question (interventions, exposures or outcomes).
- Columns: design **or** region (West, Asia, Vietnam), whichever exposes the gap best; both tables are
  allowed. Design columns by question type: intervention → SR/MA, RCT, cohort, other; prevalence or
  associated factors → SR/MA, cohort, cross-sectional, instrument-validation studies; diagnostic →
  SR/MA, diagnostic accuracy, other.
- An empty cell or one with only weak evidence is a gap candidate.

## Step 7 – Research gaps
For each gap: the type (table below), the evidence (empty map cell, a "further research is needed"
sentence in a named SR, conflicting results [a] versus [b]) and the **counter-check**: a query aimed
exactly at that gap (and ClinicalTrials.gov) was run and still found nothing. A gap that fails the
counter-check is not included. Rank gaps by fit with the user's resources; population, implementation
and methodological gaps are usually the most feasible for a thesis.

| Gap type | Sign |
|---|---|
| Evidence | No study, or only small or low-quality studies |
| Population | Present in the West, missing in Asia, Vietnam or special groups (children, older adults, pregnancy) |
| Conflicting | Opposite results, high I², an SR that concludes "uncertain" |
| Methodological | Earlier work mostly retrospective, small, unadjusted for confounding, outcome definitions differ |
| Outcome | Only surrogate outcomes, patient-important outcomes or long-term follow-up missing |
| Implementation | Evidence and guidelines exist but uptake, barriers and cost in Vietnam are unknown |
| Outdated | Main evidence predates a major change in diagnosis or treatment |

## Step 8 – Writing and numbering
Writing the review as prose belongs to `literature-review`. When the evidence table, map and gaps cite
papers, write them with `[@id]` keys (same syntax as `verify_refs.py`) and let the script number them:
`python "${CLAUDE_PLUGIN_ROOT}/scripts/cite_render.py" <project> draft.md out.md --start-marker "<review heading>"`,
with a line `{REFERENCES}` where the numbered list goes. Numbers follow first appearance in the
**review** text (tables placed before it reuse the same numbers). Never number by hand. Vancouver
strings come from the ledger records that `search_lit.py add` built from PubMed metadata (up to 6
authors then "et al.", `iso_abbreviation`, year;volume(issue):pages). A requested length applies to
the review text, not to tables or appendices. Organise by theme, not paper by paper; each paragraph:
claim → pooled evidence with numbers and [n] → certainty or conflict → meaning for the user's
question; end with a paragraph leading to the gap.

### Synthesis checks (Ogden 2019; Nguyễn Văn Tuấn 2018)
- **GRADE certainty** (high / moderate / low / very low) for each main outcome, naming the
  downgrading domains; qualitative evidence uses GRADE-CERQual (see `critical-appraisal`). Mark it
  "preliminary assessment". "Evidence is mixed" without a certainty level is not enough.
- **Apples and pears**: are studies of different design, population or intervention pooled? Report I²
  and a prediction interval when available; high I² → do not read the pooled estimate as one common
  effect (test case: a pooled OR from 5 studies with I² = 73% read as one clear effect).
- **Premature review**: a pooled estimate from fewer than 5 studies or fewer than 300 people is said
  to be imprecise (**default**; Ogden names the bias but gives no cut-off).
- **Read the 95% CI by clinical importance, not p**: never write "no difference" for p > 0.05 with a
  wide CI (write "cannot conclude yet"); a narrow CI wholly inside the negligible zone means a
  negligible effect even if p < 0.05.
- **Multiple tests and subgroups**: a lone positive among many comparisons, or in a post-hoc
  subgroup, is a hypothesis, not a finding.
- **Language matches design**: "associated with" for observational work, "effective" only for RCTs;
  for causal questions from observational data weigh the Bradford Hill criteria (above all temporal
  order); never turn qualitative accounts into objective fact.
- **Counter-evidence**: state opposing evidence and answer it, do not pick only supportive papers
  (*Choosing & Using Sources* ch. 9).
- **Replication**: prefer results replicated in several populations; be careful with a "first ever"
  result from one small study (replication crisis; Tuấn 2018).
- Hierarchy is only a starting point: finish with the self-appraisal gate in `evidence-policy.md`.
- Chapter structure for a thesis: template file §Chapter structure.

## Step 9 – Reporting
Methods follow the PRISMA-S items that apply (Rethlefsen 2021, Syst Rev 10:39, doi:10.1186/s13643-020-01542-z):
databases and platforms (PubMed via MCP or `search_lit.py`, Consensus, OpenEvidence,
ClinicalTrials.gov), the full strategy per source, filters and limits, search date, how duplicates
were removed, nomenclature check (step 0), selection criteria, numbers at each step, appraisal tools
used. Add one sentence disclosing AI use (ICMJE): which AI/MCP tools searched, screened, summarised or
appraised, and that the user is responsible for re-checking. The default limitations list: sources not
usable, domestic journals not searched, abstract-only reading, and for AI or engineering topics "IEEE
and arXiv not searched" unless they were.

## Deliverables, in order
1. Question and PICO/PECO used. 2. Search methods (step 9). 3. Evidence table (risk-of-bias column)
plus the appraisal summary table from `critical-appraisal`. 4. Evidence map. 5. Ranked gaps, each with
evidence and counter-check. 6. Thematic review with Vancouver [n] by appearance (see
`literature-review`). 7. References, each ending `PMID: …` and/or `doi: …`. 8. Limitations. 9. Next
steps: `protocol-design` (variable table; confounders to control from the evidence table) and
`sample-size-sap` (parameters from the evidence table).

## Saving, chat and export
- In chat: cite as `[n]`, name PubMed as the source with a DOI link; if Consensus was used, copy its
  upgrade or registration notice verbatim on the last line (`evidence-policy.md` §Citing sources).
- Files go to the paths in the skill's Output section. With no project folder, end the answer by asking
  in one line whether to save.
- Word export: not part of this skill in P1 (deferred to the Word-export tool in phase P3). Until then,
  the author's own export tool may be used; tell the user it is untested in Word.

## Common errors
| Error | Fix |
|---|---|
| A paper from memory in the reference list "because it surely exists" | Find it through PubMed; if not found, do not cite |
| Consensus paper cited without PMID/DOI | Verify through PubMed first (`[ti]` + `[au]` + `[dp]`) |
| Review written as "Author A (2020) studied… Author B (2021) studied…" | Write by theme, many papers per claim |
| A number differs from the original abstract | Take numbers only from returned metadata or full text; re-check before export |
| Gap concluded from one query with few hits | Try synonyms, MeSH, Consensus and ClinicalTrials.gov before concluding |
| Calling this review a "systematic review" | Call it a structured review; an SR needs its own PRISMA process |
| Searching one source only | PubMed and Consensus at least; OpenEvidence when reachable |
| OpenEvidence blocked, so stopping to wait | Tell the user (turn on a VPN), continue with PubMed and Consensus |
| Skipping the newest SR or guideline, citing old papers | Always run the SR/MA and guideline queries, prefer the last 5 years (**default**). No specific guideline → write "no specific guideline found" and use the nearest parent-disease guideline |
| Filing a paper under "Vietnam" only because `Vietnam[Affiliation]` matched | Read the abstract to confirm where the study was done |
| Searching only MeSH plus the old disease name | Step 0: check renaming or redefinition, add old and new names with `[tiab]` |
| A paper in the evidence table without appraisal | Step 4c: `critical-appraisal`, tool by real design, fill the risk-of-bias column |
| Citing a retracted paper | Step 4b: check `Retracted Publication[pt]` |
| Trusting a paper because the journal is respected | Appraise the content; source is not content |
| Writing "no difference" because p > 0.05 | Read the 95% CI by clinical importance; wide CI → "cannot conclude yet" |
| Concluding "Vietnam has no studies" | Write "not found in PubMed/Consensus"; remind the user to search domestic journals |
| The standard PCOS search missed the 2026 PMOS meta-analysis | Step 0 nomenclature check (failure logged in the 18 Nov notes) |
