# Phương pháp

Bài viết này báo cáo theo PRISMA 2020 [@page2021]. Vì toàn bộ câu hỏi lâm sàng và các nghiên cứu được đưa vào
là hư cấu (xem Tóm tắt, Đặt vấn đề), phần Phương pháp dưới đây mô tả chính xác quy trình đã thực hiện trên bộ dữ
liệu mô phỏng này, không phải một tổng quan hệ thống thật.

## Đăng ký và đề cương

Đề cương (`03_protocol/sr-protocol.md`) được viết và khoá (gate G2) trước khi bất kỳ bản ghi nào được sàng lọc,
gồm tiêu chuẩn chọn mẫu, chiến lược tìm kiếm và một đăng ký phân tích (A0–A3) cố định mô hình thống kê trước khi
xem kết quả. Vì đây là bài tập minh hoạ phần mềm, đề cương không được nộp lên PROSPERO; bản nháp minh hoạ ở
`03_protocol/prospero.md` (không áp dụng ngoài dự án này — xem "Thông tin khác"). Không có sửa đổi nào so với
đề cương đã khoá.

## Tiêu chuẩn lựa chọn

Chỉ nhận thử nghiệm ngẫu nhiên có đối chứng (randomised controlled trial) trên người lớn (từ 18 tuổi) nhập viện
vì bệnh nội khoa cấp, so sánh thuốc X (hư cấu) với giả dược, báo cáo tử vong mọi nguyên nhân trong 30 ngày.
Không giới hạn ngôn ngữ hay năm công bố. Lý do loại trừ ở bước toàn văn được quy định trước trong đề cương:
thiết kế không phải thử nghiệm ngẫu nhiên có đối chứng, không báo cáo tử vong trong 30 ngày, hoặc nhóm chứng
không phải giả dược.

## Nguồn thông tin và chiến lược tìm kiếm

Vì các nghiên cứu được đưa vào là hư cấu, nguồn duy nhất để tìm nghiên cứu đưa vào là một tệp xuất mô phỏng
("Simulated database", nền tảng fictional, mã chuỗi S1 — tác giả tự chạy và xuất, không phải một cơ sở dữ liệu y
văn thật) chạy ngày <!-- not-a-result: 02_evidence/sr/search-log.csv --> 23/11/2026. Chuỗi tìm kiếm đầy đủ ở phụ
lục `02_evidence/sr/strings.md`.

PubMed **không** được dùng để tìm nghiên cứu đưa vào, vì không tồn tại thử nghiệm thật nào về "thuốc X". PubMed
chỉ được dùng, qua `search_lit.py`, để tìm và xác minh (`verify_refs.py`) các tài liệu phương pháp luận thật
được trích dẫn trong bài này: PRISMA 2020 [@page2021], RoB 2 [@sterne2019], GRADE [@guyatt2008], thống kê I² về
dị biệt [@higgins2003], khoảng dự đoán [@inthout2016] và phương pháp REML cho mô hình hiệu ứng ngẫu nhiên
[@veroniki2016]. Không có số liệu hư cấu nào được gán cho các tài liệu thật này.

## Quy trình lựa chọn nghiên cứu

Hai người đánh giá độc lập, hư cấu (Reviewer A, Reviewer B) sàng lọc độc lập từng bản ghi ở hai bước: tiêu
đề/tóm tắt rồi toàn văn. Trước bước sàng lọc tiêu đề/tóm tắt, một trợ lý AI đọc tiêu đề và tóm tắt của từng bản
ghi và ghi lại một **gợi ý** (include/exclude/maybe) kèm lý do vào `02_evidence/sr/ai-suggestions.csv`; gợi ý
này không phải quyết định sàng lọc — quyết định cuối cùng ở cả hai bước do Reviewer A và Reviewer B thực hiện
độc lập trên phiếu riêng của từng người, ghi tại `02_evidence/sr/screening.csv`. Bất đồng được giải quyết bằng
đồng thuận giữa hai người (hàng `consensus`); một hàng đồng thuận chỉ được tính sau khi cả hai người đã quyết
định trên cùng bản ghi. Độ thống nhất giữa hai người đánh giá: κ = 0,89 ở bước tiêu đề/tóm tắt và κ = 0,59 ở
bước toàn văn (<!-- not-a-result: screening.py kappa --stage ta / --stage ft -->).

## Quy trình thu thập dữ liệu và các biến số

Hai người trích xuất độc lập (`04_data/sr/extraction-reviewer-a.csv`, `04_data/sr/extraction-reviewer-b.csv`),
hợp nhất thành một tệp đồng thuận (`04_data/sr/extraction.csv`) sau khi đối chiếu từng bất đồng. Biến số thu
thập cho mỗi thử nghiệm: thiết kế, dân số, cỡ mẫu và số sự kiện tử vong ở mỗi nhóm (thuốc X, giả dược) cho kết
cục tử vong mọi nguyên nhân tại 30 ngày, và nhận định nguy cơ sai lệch tổng quát. Vì các thử nghiệm là hư cấu,
không có tác giả nghiên cứu thật nào để liên hệ khi thiếu dữ liệu; một bất đồng về số sự kiện tử vong ở nhóm giả
dược của thử nghiệm tamsett2020 [@tamsett2020] được ghi lại và giải quyết bằng đồng thuận (xem cột
`consensus_note` trong tệp trích xuất), không suy diễn số liệu còn thiếu.

