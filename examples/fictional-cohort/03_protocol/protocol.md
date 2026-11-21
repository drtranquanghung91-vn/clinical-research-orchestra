# Đề cương nghiên cứu (Chương 2 — Đối tượng và phương pháp nghiên cứu)

> **Dự án mô phỏng** (Example author). Khoa Nội tiết, Bệnh viện Mô phỏng là địa điểm hư cấu; không có
> bệnh nhân thật, không có dữ liệu định danh. Gate G1 đang mở (câu hỏi nghiên cứu đã được xác nhận,
> xem `01_question/question.md`). Khung soạn theo `design/protocol-template.md` (SPIRIT 2013
> numbering — bản đồ đầy đủ sang SPIRIT 2025 chưa được xác minh, xem phần "Chuẩn báo cáo" dưới đây).

## Phần A — Quyết định thiết kế (tóm tắt nhanh cho tác giả)

**Tóm tắt thiết kế:** Nghiên cứu đoàn hệ hồi cứu, đơn trung tâm, trên toàn bộ người bệnh đái tháo
đường (ĐTĐ) type 2 ≥ 18 tuổi xuất viện tại Khoa Nội tiết, Bệnh viện Mô phỏng từ 01/01/2021 đến
31/12/2022, theo dõi tái nhập viện qua hệ thống thông tin bệnh viện (HIS) đến 31/12/2023. Phơi nhiễm
là HbA1c đo trong 24–48 giờ đầu nhập viện (3 nhóm < 7% / 7–9% / > 9%); kết cục chính là tái nhập viện
do mọi nguyên nhân trong 1 năm sau xuất viện. Không có can thiệp, không phân nhóm ngẫu nhiên.

**Vì sao chọn thiết kế này, phương án khác, và hạn chế:**
- **Đã chọn — đoàn hệ hồi cứu** ("retrospective cohort"): phù hợp vì câu hỏi là yếu tố liên quan/nguy
  cơ (HbA1c) với một outcome không hiếm (ước tính 15–25%, không < 5%), dữ liệu đã có sẵn trong HIS
  theo chuỗi thời gian liên tục (xuất viện → theo dõi), và đây là lựa chọn đã được xác nhận ở bước
  `research-question` (Phương án B, xem `01_question/question.md` mục 4).
- **Phương án khác đã xem xét — bệnh–chứng (case-control)**: chọn theo kết cục (có/không tái nhập
  viện) rồi tra cứu ngược HbA1c. Bị loại vì: (a) không cần thiết — outcome không hiếm nên đoàn hệ khả
  thi về số lượng (~1.200 người bệnh); (b) đoàn hệ giữ được thông tin thời gian-đến-sự kiện (cho phép
  dùng Cox/Fine-Gray ở phân tích phụ) mà case-control sẽ mất; (c) nguy cơ sai lệch chọn chứng cao hơn
  trong thiết kế hồi cứu từ một nguồn dữ liệu hành chính duy nhất.
- **Hạn chế chính của đoàn hệ hồi cứu đã chọn**: dữ liệu được thu thập trước đó cho mục đích chăm sóc
  lâm sàng, không phải cho nghiên cứu, nên có thể thiếu hoặc không đồng nhất; không có nhóm được theo
  dõi tiến cứu với đo lường chuẩn hóa thời điểm; và — quan trọng nhất trong bối cảnh dự án này —
  **tái nhập viện ở một cơ sở y tế khác không được ghi nhận** (xem mục 2.7).

## 2.1. Đối tượng nghiên cứu

### 2.1.1. Tiêu chuẩn chọn (inclusion)
1. Chẩn đoán ĐTĐ type 2 theo mã ICD-10 ghi trong hồ sơ ra viện (khối mã **E11** — "Đái tháo đường
   không phụ thuộc insulin", theo bảng phân loại ICD-10 của WHO; *lưu ý:* đây là khối mã ICD-10 công
   khai, không phải một khuyến cáo lâm sàng cần trích dẫn nguồn, nhưng danh sách mã cụ thể dùng để
   trích xuất cần được xác nhận lại với phòng Kế hoạch tổng hợp của bệnh viện trước khi triển khai
   thật, vì Việt Nam áp dụng bảng mã ICD-10 của WHO có thể khác với bảng ICD-10-CM của Hoa Kỳ).
