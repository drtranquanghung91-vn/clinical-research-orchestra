# Danh mục hồ sơ gửi Hội đồng Đạo đức

Liệt kê toàn bộ tài liệu dự kiến nộp cho Hội đồng Đạo đức trong nghiên cứu y sinh học và tình trạng
hiện tại của từng tài liệu. Trạng thái: `đã soạn` (do Claude soạn, tác giả cần rà soát), `tác giả
cung cấp`, `tác giả đã rà soát`, `đã được phê duyệt` (kèm số quyết định của hội đồng — chỉ tác giả
được ghi trạng thái này).

| Tài liệu | File | Trạng thái | Ghi chú |
|---|---|---|---|
| Đề cương nghiên cứu (protocol) | `03_protocol/protocol.md` | khóa (G2) | |
| Bảng biến số nghiên cứu | `03_protocol/variables.md` | khóa (G2) | đầu vào của CRF/từ điển dữ liệu |
| Kế hoạch phân tích thống kê (SAP) | `03_protocol/sap.md` | khóa (G2) | |
| Tính toán cỡ mẫu | `03_protocol/sample-size.md` | khóa (G2) | |
| Phiếu thu thập số liệu (CRF) | `03_protocol/ethics/crf.md` | đã soạn | sinh từ `variables.md` bằng `crf.py`; tác giả rà soát |
| Từ điển dữ liệu (data dictionary) | `03_protocol/ethics/data-dictionary.csv` | đã soạn | sinh từ `variables.md` bằng `crf.py`; tác giả rà soát |
| Bản cung cấp thông tin (lưu hồ sơ, không có phần ký tên) | `03_protocol/ethics/consent-form.md` | đã soạn | Hội đồng Đạo đức đã miễn ký phiếu đồng ý cá nhân; văn bản này lưu hồ sơ và dùng để giải thích cho người bệnh nếu họ hỏi |
| Quyết định miễn ký phiếu đồng ý cá nhân (bằng văn bản) | `[[TÁC GIẢ: …]]` | chờ hội đồng | lý do: nghiên cứu hồi cứu hồ sơ, chỉ dùng dữ liệu đã có trong EMR/HIS, không liên hệ người bệnh đã xuất viện, dữ liệu được mã hóa trước phân tích; quyết định miễn ký đã được tác giả ghi nhận trong `decisions.md` (2026-11-23) — cần bản quyết định chính thức bằng văn bản của hội đồng để lưu hồ sơ |
| Đơn đăng ký/mẫu xin phê duyệt của hội đồng | `[[TÁC GIẢ: …]]` | tác giả cung cấp | theo mẫu riêng của Hội đồng Đạo đức Bệnh viện Mô phỏng |
| Lý lịch khoa học và chứng chỉ GCP của nghiên cứu viên | `[[TÁC GIẢ: …]]` | tác giả cung cấp | |
| Công văn/giấy đồng ý cho phép sử dụng dữ liệu của Bệnh viện Mô phỏng | `[[TÁC GIẢ: …]]` | tác giả cung cấp | nơi lưu trữ EMR/HIS nguồn dữ liệu |
| Bản cam kết bảo mật và quản lý dữ liệu | `[[TÁC GIẢ: …]]` | tác giả cung cấp | nếu hội đồng yêu cầu văn bản riêng ngoài Mục 7 của `consent-form.md` |
| Quyết định/giấy chấp thuận của Hội đồng Đạo đức | `[[TÁC GIẢ: …]]` | chờ hội đồng | ghi số quyết định và ngày khi có |

## Ghi chú về việc miễn ký phiếu đồng ý cá nhân

Theo quyết định ngày 2026-11-21 của tác giả, nhóm nghiên cứu đã xin miễn ký phiếu đồng ý cá nhân với
lý do: nghiên cứu đoàn hệ hồi cứu, chỉ sử dụng dữ liệu đã có sẵn trong hồ sơ bệnh án điện tử và hệ
thống thông tin bệnh viện, người bệnh đã xuất viện (ước tính khoảng 1.200 người bệnh), không liên hệ
hoặc can thiệp thêm, dữ liệu được mã hóa (thay tên/số hồ sơ bằng mã số nghiên cứu) trước khi phân
tích.

Theo ghi nhận của tác giả trong `decisions.md` (mục "2026-11-23 — Consent waiver (author)"), **Hội
đồng Đạo đức trong nghiên cứu y sinh học của Bệnh viện Mô phỏng đã chấp thuận miễn ký phiếu đồng ý
cá nhân** vì đây là nghiên cứu hồi cứu hồ sơ (**hội đồng và quyết định này là hư cấu, dùng cho mục
đích luyện tập** — tác giả tự xác nhận trong `decisions.md`, không phải một quyết định thật của một
hội đồng đạo đức thật). Văn bản `consent-form.md` được soạn lại thành bản cung cấp thông tin, không
có phần ký tên, để lưu trong hồ sơ đạo đức. Khi nộp hồ sơ cho một hội đồng đạo đức thật, tác giả cần
có quyết định miễn ký bằng văn bản chính thức của hội đồng đó, không dùng ghi chú trong
`decisions.md` làm căn cứ pháp lý.

## Quy tắc áp dụng

Mọi quy định, yêu cầu cụ thể của Hội đồng Đạo đức Bệnh viện Mô phỏng hoặc văn bản pháp luật không
được suy diễn hay trích dẫn từ trí nhớ: chỉ ghi khi tác giả cung cấp hoặc có nguồn tra cứu cụ thể
(ghi rõ nguồn). Các mục `[[TÁC GIẢ: …]]` ở trên cần tác giả điền hoặc xác nhận với phòng/bộ phận
quản lý nghiên cứu khoa học của bệnh viện.
