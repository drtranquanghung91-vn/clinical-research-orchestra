# Câu hỏi nghiên cứu

> **Dự án mô phỏng.** Tác giả: Example author. Đây là dữ liệu/địa điểm hư cấu (Bệnh viện Mô phỏng)
> dùng để minh họa quy trình; không có bệnh nhân thật, không có dữ liệu định danh.

## 1. Bối cảnh ngắn

Ở người bệnh đái tháo đường (ĐTĐ) type 2 nhập viện, kiểm soát đường huyết kém lúc nhập viện
(HbA1c cao) được cho là một chỉ điểm của bệnh nền chưa ổn định và có thể làm tăng nguy cơ tái nhập
viện sau xuất viện. Tác giả muốn biết liệu HbA1c lúc nhập viện có liên quan với tái nhập viện trong
1 năm sau xuất viện ở người bệnh ĐTĐ type 2 tại Khoa Nội tiết, Bệnh viện Mô phỏng (bệnh viện hư cấu,
tuyến tỉnh) hay không.

**Giả định / Assumptions** (vì đây là dự án mô phỏng, không có hồ sơ bệnh án thật để kiểm tra trước;
đã được tác giả xác nhận ngày 2026-11-21):
- HbA1c lúc nhập viện được ghi nhận thường quy và đầy đủ trong hồ sơ bệnh án điện tử/HIS cho phần lớn
  người bệnh ĐTĐ type 2 nhập Khoa Nội tiết.
- HIS 2021–2023 ghi nhận ngày nhập viện và chẩn đoán chính ICD-10 cho mọi lần nhập viện, đủ để xác
  định tái nhập viện (tại chính bệnh viện này) trong vòng 1 năm sau xuất viện (giả định của dự án mô
  phỏng, do tác giả xác nhận).
- Dân số nghiên cứu là người lớn (≥ 18 tuổi), không phân biệt có hay không biến chứng cấp lúc nhập viện
  (sẽ làm rõ tiêu chuẩn loại trừ ở bước thiết kế đề cương).

## 2. Loại câu hỏi và khung PECO

Đây là câu hỏi về **yếu tố liên quan / nguy cơ** (associated factors), không phải can thiệp → dùng
khung **PECO**, thiết kế phù hợp là **đoàn hệ hồi cứu** (retrospective cohort) — khớp với
`project.yaml` (design: cohort).

| Thành phần | Nội dung | Đo lường cụ thể |
|---|---|---|
| **P**opulation | Người bệnh ĐTĐ type 2, ≥ 18 tuổi, nhập và xuất viện tại Khoa Nội tiết, Bệnh viện Mô phỏng | Mã ICD-10 ĐTĐ type 2 trong hồ sơ ra viện, xuất viện 01/2021–12/2022, theo dõi đến 31/12/2023 (đủ 365 ngày theo dõi cho mọi người bệnh) |
| **E**xposure | Kiểm soát đường huyết kém lúc nhập viện | HbA1c đo trong vòng 24–48 giờ đầu nhập viện. Phân tích chính: 3 nhóm < 7% / 7–9% / > 9%. Phân tích phụ: biến liên tục, mỗi 1% |
| **C**omparator | Kiểm soát đường huyết tốt hơn lúc nhập viện | Nhóm HbA1c thấp hơn (nhóm tham chiếu trong phân tích) |
| **O**utcome | Tái nhập viện do mọi nguyên nhân trong 1 năm sau xuất viện | Có/không tái nhập viện tại chính bệnh viện trong 365 ngày kể từ ngày xuất viện, ghi nhận qua HIS |

## 3. Kết quả tìm kiếm sơ bộ (scoping search)

**Kiểm tra đổi tên bệnh/thuật ngữ (bước 2.0):** "đái tháo đường type 2", "HbA1c" và "tái nhập viện"
(readmission) không có ghi nhận đổi tên hoặc thay đổi tiêu chuẩn chẩn đoán gần đây đáng kể ảnh hưởng
tới chiến lược tìm kiếm → không áp dụng bước này.

