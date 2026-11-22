# Thông tin khác

## Đăng ký và đề cương

Tổng quan hệ thống này **chưa đăng ký** PROSPERO. Đây là một bài tập minh hoạ phần mềm, không phải một tổng
quan hệ thống thật, nên không nộp lên một đăng ký thử nghiệm thật; một bản nháp minh hoạ cùng cấu trúc PROSPERO
được viết tại `03_protocol/prospero.md` chỉ để minh hoạ phần mềm, không phải một hồ sơ đăng ký. Đề cương đầy đủ
ở `03_protocol/sr-protocol.md`, được khoá trước khi sàng lọc; không có sửa đổi nào so với đề cương đã khoá.

## Vai trò của trợ lý AI

Một trợ lý AI tạo gợi ý (include/exclude/maybe, kèm lý do) cho bước sàng lọc tiêu đề/tóm tắt, lưu tại
`02_evidence/sr/ai-suggestions.csv`. Gợi ý này không phải quyết định sàng lọc; quyết định ở mọi bước sàng lọc,
trích xuất và đánh giá nguy cơ sai lệch đều do hai người đánh giá độc lập (hư cấu) thực hiện, bất đồng giải
quyết bằng đồng thuận (xem Phương pháp).

## Tài trợ

Không có nguồn tài trợ. Đây là dự án minh hoạ phần mềm, không có nhà tài trợ và không có vai trò của nhà tài
trợ cần khai báo.

## Xung đột lợi ích

Tác giả không có xung đột lợi ích. Đây là tổng quan hư cấu để minh hoạ phần mềm, không nhận tài trợ.

## Đóng góp của tác giả

Example author (tác giả): xây dựng câu hỏi nghiên cứu và đề cương, viết bản thảo. Reviewer A và Reviewer B
(hư cấu, xem Phương pháp): sàng lọc tiêu đề/tóm tắt và toàn văn, trích xuất dữ liệu, đánh giá nguy cơ sai lệch
RoB 2 — mỗi bước độc lập, bất đồng giải quyết bằng đồng thuận.

## Phê duyệt đạo đức

Không áp dụng. Đây là dự án minh hoạ phần mềm trên dữ liệu hư cấu/mô phỏng, không có người tham gia nghiên cứu
thật và không thu thập dữ liệu người bệnh thật, nên không cần phê duyệt của hội đồng đạo đức.

## Khả năng tiếp cận dữ liệu, mã nguồn và các vật liệu khác

Toàn bộ dữ liệu mô phỏng, mã nguồn ledger và các tệp trung gian của bài viết này nằm trong thư mục dự án:
chiến lược tìm kiếm (`02_evidence/sr/strings.md`), nhật ký tìm kiếm (`02_evidence/sr/search-log.csv`), sàng lọc
(`02_evidence/sr/screening.csv`, `02_evidence/sr/ai-suggestions.csv`), trích xuất (`04_data/sr/extraction.csv`
và hai tệp của từng người đánh giá), nguy cơ sai lệch (`04_data/sr/rob.csv`), kết quả phân tích gộp và GRADE
(`05_analysis/meta/`, `05_analysis/output/`), và ledger kết quả dùng để tạo mọi số liệu trong bài viết này
(`ledgers/results-ledger.json`).
