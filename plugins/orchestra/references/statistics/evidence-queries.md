# Finding sample-size parameters in an evidence source

Methods content by Amelia Le (co-author), adapted for clinical-research-orchestra. Source: her
`sample-size-planning-vi` v3 (20 Nov 2026), `reference/openevidence-queries.md`, generalised from
OpenEvidence to any evidence source. Used by step 4 of the `sample-size-sap` skill.

Which sources, in what order, how to call each tool, and how a reference is verified are set once in
`${CLAUDE_PLUGIN_ROOT}/references/evidence-policy.md` (§Source order, §PubMed procedure, §Consensus
procedure, §OpenEvidence procedure, §Verifying references). This file adds only what is specific to
sample-size parameters.

"Evidence source" below means whichever source the policy puts first and is available: OpenEvidence
(`oe_auth_status`, `oe_ask`, `oe_article_wait`, `oe_article_get`, `oe_citations_get`), PubMed
(`search_lit.py search` or a PubMed MCP), Europe PMC, or Consensus. The template questions in the table
are used unchanged as a natural-language question (OpenEvidence `oe_ask`, Consensus `search`, shortened to
≤ 500 characters). For PubMed or Europe PMC, turn the question into keyword blocks + `AND (randomized
controlled trial[pt] OR cohort studies[MeSH Terms])` and read the numbers in the abstract from the metadata
call (`search_lit.py fetch` or `get_article_metadata`).

## Procedure

1. Check access to the first evidence source. For OpenEvidence: `oe_auth_status`; if
   `authenticated=false` or `blocked="geo"`, tell the user once (log in again with
   `npm run login:session`, or use a VPN) and carry on with the other sources. Do not ask again and again.
2. Ask the question for **each missing parameter**. OpenEvidence: `oe_ask` with `model="sackett"` and
   `wait_for_completion=false` → `article_id`; the error "option was not found" → retry once, then
   switch to `osler` (evidence-policy §OpenEvidence procedure).
3. OpenEvidence: `oe_article_wait` with the `article_id`, `timeout_sec=240`; if `timed_out=true`, call it
   once more. The result already holds `answer_text` + `citations[]`; the PMID is in `url`.
4. Check the parameter's number against the abstract: PubMed metadata by PMID. How to read the result
   (tables use their own numbering, epub year): evidence-policy §Reading OpenEvidence results.
5. For each parameter record: **value – source study (author, year, design, n, PMID/DOI) – checked
   against the abstract or not**. No parameter is used without a source. Every source study enters the
   project through `search_lit.py add` and `verify_refs.py`.

Use OpenEvidence `model="snow"` only when a review of many studies is needed (for example choosing an
MCID, or comparing event rates across several populations); then `timeout_sec=600`.

PubMed (or Europe PMC) and Consensus are always searched **alongside** the first source, not only as a
fallback. Prefer Vietnamese or Asian studies for baseline parameters (proportions, SD): add
`AND (Vietnam[Affiliation] OR Vietnam[tiab])` (evidence-policy §PubMed procedure).

## Template questions by parameter

Replace `{...}` with the specifics. Ask in English; ask for specific numbers and study names.

| Parameter needed | Template question |
|---|---|
| Control-group event rate (p1) | `What is the reported rate of {outcome} in {population} receiving {standard care / placebo} in randomized trials and cohort studies? Give specific percentages with study name, year, sample size and follow-up duration.` |
| Expected effect (RR/OR/HR/ARR) | `In RCTs of {intervention} vs {comparator} for {condition}, what was the effect on {outcome}? Report the point estimate (RR, OR, HR or absolute difference) with 95% CI, sample size and study name for each trial and any meta-analysis.` |
| Mean and SD of a continuous outcome | `What are the reported mean and standard deviation of {outcome measure} at {time point} in {population}? Give values for each treatment arm with study name, year and n.` |
| MCID / threshold of clinical importance | `What is the established minimal clinically important difference (MCID) for {outcome measure} in {population}? Cite the anchor-based or distribution-based studies that derived it.` |
| SD of paired differences | `In before-after or crossover studies measuring {outcome} in {population}, what is the standard deviation of within-subject change, or the test-retest correlation? Cite studies with n.` |
| Median survival / event rate over time | `What is the median {overall/progression-free} survival and the {1/2/5}-year event rate for {population} treated with {standard care}? Cite trials with n and follow-up.` |
| ICC for a cluster trial | `What intraclass correlation coefficients (ICC) have been reported for {outcome} clustered by {hospital/clinic/village} in {setting}? Cite the studies and the ICC values.` |
| Dropout / loss to follow-up | `What loss-to-follow-up or withdrawal rates were observed in trials of {intervention} in {population} with {duration} follow-up? Cite specific trials.` |
| Non-inferiority margin | `What non-inferiority margins have been used and justified in trials of {intervention class} for {outcome}? Cite trials and the rationale (e.g., fraction of active-control effect).` |
| Sensitivity / specificity (diagnostic) | `What sensitivity and specificity have been reported for {index test} versus {reference standard} in {population}? Cite studies with n, prevalence and 95% CI.` |
| Prevalence | `What is the prevalence of {condition} in {population, country/region}? Cite surveys with n and year.` |

State the scale and the time point in the question (Δ and SD must match the primary outcome's time
point; `sample-size-formulas.md` §Rules for choosing parameters).

## Reading what comes back

- OpenEvidence: read `answer_text` (clean markdown); `extracted_answer_raw` is not needed. An index `[n]`
  in the text ↔ `citations[n]`; the "Ref" column in OpenEvidence tables uses its own numbering, so match
  the source by author + year.
- When the evidence source gives several different values: the study **most similar to the author's
  population, setting and comparator** gives the main value; the other values go into the sensitivity
  table.

## Fallback when no source gives usable numbers

When none of the sources (the first evidence source, PubMed/Europe PMC, Consensus) gives usable numbers,
in this order: (1) ask the author whether they have pilot data or a reference study (including theses and
Vietnamese journals); (2) if there is still nothing, use an assumed value **and label it "ASSUMPTION – no
source yet" / "GIẢ ĐỊNH – chưa có nguồn"** in the parameter table, with a wider sensitivity table.

Rules for an assumed value under (2):
- General model knowledge may be used to choose a **plausible range** (for example "delirium after cardiac
  surgery in older people is usually 20–50%"), then the midpoint or the conservative end.
- **Never** write a study name, year, n, CI or specific number from memory into the Source column or the
  reference list. A citation appears only when a tool retrieved it in this session or the author supplied
  it.
- The justification paragraph must contain the sentence: "The values of {parameters} are assumptions and
  must be replaced by cited data before the protocol is locked."
