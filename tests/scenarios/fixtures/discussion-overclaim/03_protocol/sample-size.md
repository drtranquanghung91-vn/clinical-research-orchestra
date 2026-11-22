# Tính cỡ mẫu

> **Giả định / Assumptions.** Theo yêu cầu của tác giả (Example author, 2026-11-21): "tham số nào
> không có nguồn thì ghi GIẢ ĐỊNH và làm luôn". `02_evidence/gaps.md` (Gap 1) đã xác nhận: **không có
> nghiên cứu nào đo được tỷ lệ tái nhập viện 1 năm hoặc hiệu ứng của HbA1c ở đúng mốc 1 năm** cho ĐTĐ
> type 2 nói chung. Vì vậy, hai tham số quan trọng nhất của phần tính cỡ mẫu này —
> **(1) tỷ lệ tái nhập viện 1 năm ở nhóm tham chiếu (HbA1c < 7%)** và **(2) độ lớn hiệu ứng kỳ vọng
> (OR) giữa nhóm HbA1c > 9% và nhóm tham chiếu** — đều được ghi **GIẢ ĐỊNH**, không có trích dẫn.
> Đây là **giả định rủi ro nhất** của toàn bộ đề cương (đưa vào mục "cần xác nhận" ở cuối file).
> Theo mẫu đoạn văn chuẩn của `sample-size-formulas.md`: *"Các giá trị tỷ lệ tái nhập viện 1 năm ở
> nhóm tham chiếu và OR kỳ vọng là giả định, cần thay bằng số liệu có trích dẫn (ví dụ từ một khảo
> sát hồi cứu nhỏ trên hồ sơ thật) trước khi khoá đề cương chính thức."*

## 1. Tóm tắt PECO + thiết kế

Đoàn hệ hồi cứu, đơn trung tâm. P: ĐTĐ type 2 ≥ 18 tuổi, xuất viện tại Khoa Nội tiết, Bệnh viện Mô
phỏng, 01/01/2021–31/12/2022. E: HbA1c lúc nhập viện (3 nhóm < 7% / 7–9% / > 9%, nhóm < 7% tham
chiếu; phân tích phụ: liên tục mỗi 1%). O chính: tái nhập viện mọi nguyên nhân trong 1 năm (nhị giá).
Phân tích chính: hồi quy logistic đa biến, hiệu chỉnh 4 biến nhiễu (tuổi, giới, thời gian mắc ĐTĐ,
bệnh đồng mắc) — xem `03_protocol/protocol.md`.

## 2. Bảng tham số, kèm nguồn hoặc GIẢ ĐỊNH