**Nhật ký tìm kiếm** (PubMed, qua `search_lit.py`, không giới hạn năm trừ khi ghi chú):

| Nguồn | Câu lệnh | Số kết quả |
|---|---|---|
| PubMed | `HbA1c[tiab] AND readmission[tiab] AND diabetes[tiab] AND (systematic review[pt] OR meta-analysis[pt])` | 2 |
| PubMed | `"HbA1c"[tiab] AND ("readmission"[tiab] OR "rehospitalization"[tiab] OR "rehospitalisation"[tiab]) AND "type 2 diabetes"[tiab]` | 21 |
| PubMed | `"HbA1c"[tiab] AND "readmission"[tiab] AND ("one year"[tiab] OR "1-year"[tiab] OR "12-month"[tiab] OR "12 months"[tiab])` | 21 (trùng lặp nhiều với dòng trên) |
| PubMed | `"type 2 diabetes"[tiab] AND "readmission"[tiab] AND (Vietnam[Affiliation] OR Vietnam[tiab] OR "Viet Nam"[tiab])` | 1 (người Việt nhập cư ở Úc, không phải nghiên cứu tại Việt Nam) |

**Nhận xét theo bằng chứng đã đọc (abstract):**
- Có 1 tổng quan hệ thống (2021) về hiệu quả của các can thiệp trong bệnh viện nhằm giảm thời gian
  nằm viện và tái nhập viện ở người bệnh ĐTĐ type 2 [1] — đây là câu hỏi về **can
  thiệp**, không phải về HbA1c như một yếu tố nguy cơ, nên không trả lời trực tiếp câu hỏi của đề
  tài này.
- Một nghiên cứu đoàn hệ hồi cứu 2026 ở người ĐTĐ type 2 trẻ/trung niên (Trung Quốc) cho thấy mỗi 1%
  HbA1c tăng lên liên quan với tăng nguy cơ **tái nhập viện trong 30 ngày** (aOR 1,15; KTC 95%
  1,03–1,29) [2] — cùng hướng với giả thuyết của đề tài, nhưng mốc thời gian là 30 ngày (ngắn
  hơn nhiều so với 1 năm) và chỉ giới hạn ở nhóm tuổi 18–59.
- Một nghiên cứu lớn (Anh, n = 46.357 lần xuất viện có ĐTĐ) tìm thấy HbA1c đo **sau xuất viện** thấp
  hơn lại liên quan với tái nhập viện **cao** hơn [3] — nhưng đây là HbA1c đo *sau* xuất
  viện (theo dõi ngoại trú), khác với HbA1c lúc **nhập viện** mà đề tài này muốn khảo sát; hai biến
  phơi nhiễm không giống nhau nên không hẳn là "mâu thuẫn" trực tiếp, nhưng cho thấy hướng liên quan
  giữa HbA1c và tái nhập viện có thể phụ thuộc vào thời điểm đo và cần được làm rõ.
- Không tìm thấy nghiên cứu nào tại Việt Nam (trên PubMed) khảo sát trực tiếp mối liên quan giữa
  HbA1c lúc nhập viện và tái nhập viện ở người bệnh ĐTĐ type 2 nói chung (không giới hạn theo một
  bệnh đồng mắc cụ thể như suy tim hay đột quỵ).
- Phần lớn các nghiên cứu quốc tế tìm được tập trung vào mốc 30 ngày hoặc vào các nhóm bệnh đặc thù
  (sau phẫu thuật, suy tim, đột quỵ) — mốc **1 năm** ở người bệnh ĐTĐ type 2 nói chung còn ít được
  khảo sát.

