# Báo cáo phân tích thống kê

> **Dữ liệu mô phỏng.** Toàn bộ dữ liệu trong báo cáo này là dữ liệu **MÔ PHỎNG** (`SIMULATED`),
> sinh bởi `tools/simulate_cohort.py` (seed cố định), không phải dữ liệu bệnh nhân thật. Kết quả chỉ
> minh họa quy trình phân tích của dự án ví dụ, không có giá trị lâm sàng.

## Thông tin chung

- **Tên đề tài:** HbA1c lúc nhập viện và nguy cơ tái nhập viện trong 1 năm ở người bệnh đái tháo
  đường type 2 xuất viện tại Bệnh viện Mô phỏng (2021–2023): một nghiên cứu đoàn hệ hồi cứu.
- **Thiết kế:** đoàn hệ hồi cứu, đơn trung tâm (`project.yaml → design: cohort`).
- **Tệp dữ liệu:** `04_data/cohort.deid.csv`, SHA-256:
  `7b127ad0ccfdd23c55450f6106aa540f9943d2dd50a73d9825ed5009053e5248`.
- **Số người bệnh phân tích:** {{R-A0-001.n}} (quần thể mô tả, Mục tiêu 1); {{R-A1-003.n}} ở các mô
  hình hiệu chỉnh (ca đầy đủ sau khi loại người thiếu thời gian mắc ĐTĐ, xem Mục 1 và Mục 7).
- **Ngày chạy phân tích:** 2026-11-21.
- **Phần mềm:** Python (pandas, scipy, statsmodels, lifelines); thư viện `crostats.py` vendored —
  phiên bản engine đầy đủ ghi trong `05_analysis/output/results.json` (trường `engine`).
- **Chế độ:** run mode (chạy trực tiếp từ `04_data/cohort.deid.csv`, không nhập kết quả từ phần mềm
  ngoài).

## 1. Kiểm tra chất lượng dữ liệu

Theo `04_data/cleaning-log.md` (audit chạy ở giai đoạn 4 Data, `05_analysis/audit.py`):
{{R-A0-001.n}} dòng, 0 dòng trùng lặp, 0 giá trị bất khả thi hoặc lỗi mã hóa — không có quy tắc làm
sạch nào được áp dụng lên tệp dữ liệu. Thiếu dữ liệu chỉ ở `dm_duration_years` (thời gian mắc ĐTĐ):
27 <!-- derived: R-A0-001.n - R-A1-003.n --> người bệnh
(2,5% <!-- derived: (R-A0-001.n - R-A1-003.n) / R-A0-001.n * 100 -->); mọi biến khác không thiếu.

Outlier theo quy ước Tukey (IQR × 1,5, chỉ gắn cờ, không loại bỏ): 7 <!-- not-a-result: 04_data/cleaning-log.md, audit age --> giá trị ở `age`, 6 <!-- not-a-result: 04_data/cleaning-log.md, audit hba1c --> ở `hba1c`, 29 <!-- not-a-result: 04_data/cleaning-log.md, audit los_days --> ở `los_days`, và 224 <!-- not-a-result: 04_data/cleaning-log.md, audit time_to_readmit_days --> ở
`time_to_readmit_days`. Số lượng lớn ở biến thời gian-đến-tái nhập viện là đặc điểm cấu trúc của một
biến bị kiểm duyệt tại mốc theo dõi cố định (phần lớn người không tái nhập viện dồn vào đúng một giá
trị), không phải lỗi dữ liệu — xem giải thích đầy đủ trong `cleaning-log.md`.

## 2. Đặc điểm đối tượng nghiên cứu

**Bảng 3.1.** Đặc điểm chung theo nhóm HbA1c lúc nhập viện (không kèm p, theo khuyến nghị
`sap.md` mục 7 cho thiết kế quan sát).

