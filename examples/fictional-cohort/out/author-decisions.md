# Quyết định của tác giả

> Bản nháp do `worklog.py decisions` tạo. Tác giả đọc, ghi quyết định và chịu trách nhiệm; công cụ không quyết định thay tác giả.

## 1. Yêu cầu phân tích mới (chưa đưa vào bài)

- [luận văn, vòng 1, scientific-editor] none — all findings are wording/structure fixes, not missing analyses. — Quyết định của tác giả: …
- [bài báo, vòng 1, reporting-guideline-checker] add a labelled sensitivity analysis for the adjusted model (item 12e), for example re-fitting with an alternative missing-data rule or excluding the complete-case drop, to show the main OR is robust. — Quyết định của tác giả: …
- [bài báo, vòng 1, reporting-guideline-checker] tabulate exclusion counts per criterion (death, type 1/gestational/secondary diabetes, missing HbA1c, duplicate admission) from the screening log, if still available, for items 13a/13b. — Quyết định của tác giả: …
- [bài báo, vòng 1, reporting-guideline-checker] compute missing-value counts for each Table 1 variable (age, sex, comorbidity, insulin use, length of stay), for item 14b. — Quyết định của tác giả: …
- [bài báo, vòng 1, reporting-guideline-checker] compute a summary follow-up statistic (median follow-up time or total person-time before censoring) for item 14c. — Quyết định của tác giả: …

## 2. Giả định / Assumptions

- HbA1c lúc nhập viện được ghi nhận thường quy và đầy đủ trong hồ sơ bệnh án điện tử/HIS cho phần lớn người bệnh ĐTĐ type 2 nhập Khoa Nội tiết. (`01_question/question.md:16`)
- HIS 2021–2023 ghi nhận ngày nhập viện và chẩn đoán chính ICD-10 cho mọi lần nhập viện, đủ để xác định tái nhập viện (tại chính bệnh viện này) trong vòng 1 năm sau xuất viện (giả định của dự án mô phỏng, do tác giả xác nhận). (`01_question/question.md:18`)
- Dân số nghiên cứu là người lớn (≥ 18 tuổi), không phân biệt có hay không biến chứng cấp lúc nhập viện (sẽ làm rõ tiêu chuẩn loại trừ ở bước thiết kế đề cương). (`01_question/question.md:21`)
- Theo yêu cầu của tác giả (Example author, 2026-11-21): "tham số nào không có nguồn thì ghi GIẢ ĐỊNH và làm luôn". `02_evidence/gaps.md` (Gap 1) đã xác nhận: **không có nghiên cứu nào đo được tỷ lệ tái nhập viện 1 năm hoặc hiệu ứng của HbA1c ở đúng mốc 1 năm** cho ĐTĐ type 2 nói chung. Vì vậy, hai tham số quan trọng nhất của phần tính cỡ mẫu này — **(1) tỷ lệ tái nhập viện 1 năm ở nhóm tham chiếu (HbA1c < 7%)** và **(2) độ lớn hiệu ứng kỳ vọng (OR) giữa nhóm HbA1c > 9% và nhóm tham chiếu** — đều được ghi **GIẢ ĐỊNH**, không có trích dẫn. Đây là **giả định rủi ro nhất** của toàn bộ đề cương (đưa vào mục "cần xác nhận" ở cuối file). Theo mẫu đoạn văn chuẩn của `sample-size-formulas.md`: *"Các giá trị tỷ lệ tái nhập viện 1 năm ở nhóm tham chiếu và OR kỳ vọng là giả định, cần thay bằng số liệu có trích dẫn (ví dụ từ một khảo sát hồi cứu nhỏ trên hồ sơ thật) trước khi khoá đề cương chính thức."* (`03_protocol/sample-size.md:3`)

## 3. Miễn cổng (WAIVE)

- Không có.
