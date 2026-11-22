# Bảng biến số nghiên cứu

Nguồn dữ liệu cho mọi biến: hồ sơ bệnh án điện tử (EMR) và hệ thống thông tin bệnh viện (HIS) của
Bệnh viện Mô phỏng — **không có nguồn dữ liệu ngoài hai hệ thống này** (không khảo sát, không xét
nghiệm mới, không dữ liệu từ cơ sở y tế khác). Bảng này là đầu vào cho biểu mẫu trích xuất dữ liệu
(CRF) ở bước `ethics-and-crf`.

## 1. Biến phơi nhiễm (Exposure)

| Mục tiêu | Biến | Định nghĩa / cách đo | Loại | Giá trị / đơn vị | Nguồn trong EMR/HIS | Vai trò |
|---|---|---|---|---|---|---|
| MT2 | HbA1c lúc nhập viện (phân nhóm) | Giá trị HbA1c đo trong 24–48 giờ đầu nhập viện, phân 3 nhóm | Thứ tự (ordinal)/phân loại | < 7% / 7–9% / > 9% (nhóm < 7% tham chiếu) | Kết quả xét nghiệm cận lâm sàng, EMR | Phơi nhiễm chính |
| MT2 (phụ) | HbA1c lúc nhập viện (liên tục) | Giá trị HbA1c đo trong 24–48 giờ đầu nhập viện | Liên tục | % (NGSP) | Kết quả xét nghiệm cận lâm sàng, EMR | Phơi nhiễm (phân tích phụ) |

## 2. Biến kết cục (Outcome)

| Mục tiêu | Biến | Định nghĩa / cách đo | Loại | Giá trị / đơn vị | Nguồn trong EMR/HIS | Vai trò |
|---|---|---|---|---|---|---|
| MT1, MT2 | Tái nhập viện 1 năm (mọi nguyên nhân) | ≥ 1 lần nhập viện nội trú tại BV Mô phỏng trong 365 ngày kể từ ngày xuất viện của lần nhập viện chỉ số | Nhị giá | Có / Không | Lượt nhập viện, HIS | **Kết cục chính** |
| MT1 | Tái nhập viện liên quan ĐTĐ | Tái nhập viện trong 1 năm có chẩn đoán chính/kèm theo thuộc khối ICD-10 liên quan ĐTĐ hoặc biến chứng đường huyết | Nhị giá | Có / Không | Chẩn đoán ra viện, HIS | Kết cục phụ |
| MT1 | Thời gian đến lần tái nhập viện đầu tiên | Số ngày từ ngày xuất viện đến ngày nhập viện của lần tái nhập viện đầu tiên (censored tại 365 ngày hoặc tử vong nếu không tái nhập viện) | Thời gian-đến-sự kiện | Ngày | Ngày nhập viện các lượt, HIS | Kết cục phụ |
| MT1 | Tử vong trong 1 năm (trong viện) | **Đã xác nhận: HIS chỉ ghi nhận tử vong trong viện**, không xác định được tử vong ngoài viện — biến này là "tử vong trong viện trong 365 ngày", không phải tử vong do mọi nguyên nhân đầy đủ | Nhị giá (trong viện) | Có / Không | HIS | Kết cục phụ — **không đầy đủ**, chỉ dùng cho phân tích độ nhạy (Fine-Gray) |

## 3. Biến nhiễu đưa vào mô hình chính (Confounder — Mục tiêu 2)

| Mục tiêu | Biến | Định nghĩa / cách đo | Loại | Giá trị / đơn vị | Nguồn trong EMR/HIS | Vai trò |
|---|---|---|---|---|---|---|
| MT1, MT2 | Tuổi | Tuổi tại thời điểm nhập viện chỉ số, tính theo năm hoàn chỉnh | Liên tục | Năm | Ngày sinh + ngày nhập viện, EMR | Mô tả / nhiễu |
| MT1, MT2 | Giới | Giới ghi trong hồ sơ | Phân loại nhị giá | Nam / Nữ | EMR | Mô tả / nhiễu |
| MT1, MT2 | Thời gian mắc ĐTĐ | Số năm từ ngày được chẩn đoán ĐTĐ type 2 (ghi nhận sớm nhất trong hồ sơ) đến ngày nhập viện chỉ số | Liên tục | Năm | Tiền sử bệnh, EMR | Mô tả / nhiễu |
| MT1, MT2 | Bệnh đồng mắc chính | Có/không có ≥ 1 trong: tăng huyết áp, bệnh thận mạn, bệnh tim mạch — ghi nhận **trước hoặc tại** thời điểm nhập viện chỉ số (không tính chẩn đoán phát sinh sau đó) | Nhị giá (hoặc đếm số bệnh đồng mắc nếu dữ liệu cho phép) | Có / Không (hoặc 0/1/2/3) | Chẩn đoán kèm theo + tiền sử, EMR/HIS | Nhiễu |

