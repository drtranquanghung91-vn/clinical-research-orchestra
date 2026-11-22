orchestra-role: methods

# CHƯƠNG 2. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU

**Dữ liệu mô phỏng.** Toàn bộ số liệu dùng để minh họa quy trình phân tích trong chương này và
Chương 3 là dữ liệu MÔ PHỎNG, sinh bởi script mô phỏng cohort của dự án ví dụ
(`tools/simulate_cohort.py`); không phải số liệu bệnh nhân thật, không có giá trị lâm sàng.

## 2.1. Đối tượng nghiên cứu

### 2.1.1. Tiêu chuẩn lựa chọn

Người bệnh được đưa vào nghiên cứu nếu thỏa cả 4 tiêu chuẩn sau:
1. Chẩn đoán đái tháo đường (ĐTĐ) type 2 theo mã ICD-10 ghi trong hồ sơ ra viện (khối mã E11 — "Đái
   tháo đường không phụ thuộc insulin").
2. ≥ 18 tuổi tại thời điểm nhập viện.
3. Xuất viện từ Khoa Nội tiết, Bệnh viện Mô phỏng, trong khoảng 01/01/2021–31/12/2022 (để đảm bảo đủ 365 <!-- not-a-result: mốc theo dõi của đề tài, 01_question/question.md --> ngày theo dõi trong dữ liệu hệ thống thông tin bệnh viện, HIS, 2021–2023 cho mọi người bệnh).
4. Có kết quả HbA1c được đo trong vòng 24–48 giờ đầu của lần nhập viện này, ghi nhận trong hồ sơ bệnh
   án điện tử (EMR).

### 2.1.2. Tiêu chuẩn loại trừ

Người bệnh đã thỏa tiêu chuẩn lựa chọn nhưng được loại khỏi mẫu phân tích nếu có một trong các đặc
điểm sau:
1. Tử vong trong chính lần nhập viện chỉ số (trước khi xuất viện) — không có cơ hội "tái nhập viện
   sau xuất viện" như định nghĩa của kết cục chính.
2. Chẩn đoán ĐTĐ thai kỳ, ĐTĐ type 1, hoặc ĐTĐ thứ phát, được ghi mã ICD-10 riêng biệt khỏi khối E11.
3. Hồ sơ không có giá trị HbA1c lúc nhập viện hợp lệ.
4. Nhiều lần xuất viện của cùng một người bệnh trong giai đoạn 01/2021–12/2022: chỉ lần xuất viện đầu
   tiên trong giai đoạn này được lấy làm "nhập viện chỉ số" (index admission); các lần nhập viện sau
   trong cùng giai đoạn chỉ được dùng để xác định kết cục tái nhập viện, không tạo thêm đơn vị phân
   tích độc lập.

Không áp dụng tiêu chuẩn dừng/rút lui vì đây là nghiên cứu hồi cứu trên dữ liệu đã có, không có theo
dõi tiến cứu người bệnh.

## 2.2. Thời gian và địa điểm nghiên cứu

- Địa điểm: Khoa Nội tiết, Bệnh viện Mô phỏng.
- Giai đoạn chọn mẫu (nhập viện chỉ số): người bệnh xuất viện từ 01/01/2021 đến 31/12/2022.
- Giai đoạn theo dõi kết cục: 365 <!-- not-a-result: mốc theo dõi của đề tài, 01_question/question.md --> ngày kể từ ngày xuất viện của mỗi người bệnh, qua dữ liệu HIS đến 31/12/2023.
- Thời điểm trích xuất dữ liệu: sau khi đề cương và kế hoạch phân tích thống kê (SAP) được phê
  duyệt (gate G2).

## 2.3. Phương pháp nghiên cứu

### 2.3.1. Thiết kế nghiên cứu

Nghiên cứu đoàn hệ hồi cứu (retrospective cohort study), đơn trung tâm, không can thiệp, không phân
nhóm ngẫu nhiên. Báo cáo theo STROBE (bản 2007, đã được xác nhận còn là bản hiện hành ở bước thẩm
định y văn của đề tài).

### 2.3.2. Cỡ mẫu và phương pháp chọn mẫu

Cỡ mẫu được tính trước khi trích xuất dữ liệu cho kết cục chính là tái nhập viện mọi nguyên nhân
trong 1 năm, so sánh 3 nhóm HbA1c lúc nhập viện (< 7% / 7–9% / > 9%, nhóm < 7% tham chiếu). Vì chưa có
nghiên cứu nào đo trực tiếp tỷ lệ tái nhập viện 1 năm hoặc hiệu ứng của HbA1c ở đúng mốc 1 năm cho ĐTĐ
type 2 nói chung, tỷ lệ tái nhập viện ở nhóm tham chiếu được giả định là 20% <!-- not-a-result: sample-size.md §2, giả định, không có nguồn trực tiếp --> và tỷ số chênh (OR) kỳ vọng giữa nhóm HbA1c > 9% và nhóm tham chiếu được giả định là 1,5 <!-- not-a-result: sample-size.md §2, giả định DELTA2 -->.

Với mức ý nghĩa α = 0,05 (hai phía) và lực mẫu (power) 80%, theo kiểm định tỷ lệ đơn giản cần 535 <!-- not-a-result: sample-size.md §3b --> người bệnh mỗi nhóm cực, tức 1.070 <!-- not-a-result: sample-size.md §3b --> người cho 2 nhóm cực.

Theo quy tắc số sự kiện/biến (EPV ≥ 10) cho mô hình hồi quy đa biến 6 biến, cần tối thiểu 300 <!-- not-a-result: sample-size.md §3a --> người bệnh toàn mẫu — thấp hơn mức 1.070 <!-- not-a-result: sample-size.md §3c --> nêu trên.

Giá trị lớn hơn trong hai cách tính, thận trọng hơn, được chọn làm cỡ mẫu cho đề tài này, tính bằng `samplesize.py` (two-proportions; regression-EPV). Cỡ mẫu khả dụng ước tính trước khi áp tiêu chuẩn loại trừ là 1.200 <!-- not-a-result: sample-size.md §2, số ước tính, không phải số đếm chính xác --> người bệnh, gần với mức cần cho so sánh 2 nhóm cực nêu trên, nên đề tài có thể chỉ đủ hoặc thiếu lực mẫu cho riêng so sánh này, tùy phân bố thật của 3 nhóm HbA1c trong mẫu — rủi ro này đã được tác giả xác nhận chấp nhận khi mở gate G2 (xem Chương 4, mục Hạn chế). Số người bệnh thực tế được đưa vào mẫu phân tích, sau khi áp dụng các tiêu chuẩn ở mục 2.1, là {{R-A0-001.n}} người bệnh.

Phương pháp chọn mẫu: lấy mẫu toàn bộ (census) — toàn bộ người bệnh thỏa tiêu chuẩn lựa chọn
trong giai đoạn xuất viện 01/01/2021–31/12/2022, không chọn mẫu xác suất hay thuận tiện một phần.

### 2.3.3. Biến số nghiên cứu và định nghĩa biến

Phơi nhiễm chính là HbA1c đo trong 24–48 giờ đầu nhập viện, phân tích chính theo 3 nhóm < 7% /
7–9% / > 9% (nhóm < 7% tham chiếu); phân tích phụ dùng HbA1c liên tục (mỗi 1%).

Kết cục chính là tái nhập viện do mọi nguyên nhân trong vòng 365 <!-- not-a-result: mốc theo dõi của đề tài, 01_question/question.md --> ngày kể từ ngày xuất viện của lần nhập viện chỉ số (biến nhị giá, nguồn HIS).

**Kết cục phụ:** (a) tái nhập viện có chẩn đoán chính hoặc kèm theo thuộc khối ICD-10 liên quan ĐTĐ hoặc biến chứng đường huyết, trong 1 năm; (b) thời gian từ ngày xuất viện đến ngày nhập viện của lần tái nhập viện đầu tiên (censored tại 365 <!-- not-a-result: mốc theo dõi của đề tài --> ngày nếu không tái nhập viện); (c) tử vong trong 1 năm — **HIS của Bệnh viện Mô phỏng chỉ ghi nhận được tử vong xảy ra trong viện** (ví dụ trong một lần tái nhập viện), không xác định được tử vong ngoài viện; biến này chỉ phản ánh "tử vong trong viện ghi nhận được trong 365 <!-- not-a-result: mốc theo dõi của đề tài --> ngày", không phải tử vong do mọi nguyên nhân đầy đủ, và chỉ được báo cáo mô tả (mục 2.3.6).

**Biến nhiễu đưa vào mô hình hiệu chỉnh chính (Mục tiêu 2):** tuổi, giới, thời gian mắc ĐTĐ, có/không
≥ 1 bệnh đồng mắc chính (tăng huyết áp, bệnh thận mạn, bệnh tim mạch — ghi nhận trước hoặc tại thời
điểm nhập viện chỉ số). Các biến nhiễu này được chọn trước khi thu thập dữ liệu, dựa trên y văn đã
thẩm định ở các mốc thời gian khác kết hợp kiến thức lâm sàng, không chọn theo kết quả kiểm định đơn
biến (p < 0,05).

**Biến không đưa vào mô hình hiệu chỉnh chính (trung gian/vai trò nhân quả chưa rõ):** sử dụng
insulin trong thời gian nằm viện và thời gian nằm viện — cả hai được đo sau hoặc đồng thời với thời
điểm đo HbA1c nên có thể nằm trên con đường nhân quả giữa HbA1c và kết cục; chỉ được dùng như biến
mô tả.

**Biến thăm dò có điều kiện (dự kiến ở đề cương):** tỷ số bạch cầu trung tính/lympho (NLR), chỉ số
viêm tổng hợp (SII/SIRI) và nguy cơ dinh dưỡng lúc nhập viện. Ba biến này **không có trong bộ dữ liệu
trích xuất của dự án mô phỏng này** (script mô phỏng không sinh ra các biến này) nên không được đưa
vào bất kỳ phân tích nào trong luận văn; quy tắc ngưỡng 20% dữ liệu thiếu dự kiến ở đề cương cho các
biến này không áp dụng được vì biến không tồn tại trong nguồn dữ liệu, không phải vì thiếu dữ liệu
vượt ngưỡng.

Bảng biến số đầy đủ (định nghĩa, loại biến, nguồn trong EMR/HIS, vai trò trong phân tích) được trình
bày tại Phụ lục 2.

### 2.3.4. Công cụ và quy trình thu thập số liệu

Dữ liệu được trích xuất từ hồ sơ bệnh án điện tử (EMR) và hệ thống thông tin bệnh viện (HIS) của Bệnh
viện Mô phỏng, giai đoạn 2021–2023 — không có nguồn dữ liệu nào ngoài EMR/HIS của chính bệnh viện.
Công cụ trích xuất là biểu mẫu trích xuất dữ liệu xây dựng theo đúng bảng biến số (Phụ lục 2) trước
khi trích xuất. Dữ liệu được mã hóa bằng số thứ tự nghiên cứu, loại bỏ họ tên và các định danh cá nhân
trước khi đưa vào tệp phân tích.

### 2.3.5. Sai số và biện pháp khống chế sai số

| Loại sai số | Biểu hiện cụ thể trong đề tài | Biện pháp khống chế |
|---|---|---|
| Dữ liệu thiếu/không đồng nhất | HbA1c, biến nhiễu có thể ghi thiếu hoặc không nhất quán giữa các bệnh án | Tiêu chuẩn trích xuất và biểu mẫu chuẩn hóa; loại người thiếu HbA1c hợp lệ; báo cáo rõ số lượng/% thiếu cho từng biến |
| Nhiễu do chỉ định (confounding by indication) | Người có bệnh nặng hơn lúc nhập viện có thể vừa có HbA1c cao hơn vừa có nguy cơ tái nhập viện cao hơn vì độ nặng, không phải vì HbA1c | Hồi quy đa biến hiệu chỉnh các yếu tố nhiễu định trước (mục 2.3.3); không chọn biến theo kết quả kiểm định đơn biến |
| Sai lệch thời gian bất tử (immortal time bias) | Rủi ro thấp: phơi nhiễm (HbA1c) được đo và cố định trong 24–48 giờ đầu nhập viện, trước thời điểm bắt đầu theo dõi kết cục | Giữ nguyên quy ước đo phơi nhiễm trong 24–48 giờ đầu, không đổi theo diễn biến sau đó |
| **Thiếu thông tin tái nhập viện ngoài hệ thống** | HIS chỉ ghi nhận tái nhập viện tại chính Bệnh viện Mô phỏng; người bệnh tái nhập viện ở cơ sở khác sẽ bị tính nhầm là "không tái nhập viện" | Không khắc phục được ở thiết kế này — nêu rõ ở Chương 4, mục Hạn chế; hướng và độ lớn sai lệch chưa xác định được |
| Sai lệch phát hiện (detection bias) | Thấp, vì kết cục lấy từ dữ liệu hành chính khách quan | Mốc theo dõi 365 <!-- not-a-result: mốc theo dõi của đề tài --> ngày cố định, giống nhau cho mọi nhóm HbA1c |

Thiết kế đoàn hệ hồi cứu đáp ứng tiêu chí thời gian trước–sau (temporality) vì phơi nhiễm được đo
trước kết cục, nhưng không đủ để kết luận nhân quả một mình. Ngôn ngữ dùng trong toàn bộ luận văn là
"có liên quan với", không dùng "là nguyên nhân của" hay "yếu tố nguy cơ nhân quả".

### 2.3.6. Xử lý và phân tích số liệu

Dữ liệu được quản lý và phân tích bằng Python (pandas, statsmodels)
<!-- not-a-result: 05_analysis/output/results.json → engine --> . Mục tiêu 1 được trả lời bằng thống
kê mô tả: trung bình ± độ lệch chuẩn hoặc trung vị [khoảng liên phân vị] cho biến liên tục tùy phân
bố; tần số và tỷ lệ % cho biến phân loại; tỷ lệ tái nhập viện 1 năm (chung và theo nhóm HbA1c) kèm KTC 95% Wilson (KTC: khoảng tin cậy). Mục tiêu 2 được trả lời bằng hồi quy logistic đa biến cho kết cục
nhị giá "tái nhập viện mọi nguyên nhân trong 1 năm", biến độc lập chính là nhóm HbA1c (nhóm < 7% tham
chiếu), hiệu chỉnh các biến nhiễu ở mục 2.3.3; báo cáo tỷ số chênh (OR) thô và OR đã hiệu chỉnh kèm KTC 95%. Các phân tích phụ gồm: HbA1c liên tục (mỗi 1%) thay cho 3 nhóm; tái nhập viện liên quan ĐTĐ; thời
gian đến lần tái nhập viện đầu tiên bằng hồi quy Cox (kiểm tra giả định nguy cơ tỷ lệ bằng phần dư
Schoenfeld); tử vong trong viện trong 1 năm (chỉ mô tả). Các phân tích phụ mang tính khám phá, không
hiệu chỉnh cho đa so sánh; chỉ kết cục chính (Mục tiêu 2, 3 nhóm HbA1c) được kiểm định xác nhận ở mức
ý nghĩa α = 0,05 hai phía. Mô hình hồi quy logistic được kiểm tra số sự kiện/biến (EPV) thực tế, đa
cộng tuyến (hệ số phóng đại phương sai, VIF) và tuyến tính logit cho các biến liên tục; quy tắc đổi
sang kiểm định thay thế (χ²/Fisher exact, không hiệu chỉnh) khi một nhóm HbA1c có < 5 sự kiện tái
nhập viện đã được định trước nhưng không cần áp dụng vì mọi nhóm HbA1c đều có ≥ 5 sự kiện tái nhập
viện.

**Dữ liệu thiếu:** biến thời gian mắc ĐTĐ thiếu ở 27 <!-- derived: R-A0-001.n - R-A1-003.n -->
người bệnh (2,5% <!-- derived: (R-A0-001.n - R-A1-003.n) / R-A0-001.n * 100 -->). Vì tỷ lệ này ≤ 5%
trên một biến nhiễu trong mô hình hiệu chỉnh
chính, phân tích ca đầy đủ (complete-case) được áp dụng cho các mô hình hiệu chỉnh (không dùng
imputation), theo quy tắc đã định trước trong kế hoạch phân tích thống kê. Không biến nào khác có dữ
liệu thiếu.

**Thay đổi so với đề cương/kế hoạch phân tích thống kê (SAP):**
- Trước khi có dữ liệu, SAP đã bỏ phân tích độ nhạy Fine-Gray (tử vong là nguy cơ cạnh tranh) được dự
  kiến ban đầu ở đề cương: trong thiết kế dữ liệu của đề tài này, tử vong trong viện chỉ ghi nhận được
  khi xảy ra trong một lần tái nhập viện, nghĩa là biến cố này xảy ra sau và không ngăn cản được việc
  tái nhập viện — do đó không phải một nguy cơ cạnh tranh thật đối với kết cục "thời gian đến lần tái
  nhập viện đầu tiên". Phân tích thời gian-đến-sự kiện chính vẫn dùng hồi quy Cox thông thường, coi
  người tử vong ngoài viện (không xác định được qua HIS) như censored tại thời điểm cuối theo dõi —
  một giả định có thể không hoàn toàn đúng nếu tử vong ngoài viện có liên quan đến HbA1c (nêu ở
  Chương 4, mục Hạn chế).
- Sau khi xem xét Chương 3 (kết quả đã khoá), tác giả yêu cầu bổ sung một phân tích hậu kiểm
  (post-hoc), không có trong bảng đăng ký phân tích của SAP: kiểm tra hiệu ứng của nhóm HbA1c lên tái
  nhập viện 1 năm có khác nhau theo nhóm tuổi (< 65 so với ≥ 65 tuổi) hay không, vì hội đồng bảo vệ có
  thể hỏi về người bệnh cao tuổi và chưa có kết quả nào theo tuổi được xem xét trước đó. Phân tích này
  dùng cùng biến hiệu chỉnh như Mục tiêu 2 trong từng nhóm tuổi, cộng kiểm định tương tác (nhóm HbA1c
  × nhóm tuổi) bằng kiểm định tỷ số hợp lý (likelihood-ratio test). Đây là phân tích khám phá, được
  báo cáo riêng ở Chương 3 (mục 3.4) và Chương 4, không được xem là một kết luận xác nhận.

**Phân tích độ nhạy:** ngoài việc bỏ Fine-Gray (xem trên) và phân tích ca đầy đủ cho biến nhiễu thiếu
dữ liệu (thời gian mắc ĐTĐ, 2,5% thiếu — dưới ngưỡng 5% nên không cần imputation hay phân tích độ
nhạy so sánh complete-case với imputation theo kế hoạch phân tích thống kê), không có phân tích độ
nhạy bổ sung nào khác được thực hiện trên mô hình hiệu chỉnh chính: với tỷ lệ dữ liệu thiếu thấp
(2,5%, trên một biến duy nhất) và không biến nhiễu nào khác bị thiếu dữ liệu, kế hoạch phân tích
thống kê không yêu cầu thêm phân tích độ nhạy nào cho mô hình chính của Mục tiêu 2.

**Tài trợ:** Nghiên cứu không nhận tài trợ từ bất kỳ tổ chức nào; đây là dự án minh hoạ với dữ liệu mô phỏng.

## 2.4. Đạo đức nghiên cứu

Đây là nghiên cứu hồi cứu trên dữ liệu đã có sẵn (hồ sơ bệnh án điện tử, HIS), không can thiệp, không
ảnh hưởng đến quá trình chăm sóc người bệnh. Đề cương được nộp cho Hội đồng Đạo đức trong nghiên cứu y
sinh học của Bệnh viện Mô phỏng; tác giả xin hội đồng miễn chấp thuận tham gia cá nhân (waiver of
informed consent) với lý do: (1) nghiên cứu hồi cứu, không can thiệp, không ảnh hưởng đến chăm sóc
người bệnh; (2) dữ liệu được khử định danh trước khi phân tích; (3) không khả thi về mặt thực tế để
liên hệ lại toàn bộ người bệnh đã xuất viện. Quyết định cuối cùng thuộc về hội đồng đạo đức của cơ sở.
Số quyết định/chứng nhận chấp thuận của Hội đồng Đạo đức: Không có số quyết định: đây là dự án minh
hoạ dùng dữ liệu mô phỏng, chưa nộp Hội đồng Đạo đức; một nghiên cứu thật phải được Hội đồng Đạo đức
của Bệnh viện chấp thuận trước khi trích xuất dữ liệu. Dữ liệu
được mã hóa bằng số thứ tự nghiên cứu, loại bỏ họ tên, số căn cước công dân, số điện thoại và địa chỉ
cụ thể trước khi đưa vào tệp phân tích; tệp dữ liệu có mật khẩu, chỉ nghiên cứu viên chính truy cập.
Nghiên cứu tuân thủ quy định của Bộ Y tế về đạo đức trong nghiên cứu y sinh học: các quy định hiện
hành của Bộ Y tế về đạo đức trong nghiên cứu y sinh học (tác giả sẽ ghi số hiệu văn bản khi nộp hồ sơ
thật).