| Tham số | Giá trị chọn | Nguồn | Khoảng dao động trong y văn |
|---|---|---|---|
| α (hai phía) | 0,05 | Mặc định (`sample-size-formulas.md`) | — |
| Power | 0,80 | Mặc định — không phải thử nghiệm xác nhận/outcome tử vong, không cần 0,90 | — |
| Tỷ lệ mất dữ liệu/loại trừ | Không áp dụng công thức dropout (đây là lấy mẫu toàn bộ hồi cứu, không "theo dõi mất dấu" theo nghĩa tiến cứu) — rủi ro tương đương được xử lý bằng cách so cỡ mẫu **khả dụng sau loại trừ** với cỡ mẫu **yêu cầu** (mục 4), không nhân thêm hệ số dropout | — | — |
| **Tỷ lệ tái nhập viện 1 năm, nhóm tham chiếu (HbA1c < 7%), p₁** | **0,20 — GIẢ ĐỊNH** | Không có nguồn trực tiếp (Gap 1). Suy luận thận trọng: tỷ lệ tái nhập viện **30 ngày** ở ĐTĐ type 2 nói chung là 10,9% [1] và tỷ lệ **31 ngày** là 18,5% [2] (cả hai là tỷ lệ của toàn mẫu, không riêng nhóm HbA1c thấp); ngoại suy lên mốc 1 năm cho riêng nhóm kiểm soát tốt (thường có nguy cơ thấp hơn trung bình) được giả định ở mức 20% — **đây là ước lượng của người thẩm định, không phải số liệu đo được** | Tỷ lệ tái nhập viện 1 năm ở ĐTĐ type 2 nói chung trong y văn quốc tế (ngoài phạm vi 6 tài liệu đã xác minh của dự án) thường được báo cáo trong khoảng 15–40% tùy quần thể — khoảng này **chưa được xác minh trong dự án**, chỉ nêu để người đọc biết thứ tự độ lớn |
| **OR kỳ vọng, nhóm HbA1c > 9% so với < 7%, tại 1 năm** | **1,5 — GIẢ ĐỊNH** | Không có nguồn trực tiếp (Gap 1). Tham khảo thận trọng: [1] báo cáo aOR 1,15 cho mỗi 1% HbA1c tăng (tái nhập viện 30 ngày); nếu ngoại suy đơn giản theo thang log-odds cho khoảng cách ~4–5% HbA1c giữa hai nhóm cực, kết quả lý thuyết sẽ là 1,15⁴ đến 1,15⁵ ≈ 1,75–2,01 — **giá trị này được xem là lạc quan** (ngoại suy xa ngoài phạm vi đo, khác mốc thời gian, khác quần thể tuổi). Theo nguyên tắc DELTA2 (chọn giá trị "thận trọng", không chọn giá trị lạc quan nhất), **giảm xuống OR = 1,5** làm giá trị tính cỡ mẫu chính | Phân tích độ nhạy ở mục 5 thay đổi OR trong khoảng 1,3–2,0 |
| p₂ (tính từ p₁, OR) | 0,2727 | Công thức: p₂ = OR·p₁/(1−p₁+OR·p₁) = 1,5×0,20/(0,80+0,30) = 0,2727 | — |
| Số biến (tham số) trong mô hình hồi quy đa biến | 6 | HbA1c 3 nhóm = 2 biến giả (dummy) + tuổi + giới + thời gian mắc ĐTĐ + bệnh đồng mắc = 2+4 = 6, theo `03_protocol/protocol.md` mục 2.7.2 | — |
| EPV (events per variable) | 10 (tối thiểu), báo cáo thêm 20 ở độ nhạy | Mặc định (Peduzzi 1996, nêu trong `sample-size-formulas.md` — chưa trích dẫn PMID trong dự án này, chỉ dùng như quy tắc chung đã được skill xác nhận) | 10–20 |
| Cỡ mẫu khả dụng trước loại trừ | ~1.200 | Tác giả xác nhận trực tiếp: ~50 bệnh nhân ĐTĐ type 2 xuất viện/tháng × 24 tháng | — |

## 3. Kết quả tính cỡ mẫu (từ `samplesize.py`, không tính tay)

### 3a. Theo quy tắc EPV cho mô hình hồi quy đa biến (ổn định mô hình)

```
python samplesize.py regression-epv --predictors 6 --epv 10 --p-outcome 0.20 --json
→ events_required 60, n_total_final 300

python samplesize.py regression-epv --predictors 6 --epv 20 --p-outcome 0.20 --json
→ events_required 120, n_total_final 600
```

**n tối thiểu để mô hình ổn định (EPV ≥ 10): 300 người bệnh** (toàn mẫu, không riêng từng nhóm);
báo cáo thêm ở EPV = 20: **600 người bệnh**.

### 3b. Theo kiểm định tỷ lệ đơn giản (two-proportions), so sánh 2 nhóm cực (> 9% vs < 7%)

```
python samplesize.py two-props --p1 0.20 --p2 0.2727 --json
→ n1_raw 534.89, n1_final 535, n2_final 535, n_total_final 1070, RR 1,363, OR 1,5
```

**n tối thiểu theo kiểm định đơn giản: 535 người bệnh mỗi nhóm cực (1.070 tổng cho riêng 2 trong 3
nhóm)**, với giả thuyết OR = 1,5.

### 3c. Lấy giá trị lớn hơn (theo nguyên tắc chuẩn khi so sánh 2 cách tính cho cùng mục tiêu phân tích)

**n yêu cầu = 1.070** (lớn hơn giữa 300–600 theo EPV và 1.070 theo kiểm định tỷ lệ đơn giản). Lưu ý
quan trọng theo `test-selection.md`: "nếu phân tích chính là mô hình hồi quy có hiệu chỉnh, tính n
theo kiểm định đơn giản tương ứng rồi nêu mô hình hiệu chỉnh trong SAP — hiệu chỉnh đa biến thường
làm **tăng** power, nên con số từ kiểm định đơn giản là cách tính **thận trọng** (có thể cao hơn thực
tế cần)". Vì vậy 1.070 là ước lượng thận trọng, không phải con số tuyệt đối.

## 4. So sánh với cỡ mẫu khả dụng — đánh giá khả thi