| Đặc điểm | Chung (n={{R-A0-001.n}}) | <7% (n={{R-A0-002.n}}) | 7–9% (n={{R-A0-003.n}}) | >9% (n={{R-A0-004.n}}) |
|---|---|---|---|---|
| Tuổi (năm), TB ± ĐLC | {{R-A0-001.full}} | {{R-A0-002.full}} | {{R-A0-003.full}} | {{R-A0-004.full}} |
| Nam, n (%) | {{R-A0-005.full}} | {{R-A0-006.full}} | {{R-A0-007.full}} | {{R-A0-008.full}} |
| Nữ, n (%) | {{R-A0-009.full}} | {{R-A0-010.full}} | {{R-A0-011.full}} | {{R-A0-012.full}} |
| Thời gian mắc ĐTĐ (năm), TB ± ĐLC¹ | {{R-A0-013.full}} | {{R-A0-014.full}} | {{R-A0-015.full}} | {{R-A0-016.full}} |
| Tăng huyết áp, n (%) | {{R-A0-021.full}} | {{R-A0-022.full}} | {{R-A0-023.full}} | {{R-A0-024.full}} |
| Bệnh thận mạn, n (%) | {{R-A0-029.full}} | {{R-A0-030.full}} | {{R-A0-031.full}} | {{R-A0-032.full}} |
| Bệnh tim mạch, n (%) | {{R-A0-037.full}} | {{R-A0-038.full}} | {{R-A0-039.full}} | {{R-A0-040.full}} |
| ≥1 bệnh đồng mắc (THA/BTM/tim mạch), n (%) | {{R-A0-045.full}} | {{R-A0-046.full}} | {{R-A0-047.full}} | {{R-A0-048.full}} |
| Dùng insulin khi nằm viện, n (%) | {{R-A0-053.full}} | {{R-A0-054.full}} | {{R-A0-055.full}} | {{R-A0-056.full}} |
| Thời gian nằm viện (ngày), trung vị (KTPV) | {{R-A0-057.full}} | {{R-A0-058.full}} | {{R-A0-059.full}} | {{R-A0-060.full}} |

¹ 27 <!-- derived: R-A0-001.n - R-A1-003.n --> người bệnh thiếu thời gian mắc ĐTĐ (xem Mục 1), nên
n = {{R-A1-003.n}} cho dòng này (theo từng nhóm HbA1c: {{R-A0-014.n}} / {{R-A0-015.n}} /
{{R-A0-016.n}}).

Dữ liệu đầy đủ: `05_analysis/output/tables/T3.1.csv`.

**Bảng 3.2.** Tỷ lệ tái nhập viện mọi nguyên nhân trong 1 năm, chung và theo nhóm HbA1c (KTC 95%
Wilson).

| Nhóm HbA1c | n | Tái nhập viện (%) | KTC 95% |
|---|---|---|---|
| Chung | {{R-A0-061.n}} | {{R-A0-061.value}} | {{R-A0-061.ci}} |
| <7% | {{R-A0-062.n}} | {{R-A0-062.value}} | {{R-A0-062.ci}} |
| 7–9% | {{R-A0-063.n}} | {{R-A0-063.value}} | {{R-A0-063.ci}} |
| >9% | {{R-A0-064.n}} | {{R-A0-064.value}} | {{R-A0-064.ci}} |

Dữ liệu đầy đủ: `05_analysis/output/tables/T3.2.csv`.

**Nhận xét ngắn:** phân bố tuổi, giới và bệnh đồng mắc khá tương đồng giữa 3 nhóm HbA1c; nhóm HbA1c
cao dùng insulin trong thời gian nằm viện nhiều hơn rõ rệt, phù hợp sinh lý bệnh (không hiệu chỉnh
trong mô hình chính vì là biến trung gian nghi ngờ, `variables.md` mục 4). Tỷ lệ tái nhập viện tăng
dần theo nhóm HbA1c nhưng các khoảng tin cậy chồng lấp rộng.

## 3. Phân tích chính (A1 — tái nhập viện mọi nguyên nhân trong 1 năm)

Mọi nhóm HbA1c có ≥5 sự kiện tái nhập viện (Bảng 3.2) nên quy tắc đổi sang kiểm định thay thế
(`sap.md` mục 8) không được áp dụng; hồi quy logistic tiến hành như đăng ký A1.

### 3.1 So sánh thô

| So sánh | OR thô | KTC 95% |
|---|---|---|
| 7–9% so với <7% (tham chiếu) | {{R-A1-001.value}} | {{R-A1-001.ci}} |
| >9% so với <7% (tham chiếu) | {{R-A1-002.value}} | {{R-A1-002.ci}} |

