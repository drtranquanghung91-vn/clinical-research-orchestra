BẢN NHÁP - tác giả chỉnh sửa và chịu trách nhiệm / DRAFT - the author edits and is responsible

# AI-use disclosure — case report (fictional, illustrative)

This note describes where an AI tool (orchestra skills, running on [[AUTHOR: model name and
version]]) was used while preparing this fictional case report, and what the author checked. The
author edits this note and is responsible for its content and for the manuscript; the tool is not
an author and is not listed or cited as one.

## Table of steps

| Step | Tool | What the AI did | What the author checked |
|---|---|---|---|
| Search | `search_lit.py` (PubMed/Europe PMC/Crossref) | Searched for and retrieved 9 literature records by PMID/DOI for the introduction, discussion and similar-cases table | [[AUTHOR: what you checked]] |
| Screening and appraisal | — | Not applicable: this is a single case report, not a review; no screening or appraisal step was used | — |
| Analysis code | — | Not applicable: `case_facts.py` merged the author-supplied case values into the results ledger; no statistical analysis code was run | — |
| Drafting | orchestra case-front / case-presentation / case-discussion role briefs | Drafted `06_writing/case-report/00-title.md` through `11-consent.md` from the de-identified dossier and the results ledger | [[AUTHOR: what you checked]] |
| Humanizing | `prose-humanizer`, `lint_prose.py` | Measured the drafts for AI-sounding phrasing (0 pattern hits across all 12 files); no rewrite was needed or applied | — |
| Checking | `verify_refs.py`, `audit.py` (`check_numbers`, `consistency_audit.py`, `case_lint.py`, phi-guard) | Verified all 9 references (status VERIFIED, none retracted), checked every numeric value against the results ledger, checked cross-file consistency, de-identification and section structure | [[AUTHOR: what you checked]] |

## Statements

- AI use in preparing this case report is disclosed here and, where the venue requires it, should
  also be stated in the submission system and/or the manuscript (e.g. in the acknowledgements).
- The author is responsible for the accuracy, integrity and originality of every part of this
  report, including the parts an AI tool helped draft or check.
- An AI tool is not an author of this report and is not listed or cited as one.
- No real patient-identifiable data was sent to an AI tool: this is a fictional, illustrative case,
  and the drafts were additionally checked by `case_lint.py` and phi-guard for relative time, age
  ranges and identifiers (0 block findings).
- The model name and version used are [[AUTHOR: model name and version]] (fill in from your own
  records; not guessed here).

## Case report statement (CARE / P5)

The consent statement in `06_writing/case-report/11-consent.md` reproduces the author-supplied
wording and corresponds to the following line recorded in `decisions.md`:

> CONSENT: obtained written consent form for publication, signed by the patient (fictional)

De-identification (relative time only, no calendar dates; age ranges only, no exact ages; no names,
places, institution or record numbers) was checked by `case_lint.py` and phi-guard, with 0 block
findings in the final audit (`reviews/audit.md`, 2026-11-23).

The patient-perspective quotation in `10-patient-perspective.md` was written by the author directly,
as fictional first-person narration for this illustrative patient, and was not drafted by an AI tool
(see the dated note in `decisions.md`).

## Where this goes

[[AUTHOR: state where this disclosure is placed for your target venue — e.g. methods or
acknowledgements of a manuscript, or kept as a project record only, since this is a fictional
illustrative example]]
