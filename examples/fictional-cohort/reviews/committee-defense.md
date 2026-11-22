# Rehearsal phản biện — bảo vệ luận văn thạc sĩ (20 phút trình bày, 18 slide chính + 5 slide dự phòng)

Ngày chuẩn bị: 2026-11-22. Nguồn: `ledgers/results-ledger.json` (khoá G3), `01_question/question.md`
(đã sửa mục tiêu 2, xem `decisions.md` mục "X-OBJ"), `03_protocol/protocol.md`, `sap.md`, `sample-size.md`,
`04_data/codebook.md`, `cleaning-log.md`, `05_analysis/analysis-report.rendered.md`,
`06_writing/thesis/ch1-literature-review.md`, `ch3-results.rendered.md`, `decisions.md` (toàn bộ),
`07_present/defense/deck.json`, `reviews/consistency.md`, `reviews/committee-poster.md`.

STATUS: WEAK POINTS

Phạm vi câu hỏi rộng hơn bộ câu hỏi poster (`reviews/committee-poster.md`, chỉ xoay quanh 4 hình):
lần này bao quát tổng quan tài liệu, phương pháp luận, cỡ mẫu, đạo đức, toàn bộ kết quả (kể cả A2-A6
không có trên slide), bàn luận, hạn chế, kết luận, kiến nghị và tính minh bạch khi dùng công cụ hỗ trợ.

Ghi chú phạm vi: `06_writing/thesis/` hiện chỉ có Chương 1 (tổng quan) và Chương 3 (kết quả) — chưa có
file Chương 2/4/5 riêng; nội dung bàn luận/hạn chế/kết luận/kiến nghị hiện chỉ có trong các slide của
`07_present/defense/deck.json`. Nếu quyển luận văn nộp hội đồng có các chương này viết riêng, cần đối
chiếu thêm trước khi bảo vệ (xem GAPS).

## QUESTIONS

1. Kết quả phân tích phụ A3 (tái nhập viện liên quan ĐTĐ) cho OR rất mạnh và có ý nghĩa (>9% vs <7%:
   OR 5,50; KTC 95% 2,42–12,49; p<0,001), mạnh hơn nhiều so với kết quả chính A1 (OR 1,42; KTC 95%
   0,94–2,15; p=0,097). Vì sao không lấy A3 làm kết luận chính?
   [section: multiplicity and post-hoc]
   Trả lời: A3 là outcome phụ, khám phá, định trước trong SAP (`sap.md` §9, §16) nhưng không hiệu
   chỉnh đa so sánh và dùng một định nghĩa outcome hẹp hơn (tái nhập viện liên quan ĐTĐ, không phải
   mọi nguyên nhân). EPV của mô hình A3 chỉ 15,67 (R-A3-008), thấp hơn nhiều so với A1 (EPV 39,
   R-A1-010) — mô hình kém ổn định hơn. Thông điệp chính đã được cố định trước khi xem kết quả outcome
   phụ. Số liệu: R-A3-001 (7–9% vs <7%, OR 2,97 [1,31–6,73], p=0,009), R-A3-002 (>9% vs <7%, OR 5,50
   [2,42–12,49], p<0,001), `ch3-results.rendered.md` §3.3.2. Đúng câu trả lời: kết quả này là giả
   thuyết sinh ra cần xác nhận ở nghiên cứu khác, không phải kết luận.

2. Cỡ mẫu tính trước yêu cầu 535 người/nhóm cực để đạt power 80% (OR giả định 1,5), nhưng thực tế
   nhóm <7% chỉ có 235 và nhóm >9% chỉ có 321. Power thực tế là bao nhiêu?
   [section: sample size]
   Trả lời: `sample-size.md` §4 cho bảng power theo n: 300→0,554; 400→0,678; 500→0,773; 535→0,80
   (α=0,05, OR giả định=1,5). Thực tế nhóm <7% n=235 (R-A0-002.n) và nhóm >9% n=321 (R-A0-004.n), cả
   hai dưới 535 — power thực tế thấp hơn 0,554 (giá trị thấp nhất trong bảng). Not in the project:
   `samplesize.py power` chưa được chạy đúng tại n=235/321 — nếu hội đồng hỏi số chính xác, cần chạy
   thêm trước khi bảo vệ, không ước lượng miệng.