| | Yêu cầu | Khả dụng (trước loại trừ) |
|---|---|---|
| Tổng mẫu | 1.070 (cho 2 trong 3 nhóm) hoặc 300–600 (theo EPV, toàn mẫu) | ~1.200 |
| Mỗi nhóm cực (< 7% và > 9%) | 535/nhóm | **Chưa biết** — tùy phân bố HbA1c thật trong quần thể; nếu 3 nhóm chia đều ~400/nhóm, **sẽ không đủ 535** |

**Đánh giá:** Theo quy tắc EPV, cỡ mẫu ~1.200 (hoặc ít hơn sau loại trừ) **thừa đủ** để mô hình hồi
quy đa biến ổn định (300–600 cần, có 1.200). Nhưng theo kiểm định tỷ lệ đơn giản với giả định
OR = 1,5, **cần ~535 người ở MỖI nhóm cực** — nếu nhóm HbA1c < 7% hoặc > 9% chỉ là một phần nhỏ của
tổng mẫu 1.200 (ví dụ nhóm 7–9% thường là nhóm lớn nhất trên thực tế lâm sàng), đề tài **có thể không
đủ power 80%** để phát hiện hiệu ứng ở mức giả định này.

**Power đạt được theo cỡ mẫu nhóm thực tế có thể xảy ra** (`samplesize.py power --design two-props`):

| n mỗi nhóm cực | Power đạt được (α = 0,05, OR giả định = 1,5) |
|---|---|
| 300 | 0,554 |
| 400 | 0,678 |
| 500 | 0,773 |
| 535 (yêu cầu đủ 80%) | 0,80 |

**Kết luận khả thi:** Đề tài **đủ cỡ mẫu cho mục tiêu mô tả và cho việc xây dựng mô hình hồi quy đa
biến ổn định** (EPV), nhưng **có thể thiếu power** cho so sánh cụ thể giữa 2 nhóm HbA1c cực nếu các
nhóm không đủ lớn — đây chính là **giả định rủi ro nhất** của bước này (mục 6, cần xác nhận). Khuyến
nghị: (a) kiểm tra phân bố thật của 3 nhóm HbA1c trên một mẫu nhỏ hồ sơ trước khi triển khai chính
thức; (b) nếu nhóm cực quá nhỏ, báo cáo power đạt được thực tế một cách minh bạch thay vì khẳng định
"đủ cỡ mẫu"; (c) phân tích phụ dùng HbA1c liên tục (mỗi 1%) sẽ có power cao hơn phân tích 3 nhóm vì
dùng toàn bộ thông tin liên tục, không chia nhỏ mẫu theo nhóm.

## 5. Bảng phân tích độ nhạy (tham số không chắc chắn nhất: OR giả định)

```
python samplesize.py sensitivity --design two-props --p1 0.20 --p2 0.2727 --vary p2 --values 0.24,0.26,0.2727,0.30,0.33
```

| p₂ (và OR tương ứng) | n mỗi nhóm | n tổng (2 nhóm) |
|---|---|---|
| 0,24 (OR ≈ 1,26) | 1.683 | 3.366 |
| 0,26 (OR ≈ 1,40) | 772 | 1.544 |
| 0,2727 (OR = 1,5, **giá trị chính**) | 535 | 1.070 |
| 0,30 (OR ≈ 1,71) | 294 | 588 |
| 0,33 (OR ≈ 1,97) | 180 | 360 |

**Đọc bảng:** nếu hiệu ứng thật nhỏ hơn giả định (OR gần 1,3), cỡ mẫu cần tăng rất nhanh (lên đến hơn
1.500/nhóm) — vượt xa khả năng của một trung tâm; nếu hiệu ứng thật lớn hơn giả định (OR ≈ 2,0), cỡ
mẫu cần giảm xuống còn ~180/nhóm, hoàn toàn khả thi. **Vì không có bằng chứng trực tiếp (GRADE rất
thấp, `02_evidence/appraisal/summary.md`), khoảng dao động này là lý do chính khiến phần tính cỡ mẫu
này cần được coi là sơ bộ, không phải con số cuối cùng.**

Phân tích độ nhạy theo EPV (tham số p_outcome — tỷ lệ tái nhập viện giả định):

```
python samplesize.py sensitivity --design regression-epv --predictors 6 --p-outcome 0.20 --vary p_outcome --values 0.10,0.15,0.20,0.25,0.30
```