2. ≥ 18 tuổi tại thời điểm nhập viện.
3. Xuất viện từ Khoa Nội tiết, Bệnh viện Mô phỏng, trong khoảng **01/01/2021–31/12/2022** (để đảm bảo
   đủ 365 ngày theo dõi trong dữ liệu HIS 2021–2023 cho mọi người bệnh).
4. Có kết quả HbA1c được đo trong vòng 24–48 giờ đầu của lần nhập viện này, ghi nhận trong hồ sơ bệnh
   án điện tử.

*Hạn chế về tiêu chuẩn chẩn đoán:* chẩn đoán ĐTĐ type 2 trong nghiên cứu này là chẩn đoán đã được bác
sĩ điều trị xác lập và ghi mã ICD-10 trong hồ sơ (định nghĩa vận hành, kế thừa từ
`01_question/question.md`), **không được tái xác định bằng một tiêu chuẩn chẩn đoán cụ thể có trích
dẫn** (ví dụ ADA) trong phạm vi tài liệu đã xác minh của dự án — chương `02_evidence/guidelines.md`
chỉ xác minh được mục 16 (chăm sóc nội viện) của ADA Standards of Care-2026, không phải mục tiêu
chuẩn chẩn đoán. Nếu cần trích dẫn cụ thể, chạy lại `guideline-check` nhắm đúng mục tiêu chuẩn chẩn
đoán ĐTĐ (ADA mục 2, hoặc hướng dẫn của Bộ Y tế Việt Nam) trước khi hoàn thiện đề cương.

### 2.1.2. Tiêu chuẩn loại trừ
Người bệnh **đã thỏa tiêu chuẩn chọn** nhưng có đặc điểm làm sai lệch kết quả hoặc không thể đo được
outcome một cách nhất quán:
1. Tử vong trong chính lần nhập viện chỉ số (trước khi xuất viện) — không có cơ hội "tái nhập viện
   sau xuất viện" như định nghĩa của outcome chính; vẫn được mô tả riêng (không gộp vào mẫu phân
   tích outcome tái nhập viện).
2. Chẩn đoán ĐTĐ thai kỳ, ĐTĐ type 1, hoặc ĐTĐ thứ phát (do thuốc, bệnh tụy...) được ghi mã ICD-10
   riêng biệt khỏi khối E11 trong hồ sơ.
3. Hồ sơ không có giá trị HbA1c lúc nhập viện hợp lệ (thiếu kết quả, hoặc kết quả không đáng tin —
   ví dụ lỗi kỹ thuật ghi nhận rõ trong hồ sơ) — loại vì không thể xác định nhóm phơi nhiễm.
4. Nhiều lần xuất viện của cùng một người bệnh trong giai đoạn 01/2021–12/2022: **chỉ lấy lần xuất
   viện đầu tiên trong giai đoạn này làm "nhập viện chỉ số" (index admission)** cho người bệnh đó;
   các lần nhập viện sau trong cùng giai đoạn được dùng để xác định outcome (tái nhập viện), không
   tạo thêm đơn vị phân tích độc lập — tránh vi phạm giả định độc lập giữa các quan sát.

*Không* áp dụng tiêu chuẩn dừng/rút lui (stopping/withdrawal criteria) vì đây là nghiên cứu hồi cứu
trên dữ liệu đã có, không có theo dõi tiến cứu người bệnh.

### 2.1.3. Phương pháp chọn mẫu
**Lấy mẫu toàn bộ (census)**: tất cả người bệnh thỏa tiêu chuẩn chọn trong giai đoạn xuất viện
01/01/2021–31/12/2022, không chọn mẫu xác suất hay thuận tiện một phần. Với ~50 người bệnh ĐTĐ type 2
xuất viện/tháng, cỡ mẫu tiềm năng trước khi áp tiêu chuẩn loại trừ là **~1.200 người bệnh** trong 2
năm. Vì mục tiêu là ước lượng mối liên quan (mục tiêu phân tích), không phải ước lượng một tỷ lệ cho
một dân số xác định, tính đại diện của mẫu không phải tiêu chí quyết định; giá trị nội tại (đo lường
chuẩn, kiểm soát nhiễu) được ưu tiên hơn (xem mục 2.7).

## 2.2. Thời gian và địa điểm

