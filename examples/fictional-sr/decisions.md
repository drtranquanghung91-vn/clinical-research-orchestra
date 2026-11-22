# Decisions and assumptions

Dated entries, newest last. Gate waivers use a line starting `WAIVE G<n>:` followed by the reason.

2026-11-23: Tác giả quyết định (phản hồi yêu cầu NEW-ANALYSIS của statistical-reviewer, bài tổng quan review,
vòng 1): quy định "khoảng dự đoán 95% khi k ≥ 3 nghiên cứu" ở mục 3.8 của `03_protocol/sr-protocol.md` chỉ áp
dụng cho ước lượng gộp chính (A1), không áp dụng cho các phân tích dưới nhóm (A2). Phân nhóm A2 (rob_overall =
low, k = 3) không cần và không dự kiến báo cáo khoảng dự đoán. Không chạy lại `meta.py`; không phải một
`DEVIATION`, vì đây là làm rõ một quy định đã đăng ký trước, không phải thay đổi mô hình hay phân tích sau khi
xem kết quả.
