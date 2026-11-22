orchestra-role: discussion

# CHƯƠNG 4. BÀN LUẬN

**Dữ liệu mô phỏng.** Toàn bộ số liệu được bàn luận trong chương này là dữ liệu MÔ PHỎNG, sinh bởi
script mô phỏng cohort của dự án ví dụ (`tools/simulate_cohort.py`); không phải số liệu bệnh nhân
thật, không có giá trị lâm sàng hay khoa học ngoài mục đích minh họa quy trình.

## 4.1. Đặc điểm chung và tỷ lệ tái nhập viện (Mục tiêu 1)

Trong mẫu nghiên cứu gồm {{R-A0-001.n}} người bệnh đái tháo đường (ĐTĐ) type 2, phân bố tuổi, giới và
bệnh đồng mắc khá tương đồng giữa 3 nhóm HbA1c lúc nhập viện; nhóm HbA1c cao hơn có tỷ lệ dùng insulin
trong thời gian nằm viện cao hơn rõ rệt ({{R-A0-054.full}} ở nhóm <7% so với {{R-A0-056.full}} ở nhóm
>9%), phù hợp với thực hành lâm sàng khi bác sĩ khởi trị insulin sau khi biết HbA1c cao — đây là lý do
biến này được xếp là trung gian nghi ngờ, không hiệu chỉnh trong mô hình chính (xem Chương 2, mục
2.3.3). Tỷ lệ tái nhập viện mọi nguyên nhân trong 1 năm chung của mẫu là {{R-A0-061.value}} (KTC 95%
{{R-A0-061.ci}}); tỷ lệ này là {{R-A0-062.value}} ở nhóm HbA1c <7% và {{R-A0-064.value}} ở nhóm >9%
(không kiểm định xu hướng theo nhóm trong kế hoạch phân tích thống kê), và các khoảng tin cậy của 3
nhóm chồng lấp rộng. Vì ledger tài liệu đã xác minh của đề tài
không có nghiên cứu dịch tễ học chung nào đo tỷ lệ tái nhập viện 1 năm ở ĐTĐ type 2 nói chung, tỷ lệ
quan sát được ở đây không thể đối chiếu trực tiếp với một con số tham chiếu đã công bố — đây là một
hạn chế của phần tổng quan tài liệu (Chương 1), không phải một phát hiện bất thường của mẫu.

## 4.2. Mối liên quan giữa HbA1c lúc nhập viện và tái nhập viện 1 năm (Mục tiêu 2 — kết quả chính)

Sau khi hiệu chỉnh tuổi, giới, thời gian mắc ĐTĐ và bệnh đồng mắc, tỷ số chênh (OR) của tái nhập viện
1 năm ở nhóm HbA1c 7–9% so với <7% là {{R-A1-003.full}}, và ở nhóm >9% so với <7% là
{{R-A1-004.full}}. Cả hai ước lượng đều cùng chiều với giả thuyết của đề tài (HbA1c cao hơn đi kèm OR > 1), nhưng KTC 95% của cả hai đều bao gồm giá trị 1 — mối liên quan giữa HbA1c lúc
nhập viện và tái nhập viện mọi nguyên nhân trong 1 năm **chưa được chứng minh có ý nghĩa thống kê**
ở cỡ mẫu hiện có; cần đọc đây là một ước lượng chưa chính xác (imprecise), không phải bằng chứng cho
rằng không có liên quan. Theo số đo tuyệt đối đã nêu ở mục 4.1, tỷ lệ tái nhập viện quan sát được là
{{R-A0-062.value}} ở nhóm <7% và {{R-A0-064.value}} ở nhóm >9% — một khác biệt tuyệt đối khiêm tốn,
cùng chiều với OR hiệu chỉnh nhưng cũng chưa đủ chính xác để khẳng định có ý nghĩa.