### 3.2 Mô hình hiệu chỉnh

Hồi quy logistic đa biến: tái nhập viện 1 năm theo nhóm HbA1c (3 mức, tham chiếu <7%), hiệu chỉnh
tuổi, giới, thời gian mắc ĐTĐ, ≥1 bệnh đồng mắc (`sap.md` mục 8).

| Biến | OR hiệu chỉnh | KTC 95% | p |
|---|---|---|---|
| HbA1c 7–9% so với <7% | {{R-A1-003.value}} | {{R-A1-003.ci}} | {{R-A1-003.p}} |
| HbA1c >9% so với <7% | {{R-A1-004.value}} | {{R-A1-004.ci}} | {{R-A1-004.p}} |
| Giới (Nữ so với Nam) | {{R-A1-005.value}} | {{R-A1-005.ci}} | {{R-A1-005.p}} |
| Tuổi (mỗi năm) | {{R-A1-006.value}} | {{R-A1-006.ci}} | {{R-A1-006.p}} |
| Thời gian mắc ĐTĐ (mỗi năm) | {{R-A1-007.value}} | {{R-A1-007.ci}} | {{R-A1-007.p}} |
| ≥1 bệnh đồng mắc | {{R-A1-008.value}} | {{R-A1-008.ci}} | {{R-A1-008.p}} |

**Chẩn đoán mô hình:** AUC = {{R-A1-009.value}}; EPV = {{R-A1-010.value}} (ngưỡng mặc định ≥10,
không cần cảnh báo thăm dò); VIF mỗi biến từ {{R-A1-015.value}} đến {{R-A1-012.value}} (ngưỡng quy
ước >5, không có bằng chứng đa cộng tuyến); kiểm tra tuyến tính logit (phép kiểm likelihood-ratio với
số hạng bậc hai) cho tuổi và thời gian mắc ĐTĐ đều không cho thấy bằng chứng phi tuyến tính (p > 0,05
cho cả hai biến, chi tiết tại `05_analysis/output/log.txt` dòng 102–103 <!-- not-a-result: tham chiếu số dòng trong log.txt -->).

Mô hình hội tụ, không có dấu hiệu tách biệt hoàn toàn (separation) hay đa cộng tuyến — không có
"MODEL FAILED" nào được ghi ở A1.

**Đọc kết quả:** cả hai OR hiệu chỉnh đều cùng chiều với giả thuyết (HbA1c cao hơn → nguy cơ tái
nhập viện cao hơn) nhưng khoảng tin cậy 95% của cả hai đều bao gồm giá trị 1 — chưa đạt ý nghĩa thống
kê ở mức α = 0,05. Đây phù hợp với hạn chế power đã nêu trước khi có dữ liệu (`sample-size.md` mục
4/10): cỡ mẫu được tính cho so sánh 2 nhóm cực dựa trên giả định tỷ lệ/OR kỳ vọng, không bảo đảm đủ
power nếu hiệu ứng thật nhỏ hơn giả định.

## 4. Phân tích kết cục phụ

### 4.1 A2 — HbA1c liên tục (mỗi 1%) thay cho 3 nhóm

| Biến | OR hiệu chỉnh | KTC 95% | p |
|---|---|---|---|
| HbA1c (mỗi 1%) | {{R-A2-002.value}} | {{R-A2-002.ci}} | {{R-A2-002.p}} |
| Giới (Nữ so với Nam) | {{R-A2-001.value}} | {{R-A2-001.ci}} | {{R-A2-001.p}} |
| Tuổi (mỗi năm) | {{R-A2-003.value}} | {{R-A2-003.ci}} | {{R-A2-003.p}} |
| Thời gian mắc ĐTĐ (mỗi năm) | {{R-A2-004.value}} | {{R-A2-004.ci}} | {{R-A2-004.p}} |
| ≥1 bệnh đồng mắc | {{R-A2-005.value}} | {{R-A2-005.ci}} | {{R-A2-005.p}} |

AUC = {{R-A2-006.value}}; EPV = {{R-A2-007.value}}. Kết quả thăm dò, không hiệu chỉnh đa so sánh
(`sap.md` mục 9).

### 4.2 A3 — Tái nhập viện liên quan ĐTĐ trong 1 năm

