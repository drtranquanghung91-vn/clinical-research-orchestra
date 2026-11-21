# CHƯƠNG 3. KẾT QUẢ NGHIÊN CỨU

**Dữ liệu mô phỏng.** Toàn bộ số liệu trong chương này là dữ liệu MÔ PHỎNG, sinh bởi script mô phỏng cohort của dự án ví dụ (tools/simulate_cohort.py); không phải số liệu bệnh nhân thật, không có giá trị lâm sàng.

## 3.1 Đặc điểm chung của đối tượng nghiên cứu

Dữ liệu được trích xuất từ hồ sơ bệnh án điện tử (EMR) và hệ thống thông tin bệnh viện (HIS) của Bệnh viện Mô phỏng theo tiêu chuẩn chọn và loại trừ đã định trong đề cương (phần đối tượng và phương pháp nghiên cứu, mục 2.1); quần thể phân tích mô tả gồm {{R-A0-001.n}} người bệnh đái tháo đường type 2 xuất viện giai đoạn 2021–2022, theo dõi 1 năm sau xuất viện.

[Biểu đồ 3.1: Sơ đồ luồng đối tượng nghiên cứu (sàng lọc, loại trừ, phân tích) — chờ research-figures]

Trong số {{R-A0-001.n}} người bệnh, 27 <!-- derived: R-A0-001.n - R-A1-003.n --> người (thời gian mắc đái tháo đường không ghi nhận) được xử lý theo nguyên tắc phân tích ca đầy đủ ở các mô hình hiệu chỉnh từ mục 3.2; mọi biến khác không thiếu dữ liệu.

Bảng 3.1. Đặc điểm chung của đối tượng nghiên cứu theo nhóm HbA1c lúc nhập viện (n = {{R-A0-001.n}})
| Đặc điểm | Chung | <7% | 7–9% | >9% |
|---|---|---|---|---|
| Tuổi (năm), TB ± ĐLC | {{R-A0-001.full}} | {{R-A0-002.full}} | {{R-A0-003.full}} | {{R-A0-004.full}} |
| Nữ, n (%) | {{R-A0-009.full}} | {{R-A0-010.full}} | {{R-A0-011.full}} | {{R-A0-012.full}} |
| Thời gian mắc ĐTĐ (năm), TB ± ĐLC | {{R-A0-013.full}} | {{R-A0-014.full}} | {{R-A0-015.full}} | {{R-A0-016.full}} |
| Tăng huyết áp, n (%) | {{R-A0-021.full}} | {{R-A0-022.full}} | {{R-A0-023.full}} | {{R-A0-024.full}} |
| Bệnh thận mạn, n (%) | {{R-A0-029.full}} | {{R-A0-030.full}} | {{R-A0-031.full}} | {{R-A0-032.full}} |
| Bệnh tim mạch, n (%) | {{R-A0-037.full}} | {{R-A0-038.full}} | {{R-A0-039.full}} | {{R-A0-040.full}} |
| ≥1 bệnh đồng mắc, n (%) | {{R-A0-045.full}} | {{R-A0-046.full}} | {{R-A0-047.full}} | {{R-A0-048.full}} |
| Dùng insulin khi nằm viện, n (%) | {{R-A0-053.full}} | {{R-A0-054.full}} | {{R-A0-055.full}} | {{R-A0-056.full}} |
| Thời gian nằm viện (ngày), trung vị (KTPV) | {{R-A0-057.full}} | {{R-A0-058.full}} | {{R-A0-059.full}} | {{R-A0-060.full}} |
Nguồn: số liệu nghiên cứu (mô phỏng).
Ghi chú: ĐLC: độ lệch chuẩn; KTPV: khoảng tứ phân vị; ≥1 bệnh đồng mắc = có ít nhất 1 trong tăng huyết áp, bệnh thận mạn, bệnh tim mạch; không kèm giá trị p so sánh 3 nhóm (thiết kế quan sát, không phải thử nghiệm ngẫu nhiên).

