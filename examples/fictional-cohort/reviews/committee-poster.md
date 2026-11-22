# Rehearsal phản biện — poster (layout: pathway, in 90×120 cm; nội dung giống editorial/figure-led)

Ngày chuẩn bị: 2026-11-22. Nguồn: `07_present/poster/poster.json`, `ledgers/results-ledger.json`
(khoá tại G3, xem `decisions.md`/`gates/state.json`), `03_protocol/sap.md`, `03_protocol/sample-size.md`,
`decisions.md` (toàn bộ, đặc biệt các mục 2026-11-21/22 về F4, A6, post-hoc).

STATUS: WEAK POINTS

Dự án có đủ tài liệu để trả lời hầu hết câu hỏi hội đồng/khán giả sẽ hỏi cạnh poster. Không có gap
nào ở dạng "không đọc được file". Các điểm yếu dưới đây là **thật**, đã được chính dự án ghi nhận
(không phải suy diễn thêm) — tác giả cần nói ra được, không né.

## QUESTIONS

1. Thông điệp chính của poster viết "OR hiệu chỉnh 1,42 (KTC 95% 0,94–2,15)" nhưng khoảng tin cậy
   chứa giá trị 1. Đây có phải là một kết quả dương tính không? Tại sao vẫn đưa lên làm "key message"?
   [section: clinical meaning / ý nghĩa thống kê vs ý nghĩa lâm sàng]
   Trả lời: Không, đây không phải một phát hiện dương tính chắc chắn. OR hiệu chỉnh HbA1c >9% so
   với <7% là 1,42 (KTC 95% 0,94–2,15; p=0,097) (R-A1-004) — khoảng tin cậy đi từ "không khác" (0,94,
   dưới 1) đến "tăng nguy cơ hơn gấp đôi" (2,15). Dữ liệu này tương thích với cả "không có liên quan"
   và "liên quan khá mạnh". Thông điệp trên poster (`07_present/poster/poster.json: key_message`)
   dùng đúng từ "có thể đi kèm... nhưng chưa đủ để khẳng định" — không dùng động từ nhân quả, không
   nói "có ý nghĩa thống kê". Đây là diễn giải trung thực của một khoảng tin cậy rộng, không phải
   phát hiện dương tính.

2. Cỡ mẫu có đủ cho so sánh 2 nhóm HbA1c cực không? Tính n=1.070 nhưng thực tế mỗi nhóm có bao nhiêu?
   [section: sample size]
   Trả lời: Cỡ mẫu tính trước (two-proportions, OR giả định 1,5, p₁ giả định 20% — cả hai GIẢ ĐỊNH,
   không có nguồn trực tiếp, `03_protocol/sample-size.md` mục 2) yêu cầu 535 người/nhóm cực để đạt
   power 80%. Thực tế: nhóm <7% chỉ có 235 người (R-A0-002.n), nhóm >9% có 321 người (R-A0-004.n) —
   cả hai đều thấp hơn 535 đáng kể. Đây chính là "giả định rủi ro nhất" mà tác giả đã chấp nhận ở G2
   (`decisions.md`, mục "Protocol + SAP approved"). Nói thẳng: nghiên cứu **thiếu power thực tế** cho
   so sánh nhóm cực; bảng power trong `sample-size.md` mục 4 cho thấy ở n=300/nhóm power chỉ ~55%,
   và ở n=235 còn thấp hơn — không có số post-hoc power chính xác được tính trong dự án cho n=235,
   đây là việc cần làm thêm nếu hội đồng hỏi số cụ thể (not in the project: post-hoc power tại đúng
   n=235/321 chưa được `samplesize.py power` chạy).

