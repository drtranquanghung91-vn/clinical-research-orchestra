# Audit: thesis, manuscript

Date: 2026-11-22T20:44:03 · mode: offline (stored ledger statuses) · blocks: 0 · warns: 32

| Check | Code | Block | Warn |
|---|---|---|---|
| ledgers | E-REF | 0 | 0 |
| citations | E-REF | 0 | 0 |
| results numbers | E-NUM | 0 | 0 |
| analysis declarations | E-STAT | 0 | 0 |
| literature synthesis | E-LIT | 0 | 0 |
| consistency | E-CONS | 0 | 0 |
| prose density | P00 | 0 | 1 |
| guideline checklist | E-RG | 0 | 8 |
| sections and captions | E-FMT | 0 | 0 |
| identifiers | E-PHI | 0 | 14 |
| reviewer reports | E-REV | 0 | 9 |

## Cách sửa / How to fix

- `P15`: giảm mẫu văn phong bị đánh dấu (prose-humanizer).
- `E-RG`: bổ sung mục hướng dẫn còn thiếu hoặc ghi lý do không áp dụng; chạy lại reporting-guideline-checker.
- `E-PHI`: xoá hoặc ẩn danh định danh, rồi chạy lại audit.
- `E-REV`: chạy lại agent đánh giá trên bản thảo hiện tại.

## Findings

```text
P15 warn 06_writing/thesis/ch2-methods.md:169: "**Tài trợ:**" (4 hits / 100 words)
E-RG warn 06_writing/thesis/ch3-results.md:11: item 13a is only partly reported: Chỉ có 2 mốc số liệu (đủ tiêu chuẩn chọn mẫu và số đưa vào mô hình hiệu chỉnh); không có số liệu sàng lọc/loại trừ ban đầu theo từng tiêu chuẩn vì dữ liệu mô phỏng không ghi nhận các mốc đó.
E-RG warn 06_writing/thesis/ch3-results.md:13: item 13b is only partly reported: Chỉ giải thích lý do loại khỏi mô hình hiệu chỉnh (thiếu biến nhiễu); không có lý do loại ở giai đoạn sàng lọc/đủ tiêu chuẩn ban đầu vì số liệu đó không được ghi nhận trong dữ liệu mô phỏng.
E-RG warn 06_writing/thesis/ch3-results.md:9: item 13c is only partly reported: Có hình nhưng tác giả tự ghi rõ đây là sơ đồ rút gọn, không phải lưu đồ STROBE đầy đủ (dòng 11 cùng file).
E-RG warn 06_writing/manuscript/04-results.md:12: item 13a is only partly reported: Chỉ có 2 mốc số liệu (mẫu mô tả và mẫu mô hình hiệu chỉnh); không có số liệu đủ điều kiện/sàng lọc ban đầu theo từng bước; tác giả tự ghi nhận hạn chế này.
E-RG warn 06_writing/manuscript/03-methods.md:12: item 13b is only partly reported: Tiêu chuẩn loại được liệt kê ở Phương pháp nhưng không có số lượng loại theo từng lý do, trừ số thiếu biến thời gian mắc ĐTĐ (27, 2,5%) nêu ở Kết quả.
E-RG warn 06_writing/manuscript/04-results.md:10: item 13c is only partly reported: Có sơ đồ (Hình 2, F4.png) nhưng tác giả nêu rõ đây không phải sơ đồ sàng lọc STROBE đầy đủ (dòng kế tiếp).
E-RG warn 06_writing/manuscript/04-results.md:7: item 14b is only partly reported: Chỉ số liệu thiếu của biến 'thời gian mắc ĐTĐ' (27, 2,5%) được định lượng; không có số liệu thiếu cho các biến khác trong Bảng 1 (tuổi, giới, bệnh đồng mắc, dùng insulin, thời gian nằm viện).
E-RG warn 06_writing/manuscript/03-methods.md:7: item 14c is only partly reported: Phương pháp nêu theo dõi cố định 365 ngày, nhưng phần Kết quả không báo cáo tóm tắt tổng thời gian theo dõi/person-time (ví dụ thời gian theo dõi trung vị trước khi kiểm duyệt).
E-PHI warn 06_writing/thesis/ch2-methods.md:17: possible patient identifier: full date
E-PHI warn 06_writing/thesis/ch2-methods.md:40: possible patient identifier: full date
E-PHI warn 06_writing/thesis/ch2-methods.md:41: possible patient identifier: full date
E-PHI warn 06_writing/thesis/ch2-methods.md:67: possible patient identifier: full date
E-PHI warn 06_writing/thesis/thesis.assembled.md:315: possible patient identifier: full date
E-PHI warn 06_writing/thesis/thesis.assembled.md:338: possible patient identifier: full date
E-PHI warn 06_writing/thesis/thesis.assembled.md:339: possible patient identifier: full date
E-PHI warn 06_writing/thesis/thesis.assembled.md:365: possible patient identifier: full date
E-PHI warn 06_writing/manuscript/03-methods.md:7: possible patient identifier: full date
E-PHI warn 06_writing/manuscript/03-methods.md:8: possible patient identifier: full date
E-PHI warn 06_writing/manuscript/04-results.md:5: possible patient identifier: full date
E-PHI warn 06_writing/manuscript/manuscript.assembled.md:108: possible patient identifier: full date
E-PHI warn 06_writing/manuscript/manuscript.assembled.md:109: possible patient identifier: full date
E-PHI warn 06_writing/manuscript/manuscript.assembled.md:163: possible patient identifier: full date
E-REV warn reviews/rounds/thesis/r3/reviews/citation-verifier.md:1: citation-verifier reviewed an earlier version of the thesis drafts (digest differs); rerun it if the content changed
E-REV warn reviews/rounds/thesis/r3/reviews/statistical-reviewer.md:1: statistical-reviewer reviewed an earlier version of the thesis drafts (digest differs); rerun it if the content changed
E-REV warn reviews/rounds/thesis/r3/reviews/scientific-editor.md:1: scientific-editor reviewed an earlier version of the thesis drafts (digest differs); rerun it if the content changed
E-REV warn reviews/rounds/thesis/r3/reviews/consistency.md:1: consistency-auditor reviewed an earlier version of the thesis drafts (digest differs); rerun it if the content changed
E-REV warn reviews/citation-verifier.md:1: citation-verifier reviewed an earlier version of the manuscript drafts (digest differs); rerun it if the content changed
E-REV warn reviews/statistical-reviewer.md:1: statistical-reviewer reviewed an earlier version of the manuscript drafts (digest differs); rerun it if the content changed
E-REV warn reviews/rounds/manuscript/r3/reviews/reporting-guideline-checker.md:1: reporting-guideline-checker reviewed an earlier version of the manuscript drafts (digest differs); rerun it if the content changed
E-REV warn reviews/scientific-editor.md:1: scientific-editor reviewed an earlier version of the manuscript drafts (digest differs); rerun it if the content changed
E-REV warn reviews/consistency.md:1: consistency-auditor reviewed an earlier version of the manuscript drafts (digest differs); rerun it if the content changed
```

G4: no block; the author may open G4 (`gate.py open . G4 --by "<name>"`).