Nhận xét: Tuổi trung bình của {{R-A0-001.n}} người bệnh là {{R-A0-001.full}} năm, tương đồng giữa 3 nhóm HbA1c; trong đó nữ chiếm {{R-A0-009.full}}. Nhóm HbA1c >9% có tỷ lệ dùng insulin khi nằm viện ({{R-A0-056.full}}) cao hơn rõ so với nhóm <7% ({{R-A0-054.full}}), phù hợp thực hành kiểm soát đường huyết; đây là biến mô tả, không hiệu chỉnh trong mô hình chính vì là trung gian nghi ngờ.

Bảng 3.2. Tỷ lệ tái nhập viện mọi nguyên nhân trong 1 năm, chung và theo nhóm HbA1c
| Nhóm HbA1c | N | Tái nhập viện, n (%) | KTC 95% |
|---|---|---|---|
| Chung | {{R-A0-061.n}} | {{R-A0-061.count}} ({{R-A0-061.value}}) | {{R-A0-061.ci}} |
| <7% | {{R-A0-062.n}} | {{R-A0-062.count}} ({{R-A0-062.value}}) | {{R-A0-062.ci}} |
| 7–9% | {{R-A0-063.n}} | {{R-A0-063.count}} ({{R-A0-063.value}}) | {{R-A0-063.ci}} |
| >9% | {{R-A0-064.n}} | {{R-A0-064.count}} ({{R-A0-064.value}}) | {{R-A0-064.ci}} |
Nguồn: số liệu nghiên cứu (mô phỏng).
Ghi chú: N: số người bệnh trong nhóm; n: số người tái nhập viện; KTC: khoảng tin cậy, phương pháp Wilson.

Nhận xét: Tỷ lệ tái nhập viện mọi nguyên nhân trong 1 năm chung là {{R-A0-061.value}} (KTC 95%: {{R-A0-061.ci}}); tỷ lệ này tăng dần theo nhóm HbA1c, từ {{R-A0-062.value}} ở nhóm <7% đến {{R-A0-064.value}} ở nhóm >9%, nhưng khoảng tin cậy của 3 nhóm còn chồng lấp.

## 3.2 Mối liên quan giữa HbA1c lúc nhập viện và tái nhập viện trong 1 năm (Mục tiêu 2)

### 3.2.1 Phân tích thô

So với nhóm HbA1c <7% (tham chiếu), tỷ số chênh thô của tái nhập viện là {{R-A1-001.value}} (KTC 95%: {{R-A1-001.ci}}) ở nhóm 7–9% và {{R-A1-002.value}} (KTC 95%: {{R-A1-002.ci}}) ở nhóm >9%; cả hai khoảng tin cậy đều chứa giá trị 1.

### 3.2.2 Phân tích hiệu chỉnh

Bảng 3.3. Tái nhập viện mọi nguyên nhân trong 1 năm theo nhóm HbA1c: tỷ số chênh thô và hiệu chỉnh
| Biến | OR thô (KTC 95%) | OR hiệu chỉnh (KTC 95%) | p (hiệu chỉnh) |
|---|---|---|---|
| HbA1c 7–9% so với <7% | {{R-A1-001.value}} ({{R-A1-001.ci}}) | {{R-A1-003.value}} ({{R-A1-003.ci}}) | {{R-A1-003.p}} |
| HbA1c >9% so với <7% | {{R-A1-002.value}} ({{R-A1-002.ci}}) | {{R-A1-004.value}} ({{R-A1-004.ci}}) | {{R-A1-004.p}} |
| Giới (Nữ so với Nam) | | {{R-A1-005.value}} ({{R-A1-005.ci}}) | {{R-A1-005.p}} |
| Tuổi (mỗi năm) | | {{R-A1-006.value}} ({{R-A1-006.ci}}) | {{R-A1-006.p}} |
| Thời gian mắc ĐTĐ (mỗi năm) | | {{R-A1-007.value}} ({{R-A1-007.ci}}) | {{R-A1-007.p}} |
| ≥1 bệnh đồng mắc | | {{R-A1-008.value}} ({{R-A1-008.ci}}) | {{R-A1-008.p}} |
Nguồn: số liệu nghiên cứu (mô phỏng); hồi quy logistic đa biến, script phân tích analysis.py (A1).
Ghi chú: OR: tỷ số chênh; KTC: khoảng tin cậy; hiệu chỉnh theo tuổi, giới, thời gian mắc ĐTĐ, ≥1 bệnh đồng mắc.

