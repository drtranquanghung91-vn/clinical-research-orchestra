**BẢN NHÁP - tác giả chỉnh sửa và chịu trách nhiệm / DRAFT - the author edits and is responsible**

# Công bố việc sử dụng AI / AI-use disclosure

Bài viết: tổng quan hệ thống và phân tích gộp (hư cấu) — "Thuốc X và tử vong 30 ngày ở người lớn nhập viện vì
bệnh nội khoa cấp" (deliverable `review`). Dự án minh hoạ phần mềm; năm thử nghiệm đưa vào và hai người đánh
giá (Reviewer A, Reviewer B) là hư cấu.

## Bảng các bước / Table of steps

| Bước / Step | Công cụ / Tool | AI làm gì / What the AI did | Tác giả đã kiểm tra / What the author checked |
|---|---|---|---|
| Tìm kiếm / Search | `search_lit.py` (PubMed/Europe PMC, Crossref) | Tìm và lấy định danh (PMID/DOI) cho 6 tài liệu phương pháp luận thật (PRISMA 2020, RoB 2, GRADE, I²/khoảng dự đoán, REML); không dùng để tìm năm thử nghiệm đưa vào (nguồn duy nhất cho các thử nghiệm là một tệp xuất mô phỏng do tác giả tự chạy, không qua AI). | [[TÁC GIẢ: những gì anh đã kiểm tra]] |
| Sàng lọc và thẩm định / Screening and appraisal | vai `screen-suggest` (orchestra) | Đưa ra gợi ý include/exclude/maybe cho 20 bản ghi ở bước sàng lọc tiêu đề/tóm tắt, kèm lý do, lưu tại `02_evidence/sr/ai-suggestions.csv`. AI **không** quyết định sàng lọc ở bất kỳ bước nào. | [[TÁC GIẢ: những gì anh đã kiểm tra]] |
| Trích xuất dữ liệu và RoB 2 / Extraction and risk of bias | — | Không có bản dự thảo AI nào (không dùng vai `extract-draft`/`rob-draft`) được ghi nhận cho dự án này. AI **không** quyết định giá trị trích xuất hay nhận định RoB 2 ở bất kỳ miền hay thử nghiệm nào. | [[TÁC GIẢ: những gì anh đã kiểm tra]] |
| Mã phân tích / Analysis code | `meta.py`, `grade.py` (Python, thư viện chuẩn) | Tính RR gộp (mô hình hiệu ứng ngẫu nhiên, REML), τ², I², khoảng dự đoán, phân tích dưới nhóm, phân tích độ nhạy, và chứng cứ GRADE từ dữ liệu đã trích xuất. Không dùng R/metafor (`meta.py r-check` không chạy). | [[TÁC GIẢ: những gì anh đã kiểm tra]] |
| Viết bản thảo / Drafting | vai `review-systematic` và các vai P4 (đặt vấn đề, phương pháp/kết quả, bàn luận, kết luận, tóm tắt) (orchestra) | Soạn 8 file bản thảo (`06_writing/review/00-title.md` … `07-other-information.md`); mọi số liệu lấy qua placeholder `{{R-…}}` từ ledger kết quả, mọi trích dẫn qua `[@id]` từ `ledgers/references.json`. | [[TÁC GIẢ: những gì anh đã kiểm tra]] |
| Làm tự nhiên văn phong / Humanizing | — | Không chạy một bước humanize riêng (skill `prose-humanizer`); văn bản đạt điểm "prose" tối đa (2/2, 5 lượt khớp mẫu / 4592 từ) ở `worklog.py score . review --round 1` mà không cần bước này. | [[TÁC GIẢ: những gì anh đã kiểm tra]] |
| Kiểm tra / Checking | `verify_refs.py`, `check_numbers.py`, `consistency_audit.py`, `guideline_checklist.py`, `audit.py` | Kiểm trích dẫn (11/11 ở trạng thái VERIFIED hoặc MANUAL hợp lệ, 0 citation finding), số liệu (0 E-NUM block ở bản cuối), nhất quán số liệu/thuật ngữ (0 E-CONS), checklist PRISMA 2020 (0 absent item). `audit.py . review` cuối cùng: 0 block, 15 warn. | [[TÁC GIẢ: những gì anh đã kiểm tra]] |

## Tuyên bố / Statements

- Việc sử dụng AI được công bố khi nộp/công bố và trong bản thảo: hỗ trợ sàng lọc được ghi ở mục "Vai trò của
  trợ lý AI" (`06_writing/review/07-other-information.md`); hỗ trợ phân tích được ghi ở Phương pháp
  (`06_writing/review/03-methods.md`).
- Tác giả chịu trách nhiệm về tính chính xác, toàn vẹn và nguyên bản của mọi phần của bài viết, kể cả những
  phần có sự hỗ trợ của công cụ AI.
- Công cụ AI không phải là tác giả và không bao giờ được liệt kê hay trích dẫn như một tác giả.
- Không có dữ liệu định danh người bệnh nào được gửi cho công cụ AI: toàn bộ dữ liệu trong dự án này là dữ liệu
  mô phỏng/hư cấu, không có người tham gia nghiên cứu thật.
- Tên và phiên bản mô hình AI đã dùng: [[TÁC GIẢ: tên và phiên bản mô hình AI đã dùng]].

## Nơi đặt công bố này / Where it goes

Theo tạp chí/nơi công bố dự kiến: trong Phương pháp hoặc phần Lời cảm ơn/Khai báo của bản thảo, kèm hoặc thay
cho mục "Vai trò của trợ lý AI" đã có trong `06_writing/review/07-other-information.md`.

---
Bản nháp do skill tạo từ `02_evidence/sr/ai-suggestions.csv`, `ledgers/references.json`, `reviews/worklog.json`
và `reviews/audit.json`. Tác giả đọc, điền các mục `[[TÁC GIẢ: …]]` và chịu trách nhiệm; không có skill nào
đánh dấu tài liệu này là bản cuối.
