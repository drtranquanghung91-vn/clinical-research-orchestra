# Chương 1. Tổng quan tài liệu

> **Dự án mô phỏng** (Example author). Bệnh viện Mô phỏng là địa điểm hư cấu dùng để minh họa quy
> trình; không có bệnh nhân thật. Chương này chỉ trích dẫn các tài liệu đã được xác minh
> (`verify_refs.py` → VERIFIED) trong `ledgers/references.json` của dự án; không trích dẫn gì từ bộ
> nhớ của mô hình.

## 1.1. Khái niệm và định nghĩa

Đái tháo đường (ĐTĐ) type 2 là bệnh lý rối loạn chuyển hóa đường huyết mạn tính, đặc trưng bởi đề
kháng insulin kết hợp suy giảm chức năng tế bào beta tụy. HbA1c (glycated hemoglobin A) là chỉ số
phản ánh nồng độ đường huyết trung bình trong khoảng 2–3 tháng trước đó, hiện được dùng rộng rãi cả
để chẩn đoán và theo dõi kiểm soát đường huyết. Trong nghiên cứu này, "tái nhập viện" được định nghĩa
là việc nhập viện lại do mọi nguyên nhân trong vòng 1 năm (365 ngày) kể từ ngày xuất viện của lần
nhập viện chỉ số, ghi nhận qua hệ thống thông tin bệnh viện (HIS) (xem `01_question/question.md`).

*Hạn chế của mục này:* bộ tài liệu tham khảo đã được xác minh (verified) của dự án ở thời điểm viết
chương này (6 tài liệu, xem mục 1.5–1.7) gồm các nghiên cứu về HbA1c/tái nhập viện và một chương
guideline nội viện; **không có tài liệu nào trong ledger khảo sát tiêu chuẩn chẩn đoán ĐTĐ type 2
nói chung**. Phần định nghĩa trên là định nghĩa vận hành (operational definition) dùng cho thiết kế
nghiên cứu, không phải một phát hiện cần trích dẫn thống kê; nếu hội đồng yêu cầu trích dẫn tiêu
chuẩn chẩn đoán ĐTĐ (ví dụ ADA hoặc WHO), cần bổ sung tìm kiếm và thêm tài liệu vào ledger trước khi
viết lại mục này.

## 1.2. Dịch tễ học

*Mục này chưa thể viết với trích dẫn đã xác minh.* Bộ tài liệu hiện có của dự án không chứa nghiên
cứu nào về tỷ lệ mắc/tỷ lệ mới mắc ĐTĐ type 2 hoặc tỷ lệ tái nhập viện ở quy mô dân số (quốc gia,
khu vực). Đây là một khoảng trống của chính chương này (không phải khoảng trống nghiên cứu của đề
tài — xem mục 1.7): cần chạy thêm `literature-search` cho các câu hỏi dịch tễ học chung trước khi bổ
sung số liệu gánh nặng bệnh (ví dụ tỷ lệ mắc ĐTĐ type 2, tỷ lệ tái nhập viện chung ở người bệnh nội
khoa) vào mục này.

## 1.3. Cơ chế bệnh sinh

Mục này chỉ nêu ở mức tối thiểu cần để giải thích biến số của nghiên cứu, không trình bày đầy đủ cơ
chế bệnh sinh ĐTĐ type 2. HbA1c cao kéo dài phản ánh tình trạng tăng đường huyết mạn tính, được cho
là có liên quan với tăng nguy cơ biến chứng cấp (hạ/tăng đường huyết, nhiễm trùng, mất nước) và biến
chứng mạn (tim mạch, thận, thần kinh) — các biến chứng này có thể là con đường trung gian (mediator)
giữa kiểm soát đường huyết kém và tái nhập viện. *Hạn chế:* phát biểu trên là kiến thức sinh lý bệnh
nền tảng, không gán trích dẫn cho một con số cụ thể vì không có tài liệu sinh lý bệnh nào trong
ledger đã xác minh của dự án.

## 1.4. Chẩn đoán và điều trị — liên quan đến biến số nghiên cứu