3. Hình sơ đồ mẫu trên poster ("Hình 1", F4: n=1070 → loại 27 → 1043) có phải là sơ đồ STROBE đầy đủ
   không? Vì sao không có số liệu sàng lọc/loại trừ ban đầu?
   [section: methods choice / reporting guideline]
   Trả lời: Không, đây chủ động là một sơ đồ rút gọn, không phải STROBE đầy đủ — chú thích trên chính
   hình (F4, `07_present/figures/figures.json`) nói rõ điều này. Bộ dữ liệu mô phỏng được sinh ra
   trực tiếp ở cỡ mẫu phân tích cuối (1070), không có bước sàng lọc/đủ tiêu chuẩn chọn mẫu nào được
   ghi lại trước đó (`decisions.md`, mục "F4 (STROBE flow) blocked", 2026-11-22). Hai ô duy nhất có
   số liệu thật: toàn đoàn hệ n=1070 (R-A0-001.n) và quần thể vào mô hình hiệu chỉnh n=1043
   (R-A1-003.n), loại 27 vì thiếu biến hiệu chỉnh (thời gian mắc ĐTĐ). Trên dữ liệu thật, bước tiếp
   theo đúng STROBE phải truy lại số hồ sơ được sàng lọc ban đầu và lý do loại trừ theo từng tiêu chí —
   việc này **chưa làm được** ở dự án ví dụ này vì không tồn tại số liệu đó.

4. Dữ liệu dùng trong nghiên cứu là dữ liệu thật của bệnh nhân hay dữ liệu giả?
   [section: data / tính trung thực]
   Trả lời: Dữ liệu mô phỏng hoàn toàn (`tools/simulate_cohort.py`, seed 20261121, 1.070 dòng) — đây
   là một dự án ví dụ/luyện tập, không có giá trị lâm sàng, không đại diện cho bệnh nhân thật ở "Bệnh
   viện Mô phỏng" (tên giả định). Ghi chú này có mặt rõ ràng, có heading riêng ("Ghi chú về dữ liệu")
   trên cả 3 layout poster, không giấu trong phần tài liệu tham khảo (`decisions.md`, mục 2026-11-22
   "Poster revised"). Khi trình bày thật ở hội nghị với dữ liệu mô phỏng, phải nói rõ điều này ngay
   từ đầu, không đợi khán giả hỏi.

5. Thiết kế hồi cứu, đơn trung tâm — kết quả áp dụng được cho đối tượng nào? Có nên ngoại suy ra toàn
   tỉnh/toàn quốc không?
   [section: generalisability]
   Trả lời: Không. Đây là đoàn hệ hồi cứu, lấy mẫu toàn bộ (census) tại một khoa Nội tiết của một
   bệnh viện, một giai đoạn xuất viện 01/2021–12/2022 (`03_protocol/sap.md` mục 3). Kết quả chỉ mô tả
   quần thể người bệnh ĐTĐ type 2 xuất viện tại đúng cơ sở và giai đoạn đó; không có cơ sở để ngoại suy
   sang bệnh viện khác, tuyến khác hay toàn quốc. Giới hạn này đã được liệt trong phần "Kết luận và
   hạn chế" trên poster.

