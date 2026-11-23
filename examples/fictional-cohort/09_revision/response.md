# Thư trả lời phản biện — manuscript

Chúng tôi xin cảm ơn Ban biên tập và hai Phản biện đã dành thời gian đọc và góp ý cho bản thảo. Dưới
đây là trả lời cho từng góp ý; các thay đổi trong bản thảo được trích dẫn nguyên văn và vị trí file.

## E1

> Please keep the main text within the journal's word limit when you revise the manuscript.

Văn bản chính (Đặt vấn đề–Kết luận) trước khi sửa dài hơn giới hạn từ của tạp chí
(`project.yaml` → `target.text_words`), theo cách đếm thô (gồm cả bảng). Theo cách đếm từ chính thức
của dự án (`lint_prose.word_count`, loại bảng, chú thích hình, tiêu đề, nhóm trích dẫn — cách đếm phù
hợp với quy ước đa số tạp chí, không tính bảng/hình vào giới hạn từ chính văn), văn bản chính đã sửa
nằm trong giới hạn <!-- not-a-result: số từ, không phải kết quả nghiên cứu -->. Chúng tôi đã rút ngắn
hành văn ở Đặt vấn đề, Đối tượng và phương pháp, Kết quả và Bàn luận — không bớt số liệu hay kết quả
nào — đồng thời thêm nội dung trả lời R1.1 và R2.1 bên dưới.

[[CHANGE: 06_writing/manuscript/05-discussion.md | "So với y văn, kết quả này cùng hướng nhưng kém chắc chắn hơn một nghiên cứu đoàn hệ tại Trung Quốc"]]

## R1.1

> The exclusion criteria are unclear. Please state exactly which patients were excluded and why.

Chúng tôi đã viết lại tiêu chuẩn loại thành danh sách rõ từng lý do (4 tiêu chuẩn, áp dụng tuần tự),
thay cho câu văn liền mạch trước đây. Dữ liệu nguồn của nghiên cứu không ghi nhận số người bệnh bị loại
theo từng lý do riêng (chỉ có tổng số đưa vào mẫu phân tích) — đây là hạn chế đã có từ vòng nộp trước
(tác giả đã quyết định không làm thêm phân tích để khôi phục số liệu sàng lọc, xem
`out/author-decisions.md` mục 1); chúng tôi nêu rõ điều này ngay trong phần tiêu chuẩn loại và nhắc lại
ở Hạn chế, để người đọc không hiểu nhầm là số liệu bị thiếu sót trong lúc viết.

[[CHANGE: 06_writing/manuscript/03-methods.md | "Tiêu chuẩn loại, áp dụng tuần tự: (1) tử vong trong lần nhập viện chỉ số — không có thời gian theo dõi sau xuất viện; (2) ĐTĐ thai kỳ, type 1 hoặc thứ phát — cơ chế bệnh khác ĐTĐ type 2; (3) không có HbA1c đo trong 24–48 giờ đầu nhập viện — thiếu giá trị phơi nhiễm chính; (4) xuất viện nhiều lần trong giai đoạn trên — chỉ lần xuất viện đầu tiên được lấy làm nhập viện chỉ số."]]

[[CHANGE: 06_writing/manuscript/05-discussion.md | "số người bị loại theo từng tiêu chuẩn riêng không có trong dữ liệu nguồn nên không ước lượng được quy mô sai lệch này"]]

## R1.2

> Please add a subgroup analysis by sex.

Không thay đổi bản thảo cho mục này. Giới đã được đưa vào mô hình chính làm yếu tố hiệu chỉnh (định trước
theo `03_protocol/sap.md` §10), nhưng một phân tích phân nhóm/tương tác theo giới không được đăng ký
trước trong SAP — SAP §10 yêu cầu mọi phân nhóm mới phải khai báo trước khi xem kết cục và kiểm định
bằng số hạng tương tác, không suy luận từ các mô hình riêng theo từng nhóm. Tác giả quyết định không
bổ sung phân tích này (2026-11-23), với hai lý do: (1) không định trước trong SAP; (2) chia mẫu theo
giới sẽ tạo các nhóm nhỏ hơn nữa trong một mẫu đã biết trước là thiếu lực mẫu cho phân tích chính
(xem Hạn chế), nên một phân tích tương tác theo giới khó cho ước lượng đủ tin cậy. Chúng tôi xem đây
là một hướng hợp lý cho nghiên cứu xác nhận tiếp theo, đa trung tâm, cỡ mẫu lớn hơn.

## R2.1

> Please discuss residual confounding more explicitly in the Discussion.

Chúng tôi đã viết lại đoạn nhiễu tồn dư trong Hạn chế, nêu cụ thể ba nhóm yếu tố không đo được trong dữ
liệu hồi cứu này (tuân thủ điều trị/tái khám trước đó, kinh tế–xã hội và khả năng tiếp cận chăm sóc sau
xuất viện, mức độ nặng của bệnh đồng mắc), kèm suy luận về hướng ảnh hưởng khi có thể, và nêu rõ khoảng
tin cậy rộng quan sát được có thể một phần phản ánh nhiễu tồn dư, không chỉ cỡ mẫu nhỏ.

[[CHANGE: 06_writing/manuscript/05-discussion.md | "Một số yếu tố khác có thể ảnh hưởng đồng thời đến HbA1c lúc nhập viện và nguy cơ tái nhập viện nhưng không có trong dữ liệu hồi cứu này: mức độ tuân thủ điều trị và tái khám trước đó (hướng nhiễu khó đoán); tình trạng kinh tế–xã hội và khả năng tiếp cận chăm sóc sau xuất viện (người khó khăn hơn có thể vừa kiểm soát đường huyết kém hơn vừa ít được theo dõi sau ra viện, nên có thể đẩy OR quan sát được lên cao hơn giá trị thật); và mức độ nặng của bệnh đồng mắc (chỉ ghi có/không, không có thang điểm, nên phần nhiễu do bệnh đồng mắc có thể chưa được hiệu chỉnh hết)."]]

## R2.2

> Please give the confidence interval of the adjusted odds ratio in the abstract.

Không thay đổi vì tóm tắt đã có khoảng tin cậy 95% của cả hai OR hiệu chỉnh, ở câu: "Sau hiệu chỉnh, OR
của tái nhập viện là {{R-A1-003.value}} (KTC 95%: {{R-A1-003.ci}}) ở nhóm HbA1c 7–9% và
{{R-A1-004.value}} (KTC 95%: {{R-A1-004.ci}}) ở nhóm >9%" (`06_writing/manuscript/01-abstract.md`, mục
Kết quả). Chúng tôi giữ nguyên câu này và chỉ nêu rõ vị trí trong thư trả lời.
