# Evidence policy

Shared by every orchestra skill that touches the literature. It states which sources to use, in
what order, how a reference earns its place in the ledger, and how to read tool output safely.

## Source order
1. OpenEvidence MCP, if installed and the user has not excluded it.
2. PubMed via `search_lit.py search` (E-utilities).
3. Europe PMC via `search_lit.py search --source europepmc` (also open-access full text).
4. Crossref via `search_lit.py doi` for DOIs without a PMID.

Optional extras: Consensus (natural-language search, no PMID/DOI) and ClinicalTrials.gov
(`search_lit.py trial <NCT>`, or a trial-registry MCP when connected).
If the user names one source as the only one allowed (for example "chỉ dùng OpenEvidence"), use
only that source and record what could not be checked as a limitation.

## Source roles
| Source | Use it for | Returns | Weak point |
|---|---|---|---|
| PubMed (`search_lit.py search/fetch`, or a PubMed MCP: `search_articles`, `get_article_metadata`, `lookup_article_by_citation`, `find_related_articles`, `get_full_text_article`) | Systematic search with MeSH plus Boolean; counting hits; verifying every reference (PMID, DOI) | The search call returns only PMIDs, `total_count` and `query_translation`; a metadata call is needed for title, abstract, DOI and publication type | No ranking by quality |
| Consensus (`search`) | Natural-language questions; quickly surfaces key SR/MA/RCT with abstract and citation count. Without a connected Consensus account it returns 3 papers per call (checked Nov 2026; connected free or paid accounts return more) | Title, consensus.app link, authors, year, journal, abstract; **no PMID/DOI** | Must be verified through PubMed before it enters a reference list |
| OpenEvidence (`oe_auth_status`, `oe_ask`, `oe_article_wait`, `oe_citations_get`) | Cited clinical synthesis: baseline rates, MCID, guidelines, "what is known" | Text with `[n]` markers plus citations (DOI/PMID when available) | Geo-blocked in some regions (VPN needed); the answer is a secondary synthesis |
| ClinicalTrials.gov (optional: `search_trials`, `get_trial_details`, `analyze_endpoints`) | Ongoing or unpublished trials, how endpoints and eligibility are defined | NCT number, design, outcomes, status | Registered studies only |
| Europe PMC and Crossref (via `search_lit.py`) | Open-access full text; DOI lookup when there is no PMID | Metadata and, where open, full text | Coverage and fields differ from PubMed |

## Tool access
- Call tools by **name suffix**; the server prefix differs between machines (for example
  `mcp__<uuid>__search_articles` or `mcp__plugin_healthcare_PubMed__search_articles`).
- If a tool is not in the list, run `ToolSearch` with keywords (`pubmed search_articles`,
  `consensus search`, `openevidence oe_ask`) before concluding it is absent.
- Read tool output that was saved to a file with `python -I -X utf8 script.py`. Windows defaults
  to cp1252 and breaks Vietnamese text and characters such as ø, ä, é. Do not rely on
  `PYTHONIOENCODING`: isolated mode (`python -I`) ignores every `PYTHON*` variable.

## Identifiers
- A work may be cited only if it is in `ledgers/references.json`, added by `search_lit.py add`
  (or by a lookup tool in this session), and checked by `verify_refs.py --write`.
- Never type a PMID or DOI from memory. If a lookup fails, say so; do not substitute.
- Knowledge recalled from the model's own memory never goes into a reference list. It may serve as
  a search keyword, and the hit is then verified as below.
- Numbers (rates, RR, CI, n) quoted in a document must come from an abstract, metadata or full text
  returned in this session, not from memory.
- `RETRACTED`, `NOT_FOUND` and `MISMATCH` records are not cited until resolved. Check for
  retraction before citing: `(<pmid1>[pmid] OR ...) AND (Retracted Publication[pt] OR Retraction
  of Publication[pt] OR "Expression of Concern"[pt])`, at most 10 PMIDs per query.

## Reading level
Record what was read: abstract only → claims status `verified-abstract`; full text → `verified-fulltext`.
Never describe methods or subgroup results that only the full text contains when you read the abstract only.

## Nomenclature check (step 0 of every search)
Before searching: list current and former names of the condition and intervention, MeSH terms and
their recent changes, Vietnamese and English terms, abbreviations. Search old and new names.
Regression case: PCOS was renamed PMOS (2026) and a 2026 PLoS Medicine meta-analysis (Olalere et al.,
doi:10.1371/journal.pmed.1004887) was indexed under "Metabolic Syndrome", so a standard PCOS query
missed it.

## Search plans
Separate planning from writing. Targeted searches find one named primary source (a trial, a scale,
a guideline). Exploratory searches return ranked lists for context. Record both in
`02_evidence/search-strategy.md` with PRISMA-S fields (databases, dates, full strings, limits, counts).

## PubMed procedure
1. Build the query from concept blocks and run it with 20–50 results. Log `total_count` and
   `query_translation` in the search log.