6. Vì sao chia HbA1c thành 3 nhóm (<7/7–9/>9%) để làm phân tích chính, trong khi phân tích HbA1c liên
   tục mới có power cao hơn (ít mất thông tin hơn)?
   [section: methods choice]
   Trả lời: Quyết định định trước trong đề cương (`decisions.md`, mục "Research question confirmed"):
   3 nhóm được chọn làm phân tích chính vì **dễ diễn giải lâm sàng theo ngưỡng kiểm soát đường huyết**
   (`sample-size.md` mục 8, câu hỏi hội đồng #3); HbA1c liên tục là phân tích phụ. Kết quả thực tế của
   phân tích phụ liên tục: OR mỗi 1% HbA1c = 1,02 (KTC 95% 0,93–1,11; p=0,677) (R-A2-002) — khoảng
   tin cậy rất hẹp quanh 1, không gợi ý một liên quan tuyến tính rõ, yếu hơn cả phân tích 3 nhóm. Nên
   nói thẳng khi được hỏi: chọn 3 nhóm vì lý do lâm sàng, không phải vì nhóm 3 cho kết quả "đẹp" hơn —
   thực ra phân tích liên tục còn yếu hơn.

7. Mô hình hiệu chỉnh những biến nhiễu nào? Vì sao không đưa insulin lúc nhập viện hoặc số ngày nằm
   viện vào mô hình — hai biến này khác rất nhiều giữa 3 nhóm HbA1c (insulin: 14% ở <7% so với 50% ở
   >9%)?
   [section: confounding and bias]
   Trả lời: Mô hình A1 hiệu chỉnh 4 biến: tuổi, giới, thời gian mắc ĐTĐ, bệnh đồng mắc (≥1 trong
   THA/BTM/bệnh tim mạch) (`03_protocol/sap.md` mục 8). Insulin lúc nhập viện và số ngày nằm viện
   **không** được đưa vào vì được phân loại là biến đo sau/đồng thời với cửa sổ phơi nhiễm HbA1c
   (24–48 giờ đầu), tức là **có thể là biến trung gian (mediator)**, không phải biến nhiễu — hiệu
   chỉnh một biến trung gian sẽ loại một phần hiệu ứng thật của HbA1c (`decisions.md`, mục "Protocol
   design", điểm 2). Đây là một quyết định phương pháp có lý do, không phải thiếu sót, nhưng cần nói
   được logic này khi bị hỏi.

8. Có bao nhiêu phân tích được thực hiện trong nghiên cứu này? Có hiệu chỉnh cho nhiều so sánh
   (multiplicity) không?
   [section: multiplicity and post-hoc]
   Trả lời: Đăng ký trước trong SAP: A0 (mô tả) đến A5 (tử vong, chỉ mô tả) (`03_protocol/sap.md` mục
   16), cộng 1 phân tích hậu kiểm A6 (phân nhóm tuổi) phát sinh sau khi có dữ liệu, được ghi "POST-HOC"
   trước khi chạy (`decisions.md`, mục 2026-11-21 "Post-hoc subgroup by age"). SAP mục 9 nói rõ: chỉ
   outcome chính (A1, tái nhập viện mọi nguyên nhân, 3 nhóm HbA1c) được kiểm định xác nhận ở α=0,05;
   tất cả outcome phụ (A2–A5) và A6 là **khám phá, không hiệu chỉnh đa so sánh** (không Bonferroni/
   Holm). Điều này có nghĩa p của A3 (xem câu 9) không nên đọc như một kết quả xác nhận cuối cùng.

9. Phân tích tái nhập viện liên quan ĐTĐ (A3, không có trên poster) cho OR rất mạnh và có ý nghĩa
   thống kê rõ (OR >9% vs <7% = 5,50, KTC 95% 2,42–12,49, p<0,001) — mạnh hơn nhiều so với kết quả
   chính trên poster. Vì sao không đưa lên poster làm thông điệp chính?
   [section: multiplicity and post-hoc — điểm yếu cần chuẩn bị kỹ nhất]
   Trả lời: A3 (R-A3-001: OR 7-9% vs <7% = 2,97, KTC 95% 1,31–6,73, p=0,009; R-A3-002: OR >9% vs
   <7% = 5,50, KTC 95% 2,42–12,49, p<0,001) là outcome **phụ, khám phá**, không phải outcome chính
   (`03_protocol/sap.md` mục 9, 16). Không đưa lên poster vì: (a) tác giả đã cố định thông điệp chính
   trước khi xem kết quả outcome phụ ("không được làm mạnh hơn hoặc đổi hướng thông điệp", xem
   `decisions.md` mục "Poster built"), và A3 dùng một định nghĩa outcome hẹp hơn (tái nhập viện *liên
   quan ĐTĐ*, không phải mọi nguyên nhân); (b) EPV của mô hình A3 chỉ 15,67 (R-A3-008) — thấp hơn A1,
   ít ổn định hơn; (c) không hiệu chỉnh đa so sánh cho outcome phụ, nên một kết quả "đẹp" trong số
   nhiều phân tích phụ dễ là nhiễu ngẫu nhiên (multiple-comparisons). Đây là **điểm yếu cần nói trung
   thực**: kết quả A3 mạnh và đáng chú ý, cần được nêu là phát hiện cần kiểm định lại trên một nghiên
   cứu khác (giả thuyết sinh ra, không phải kết luận xác nhận), không phải lý do để thay đổi thông
   điệp chính trên poster.

10. Phân tích dưới nhóm theo tuổi (<65 so với ≥65) trên poster có không? Có phải phân tích định
    trước không? Kết quả ra sao?
    [section: multiplicity and post-hoc]
    Trả lời: Không có trên poster. Đây là phân tích hậu kiểm A6, yêu cầu bởi tác giả sau khi đã có dữ
    liệu (không có trong SAP đăng ký trước), ghi rõ "POST-HOC" trước khi chạy (`decisions.md`, mục
    2026-11-21). Kết quả: p tương tác (HbA1c × nhóm tuổi) = 0,835 (R-A6-015, n=1043) — không có bằng
    chứng hiệu ứng khác nhau theo tuổi. Cả hai tầng tuổi có khoảng tin cậy rất rộng và chứa 1: <65,
    OR >9% vs <7% = 1,61 (0,86–3,02) (R-A6-002); ≥65, OR >9% vs <7% = 1,27 (0,72–2,24) (R-A6-009).
    Nếu được hỏi tại poster: nói rõ đây là khám phá, không có bằng chứng hiệu ứng khác nhau theo tuổi,
    không nên diễn giải riêng từng tầng tuổi như một phát hiện độc lập.

11. Phân tích Cox giả định gì về tử vong? Có vi phạm giả định không?
    [section: confounding and bias / giả định mô hình]
    Trả lời: Hệ thống thông tin bệnh viện chỉ ghi được tử vong **trong viện**, không ghi được tử vong
    ngoài viện. Mô hình Cox chính (A4) coi người tử vong ngoài viện (không quan sát được) là "kiểm
    duyệt" (censored) tại cuối theo dõi — đây là **giả định censoring không mang thông tin**, có thể
    sai nếu tử vong ngoài viện liên quan đến HbA1c (người HbA1c rất cao có thể tử vong ngoài viện
    nhiều hơn, làm giảm ảo số ca tái nhập viện quan sát được ở nhóm đó) (`03_protocol/sap.md` mục 4,
    10; `decisions.md` mục "Protocol confirm items"). Fine-Gray (tử vong là nguy cơ cạnh tranh) đã bị
    loại khỏi SAP vì về logic, tử vong trong viện chỉ xảy ra sau một lần tái nhập viện trong hệ thống
    này nên không phải nguy cơ cạnh tranh thật — nhưng tử vong *ngoài viện* (nguy cơ cạnh tranh thật)
    vẫn không đo được. Giả định PH (Schoenfeld) không bị vi phạm trong mô hình đã chạy (p tối thiểu
    thô=0,472 [R-A4-004], hiệu chỉnh=0,274 [R-A4-013]) — nhưng đó là một giả định khác, không thay
    thế cho vấn đề censoring không mang thông tin nêu trên.

12. Dữ liệu thiếu bao nhiêu? Xử lý thế nào?
    [section: missing data]
    Trả lời: Chỉ một biến có dữ liệu thiếu: thời gian mắc ĐTĐ (`dm_duration_years`), thiếu 27/1.070 =
    2,5% (`decisions.md`, mục "Data preparation"). Theo ngưỡng định trước trong SAP mục 11 (≤5% →
    phân tích ca đầy đủ, >5–10% → multiple imputation), 2,5% ≤ 5% nên dùng **complete-case**, không
    imputation — quyết định có ngưỡng định trước, không phải tuỳ chọn tại chỗ. Đây là lý do mô hình
    hiệu chỉnh A1/A4 chỉ còn 1.043 người (loại 27). Không có biến nhiễu khác bị thiếu.

## WEAK POINTS TO PREPARE (xếp theo mức độ nên chuẩn bị kỹ)

1. **Thiếu power cho so sánh nhóm cực.** Yêu cầu 535/nhóm, thực tế 235 (<7%) và 321 (>9%)
   (R-A0-002.n, R-A0-004.n so với `sample-size.md` mục 4). Cách nói trung thực: "nghiên cứu này có đủ
   cỡ mẫu để xây dựng mô hình hồi quy ổn định (EPV), nhưng có thể thiếu power cho so sánh 2 nhóm HbA1c
   cực — đây là một hạn chế đã được nhận diện và chấp nhận từ bước thiết kế, không phải phát hiện sau
   khi có kết quả." Không nói "nghiên cứu đủ cỡ mẫu" một cách chung, không có điều kiện.

2. **A3 (tái nhập viện liên quan ĐTĐ) cho kết quả mạnh, có ý nghĩa, nhưng là phân tích phụ/khám phá,
   không trên poster.** Nếu khán giả tự tìm thấy qua luận văn/báo cáo phân tích đầy đủ và hỏi "sao
   không đưa lên poster", câu trả lời sẵn sàng: kết quả này cần một nghiên cứu xác nhận riêng (không
   hiệu chỉnh đa so sánh, outcome hẹp hơn, EPV thấp hơn — R-A3-008 = 15,67), không phải lý do đổi
   thông điệp chính đã cố định.

3. **Sơ đồ mẫu (F4) không phải STROBE đầy đủ.** Phải nói ngay khi giới thiệu sơ đồ, không đợi hội
   đồng chỉ ra — dữ liệu mô phỏng này không có số liệu sàng lọc/loại trừ ban đầu, chỉ có 2 ô
   (1070 → 1043).

4. **Dữ liệu mô phỏng, một trung tâm, hồi cứu.** Ba hạn chế độc lập, không nên gộp mơ hồ thành một
   câu "có hạn chế" — nói rõ từng ý khi được hỏi riêng.

5. **Giả định censoring không mang thông tin trong Cox** có thể sai nếu tử vong ngoài viện liên quan
   đến HbA1c — một giả định chưa kiểm được bằng dữ liệu hiện có, không phải một kiểm định đã "đạt".

## GAPS

- Không có gap về đọc file: toàn bộ `project.yaml`, `03_protocol/protocol.md`, `03_protocol/sap.md`,
  `ledgers/results-ledger.json`, `decisions.md`, `07_present/poster/poster.json` và các file liên
  quan (`07_present/figures/figures.json`, `03_protocol/sample-size.md`) đều đọc được.
- `06_writing/thesis/ch3-results.rendered.md` chưa đọc trực tiếp trong buổi rà soát này (đã lấy đủ số
  liệu tương ứng từ `ledgers/results-ledger.json`, vốn là nguồn khoá — không ảnh hưởng đến các câu
  trả lời trên); nếu hội đồng hỏi số thứ tự bảng/trang trong luận văn, tác giả nên tự đối chiếu thêm.
- **Not in the project**: post-hoc power thực tế tại đúng n=235 (nhóm <7%) và n=321 (nhóm >9%) chưa
  được `samplesize.py power` tính cụ thể — chỉ có bảng tại n=300/400/500/535 trong `sample-size.md`
  mục 4. Nếu hội đồng hỏi con số chính xác, tác giả cần chạy thêm `samplesize.py power --design
  two-props --n 235 ...` trước buổi báo cáo, không ước lượng miệng.
