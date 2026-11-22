STATUS: PASS

FINDINGS
| code | location (file:line) | fix |
| --- | --- | --- |

All `[@id]` citations in `06_writing/review/*.md` (excluding `.rendered/.numbered/.humanized/.assembled`) resolve
to a ledger record in `ledgers/references.json` that is either `verify_refs.py 2026-11-23 VERIFIED`
(page2021, sterne2019, guyatt2008, inthout2016, veroniki2016, higgins2003) or `source: manual` with a `seen_in`
entry (varrow2017, quellin2019, tamsett2020, orbeck2021, lindqvar2022) — no E-REF. For the five records with a
stored abstract (page2021, guyatt2008, inthout2016, veroniki2016, higgins2003), every citing sentence in
`02-introduction.md`, `03-methods.md` and `05-discussion.md` matches the abstract's direction, population,
design and strength (method citations only: PRISMA reporting [@page2021], RoB 2 naming [@sterne2019] itself
unchecked below, GRADE naming [@guyatt2008], I² statistic [@higgins2003], prediction interval [@inthout2016],
REML as one of the between-study-variance methods compared by [@veroniki2016]) — no C-SCOPE or C-SUPPORT.

This round covers only prose edits to `01-abstract.md` (word-count trim, added search-source and limitations
clauses); that file carries no `[@id]` citation, so none of the edits touch anything checked here. No
citations were added, removed or reworded anywhere in `06_writing/review/` since the prior round.

GAPS
sterne2019 (RoB 2, cited in `02-introduction.md:7`, `03-methods.md:32,64`, `04-results.md:35` and elsewhere) —
ledger record has no stored abstract (`abstract: ""`); cannot compare the citing sentences against source
content. C-NOABS, unchanged from prior rounds; no fix available short of `verify_refs.py --write` finding an
abstract or the author replacing the citation.

varrow2017, quellin2019, tamsett2020, orbeck2021, lindqvar2022 (the five fictional trials, cited throughout
`04-results.md` and `05-discussion.md:59`) — manual records with no stored abstract; these are the author's own
fictional study records (`source: manual`, `seen_in` populated), so they are exempt from E-REF, but with no
abstract their citing sentences cannot be checked for scope or support. C-NOABS, unchanged from prior rounds;
not fixable since the trials are fictional and have no real abstract to store.

CONFLICTS
none

NEW-ANALYSIS: none
drafts-digest: review f97145f453e6a4d170cab9c7038c97c7c27a490bbe6b61ade01123dd564914d0
```scores
{"deliverable": "review", "citations": 1}
```