- **Địa điểm:** Khoa Nội tiết, Bệnh viện Mô phỏng (địa điểm hư cấu, tuyến tỉnh, dự án mô phỏng).
- **Giai đoạn chọn mẫu (nhập viện chỉ số):** người bệnh xuất viện từ 01/01/2021 đến 31/12/2022.
- **Giai đoạn theo dõi outcome:** 365 ngày kể từ ngày xuất viện của mỗi người bệnh, qua dữ liệu HIS
  đến 31/12/2023 (đảm bảo mọi người bệnh trong mẫu đều có đủ 365 ngày dữ liệu theo dõi).
- **Thời điểm thu thập/trích xuất dữ liệu:** sau khi đề cương và SAP được phê duyệt (gate G2).

## 2.3. Phương pháp nghiên cứu

### 2.3.1. Thiết kế
Nghiên cứu đoàn hệ hồi cứu (retrospective cohort study), đơn trung tâm. Báo cáo theo **STROBE**
(bản 2007, đã xác nhận còn là bản hiện hành qua `guideline-check`, xem `02_evidence/guidelines.md`).

### 2.3.2. Cỡ mẫu
*(Để trống — tính ở bước `sample-size-sap`.)* Xem Phần C — Chuyển giao tính cỡ mẫu.

### 2.3.3. Phương pháp chọn mẫu
Lấy mẫu toàn bộ (census), như mục 2.1.3. Không áp dụng phân nhóm ngẫu nhiên, không che giấu phân bổ,
không làm mù (không can thiệp).

## 2.4. Can thiệp
**Không áp dụng** — đây là nghiên cứu quan sát (đoàn hệ hồi cứu trên một phơi nhiễm tự nhiên — HbA1c
lúc nhập viện — không phải một can thiệp do nghiên cứu viên chỉ định).

## 2.5. Biến số và chỉ số nghiên cứu

Bảng biến số đầy đủ (định nghĩa, loại biến, nguồn trong EMR/HIS, vai trò trong phân tích) được viết
tại `03_protocol/variables.md`. Dưới đây chỉ nêu định nghĩa outcome và phơi nhiễm chính:

| Outcome | Định nghĩa | Thời điểm đo | Nguồn | Đơn vị |
|---|---|---|---|---|
| **Kết cục chính** — Tái nhập viện mọi nguyên nhân trong 1 năm | Có/không có ≥ 1 lần nhập viện nội trú (bất kỳ khoa nào) tại Bệnh viện Mô phỏng trong vòng 365 ngày kể từ ngày xuất viện của lần nhập viện chỉ số | Theo dõi liên tục đến 365 ngày hoặc đến ngày tái nhập viện đầu tiên, lấy theo HIS | HIS | Nhị giá (Có/Không) |
| Kết cục phụ (a) — Tái nhập viện liên quan ĐTĐ | Tái nhập viện trong 1 năm có chẩn đoán chính hoặc chẩn đoán kèm theo thuộc khối ICD-10 liên quan ĐTĐ/biến chứng đường huyết (hạ/tăng đường huyết, biến chứng cấp) | Như trên | HIS | Nhị giá |
| Kết cục phụ (b) — Thời gian đến lần tái nhập viện đầu tiên | Số ngày từ ngày xuất viện đến ngày nhập viện của lần tái nhập viện đầu tiên (hoặc censored tại 365 ngày/tử vong **trong viện** nếu không tái nhập viện — xem mục 2.7 và 2.8 về hạn chế nguy cơ cạnh tranh) | Liên tục trong 365 ngày | HIS | Ngày (thời gian-đến-sự kiện) |
| Kết cục phụ (c) — Tử vong trong 1 năm | **Đã xác nhận (2026-11-21): HIS của Bệnh viện Mô phỏng chỉ ghi nhận được tử vong xảy ra trong viện (ví dụ trong một lần tái nhập viện); không xác định được tử vong ngoài viện (tại nhà hoặc cơ sở khác).** Biến này chỉ phản ánh "tử vong trong viện ghi nhận được trong 365 ngày", không phải tử vong do mọi nguyên nhân thật — không dùng làm kết cục tử vong đầy đủ, chỉ dùng cho phân tích độ nhạy (mục 2.8) | 365 ngày, chỉ bắt được tử vong trong viện | HIS | Nhị giá (trong viện) — **không đầy đủ, xem hạn chế** |