## Kết cục

Kết cục duy nhất trong đăng ký phân tích: tử vong mọi nguyên nhân tại thời điểm 30 ngày.

## Nguy cơ sai lệch trong từng nghiên cứu

Nguy cơ sai lệch của mỗi thử nghiệm được đánh giá bằng công cụ RoB 2 (Cochrane risk-of-bias tool for randomized
trials) [@sterne2019] trên 5 miền (ngẫu nhiên hoá, sai lệch do can thiệp phân công, dữ liệu kết cục thiếu, đo
lường kết cục, lựa chọn kết quả báo cáo), với nhận định tổng quát theo đúng thuật toán của công cụ (mức xấu nhất
trong các miền, không phải điểm cộng dồn). Cả Reviewer A và Reviewer B đánh giá độc lập; bất đồng giải quyết
bằng đồng thuận. Chi tiết theo từng miền và từng thử nghiệm ở `04_data/sr/rob.csv` và Hình 2.

## Thước đo hiệu quả

Risk ratio (RR) cho kết cục tử vong mọi nguyên nhân 30 ngày.

## Phương pháp tổng hợp

Một thử nghiệm đủ điều kiện gộp vào phân tích chính khi đáp ứng tiêu chuẩn lựa chọn (Tiêu chuẩn lựa chọn) và
báo cáo được số sự kiện tử vong trên số người theo dõi ở từng nhóm (bảng 2×2) cho kết cục tử vong mọi nguyên
nhân tại 30 ngày; cả năm thử nghiệm được đưa vào đều đáp ứng điều kiện này, không có số liệu nào cần suy diễn
hay quy đổi đơn vị trước khi gộp. Bất đồng duy nhất về số liệu trích xuất (tamsett2020 [@tamsett2020], số sự
kiện tử vong ở nhóm giả dược) được giải quyết bằng đồng thuận giữa hai người đánh giá trước khi đưa vào phân
tích gộp (xem Quy trình thu thập dữ liệu).

Các thử nghiệm đủ điều kiện được gộp bằng mô hình hiệu ứng ngẫu nhiên, ước lượng phương sai giữa nghiên cứu bằng
phương pháp REML (restricted maximum likelihood) — một trong các phương pháp ước lượng phương sai giữa nghiên
cứu được so sánh bởi Veroniki và cộng sự [@veroniki2016] — không hiệu chỉnh Hartung-Knapp-Sidik-Jonkman.
Mô hình này được chọn trước khi xem bất kỳ kết quả nào, ghi trong đăng ký phân tích của đề cương (A1); một thay
đổi mô hình sau khi khoá đề cương sẽ được ghi là một dòng `DEVIATION` trong `decisions.md` — không có sửa đổi
nào ở bài viết này. Dị biệt giữa các nghiên cứu được báo cáo bằng τ², thống kê I² [@higgins2003] và khoảng dự
đoán (prediction interval) 95% [@inthout2016] — khoảng dự đoán chỉ được tính khi số nghiên cứu gộp k ≥ 3, theo
quy định trước của đề cương (`03_protocol/sr-protocol.md` mục 3.8). Hai phân tích bổ sung được đăng ký
trước: phân tích dưới nhóm theo nhận định nguy cơ sai lệch tổng quát (A2) và phân tích loại dần từng nghiên cứu
(leave-one-out, A3) để kiểm tra độ nhạy của ước lượng gộp chính. Kết quả tổng hợp được trình bày bằng một bảng
đặc điểm nghiên cứu, một forest plot và một bảng tóm tắt kết quả GRADE (Kết quả).

Tính toán được thực hiện bằng công cụ `meta.py` và `grade.py` của phần mềm dự án này (Python, thư viện chuẩn),
không dùng gói R/metafor.

## Đánh giá sai lệch công bố

Kiểm định Egger và biểu đồ hình phễu chỉ được quy định thực hiện khi số nghiên cứu gộp k ≥ 10; vì phân tích gộp
chính chỉ gộp năm thử nghiệm, sai lệch công bố không được đánh giá bằng kiểm định thống kê — đây là một hạn chế
được nêu lại ở phần Bàn luận.

## Đánh giá độ tin cậy của bằng chứng tổng hợp

Độ tin cậy của bằng chứng cho kết cục tử vong mọi nguyên nhân 30 ngày được chấm theo GRADE (Grading of
Recommendations Assessment, Development and Evaluation) [@guyatt2008], xuất phát từ mức cao cho bằng chứng từ
thử nghiệm ngẫu nhiên và hạ bậc theo nguy cơ sai lệch, tính không thống nhất, tính gián tiếp, tính không chính
xác và sai lệch công bố, với lý do hạ bậc ghi tại `05_analysis/meta/grade.json`. Bảng tóm tắt kết quả (summary
of findings) ở Bảng 2.
