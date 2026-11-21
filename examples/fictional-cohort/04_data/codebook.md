# Codebook — `04_data/cohort.deid.csv`

Nguồn: dữ liệu **MÔ PHỎNG** (`SIMULATED`), sinh bởi `tools/simulate_cohort.py` (seed cố định
20261121), đối chiếu với `03_protocol/variables.md`. Không có tệp thô trong `00_inputs/`; không
chạy `deidentify-data` vì tệp đã ở dạng ẩn danh ngay từ khi sinh (không có họ tên/số hồ sơ/ngày
tháng thật — ngày được thay bằng số ngày, xem cột `los_days` và `time_to_readmit_days`).

n = 1.070 dòng (đúng với `03_protocol/sample-size.md`).

## Biến hành chính / định danh

| Variable | Type | Unit | Coding | Source column | Notes |
|---|---|---|---|---|---|
| simulated | text | — | luôn `SIMULATED` | cột 1, mọi dòng | cờ xác nhận dữ liệu mô phỏng, không phải biến phân tích |
| pid | text (ID) | — | `P0001`…`P1070` | mã số nghiên cứu | định danh nghiên cứu thay số hồ sơ gốc; không dùng trong phân tích thống kê |

## Biến phơi nhiễm

| Variable | Type | Unit | Coding | Source column | Notes |
|---|---|---|---|---|---|
| hba1c | continuous | % (NGSP) | 1 chữ số thập phân | HbA1c lúc nhập viện — variables.md §1 | phơi nhiễm phụ (phân tích liên tục, mỗi 1%) |
| hba1c_group | ordinal/categorical | — | `<7` / `7-9` / `>9` (nhóm `<7` tham chiếu) | HbA1c lúc nhập viện, phân nhóm — variables.md §1 | **phơi nhiễm chính**; nhất quán với `hba1c` (kiểm tra ở audit) |

## Biến kết cục

| Variable | Type | Unit | Coding | Source column | Notes |
|---|---|---|---|---|---|
| readmit_1y | binary | — | 0 = Không, 1 = Có | Tái nhập viện 1 năm mọi nguyên nhân — variables.md §2 | **kết cục chính** |
| readmit_dm_1y | binary | — | 0 = Không, 1 = Có | Tái nhập viện liên quan ĐTĐ — variables.md §2 | kết cục phụ; theo thiết kế chỉ có thể = 1 khi `readmit_1y` = 1 (kiểm tra ở audit) |
| time_to_readmit_days | continuous | ngày | 1–365; = 365 khi không tái nhập viện trong năm (censored) | Thời gian đến lần tái nhập viện đầu tiên — variables.md §2 | kết cục phụ, thời gian-đến-sự kiện; biến censor là `1 - readmit_1y` |
| death_inhosp_1y | binary | — | 0 = Không, 1 = Có | Tử vong trong viện trong 365 ngày — variables.md §2 | kết cục phụ, **không đầy đủ**: chỉ tử vong trong viện, không phải tử vong do mọi nguyên nhân (đã ghi trong variables.md và `decisions.md`); theo SAP 1.1 không còn dùng Fine-Gray (tử vong sau xuất viện chỉ xảy ra sau một lần tái nhập viện, không phải nguy cơ cạnh tranh) |

## Biến nhiễu / mô tả

| Variable | Type | Unit | Coding | Source column | Notes |
|---|---|---|---|---|---|
| age | continuous | năm (năm hoàn chỉnh) | 30–95 (giới hạn mô phỏng) | Tuổi — variables.md §3 | |
| sex | binary categorical | — | `Nam` / `Nữ` | Giới — variables.md §3 | |
| dm_duration_years | continuous | năm | 1 chữ số thập phân; để trống (missing) nếu không ghi nhận | Thời gian mắc ĐTĐ — variables.md §3 | ~2% thiếu theo thiết kế mô phỏng (xem audit); KHÔNG suy diễn giá trị |
| htn | binary | — | 0/1 | thành phần của "Bệnh đồng mắc chính" — variables.md §3 | |
| ckd | binary | — | 0/1 | thành phần của "Bệnh đồng mắc chính" — variables.md §3 | |
| cvd | binary | — | 0/1 | thành phần của "Bệnh đồng mắc chính" — variables.md §3 | |
| *comorb_any* (dẫn xuất, không có cột riêng) | binary (derived) | — | = 1 nếu `htn`=1 HOẶC `ckd`=1 HOẶC `cvd`=1, ngược lại 0 | tính từ `htn`,`ckd`,`cvd` | biến nhiễu đưa vào mô hình chính (variables.md §3); tính ở bước phân tích, không ghi thêm cột vào `04_data/` để tránh sửa tệp dữ liệu |

## Biến mô tả / trung gian nghi ngờ (không hiệu chỉnh trong mô hình chính)

| Variable | Type | Unit | Coding | Source column | Notes |
|---|---|---|---|---|---|
| insulin | binary | — | 0 = Không, 1 = Có | Sử dụng insulin trong thời gian nằm viện — variables.md §4 | mô tả/trung gian nghi ngờ, không hiệu chỉnh trong mô hình chính |
| los_days | continuous | ngày | nguyên dương | Thời gian nằm viện (lần nhập viện chỉ số) — variables.md §4 | mô tả, vai trò nhân quả chưa rõ, không hiệu chỉnh trong mô hình chính |

## Biến thăm dò trong variables.md KHÔNG có trong tệp dữ liệu này

| Variable (variables.md §5) | Tình trạng |
|---|---|
| NLR (tỷ số bạch cầu trung tính/lympho) | **Không có cột tương ứng** trong `cohort.deid.csv` — `tools/simulate_cohort.py` không sinh biến này. Vì đây là dự án mô phỏng không có công thức máu thật, biến này không được đưa vào trích xuất. Trên dữ liệu thật, phải kiểm tra tỷ lệ thiếu công thức bạch cầu phân loại theo ngưỡng 20% đã chốt trong `decisions.md` trước khi quyết định đưa vào. |
| SII / SIRI | Như trên — không có trong tệp này. |
| Nguy cơ dinh dưỡng lúc nhập viện (NRS-2002…) | Như trên — không có trong tệp này (bệnh viện mô phỏng không có thang đo này trong hồ sơ). |

Đây không phải dữ liệu thiếu (missing) của một biến đã thu thập — là biến **chưa được trích xuất**
trong bộ dữ liệu mô phỏng này. Không tự thêm cột giả định; nếu tác giả cần các biến này cho phân
tích thăm dò, phải tạo lại dữ liệu mô phỏng (sửa `tools/simulate_cohort.py`) hoặc ghi rõ trong SAP
rằng nhánh phân tích đó bị bỏ với dữ liệu hiện có.