**Tình huống áp dụng:** kết hợp giữa *"đã có bằng chứng ở nước ngoài nhưng chưa có ở Việt Nam"* và
*"bằng chứng còn mâu thuẫn/chưa nhất quán về chiều hướng và mốc thời gian"*. Đây là một câu hỏi
nghiên cứu hợp lệ (regular-vs-research test: chưa có guideline hay tổng quan hệ thống nào trả lời
trực tiếp câu hỏi này cho bối cảnh và mốc thời gian đã chọn).

*Lưu ý:* hầu hết tạp chí tiếng Việt (Tạp chí Y học Việt Nam, Y học TP.HCM…) không được lập chỉ mục
trên PubMed; tác giả nên tìm thêm trên Google Scholar/thư viện trường trước khi khẳng định "chưa ai
làm ở Việt Nam" — ở đây chỉ có thể viết "chưa tìm thấy trên PubMed/Consensus".

## 4. FINER cho các phương án

| Phương án | F (1–5) | I (1–5) | N (1–5) | E (1–5) | R (1–5) |
|---|---|---|---|---|---|
| **A. Đa trung tâm, nhiều bệnh viện tuyến tỉnh** | 1 — vượt khả năng dữ liệu/thời gian của 1 luận văn ThS 12 tháng, cần hợp tác nhiều cơ sở | 5 | 5 | 5 | 5 |
| **B. Đoàn hệ hồi cứu đơn trung tâm (đề xuất)** — tại Khoa Nội tiết, BV Mô phỏng, xuất viện 2021–2022, theo dõi 1 năm qua HIS, HbA1c nhập viện là phơi nhiễm chính, hiệu chỉnh đa biến | 4 — ~600 bệnh nhân/năm, đủ dữ liệu HIS, cỡ mẫu khả thi (xem dưới) | 4 — vấn đề sát với thực hành tại khoa | 4 — "dữ liệu mới + câu hỏi cũ ở quần thể chưa có dữ liệu" (Việt Nam); làm rõ thêm sự khác biệt về mốc thời gian (1 năm) so với các nghiên cứu 30 ngày đã có | 5 — hồi cứu, không can thiệp, dữ liệu đã có | 4 — nếu có liên quan, gợi ý cần theo dõi/can thiệp sớm sau xuất viện cho nhóm HbA1c cao |
| **C. Chỉ phân tích cắt ngang (HbA1c nhập viện vs. có/không tái nhập viện tại 1 mốc, không phân tích thời gian-đến-sự kiện)** | 5 — đơn giản hơn, ít yêu cầu dữ liệu ngày tháng chính xác | 3 — câu hỏi an toàn nhưng kém hấp dẫn hội đồng | 2 — không khai thác hết lợi thế dữ liệu theo dõi dọc đã có | 5 | 2 — kết luận yếu hơn (không nói được thời gian đến tái nhập viện) |

**Khả thi về số lượng (tầm soát, chưa phải tính cỡ mẫu chính thức):** ước lượng hồi quy logistic với
khoảng 8–10 biến trong mô hình, tỷ lệ tái nhập viện kỳ vọng ~15–25% (dựa trên khoảng dao động của các
nghiên cứu quốc tế đã đọc, không phải số liệu Việt Nam) → cần ~10 × số biến / tỷ lệ kết cục ≈
320–530 người bệnh có đủ dữ liệu. Với ~600 bệnh nhân xuất viện/năm, chỉ lấy các năm xuất viện cho
phép đủ 365 ngày theo dõi trong HIS 2021–2023 (ví dụ xuất viện 2021–2022), cỡ mẫu tiềm năng
~800–1.200 trước khi áp tiêu chuẩn loại trừ — khả thi. Cỡ mẫu chính thức sẽ được tính ở bước
`sample-size-sap`.

**Khuyến nghị:** chọn **Phương án B**. Phương án A vượt quá khả năng một luận văn ThS 12 tháng, dữ
liệu đơn trung tâm (Feasible ≤ 2). Phương án C khả thi hơn nhưng lãng phí lợi thế dữ liệu theo dõi
dọc đã có và cho kết luận yếu hơn.

## 5. Phiên bản cuối