So với y văn đã thẩm định ở Chương 1, kết quả này cùng hướng nhưng không cùng độ chắc chắn với một
nghiên cứu đoàn hệ tại Trung Quốc ghi nhận HbA1c lúc nhập viện liên quan có ý nghĩa thống kê với tái
nhập viện trong 30 ngày (mỗi 1% HbA1c, aOR = 1,15 <!-- not-a-result: hu2026, tái nhập viện 30 ngày -->)
[@hu2026]. Sự khác biệt có thể giải thích bằng thiết kế: nghiên cứu của [@hu2026] theo dõi mốc ngắn
hơn nhiều (30 ngày so với 365 <!-- not-a-result: mốc theo dõi của đề tài --> ngày của đề tài này), nên liên quan gần thời điểm đo phơi nhiễm có thể rõ
hơn; đề tài này theo dõi dài hơn, trong đó nhiều yếu tố khác xảy ra sau thời điểm đo HbA1c (bệnh mới
phát sinh, thay đổi điều trị) có thể làm loãng mối liên quan quan sát được, và cỡ mẫu nhóm cực của đề
tài nhỏ hơn ngưỡng cần cho lực mẫu 80% đã tính trước (Chương 2, mục 2.3.2). Nghiên cứu duy nhất đã
thẩm định ở mốc 1 năm sử dụng mô hình học máy không tách riêng được hiệu ứng độc lập của HbA1c
[@li2026], nên không thể đối chiếu trực tiếp độ lớn hiệu ứng với kết quả của đề tài này.

## 4.3. Cơ chế có thể

HbA1c lúc nhập viện phản ánh mức kiểm soát đường huyết trung bình trong khoảng 3 tháng trước đó
(Chương 1, mục 1.3); về mặt sinh lý bệnh, kiểm soát đường huyết kém kéo dài **có thể** đi kèm nguy cơ
nhiễm trùng, biến chứng mạch máu và suy giảm miễn dịch cao hơn — những yếu tố này **có thể liên quan
với** khả năng phải nhập viện trở lại cao hơn, không phải một chuỗi nhân quả đã được chứng minh. Đây
là suy luận sinh lý bệnh chung, **chưa có tài liệu nào trong ledger
đã xác minh của đề tài** khảo sát trực tiếp cơ chế này ở quần thể ĐTĐ type 2 và mốc 1 năm
<!-- not-a-result: suy luận sinh lý bệnh chung, không có tài liệu sinh lý bệnh được xác minh trong
ledger của đề tài -->, nên cần được đọc như một giả thuyết hợp lý, không phải một cơ chế đã được
chứng minh cho chính nghiên cứu này.

## 4.4. Các kết quả phân tích phụ (A2–A5)

Khi dùng HbA1c liên tục (mỗi 1%) thay cho 3 nhóm, tỷ số chênh sau hiệu chỉnh cho mức tăng mỗi 1% là
{{R-A2-002.full}} — khoảng tin cậy hẹp quanh giá trị 1, không gợi ý một liên quan tuyến tính rõ giữa
HbA1c và tái nhập viện mọi nguyên nhân ở mức hiệu ứng mỗi 1%. Ngược lại, khi giới hạn kết cục vào tái
nhập viện có liên quan trực tiếp
đến ĐTĐ, OR hiệu chỉnh ở nhóm 7–9% là {{R-A3-001.full}} và ở nhóm >9% là {{R-A3-002.full}} — cả hai
đều có ý nghĩa thống kê và KTC 95% không chứa 1, mạnh hơn nhiều so với kết cục chính. Đây là một phát
hiện đáng chú ý nhưng phải được đọc đúng vị trí của nó: đây là kết cục phụ, mang tính khám phá, không
được hiệu chỉnh cho đa so sánh (Chương 2, mục 2.3.6) — kết quả này nên được xem như một giả thuyết cần
kiểm định lại ở một nghiên cứu độc lập, không phải một kết luận xác nhận của đề tài. Phân tích thời
gian đến lần tái nhập viện đầu tiên bằng hồi quy Cox cho kết quả cùng chiều và cùng độ lớn với kết quả
chính: HR hiệu chỉnh {{R-A4-005.full}} ở nhóm 7–9% và {{R-A4-006.full}} ở nhóm >9%, cả hai KTC 95%
cũng chứa 1 — nhất quán nội bộ với kết quả OR của Mục tiêu 2, không cung cấp thêm bằng chứng mới về
mối liên quan. Tử vong trong viện trong 1 năm chỉ được mô tả ({{R-A5-001.full}} chung,
{{R-A5-004.full}} ở nhóm >9%), không phân tích đa biến, vì biến này không ghi nhận được tử vong ngoài
viện — không nên dùng số liệu này để bàn về mối liên quan giữa HbA1c và tử vong.