3. Mô hình hiệu chỉnh chỉ có 4 biến (tuổi, giới, thời gian mắc ĐTĐ, bệnh đồng mắc), không đưa insulin
   lúc nằm viện hay số ngày nằm viện vào — trong khi tỷ lệ dùng insulin khác rất rõ giữa nhóm (14,0%
   ở <7% so với 49,8% ở >9%, Bảng 3.1). Đây có phải là bỏ sót biến nhiễu quan trọng không?
   [section: confounding and bias]
   Trả lời: Không phải bỏ sót — là quyết định phân loại trước khi thu thập dữ liệu. Insulin và số
   ngày nằm viện được đo sau/đồng thời với cửa sổ phơi nhiễm HbA1c (24–48h đầu), nên được xếp là biến
   trung gian (mediator) khả năng, không phải biến nhiễu; hiệu chỉnh một biến trung gian sẽ loại một
   phần hiệu ứng thật của HbA1c (`protocol.md` §2.7.2). Số liệu mô tả: R-A0-054 (insulin, <7%, 14,0%),
   R-A0-056 (insulin, >9%, 49,8%). Cần trả lời đúng logic khi bị hỏi, không chỉ nói "theo kế hoạch".

4. Phân tích Cox chính giả định gì về tử vong? Giả định đó có bị vi phạm không?
   [section: confounding and bias / giả định mô hình]
   Trả lời: HIS chỉ ghi nhận được tử vong trong viện, không ghi được tử vong ngoài viện. Mô hình Cox
   chính (A4) coi người tử vong ngoài viện (không quan sát được) là censored — giả định censoring
   không mang thông tin, có thể sai nếu tử vong ngoài viện liên quan đến HbA1c (`sap.md` §4, §10).
   Giả định PH (Schoenfeld) không bị vi phạm: p tối thiểu mô hình thô = 0,472 (R-A4-004), mô hình hiệu
   chỉnh = 0,274 (R-A4-013) — nhưng đây là một giả định khác, không thay thế vấn đề censoring. Fine-Gray
   bị loại khỏi SAP vì tử vong trong viện ở hệ thống này chỉ xảy ra sau một lần tái nhập viện, không
   phải nguy cơ cạnh tranh thật (`sap.md` §15).

5. Mục tiêu cụ thể 2 trong đề cương (`question.md`) từng ghi hiệu chỉnh 6 yếu tố (gồm cả thời gian
   nằm viện, dùng insulin), nhưng mô hình thực tế (Bảng 3.3) chỉ hiệu chỉnh 4 biến. Tại sao có sự
   khác biệt này, và đã được sửa chưa?
   [section: methods / tính nhất quán]
   Trả lời: Đây là một wording drift thật, được phát hiện bởi `consistency_audit.py` và agent
   `consistency-auditor` trước khi làm slide (`reviews/consistency.md`, mã X-OBJ) — mục tiêu 2 trong
   `question.md` còn sót cách viết cũ từ trước khi có quyết định phân loại biến trung gian
   (2026-11-21). `protocol.md` §2.7.2 (xác nhận sau, có giá trị cao hơn) mới là nguồn đúng: chỉ 4 biến
   hiệu chỉnh. `question.md` đã được sửa lại đúng ngày 2026-11-22 để khớp với `protocol.md`, `sap.md`
   §16, Bảng 3.3, slide phương pháp của deck. Không đọc nhầm bản cũ khi trả lời hội đồng.