**Phơi nhiễm chính:** HbA1c đo trong 24–48 giờ đầu nhập viện; phân tích chính theo 3 nhóm
**< 7% / 7–9% / > 9%** (nhóm < 7% là nhóm tham chiếu); phân tích phụ dùng HbA1c liên tục (mỗi 1%) —
đã được tác giả xác nhận tại `01_question/question.md` mục 6.

## 2.6. Công cụ và quy trình thu thập số liệu

- **Nguồn dữ liệu:** hồ sơ bệnh án điện tử (EMR) và hệ thống thông tin bệnh viện (HIS) của Bệnh viện
  Mô phỏng, 2021–2023. **Không có nguồn dữ liệu nào ngoài EMR/HIS của chính bệnh viện** (không khảo
  sát người bệnh, không truy xuất dữ liệu từ bệnh viện khác, không làm thêm xét nghiệm — theo kinh
  phí hạn chế đã xác nhận).
- **Công cụ:** biểu mẫu trích xuất dữ liệu (data extraction form) theo đúng bảng biến số ở
  `03_protocol/variables.md`, xây dựng trước khi trích xuất.
- **Người trích xuất và quy trình chống sai lệch quan sát:** nên có ≥ 1 người trích xuất biến nhiễu
  và biến mô tả **không biết trước** nhóm HbA1c của người bệnh khi có thể (giảm sai lệch do biết
  trước giả thuyết); với dữ liệu điện tử trích xuất bằng truy vấn (query) trên HIS thay vì đọc tay
  từng hồ sơ, rủi ro này thấp hơn — ưu tiên trích xuất bằng truy vấn có cấu trúc, chỉ đọc tay hồ sơ
  khi cần xác minh các trường hợp bất thường hoặc thiếu dữ liệu.
- **Sơ đồ nghiên cứu (flow diagram):**

```
Người bệnh ĐTĐ type 2 xuất viện từ Khoa Nội tiết, BV Mô phỏng, 01/01/2021-31/12/2022 (ước tính n ~ 1.200)
  └─ Loại: ĐTĐ thai kỳ/type 1/thứ phát (n = …)
      └─ Loại: tử vong trong lần nhập viện chỉ số (n = …)
          └─ Loại: thiếu HbA1c lúc nhập viện hợp lệ (n = …)
              └─ Loại: trùng lần xuất viện trong giai đoạn (chỉ giữ lần đầu) (n = …)
                  └─ Mẫu phân tích (n = …)
                      ├─ Nhóm HbA1c < 7% ─ theo dõi 365 ngày qua HIS ─ Tái nhập viện? (Có/Không)
                      ├─ Nhóm HbA1c 7-9% ─ theo dõi 365 ngày qua HIS ─ Tái nhập viện? (Có/Không)
                      └─ Nhóm HbA1c > 9% ─ theo dõi 365 ngày qua HIS ─ Tái nhập viện? (Có/Không)
                          └─ Phân tích: Mục tiêu 1 (mô tả) + Mục tiêu 2 (hồi quy đa biến)
```

- **Lịch trình đánh giá outcome:** cố định theo mốc 365 ngày tính từ time zero (ngày xuất viện của
  nhập viện chỉ số), **giống nhau cho mọi nhóm HbA1c** — tránh sai lệch phát hiện (detection bias) do
  một nhóm được "theo dõi" sát hơn nhóm khác (không áp dụng trực tiếp ở đây vì outcome lấy từ dữ liệu
  hành chính khách quan, không phải thăm khám chủ động, nhưng vẫn giữ nguyên tắc mốc thời gian cố
  định, đồng nhất).

## 2.7. Sai số và biện pháp khống chế

### 2.7.1. Sai số theo thiết kế đoàn hệ hồi cứu

