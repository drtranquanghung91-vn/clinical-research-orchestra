# CHƯƠNG 3. KẾT QUẢ NGHIÊN CỨU

**Dữ liệu mô phỏng.** Toàn bộ số liệu trong chương này là dữ liệu MÔ PHỎNG, sinh bởi script mô phỏng cohort của dự án ví dụ (tools/simulate_cohort.py); không phải số liệu bệnh nhân thật, không có giá trị lâm sàng.

## 3.1 Đặc điểm chung của đối tượng nghiên cứu

Dữ liệu được trích xuất từ hồ sơ bệnh án điện tử (EMR) và hệ thống thông tin bệnh viện (HIS) của Bệnh viện Mô phỏng theo tiêu chuẩn chọn và loại trừ đã định trong đề cương (phần đối tượng và phương pháp nghiên cứu, mục 2.1); quần thể phân tích mô tả gồm 1070 người bệnh đái tháo đường type 2 xuất viện giai đoạn 2021–2022, theo dõi 1 năm sau xuất viện.

[Biểu đồ 3.1: Sơ đồ luồng đối tượng nghiên cứu (sàng lọc, loại trừ, phân tích) — chờ research-figures]

Trong số 1070 người bệnh, 27 <!-- derived: R-A0-001.n - R-A1-003.n --> người (thời gian mắc đái tháo đường không ghi nhận) được xử lý theo nguyên tắc phân tích ca đầy đủ ở các mô hình hiệu chỉnh từ mục 3.2; mọi biến khác không thiếu dữ liệu.

Bảng 3.1. Đặc điểm chung của đối tượng nghiên cứu theo nhóm HbA1c lúc nhập viện (n = 1070)
| Đặc điểm | Chung | <7% | 7–9% | >9% |
|---|---|---|---|---|
| Tuổi (năm), TB ± ĐLC | 63,1 ± 10,5 | 63,7 ± 10,8 | 63,2 ± 10,4 | 62,4 ± 10,3 |
| Nữ, n (%) | 536 (50,1%) | 110 (46,8%) | 254 (49,4%) | 172 (53,6%) |
| Thời gian mắc ĐTĐ (năm), TB ± ĐLC | 9,2 ± 5,2 | 9,0 ± 5,3 | 9,2 ± 5,2 | 9,1 ± 5,3 |
| Tăng huyết áp, n (%) | 374 (35,0%) | 89 (37,9%) | 166 (32,3%) | 119 (37,1%) |
| Bệnh thận mạn, n (%) | 151 (14,1%) | 35 (14,9%) | 77 (15,0%) | 39 (12,1%) |
| Bệnh tim mạch, n (%) | 188 (17,6%) | 48 (20,4%) | 96 (18,7%) | 44 (13,7%) |
| ≥1 bệnh đồng mắc, n (%) | 575 (53,7%) | 136 (57,9%) | 274 (53,3%) | 165 (51,4%) |
| Dùng insulin khi nằm viện, n (%) | 322 (30,1%) | 33 (14,0%) | 129 (25,1%) | 160 (49,8%) |
| Thời gian nằm viện (ngày), trung vị (KTPV) | 7,0 (5,0–10,0) | 7,0 (5,0–9,5) | 7,0 (5,0–10,0) | 7,0 (5,0–9,0) |
Nguồn: số liệu nghiên cứu (mô phỏng).
Ghi chú: ĐLC: độ lệch chuẩn; KTPV: khoảng tứ phân vị; ≥1 bệnh đồng mắc = có ít nhất 1 trong tăng huyết áp, bệnh thận mạn, bệnh tim mạch; không kèm giá trị p so sánh 3 nhóm (thiết kế quan sát, không phải thử nghiệm ngẫu nhiên).

Nhận xét: Tuổi trung bình của 1070 người bệnh là 63,1 ± 10,5 năm, tương đồng giữa 3 nhóm HbA1c; trong đó nữ chiếm 536 (50,1%). Nhóm HbA1c >9% có tỷ lệ dùng insulin khi nằm viện (160 (49,8%)) cao hơn rõ so với nhóm <7% (33 (14,0%)), phù hợp thực hành kiểm soát đường huyết; đây là biến mô tả, không hiệu chỉnh trong mô hình chính vì là trung gian nghi ngờ.

