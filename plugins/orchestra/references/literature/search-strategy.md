# Building the search strategy

Methods content by Amelia Le (co-author), adapted for clinical-research-orchestra. Translated from
`literature-evidence-research-vi/reference/search-strategy.md` (v3). Used by `literature-search` and
by `research-question` (scoping search). Tool procedures: `${CLAUDE_PLUGIN_ROOT}/references/evidence-policy.md`.
Every PMID below is an illustration from the source; re-find a paper through a tool before citing it.

## Nomenclature check (before every query)

1. Search Consensus and PubMed for the last 2 years:
   `{condition} AND (renamed OR "new name" OR nomenclature OR "formerly known as")`, and read the
   newest guideline or consensus statement.
2. A new name or new diagnostic criteria → the P block holds MeSH + old name `[tiab]` + new name
   `[tiab]` + new abbreviation. MeSH updates slowly; papers using the new name may carry a different
   MeSH heading.
3. Check: run `<PMID of a paper that uses the new name>[pmid] AND (P block)`; 0 results → the P block
   is still incomplete.
   MeSH drift: take 2–3 new-name papers from the search results and test their headings with
   `search_lit.py search '<PMID>[pmid] AND "<old heading>"[Mesh]'` (fetched records carry no MeSH field;
   1 result = indexed under it, 0 = not, or not yet indexed). Write one line in `search-strategy.md`:
   `MeSH drift: <old heading> → <new heading or none>; P block uses [tiab] for the new name`. Only
   headings a tool confirmed; never one from memory.
4. Example: PCOS → PMOS (*polyendocrine metabolic ovarian syndrome*, 2026): add
   `"polyendocrine metabolic ovarian syndrome"[tiab] OR PMOS[tiab]`; the meta-analysis PMID 42776991
   is indexed under MeSH "Metabolic Syndrome" (confirmed 2026-11-23 with
   `42776991[pmid] AND "Metabolic Syndrome"[Mesh]`: 1 hit; the same probe with "Polycystic Ovary Syndrome": 0 hits). Measure what is missed with
   `(new name) AND (I block) NOT (old P block)`: the GLP-1 RA in PMOS test case (Nov 2026) returned 4
   papers that the standard PCOS query missed; record that number in the search log.
5. Other frequent renamings (check the same way; never assume the list is complete): NAFLD → MASLD;
   changed diagnostic criteria (for example a new DSM, KDIGO or ADA version). The aim is the checking
   habit, not a list.
6. **Check intervention and exposure terms too, not only the condition.** Ambiguous or changing terms →
   list all variants and exclude stray meanings with `NOT`. Verified example (Nov 2026): "robotic" +
   cardiovascular returns robotic percutaneous coronary intervention (CorPath, R-One) as well as
   rehabilitation robots; 10 of the first 30 ClinicalTrials.gov trials were off topic. Add
   `NOT (percutaneous coronary[tiab] OR PCI[tiab] OR rehabilitation[tiab])` and read titles before
   counting. "Totally endoscopic" may or may not use a robot: separate the two when synthesising.
   AI: `"artificial intelligence" OR "machine learning" OR "deep learning" OR "computer vision" OR "neural network"`.
7. Topics with **AI, engineering or devices**: much work appears only in IEEE Xplore, arXiv or
   engineering conferences (MICCAI) and not in PubMed. Search them if a tool is available; otherwise
   record this under limitations ("IEEE/arXiv not searched").

## From PICO/PECO to concept blocks

1. Each component P, I/E, C, O is one block. Usually **P + I/E (+ O)** is enough; the C and O blocks
   often lose relevant papers, so add them when there are more than 500 results (**default**).
2. Each block: main MeSH term + free text (synonyms, abbreviations, brand names, British and American
   spellings).
3. OR inside a block, AND between blocks. Use full brackets.

## Common PubMed tags

| Tag | Meaning | Example |
|---|---|---|
| `[MeSH Terms]` | MeSH term (includes narrower terms) | `"Diabetes Mellitus, Type 2"[MeSH Terms]` |
| `[Majr]` | MeSH as major topic | `"Delirium"[Majr]` |
| `[tiab]` | Title and abstract | `delirium[tiab]` |
| `[ti]` + `[au]` + `[dp]` | Verify one paper (title words + first author + year) | `frailty[ti] AND overtreatment[ti] AND Smith[au] AND 2023[dp]` |
| `[pt]` | Publication type | `randomized controlled trial[pt]`, `meta-analysis[pt]`, `systematic review[pt]`, `practice guideline[pt]` |
| `[Affiliation]` | Author affiliation | `Vietnam[Affiliation]` |
| `[doi]` | Search by DOI | `10.1001/jama.2019.0234[doi]` |

Do not use the `*` wildcard (the tool refuses it); list variants instead
(`child OR children OR pediatric OR paediatric`).

## Worked example: delirium after cardiac surgery in older adults, dexmedetomidine

```
("Delirium"[MeSH Terms] OR delirium[tiab] OR "acute confusion"[tiab])
AND ("Cardiac Surgical Procedures"[MeSH Terms] OR "cardiac surgery"[tiab] OR CABG[tiab] OR "coronary artery bypass"[tiab] OR "valve surgery"[tiab])
AND ("Dexmedetomidine"[MeSH Terms] OR dexmedetomidine[tiab] OR Precedex[tiab])
AND ("Aged"[MeSH Terms] OR elderly[tiab] OR "older adults"[tiab] OR geriatric[tiab])
```

Variants to run:
- `... AND (systematic review[pt] OR meta-analysis[pt])`
- `... AND randomized controlled trial[pt]`
- Drop the intervention block and add `AND (incidence[tiab] OR prevalence[tiab] OR "risk factors"[MeSH Terms])`
  for epidemiology and risk factors
- `... AND (Vietnam[Affiliation] OR Vietnam[tiab] OR Vietnamese[tiab])`
- Asia: `AND (Asia[MeSH Terms] OR China[Affiliation] OR Japan[Affiliation] OR Korea[Affiliation] OR Thailand[Affiliation])`

## Questions for Consensus / OpenEvidence (English, specific)

- Epidemiology: "What is the incidence of postoperative delirium after cardiac surgery in patients aged 65 and older?"
- Effectiveness: "Does perioperative dexmedetomidine reduce postoperative delirium after cardiac surgery compared with propofol or placebo?"
- Associated factors: "What are the independent risk factors for delirium after cardiac surgery in older adults?"
- Measurement: "Which delirium assessment tools are validated after cardiac surgery (CAM-ICU, 3D-CAM)?"
- Guideline: "What do current guidelines recommend for prevention of postoperative delirium in older surgical patients?"
- Gap: "What are the main unanswered research questions about {topic}?"

## Search log (one row per query)

Kept in `02_evidence/search-strategy.md`.

| # | Date | Source | Query / question | Filters | Results | Kept |
|---|---|---|---|---|---|---|

## When results look wrong (thresholds are **defaults**)

| Situation | What to do |
|---|---|
| More than 500 papers | Add the O or C block; use `[Majr]`; limit publication type or years |
| Fewer than 10 papers | Drop a less important block; add synonyms; check `query_translation` to see whether PubMed understood the query |
| Off-topic results | Read `query_translation`: PubMed may map to the wrong MeSH ("cardiac surgery" → also "thoracic surgery"); add `[tiab]` to force the exact words |