## 4.5. Phân tích hậu kiểm theo nhóm tuổi (A6)

Hiệu ứng của nhóm HbA1c lên tái nhập viện 1 năm có vẻ lớn hơn một chút ở nhóm người bệnh dưới 65 tuổi
(OR nhóm >9% so với <7% là {{R-A6-002.full}}) so với nhóm từ 65 tuổi trở lên ({{R-A6-009.full}}), nhưng
kiểm định tương tác nhóm HbA1c × nhóm tuổi không có ý nghĩa thống kê (p tương tác = {{R-A6-015.value}}).
Đây là phân tích hậu kiểm, được tác giả yêu cầu bổ sung sau khi xem Chương 3 vì lo ngại hội đồng bảo vệ
có thể hỏi về người cao tuổi (Chương 2, mục 2.3.6) — kết quả chỉ trả lời rằng **chưa có bằng chứng** cho
thấy hiệu ứng HbA1c khác nhau thật sự theo tuổi ở cỡ mẫu hiện có (mỗi tầng tuổi chỉ còn khoảng một nửa
cỡ mẫu của phân tích chính, nên KTC rất rộng), không phải bằng chứng rằng hiệu ứng giống nhau giữa hai
nhóm tuổi.

## 4.6. Đối chiếu với các khoảng trống nghiên cứu đã nêu ở Chương 1

Đề tài góp phần lấp một phần khoảng trống thứ nhất đã nêu ở Chương 1 (chưa có nghiên cứu đoàn hệ
truyền thống báo cáo OR/HR của HbA1c lúc nhập viện cho tái nhập viện 1 năm ở ĐTĐ type 2 nói chung)
bằng cách cung cấp ước lượng trực tiếp ở đúng mốc này, dù ước lượng đó chưa đạt ý nghĩa thống kê. Đề
tài cũng là một trong số rất ít dữ liệu được thu thập trong bối cảnh Việt Nam cho câu hỏi này (khoảng
trống thứ hai), với lưu ý đã nêu ở Chương 1 rằng khoảng trống này chỉ được xác nhận trong phạm vi tài
liệu đã tìm trên PubMed. Khoảng trống thứ ba — liệu hướng liên quan giữa HbA1c và tái nhập viện có phụ
thuộc vào thời điểm đo hay không — **không được giải quyết trực tiếp** bởi đề tài này, vì đề tài chỉ
khảo sát HbA1c đo lúc nhập viện, không đối chiếu với HbA1c đo sau xuất viện trên cùng một mẫu; đây vẫn
là một câu hỏi mở cho nghiên cứu tiếp theo. Khoảng trống thứ tư (chưa có khuyến cáo cụ thể về ngưỡng
HbA1c để dự phòng tái nhập viện dài hạn) nằm ngoài phạm vi một luận văn thạc sĩ đơn trung tâm; kết quả
chưa đạt ý nghĩa thống kê của đề tài này **chưa đủ** để đề xuất một ngưỡng cụ thể cho mục đích đó.

## 4.7. Điểm mạnh của nghiên cứu