| Tỷ lệ outcome giả định | n tổng cần (EPV = 10) |
|---|---|
| 0,10 | 600 |
| 0,15 | 400 |
| 0,20 (giá trị chính) | 300 |
| 0,25 | 240 |
| 0,30 | 200 |

## 6. Kiểm định thứ cấp (Cox, thời gian-đến-tái nhập viện) — kiểm tra power

Với HR giả định cũng là 1,5 (nhất quán với OR giả định ở phân tích chính) và tỷ lệ sự kiện nhóm tham
chiếu 0,20 trong 1 năm (cùng giả định p₁):

```
python samplesize.py survival --hr 1.5 --p-event-ctrl 0.20 --json
→ events_required 191, n1_final 395, n2_final 395, n_total_final 790
```

Với số sự kiện thực tế có thể đạt được thấp hơn (ví dụ chỉ ~150 sự kiện nếu tỷ lệ tái nhập viện thật
thấp hơn giả định):

```
python samplesize.py power --design survival --n 150 --hr 1.5 --json → power 0,6995
python samplesize.py power --design survival --n 191 --hr 1.5 --json → power 0,8001 (đúng theo thiết kế)
```

**Lưu ý quan trọng đã xác nhận ở `protocol.md`:** phân tích Cox chính dùng tử vong ngoài viện (không
xác định được) như censored — có thể vi phạm giả định censoring không mang thông tin nếu tử vong có
liên quan đến HbA1c; Fine-Gray chỉ là phân tích độ nhạy vì HIS chỉ bắt được tử vong trong viện.

## 7. Đoạn văn giải thích cỡ mẫu (để dán vào đề cương, mục 2.3.2)

Cỡ mẫu được tính cho outcome chính là tái nhập viện mọi nguyên nhân trong 1 năm, với thiết kế đoàn hệ
hồi cứu so sánh 3 nhóm HbA1c lúc nhập viện (< 7% / 7–9% / > 9%, nhóm < 7% tham chiếu). **Vì chưa có
nghiên cứu nào đo trực tiếp tỷ lệ tái nhập viện 1 năm hoặc hiệu ứng của HbA1c ở đúng mốc 1 năm cho
ĐTĐ type 2 nói chung** (Gap 1, `02_evidence/gaps.md`), tỷ lệ tái nhập viện ở nhóm tham chiếu được
**giả định** là 20% và tỷ số chênh (OR) kỳ vọng giữa nhóm HbA1c > 9% và nhóm tham chiếu được **giả
định** là 1,5 (lựa chọn thận trọng theo DELTA2, thấp hơn mức ngoại suy lạc quan ~1,75–2,0 từ
[1]). Với α = 0,05 (hai phía) và power = 80%, cần 535 người bệnh mỗi nhóm cực (1.070 tổng cho
riêng 2 nhóm cực) theo kiểm định tỷ lệ đơn giản; theo quy tắc số sự kiện/biến (EPV ≥ 10) cho mô hình
hồi quy đa biến 6 biến, cần tối thiểu 300 người bệnh (toàn mẫu). Lấy giá trị lớn hơn, thận trọng, là
**1.070 người bệnh** — gần với cỡ mẫu khả dụng ước tính trước loại trừ (~1.200), nên đề tài **có thể
chỉ đủ hoặc thiếu power** cho so sánh 2 nhóm HbA1c cực, tùy vào phân bố thật của HbA1c trong quần thể
(chưa xác định được ở bước lập kế hoạch này). Tính bằng `samplesize.py` (two-proportions;
regression-EPV). Phân tích độ nhạy cho thấy nếu OR thật nằm trong khoảng 1,3–2,0, cỡ mẫu cần dao
động từ 180 đến hơn 1.600 người mỗi nhóm cực (360 đến hơn 3.300 người cho 2 nhóm). **Các giá trị tỷ lệ tái nhập viện 1 năm ở nhóm tham
chiếu (20%) và OR kỳ vọng (1,5) là giả định, cần thay bằng số liệu có trích dẫn (ví dụ một khảo sát
nhỏ trên hồ sơ thật) trước khi khoá đề cương chính thức.**

## 8. Giải thích cho hội đồng (Explaining to the committee)

- **Vì sao dùng giả định cho tỷ lệ outcome và OR?** Vì đây đúng là khoảng trống nghiên cứu mà đề tài
  hướng tới lấp đầy (Gap 1) — không có nghiên cứu nào đã đo được các số này ở đúng mốc 1 năm, đúng
  phơi nhiễm (HbA1c lúc nhập viện), đúng quần thể (ĐTĐ type 2 nói chung).
