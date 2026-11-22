# Kế hoạch phân tích thống kê (SAP)

> Dựa trên ICH E9, khung estimand ICH E9(R1), và mẫu SAP trong `sap-template.md`. Dự án mô phỏng
> (Example author). Mục nào không áp dụng ghi "Không áp dụng" kèm lý do.

## 1. Thông tin hành chính

- **Tên đề tài:** HbA1c lúc nhập viện và nguy cơ tái nhập viện trong 1 năm ở người bệnh đái tháo
  đường type 2 xuất viện tại Bệnh viện Mô phỏng (2021–2023): một nghiên cứu đoàn hệ hồi cứu.
- **Phiên bản SAP:** 1.1 (1.0 ngày 2026-11-21; 1.1 thêm bảng đăng ký phân tích, mục 16). **Ngày:** 2026-11-21. **Tác giả/người viết SAP:** Example author (với hỗ
  trợ soạn thảo của Claude, Anthropic — xem công bố sử dụng AI ở `02_evidence/search-strategy.md`).
- **Trạng thái:** soạn trước khi trích xuất dữ liệu (pre-data-lock) — đúng nguyên tắc viết SAP trước
  khi có dữ liệu.

## 2. Mục tiêu và giả thuyết

Câu hỏi nghiên cứu (PECO) và giả thuyết đầy đủ: xem `01_question/question.md` mục 5.
- **Giả thuyết chính:** H₀: không có sự khác biệt về nguy cơ tái nhập viện 1 năm giữa 3 nhóm HbA1c
  lúc nhập viện (< 7% / 7–9% / > 9%). H₁: có sự khác biệt ở ít nhất một nhóm so với nhóm tham chiếu
  (< 7%). Loại: khảo sát mối liên quan (association), không phải so sánh hiệu quả điều trị — không áp
  dụng superiority/non-inferiority/equivalence. Kiểm định hai phía.
- **Mục tiêu phụ:** mô tả đặc điểm và tỷ lệ tái nhập viện 1 năm (Mục tiêu 1); phân tích phụ bằng
  HbA1c liên tục; thời gian-đến-tái nhập viện đầu tiên (Cox); tái nhập viện liên quan ĐTĐ; tử vong
  trong viện trong 1 năm (có hạn chế, xem mục 9).

## 3. Thiết kế nghiên cứu

Đoàn hệ hồi cứu, đơn trung tâm, lấy mẫu toàn bộ (census), không phân bổ, không ngẫu nhiên, không làm
mù (không can thiệp). Thời điểm đo phơi nhiễm: 24–48 giờ đầu nhập viện chỉ số. Thời gian theo dõi
outcome: 365 ngày kể từ ngày xuất viện (time zero), cố định và giống nhau cho mọi nhóm. Chi tiết đầy
đủ: `03_protocol/protocol.md`.

## 4. Outcome và estimand (theo khung ICH E9(R1))

| | Kết cục chính | Kết cục phụ — thời gian-đến-sự kiện |
|---|---|---|
| **Biến** | Tái nhập viện mọi nguyên nhân trong 365 ngày (nhị giá) | Thời gian từ xuất viện đến lần tái nhập viện đầu tiên |
| **Quần thể** | Toàn bộ mẫu phân tích (sau áp tiêu chuẩn chọn/loại trừ, mục 6 `protocol.md`) | Như trên |
| **Xử lý sự kiện xen vào (intercurrent events)** | Chính sách điều trị thực tế (treatment policy) — không loại trừ ai vì lý do xảy ra sau time zero, trừ tiêu chuẩn loại trừ đã định trước | Tử vong ngoài viện (không xác định được) được xử lý như **censored** tại thời điểm cuối theo dõi trong phân tích Cox chính — **giả định censoring không mang thông tin, có thể không đúng** nếu tử vong liên quan đến HbA1c (hạn chế đã nêu); Fine-Gray (tử vong trong viện là nguy cơ cạnh tranh) chỉ dùng ở phân tích độ nhạy |
| **Tóm tắt ở mức dân số** | OR (thô và đã hiệu chỉnh) kèm KTC 95% | HR (thô và đã hiệu chỉnh) kèm KTC 95%; sub-hazard ratio ở phân tích độ nhạy Fine-Gray |

## 5. Cỡ mẫu