| Loại sai số | Biểu hiện cụ thể trong đề tài này | Khống chế ở thiết kế | Khống chế ở phân tích |
|---|---|---|---|
| Dữ liệu thiếu/không đồng nhất | HbA1c, biến nhiễu có thể ghi thiếu hoặc không nhất quán giữa các bệnh án | Tiêu chuẩn trích xuất rõ ràng, biểu mẫu chuẩn hóa (mục 2.6); loại người thiếu HbA1c hợp lệ (mục 2.1.2) | Báo cáo rõ số lượng và % thiếu dữ liệu cho từng biến; phân tích độ nhạy nếu thiếu > 10% ở biến quan trọng |
| Nhiễu do chỉ định (confounding by indication) | Người có bệnh nặng hơn lúc nhập viện có thể vừa có HbA1c cao hơn vừa có nguy cơ tái nhập viện cao hơn vì độ nặng, không phải vì HbA1c | Đo các chỉ số độ nặng/bệnh đồng mắc sẵn có tại thời điểm nhập viện (mục 2.7.2) | Hồi quy đa biến hiệu chỉnh các yếu tố nhiễu đã định trước (mục 2.7.2); không chọn biến theo p < 0,05 |
| Sai lệch thời gian bất tử (immortal time bias) | **Rủi ro thấp trong đề tài này**: phơi nhiễm (HbA1c) được đo và cố định trong 24–48 giờ đầu nhập viện — trước thời điểm "time zero" (ngày xuất viện) — nên không có khoảng thời gian nào mà người bệnh phải "sống sót" mới được phân vào nhóm phơi nhiễm | Giữ nguyên quy ước đo phơi nhiễm trong 24–48h đầu, không đổi theo diễn biến sau đó | — |
| **Thiếu thông tin tái nhập viện ngoài hệ thống** | HIS chỉ ghi nhận tái nhập viện **tại chính Bệnh viện Mô phỏng**; người bệnh tái nhập viện ở cơ sở khác sẽ bị tính nhầm là "không tái nhập viện" | Không khắc phục được ở thiết kế (không có dữ liệu liên thông — hạn chế đã xác nhận) | Nêu rõ trong hạn chế (mục dưới); không khẳng định đây là sai lệch non-differential — hướng và độ lớn sai lệch **chưa xác định được** với dữ liệu hiện có |
| Sai lệch phát hiện (detection bias) | Thấp, vì outcome lấy từ dữ liệu hành chính khách quan (có nhập viện lại hay không), không phải đánh giá chủ quan | Mốc theo dõi 365 ngày cố định, giống nhau mọi nhóm (mục 2.6) | — |
| Mất dấu | Thấp trong hệ thống (HIS ghi nhận mọi lần nhập viện tại viện); "mất dấu" thực chất trùng với mục "thiếu thông tin ngoài hệ thống" ở trên | — | — |

### 2.7.2. Phân loại biến thứ ba (nhiễu / trung gian / yếu tố điều biến) — DAG dạng chữ

Các biến nhiễu được chọn **trước khi thu thập dữ liệu**, từ y văn đã thẩm định ở `02_evidence/` (dù
không có nghiên cứu nào trả lời trực tiếp câu hỏi 1 năm, các yếu tố dưới đây được nêu như biến dự báo
tái nhập viện ở ĐTĐ type 2 trong các mốc thời gian khác — xem `02_evidence/evidence-table.md`,
`02_evidence/gaps.md`) kết hợp kiến thức lâm sàng, **không chọn theo p < 0,05 đơn biến**.

```
Tuổi ───────────────┬──────────────► Tái nhập viện 1 năm
                     ▲                      ▲
HbA1c lúc nhập viện ─┼──────────────────────┤
                     ▲                      │
Thời gian mắc ĐTĐ ───┤                      │
                     ▲                      │
Bệnh đồng mắc ───────┴──────────────────────┘
(THA, bệnh thận mạn, bệnh tim mạch — ghi nhận TRƯỚC hoặc TẠI thời điểm nhập viện)

HbA1c lúc nhập viện ──► Sử dụng insulin trong thời gian nằm viện ──► Tái nhập viện 1 năm
                         (có thể là TRUNG GIAN — bác sĩ khởi trị insulin SAU khi biết HbA1c cao —
                          không đưa vào mô hình chính; có thể xét ở phân tích phụ/nhạy)

HbA1c lúc nhập viện ──► Thời gian nằm viện ──► Tái nhập viện 1 năm
                         (vai trò chưa rõ ràng — có thể vừa chịu ảnh hưởng của HbA1c/độ nặng,
                          vừa ảnh hưởng ngược lại outcome → không đưa vào mô hình chính là biến
                          nhiễu; dùng như biến mô tả/phân tích phụ)
```