Đề tài sử dụng thiết kế đoàn hệ hồi cứu với lấy mẫu toàn bộ (census), tránh được sai lệch chọn mẫu
thuận tiện; thời điểm đo phơi nhiễm (24–48 giờ đầu nhập viện) được cố định trước thời điểm bắt đầu
theo dõi kết cục, nên nguy cơ sai lệch thời gian bất tử thấp (Chương 2, mục 2.3.5). Các biến nhiễu
được chọn trước khi thu thập dữ liệu, dựa trên y văn và kiến thức lâm sàng, không chọn theo kết quả
kiểm định đơn biến. Báo cáo kết quả theo đúng khung STROBE, với bảng đăng ký phân tích công khai trước
khi xem dữ liệu, giúp phân biệt rõ phân tích đã định trước (A0–A5) với phân tích hậu kiểm (A6) — tránh
nhầm lẫn kết quả thăm dò với kết quả xác nhận.

## 4.8. Hạn chế của nghiên cứu

- **Dữ liệu thiếu:** 27 <!-- derived: R-A0-001.n - R-A1-003.n --> người bệnh (2,5% <!-- derived: (R-A0-001.n - R-A1-003.n) / R-A0-001.n * 100 -->) thiếu thời gian mắc ĐTĐ, bị loại khỏi các mô hình hiệu chỉnh theo quy tắc phân tích ca đầy đủ đã định trước; tỷ lệ này thấp nên ít có khả năng làm sai lệch lớn kết quả, nhưng cỡ mẫu phân tích của các mô hình hiệu chỉnh vẫn nhỏ hơn một chút so với mẫu mô tả đầy đủ.
- **Lực mẫu (power):** cả OR chính (Mục tiêu 2) và HR phụ (A4) đều không đạt ý nghĩa thống kê, với KTC 95% rộng và chứa 1 — phù hợp với rủi ro về lực mẫu đã được tác giả xác nhận chấp nhận trước khi có dữ liệu (Chương 2, mục 2.3.2): cỡ mẫu yêu cầu cho so sánh 2 nhóm HbA1c cực gần với cỡ mẫu khả dụng, nên một hiệu ứng thật có độ lớn khiêm tốn có thể không được phát hiện ở mức ý nghĩa 0,05.
- **Nhiễu tồn dư/chưa đo được (residual/unmeasured confounding):** mô hình chính chỉ hiệu chỉnh 4 yếu
  tố định trước (tuổi, giới, thời gian mắc ĐTĐ, bệnh đồng mắc); các yếu tố khác có thể ảnh hưởng đồng
  thời đến HbA1c và nguy cơ tái nhập viện nhưng không có trong dữ liệu HIS/EMR (ví dụ mức độ tuân thủ
  điều trị, điều kiện kinh tế–xã hội, hỗ trợ chăm sóc sau xuất viện) không được hiệu chỉnh. Hướng ảnh
  hưởng khó suy đoán một chiều: người bệnh kiểm soát đường huyết kém (HbA1c cao) cũng có thể là người
  có điều kiện tiếp cận chăm sóc kém hơn — nếu vậy, nhiễu tồn dư này sẽ làm OR hiệu chỉnh cao hơn giá
  trị thật (phóng đại mối liên quan); nhưng cũng có thể người bệnh HbA1c cao được theo dõi sát hơn sau
  xuất viện, kéo OR hiệu chỉnh về gần 1 hơn giá trị thật. Vì không có dữ liệu đo các yếu tố này, không
  thể xác định chiều nào chiếm ưu thế ở mẫu này.
