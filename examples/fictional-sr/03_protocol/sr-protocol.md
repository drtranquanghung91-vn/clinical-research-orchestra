# Đề cương tổng quan hệ thống

> **LƯU Ý:** Đây là một tổng quan hệ thống HƯ CẤU, được xây dựng để minh hoạ phần mềm. "Thuốc X" là thuốc hư cấu;
> toàn bộ nghiên cứu được đưa vào (nguồn S1, "Simulated database", nền tảng: fictional) là dữ liệu mô phỏng, không
> phải dữ liệu người bệnh thật và không mô tả một can thiệp y khoa thật. Các tài liệu PubMed được dùng trong đề
> cương này chỉ là tài liệu nền/phương pháp luận THẬT (PRISMA 2020, RoB 2, GRADE, I² và khoảng dự đoán, REML);
> không có số liệu hư cấu nào được gán cho các tài liệu đó.

## 1. Thông tin hành chính

### 1.1 Tiêu đề
Thuốc X và tử vong 30 ngày ở người lớn nhập viện vì bệnh nội khoa cấp: tổng quan hệ thống và phân tích gộp các
thử nghiệm ngẫu nhiên có đối chứng (hư cấu) — đề cương (protocol).

### 1.2 Đăng ký
Chưa đăng ký ("not registered"). Đây là một tổng quan hệ thống hư cấu dùng để minh hoạ phần mềm, không phải một
tổng quan hệ thống thật, nên không đăng ký PROSPERO. Bản nháp PROSPERO minh hoạ: `03_protocol/prospero.md`.

### 1.3 Tác giả, liên hệ và vai trò
- Tác giả (author): Example author.
- Người đánh giá độc lập (reviewers), ghi tại `project.yaml → review.reviewers`:
  - Reviewer A (hư cấu)
  - Reviewer B (hư cấu)
- Bất đồng ở bước sàng lọc và trích xuất được giải quyết bằng đồng thuận (consensus) giữa Reviewer A và Reviewer B.

### 1.4 Sửa đổi
Mọi thay đổi sau khi khoá đề cương (gate G2) được ghi lại dưới dạng một dòng `DEVIATION A<n>:` trong
`decisions.md`, kèm ngày sửa đổi. Chưa có sửa đổi nào tại thời điểm soạn đề cương này.

### 1.5 Hỗ trợ
Không có nguồn tài trợ. Đây là dự án minh hoạ phần mềm, không có nhà tài trợ (sponsor) và không có vai trò của
nhà tài trợ cần khai báo.

## 2. Giới thiệu

### 2.1 Lý do thực hiện
Đề cương này minh hoạ toàn bộ quy trình của một tổng quan hệ thống/phân tích gộp (tìm kiếm, sàng lọc hai người
độc lập, trích xuất hai người độc lập, đánh giá nguy cơ sai lệch RoB 2, phân tích gộp mô hình hiệu ứng ngẫu
nhiên, GRADE) trên một câu hỏi lâm sàng hư cấu, không nhằm đưa ra khuyến cáo điều trị thật.

### 2.2 Mục tiêu (PICO)
- **Population (P):** người lớn (từ 18 tuổi) nhập viện vì bệnh nội khoa cấp.
- **Intervention (I):** thuốc X (hư cấu).
- **Comparator (C):** giả dược (placebo).
- **Outcome (O):** tử vong mọi nguyên nhân trong 30 ngày.

Câu hỏi: Ở người lớn (từ 18 tuổi) nhập viện vì bệnh nội khoa cấp, thuốc X (hư cấu) so với giả dược có làm giảm
tử vong mọi nguyên nhân trong 30 ngày không?

## 3. Phương pháp