Nhận xét: Sau hiệu chỉnh theo tuổi, giới, thời gian mắc đái tháo đường và bệnh đồng mắc, nhóm HbA1c >9% có tỷ số chênh tái nhập viện là {{R-A1-004.value}} so với nhóm <7% (KTC 95%: {{R-A1-004.ci}}; p = {{R-A1-004.p}}) và nhóm 7–9% là {{R-A1-003.value}} (KTC 95%: {{R-A1-003.ci}}; p = {{R-A1-003.p}}); cả hai khoảng tin cậy đều chứa giá trị 1 nên ước lượng còn kém chính xác, tương thích với từ không khác biệt đến tăng vừa phải nguy cơ tái nhập viện, chưa đủ bằng chứng xác nhận mối liên quan ở cỡ mẫu này. Mô hình có diện tích dưới đường cong ROC là {{R-A1-009.value}} và số sự kiện trên mỗi biến (EPV) là 39 <!-- derived: R-A1-010.value, làm tròn đến số nguyên -->; EPV ≥ 10 <!-- not-a-result: ngưỡng mặc định EPV --> nên không có cảnh báo về số biến cố trên mỗi biến.

## 3.3 Kết quả các phân tích phụ

### 3.3.1 HbA1c liên tục thay cho 3 nhóm

Bảng 3.4. Tái nhập viện mọi nguyên nhân trong 1 năm theo HbA1c liên tục (mỗi 1%), OR hiệu chỉnh
| Biến | OR hiệu chỉnh (KTC 95%) | p |
|---|---|---|
| HbA1c (mỗi 1%) | {{R-A2-002.value}} ({{R-A2-002.ci}}) | {{R-A2-002.p}} |
| Giới (Nữ so với Nam) | {{R-A2-001.value}} ({{R-A2-001.ci}}) | {{R-A2-001.p}} |
| Tuổi (mỗi năm) | {{R-A2-003.value}} ({{R-A2-003.ci}}) | {{R-A2-003.p}} |
| Thời gian mắc ĐTĐ (mỗi năm) | {{R-A2-004.value}} ({{R-A2-004.ci}}) | {{R-A2-004.p}} |
| ≥1 bệnh đồng mắc | {{R-A2-005.value}} ({{R-A2-005.ci}}) | {{R-A2-005.p}} |
Nguồn: số liệu nghiên cứu (mô phỏng); hồi quy logistic đa biến, script phân tích analysis.py (A2).
Ghi chú: OR: tỷ số chênh; KTC: khoảng tin cậy; phân tích phụ, thăm dò, không hiệu chỉnh đa so sánh.

Nhận xét: Mỗi 1% HbA1c tăng thêm liên quan với tỷ số chênh tái nhập viện hiệu chỉnh là {{R-A2-002.value}} (KTC 95%: {{R-A2-002.ci}}; p = {{R-A2-002.p}}); khoảng tin cậy hẹp quanh giá trị 1, tương thích với khác biệt nhỏ hoặc không có khác biệt theo mỗi 1% HbA1c. Đây là phân tích phụ, mang tính thăm dò, không hiệu chỉnh đa so sánh.

### 3.3.2 Tái nhập viện liên quan đái tháo đường trong 1 năm

