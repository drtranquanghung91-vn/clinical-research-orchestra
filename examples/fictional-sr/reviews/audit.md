# Audit: review

Date: 2026-11-23T03:21:11 · mode: offline (stored ledger statuses) · blocks: 0 · warns: 15

| Check | Code | Block | Warn |
|---|---|---|---|
| ledgers | E-REF | 0 | 0 |
| citations | E-REF | 0 | 0 |
| results numbers | E-NUM | 0 | 0 |
| analysis declarations | E-STAT | 0 | 0 |
| case report | E-CASE | 0 | 0 |
| screening and extraction | E-SCR | 0 | 1 |
| GRADE wording | E-GRADE | 0 | 4 |
| literature synthesis | E-LIT | 0 | 0 |
| consistency | E-CONS | 0 | 0 |
| prose density | P00 | 0 | 0 |
| guideline checklist | E-RG | 0 | 3 |
| sections and captions | E-FMT | 0 | 0 |
| identifiers | E-PHI | 0 | 2 |
| reviewer reports | E-REV | 0 | 5 |

## Cách sửa / How to fix

- `E-SCR`: bổ sung quyết định của người sàng lọc thứ hai, giải quyết bất đồng bằng dòng consensus, ghi lý do loại toàn văn, chạy lại screening.py counts và extract_check.py.
- `E-GRADE`: viết mức khẳng định theo độ chắc chắn GRADE (references/review/grade-wording.md).
- `E-RG`: bổ sung mục hướng dẫn còn thiếu hoặc ghi lý do không áp dụng; chạy lại reporting-guideline-checker.
- `E-PHI`: xoá hoặc ẩn danh định danh, rồi chạy lại audit.
- `E-REV`: chạy lại agent đánh giá trên bản thảo hiện tại.

## Findings

```text
E-SCR warn 04_data/sr/extraction-reviewer-a.csv:7: tamsett2020 / tử vong mọi nguyên nhân / 30 ngày / giả dược: events Reviewer A=26, Reviewer B=25
E-GRADE warn 06_writing/review/01-abstract.md:14: R-A1-001 has low certainty (GRADE); hedge the claim ('có thể', 'độ tin cậy thấp', 'mức chắc chắn thấp', …)
E-GRADE warn 06_writing/review/04-results.md:45: R-A1-001 has low certainty (GRADE); hedge the claim ('có thể', 'độ tin cậy thấp', 'mức chắc chắn thấp', …)
E-GRADE warn 06_writing/review/04-results.md:72: R-A1-001 has low certainty (GRADE); hedge the claim ('có thể', 'độ tin cậy thấp', 'mức chắc chắn thấp', …)
E-GRADE warn 06_writing/review/sof.md:1: R-A1-001 has low certainty (GRADE); hedge the claim ('có thể', 'độ tin cậy thấp', 'mức chắc chắn thấp', …)
E-RG warn 06_writing/review/01-abstract.md:9: item 2 is only partly reported: Abstract names the information source and gives a limitations statement, closing the two gaps flagged previously. Still missing the date the source was last searched (required by the PRISMA 2020 for Abstracts checklist); the date is given in Methods (03-methods.md:27, 23/11/2026) but not repeated in the abstract.
E-RG warn 06_writing/review/02-introduction.md:13: item 3 is only partly reported: Author deliberately omits rationale in light of existing disease-burden evidence because the intervention is fictional; author has reviewed this gap and chosen to keep the fictional framing as-is (final decision, not re-flagged as newly broken).
E-RG warn 06_writing/review/03-methods.md:27: item 7 is only partly reported: The full search strategy is referenced only in an external appendix file (02_evidence/sr/strings.md) rather than reproduced in the manuscript; author has reviewed this gap and chosen to keep the external-appendix approach as-is (final decision, not re-flagged as newly broken).
E-PHI warn 06_writing/review/03-methods.md:27: possible patient identifier: full date
E-PHI warn 06_writing/review/review.assembled.md:99: possible patient identifier: full date
E-REV warn reviews/citation-verifier.md:1: citation-verifier reviewed an earlier version of the review drafts (digest differs); rerun it if the content changed
E-REV warn reviews/statistical-reviewer.md:1: statistical-reviewer reviewed an earlier version of the review drafts (digest differs); rerun it if the content changed
E-REV warn reviews/reporting-guideline-checker.md:1: reporting-guideline-checker reviewed an earlier version of the review drafts (digest differs); rerun it if the content changed
E-REV warn reviews/scientific-editor.md:1: scientific-editor reviewed an earlier version of the review drafts (digest differs); rerun it if the content changed
E-REV warn reviews/consistency.md:1: consistency-auditor reviewed an earlier version of the review drafts (digest differs); rerun it if the content changed
```

G4: no block; the author may open G4 (`gate.py open . G4 --by "<name>"`).