### Tên đề tài (đã chọn — Example author, 2026-11-21)
**HbA1c lúc nhập viện và nguy cơ tái nhập viện trong 1 năm ở người bệnh đái tháo đường type 2 xuất
viện tại Bệnh viện Mô phỏng (2021–2023): một nghiên cứu đoàn hệ hồi cứu**

(2 lựa chọn còn lại, không chọn: *Mối liên quan giữa HbA1c lúc nhập viện và tái nhập viện trong 1
năm sau xuất viện ở người bệnh đái tháo đường type 2 tại Khoa Nội tiết, Bệnh viện Mô phỏng giai đoạn
2021–2023*; *Tỷ lệ tái nhập viện trong 1 năm và một số yếu tố liên quan, trong đó có kiểm soát đường
huyết lúc nhập viện, ở người bệnh đái tháo đường type 2 tại Khoa Nội tiết, Bệnh viện Mô phỏng giai
đoạn 2021–2023*.)

### Câu hỏi nghiên cứu
Ở người bệnh đái tháo đường type 2 xuất viện tại Khoa Nội tiết, Bệnh viện Mô phỏng từ 01/2021 đến
12/2022 (theo dõi đến 31/12/2023), HbA1c lúc nhập viện có liên quan với tái nhập viện do mọi nguyên
nhân trong 1 năm sau xuất viện không?

### Mục tiêu

**Mục tiêu tổng quát:** Xác định mối liên quan giữa HbA1c lúc nhập viện và tái nhập viện trong 1
năm sau xuất viện ở người bệnh đái tháo đường type 2 tại Khoa Nội tiết, Bệnh viện Mô phỏng giai đoạn
2021–2023.

**Mục tiêu cụ thể:**
1. Mô tả đặc điểm lâm sàng, cận lâm sàng (trong đó có HbA1c lúc nhập viện) và tỷ lệ tái nhập viện
   trong 1 năm của người bệnh đái tháo đường type 2 xuất viện tại Khoa Nội tiết, Bệnh viện Mô phỏng
   giai đoạn 2021–2022.
2. Xác định mối liên quan giữa HbA1c lúc nhập viện và tái nhập viện trong 1 năm sau xuất viện, có
   hiệu chỉnh một số yếu tố nhiễu (tuổi, giới, thời gian mắc bệnh, bệnh đồng mắc); thời gian nằm viện
   và sử dụng insulin được xử lý là biến trung gian (mediator), không hiệu chỉnh trong mô hình chính
   (xem `protocol.md` mục 2.7.2).

*(Mục tiêu 1 là mô tả, mục tiêu 2 là phân tích; mỗi mục tiêu trả lời bằng đúng một bảng/phân tích
chính trong kết quả, theo khuyến nghị của quy trình.)*

### Giả thuyết
- **Dạng lời:** người bệnh đái tháo đường type 2 có HbA1c lúc nhập viện cao (nhóm 7–9% hoặc > 9%)
  có tỷ lệ/nguy cơ tái nhập viện trong 1 năm sau xuất viện cao hơn người thuộc nhóm HbA1c < 7%
  (nhóm tham chiếu).
- **H₀ / H₁ (phân tích chính, 3 nhóm HbA1c):** H₀: không có sự khác biệt về nguy cơ tái nhập viện 1
  năm giữa 3 nhóm HbA1c lúc nhập viện (< 7% / 7–9% / > 9%) (OR₇₋₉ = OR>₉ = 1 so với nhóm < 7%, hoặc
  HR tương ứng = 1). H₁: có sự khác biệt giữa ít nhất một nhóm so với nhóm tham chiếu. Phân tích phụ
  dùng HbA1c liên tục (mỗi 1%): H₀: OR (hoặc HR) = 1; H₁: OR (hoặc HR) ≠ 1.
- **Hai phía** (kiểm định hai bên), vì chưa có đủ bằng chứng thống nhất về chiều hướng ở mốc 1 năm
  (xem mục 3 — các nghiên cứu đã đọc dùng mốc 30 ngày hoặc đo HbA1c ở thời điểm khác).