Bảng 3.5. Tái nhập viện liên quan đái tháo đường trong 1 năm theo nhóm HbA1c, OR hiệu chỉnh
| Biến | OR hiệu chỉnh (KTC 95%) | p |
|---|---|---|
| HbA1c 7–9% so với <7% | {{R-A3-001.value}} ({{R-A3-001.ci}}) | {{R-A3-001.p}} |
| HbA1c >9% so với <7% | {{R-A3-002.value}} ({{R-A3-002.ci}}) | {{R-A3-002.p}} |
| Giới (Nữ so với Nam) | {{R-A3-003.value}} ({{R-A3-003.ci}}) | {{R-A3-003.p}} |
| Tuổi (mỗi năm) | {{R-A3-004.value}} ({{R-A3-004.ci}}) | {{R-A3-004.p}} |
| Thời gian mắc ĐTĐ (mỗi năm) | {{R-A3-005.value}} ({{R-A3-005.ci}}) | {{R-A3-005.p}} |
| ≥1 bệnh đồng mắc | {{R-A3-006.value}} ({{R-A3-006.ci}}) | {{R-A3-006.p}} |
Nguồn: số liệu nghiên cứu (mô phỏng); hồi quy logistic đa biến, script phân tích analysis.py (A3).
Ghi chú: OR: tỷ số chênh; KTC: khoảng tin cậy; phân tích phụ, thăm dò, không hiệu chỉnh đa so sánh.

Nhận xét: Nhóm HbA1c 7–9% và >9% có tỷ số chênh tái nhập viện liên quan đái tháo đường hiệu chỉnh cao hơn rõ so với nhóm <7%, tương ứng {{R-A3-001.value}} (KTC 95%: {{R-A3-001.ci}}; p = {{R-A3-001.p}}) và {{R-A3-002.value}} (KTC 95%: {{R-A3-002.ci}}; p {{R-A3-002.p}}); khoảng tin cậy không chứa giá trị 1 nhưng còn khá rộng. Đây là kết cục phụ, mang tính thăm dò, cần xem là giả thuyết cần kiểm định lại ở nghiên cứu khác, không phải kết luận xác nhận.

### 3.3.3 Thời gian đến lần tái nhập viện đầu tiên

Bảng 3.6. Thời gian đến lần tái nhập viện đầu tiên theo nhóm HbA1c: tỷ số nguy cơ thô và hiệu chỉnh
| Biến | HR thô (KTC 95%) | HR hiệu chỉnh (KTC 95%) | p (hiệu chỉnh) |
|---|---|---|---|
| HbA1c 7–9% so với <7% | {{R-A4-001.value}} ({{R-A4-001.ci}}) | {{R-A4-005.value}} ({{R-A4-005.ci}}) | {{R-A4-005.p}} |
| HbA1c >9% so với <7% | {{R-A4-002.value}} ({{R-A4-002.ci}}) | {{R-A4-006.value}} ({{R-A4-006.ci}}) | {{R-A4-006.p}} |
| Tuổi (mỗi năm) | | {{R-A4-007.value}} ({{R-A4-007.ci}}) | {{R-A4-007.p}} |
| Giới (Nữ so với Nam) | | {{R-A4-008.value}} ({{R-A4-008.ci}}) | {{R-A4-008.p}} |
| Thời gian mắc ĐTĐ (mỗi năm) | | {{R-A4-009.value}} ({{R-A4-009.ci}}) | {{R-A4-009.p}} |
| ≥1 bệnh đồng mắc | | {{R-A4-010.value}} ({{R-A4-010.ci}}) | {{R-A4-010.p}} |
Nguồn: số liệu nghiên cứu (mô phỏng); hồi quy Cox, kiểm duyệt tại 1 năm, script phân tích analysis.py (A4).
Ghi chú: HR: tỷ số nguy cơ; KTC: khoảng tin cậy; phân tích phụ, thăm dò; giả định tỷ số nguy cơ không đổi theo thời gian được kiểm tra bằng phần dư Schoenfeld, không ghi nhận vi phạm ở cả hai mô hình.

Nhận xét: Thời gian đến lần tái nhập viện đầu tiên có xu hướng ngắn hơn ở nhóm HbA1c cao hơn, với tỷ số nguy cơ hiệu chỉnh là {{R-A4-006.value}} ở nhóm >9% (KTC 95%: {{R-A4-006.ci}}; p = {{R-A4-006.p}}) và {{R-A4-005.value}} ở nhóm 7–9% (KTC 95%: {{R-A4-005.ci}}; p = {{R-A4-005.p}}) so với nhóm <7%; cả hai khoảng tin cậy đều chứa giá trị 1, hướng và độ lớn tương tự tỷ số chênh ở mục 3.2.2.

