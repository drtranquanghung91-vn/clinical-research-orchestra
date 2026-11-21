# Thẩm định: Robbins T, Sankaranarayanan S, Randeva H, Keung SNLC, Arvanitis TN (2021)

**Association between glycosylated haemoglobin and outcomes for patients discharged from hospital
with diabetes: A health informatics approach.** Digit Health. 2021;7:20552076211007661.
doi:10.1177/20552076211007661. PMID: 33948220.

**Nội dung đã đọc:** chỉ abstract (metadata PubMed) — **"thẩm định sơ bộ từ abstract"**.

**Quyết định mà bản thẩm định này phục vụ:** có nên trích dẫn bài này trong phần tổng quan/biện luận
của luận văn, và có thể dùng số liệu của nó làm tham số cỡ mẫu cho câu hỏi của đề tài không.

## Ba câu hỏi (trả lời trước)

1. **Đáng tin (Trustworthy)?** **Còn quan ngại (some concerns đến serious)**. Abstract chỉ nêu kiểm
   định đơn biến (p-value, Cohen's D) và **không nêu mô hình hồi quy đa biến hiệu chỉnh nhiễu** —
   điểm quan ngại chính. Cỡ mẫu đúng phơi nhiễm "HbA1c lúc nhập viện" rất nhỏ (n = 399/46.357).
2. **Có giá trị (Valuable)?** Hiệu ứng **nhỏ** (Cohen's D 0,28–0,39) dù có ý nghĩa thống kê — cỡ mẫu
   rất lớn (n = 46.357) dễ cho p nhỏ với hiệu ứng nhỏ; không nên đọc p mà bỏ qua độ lớn hiệu ứng.
3. **Áp dụng (Relevant)?** **Gián tiếp và khác hẳn** câu hỏi của đề tài — phơi nhiễm là HbA1c đo
   **sau xuất viện** (không phải lúc nhập viện), gộp cả T1DM và T2DM, hệ thống y tế Anh (NHS).

**Khuyến nghị:** **không dùng làm bằng chứng trực tiếp hoặc tham số cỡ mẫu** cho câu hỏi của đề tài.
Điểm quyết định: (a) phơi nhiễm khác hẳn (thời điểm đo HbA1c), (b) không rõ có hiệu chỉnh đa biến hay
không. Chỉ dùng trong phần biện luận để minh họa rằng chiều hướng liên quan giữa HbA1c và tái nhập
viện có thể phụ thuộc vào **thời điểm đo** (xem `gaps.md`, Gap 3) — không trình bày như thể cùng một
phơi nhiễm với [1] hay với đề tài.

## 1. Câu hỏi của bài báo vs. câu hỏi của tác giả

| | Bài báo [2] | Đề tài |
|---|---|---|
| P | Mọi lần xuất viện có ĐTĐ (T1DM + T2DM gộp), 1 trung tâm chuyển tuyến lớn, Anh, 3 năm | ĐTĐ **type 2** ≥ 18 tuổi, xuất viện tại Bệnh viện Mô phỏng, 2021–2022 |
| E | HbA1c đo **sau xuất viện** (ngoại trú), giá trị tuyệt đối/tương đối và tần suất đo | HbA1c đo **lúc nhập viện** |
| C | HbA1c sau xuất viện cao hơn | HbA1c < 7% (tham chiếu) |
| O | Tái nhập viện, tử vong (mốc thời gian không nêu rõ trong abstract cho tái nhập viện; 1 năm được nêu cho việc "có HbA1c trong 1 năm sau xuất viện", không phải mốc đo outcome) | Tái nhập viện mọi nguyên nhân trong 1 năm |

**Sàng lọc liên quan:** **không đạt đầy đủ 2 "có".** Phơi nhiễm khác hẳn (HbA1c *sau* xuất viện,
không phải *lúc nhập viện*), và gộp cả T1DM — hai khác biệt lớn với câu hỏi của đề tài. Tiếp tục
thẩm định nhưng bài này chỉ dùng để **minh họa khả năng mối liên quan phụ thuộc thời điểm đo HbA1c**
(xem `gaps.md`, Gap 3), không dùng làm bằng chứng trực tiếp hay tham số cỡ mẫu cho đề tài.

## 2. Thiết kế thật và công cụ

Quan sát, có nhóm so sánh, chọn theo mức phơi nhiễm (HbA1c sau xuất viện) rồi đối chiếu outcome →
**đoàn hệ hồi cứu trên một phơi nhiễm**, khai thác qua dữ liệu tin học y tế. Công cụ chính theo
`tools-by-design.md`: **ROBINS-E**. Ở mức chỉ đọc abstract, dùng **NOS** làm công cụ thay thế nhẹ
hơn (bảng mục 4 ánh xạ sang các miền ROBINS-E tương ứng). Chuẩn báo cáo: STROBE.

## 3. Độ tin cậy nguồn

Không có trong danh sách bị thu hồi (câu lệnh #8 trong `search-strategy.md`, 0 kết quả). *Digital
Health* (SAGE) — không có dấu hiệu "predatory". Tài trợ/COI không nêu trong abstract. Không phải
RCT nên không áp dụng mục so sánh outcome đăng ký trước với outcome báo cáo.

## 4. Bảng theo miền (NOS, đoàn hệ — ánh xạ sang miền ROBINS-E trong cột cuối)

| Miền NOS | Câu hỏi | Trả lời | Cơ sở | Nhận định | ≈ Miền ROBINS-E |
|---|---|---|---|---|---|
| Lựa chọn — tính đại diện | Mẫu đại diện cho người xuất viện có ĐTĐ? | Có lẽ có (cỡ mẫu rất lớn, toàn bộ xuất viện 3 năm) | "All discharges (n = 46,357) with diabetes from a major tertiary referral centre over 3 years" | Gộp T1DM+T2DM — không tách riêng ở phân tích chính (chỉ "further evaluation" theo nhóm) | Chọn người tham gia |
| Lựa chọn — xác định phơi nhiễm | HbA1c đo chuẩn hóa, đủ số liệu? | Có lẽ không, cho phần "HbA1c lúc nhập viện" | Chỉ 399/46.357 có HbA1c lúc nhập viện — **cỡ mẫu rất nhỏ** cho đúng phơi nhiễm gần với đề tài này | Phần phân tích chính của bài dùng HbA1c **sau xuất viện** (n = 3.138), không phải lúc nhập viện | Đo lường phơi nhiễm |
| Lựa chọn — outcome chưa xảy ra lúc bắt đầu | Hợp lý theo thiết kế | Có lẽ có | Theo logic đoàn hệ hồi cứu | — | Can thiệp/sự kiện sau phơi nhiễm |
| Khả năng so sánh — hiệu chỉnh nhiễu | Có hồi quy đa biến hiệu chỉnh nhiễu? | **Không rõ, cần đọc full-text** | Abstract chỉ nêu "statistical significance and standardised Cohen's D effect size calculations" — có vẻ là kiểm định **đơn biến**, không nêu mô hình đa biến | Đây là điểm quan ngại chính — không rõ đã kiểm soát tuổi, bệnh đồng mắc, mức độ nặng | Nhiễu |
| Kết cục — đánh giá | Outcome khách quan? | Có | Dữ liệu hành chính bệnh viện | — | Đo lường outcome |
| Kết cục — thời gian theo dõi | Đủ dài, rõ mốc? | Không rõ | Abstract không nêu rõ mốc theo dõi cụ thể cho biến "tái nhập viện" (chỉ nêu 1 năm cho việc có đo HbA1c) | — | Đo lường outcome |
| Kết cục — mất dấu | Không nêu | Không rõ, cần đọc full-text | — | — | Dữ liệu thiếu |

**Nhận định tổng thể:** **một số quan ngại đến nguy cơ cao (some concerns to serious)** — thiếu rõ
về hiệu chỉnh đa biến (chỉ thấy kiểm định đơn biến trong abstract, miền Nhiễu) là điểm quan ngại
chính, cộng với cỡ mẫu rất nhỏ (n=399) cho đúng phơi nhiễm "HbA1c lúc nhập viện" gần với đề tài.

## 5. Giá trị (Valuable) — đọc theo vùng ý nghĩa lâm sàng

- HbA1c trung bình ở nhóm **tái nhập viện** thấp hơn nhóm không tái nhập viện: 57,82 vs 60,39
  (đơn vị mmol/mol theo IFCC, tương ứng khoảng 7,4% vs 7,7% theo NGSP — **đơn vị không được nêu rõ
  trong abstract, đây là suy luận, cần xác nhận qua full-text**); p = 0,009; Cohen's D 0,28 — **hiệu
  ứng nhỏ** theo quy ước Cohen (0,2 = nhỏ, 0,5 = trung bình).
- Thời gian đến khi đo HbA1c: 97 ngày (tái nhập viện) vs 113 ngày (không tái nhập viện); p = 0,00006;
  Cohen's D 0,39 — hiệu ứng nhỏ-đến-trung bình.
- Đây là kiểm định có ý nghĩa thống kê (p < 0,05) nhưng **độ lớn hiệu ứng nhỏ** (Cohen's D < 0,3 cho
  giá trị HbA1c) — với n = 46.357, p nhỏ có thể đi cùng hiệu ứng không quan trọng lâm sàng; cần đọc
  bằng "vùng ý nghĩa lâm sàng", không chỉ bằng p. **Không viết "không có liên quan" vì p < 0,05 ở
  đây — ngược lại, p nhỏ + hiệu ứng nhỏ nghĩa là có liên quan về thống kê nhưng độ lớn khiêm tốn.**
- Chiều hướng: HbA1c **thấp hơn** liên quan tái nhập viện **cao hơn** — **ngược** với giả thuyết của
  đề tài (HbA1c cao hơn → tái nhập viện cao hơn), nhưng đây là HbA1c đo ở thời điểm khác (sau xuất
  viện, có thể phản ánh kiểm soát quá chặt/hạ đường huyết hoặc bệnh nặng hơn được theo dõi sát hơn —
  khả năng nhiễu do chỉ định ngược, xem mục 6; diễn giải của tác giả gốc không có trong phần abstract
  đã trích).

## 6. Áp dụng (Relevant)

- Dân số gộp T1DM+T2DM — khác đề tài (chỉ ĐTĐ type 2).
- Phơi nhiễm khác thời điểm đo (sau xuất viện, không phải lúc nhập viện) — **không thể dùng trực
  tiếp** làm bằng chứng hay tham số cho câu hỏi của đề tài; chỉ dùng để minh họa rằng chiều hướng liên
  quan giữa HbA1c và tái nhập viện có thể đổi theo thời điểm đo (nguy cơ nhiễu do chỉ định ngược —
  reverse causation/confounding by indication: người được theo dõi HbA1c sát hơn sau xuất viện có thể
  là người được nhận biết là nguy cơ cao hơn).
- Hệ thống y tế Anh (NHS), 1 trung tâm — không trực tiếp áp dụng cho Bệnh viện Mô phỏng (Việt Nam,
  tuyến tỉnh).

## 7. Cần kiểm tra thêm (tối đa 3, cần full-text)

1. Mô hình phân tích chính có hiệu chỉnh đa biến (hồi quy) hay chỉ kiểm định đơn biến như abstract
   gợi ý?
2. Đơn vị HbA1c (mmol/mol IFCC hay % NGSP) và mốc thời gian cụ thể cho biến "tái nhập viện".
3. Kết quả tách riêng cho nhóm T2DM (abstract chỉ nêu "further evaluation... cohorts of T1DM and
   T2DM" mà không cho số liệu).

## Tài liệu tham khảo

1. Hu X, Su X, Chen S, Wang Q, He F, Zhang R. Predictors of 30-day readmission in young and middle-aged T2DM patients: a retrospective cohort study. Endocrine. 2026;91(1). doi:10.1007/s12020-026-04626-3. PMID: 42068438.
2. Robbins T, Sankaranarayanan S, Randeva H, Keung SNLC, Arvanitis TN. Association between glycosylated haemoglobin and outcomes for patients discharged from hospital with diabetes: A health informatics approach. Digit Health. 2021;7:20552076211007661. doi:10.1177/20552076211007661. PMID: 33948220.