6. Quy trình phê duyệt đạo đức của đề tài đã hoàn tất chưa? Miễn chấp thuận tham gia cá nhân đã được
   cấp chưa?
   [section: ethics]
   Trả lời: Chưa. Đề cương đề nghị nộp Hội đồng Đạo đức trong nghiên cứu y sinh học của Bệnh viện Mô
   phỏng, xin miễn chấp thuận tham gia cá nhân với 3 lý do (hồi cứu không can thiệp, dữ liệu khử định
   danh, không khả thi liên hệ lại ~1.200 người bệnh) — nhưng quyết định cuối cùng vẫn thuộc hội đồng
   đạo đức của cơ sở, chưa phải một sự miễn trừ đã được cấp (`protocol.md` §2.9). Văn bản/thông tư cụ
   thể của Bộ Y tế chưa được xác minh trong dự án — not in the project.

7. Vì sao chọn đoàn hệ hồi cứu, không chọn bệnh–chứng hoặc cắt ngang?
   [section: methods choice]
   Trả lời: Đoàn hệ hồi cứu được chọn vì outcome không hiếm (thực tế 22,1% — R-A0-061), dữ liệu HIS
   có sẵn theo chuỗi thời gian, và giữ được thông tin thời gian-đến-sự kiện cho Cox (A4) mà
   case-control sẽ mất. Case-control bị loại vì không cần thiết về số lượng và tăng nguy cơ sai lệch
   chọn chứng từ một nguồn dữ liệu hành chính duy nhất. Cắt ngang bị loại vì lãng phí lợi thế dữ liệu
   theo dõi dọc và cho kết luận yếu hơn.

8. Luận văn nói "chưa tìm thấy nghiên cứu tại Việt Nam" — điều này có nghĩa là "chưa có nghiên cứu nào
   ở Việt Nam" không?
   [section: tổng quan tài liệu]
   Trả lời: Không, hai câu này khác nhau. Kết luận đúng và duy nhất được hỗ trợ là "chưa tìm thấy trên
   PubMed/Europe PMC trong phiên tìm kiếm đã thực hiện" (`ch1-literature-review.md` §1.6), không phải
   "chưa ai làm ở Việt Nam" — vì phần lớn tạp chí y khoa tiếng Việt không được lập chỉ mục trên PubMed
   và chưa được tìm trong phiên này. Phải nói đúng mức độ chứng cứ, không phóng đại thành "khoảng
   trống tuyệt đối".

9. Toàn bộ tài liệu trích dẫn trong tổng quan đều ở mốc 30 ngày hoặc dùng mô hình học máy, và GRADE sơ
   bộ cho câu hỏi của đề tài là "rất thấp". Nền tảng đặt vấn đề như vậy có đủ chắc để xây dựng giả
   thuyết 1 năm không?
   [section: tổng quan tài liệu / đặt vấn đề]
   Trả lời: Đúng, đây là một hạn chế có thật, không che giấu. `ch1-literature-review.md` §1.5.5 nêu
   rõ: không có nghiên cứu nào đo đồng thời đúng phơi nhiễm, đúng outcome và đúng mốc 1 năm; mức tin
   cậy GRADE sơ bộ rất thấp do tính gián tiếp nghiêm trọng. Đây chính là lý do đề tài dùng giả thuyết
   hai phía và vì sao hai tham số cỡ mẫu phải ghi GIẢ ĐỊNH (`sample-size.md` mục 2) — bằng chứng rất
   thấp không phải là lý do không làm đề tài, mà chính là khoảng trống mà đề tài hướng tới lấp đầy.