### 3.1 Tiêu chuẩn lựa chọn
- **Thiết kế:** chỉ nhận thử nghiệm ngẫu nhiên có đối chứng (randomised controlled trial).
- **Đối tượng:** người lớn (từ 18 tuổi) nhập viện vì bệnh nội khoa cấp.
- **Can thiệp:** thuốc X (hư cấu).
- **Nhóm chứng:** giả dược.
- **Kết cục:** tử vong mọi nguyên nhân trong 30 ngày.
- **Bối cảnh (setting):** bệnh viện (nội trú).
- **Ngôn ngữ:** mọi ngôn ngữ, không giới hạn.
- **Năm công bố:** mọi năm, không giới hạn.

### 3.2 Nguồn thông tin
Vì toàn bộ nghiên cứu được đưa vào là hư cấu, nguồn duy nhất để tìm nghiên cứu đưa vào là:

| Nguồn | Nền tảng | Mã chuỗi tìm kiếm | Ghi chú |
|---|---|---|---|
| Simulated database | fictional | S1 | Tệp xuất do tác giả tự chạy; xem `02_evidence/sr/strings.md` |

PubMed **không** được dùng để tìm nghiên cứu đưa vào (vì không có nghiên cứu thật nào về "thuốc X"). PubMed chỉ
được dùng để tìm tài liệu nền và tài liệu phương pháp luận **thật** (PRISMA 2020, RoB 2, GRADE, I² và khoảng dự
đoán, REML), thêm bằng `search_lit.py` và kiểm bằng `verify_refs.py`. Không có đăng ký thử nghiệm (trial
registry) nào được tra cứu, vì lý do nêu trên.

Ngày tìm kiếm dự kiến: tác giả tự chạy nguồn S1 và ghi ngày chạy thực tế vào `02_evidence/sr/search-log.csv` khi
thực hiện.

### 3.3 Chiến lược tìm kiếm
Xem `02_evidence/sr/strings.md` — một khối cho mỗi nguồn, mã S1 cho nguồn "Simulated database".

### 3.4 Hồ sơ nghiên cứu
- **Quản lý dữ liệu:** `02_evidence/sr/records.csv`, `02_evidence/sr/screening.csv`,
  `02_evidence/sr/search-log.csv`.
- **Lựa chọn:** Reviewer A và Reviewer B sàng lọc tiêu đề/tóm tắt (title/abstract) và toàn văn (full text) một
  cách độc lập. Bất đồng được giải quyết bằng đồng thuận (hàng `consensus`). Gợi ý của AI (nếu dùng) chỉ lưu
  trong `ai-suggestions.csv` và không bao giờ là quyết định sàng lọc.
- **Thu thập dữ liệu:** hai người trích xuất độc lập — `04_data/sr/extraction-reviewer-a.csv` và
  `04_data/sr/extraction-reviewer-b.csv` — và một tệp đồng thuận `04_data/sr/extraction.csv`. Vì nghiên cứu là
  hư cấu, không có tác giả nghiên cứu thật nào để liên hệ khi thiếu dữ liệu; mọi dữ liệu thiếu được ghi nhận là
  thiếu trong tệp trích xuất, không suy diễn.

### 3.5 Biến số dữ liệu (data items)
Theo tệp trích xuất `04_data/sr/extraction.csv`: mã nghiên cứu, thiết kế, cỡ mẫu mỗi nhóm, đặc điểm dân số,
nhóm can thiệp ("thuốc X") và nhóm chứng ("giả dược"), số kiện/số người theo dõi cho kết cục tử vong mọi
nguyên nhân tại 30 ngày, và các cột nguy cơ sai lệch (bao gồm `rob_overall`).

### 3.6 Kết cục và thứ tự ưu tiên
Kết cục chính (và duy nhất trong đăng ký phân tích này): **tử vong mọi nguyên nhân** tại thời điểm **30 ngày**.