*(Sao lại không đổi từ `03_protocol/sample-size.md` mục 7 — đoạn văn giải thích cỡ mẫu.)*

Cỡ mẫu được tính cho outcome chính là tái nhập viện mọi nguyên nhân trong 1 năm, với thiết kế đoàn hệ
hồi cứu so sánh 3 nhóm HbA1c lúc nhập viện (< 7% / 7–9% / > 9%, nhóm < 7% tham chiếu). Vì chưa có
nghiên cứu nào đo trực tiếp tỷ lệ tái nhập viện 1 năm hoặc hiệu ứng của HbA1c ở đúng mốc 1 năm cho
ĐTĐ type 2 nói chung (Gap 1, `02_evidence/gaps.md`), tỷ lệ tái nhập viện ở nhóm tham chiếu được giả
định là 20% và tỷ số chênh (OR) kỳ vọng giữa nhóm HbA1c > 9% và nhóm tham chiếu được giả định là 1,5
(lựa chọn thận trọng theo DELTA2, thấp hơn mức ngoại suy lạc quan ~1,75–2,0 từ [1]). Với
α = 0,05 (hai phía) và power = 80%, cần 535 người bệnh mỗi nhóm cực (1.070 tổng cho riêng 2 nhóm cực)
theo kiểm định tỷ lệ đơn giản; theo quy tắc số sự kiện/biến (EPV ≥ 10) cho mô hình hồi quy đa biến 6
biến, cần tối thiểu 300 người bệnh (toàn mẫu). Lấy giá trị lớn hơn, thận trọng, là 1.070 người bệnh —
gần với cỡ mẫu khả dụng ước tính trước loại trừ (~1.200), nên đề tài có thể chỉ đủ hoặc thiếu power
cho so sánh 2 nhóm HbA1c cực, tùy vào phân bố thật của HbA1c trong quần thể. Tính bằng `samplesize.py`
(two-proportions; regression-EPV). Phân tích độ nhạy cho thấy nếu OR thật nằm trong khoảng 1,3–2,0,
cỡ mẫu cần dao động từ 180 đến hơn 1.600 người mỗi nhóm cực (360 đến hơn 3.300 người cho 2 nhóm). **Các giá trị tỷ lệ tái nhập viện 1 năm
ở nhóm tham chiếu (20%) và OR kỳ vọng (1,5) là giả định, cần thay bằng số liệu có trích dẫn trước khi
khoá đề cương chính thức.**

Dưới thử nghiệm phân cấp (hierarchical testing) không áp dụng chặt — Mục tiêu 1 (mô tả) không cần
power; Mục tiêu 2 (phân tích chính) là outcome chính duy nhất, không có outcome phụ "quan trọng" cần
kiểm định phân cấp với α chia nhỏ.

## 6. Quần thể phân tích

- **Quần thể phân tích chính:** toàn bộ người bệnh thỏa tiêu chuẩn chọn, sau áp tiêu chuẩn loại trừ
  (`protocol.md` mục 2.1.1–2.1.2), có đủ dữ liệu cho outcome chính và các biến nhiễu trong mô hình
  chính. Không có khái niệm ITT/mITT/per-protocol theo nghĩa thử nghiệm can thiệp (không can thiệp).
- **Quần thể mô tả (Mục tiêu 1):** toàn bộ mẫu phân tích, kể cả người bị loại khỏi mô hình hồi quy
  chính do thiếu biến nhiễu (mô tả riêng số lượng/% bị loại).

## 7. Thống kê mô tả

- Bảng 1 (đặc điểm chung): biến liên tục — trung bình ± độ lệch chuẩn (nếu phân bố chuẩn) hoặc trung
  vị [khoảng liên phân vị] (nếu lệch); biến phân loại — tần số, tỷ lệ %. Trình bày theo 3 nhóm HbA1c
  và tổng.
- **Không** đi kèm giá trị p so sánh "baseline" giữa 3 nhóm theo cách diễn giải như một RCT (đây là
  đoàn hệ quan sát, không phải can thiệp ngẫu nhiên — nhưng khác CONSORT, việc mô tả sự khác biệt giữa
  3 nhóm phơi nhiễm quan sát được **là một phần hợp lý của mô tả nhiễu tiềm ẩn**, có thể trình bày có
  hoặc không kèm p tùy quy ước của hội đồng; khuyến nghị trình bày không kèm p, diễn giải bằng độ lớn
  khác biệt).