10. Chẩn đoán đái tháo đường type 2 trong nghiên cứu dựa trên tiêu chuẩn nào? Có trích dẫn ADA hay WHO
    không?
    [section: methods choice / định nghĩa]
    Trả lời: Không có trích dẫn tiêu chuẩn chẩn đoán cụ thể. Định nghĩa là vận hành: chẩn đoán đã được
    bác sĩ điều trị xác lập và ghi mã ICD-10 khối E11 trong hồ sơ ra viện (`protocol.md` §2.1.1). Lý
    do: `02_evidence/guidelines.md` chỉ xác minh được mục 16 (chăm sóc nội viện) của ADA Standards of
    Care-2026, không phải mục tiêu chuẩn chẩn đoán. Nếu hội đồng yêu cầu trích dẫn cụ thể, cần chạy
    thêm `guideline-check` trước khi hoàn thiện — not in the project hiện tại.

11. Dữ liệu thiếu bao nhiêu, xử lý bằng cách nào?
    [section: missing data]
    Trả lời: Chỉ một biến thiếu: thời gian mắc ĐTĐ, 27/1.070 = 2,5% (`cleaning-log.md`). Theo ngưỡng
    định trước trong SAP §11 (≤5% → complete-case; >5–10% → multiple imputation), 2,5% ≤ 5% nên dùng
    complete-case, không imputation — đây là lý do mô hình hiệu chỉnh A1/A4 chỉ còn n=1043
    (R-A1-003.n, R-A4-005.n), loại 27. Không có biến nhiễu khác bị thiếu; biến phơi nhiễm HbA1c thiếu
    đã bị loại khỏi mẫu theo tiêu chuẩn loại trừ, không imputation cho phơi nhiễm.

12. Tổng cộng bao nhiêu phân tích được thực hiện? Có hiệu chỉnh cho nhiều so sánh không?
    [section: multiplicity and post-hoc]
    Trả lời: Đăng ký trước: A0 (mô tả) đến A5 (tử vong, chỉ mô tả), `sap.md` §16. Thêm 1 phân tích hậu
    kiểm A6 (phân nhóm tuổi), ghi "POST-HOC" trước khi chạy. SAP §9 nói rõ: chỉ outcome chính (A1, 3
    nhóm HbA1c) được kiểm định xác nhận ở α=0,05; A2–A6 là khám phá, không hiệu chỉnh đa so sánh
    (không Bonferroni/Holm). p<0,001 của A3 (câu 1) không nên đọc như một kết quả xác nhận cuối cùng.

13. Phân tích dưới nhóm theo tuổi (A6) có định trước không? Kết quả ra sao?
    [section: multiplicity and post-hoc]
    Trả lời: Không định trước — là hậu kiểm, yêu cầu bởi tác giả sau khi đã có dữ liệu, ghi "POST-HOC"
    trước khi chạy ngày 2026-11-21. Kết quả: p tương tác HbA1c × nhóm tuổi = 0,835 (R-A6-015, n=1043)
    — không có bằng chứng hiệu ứng khác nhau theo tuổi. Cả hai tầng đều KTC rộng chứa 1: <65 tuổi, OR
    >9% vs <7% = 1,61 (0,86–3,02) (R-A6-002); ≥65 tuổi, OR = 1,27 (0,72–2,24) (R-A6-009). Không nên
    diễn giải riêng từng tầng tuổi như phát hiện độc lập.

14. "Tử vong trong 1 năm" trong luận văn có nghĩa là tử vong do mọi nguyên nhân không?
    [section: methods choice / outcome definition]
    Trả lời: Không. HIS chỉ ghi nhận được tử vong trong viện; không xác định được tử vong ngoài viện.
    Biến này chỉ phản ánh "tử vong trong viện ghi nhận được trong 365 ngày", không phải tử vong do mọi
    nguyên nhân thật. Số liệu: R-A5-001 (chung, 2,2%, KTC 1,5–3,3%), từ 1,3% (<7%, R-A5-002) đến 2,8%
    (>9%, R-A5-004) — chỉ dùng cho mục tiêu mô tả, không phân tích đa biến.