Theo "Standards of Care in Diabetes-2026", mục 16 "Diabetes Care in the Hospital" của Hiệp hội Đái
tháo đường Hoa Kỳ (American Diabetes Association, ADA) [@american2026] — guideline lâm sàng hiện
hành (bản 2026, đã xác nhận còn hiệu lực ở bước `guideline-check`, xem `02_evidence/guidelines.md`) —
kiểm soát đường huyết nội viện và lập kế hoạch xuất viện/chuyển tiếp chăm sóc (transition of care) là
một phần khuyến cáo chuẩn trong chăm sóc người bệnh ĐTĐ nhập viện. Tuy nhiên, trong phiên đánh giá
này chỉ đọc được phần tóm tắt chung của chương này trên PubMed (không đọc full-text), nên **chương
này không trích dẫn một ngưỡng HbA1c cụ thể hay một khuyến cáo định lượng nào từ guideline** —
nếu cần trích một khuyến cáo cụ thể (ví dụ mục tiêu đường huyết nội viện theo cá thể hóa), cần đọc
bản đầy đủ (doi:10.2337/dc26-S016) trước khi viết. Đây cũng là cơ sở của Khoảng trống 4 (mục 1.7):
guideline hiện hành không đưa ra ngưỡng HbA1c cụ thể để dự báo hoặc dự phòng tái nhập viện dài hạn.

Phân nhóm HbA1c lúc nhập viện dùng trong phân tích chính của đề tài (< 7% / 7–9% / > 9%, xem
`01_question/question.md` mục 6) là quy ước vận hành do tác giả lựa chọn và đã được xác nhận, không
phải một ngưỡng được trích trực tiếp từ guideline trên trong phạm vi tài liệu đã đọc của dự án này.

## 1.5. Các nghiên cứu trên thế giới

### 1.5.1. Can thiệp trong bệnh viện nhằm giảm tái nhập viện ở đái tháo đường type 2

Các can thiệp trong bệnh viện (giáo dục người bệnh, đội chăm sóc chuyên khoa, chuẩn hóa phác đồ
insulin...) nhằm giảm thời gian nằm viện và tái nhập viện ở người bệnh ĐTĐ type 2 đã được tổng hợp
trong một tổng quan hệ thống [@chakraborty2021]. Tuy nhiên, phần tóm tắt (abstract) của tổng quan
này không báo cáo số liệu gộp (effect size, khoảng tin cậy) cho hiệu quả cụ thể của từng loại can
thiệp, và nhiều tiêu chí AMSTAR 2 trọng yếu (đăng ký đề cương trước, chiến lược tìm kiếm, đánh giá
nguy cơ sai lệch của các nghiên cứu gộp vào) không thể xác định chỉ từ abstract (xem
`02_evidence/appraisal/chakraborty2021.md`). Vì vậy, tổng quan này chỉ cho biết **đã có nỗ lực can
thiệp** nhằm giảm tái nhập viện ở ĐTĐ type 2, và theo phần tóm tắt không ghi nhận thay đổi có ý nghĩa
về tỷ lệ tái nhập viện, và — quan
trọng hơn đối với đề tài — đây là câu hỏi về **hiệu quả can thiệp**, không phải về HbA1c lúc nhập
viện như một yếu tố nguy cơ tự nhiên (không can thiệp), nên không trả lời trực tiếp câu hỏi nghiên
cứu của đề tài này.

### 1.5.2. HbA1c lúc nhập viện và tái nhập viện ngắn hạn

