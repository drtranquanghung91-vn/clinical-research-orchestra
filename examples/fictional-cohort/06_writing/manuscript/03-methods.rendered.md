orchestra-role: methods

# ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU

**Thiết kế, địa điểm và thời gian.** Đây là nghiên cứu đoàn hệ hồi cứu, đơn trung tâm, thực hiện tại
Khoa Nội tiết, Bệnh viện Mô phỏng. Người bệnh được chọn theo thời điểm xuất viện (nhập viện chỉ số) từ
01/01/2021 đến 31/12/2022; kết cục được theo dõi 365 <!-- not-a-result: mốc theo dõi của đề tài, 01_question/question.md --> ngày kể từ ngày xuất viện của mỗi người bệnh, qua hệ thống thông tin bệnh
viện (HIS) đến 31/12/2023. Báo cáo theo STROBE (bản 2007).

**Đối tượng nghiên cứu.** Tiêu chuẩn chọn: chẩn đoán ĐTĐ type 2 (ICD-10 khối E11) ghi trong hồ sơ ra
viện; ≥ 18 tuổi; xuất viện từ Khoa Nội tiết, Bệnh viện Mô phỏng trong giai đoạn trên; có HbA1c đo trong
24–48 giờ đầu nhập viện. Tiêu chuẩn loại: tử vong trong lần nhập viện chỉ số; ĐTĐ thai kỳ/type 1/thứ
phát; không có HbA1c lúc nhập viện hợp lệ; hoặc xuất viện nhiều lần trong giai đoạn trên, khi đó chỉ
lần đầu được lấy làm nhập viện chỉ số. Chọn mẫu toàn bộ (census). Cỡ mẫu yêu cầu cho so sánh 2 nhóm
HbA1c cực (giả thuyết OR = 1,5 <!-- not-a-result: sample-size.md §3b, giả định -->) là 1.070 <!-- not-a-result: sample-size.md §3c --> người bệnh, so với 1.200 <!-- not-a-result: sample-size.md §2, số ước tính --> người bệnh khả dụng — rủi ro thiếu lực mẫu được chấp nhận trước khi xem dữ liệu (xem
Hạn chế). Số người bệnh thực tế đưa vào mẫu phân tích là 1070.

**Biến số.** Phơi nhiễm chính là HbA1c đo trong 24–48 giờ đầu nhập viện, phân tích chính theo 3 nhóm
< 7% / 7–9% / > 9% (nhóm < 7% tham chiếu); phân tích phụ dùng HbA1c liên tục (mỗi 1%). Kết cục chính là
tái nhập viện do mọi nguyên nhân trong vòng 365 <!-- not-a-result: mốc theo dõi của đề tài --> ngày
kể từ ngày xuất viện. Kết cục phụ gồm: tái nhập viện liên quan ĐTĐ/biến chứng đường huyết; thời gian
đến lần tái nhập viện đầu tiên (kiểm duyệt tại 365 <!-- not-a-result: mốc theo dõi của đề tài --> ngày);
và tử vong trong 1 năm — chỉ ghi nhận được tử vong **trong viện** nên chỉ báo cáo mô tả. Biến
nhiễu đưa vào mô hình hiệu chỉnh chính (định trước): tuổi, giới, thời gian mắc ĐTĐ, có/không ≥ 1 bệnh
đồng mắc chính. Sử dụng insulin khi nằm viện và thời gian nằm viện được đo sau hoặc đồng thời với HbA1c
nên có thể là biến trung gian; hai biến này chỉ dùng mô tả, không hiệu chỉnh trong mô hình chính.

**Nguồn dữ liệu.** Dữ liệu được trích xuất từ hồ sơ bệnh án điện tử và HIS của Bệnh viện Mô phỏng,
2021–2023.

**Sai số.** HIS chỉ ghi nhận tái nhập viện tại chính Bệnh viện Mô phỏng — người bệnh tái nhập viện ở
cơ sở khác bị tính nhầm là không tái nhập viện (hướng, độ lớn sai lệch chưa rõ). Nhiễu do chỉ định
được kiểm soát bằng hiệu chỉnh đa biến; sai lệch thời gian bất tử được hạn chế vì phơi nhiễm
được đo và cố định trước thời điểm bắt đầu theo dõi.

**Xử lý và phân tích số liệu.** Dữ liệu được quản lý và phân tích bằng Python (pandas, statsmodels)
<!-- not-a-result: 05_analysis/output/results.json → engine -->. Mục tiêu 1 dùng thống kê mô tả (trung
bình ± độ lệch chuẩn hoặc trung vị [khoảng liên phân vị]; tần số, tỷ lệ %; tỷ lệ tái nhập viện kèm
khoảng tin cậy 95% (KTC) Wilson). Mục tiêu 2 dùng hồi quy logistic đa biến, hiệu chỉnh các biến nhiễu
nêu trên, báo cáo tỷ số chênh (OR) thô và hiệu chỉnh kèm KTC 95%. Phân tích phụ, mang tính khám phá,
không hiệu chỉnh đa so sánh, gồm: HbA1c liên tục; tái nhập viện liên quan ĐTĐ; thời gian đến lần tái
nhập viện đầu tiên bằng hồi quy Cox (giả định nguy cơ tỷ lệ kiểm tra bằng phần dư Schoenfeld); tử vong
trong viện (chỉ mô tả). Phân tích độ nhạy Fine-Gray (tử vong là nguy cơ cạnh tranh) không thực hiện:
tử vong trong viện chỉ xảy ra sau tái nhập viện, không phải nguy cơ cạnh tranh thật. Mức ý nghĩa
α = 0,05, hai phía, chỉ áp dụng kiểm định xác nhận cho
kết cục chính. Biến thời gian mắc ĐTĐ thiếu ở 27 <!-- derived: R-A0-001.n - R-A1-003.n --> người bệnh
(2,5% <!-- derived: (R-A0-001.n - R-A1-003.n) / R-A0-001.n * 100 -->), biến duy nhất thiếu dữ liệu; vì
≤ 5% trên một biến nhiễu, phân tích ca đầy đủ được áp dụng. Thời gian theo dõi cố định 365 <!-- not-a-result: mốc theo dõi của đề tài --> ngày cho mọi người bệnh theo thiết kế. Sau khi xem kết quả đã
khóa, một phân tích hậu kiểm không đăng ký trước được thực hiện theo đề nghị của tác giả: hiệu ứng
nhóm HbA1c lên tái nhập viện có khác theo nhóm tuổi (< 65 so với ≥ 65) không, dùng cùng biến hiệu
chỉnh cộng kiểm định tương tác; kết quả này mang tính khám phá.

**Đạo đức nghiên cứu.** Đây là nghiên cứu hồi cứu trên dữ liệu đã có sẵn, không can thiệp. Dữ liệu
được mã hóa bằng số thứ tự nghiên cứu, loại bỏ định danh cá nhân trước khi phân tích. Không có số
quyết định: đây là dự án minh hoạ dùng dữ liệu mô phỏng, chưa nộp Hội đồng Đạo đức; một nghiên cứu
thật phải được Hội đồng Đạo đức của Bệnh viện chấp thuận trước khi trích xuất dữ liệu.