**Biến nhiễu đưa vào mô hình chính (hiệu chỉnh đa biến, Mục tiêu 2):** tuổi, giới, thời gian mắc ĐTĐ,
có/không bệnh đồng mắc chính (tăng huyết áp, bệnh thận mạn, bệnh tim mạch — mã hóa có/không từ chẩn
đoán kèm theo ghi **trước hoặc tại** thời điểm nhập viện chỉ số).

**Không đưa vào mô hình chính (phân loại là trung gian/chưa rõ vai trò nhân quả):** sử dụng insulin
trong thời gian nằm viện, thời gian nằm viện — cả hai được đo **sau hoặc đồng thời** với thời điểm đo
HbA1c nên có thể nằm trên con đường nhân quả giữa HbA1c và outcome; có thể khảo sát ở phân tích phụ
nhưng không hiệu chỉnh trong mô hình chính của Mục tiêu 2.

**Biến thăm dò, không bắt buộc trong mô hình chính (ràng buộc ngân sách/dữ liệu):** tỷ số
bạch cầu trung tính/lympho (NLR) và các chỉ số viêm tổng hợp (SII, SIRI) được nêu trong y văn đã
thẩm định ở mốc thời gian khác [1,2]. Về mặt kỹ thuật, các chỉ số này **chỉ cần công
thức máu có bạch cầu phân loại đã làm thường quy lúc nhập viện — không cần xét nghiệm mới** (phù hợp
với ràng buộc kinh phí). **Ngưỡng đã được tác giả xác nhận (2026-11-21): nếu tỷ lệ hồ sơ thiếu công
thức bạch cầu phân loại lúc nhập viện > 20%, bỏ hẳn NLR/SII/SIRI khỏi phân tích (không đưa vào cả mô
hình chính và phân tích thăm dò); nếu ≤ 20%, đưa vào như biến thăm dò/phụ, không đưa vào mô hình
chính của Mục tiêu 2.**

**Số lượng biến nhiễu trong mô hình chính:** 4 biến (tuổi, giới, thời gian mắc ĐTĐ, bệnh đồng mắc —
có thể gộp bệnh đồng mắc thành 1 biến tổng hợp nếu cần giảm số biến). Số biến tối đa mô hình có thể
chứa phụ thuộc số sự kiện (outcome) quan sát được (quy tắc mặc định ~10 sự kiện/biến) — tính cụ thể ở
`sample-size-sap`.

### 2.7.3. Nhân quả từ dữ liệu quan sát
Thiết kế đoàn hệ hồi cứu đáp ứng được tiêu chí **thời gian trước–sau** (temporality) của Bradford Hill
(phơi nhiễm đo trước outcome) nếu time zero được xác định đúng như mục 2.6, nhưng **không đủ** để kết
luận nhân quả một mình — các tiêu chí khác (liều–đáp ứng, nhất quán giữa nhiều nghiên cứu độc lập,
cơ chế sinh học hợp lý) cần được thảo luận ở Chương 4 (Dự kiến bàn luận), không phải trong đề cương.
Ngôn ngữ dùng trong toàn bộ luận văn: **"có liên quan với"**, không dùng "là nguyên nhân của" hay
"yếu tố nguy cơ nhân quả".

## 2.8. Xử lý và phân tích số liệu

- **Phần mềm:** R hoặc Stata (script có thể chạy lại được — không dùng Excel cho phân tích chính).
- **Mục tiêu 1 (mô tả):** thống kê mô tả đặc điểm lâm sàng/cận lâm sàng và tỷ lệ tái nhập viện 1 năm
  (tần số, tỷ lệ %; trung bình ± độ lệch chuẩn hoặc trung vị [khoảng liên phân vị] tùy phân bố).
- **Mục tiêu 2 (phân tích chính):** hồi quy logistic đa biến cho outcome nhị giá "tái nhập viện mọi
  nguyên nhân trong 1 năm (có/không)", biến độc lập chính là nhóm HbA1c (3 nhóm, nhóm < 7% tham
  chiếu), hiệu chỉnh các biến nhiễu ở mục 2.7.2. Báo cáo OR thô và OR đã hiệu chỉnh kèm KTC 95%.