- Tỷ lệ tái nhập viện 1 năm tổng thể và theo từng nhóm HbA1c (Mục tiêu 1), kèm KTC 95% (Wilson).

## 8. Phân tích outcome chính

- **Mô hình:** hồi quy logistic đa biến. Biến phụ thuộc: tái nhập viện 1 năm (có/không). Biến độc lập
  chính: nhóm HbA1c (3 nhóm, nhóm < 7% là tham chiếu, 2 biến giả). Biến hiệu chỉnh (định trước, không
  chọn theo p đơn biến): tuổi, giới, thời gian mắc ĐTĐ, bệnh đồng mắc chính (`protocol.md` mục 2.7.2).
- **Ước lượng và báo cáo:** OR thô và OR đã hiệu chỉnh, kèm KTC 95%, cho từng nhóm so với nhóm tham
  chiếu. Đọc KTC 95% theo vùng ý nghĩa lâm sàng (ví dụ: toàn bộ KTC nằm trên OR = 1 và cận dưới xa 1 →
  có ý nghĩa và đáng kể; cận dưới rất gần 1 → có ý nghĩa thống kê nhưng độ lớn khiêm tốn, như trường
  hợp đã thấy ở [1] mốc 30 ngày) — không chỉ báo cáo p < 0,05.
- **Mức ý nghĩa:** α = 0,05, hai phía.
- **Kiểm tra giả định mô hình:** số sự kiện/biến (EPV) thực tế sau khi có dữ liệu (so với EPV ≥ 10 dự
  kiến ở `sample-size.md`); kiểm tra đa cộng tuyến (VIF) giữa các biến hiệu chỉnh; kiểm tra tuyến tính
  logit cho biến tuổi/thời gian mắc ĐTĐ (nếu dùng dạng liên tục trong mô hình).
- **Quy tắc đổi sang kiểm định thay thế:** nếu một nhóm HbA1c có < 5 sự kiện tái nhập viện (ô kỳ vọng
  quá nhỏ cho hồi quy ổn định), chuyển sang Fisher exact/χ² cho phân tích đơn biến không hiệu chỉnh,
  nêu rõ đây là phân tích thay thế do hạn chế cỡ mẫu — quyết định trước khi xem outcome theo nhóm.

## 9. Phân tích outcome phụ

| Outcome phụ | Kiểm định/mô hình | Estimand | KTC |
|---|---|---|---|
| HbA1c liên tục (mỗi 1%) thay cho 3 nhóm | Hồi quy logistic đa biến (cùng biến hiệu chỉnh) | OR mỗi 1% HbA1c | 95% |
| Tái nhập viện liên quan ĐTĐ | Hồi quy logistic đa biến | OR | 95% |
| Thời gian đến lần tái nhập viện đầu tiên | Hồi quy Cox (kiểm tra giả định PH bằng Schoenfeld residuals) | HR | 95% |
| Tử vong trong viện trong 1 năm | Thống kê mô tả (tần số/tỷ lệ) — **không đủ dữ liệu để phân tích đa biến có ý nghĩa do không xác định được tử vong ngoài viện** (hạn chế đã xác nhận) | Tỷ lệ | 95% (Wilson) |

**Chiến lược đa so sánh:** các outcome phụ được xem là **khám phá (exploratory)**, không hiệu chỉnh
đa so sánh (không Bonferroni/Holm) — chỉ outcome chính (tái nhập viện 1 năm, 3 nhóm HbA1c) được kiểm
định xác nhận ở α = 0,05; kết quả outcome phụ diễn giải như giả thuyết cần kiểm định lại, không phải
kết luận cuối cùng.

## 10. Phân tích bổ sung và phân nhóm

- **Phân tích độ nhạy Fine-Gray** (tử vong trong viện là nguy cơ cạnh tranh) cho outcome thời gian-
  đến-tái nhập viện — xem mục 4 và `protocol.md` mục 2.8; kết quả phải nêu rõ hạn chế đánh giá thấp số
  sự kiện cạnh tranh thật.