| Biến | OR hiệu chỉnh | KTC 95% | p |
|---|---|---|---|
| HbA1c 7–9% so với <7% | {{R-A3-001.value}} | {{R-A3-001.ci}} | {{R-A3-001.p}} |
| HbA1c >9% so với <7% | {{R-A3-002.value}} | {{R-A3-002.ci}} | {{R-A3-002.p}} |
| Giới (Nữ so với Nam) | {{R-A3-003.value}} | {{R-A3-003.ci}} | {{R-A3-003.p}} |
| Tuổi (mỗi năm) | {{R-A3-004.value}} | {{R-A3-004.ci}} | {{R-A3-004.p}} |
| Thời gian mắc ĐTĐ (mỗi năm) | {{R-A3-005.value}} | {{R-A3-005.ci}} | {{R-A3-005.p}} |
| ≥1 bệnh đồng mắc | {{R-A3-006.value}} | {{R-A3-006.ci}} | {{R-A3-006.p}} |

AUC = {{R-A3-007.value}}; EPV = {{R-A3-008.value}} (vẫn trên ngưỡng mặc định ≥10, nhưng thấp hơn các
mô hình khác vì outcome ít sự kiện hơn — diễn giải thận trọng hơn). Kết quả thăm dò, không hiệu chỉnh
đa so sánh. Cả hai OR theo nhóm HbA1c đều có ý nghĩa thống kê và KTC 95% không chứa 1, hướng phù hợp
giả thuyết sinh học (men hóa đường huyết kém liên quan biến chứng/tái nhập ĐTĐ) — nhưng đây là outcome
phụ, cần xem là giả thuyết cần kiểm định lại, không phải kết luận xác nhận.

### 4.3 A4 — Thời gian đến lần tái nhập viện đầu tiên (Cox, kiểm duyệt trong 1 năm)

**HR thô:**

| So sánh | HR thô | KTC 95% | p |
|---|---|---|---|
| 7–9% so với <7% | {{R-A4-001.value}} | {{R-A4-001.ci}} | {{R-A4-001.p}} |
| >9% so với <7% | {{R-A4-002.value}} | {{R-A4-002.ci}} | {{R-A4-002.p}} |

**HR hiệu chỉnh** (cùng biến hiệu chỉnh như A1):

| Biến | HR hiệu chỉnh | KTC 95% | p |
|---|---|---|---|
| HbA1c 7–9% so với <7% | {{R-A4-005.value}} | {{R-A4-005.ci}} | {{R-A4-005.p}} |
| HbA1c >9% so với <7% | {{R-A4-006.value}} | {{R-A4-006.ci}} | {{R-A4-006.p}} |
| Tuổi (mỗi năm) | {{R-A4-007.value}} | {{R-A4-007.ci}} | {{R-A4-007.p}} |
| Giới (Nữ so với Nam) | {{R-A4-008.value}} | {{R-A4-008.ci}} | {{R-A4-008.p}} |
| Thời gian mắc ĐTĐ (mỗi năm) | {{R-A4-009.value}} | {{R-A4-009.ci}} | {{R-A4-009.p}} |
| ≥1 bệnh đồng mắc | {{R-A4-010.value}} | {{R-A4-010.ci}} | {{R-A4-010.p}} |

**Chẩn đoán mô hình:** chỉ số đồng thuận (concordance) = {{R-A4-003.value}} (mô hình thô) và
{{R-A4-012.value}} (mô hình hiệu chỉnh); EPV mô hình hiệu chỉnh = {{R-A4-011.value}}. Kiểm định giả
định PH (phần dư Schoenfeld) cho p nhỏ nhất = {{R-A4-004.value}} ở mô hình thô (p > 0,05, không vi
phạm) và {{R-A4-013.value}} ở mô hình hiệu chỉnh (p > 0,05, không vi phạm).

Kết quả thăm dò, không hiệu chỉnh đa so sánh. Hướng và độ lớn HR tương tự OR ở A1 (nhóm HbA1c cao hơn
có HR > 1 nhưng KTC 95% chứa 1).

### 4.4 A5 — Tử vong trong viện trong 1 năm (chỉ mô tả)