### 3.3.4 Tử vong trong viện trong 1 năm

Bảng 3.7. Tỷ lệ tử vong trong viện trong 1 năm, chung và theo nhóm HbA1c
| Nhóm HbA1c | n | Tử vong trong viện (%) | KTC 95% |
|---|---|---|---|
| Chung | {{R-A5-001.n}} | {{R-A5-001.value}} | {{R-A5-001.ci}} |
| <7% | {{R-A5-002.n}} | {{R-A5-002.value}} | {{R-A5-002.ci}} |
| 7–9% | {{R-A5-003.n}} | {{R-A5-003.value}} | {{R-A5-003.ci}} |
| >9% | {{R-A5-004.n}} | {{R-A5-004.value}} | {{R-A5-004.ci}} |
Nguồn: số liệu nghiên cứu (mô phỏng).
Ghi chú: KTC: khoảng tin cậy, phương pháp Wilson; chỉ ghi nhận được tử vong trong viện (không phải tử vong do mọi nguyên nhân); chỉ thống kê mô tả, không phân tích đa biến.

Nhận xét: Tỷ lệ tử vong trong viện trong 1 năm thấp ở cả 3 nhóm HbA1c, từ {{R-A5-002.value}} ở nhóm <7% đến {{R-A5-004.value}} ở nhóm >9% (chung: {{R-A5-001.value}}); kết cục này không đầy đủ (không xác định được tử vong ngoài viện) nên chỉ mang tính mô tả.

## 3.4 Phân tích thăm dò (hậu kiểm)

Phân tích thăm dò (hậu kiểm) theo nhóm tuổi (<65 và ≥65), không có trong kế hoạch phân tích, được thực hiện theo yêu cầu của tác giả ngày 2026-11-21 (ghi nhận là phân tích hậu kiểm A6 trong nhật ký quyết định của đề tài) để kiểm tra hiệu ứng nhóm HbA1c lên tái nhập viện 1 năm có khác nhau theo tuổi không.

Bảng 3.8 (hậu kiểm, kết quả thăm dò). Tái nhập viện mọi nguyên nhân trong 1 năm theo nhóm HbA1c, OR hiệu chỉnh trong từng nhóm tuổi
| Biến | Tuổi <65 (n = {{R-A6-001.n}}) | Tuổi ≥65 (n = {{R-A6-008.n}}) |
|---|---|---|
| HbA1c 7–9% so với <7%, OR (KTC 95%) | {{R-A6-001.value}} ({{R-A6-001.ci}}) | {{R-A6-008.value}} ({{R-A6-008.ci}}) |
| HbA1c >9% so với <7%, OR (KTC 95%) | {{R-A6-002.value}} ({{R-A6-002.ci}}) | {{R-A6-009.value}} ({{R-A6-009.ci}}) |
Nguồn: số liệu nghiên cứu (mô phỏng); hồi quy logistic đa biến trong từng nhóm tuổi, hậu kiểm, script phân tích analysis.py (A6).
Ghi chú: OR: tỷ số chênh; KTC: khoảng tin cậy; cùng biến hiệu chỉnh như mục 3.2.2; kết quả thăm dò, không có trong kế hoạch phân tích.

Phân tích thăm dò (hậu kiểm) theo nhóm tuổi cho thấy OR hiệu chỉnh của nhóm HbA1c >9% so với <7% là {{R-A6-002.value}} ở người <65 tuổi và {{R-A6-009.value}} ở người ≥65 tuổi, với p kiểm định tương tác nhóm HbA1c × nhóm tuổi là {{R-A6-015.value}}; khoảng tin cậy ở cả hai nhóm tuổi đều chứa giá trị 1 và p tương tác lớn, nên chưa có bằng chứng hiệu ứng HbA1c khác nhau thật sự theo tuổi ở cỡ mẫu này — kết quả này chỉ mang tính tạo giả thuyết, cần nghiên cứu xác nhận thêm, không nên trích dẫn như một kết luận độc lập.
