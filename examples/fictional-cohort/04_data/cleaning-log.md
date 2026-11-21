# Cleaning log — `04_data/cohort.deid.csv`

Mọi dòng trong tệp là `SIMULATED`. Không có tệp thô trong `00_inputs/`; tệp dữ liệu KHÔNG bị sửa ở
bước này (đúng nguyên tắc §1 của `data-preparation`). Audit chạy bằng `05_analysis/audit.py`
(dùng `crostats.audit`, vendored từ clinical-research-orchestra 0.2.0).

## Kết quả audit (2026-11-21)

- Số dòng: 1.070 (đúng `03_protocol/sample-size.md`).
- Dòng trùng lặp hoàn toàn: 0.
- `pid` trùng lặp: 0; đúng định dạng `P0001`…`P1070`, không có khoảng trống trong dải số.
- Thiếu dữ liệu: chỉ `dm_duration_years` có 27/1.070 (2,5%) giá trị trống; tất cả biến khác không
  thiếu.
- Outlier (Tukey, IQR × 1,5 — mặc định, xem `judgement-defaults.md`): `age` 7, `hba1c` 6, `los_days`
  29, `time_to_readmit_days` 224, `dm_duration_years` 0. **Không có outlier nào bị loại hoặc sửa** —
  đúng nguyên tắc "outliers flagged, never removed".

## Kiểm tra giá trị bất khả thi / logic nội bộ (không phải outlier thống kê)

| Kiểm tra | Kết quả |
|---|---|
| `age` trong khoảng hợp lý (18–105) | đạt: 30–95 |
| `hba1c` trong khoảng hợp lý (4–16%) | đạt: 5,0–13,7 |
| `hba1c_group` khớp ngưỡng của `hba1c` (<7 / 7–9 / >9) | đạt: 0 dòng lệch |
| `los_days` dương, hợp lý (1–120 ngày) | đạt: 2–33 |
| `dm_duration_years` không âm, không vượt tuổi | đạt: 0,0–23,9 (trong các dòng có ghi nhận) |
| `readmit_dm_1y` = 1 chỉ khi `readmit_1y` = 1 | đạt: 0 dòng vi phạm |
| `time_to_readmit_days` = 365 khi `readmit_1y` = 0; trong [1,365] khi `readmit_1y` = 1 | đạt: 0 dòng vi phạm |
| `death_inhosp_1y` = 1 chỉ khi có tái nhập viện (`readmit_1y` = 1) | đạt: 0 dòng vi phạm |
| `htn`, `ckd`, `cvd`, `insulin`, `readmit_1y`, `readmit_dm_1y`, `death_inhosp_1y` chỉ nhận 0/1 | đạt |
| `sex` chỉ nhận `Nam`/`Nữ` | đạt |

## Quy tắc làm sạch áp dụng

**Không có quy tắc làm sạch nào được áp dụng.** Không phát hiện giá trị bất khả thi, lỗi mã hóa,
hoặc dòng trùng lặp cần xử lý. Bảng dưới đây được giữ trống có chủ đích (template từ
`data-preparation.md`) để ghi nhận nếu phát sinh trong các lượt audit sau (ví dụ khi dữ liệu thật
thay thế dữ liệu mô phỏng ở `ethics-and-crf`/thu thập thật).

| Date | Rule | Variable | Rows affected | Reason | Reversible? |
|---|---|---|---|---|---|
| — | (không có) | — | 0 | audit 2026-11-21 không phát hiện giá trị bất khả thi hoặc lỗi mã hóa | — |

## Dữ liệu thiếu (chỉ mô tả, không suy diễn — theo `data-preparation.md` §"Missing data")

- `dm_duration_years`: 27/1.070 dòng (2,5%) trống. Theo `tools/simulate_cohort.py`, đây là thiếu
  ngẫu nhiên mô phỏng (MAR theo thiết kế: xác suất thiếu cố định 2%, không phụ thuộc giá trị hay
  nhóm). Codebook ghi "để trống nếu không ghi nhận"; **không impute ở bước này** — việc có impute
  hay không thuộc `03_protocol/sap.md`; SAP hiện chưa nêu phương pháp xử lý thiếu cho biến này, cần
  tác giả quyết định và ghi vào `decisions.md` trước khi chạy `statistical-analysis` nếu muốn khác
  với complete-case.
- Mọi biến khác: 0% thiếu.

## Ghi chú về outlier (không phải lỗi, không bị loại)

- `time_to_readmit_days` có 224 giá trị bị gắn cờ "outlier" theo IQR × 1,5 cơ học — đây là đặc điểm
  cấu trúc của một biến bị censor tại 365 ngày (phần lớn cỡ mẫu không tái nhập viện nên dồn vào giá
  trị 365, khiến các trường hợp có tái nhập viện thật trở thành "lệch" theo IQR dù hoàn toàn hợp lệ
  về mặt lâm sàng). Không xử lý gì thêm; biến censor tương ứng là `1 - readmit_1y`, cần dùng đúng
  trong phân tích thời gian-đến-sự kiện (Cox) theo SAP.
- `age`, `hba1c`, `los_days`, `dm_duration_years`: các outlier nằm trong khoảng giá trị lâm sàng hợp
  lý (xem bảng kiểm tra trên), không có dấu hiệu lỗi nhập liệu. Giữ nguyên, gắn cờ để tác giả xem lại
  khi phân tích mô tả (Table 1).