Bảng 3.2. Tỷ lệ tái nhập viện mọi nguyên nhân trong 1 năm, chung và theo nhóm HbA1c
| Nhóm HbA1c | N | Tái nhập viện, n (%) | KTC 95% |
|---|---|---|---|
| Chung | 1070 | 236<!-- derived: R-A0-061.count --> (22,1%) | 19,7–24,6 |
| <7% | 235 | 46<!-- derived: R-A0-062.count --> (19,6%) | 15,0–25,1 |
| 7–9% | 514 | 108<!-- derived: R-A0-063.count --> (21,0%) | 17,7–24,7 |
| >9% | 321 | 82<!-- derived: R-A0-064.count --> (25,5%) | 21,1–30,6 |
Nguồn: số liệu nghiên cứu (mô phỏng).
Ghi chú: N: số người bệnh trong nhóm; n: số người tái nhập viện; KTC: khoảng tin cậy, phương pháp Wilson.

Nhận xét: Tỷ lệ tái nhập viện mọi nguyên nhân trong 1 năm chung là 22,1% (KTC 95%: 19,7–24,6); tỷ lệ này tăng dần theo nhóm HbA1c, từ 19,6% ở nhóm <7% đến 25,5% ở nhóm >9%, nhưng khoảng tin cậy của 3 nhóm còn chồng lấp.

## 3.2 Mối liên quan giữa HbA1c lúc nhập viện và tái nhập viện trong 1 năm (Mục tiêu 2)

### 3.2.1 Phân tích thô

So với nhóm HbA1c <7% (tham chiếu), tỷ số chênh thô của tái nhập viện là 1,09 (KTC 95%: 0,74–1,61) ở nhóm 7–9% và 1,41 (KTC 95%: 0,94–2,12) ở nhóm >9%; cả hai khoảng tin cậy đều chứa giá trị 1.

### 3.2.2 Phân tích hiệu chỉnh

Bảng 3.3. Tái nhập viện mọi nguyên nhân trong 1 năm theo nhóm HbA1c: tỷ số chênh thô và hiệu chỉnh
| Biến | OR thô (KTC 95%) | OR hiệu chỉnh (KTC 95%) | p (hiệu chỉnh) |
|---|---|---|---|
| HbA1c 7–9% so với <7% | 1,09 (0,74–1,61) | 1,10 (0,74–1,62) | 0,641 |
| HbA1c >9% so với <7% | 1,41 (0,94–2,12) | 1,42 (0,94–2,15) | 0,097 |
| Giới (Nữ so với Nam) | | 0,92 (0,69–1,24) | 0,601 |
| Tuổi (mỗi năm) | | 1,02 (1,00–1,03) | 0,017 |
| Thời gian mắc ĐTĐ (mỗi năm) | | 1,01 (0,98–1,04) | 0,379 |
| ≥1 bệnh đồng mắc | | 1,38 (1,01–1,89) | 0,043 |
Nguồn: số liệu nghiên cứu (mô phỏng); hồi quy logistic đa biến, script phân tích analysis.py (A1).
Ghi chú: OR: tỷ số chênh; KTC: khoảng tin cậy; hiệu chỉnh theo tuổi, giới, thời gian mắc ĐTĐ, ≥1 bệnh đồng mắc.

Nhận xét: Sau hiệu chỉnh theo tuổi, giới, thời gian mắc đái tháo đường và bệnh đồng mắc, nhóm HbA1c >9% có tỷ số chênh tái nhập viện là 1,42 so với nhóm <7% (KTC 95%: 0,94–2,15; p = 0,097) và nhóm 7–9% là 1,10 (KTC 95%: 0,74–1,62; p = 0,641); cả hai khoảng tin cậy đều chứa giá trị 1 nên ước lượng còn kém chính xác, tương thích với từ không khác biệt đến tăng vừa phải nguy cơ tái nhập viện, chưa đủ bằng chứng xác nhận mối liên quan ở cỡ mẫu này. Mô hình có diện tích dưới đường cong ROC là 0,588 và số sự kiện trên mỗi biến (EPV) là 39 <!-- derived: R-A1-010.value, làm tròn đến số nguyên -->; EPV ≥ 10 <!-- not-a-result: ngưỡng mặc định EPV --> nên không có cảnh báo về số biến cố trên mỗi biến.

## 3.3 Kết quả các phân tích phụ

### 3.3.1 HbA1c liên tục thay cho 3 nhóm