- **Vì sao chọn OR = 1,5, không chọn số ngoại suy ~1,75–2,0?** Theo nguyên tắc DELTA2, giá trị mục
  tiêu phải "thận trọng", không phải giá trị lạc quan nhất có thể ngoại suy được.
- **Vì sao tính cả EPV và kiểm định tỷ lệ đơn giản?** Vì phân tích chính là hồi quy đa biến có hiệu
  chỉnh — EPV đảm bảo mô hình ổn định (đủ sự kiện cho mỗi biến), còn kiểm định tỷ lệ đơn giản ước
  lượng khả năng phát hiện đúng hiệu ứng (power); dùng cả hai và lấy giá trị thận trọng hơn.
- **Câu hỏi hội đồng có thể hỏi #1**: "Nếu không đủ power, kết quả có còn giá trị không?" — Trả lời:
  có, miễn là báo cáo trung thực power đạt được thực tế (post-hoc) và đọc khoảng tin cậy theo vùng ý
  nghĩa lâm sàng, không chỉ bằng p; một kết quả "chưa đủ bằng chứng" với khoảng tin cậy rộng vẫn có
  giá trị khoa học nếu được diễn giải đúng.
- **Câu hỏi #2**: "Vì sao không khảo sát toàn bộ tuyến tỉnh để tăng cỡ mẫu?" — Trả lời: ngoài phạm vi
  nguồn lực và kinh phí hiện có (đã xác nhận với tác giả); đây là một hạn chế đã nêu trong đề cương.
- **Câu hỏi #3**: "Phân tích HbA1c liên tục có thay thế được phân tích 3 nhóm không?" — Trả lời: có
  thể dùng như phân tích phụ với power cao hơn (không mất thông tin do chia nhóm), nhưng phân tích 3
  nhóm được giữ làm chính vì dễ diễn giải lâm sàng theo ngưỡng kiểm soát đường huyết.

## 9. Kiểm định chính và kiểm định thay thế

- **Kiểm định chính:** hồi quy logistic đa biến (outcome nhị giá, hiệu chỉnh nhiễu) — khớp với cỡ mẫu
  tính ở mục 3a/3b theo `test-selection.md` (outcome nhị giá, ≥ 3 nhóm, có hiệu chỉnh → logistic
  regression).
- **Kiểm định thay thế:** nếu cỡ mẫu nhóm cực quá nhỏ để chạy mô hình đa biến ổn định, dùng kiểm định
  χ² (hoặc Fisher exact nếu có ô kỳ vọng < 5) cho phân tích đơn biến không hiệu chỉnh, nêu rõ là phân
  tích thay thế do hạn chế cỡ mẫu.
- **Kiểm định phụ:** hồi quy Cox (thời gian-đến-tái nhập viện); Fine-Gray chỉ là phân tích độ nhạy
  (xem mục 6 và `protocol.md`).

## 10. Mục cần tác giả xác nhận (giả định rủi ro nhất)

Theo chỉ đạo của tác giả ("làm luôn, không cần hỏi lại"), các giả định dưới đây **đã được áp dụng để
tính xong** cỡ mẫu, nhưng vẫn là giả định rủi ro nhất cần thay bằng số liệu thật trước khi khóa đề
cương chính thức:
1. Tỷ lệ tái nhập viện 1 năm ở nhóm HbA1c < 7% = 20% (giả định).
2. OR kỳ vọng giữa nhóm HbA1c > 9% và < 7% tại 1 năm = 1,5 (giả định).
3. Phân bố thực tế của 3 nhóm HbA1c trong quần thể ~1.200 người bệnh (ảnh hưởng trực tiếp đến việc có
   đủ 535 người/nhóm cực hay không) — **chưa biết**, khuyến nghị kiểm tra trên một mẫu nhỏ hồ sơ thật
   trước khi triển khai chính thức.

## Tài liệu tham khảo

1. Hu X, Su X, Chen S, Wang Q, He F, Zhang R. Predictors of 30-day readmission in young and middle-aged T2DM patients: a retrospective cohort study. Endocrine. 2026;91(1). doi:10.1007/s12020-026-04626-3. PMID: 42068438.
2. Cao J, Shi Q, Yu Z, Xie H. A nomogram incorporating nutritional risk for predicting 31-day unplanned readmission in adults with type 2 diabetes mellitus using LASSO regression. Front Nutr. 2026;13:1863130. doi:10.3389/fnut.2026.1863130. PMID: 42876841.