### 3.7 Nguy cơ sai lệch trong từng nghiên cứu
RoB 2 (Cochrane risk-of-bias tool for randomized trials) cho mỗi thử nghiệm ngẫu nhiên có đối chứng được đưa
vào, theo kết cục tử vong mọi nguyên nhân 30 ngày. Nhận định tổng quát (overall judgement) theo đúng thuật toán
của công cụ RoB 2, không phải điểm cộng dồn. Đánh giá do cả Reviewer A và Reviewer B thực hiện độc lập, bất đồng
giải quyết bằng đồng thuận.

### 3.8 Tổng hợp dữ liệu
- **Thước đo hiệu quả:** RR (risk ratio).
- **Mô hình:** hiệu ứng ngẫu nhiên (random effects), ước lượng REML (RE-REML); không dùng hiệu chỉnh HKSJ
  (Hartung-Knapp-Sidik-Jonkman) — HKSJ = no.
- **Dị biệt (heterogeneity):** báo cáo τ², I² và khoảng dự đoán (prediction interval) 95% khi k ≥ 3 nghiên cứu.
- Mô hình được tác giả lựa chọn trước khi xem kết quả (xem Đăng ký phân tích dưới đây). Mọi thay đổi mô hình sau
  khi khoá đề cương là một dòng `DEVIATION A<n>:` trong `decisions.md`, không bao giờ là thay đổi âm thầm.
- Nếu không phù hợp để gộp (ví dụ dị biệt quá cao), sẽ trình bày tổng hợp tường thuật có cấu trúc (SWiM) thay
  cho ước lượng gộp.

### 3.9 Sai lệch công bố (meta-bias)
Kiểm định Egger và biểu đồ hình phễu (funnel plot) chỉ thực hiện khi số nghiên cứu gộp k ≥ 10.

### 3.10 Độ tin cậy của bằng chứng tổng hợp
GRADE (Grading of Recommendations Assessment, Development and Evaluation) cho kết cục chính — tử vong mọi
nguyên nhân 30 ngày — với bảng tóm tắt kết quả (summary of findings).

## Lý do loại trừ ở bước toàn văn
- thiết kế không phải thử nghiệm ngẫu nhiên có đối chứng
- không báo cáo tử vong trong 30 ngày
- nhóm chứng không phải giả dược

## Đăng ký phân tích

| ID | Type | Outcome | Timepoint | Measure | Model | HKSJ | Experimental | Comparator | Factor |
|---|---|---|---|---|---|---|---|---|---|
| A0 | counts | PRISMA flow | | | | | | | |
| A1 | pool | tử vong mọi nguyên nhân | 30 ngày | RR | RE-REML | no | thuốc X | giả dược | |
| A2 | subgroup | tử vong mọi nguyên nhân | 30 ngày | RR | RE-REML | no | thuốc X | giả dược | rob_overall |
| A3 | leave-one-out | tử vong mọi nguyên nhân | 30 ngày | RR | RE-REML | no | thuốc X | giả dược | |

- A0 = số lượng PRISMA (PRISMA flow counts).
- A1 = ước lượng gộp chính (pool) cho kết cục tử vong mọi nguyên nhân tại 30 ngày, thuốc X so với giả dược.
- A2 = phân tích dưới nhóm (subgroup) theo yếu tố `rob_overall` (nhận định tổng quát RoB 2), cùng kết cục/thước
  đo/mô hình như A1.
- A3 = phân tích loại dần từng nghiên cứu (leave-one-out) để kiểm tra độ nhạy của ước lượng gộp A1.
- Mô hình (RE-REML, HKSJ = no) được chọn trước khi xem kết quả; một thay đổi sau này là một dòng
  `DEVIATION A<n>:` trong `decisions.md`, không phải một thay đổi âm thầm. Phân tích mạng (network
  meta-analysis), dữ liệu từng cá nhân (IPD), độ chính xác chẩn đoán (diagnostic accuracy) và hồi quy gộp
  (meta-regression) với hơn một yếu tố không thuộc phạm vi đề cương này; cần chuyên viên thống kê.