Bảng 3.4. Tái nhập viện mọi nguyên nhân trong 1 năm theo HbA1c liên tục (mỗi 1%), OR hiệu chỉnh
| Biến | OR hiệu chỉnh (KTC 95%) | p |
|---|---|---|
| HbA1c (mỗi 1%) | 1,02 (0,93–1,11) | 0,677 |
| Giới (Nữ so với Nam) | 0,93 (0,70–1,25) | 0,652 |
| Tuổi (mỗi năm) | 1,02 (1,00–1,03) | 0,020 |
| Thời gian mắc ĐTĐ (mỗi năm) | 1,01 (0,98–1,04) | 0,378 |
| ≥1 bệnh đồng mắc | 1,37 (1,01–1,88) | 0,046 |
Nguồn: số liệu nghiên cứu (mô phỏng); hồi quy logistic đa biến, script phân tích analysis.py (A2).
Ghi chú: OR: tỷ số chênh; KTC: khoảng tin cậy; phân tích phụ, thăm dò, không hiệu chỉnh đa so sánh.

Nhận xét: Mỗi 1% HbA1c tăng thêm liên quan với tỷ số chênh tái nhập viện hiệu chỉnh là 1,02 (KTC 95%: 0,93–1,11; p = 0,677); khoảng tin cậy hẹp quanh giá trị 1, tương thích với khác biệt nhỏ hoặc không có khác biệt theo mỗi 1% HbA1c. Đây là phân tích phụ, mang tính thăm dò, không hiệu chỉnh đa so sánh.

### 3.3.2 Tái nhập viện liên quan đái tháo đường trong 1 năm

Bảng 3.5. Tái nhập viện liên quan đái tháo đường trong 1 năm theo nhóm HbA1c, OR hiệu chỉnh
| Biến | OR hiệu chỉnh (KTC 95%) | p |
|---|---|---|
| HbA1c 7–9% so với <7% | 2,97 (1,31–6,73) | 0,009 |
| HbA1c >9% so với <7% | 5,50 (2,42–12,49) | < 0,001 |
| Giới (Nữ so với Nam) | 0,85 (0,55–1,31) | 0,457 |
| Tuổi (mỗi năm) | 1,01 (0,99–1,03) | 0,314 |
| Thời gian mắc ĐTĐ (mỗi năm) | 1,02 (0,98–1,06) | 0,302 |
| ≥1 bệnh đồng mắc | 1,54 (0,96–2,45) | 0,071 |
Nguồn: số liệu nghiên cứu (mô phỏng); hồi quy logistic đa biến, script phân tích analysis.py (A3).
Ghi chú: OR: tỷ số chênh; KTC: khoảng tin cậy; phân tích phụ, thăm dò, không hiệu chỉnh đa so sánh.

Nhận xét: Nhóm HbA1c 7–9% và >9% có tỷ số chênh tái nhập viện liên quan đái tháo đường hiệu chỉnh cao hơn rõ so với nhóm <7%, tương ứng 2,97 (KTC 95%: 1,31–6,73; p = 0,009) và 5,50 (KTC 95%: 2,42–12,49; p < 0,001); khoảng tin cậy không chứa giá trị 1 nhưng còn khá rộng. Đây là kết cục phụ, mang tính thăm dò, cần xem là giả thuyết cần kiểm định lại ở nghiên cứu khác, không phải kết luận xác nhận.

### 3.3.3 Thời gian đến lần tái nhập viện đầu tiên

Bảng 3.6. Thời gian đến lần tái nhập viện đầu tiên theo nhóm HbA1c: tỷ số nguy cơ thô và hiệu chỉnh
| Biến | HR thô (KTC 95%) | HR hiệu chỉnh (KTC 95%) | p (hiệu chỉnh) |
|---|---|---|---|
| HbA1c 7–9% so với <7% | 1,07 (0,76–1,52) | 1,07 (0,75–1,51) | 0,717 |
| HbA1c >9% so với <7% | 1,35 (0,94–1,94) | 1,35 (0,94–1,93) | 0,109 |
| Tuổi (mỗi năm) | | 1,02 (1,00–1,03) | 0,023 |
| Giới (Nữ so với Nam) | | 0,94 (0,73–1,22) | 0,647 |
| Thời gian mắc ĐTĐ (mỗi năm) | | 1,01 (0,99–1,04) | 0,407 |
| ≥1 bệnh đồng mắc | | 1,33 (1,01–1,76) | 0,043 |
Nguồn: số liệu nghiên cứu (mô phỏng); hồi quy Cox, kiểm duyệt tại 1 năm, script phân tích analysis.py (A4).
Ghi chú: HR: tỷ số nguy cơ; KTC: khoảng tin cậy; phân tích phụ, thăm dò; giả định tỷ số nguy cơ không đổi theo thời gian được kiểm tra bằng phần dư Schoenfeld, không ghi nhận vi phạm ở cả hai mô hình.

