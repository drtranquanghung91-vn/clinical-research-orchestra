# PHỤ LỤC

## Phụ lục 1. Bảng kiểm STROBE

*Bảng kiểm STROBE (đoàn hệ) sẽ được chèn vào đây sau vòng rà soát nội dung lần 1, khi agent
`reporting-guideline-checker` tạo xong `reviews/guideline-checklist.json` và được in bằng
`guideline_checklist.py . --table`. Mục này chưa phải một khối chờ hình/bảng theo quy ước của
`assemble.py` (không dùng cú pháp "Bảng …/Hình …/Biểu đồ … — chờ …"), chỉ là một đoạn văn bản thường,
để tránh bị tính là lỗi định dạng trước khi vòng rà soát đầu tiên hoàn tất.*

## Phụ lục 2. Bảng biến số nghiên cứu (biểu mẫu trích xuất dữ liệu)

Nguồn dữ liệu cho mọi biến: hồ sơ bệnh án điện tử (EMR) và hệ thống thông tin bệnh viện (HIS) của
Bệnh viện Mô phỏng — không có nguồn dữ liệu ngoài hai hệ thống này. Bảng này là cơ sở của biểu mẫu
trích xuất dữ liệu dùng trong nghiên cứu (dẫn từ `03_protocol/variables.md`); đây là trích xuất từ
dữ liệu điện tử đã có sẵn, không phải một bộ công cụ thu thập trực tiếp trên người bệnh (CRF giấy).

**Biến phơi nhiễm**

| Biến | Định nghĩa / cách đo | Loại | Giá trị / đơn vị | Vai trò |
|---|---|---|---|---|
| HbA1c lúc nhập viện (phân nhóm) | Giá trị HbA1c đo trong 24–48 giờ đầu nhập viện, phân 3 nhóm | Thứ tự/phân loại | < 7% / 7–9% / > 9% (nhóm < 7% tham chiếu) | Phơi nhiễm chính |
| HbA1c lúc nhập viện (liên tục) | Giá trị HbA1c đo trong 24–48 giờ đầu nhập viện | Liên tục | % (NGSP) | Phơi nhiễm (phân tích phụ) |

**Biến kết cục**

| Biến | Định nghĩa / cách đo | Loại | Giá trị / đơn vị | Vai trò |
|---|---|---|---|---|
| Tái nhập viện 1 năm (mọi nguyên nhân) | ≥ 1 lần nhập viện nội trú tại BV Mô phỏng trong 365 <!-- not-a-result: mốc theo dõi của đề tài --> ngày kể từ ngày xuất viện của lần nhập viện chỉ số | Nhị giá | Có / Không | Kết cục chính |
| Tái nhập viện liên quan ĐTĐ | Tái nhập viện trong 1 năm có chẩn đoán chính/kèm theo thuộc khối ICD-10 liên quan ĐTĐ hoặc biến chứng đường huyết | Nhị giá | Có / Không | Kết cục phụ |
| Thời gian đến lần tái nhập viện đầu tiên | Số ngày từ ngày xuất viện đến ngày nhập viện của lần tái nhập viện đầu tiên (censored tại 365 <!-- not-a-result: mốc theo dõi của đề tài --> ngày nếu không tái nhập viện) | Thời gian-đến-sự kiện | Ngày | Kết cục phụ |
| Tử vong trong 1 năm (trong viện) | HIS chỉ ghi nhận tử vong trong viện; không xác định được tử vong ngoài viện | Nhị giá (trong viện) | Có / Không | Kết cục phụ — không đầy đủ, chỉ dùng cho phân tích độ nhạy |

**Biến nhiễu đưa vào mô hình chính**

| Biến | Định nghĩa / cách đo | Loại | Giá trị / đơn vị | Vai trò |
|---|---|---|---|---|
| Tuổi | Tuổi tại thời điểm nhập viện chỉ số, tính theo năm hoàn chỉnh | Liên tục | Năm | Mô tả / nhiễu |
| Giới | Giới ghi trong hồ sơ | Phân loại nhị giá | Nam / Nữ | Mô tả / nhiễu |
| Thời gian mắc ĐTĐ | Số năm từ ngày được chẩn đoán ĐTĐ type 2 đến ngày nhập viện chỉ số | Liên tục | Năm | Mô tả / nhiễu |
| Bệnh đồng mắc chính | Có/không ≥ 1 trong: tăng huyết áp, bệnh thận mạn, bệnh tim mạch — ghi nhận trước hoặc tại thời điểm nhập viện chỉ số | Nhị giá | Có / Không | Nhiễu |