15. Sơ đồ chọn mẫu trên slide/luận văn (F4: 1070 → loại 27 → 1043) có phải là sơ đồ STROBE đầy đủ
    không?
    [section: methods choice / reporting guideline]
    Trả lời: Không — là sơ đồ rút gọn, chủ động, không phải STROBE đầy đủ (ghi rõ trên hình F4 và
    trong notes của slide diagram). Dữ liệu mô phỏng được sinh trực tiếp ở cỡ mẫu phân tích cuối
    (1.070), không có số liệu sàng lọc/loại trừ ban đầu nào được ghi lại. Hai ô duy nhất có số thật:
    toàn đoàn hệ n=1070 (R-A0-001.n) và quần thể vào mô hình hiệu chỉnh n=1043 (R-A1-003.n), loại 27
    vì thiếu thời gian mắc ĐTĐ. Trên dữ liệu thật, bước tiếp theo đúng STROBE phải truy lại số hồ sơ
    sàng lọc ban đầu theo từng tiêu chí loại trừ — chưa làm được vì không có số liệu đó.

16. OR hiệu chỉnh nhóm >9% là 1,42 nhưng KTC 95% chứa 1 (0,94–2,15). Anh/chị khuyên bác sĩ lâm sàng
    làm gì "ngày thứ Hai" với kết quả này?
    [section: clinical meaning]
    Trả lời: Không nên thay đổi thực hành dựa trên kết quả này một mình — KTC 95% đi từ "không khác"
    (0,94) đến "tăng nguy cơ hơn gấp đôi" (2,15) (R-A1-004), tương thích với cả "không liên quan" và
    "liên quan đáng kể". Điều có thể nói: hướng kết quả nhất quán với y văn 30 ngày, gợi ý cần theo
    dõi sát hơn sau xuất viện cho nhóm HbA1c cao trong khi chờ nghiên cứu xác nhận lớn hơn — không kết
    luận nhân quả, không khuyến cáo ngưỡng điều trị cụ thể.

17. Kết quả của đề tài có phù hợp với y văn quốc tế không? Có gì khác?
    [section: bàn luận / so sánh y văn]
    Trả lời: Hướng kết quả phù hợp với nghiên cứu 30 ngày tại Trung Quốc (aOR 1,15; KTC 95%
    1,03–1,29) [@hu2026]. Khác biệt: đề tài này ở mốc 1 năm (dài hơn nhiều), KTC rộng hơn và chứa giá
    trị 1 (R-A1-004). Về chiều hướng theo thời điểm đo, [@robbins2021] ghi nhận HbA1c đo sau xuất viện
    thấp hơn lại liên quan tái nhập viện cao hơn — khác thời điểm đo (sau xuất viện) với đề tài này
    (lúc nhập viện), cần nêu rõ khi bàn luận.

18. Kết quả này áp dụng được cho ai? Có nên ngoại suy ra toàn tỉnh/toàn quốc không?
    [section: generalisability]
    Trả lời: Không. Đoàn hệ hồi cứu, lấy mẫu toàn bộ (census) tại một khoa Nội tiết của một bệnh
    viện, giai đoạn xuất viện 01/2021–12/2022 duy nhất. Kết quả chỉ mô tả đúng quần thể và giai đoạn
    đó; không có cơ sở ngoại suy sang bệnh viện khác, tuyến khác hay toàn quốc.

19. Vì sao chọn phân tích 3 nhóm HbA1c làm chính, trong khi phân tích HbA1c liên tục có power cao hơn?
    [section: methods choice]
    Trả lời: Quyết định định trước: 3 nhóm được chọn vì dễ diễn giải lâm sàng theo ngưỡng kiểm soát
    đường huyết. Kết quả thực tế của phân tích liên tục (phụ): OR mỗi 1% HbA1c = 1,02 (KTC 95%
    0,93–1,11; p=0,677) (R-A2-002) — KTC hẹp quanh 1, yếu hơn cả phân tích 3 nhóm. Cần nói thẳng: chọn
    3 nhóm vì lý do lâm sàng định trước, không phải vì cho kết quả "đẹp" hơn.