| Nhóm HbA1c | n | Tử vong trong viện (%) | KTC 95% |
|---|---|---|---|
| Chung | {{R-A5-001.n}} | {{R-A5-001.value}} | {{R-A5-001.ci}} |
| <7% | {{R-A5-002.n}} | {{R-A5-002.value}} | {{R-A5-002.ci}} |
| 7–9% | {{R-A5-003.n}} | {{R-A5-003.value}} | {{R-A5-003.ci}} |
| >9% | {{R-A5-004.n}} | {{R-A5-004.value}} | {{R-A5-004.ci}} |

Chỉ thống kê mô tả, **không phân tích đa biến** (`sap.md` mục 9) vì HIS chỉ ghi nhận tử vong trong
viện, không xác định được tử vong ngoài viện — biến này không phải tử vong do mọi nguyên nhân đầy đủ.

## 5. Phân tích hậu kiểm và sai lệch so với đề cương

Các phân tích sau không có trong kế hoạch phân tích (`sap.md` mục 16); mang tính thăm dò, tạo giả
thuyết. Không có sai lệch (deviation) nào trong lượt chạy này — toàn bộ kết quả ở Mục 3–4 khớp đúng
bảng đăng ký A0–A5; `analysis_plan.py check` xác nhận 0 phân tích chặn, 0 cảnh báo.

### A6 — Hiệu ứng nhóm HbA1c lên tái nhập viện 1 năm theo nhóm tuổi

> POST-HOC A6: author wants to see whether the HbA1c-group effect on 1-year all-cause readmission
> differs by age (< 65 vs ≥ 65) — not registered in sap.md §16, requested because the thesis
> committee may ask about older patients and no age-stratified result has been looked at yet,
> requested by Example author, 2026-11-21. (`decisions.md`)

Mô hình hiệu chỉnh của A1 (tuổi, giới, thời gian mắc ĐTĐ, ≥1 bệnh đồng mắc) được chạy riêng trong 2
nhóm tuổi (hậu kiểm, kết quả thăm dò), cộng kiểm định tương tác nhóm HbA1c × nhóm tuổi
(likelihood-ratio).

**Bảng 3.8 (hậu kiểm, kết quả thăm dò).** OR hiệu chỉnh theo nhóm HbA1c, trong từng nhóm tuổi:
| Biến | Tuổi < 65 (n={{R-A6-001.n}}) | Tuổi ≥ 65 (n={{R-A6-008.n}}) |
|---|---|---|
| HbA1c 7–9% so với <7%, OR (KTC 95%) | {{R-A6-001.value}} ({{R-A6-001.ci}}) | {{R-A6-008.value}} ({{R-A6-008.ci}}) |
| HbA1c >9% so với <7%, OR (KTC 95%) | {{R-A6-002.value}} ({{R-A6-002.ci}}) | {{R-A6-009.value}} ({{R-A6-009.ci}}) |
| AUC | {{R-A6-007.value}} | {{R-A6-014.value}} |

**p tương tác (nhóm HbA1c × nhóm tuổi, hậu kiểm) = {{R-A6-015.value}}** (likelihood-ratio test, 2 bậc
tự do; mô hình không "MODEL FAILED" ở cả hai nhóm tuổi và ở phép kiểm tương tác).

**Diễn giải (thăm dò):** OR theo nhóm HbA1c cao hơn một chút ở nhóm <65 tuổi so với nhóm ≥65 tuổi,
nhưng p tương tác > 0,05 (lớn) — không có bằng chứng rằng hiệu ứng HbA1c khác nhau thật sự giữa hai
nhóm tuổi ở cỡ mẫu này; KTC 95% ở cả hai nhóm tuổi đều rất rộng (mỗi nhóm chỉ còn khoảng một nửa cỡ
mẫu của A1) và đều chứa 1. Kết quả này **không phải kết luận xác nhận**, chỉ trả lời câu hỏi "chưa
thấy khác biệt rõ theo tuổi ở cỡ mẫu hiện có" — không nên trích dẫn như một phát hiện độc lập trong
phần Kết quả chính của luận văn.

Dữ liệu đầy đủ: `05_analysis/output/tables/T3.8.csv`.

## 6. Lý do chọn phép kiểm và giả định