HbA1c lúc nhập viện cao hơn có thể liên quan với tăng nguy cơ tái nhập viện trong vòng 30–31 ngày ở
người bệnh ĐTĐ type 2. Một nghiên cứu đoàn hệ hồi cứu tại Trung Quốc trên 950 người bệnh 18–59 tuổi
cho thấy mỗi 1% HbA1c lúc nhập viện tăng thêm liên quan với tăng nguy cơ tái nhập viện 30 ngày (tỷ số
chênh đã hiệu chỉnh — aOR — 1,15; khoảng tin cậy [KTC] 95% 1,03–1,29), dù cận dưới của khoảng tin cậy
rất gần 1, cho thấy độ lớn hiệu ứng khiêm tốn [@hu2026]. Một nghiên cứu khác trên 1.627 người bệnh ĐTĐ
type 2 xây dựng mô hình dự báo (nomogram) cho tái nhập viện ngoài kế hoạch trong 31 ngày cũng đưa
HbA1c vào làm một trong sáu biến dự báo được chọn bằng hồi quy LASSO, tuy không báo cáo chiều hướng
hay độ lớn hiệu ứng riêng của HbA1c trong phần tóm tắt [@cao2026]. Hai nghiên cứu đồng thuận về việc
HbA1c lúc nhập viện có vai trò trong dự báo tái nhập viện ngắn hạn, nhưng cả hai đều ở mốc thời gian
30–31 ngày — ngắn hơn nhiều so với mốc 1 năm mà đề tài này khảo sát — và đều là nghiên cứu đơn trung
tâm, hồi cứu, với một số điểm chưa rõ về mức độ hiệu chỉnh nhiễu đầy đủ hay kiểm định ngoài (external
validation) (xem `02_evidence/appraisal/hu2026.md`, `02_evidence/appraisal/cao2026.md`). Do đó, chưa
rõ liệu mối liên quan này có còn đúng ở mốc 1 năm hay không — đây là bằng chứng **gián tiếp**
(indirect) cho câu hỏi của đề tài.

### 1.5.3. Thời điểm đo HbA1c và chiều hướng của mối liên quan

