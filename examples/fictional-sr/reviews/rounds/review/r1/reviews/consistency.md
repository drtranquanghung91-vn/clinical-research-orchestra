STATUS: PASS
FINDINGS
| code | location (file:line) | fix |
|---|---|---|

No E-CONS findings: `consistency_audit.py .` returned "0 block, 0 warn" (exit 0).

Fresh full re-check after the author's abstract-only edit. The two new sentences in
`06_writing/review/01-abstract.md:8-9` ("tệp xuất mô phỏng (\"Simulated database\"), chạy một lần") and
`01-abstract.md:21` ("không đánh giá được sai lệch công bố") match the authoritative wording in
`03_protocol/sr-protocol.md:67,97-101`, `06_writing/review/03-methods.md:25-27,99-101`, and
`06_writing/review/05-discussion.md:44-45,67-69` (single simulated-export source, run once; publication bias
not tested because k<10). Timepoint "tử vong mọi nguyên nhân...30 ngày" is worded identically in
`03_protocol/sr-protocol.md:45,57,97`, `03-methods.md:18,59,71`, `04-results.md`, and the abstract. All
abstract numbers (5 trials; 1785 participants = 298+438+192+615+242 from
`ledgers/results-ledger.json` R-A1-011..015; RR 0.6553→0.66, CI 0.4573–0.9392→0.46–0.94; I²
54.17→54.2%; prediction interval 0.2153–1.9946→0.22–1.99; subgroup p 0.006439→0.006) round correctly
from `ledgers/results-ledger.json` (R-A0-010, R-A1-001, R-A1-003, R-A1-005, R-A2-001) and agree with
`06_writing/review/review.assembled.md` (timestamp newer than every source chapter including the edited
abstract; no unresolved `{{...}}` placeholders remain). GRADE certainty "thấp" matches `sof.md`.

GAPS     Abstract word count (≈264 words in the assembled text, counting labels, excluding HTML comments)
         exceeds the 250-word cap the author mentioned; no documented house limit exists inside the
         project files (protocol/decisions/SAP) to confirm whether labels or comment markers should be
         excluded from that count, so this is not raised as a finding — ask the author which counting
         rule applies. `review.draft.docx` is binary and was not diffed; only `review.assembled.md` was
         checked for currency.
CONFLICTS None found.

drafts-digest: review f97145f453e6a4d170cab9c7038c97c7c27a490bbe6b61ade01123dd564914d0

```scores
{"deliverable": "review", "consistency": 2}
```