20. Công cụ AI (Claude/Anthropic) được dùng ở mức nào trong luận văn? Điều này có cần công bố không?
    [section: minh bạch/quy trình]
    Trả lời: Có công bố, theo ICMJE. `02_evidence/search-strategy.md` ghi rõ việc tìm kiếm, sàng lọc,
    tổng hợp bảng bằng chứng và soạn thảo văn bản ở `02_evidence/` được thực hiện với sự hỗ trợ của
    Claude (Anthropic); tác giả chịu trách nhiệm kiểm tra lại toàn bộ trích dẫn/số liệu trước khi dùng
    cho công bố. `sap.md` §1 cũng ghi tương tự cho SAP. Cần nói rõ: AI hỗ trợ tìm kiếm/soạn thảo văn
    bản và chạy script phân tích theo chỉ đạo của tác giả; tác giả là người quyết định thiết kế, xác
    nhận mọi giả định và chịu trách nhiệm cuối cùng về nội dung.

21. Kết luận và kiến nghị của luận văn có vượt quá những gì dữ liệu cho phép không?
    [section: kết luận / kiến nghị]
    Trả lời: Theo đúng ngôn ngữ được quy định trước ("có liên quan với", không dùng "là nguyên nhân
    của"), kết luận trong deck khớp với KTC chứa 1 của R-A1-004. Kiến nghị ("xác nhận ở nghiên cứu đa
    trung tâm trước khi áp dụng lâm sàng") chỉ xuất phát từ đúng những gì đã kết luận, không thêm đề
    xuất ngưỡng điều trị hay thay đổi phác đồ cụ thể chưa có cơ sở. Đây là điểm mạnh cần giữ nguyên
    khi trả lời — không "nói mạnh hơn" dữ liệu cho phép dù bị hội đồng gợi ý.

22. Đóng góp mới (tính mới) và ý nghĩa thực tiễn của đề tài là gì, khi mức độ tin cậy của bằng chứng
    nền (GRADE) là rất thấp?
    [section: tính mới / ý nghĩa thực tiễn]
    Trả lời: Tính mới nằm ở việc lấp 3 khoảng trống đã xác định: (1) mốc thời gian 1 năm với hồi quy
    đa biến truyền thống; (2) quần thể Việt Nam (chưa tìm thấy trên PubMed); (3) đo HbA1c đúng lúc
    nhập viện (khác thời điểm với [@robbins2021]). Ý nghĩa thực tiễn: nếu khẳng định được ở nghiên cứu
    lớn hơn, có thể góp phần xây dựng khuyến cáo ngưỡng HbA1c để dự phòng tái nhập viện dài hạn — hiện
    ADA Standards of Care-2026 mục 16 chưa có ngưỡng này. Cần nói rõ: đây là bước đầu, không phải bằng
    chứng đủ để thay đổi khuyến cáo ngay.

## WEAK POINTS TO PREPARE (xếp theo mức độ nên chuẩn bị kỹ)

1. **Thiếu power cho so sánh 2 nhóm HbA1c cực.** Yêu cầu 535/nhóm, thực tế 235 (<7%, R-A0-002.n) và
   321 (>9%, R-A0-004.n). Cách nói trung thực: "đủ cỡ mẫu để mô hình hồi quy ổn định (EPV=39,
   R-A1-010), nhưng có thể thiếu power cho so sánh 2 nhóm cực — hạn chế đã nhận diện và chấp nhận từ
   bước thiết kế (G2), không phải phát hiện sau khi có kết quả." Không nói "đủ cỡ mẫu" một cách chung.

2. **A3 (tái nhập viện liên quan ĐTĐ) mạnh và có ý nghĩa nhưng là phân tích phụ/khám phá, không là
   kết luận chính.** Chuẩn bị sẵn lý do không hiệu chỉnh đa so sánh, EPV thấp hơn (15,67 vs 39),
   outcome hẹp hơn — nói là giả thuyết cần xác nhận, không phải kết luận.