- **Sai lệch chọn mẫu tiềm ẩn từ tiêu chuẩn loại trừ thiếu HbA1c:** người bệnh không có kết quả HbA1c
  hợp lệ lúc nhập viện bị loại khỏi mẫu phân tích (Chương 2, mục 2.1.2). Nếu lý do không đo HbA1c là
  ngẫu nhiên (ví dụ do quy trình xét nghiệm), sai lệch này không đáng kể; nhưng nếu người bệnh nặng
  hơn, nhập viện cấp cứu không kịp làm đủ xét nghiệm thường quy, bị loại ra nhiều hơn, mẫu phân tích có
  thể nghiêng về phía người bệnh ổn định hơn ở lúc nhập viện — khi đó ước lượng mối liên quan ở mẫu
  này có thể thận trọng hơn (gần 1 hơn) so với toàn bộ quần thể đích. Không có dữ liệu để kiểm tra giả
  thuyết này với mẫu hiện có.
- **Thiết kế đơn trung tâm, hồi cứu trên dữ liệu hành chính:** HIS chỉ ghi nhận tái nhập viện tại chính
  Bệnh viện Mô phỏng; người bệnh tái nhập viện ở cơ sở khác bị tính nhầm là "không tái nhập viện". Nếu
  khả năng tái nhập viện ở nơi khác không khác nhau giữa 3 nhóm HbA1c, tỷ lệ tái nhập viện quan sát
  được ở cả 3 nhóm đều thấp hơn tỷ lệ thật theo cùng một mức, và OR có thể gần 1 hơn giá trị thật (ước
  lượng thận trọng); nhưng nếu người bệnh HbA1c cao (bệnh nặng hơn) có xu hướng được chuyển đến cơ sở
  chuyên khoa cao hơn khi tái nhập viện, OR quan sát được có thể thấp hơn giá trị thật theo chiều
  khác. Không thể phân biệt hai khả năng này với dữ liệu hiện có.
- **Tử vong chỉ ghi nhận được trong viện:** phân tích Cox chính coi tử vong ngoài viện (không xác định
  được) như censored tại thời điểm cuối theo dõi — giả định censoring không mang thông tin có thể
  không đúng nếu tử vong ngoài viện có liên quan đến HbA1c.
- **EPV của phân tích A3 thấp hơn các mô hình khác** (do ít sự kiện tái nhập viện liên quan ĐTĐ) — vẫn
  trên ngưỡng mặc định nhưng các OR của A3 cần diễn giải thận trọng hơn kết quả chính.
- **Các kết quả phụ (A2–A5) và phân tích hậu kiểm theo tuổi (A6) mang tính khám phá/tạo giả thuyết,
  không hiệu chỉnh đa so sánh** — không được dùng để kết luận xác nhận.
- **Dữ liệu mô phỏng:** số liệu dùng trong luận văn này là dữ liệu mô phỏng cho mục đích minh họa quy
  trình, không phải số liệu bệnh nhân thật tại Bệnh viện Mô phỏng; kết quả không có giá trị áp dụng
  ngoài phạm vi minh họa này.
- **Khả năng ngoại suy:** kết quả chỉ áp dụng cho người bệnh ĐTĐ type 2 xuất viện tại một khoa của một
  bệnh viện tuyến tỉnh trong giai đoạn 2021–2022; không ngoại suy sang các cơ sở khác hoặc quần thể
  khác mà không có dữ liệu riêng kiểm chứng.

## 4.9. Ý nghĩa

Trong phạm vi quần thể và cỡ mẫu đã khảo sát, chưa có đủ bằng chứng để khẳng định HbA1c lúc nhập viện
có liên quan với tái nhập viện mọi nguyên nhân trong 1 năm sau xuất viện; vì vậy kết quả của đề tài
chưa đủ cơ sở để đề xuất dùng HbA1c lúc nhập viện như một yếu tố phân loại nguy cơ tái nhập viện 1 năm
trong thực hành tại Khoa Nội tiết, Bệnh viện Mô phỏng. Phát hiện về tái nhập viện liên quan ĐTĐ (A3) và
kết quả hậu kiểm theo tuổi (A6) gợi ý hai hướng cho nghiên cứu tiếp theo, được trình bày cụ thể ở phần
Kiến nghị.