| Phân tích | Phép kiểm/mô hình | Lý do | Giả định chính (kiểm tra thế nào) |
|---|---|---|---|
| A0 Bảng 1, biến liên tục | TB ± ĐLC hoặc trung vị (KTPV) | quy tắc chuẩn tắc mặc định | Shapiro–Wilk khi n < 50; trị tuyệt đối độ lệch (skewness) khi n ≥ 50 (`crostats.describe`) |
| A0 tỷ lệ tái nhập viện/tử vong | KTC 95% Wilson (`statsmodels.proportion_confint`) | không có sẵn trong `crostats`; Wilson ổn định hơn Wald với tỷ lệ gần 0/1 hoặc n nhỏ | — |
| A1, A3 OR thô | Woolf CI (`crostats.crude_effect`) | bảng 2×2 | hiệu chỉnh Haldane nếu có ô bằng 0 (không cần ở đây) |
| A1, A2, A3 OR hiệu chỉnh | Hồi quy logistic (`crostats.fit_logistic`) | outcome nhị giá, biến hiệu chỉnh định trước theo `sap.md` mục 8 | EPV ≥ 10 (mặc định); không tách biệt hoàn toàn (kiểm tra tự động, không có "MODEL FAILED") |
| A1 VIF | `statsmodels.variance_inflation_factor` | `sap.md` mục 8 yêu cầu kiểm tra đa cộng tuyến; không có sẵn trong `crostats` | ngưỡng quy ước VIF > 5 |
| A1 tuyến tính logit | Likelihood-ratio, số hạng bậc hai | `sap.md` mục 8; không dùng Box–Tidwell (var × ln(var)) vì `dm_duration_years` có giá trị 0, ln(0) không xác định | p ≥ 0,05 → không có bằng chứng phi tuyến |
| A4 HR | Hồi quy Cox (`crostats.fit_cox`) | outcome thời gian-đến-sự kiện, kiểm duyệt tại 1 năm | giả định PH bằng phần dư Schoenfeld (rank transform) |
| Đa so sánh | Không hiệu chỉnh (Bonferroni/Holm) | `sap.md` mục 9: một outcome chính duy nhất (A1); A2–A5 là thăm dò/tạo giả thuyết | — |

**Giả định suy ra khi viết script (không hỏi lại tác giả):** nhóm HbA1c được đổi nhãn hiển thị
(`hba1c_grp3`: "<7%"/"7-9%"/">9%" → "1. <7%"/"2. 7-9%"/"3. >9%") chỉ để Bảng 1 và các mô hình hiển thị
đúng thứ tự lâm sàng (crostats sắp nhóm theo thứ tự chữ-số của chuỗi gốc, cho ra thứ tự "7-9%", "<7%",
">9%" nếu không đổi nhãn) — không làm thay đổi giá trị, nhóm tham chiếu hay kết quả thống kê. Biến
"≥1 bệnh đồng mắc" (`comorb_any`) được tính trong lúc phân tích (không thêm cột vào tệp dữ liệu) từ
`htn`/`ckd`/`cvd`, đúng định nghĩa biến nhiễu ở `variables.md` mục 3.

## 7. Hạn chế về phương pháp

- **Dữ liệu thiếu:** 27 <!-- derived: R-A0-001.n - R-A1-003.n --> người bệnh
  (2,5% <!-- derived: (R-A0-001.n - R-A1-003.n) / R-A0-001.n * 100 -->) thiếu thời gian mắc ĐTĐ bị loại khỏi
  các mô hình hiệu chỉnh (A1–A4 hiệu chỉnh) theo quy tắc phân tích ca đầy đủ đã chốt (`sap.md` mục 11:
  thiếu ≤5% ở biến hiệu chỉnh → ca đầy đủ, không impute). Đây là quyết định của tác giả, không phải
  giả định của bước phân tích này; không so sánh độ nhạy với imputation vì dưới ngưỡng áp dụng
  imputation (>5%) của `sap.md`.
- **Power:** cả hai OR/HR chính (A1, A4) đều không đạt ý nghĩa thống kê, KTC 95% rộng và chứa 1 — phù
  hợp với rủi ro power đã nêu trước khi có dữ liệu (`sample-size.md` mục 4/10, được tác giả chấp nhận
  khi mở gate G2). Không nên diễn giải "không có liên quan" từ kết quả này; đúng hơn là "chưa đủ bằng
  chứng xác nhận ở cỡ mẫu này".