- **Phân tích độ nhạy dữ liệu thiếu:** loại trừ người có biến nhiễu bị thiếu > ngưỡng (quyết định cụ
  thể khi có dữ liệu thật, xem mục 11).
- **NLR/SII/SIRI** (đã xác nhận với tác giả): nếu tỷ lệ hồ sơ thiếu công thức bạch cầu phân loại lúc
  nhập viện ≤ 20%, đưa vào như phân tích thăm dò/phụ (không vào mô hình chính); nếu > 20%, bỏ hẳn.
- **Phân nhóm:** không có phân nhóm định trước nào khác được khai báo ở bước này (không phát sinh từ
  `protocol.md`); nếu tác giả muốn thêm phân nhóm (ví dụ theo tuổi), phải khai báo trước khi xem dữ
  liệu outcome và kiểm định bằng tương tác (interaction term), không suy luận từ phân nhóm riêng lẻ.

## 11. Dữ liệu thiếu

- **Cơ chế kỳ vọng:** MAR (missing at random) cho phần lớn biến nhiễu hành chính (ví dụ bệnh đồng
  mắc ghi thiếu do sai sót nhập liệu, không liên quan hệ thống đến giá trị thật); **không loại trừ**
  khả năng MNAR cho biến công thức bạch cầu phân loại nếu việc không chỉ định xét nghiệm này liên
  quan đến độ nặng bệnh (cần bàn luận khi có số liệu thật).
- **Phương pháp chính:** nếu tỷ lệ thiếu ở một biến nhiễu trong mô hình chính (tuổi, giới, thời gian
  mắc ĐTĐ, bệnh đồng mắc) ≤ 5%, dùng phân tích ca đầy đủ (complete case); nếu > 5–10%, dùng imputation
  đa biến (multiple imputation) cho biến đó, với mô hình imputation bao gồm outcome và các biến trong
  mô hình chính.
- **Độ nhạy:** so sánh kết quả hồi quy chính giữa complete case và sau imputation (nếu áp dụng); báo
  cáo cả hai nếu khác biệt đáng kể về kết luận.
- **HbA1c (phơi nhiễm):** người thiếu HbA1c lúc nhập viện hợp lệ đã bị **loại khỏi mẫu phân tích**
  theo tiêu chuẩn loại trừ (`protocol.md` mục 2.1.2, điểm 3) — không áp dụng imputation cho biến phơi
  nhiễm chính.

## 12. Phân tích giữa kỳ và dừng sớm

**Không áp dụng** — nghiên cứu hồi cứu trên dữ liệu đã có sẵn (2021–2023), không có giai đoạn thu
thập dữ liệu kéo dài cần phân tích giữa kỳ, không có DSMB.

## 13. An toàn

**Không áp dụng** — không can thiệp, không theo dõi an toàn (AE/SAE) theo nghĩa thử nghiệm.

## 14. Phần mềm và báo cáo

- **Phần mềm:** R hoặc Stata (script có thể chạy lại, lưu lại mã nguồn và phiên bản phần mềm — không
  dùng Excel cho phân tích suy luận). Không dùng "seed" ngẫu nhiên nào cần cố định vì không có chọn
  mẫu/phân bổ ngẫu nhiên và không có imputation Monte Carlo cần tái lập chính xác từng lần chạy (nếu
  dùng multiple imputation ngẫu nhiên, cố định seed và ghi lại).
- **Chuẩn báo cáo:** STROBE (đoàn hệ) — đã xác nhận bản 2007 còn hiện hành
  (`02_evidence/guidelines.md`). Số chữ số thập phân: tỷ lệ % lấy 1 chữ số; OR/HR và KTC 95% lấy 2 chữ
  số; p trình bày "p < 0,001" khi nhỏ hơn 0,001, ngược lại lấy 3 chữ số.

## 15. Thay đổi so với đề cương