- **Phân tích phụ/nhạy:** (a) HbA1c liên tục (mỗi 1%) thay cho 3 nhóm; (b) **đã xác nhận (2026-11-21):
  HIS chỉ ghi nhận được tử vong trong viện, không xác định được tử vong ngoài viện — vì vậy hồi quy
  Fine-Gray (coi tử vong là nguy cơ cạnh tranh) chỉ được dùng như **phân tích độ nhạy**, không phải
  phân tích chính cho outcome "thời gian đến lần tái nhập viện đầu tiên"; kết quả Fine-Gray phải ghi
  rõ hạn chế là **đánh giá thấp (underestimate)** số sự kiện cạnh tranh thật (chỉ bắt được tử vong
  trong viện), nên khoảng tin cậy và tỷ số sub-hazard có thể lệch theo hướng chưa xác định được; phân
  tích chính cho outcome thời gian-đến-sự kiện vẫn dùng hồi quy Cox thông thường, coi người tử vong
  ngoài viện (không xác định được) như censored tại thời điểm cuối theo dõi — một giả định không
  hoàn toàn đúng (vi phạm giả định censoring không thông tin nếu tử vong liên quan đến HbA1c), cần
  nêu rõ trong hạn chế của luận văn; (c) phân tích độ nhạy loại trừ người có biến nhiễu bị thiếu dữ
  liệu > ngưỡng do tác giả quyết định.
- **Dữ liệu thiếu:** báo cáo số lượng/% thiếu cho mỗi biến; không tự động "xóa theo dòng" (complete
  case) nếu tỷ lệ thiếu > 5–10% ở một biến nhiễu quan trọng — xem xét imputation đa biến hoặc phân
  tích độ nhạy, quyết định cụ thể ở `sample-size-sap`/SAP.
- **Mức ý nghĩa:** hai phía, α = 0,05 (mặc định, có thể điều chỉnh ở SAP nếu có nhiều so sánh).
- Kế hoạch phân tích chi tiết (SAP) được viết đầy đủ ở bước `sample-size-sap` → `03_protocol/sap.md`.

## 2.9. Đạo đức nghiên cứu

- Đây là nghiên cứu **hồi cứu trên dữ liệu đã có sẵn** (hồ sơ bệnh án điện tử, HIS), không can thiệp,
  không ảnh hưởng đến quá trình chăm sóc người bệnh.
- **Đã xác nhận (2026-11-21):** đề cương sẽ được nộp cho **Hội đồng Đạo đức trong nghiên cứu y sinh
  học của Bệnh viện Mô phỏng**. Tác giả xin hội đồng **miễn chấp thuận tham gia cá nhân (waiver of
  informed consent)** với lý do: (1) nghiên cứu hồi cứu trên dữ liệu đã có sẵn, không can thiệp,
  không ảnh hưởng đến chăm sóc người bệnh; (2) dữ liệu được khử định danh trước khi phân tích (xem
  bảo mật thông tin dưới đây); (3) không khả thi về mặt thực tế để liên hệ lại toàn bộ ~1.200 người
  bệnh đã xuất viện. **Quyết định cuối cùng vẫn thuộc hội đồng đạo đức của cơ sở** — đây là đề nghị
  của tác giả trong đề cương, không phải một sự miễn trừ đã được cấp.
- **Bảo mật thông tin:** dữ liệu được mã hóa bằng số thứ tự nghiên cứu, loại bỏ họ tên, số CMND/CCCD,
  số điện thoại, địa chỉ cụ thể trước khi đưa vào tệp phân tích; tệp dữ liệu có mật khẩu, chỉ nghiên
  cứu viên chính truy cập; tuân thủ quy định của Bộ Y tế về đạo đức trong nghiên cứu y sinh học
  **[văn bản/thông tư cụ thể: chưa xác minh trong phiên này — người dùng cần kiểm tra bản gốc trước
  khi nộp hội đồng, theo nguyên tắc không trích dẫn số hiệu văn bản từ bộ nhớ]**.
- Chi tiết biểu mẫu chấp thuận, quy trình xin phê duyệt, bộ công cụ thu thập (CRF) đầy đủ thuộc bước
  `ethics-and-crf` (ngoài phạm vi skill này).

## Chuẩn báo cáo