Nhận xét: Thời gian đến lần tái nhập viện đầu tiên có xu hướng ngắn hơn ở nhóm HbA1c cao hơn, với tỷ số nguy cơ hiệu chỉnh là 1,35 ở nhóm >9% (KTC 95%: 0,94–1,93; p = 0,109) và 1,07 ở nhóm 7–9% (KTC 95%: 0,75–1,51; p = 0,717) so với nhóm <7%; cả hai khoảng tin cậy đều chứa giá trị 1, hướng và độ lớn tương tự tỷ số chênh ở mục 3.2.2.

### 3.3.4 Tử vong trong viện trong 1 năm

Bảng 3.7. Tỷ lệ tử vong trong viện trong 1 năm, chung và theo nhóm HbA1c
| Nhóm HbA1c | n | Tử vong trong viện (%) | KTC 95% |
|---|---|---|---|
| Chung | 1070 | 2,2% | 1,5–3,3 |
| <7% | 235 | 1,3% | 0,4–3,7 |
| 7–9% | 514 | 2,3% | 1,3–4,0 |
| >9% | 321 | 2,8% | 1,5–5,2 |
Nguồn: số liệu nghiên cứu (mô phỏng).
Ghi chú: KTC: khoảng tin cậy, phương pháp Wilson; chỉ ghi nhận được tử vong trong viện (không phải tử vong do mọi nguyên nhân); chỉ thống kê mô tả, không phân tích đa biến.

Nhận xét: Tỷ lệ tử vong trong viện trong 1 năm thấp ở cả 3 nhóm HbA1c, từ 1,3% ở nhóm <7% đến 2,8% ở nhóm >9% (chung: 2,2%); kết cục này không đầy đủ (không xác định được tử vong ngoài viện) nên chỉ mang tính mô tả.

## 3.4 Phân tích thăm dò (hậu kiểm)

Phân tích thăm dò (hậu kiểm) theo nhóm tuổi (<65 và ≥65), không có trong kế hoạch phân tích, được thực hiện theo yêu cầu của tác giả ngày 2026-11-21 (ghi nhận là phân tích hậu kiểm A6 trong nhật ký quyết định của đề tài) để kiểm tra hiệu ứng nhóm HbA1c lên tái nhập viện 1 năm có khác nhau theo tuổi không.

Bảng 3.8 (hậu kiểm, kết quả thăm dò). Tái nhập viện mọi nguyên nhân trong 1 năm theo nhóm HbA1c, OR hiệu chỉnh trong từng nhóm tuổi
| Biến | Tuổi <65 (n = 572) | Tuổi ≥65 (n = 471) |
|---|---|---|
| HbA1c 7–9% so với <7%, OR (KTC 95%) | 1,22 (0,67–2,23) | 1,00 (0,59–1,69) |
| HbA1c >9% so với <7%, OR (KTC 95%) | 1,61 (0,86–3,02) | 1,27 (0,72–2,24) |
Nguồn: số liệu nghiên cứu (mô phỏng); hồi quy logistic đa biến trong từng nhóm tuổi, hậu kiểm, script phân tích analysis.py (A6).
Ghi chú: OR: tỷ số chênh; KTC: khoảng tin cậy; cùng biến hiệu chỉnh như mục 3.2.2; kết quả thăm dò, không có trong kế hoạch phân tích.

Phân tích thăm dò (hậu kiểm) theo nhóm tuổi cho thấy OR hiệu chỉnh của nhóm HbA1c >9% so với <7% là 1,61 ở người <65 tuổi và 1,27 ở người ≥65 tuổi, với p kiểm định tương tác nhóm HbA1c × nhóm tuổi là 0,835; khoảng tin cậy ở cả hai nhóm tuổi đều chứa giá trị 1 và p tương tác lớn, nên chưa có bằng chứng hiệu ứng HbA1c khác nhau thật sự theo tuổi ở cỡ mẫu này — kết quả này chỉ mang tính tạo giả thuyết, cần nghiên cứu xác nhận thêm, không nên trích dẫn như một kết luận độc lập.