## 4. Biến không đưa vào mô hình chính (trung gian / chưa rõ vai trò — xem `protocol.md` mục 2.7.2)

| Mục tiêu | Biến | Định nghĩa / cách đo | Loại | Giá trị / đơn vị | Nguồn trong EMR/HIS | Vai trò |
|---|---|---|---|---|---|---|
| MT1 (mô tả), phân tích phụ | Sử dụng insulin trong thời gian nằm viện | Có/không chỉ định insulin (bất kỳ dạng) trong lần nhập viện chỉ số | Nhị giá | Có / Không | Y lệnh thuốc, EMR | Mô tả / **trung gian nghi ngờ** (không hiệu chỉnh trong mô hình chính) |
| MT1 (mô tả), phân tích phụ | Thời gian nằm viện (lần nhập viện chỉ số) | Số ngày từ nhập viện đến xuất viện | Liên tục | Ngày | EMR | Mô tả / **vai trò nhân quả chưa rõ** (không hiệu chỉnh trong mô hình chính) |

## 5. Biến thăm dò, không bắt buộc (phụ thuộc tính khả dụng dữ liệu — xem `protocol.md` mục 2.7.2)

| Mục tiêu | Biến | Định nghĩa / cách đo | Loại | Giá trị / đơn vị | Nguồn trong EMR/HIS | Vai trò |
|---|---|---|---|---|---|---|
| Thăm dò (có điều kiện) | Tỷ số bạch cầu trung tính/lympho (NLR) | Tính từ công thức máu (bạch cầu phân loại) lúc nhập viện, nếu đã làm thường quy | Liên tục | Tỷ số | Công thức máu, EMR | **Đã xác nhận:** nếu > 20% hồ sơ thiếu công thức bạch cầu phân loại → bỏ hẳn biến này; nếu ≤ 20% → đưa vào phân tích thăm dò/phụ (không vào mô hình chính) |
| Thăm dò (có điều kiện) | Chỉ số viêm tổng hợp (SII hoặc SIRI) | Tính từ công thức máu lúc nhập viện, nếu đã làm thường quy | Liên tục | Chỉ số tính toán | Công thức máu, EMR | Cùng điều kiện ngưỡng 20% như trên |
| Thăm dò | Nguy cơ dinh dưỡng lúc nhập viện | Nếu bệnh viện có thang đánh giá dinh dưỡng thường quy (ví dụ NRS-2002) ghi trong hồ sơ; nếu không có, bỏ biến này (không làm thêm đánh giá mới theo ràng buộc kinh phí) | Phân loại hoặc liên tục (tùy thang đo nếu có) | Tùy thang đo | Hồ sơ điều dưỡng/dinh dưỡng, EMR (nếu có) | Thăm dò, có điều kiện |

## 6. Biến hành chính / định danh nghiên cứu (không dùng trong phân tích thống kê)

| Biến | Định nghĩa | Loại | Nguồn | Vai trò |
|---|---|---|---|---|
| Mã số nghiên cứu | Số thứ tự do nghiên cứu viên gán, thay cho họ tên/số hồ sơ gốc | Định danh | Gán khi trích xuất | Ẩn danh hóa — không phải biến phân tích |
| Ngày nhập viện chỉ số | Ngày nhập viện của lần nhập viện chỉ số | Ngày | EMR | Xác định time zero |
| Ngày xuất viện chỉ số | Ngày xuất viện của lần nhập viện chỉ số | Ngày | EMR | Xác định time zero (gốc tính 365 ngày theo dõi) |

---

**Nguyên tắc chung áp dụng cho toàn bảng:**
- Mọi biến liên tục được thu thập ở dạng thô (ví dụ ngày sinh, không phải nhóm tuổi đã phân loại
  sẵn) rồi mới tính toán — theo đúng nguyên tắc đo lường của `protocol-design`.
- Biến nào không phục vụ trực tiếp Mục tiêu 1 hoặc Mục tiêu 2 không được đưa vào bảng này (tránh kéo
  dài biểu mẫu trích xuất và tăng dữ liệu thiếu không cần thiết).
- Bảng này sẽ được dùng làm từ điển dữ liệu (data dictionary) khi xây dựng CRF chi tiết ở bước
  `ethics-and-crf`.