2. Fetch metadata in batches of **at most 8 PMIDs**; larger batches return output so long that it is
   saved to a file.
3. Filter by publication type with `AND (systematic review[pt] OR meta-analysis[pt])` or
   `AND randomized controlled trial[pt]`, or limit by year.
4. The tool refuses queries with **more than 20 Boolean operators** (`INVALID_QUERY`). Long MeSH
   blocks: split into several queries and merge the PMIDs. Retraction checks: at most 10 PMIDs per
   query.
5. Vietnam context: add `AND (Vietnam[Affiliation] OR Viet Nam[Affiliation] OR Vietnam[Title/Abstract])`.
   An `[Affiliation]` match does not prove the work was done in Vietnam (Vietnamese authors abroad,
   international collaborations): read the abstract before placing a study in the "Vietnam" column.
6. `find_related_articles` ignores `max_results` and returns many PMIDs ranked by similarity: look at
   about the first 10 and expect little.
7. `lookup_article_by_citation` can return the PMID in the `key` field and its own key in `pmid`:
   re-check with a metadata call before use.
8. PubMed requires attribution: say that the data came from PubMed and give the DOI link
   `https://doi.org/<doi>`.

## Intermediate summary layer
When a mod or hook (for example an input router) shortens tool output with a helper model instead of
returning the raw JSON, the summary is for screening only.
- Numbers used as **sample-size parameters, primary results or evidence-table entries** are re-read
  from the raw JSON (the file the hook's note points to) or re-fetched with 1–2 PMIDs.
- Never copy the helper model's own comments ("possible transcription error…") as if they were the
  paper's content.
- While such a layer is active, run metadata lookups **one at a time, never in parallel**: raw JSON
  files can be named by the second, so two calls in the same second overwrite each other and the raw
  data of one batch is lost (verified Nov 2026). If a file is lost, call the needed PMIDs again.

## Consensus procedure
1. Search with a specific English question and **no filters** unless the user asks or SR/RCT are
   needed (then `study_types`). At most 3 calls in parallel; on a rate limit wait 30 seconds.
2. When quoting Consensus in a chat answer: number the items, link the exact URL returned, and copy
   the upgrade or registration notice the tool returns **verbatim** at the end of the chat message.
   Never put that notice in a protocol or review file.

## OpenEvidence procedure
1. Call `oe_auth_status` first.
   - `blocked="geo"`: tell the user to turn on a VPN; do **not** ask for a login again. Continue
     with PubMed (and Consensus if available); do not wait.
   - `authenticated=false` without geo-block: the user must run `npm run login:session` in the
     openevidence-mcp folder; continue with other sources.
   - **Any other error** (for example `browserType.launchPersistentContext … has been closed`, the
     MCP browser fails to start, connection timeout): retry `oe_auth_status` **once**. If it still
     fails, tell the user in one sentence (close any Chrome windows using the openevidence-mcp
     profile, or restart the MCP), log "OpenEvidence: technical failure" in the search log and
     continue with the other sources without waiting.
2. `oe_ask` with `model="sackett"` (comprehensive answer to a complex question, about 1 minute,
   about 10 citations) and `wait_for_completion=false`, then `oe_article_wait` with
   `timeout_sec=240` (on timeout call it once more). If the tool reports "option was not found in
   the model menu" (it sometimes happens when the MCP browser has not finished loading the menu,
   especially on the first call after turning on a VPN): retry `sackett` once; if it still fails use
   `model="osler"` (fast, direct) and note that in the search log.
3. `model="snow"` only for deep multi-study reviews (4–7 minutes, 30–60 citations, `timeout_sec=600`).
4. Ask in English and request specific figures with study name, year and n. Put no patient
   identifiers in the question.

### Reading OpenEvidence results
- `oe_article_wait` already returns `answer_text` (markdown) and `citations[]` (authors, title,
  `url`, year). A `url` of the form `https://pubmed.ncbi.nlm.nih.gov/<PMID>` gives the PMID; a
  `doi.org/…` URL gives the DOI. `oe_citations_get` is only needed for BibTeX (which often lacks DOIs).
- A `[n]` marker in the **text** matches `citations[n]`. The "Ref" column inside an OpenEvidence
  **table** uses the table's own numbering and does **not** match the global list: assign sources to
  table rows by first author and year, never by number.
- `year` in a citation may be the epub year (one year before print). Take year, volume and pages
  from PubMed metadata, not from OpenEvidence.
- An OpenEvidence answer is a secondary synthesis. A figure used as a **sample-size parameter** or a
  **main conclusion** is checked against the PubMed abstract (metadata call on the PMID from the
  `url`); a figure not found in the abstract is written "per OpenEvidence, not checked against the
  abstract".

## Verifying references (required before anything enters the reference list)
Every reference needs a **PMID or DOI that a tool returned in this session**.