**Biến không đưa vào mô hình chính (trung gian/vai trò nhân quả chưa rõ)**

| Biến | Định nghĩa / cách đo | Loại | Giá trị / đơn vị | Vai trò |
|---|---|---|---|---|
| Sử dụng insulin trong thời gian nằm viện | Có/không chỉ định insulin trong lần nhập viện chỉ số | Nhị giá | Có / Không | Mô tả / trung gian nghi ngờ |
| Thời gian nằm viện (lần nhập viện chỉ số) | Số ngày từ nhập viện đến xuất viện | Liên tục | Ngày | Mô tả / vai trò nhân quả chưa rõ |

**Biến thăm dò, có điều kiện (dự kiến ở đề cương, không có trong bộ dữ liệu mô phỏng của dự án này)**

| Biến | Định nghĩa / cách đo | Tình trạng |
|---|---|---|
| Tỷ số bạch cầu trung tính/lympho (NLR) | Tính từ công thức máu lúc nhập viện | Không có trong bộ dữ liệu trích xuất của dự án mô phỏng này |
| Chỉ số viêm tổng hợp (SII/SIRI) | Tính từ công thức máu lúc nhập viện | Như trên |
| Nguy cơ dinh dưỡng lúc nhập viện | Thang đánh giá dinh dưỡng thường quy (nếu có) | Như trên |

## Phụ lục 3. Từ điển biến (data dictionary) của tệp dữ liệu phân tích

Từ điển biến dưới đây mô tả cách mã hóa từng biến trong tệp dữ liệu phân tích đã khử định danh
(`04_data/cohort.deid.csv`, dữ liệu MÔ PHỎNG, n = {{R-A0-001.n}}). Không có họ tên, số hồ sơ, ngày
tháng thật hay định danh cá nhân nào trong tệp này hoặc trong bảng dưới đây.

| Biến | Loại | Đơn vị | Mã hóa | Ghi chú |
|---|---|---|---|---|
| hba1c | Liên tục | % (NGSP) | 1 chữ số thập phân | Phơi nhiễm phụ (phân tích liên tục, mỗi 1%) |
| hba1c_group | Thứ tự/phân loại | — | `<7` / `7-9` / `>9` (nhóm `<7` tham chiếu) | Phơi nhiễm chính |
| readmit_1y | Nhị giá | — | 0 = Không, 1 = Có | Kết cục chính |
| readmit_dm_1y | Nhị giá | — | 0 = Không, 1 = Có | Kết cục phụ; chỉ = 1 khi readmit_1y = 1 |
| time_to_readmit_days | Liên tục | Ngày | 1–365 <!-- not-a-result: thiết kế biến, giới hạn theo dõi 365 ngày của đề tài -->; = 365 <!-- not-a-result: thiết kế biến --> khi không tái nhập viện (censored) | Kết cục phụ, thời gian-đến-sự kiện |
| death_inhosp_1y | Nhị giá | — | 0 = Không, 1 = Có | Kết cục phụ, chỉ tử vong trong viện, không đầy đủ |
| age | Liên tục | Năm | Số nguyên | — |
| sex | Phân loại nhị giá | — | `Nam` / `Nữ` | — |
| dm_duration_years | Liên tục | Năm | 1 chữ số thập phân; để trống nếu không ghi nhận | ~2,5% thiếu theo thiết kế; không suy diễn giá trị |
| htn / ckd / cvd | Nhị giá | — | 0/1 | Thành phần của biến dẫn xuất "bệnh đồng mắc chính" |
| *comorb_any* (dẫn xuất) | Nhị giá | — | = 1 nếu htn=1 hoặc ckd=1 hoặc cvd=1 | Tính ở bước phân tích, không có cột riêng trong tệp dữ liệu |
| insulin | Nhị giá | — | 0 = Không, 1 = Có | Mô tả/trung gian nghi ngờ |
| los_days | Liên tục | Ngày | Số nguyên dương | Mô tả, vai trò nhân quả chưa rõ |
| pid | Định danh nghiên cứu | — | `P0001`…`P1070` | Mã số nghiên cứu, không dùng trong phân tích thống kê, không phải số hồ sơ gốc |