Báo cáo theo **STROBE** (đoàn hệ) — bản 2007, đã xác nhận còn hiện hành (`02_evidence/guidelines.md`).
Cột SPIRIT trong khung đề cương (`design/protocol-template.md`) dùng **số thứ tự SPIRIT 2013**; bản
đồ đầy đủ sang SPIRIT 2025 (34 mục) **chưa được xác minh** — không áp dụng trực tiếp cho đề tài này vì
đây không phải một thử nghiệm can thiệp, nhưng ghi chú này được giữ lại theo đúng quy ước của khung
đề cương dùng chung trong dự án.

## Phần C — Chuyển giao tính cỡ mẫu và các mục cần xác nhận

### Chuyển giao cho `sample-size-sap`
- **Outcome chính:** nhị giá (tái nhập viện 1 năm, có/không).
- **Loại biến phơi nhiễm chính:** phân loại 3 nhóm (HbA1c < 7% / 7–9% / > 9%, nhóm < 7% tham chiếu);
  phân tích phụ dùng biến liên tục.
- **Thiết kế:** đoàn hệ hồi cứu, so sánh ≥ 3 nhóm (hồi quy logistic đa biến là phân tích chính).
- **Số biến nhiễu dự kiến hiệu chỉnh trong mô hình chính:** 4 (tuổi, giới, thời gian mắc ĐTĐ, bệnh
  đồng mắc) — cần tính số sự kiện/biến (events per variable) phù hợp.
- **Tham số cần tìm/xác nhận ở bước tiếp theo:** tỷ lệ tái nhập viện 1 năm kỳ vọng ở Bệnh viện Mô
  phỏng (tham khảo thận trọng từ y văn gián tiếp — 30 ngày: 10,9% [3]; 31 ngày: 18,5%
  [2] — **không ngoại suy trực tiếp sang 1 năm**, cần ước lượng riêng hoặc dùng khoảng rộng);
  độ lớn hiệu ứng kỳ vọng giữa các nhóm HbA1c (chưa có số liệu trực tiếp — xem GRADE rất thấp,
  `02_evidence/appraisal/summary.md`); cỡ mẫu khả dụng thực tế sau áp tiêu chuẩn loại trừ (ước tính
  trước loại trừ: ~1.200).

### Các mục đã được tác giả xác nhận (2026-11-21)
1. **Ngưỡng tỷ lệ thiếu dữ liệu cho công thức bạch cầu phân loại:** > 20% thiếu → bỏ hẳn NLR/SII/SIRI
   khỏi mọi phân tích; ≤ 20% → đưa vào phân tích thăm dò/phụ (xem mục 2.7.2).
2. **Xác định tử vong:** HIS chỉ ghi nhận được tử vong **trong viện**, không xác định được tử vong
   ngoài viện → Fine-Gray chỉ dùng làm phân tích độ nhạy, không phải phân tích chính; hạn chế này
   được ghi rõ trong mục 2.5 (bảng outcome) và 2.8 (xem trên).
3. **Quy trình phê duyệt đạo đức:** nộp Hội đồng Đạo đức của Bệnh viện Mô phỏng, xin miễn chấp thuận
   tham gia cá nhân vì tính hồi cứu và dữ liệu đã khử định danh (xem mục 2.9).

*(Không còn mục nào cần xác nhận thêm ở bước này; các mục mới có thể phát sinh ở bước `sample-size-sap`
sẽ được nêu riêng trong `03_protocol/sample-size.md`/`sap.md`.)*

## Tài liệu tham khảo

1. Li L, Jiang S. Dynamic evolution of readmission risk factors across short-, medium-, and long-term horizons in type 2 diabetes: a machine learning-based predictive modeling study with SHAP interpretability. Front Endocrinol (Lausanne). 2026;17:1827506. doi:10.3389/fendo.2026.1827506. PMID: 42440445.
2. Cao J, Shi Q, Yu Z, Xie H. A nomogram incorporating nutritional risk for predicting 31-day unplanned readmission in adults with type 2 diabetes mellitus using LASSO regression. Front Nutr. 2026;13:1863130. doi:10.3389/fnut.2026.1863130. PMID: 42876841.
3. Hu X, Su X, Chen S, Wang Q, He F, Zhang R. Predictors of 30-day readmission in young and middle-aged T2DM patients: a retrospective cohort study. Endocrine. 2026;91(1). doi:10.1007/s12020-026-04626-3. PMID: 42068438.