- **EPV A3 thấp hơn các mô hình khác** ({{R-A3-008.value}}, do ít sự kiện tái nhập viện liên quan ĐTĐ)
  — vẫn trên ngưỡng mặc định ≥10 nhưng các OR cần diễn giải thận trọng hơn A1.
- **Nhiễu tồn dư (residual confounding):** thiết kế đoàn hệ quan sát, không ngẫu nhiên hóa — các biến
  hiệu chỉnh chỉ gồm các yếu tố định trước trong `protocol.md` mục 2.7.2; không loại trừ khả năng còn
  yếu tố nhiễu chưa đo được (ví dụ mức độ tuân thủ điều trị, kinh tế xã hội).
- **Tử vong (A5):** chỉ ghi nhận được tử vong trong viện, không phải tử vong do mọi nguyên nhân — đã
  nêu rõ trong `variables.md`, `decisions.md` và SAP; không dùng để kết luận về tử vong nói chung.
- **Kết quả phụ (A2–A5):** mang tính khám phá/tạo giả thuyết, không hiệu chỉnh đa so sánh theo
  `sap.md` mục 9 — xác suất dương tính giả tăng theo số phép kiểm; không nên trích dẫn như kết luận
  độc lập.
- **Dữ liệu mô phỏng:** mọi số liệu trong báo cáo này đến từ `tools/simulate_cohort.py`, không phải
  bệnh nhân thật — không có giá trị suy luận lâm sàng, chỉ minh họa quy trình.

## 8. Tóm tắt cho người đọc phổ thông

**Chúng tôi đã làm gì?** Chúng tôi xem xét hồ sơ của {{R-A0-001.n}} người bệnh đái tháo đường type 2
từng nhập viện, chia theo mức đường huyết trung bình (HbA1c) đo được ngay khi nhập viện, rồi theo dõi
xem trong 1 năm sau khi xuất viện họ có phải nhập viện lại không.

**Chúng tôi tìm thấy gì?**
- Tỷ lệ phải nhập viện lại trong 1 năm là {{R-A0-061.value}} tính chung cho cả nhóm; tỷ lệ này là
  {{R-A0-062.value}} ở người có đường huyết tốt (<7%) và {{R-A0-064.value}} ở người có đường huyết
  rất cao (>9%).
- Sau khi tính đến sự khác biệt về tuổi, giới, thời gian mắc bệnh và các bệnh kèm theo, nhóm đường
  huyết rất cao vẫn có xu hướng dễ phải nhập viện lại hơn, nhưng sự khác biệt này **chưa đủ chắc chắn**
  để khẳng định — có thể một phần là do ngẫu nhiên vì số người trong mỗi nhóm chưa đủ lớn.
- Tỷ lệ tử vong trong thời gian nằm viện (của một lần nhập viện sau đó) rất thấp ở cả 3 nhóm
  ({{R-A5-001.value}} tính chung).

**Điều này có ý nghĩa gì?** Kết quả gợi ý rằng kiểm soát đường huyết kém lúc nhập viện có thể liên
quan đến khả năng phải nhập viện lại cao hơn, nhưng cần nghiên cứu với nhiều người bệnh hơn để khẳng
định chắc chắn hơn trước khi áp dụng vào thực hành.

**Những gì chúng tôi chưa biết / hạn chế:**
- Một số ít người bệnh (27 <!-- derived: R-A0-001.n - R-A1-003.n -->, dưới 3% tổng số) thiếu thông
  tin về thời gian mắc bệnh đái tháo đường và không được đưa vào các so sánh có tính đến yếu tố khác.
- Đây là dữ liệu từ hồ sơ có sẵn (không phải thử nghiệm có đối chứng), nên có thể còn những yếu tố
  khác chưa đo được ảnh hưởng đến kết quả.
- Kết quả về tử vong chỉ tính được tử vong xảy ra trong lúc nằm viện, không tính được trường hợp mất
  sau khi về nhà.
- **Toàn bộ số liệu trong báo cáo này là dữ liệu mô phỏng cho mục đích minh họa, không phải số liệu
  bệnh nhân thật.**