3. **X-OBJ — mục tiêu cụ thể 2 vừa được sửa lại ngày 2026-11-22** để khớp với protocol.md (4 biến,
   không phải 6). Phải chắc chắn đọc đúng bản đã sửa khi trình bày bằng lời, không lỡ đọc lại số
   "6 biến" từ bản cũ trong đầu.

4. **Giả định censoring không mang thông tin trong Cox** (tử vong ngoài viện không đo được) — một giả
   định chưa kiểm được bằng dữ liệu hiện có, khác với giả định PH (đã kiểm, không vi phạm). Không nhầm
   hai loại giả định này khi trả lời.

5. **Sơ đồ chọn mẫu (F4) không phải STROBE đầy đủ.** Phải nói ngay khi giới thiệu, không đợi hội đồng
   chỉ ra.

6. **Nền tảng bằng chứng của Chương 1 ở mức GRADE rất thấp**, và một số mục (1.1 chẩn đoán, 1.2 dịch
   tễ) tự nhận "chưa thể viết với trích dẫn đã xác minh" — cần nói đây là khoảng trống của chính chương
   tổng quan (do giới hạn tìm kiếm), không phải khoảng trống nghiên cứu của đề tài, tránh nhầm lẫn hai
   loại "gap" khi hội đồng hỏi.

7. **Đạo đức chưa có quyết định phê duyệt/miễn trừ thật** — chỉ là đề nghị trong đề cương; cần nói rõ
   tình trạng thật, không ngụ ý đã được chấp thuận.

8. **Tiêu chuẩn chẩn đoán ĐTĐ type 2 là định nghĩa vận hành (ICD-10), không trích dẫn ADA/WHO cụ thể**
   — chuẩn bị câu trả lời ngắn nếu hội đồng hỏi ngưỡng/tiêu chuẩn chẩn đoán kèm nguồn.

## GAPS

- `06_writing/thesis/` chỉ có Chương 1 (tổng quan) và Chương 3 (kết quả); không có file Chương 2
  (đối tượng-phương pháp đầy đủ dạng chương thesis, hiện chỉ có `03_protocol/protocol.md`), Chương 4
  (bàn luận) hoặc Chương 5 (kết luận-kiến nghị) riêng — nội dung này hiện chỉ có trong các slide
  bàn luận/hạn chế/kết luận/kiến nghị của `07_present/defense/deck.json`. Nếu quyển luận văn nộp hội
  đồng có các chương này viết riêng, cần đối chiếu thêm trước khi bảo vệ.
- Post-hoc power chính xác tại n=235 (nhóm <7%) và n=321 (nhóm >9%) chưa được tính (`samplesize.py
  power` chưa chạy đúng các giá trị này) — cần chạy thêm nếu hội đồng hỏi số cụ thể.
- Số hiệu văn bản/thông tư của Bộ Y tế về đạo đức nghiên cứu y sinh học chưa xác minh trong dự án
  (`protocol.md` §2.9 tự ghi "chưa xác minh trong phiên này").
- Tìm kiếm tài liệu tiếng Việt (Google Scholar, Tạp chí Y học Việt Nam/TP.HCM) cho quần thể Việt Nam
  chưa được thực hiện — đã tự ghi nhận là hạn chế trong `02_evidence/search-strategy.md` và
  `ch1-literature-review.md` §1.6.

Ba điểm yếu cần chuẩn bị kỹ nhất: (1) thiếu power thực tế cho so sánh 2 nhóm HbA1c cực (235/321 so với
yêu cầu 535); (2) kết quả phân tích phụ A3 mạnh hơn nhiều kết quả chính nhưng không được dùng làm kết
luận — phải giải thích đúng lý do (đa so sánh, EPV thấp); (3) giả định censoring không mang thông tin
trong mô hình Cox (tử vong ngoài viện không đo được).
