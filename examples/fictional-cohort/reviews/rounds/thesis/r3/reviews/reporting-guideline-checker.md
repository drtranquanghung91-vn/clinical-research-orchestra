STATUS: FINDINGS

| code | location (file:line) | fix |
|---|---|---|
| 1a | (no draft) | No title page or abstract draft exists in `06_writing/thesis/`. Add an abstract (or title-page draft) naming the design ("đoàn hệ hồi cứu") so 1a can be checked. Deliberately out of this round's requested scope (decisions.md 2026-11-22), left for the author. |
| 1b | (no draft) | Same missing abstract draft. Add a balanced structured abstract summarising objectives, methods, main results (with CIs) and conclusion. Deliberately out of this round's requested scope, left for the author. |
| 13a | ch3-results.md:11 | The flow figure only shows eligible-cohort-to-analysed-model counts. Add counts for the initial pool before applying the four eligibility/exclusion criteria in ch2-methods.md 2.1, if those counts can ever be recovered. A known, permanent limitation of this simulated dataset; author has already decided not to fix it this round (decisions.md 2026-11-22). |
| 13b | ch3-results.md:11 | Only the "missing confounder data" exclusion is quantified. Report how many patients were excluded for each of the other three criteria (died during index stay; type 1/gestational/secondary diabetes; missing valid HbA1c; repeat admissions collapsed to one index admission). Same unfixed-by-choice status as 13a. |
| 13c | ch3-results.md:11 | Figure 3.1/Biểu đồ 3.1 is explicitly labelled by the authors as not a full STROBE flow diagram. Author already chose the minimal 2-box diagram option; accepted as a documented limitation, not fixed. |
| 22 | ch2-methods.md:169 | A "Tài trợ" subsection now exists but still carries an unfilled `[[TÁC GIẢ: ...]]` placeholder instead of the actual funding source and the funder's role. Author must replace the placeholder with the real statement (even "no external funding") before this item is satisfied. |

GAPS
- 6b (matching) is marked `na`: the design is an unmatched census cohort (ch2-methods.md:66), so matching criteria do not apply; only the author/committee can confirm no matched sub-design was intended.

CONFLICTS
- Items 13a-13c: a full STROBE flow diagram needs screening-stage counts that do not exist in this simulated project's extraction log; the author has already chosen (decisions.md 2026-11-22) to keep the minimal 2-box diagram and document the gap rather than invent counts — recorded here, not re-opened.
- Item 22: only the author knows the true funding source and the funder's role; the placeholder text cannot be filled in by this check.

Round 3 (final round) re-verification: only a non-STROBE-relevant reword happened in ch4-discussion.md §4.2/4.8 (fixing a causal-wording false positive, same facts/numbers; no line-count change in that file). All item locations were re-checked against the current drafts and are unchanged from round 2. `guideline_checklist.py` reported no quote-mismatch block, only the same 2 block (1a/1b absent) and 4 warn (13a/13b/13c/22 partial) findings as round 2, by the author's explicit, on-the-record choice to leave them unfixed this round.

drafts-digest: thesis eefc31e42500dbe9cf9594a32c21bbe771bc320b20a6124018556b0aa0834608
```scores
{"deliverable": "thesis", "guideline": 1}
```