| Where the paper came from | How to verify |
|---|---|
| PubMed metadata call | Verified |
| Consensus | Search PubMed with 4–6 distinctive title words tagged `[ti]`, first author surname `[au]` and year `[dp]`, for example `dexmedetomidine[ti] AND delirium[ti] AND cardiac[ti] AND Zhong[au] AND 2024[dp]`, then fetch metadata and match title, first author and year. Do **not** use the whole title in quotes with `[Title]` (it often returns 0 although the paper is in PubMed). Still 0: drop words and keep `<first author>[au] AND <year>[dp] AND <1 distinctive word>[tiab]`; with a DOI search `<doi>[doi]` |
| OpenEvidence citation with a PubMed/DOI link | PMID from the `url`, then a metadata call; or search `<doi>[doi]` |
| OpenEvidence citation without an ID | `lookup_article_by_citation` (journal, year, first author, page) or a title search |
| Consensus paper not in PubMed (journal not indexed, Vietnamese journals) | Keep it with authors, year, journal and the consensus.app URL exactly as returned, and tag the entry `[not verified in PubMed]`. Such entries must not exceed 20% of the list and must not be the only source for a key figure (sample-size parameter, main conclusion). Consensus returns no author names for some papers; a paper without author names is not put in the list |
| Trial registration (NCT…) | Verified if `search_lit.py trial` or a registry tool (`search_trials`, `get_trial_details`) returned it. Cite as `ClinicalTrials.gov. {Trial name}. NCT…. Accessed {date}. https://clinicaltrials.gov/study/NCT…` |
| Guideline, Ministry of Health document, book | See "Citing sources" below |
| Recalled from model memory | **Not in the list.** May be used as a search keyword, then verified as above |

## Citing sources when several tools are combined
- **In files** (review, protocol): one style only, numbered Vancouver `[n]`; each entry ends with
  `doi: …. PMID: ….`. No consensus.app link in the list, except the one allowed exception above.
- **In chat answers**: still numbered `[n]`. End the answer with one line "Sources searched:
  PubMed (DOI links in the list), Consensus, OpenEvidence", naming those actually used. If Consensus
  was used, its upgrade/registration notice goes on the very last line of the chat message.
- Order at the end of a chat message: (1) the single confirming question, including any offer to
  save a file; (2) the "Sources searched" line; (3) the Consensus notice, if any.
- Publication year in Vancouver: the year in `publication_date` that PubMed metadata returns (it may
  be the epub year; no tool gives the print year separately, and readers can look it up in PubMed).
  Never take the year from OpenEvidence or Consensus when PubMed has it. If pages are missing use the
  article number from the metadata or the DOI.
- **Guideline, Ministry of Health document or book** not in PubMed: give organisation, title, year,
  decision number (if any) and the official URL taken from a tool. With no URL from a tool, write
  `[not verified – user must check the original]`. Never quote a specific number (threshold, dose)
  from a guideline whose text you could not read.

## When no source works
State which source failed and how, and use the ones that remain. If none remains, still do the
methodological reasoning, but label every figure and every claim about the literature
**"ASSUMPTION – no source"** and leave the reference list empty with the sentence "To be looked up
again when the MCP works".

## Evidence hierarchy for quick appraisal
1. Guideline based on systematic reviews (name the organisation and year)
2. SR/MA of RCTs
3. RCT
4. SR/MA of observational studies
5. Prospective cohort
6. Retrospective cohort, case-control
7. Cross-sectional, case series, case report
8. Expert opinion, narrative review

Also note year of publication, population (Asian/Vietnamese or not), sample size, and obvious risk of
bias (no blinding, large loss to follow-up, no confounder adjustment).

The hierarchy is only a starting point: a high-risk-of-bias RCT can be less trustworthy than a
well-done cohort. Confidence in each study comes from a design-specific appraisal tool (use the Skill
tool with `critical-appraisal`, when installed); certainty of the whole body of evidence comes from GRADE.

## Self-appraisal gate
Before sending a research question, review, protocol or sample size, answer five questions
(Ogden 2019, ch. 5) and fix every "no":
1. Am I allowed to say this (do the design and data permit that conclusion)?
2. Does the conclusion match what was done and found?
3. What would it take to really know it?
4. Can it be known (measurable, enough people, enough time)?
5. Is the conclusion fully proven, or do other explanations remain (chance, bias, confounding,
   reverse causation)?

## Basis
The self-appraisal gate and the source-use rules draw on these books and course material:
- Nguyễn Văn Tuấn. Cẩm nang nghiên cứu khoa học: Từ ý tưởng đến công bố. 2018.
- Ogden J. Thinking Critically About Research: A Step by Step Approach. Routledge; 2019.
- Gruwell C, Ewing R. Critical Thinking in Academic Research. 2nd ed. 2023.
- Choosing & Using Sources: A Guide to Academic Research. Ohio State University Libraries.
- Course slides: Critical Thinking in Medical Research (Modules 1–7).