| Thay đổi | Lý do | Ngày | Trước/sau khi xem outcome |
|---|---|---|---|
| Thêm bảng đăng ký phân tích A0–A5 (mục 16), mỗi phân tích ở mục 7–9 một ID | Để kiểm tra được phân tích nào đã định trước (`analysis_plan.py check`) | 2026-11-21 | Trước — chưa có dữ liệu |
| Bỏ phân tích độ nhạy Fine-Gray (mục 4, mục 10) | Sau xuất viện, HIS chỉ ghi nhận tử vong xảy ra trong một lần nhập viện tại BV Mô phỏng, tức là sau khi đã tái nhập viện; biến cố này không thể xảy ra trước và ngăn cản tái nhập viện, nên không phải nguy cơ cạnh tranh. Tử vong ngoài viện (nguy cơ cạnh tranh thật) không đo được — giữ là hạn chế ở mục 4 | 2026-11-21 | Trước — chưa có dữ liệu |
| Phần mềm: Python (pandas, statsmodels, lifelines; thư viện `crostats.py` sao vào `05_analysis/`) thay cho R/Stata | Script chạy lại được, cùng nguyên tắc mục 14 | 2026-11-21 | Trước — chưa có dữ liệu |

## 16. Bảng đăng ký phân tích (Analysis register)

Mỗi kết quả trong `05_analysis/output/results.json` mang một ID dưới đây. Phân tích không có trong bảng
là hậu kiểm (`POST-HOC A<n>:` trong `decisions.md`, trước khi chạy) hoặc sai lệch so với kế hoạch
(`DEVIATION A<n>:`).

| ID | Objective | Outcome | Population | Method | Covariates | Multiplicity |
|---|---|---|---|---|---|---|
| A0 | MT1, mô tả | Đặc điểm chung theo 3 nhóm HbA1c và tổng (Bảng 1); tỷ lệ tái nhập viện 1 năm chung và theo nhóm | Quần thể mô tả (mục 6) | Trung bình ± ĐLC hoặc trung vị [KTPV]; n (%); tỷ lệ kèm KTC 95% Wilson; không kèm p | Không | Không áp dụng |
| A1 | MT2, chính | Tái nhập viện mọi nguyên nhân trong 1 năm | Quần thể phân tích chính (mục 6, ca đầy đủ theo mục 11) | Hồi quy logistic: nhóm HbA1c 3 mức (< 7% tham chiếu); OR thô và OR hiệu chỉnh, KTC 95%; EPV, VIF; quy tắc < 5 sự kiện/nhóm ở mục 8 | Tuổi, giới, thời gian mắc ĐTĐ, bệnh đồng mắc chính (≥ 1 trong THA, BTM, bệnh tim mạch) | Không (kết cục chính duy nhất, α = 0,05 hai phía) |
| A2 | MT2, phụ | Tái nhập viện mọi nguyên nhân trong 1 năm | Như A1 | Hồi quy logistic, HbA1c liên tục (OR mỗi 1%) | Như A1 | Thăm dò, không hiệu chỉnh đa so sánh |
| A3 | MT1, phụ | Tái nhập viện liên quan ĐTĐ trong 1 năm | Như A1 | Hồi quy logistic, nhóm HbA1c 3 mức | Như A1 | Thăm dò, không hiệu chỉnh đa so sánh |
| A4 | MT1, phụ | Thời gian đến lần tái nhập viện đầu tiên (kiểm duyệt tại 365 ngày) | Như A1 | Hồi quy Cox, nhóm HbA1c 3 mức; HR thô và HR hiệu chỉnh, KTC 95%; giả định PH bằng phần dư Schoenfeld | Như A1 | Thăm dò, không hiệu chỉnh đa so sánh |
| A5 | MT1, phụ | Tử vong trong viện trong 1 năm | Quần thể mô tả | Tần số, tỷ lệ, KTC 95% Wilson; không phân tích đa biến (mục 9) | Không | Thăm dò |

Các phân tích có điều kiện ở mục 10–11 không có ID: NLR/SII/SIRI và nguy cơ dinh dưỡng (chỉ khi dữ
liệu đủ theo ngưỡng 20%), độ nhạy dữ liệu thiếu (chỉ khi một biến hiệu chỉnh thiếu > 5%). Nếu điều kiện
thoả và phân tích được chạy, nó nhận ID mới kèm dòng `DEVIATION A<n>:` trước khi chạy; nếu không, lý do
được ghi trong `decisions.md`.

## Tài liệu tham khảo

1. Hu X, Su X, Chen S, Wang Q, He F, Zhang R. Predictors of 30-day readmission in young and middle-aged T2DM patients: a retrospective cohort study. Endocrine. 2026;91(1). doi:10.1007/s12020-026-04626-3. PMID: 42068438.
