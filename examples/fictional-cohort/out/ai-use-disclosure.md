BẢN NHÁP - tác giả chỉnh sửa và chịu trách nhiệm / DRAFT - the author edits and is responsible

# Công bố sử dụng AI (luận văn và bài báo)

Dự án mô phỏng — Example author. Áp dụng cho cả hai sản phẩm viết từ kết quả đã khóa ở gate G3:
luận văn (`06_writing/thesis/` → `out/thesis.docx`) và bài báo riêng cho "Tạp chí Y học Mô phỏng"
(`06_writing/manuscript/` → `out/manuscript.docx`).

## Các bước chung cho cả hai sản phẩm (cùng một nền bằng chứng và một bộ kết quả đã khóa)

| Bước / Step | Công cụ / Tool | AI làm gì / What the AI did | Tác giả đã kiểm tra / What the author checked |
|---|---|---|---|
| Tìm kiếm tài liệu | `search_lit.py` (PubMed/Europe PMC) | Chạy các câu lệnh tìm kiếm, tổng hợp kết quả | Tác giả đã duyệt và chấp nhận bằng chứng ở giai đoạn `literature-search` (`decisions.md`, 2026-11-21) |
| Sàng lọc và thẩm định | Kỹ năng orchestra (critical-appraisal) | Thẩm định sơ bộ 6 tài liệu từ tóm tắt (ROBINS-E/NOS, AMSTAR 2, PROBAST+AI) | Tác giả đã duyệt phần thẩm định bằng chứng (`decisions.md`, 2026-11-21) |
| Phân tích số liệu | `analysis.py` / `crostats.py`, chạy cục bộ trên máy | Viết và chạy script phân tích theo SAP (A0–A6), và phân tích hậu kiểm A6 theo yêu cầu tác giả | Tác giả đã đọc toàn bộ `05_analysis/analysis-report.rendered.md` (kể cả mục A6) và tự khóa gate G3 (`decisions.md`, 2026-11-21) |

## Luận văn (`06_writing/thesis/`)

| Bước / Step | Công cụ / Tool | AI làm gì / What the AI did | Tác giả đã kiểm tra / What the author checked |
|---|---|---|---|
| Soạn luận văn | Vai trò orchestra (introduction/methods/discussion/conclusion/abstract; results-writing cho Chương 3) | Viết Đặt vấn đề, Chương 2, Chương 4, Kết luận, Kiến nghị, Phụ lục, Tóm tắt; Chương 1 và Chương 3 giữ nguyên bản tác giả đã duyệt trước | Tác giả tự điền 3 chỗ `[[TÁC GIẢ: …]]` trong `ch2-methods.md` (tài trợ, số quyết định đạo đức, văn bản Bộ Y tế) bằng chữ của mình, tự viết thêm `00-tom-tat.md`, xác nhận STROBE 6b là `na`, và tự sửa lại 2 câu bị gắn cờ trong `ch3-results.md` cùng 1 câu trong `ch1-literature-review.md` (`decisions.md`, 2026-11-22) |
| Làm tự nhiên văn phong | `prose-humanizer`, `lint_prose.py` | Chạy trên 6 file đã soạn mới (không áp dụng cho Chương 1/3 giữ nguyên); 1 sửa cơ học (bỏ `**đậm**` quanh nhãn trường trong `ch2-methods.md`) | [[AUTHOR: tác giả có tự đọc lại đoạn văn sau khi làm tự nhiên văn phong không]] |
| Kiểm tra | `verify_refs.py`, `check_numbers.py`, `consistency_audit.py`, `analysis_plan.py`, `guideline_checklist.py`, `audit.py` | Kiểm tra số liệu, trích dẫn, nhất quán, bảng kiểm STROBE | Tác giả ra lệnh mở gate G4 cho luận văn dựa trên audit tổng hợp này (0 khối lỗi, xem `reviews/audit.md`), 2026-11-22 |

## Bài báo (`06_writing/manuscript/`)

| Bước / Step | Công cụ / Tool | AI làm gì / What the AI did | Tác giả đã kiểm tra / What the author checked |
|---|---|---|---|
| Lập dàn ý | Kỹ năng orchestra (manuscript-writing) | Đề xuất dàn ý 7 phần, 3 bảng + 2 hình trong giới hạn tạp chí | Tác giả duyệt dàn ý trước khi viết văn xuôi (2026-11-22) |
| Soạn bài báo | Vai trò orchestra (introduction/methods/results/discussion/conclusion/abstract) | Viết mới hoàn toàn 7 phần (00-title đến 06-conclusion) từ ledger kết quả đã khóa, không chép lại luận văn | [[AUTHOR: tác giả đã đọc lại từng câu nào trước khi nộp]] |
| Làm tự nhiên văn phong | `lint_prose.py` | Không chạy `prose-humanizer` toàn bộ vì không có đoạn văn nào bị gắn cờ mẫu AI; chỉ 1 sửa cơ học (bỏ `**đậm**` ở nhãn trang bìa `00-title.md`) | — |
| Kiểm tra | `verify_refs.py`, `check_numbers.py`, `consistency_audit.py`, `analysis_plan.py`, `guideline_checklist.py`, `audit.py` | Kiểm tra số liệu, trích dẫn, nhất quán, bảng kiểm STROBE | Tác giả đọc `reviews/audit.md` của riêng bài báo (0 khối, 15 cảnh báo) và quyết định không chạy thêm 3 phân tích được đề nghị (`out/author-decisions.md`), rồi ra lệnh mở gate G4 cho cả hai sản phẩm dựa trên audit tổng hợp cuối cùng, 2026-11-22 |

## Nội dung công bố (theo khuyến cáo ICMJE, diễn giải không trích dẫn nguyên văn)

- Việc sử dụng AI được công bố khi nộp bài và trong văn bản: hỗ trợ soạn thảo ghi ở đây (hoặc phần
  lời cảm ơn/tuyên bố của từng sản phẩm), việc dùng AI hỗ trợ viết mã phân tích ghi ở phần Đối tượng
  và phương pháp/Phương pháp của từng sản phẩm.
- Tác giả chịu trách nhiệm về tính chính xác, toàn vẹn và nguyên bản của toàn bộ luận văn và bài báo,
  kể cả những phần có sự hỗ trợ của công cụ AI.
- Công cụ AI không phải là tác giả và không được liệt kê hay trích dẫn như một tác giả, ở cả hai sản
  phẩm.
- Không có dữ liệu định danh người bệnh nào được gửi cho công cụ AI: toàn bộ dữ liệu là dữ liệu mô
  phỏng, không có người bệnh thật (dự án minh hoạ).
- Tên và phiên bản mô hình: Claude (Anthropic), theo đúng cách ghi đã dùng trong
  `02_evidence/search-strategy.md` và `03_protocol/sap.md`; dự án không ghi số phiên bản cụ thể hơn,
  nên không ghi thêm ở đây.

## Nơi đặt công bố này

[[AUTHOR: chọn nơi đặt công bố sử dụng AI trong bản nộp — luận văn: sau Lời cam đoan hoặc trong Phụ
lục, theo quy định của cơ sở đào tạo; bài báo: phần Phương pháp hay phần Lời cảm ơn/Tuyên bố, theo
đúng yêu cầu của "Tạp chí Y học Mô phỏng"]]