- **Hướng/độ lớn tham khảo để tính cỡ mẫu (không phải số liệu Việt Nam):** mỗi 1% HbA1c tăng liên
  quan với tăng nguy cơ tái nhập viện 30 ngày, aOR 1,15 (KTC 95% 1,03–1,29) [2]; cỡ mẫu chính
  thức sẽ dùng khoảng này làm tham khảo thận trọng ở bước `sample-size-sap`, không ngoại suy trực
  tiếp sang mốc 1 năm.
- Đây không phải nghiên cứu can thiệp nên không áp dụng superiority/non-inferiority/equivalence.

### Kết cục
- **Kết cục chính:** tái nhập viện do mọi nguyên nhân trong vòng 365 ngày kể từ ngày xuất viện (biến
  nhị giá có/không; nguồn: HIS 2021–2023 của chính bệnh viện).
- **Kết cục phụ:** (a) tái nhập viện có liên quan đến đái tháo đường/biến chứng đường huyết (hạ/tăng
  đường huyết, biến chứng cấp) trong 1 năm; (b) thời gian từ xuất viện đến lần tái nhập viện đầu
  tiên; (c) tử vong trong 1 năm (nếu dữ liệu HIS cho phép xác định).

### Thiết kế đề xuất
Đoàn hệ hồi cứu (retrospective cohort), một trung tâm, báo cáo theo STROBE — khớp với `project.yaml`.

## 6. Xác nhận của tác giả

Xác nhận bởi Example author, ngày 2026-11-21 (xem `decisions.md`):

1. **Khung thời gian chọn mẫu:** người bệnh xuất viện 01/2021–12/2022, theo dõi đến 31/12/2023 (đủ
   365 ngày cho mọi người bệnh trong mẫu).
2. **Phân nhóm HbA1c lúc nhập viện:** phân tích chính dùng 3 nhóm < 7% / 7–9% / > 9%; HbA1c liên tục
   mỗi 1% là phân tích phụ.
3. **Chất lượng ghi nhận trong HIS:** HIS ghi ngày nhập viện và chẩn đoán chính ICD-10 cho mọi lần
   nhập viện (giả định của dự án mô phỏng, do tác giả xác nhận — trên dữ liệu thật cần kiểm tra lại
   trên một mẫu nhỏ hồ sơ trước khi triển khai chính thức).

## 7. Tài liệu tham khảo

1. Chakraborty A, Pearson O, Schwartzkopff KM, O'rourke I, Ranasinghe I, Mah PM, et al. The effectiveness of in-hospital interventions on reducing hospital length of stay and readmission of patients with Type 2 Diabetes Mellitus: A systematic review. Diabetes Res Clin Pract. 2021;174:108363. doi:10.1016/j.diabres.2020.108363. PMID: 32771487.
2. Hu X, Su X, Chen S, Wang Q, He F, Zhang R. Predictors of 30-day readmission in young and middle-aged T2DM patients: a retrospective cohort study. Endocrine. 2026;91(1). doi:10.1007/s12020-026-04626-3. PMID: 42068438.
3. Robbins T, Sankaranarayanan S, Randeva H, Keung SNLC, Arvanitis TN. Association between glycosylated haemoglobin and outcomes for patients discharged from hospital with diabetes: A health informatics approach. Digit Health. 2021;7:20552076211007661. doi:10.1177/20552076211007661. PMID: 33948220.

## 8. Bước tiếp theo

Sau khi tác giả xác nhận (mục 6) và chọn tên đề tài (mục 5), bước tiếp theo là tổng quan tài liệu
đầy đủ có thẩm định chất lượng từng bài (`literature-search`, có dùng `critical-appraisal`), rồi đến
thiết kế đề cương chi tiết (`protocol-design`) và tính cỡ mẫu chính thức (`sample-size-sap`).