Chưa rõ liệu chiều hướng của mối liên quan giữa HbA1c và tái nhập viện có phụ thuộc vào **thời điểm
đo HbA1c** hay không. Trong khi HbA1c đo **lúc nhập viện** cao hơn liên quan với tăng nguy cơ tái
nhập viện 30 ngày như trên [@hu2026], một nghiên cứu quy mô lớn tại Anh (46.357 lần xuất viện có ĐTĐ,
gộp cả đái tháo đường type 1 và type 2) lại ghi nhận HbA1c đo **sau xuất viện** thấp hơn liên quan
với tăng nguy cơ tái nhập viện (trung bình 57,82 so với 60,39 ở nhóm không tái nhập viện; p = 0,009;
hệ số Cohen's D 0,28 — hiệu ứng nhỏ theo quy ước Cohen) [@robbins2021]. Hai kết quả này không hẳn là
mâu thuẫn trực tiếp vì đo HbA1c ở hai thời điểm khác nhau (lúc nhập viện so với sau xuất viện), nhưng
gợi ý rằng mối liên quan giữa HbA1c và tái nhập viện có thể phức tạp hơn một chiều đơn giản, có thể
do nhiễu bởi chỉ định ngược (người được theo dõi HbA1c sát hơn sau xuất viện có thể là người đã được
nhận diện có nguy cơ cao hơn) [@robbins2021]. Phần phân tích chính của nghiên cứu Anh dùng kiểm định
đơn biến (không rõ có hiệu chỉnh đa biến hay không từ abstract), và chỉ có 399 trong số 46.357 lần
xuất viện có HbA1c lúc nhập viện — quá nhỏ để ước lượng riêng mối liên quan ở đúng thời điểm phơi
nhiễm mà đề tài này quan tâm (xem `02_evidence/appraisal/robbins2021.md`). Vì vậy, chưa rõ liệu phát
hiện "nghịch hướng" này có áp dụng cho HbA1c đo lúc nhập viện ở mốc theo dõi 1 năm hay không; đề tài
này cần nêu rõ sự khác biệt về thời điểm đo khi đối chiếu kết quả của chính mình với [@robbins2021].

### 1.5.4. Yếu tố dự báo tái nhập viện ở mốc thời gian dài hơn

Ở mốc thời gian dài hơn (365 ngày), các yếu tố dự báo tái nhập viện ở ĐTĐ type 2 có thể không còn
giống như ở mốc ngắn hạn. Một nghiên cứu xây dựng 9 mô hình học máy để dự báo tái nhập viện ở 30, 60
và 365 ngày trên 12.041 người bệnh ĐTĐ type 2 (cùng 2.007 người bệnh dùng để kiểm định thời gian cho
các mô hình ngắn/trung hạn) cho thấy yếu tố nổi bật nhất thay đổi theo mốc thời gian: tuổi chiếm ưu
thế ở mốc 30 ngày, các chỉ số viêm (SII, SIRI) và thời gian nằm viện nổi lên ở mốc 60 ngày, còn biến
chứng mạn tính đặc hiệu của ĐTĐ chiếm ưu thế ở mốc 365 ngày (phân tích SHAP) [@li2026]. Đây là bằng
chứng gần nhất về mốc thời gian 1 năm ở ĐTĐ type 2 nói chung, nhưng nghiên cứu này dùng mô hình dự báo
đa biến bằng học máy, không ước lượng một hiệu ứng độc lập (OR/HR) riêng cho HbA1c, và phần tóm tắt
không nêu rõ liệu HbA1c có nằm trong tập biến ứng viên của mô hình hay không (xem
`02_evidence/appraisal/li2026.md`). Do đó, dù gợi ý rằng bản chất nguy cơ tái nhập viện có thể "dịch
chuyển" từ các yếu tố cấp tính sang biến chứng mạn tính theo thời gian, nghiên cứu này **không thể**
dùng để trả lời trực tiếp liệu HbA1c lúc nhập viện có còn là yếu tố dự báo độc lập ở mốc 1 năm hay
không.

### 1.5.5. Tổng hợp bằng chứng thế giới

Gộp lại ba dòng bằng chứng trên (mục 1.5.2–1.5.4), **chưa rõ liệu** HbA1c lúc nhập viện có liên quan
độc lập với tái nhập viện mọi nguyên nhân trong 1 năm ở người bệnh ĐTĐ type 2 nói chung hay không.
Không có nghiên cứu nào trong bộ tài liệu đã xác minh của dự án đo đồng thời đúng phơi nhiễm (HbA1c
lúc nhập viện), đúng outcome (tái nhập viện mọi nguyên nhân) và đúng mốc thời gian (1 năm) ở đúng dân
số (ĐTĐ type 2 nói chung, không giới hạn theo một bệnh đồng mắc cụ thể). Mức độ tin cậy sơ bộ theo
GRADE cho kết cục này được đánh giá là **rất thấp** (very low), hạ bậc chủ yếu do tính gián tiếp
(indirectness) nghiêm trọng và một phần do nguy cơ sai lệch chưa được loại trừ ở một số nghiên cứu
(xem `02_evidence/appraisal/summary.md`, mục GRADE sơ bộ). Không có SR/MA nào gộp số liệu định lượng
cho câu hỏi này, nên không áp dụng việc đọc I²/khoảng dự báo (prediction interval).

## 1.6. Các nghiên cứu tại Việt Nam

Trong phiên tìm kiếm trên PubMed đã thực hiện ở bước `literature-search` (câu lệnh tìm kiếm riêng cho
"type 2 diabetes" + "readmission" + Việt Nam, xem `02_evidence/search-strategy.md`), **chưa tìm thấy
nghiên cứu nào thực hiện tại Việt Nam** khảo sát trực tiếp mối liên quan giữa HbA1c lúc nhập viện và
tái nhập viện ở người bệnh ĐTĐ type 2. Kết quả duy nhất liên quan đến "Vietnam" là một nghiên cứu về
người Việt nhập cư tại Úc, không phải nghiên cứu thực hiện tại Việt Nam, và do đó không được tính vào
bức tranh bằng chứng trong nước.

Cần nêu rõ: kết luận đúng ở đây là **"chưa tìm thấy trên PubMed/Consensus trong phiên tìm kiếm đã
thực hiện"**, không phải "chưa có nghiên cứu nào tại Việt Nam". Phần lớn tạp chí y khoa tiếng Việt
(Tạp chí Y học Việt Nam, Y học TP. Hồ Chí Minh…) không được lập chỉ mục trên PubMed và **chưa được
tìm trong phiên này** (hạn chế đã ghi trong `02_evidence/search-strategy.md`). Tác giả cần tìm thêm
trên Google Scholar và thư viện các trường y trước khi khẳng định khoảng trống về quần thể Việt Nam
trong phần đặt vấn đề cuối cùng của luận văn.

## 1.7. Khoảng trống nghiên cứu và lý do thực hiện đề tài

Bốn khoảng trống dưới đây được xác định đầy đủ, kèm kiểm tra phản chứng, tại `02_evidence/gaps.md`;
mục này chỉ tóm tắt và gắn mỗi khoảng trống với mục tiêu của đề tài (`01_question/question.md`).

**Khoảng trống 1 — phương pháp và mốc thời gian.** Chưa có nghiên cứu đoàn hệ dùng hồi quy đa biến
truyền thống (báo cáo OR/HR) khảo sát HbA1c lúc nhập viện và tái nhập viện **1 năm** ở ĐTĐ type 2 nói
chung: bằng chứng hiện có chỉ ở mốc 30–31 ngày [@hu2026; @cao2026] hoặc dùng mô hình học máy không
tách riêng hiệu ứng của HbA1c ở mốc 365 ngày [@li2026]. Đây là khoảng trống trực tiếp mà **Mục tiêu
cụ thể 2** của đề tài (xác định mối liên quan giữa HbA1c lúc nhập viện và tái nhập viện 1 năm, hiệu
chỉnh nhiễu) hướng tới lấp đầy.

**Khoảng trống 2 — quần thể Việt Nam.** Chưa tìm thấy trên PubMed nghiên cứu nào thực hiện tại Việt
Nam về chủ đề này (mục 1.6). Đề tài, thực hiện tại Khoa Nội tiết, Bệnh viện Mô phỏng, trực tiếp lấp
khoảng trống quần thể này (với lưu ý về giới hạn tìm kiếm đã nêu ở mục 1.6).

**Khoảng trống 3 — chưa nhất quán theo thời điểm đo.** Hướng tác động của HbA1c lên tái nhập viện có
thể khác nhau tùy thời điểm đo (lúc nhập viện so với sau xuất viện) [@hu2026; @robbins2021] (mục
1.5.3). Đề tài đo HbA1c **lúc nhập viện**, nhất quán với **Mục tiêu cụ thể 2**, và cần thảo luận rõ
điểm khác biệt này khi so sánh với [@robbins2021] ở phần biện luận của luận văn.

**Khoảng trống 4 — chưa có khuyến cáo thực hành.** Guideline hiện hành (ADA Standards of Care-2026,
mục 16) [@american2026] không đưa ra ngưỡng HbA1c cụ thể để dự phòng tái nhập viện dài hạn ở ĐTĐ type
2 (mục 1.4). Nếu đề tài tìm thấy mối liên quan có ý nghĩa, kết quả có thể là bước đầu góp phần cung
cấp bằng chứng cho loại khuyến cáo này trong tương lai — đây là ý nghĩa thực tiễn ("So what?") đã nêu
ở `01_question/question.md` mục 5, không phải là một mục tiêu cụ thể của chính đề tài.

Tổng hợp lại, với mức độ tin cậy GRADE sơ bộ là **rất thấp** cho câu hỏi "HbA1c lúc nhập viện và tái
nhập viện 1 năm ở ĐTĐ type 2" (mục 1.5.5), đề tài "HbA1c lúc nhập viện và nguy cơ tái nhập viện trong
1 năm ở người bệnh đái tháo đường type 2 xuất viện tại Bệnh viện Mô phỏng (2021–2023): một nghiên cứu
đoàn hệ hồi cứu" là cần thiết để tạo ra bằng chứng trực tiếp, phù hợp với mốc thời gian và quần thể mà
y văn hiện có chưa trả lời được.

## Tài liệu tham khảo

{REFERENCES}
