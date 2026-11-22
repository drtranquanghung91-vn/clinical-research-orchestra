# PHỤ LỤC

## Phụ lục 1. Bảng kiểm STROBE

In bằng `guideline_checklist.py . --deliverable thesis --table` từ `reviews/guideline-checklist.json`
(cập nhật lần cuối sau khi bổ sung Tóm tắt, 2026-11-22; xem file đó để biết số dòng chính xác của mỗi
mục — bảng dưới đây chỉ ghi tên tệp, không ghi số dòng, để tránh các số dòng bị đọc nhầm thành số
liệu kết quả). Ba mục 13a–13c ghi "một phần": sơ đồ số lượng đối tượng (Biểu đồ 3.1) chỉ là bản rút
gọn, không phải sơ đồ luồng STROBE đầy đủ, vì dữ liệu mô phỏng của đề tài này không ghi nhận số liệu
sàng lọc/loại trừ ban đầu theo từng tiêu chuẩn — quyết định của tác giả, xem `decisions.md`. Mục 6b
ghi "không áp dụng" vì đây là đoàn hệ lấy mẫu toàn bộ, không ghép cặp.

| Mục | Phần | Nội dung (diễn giải) | Trạng thái | Tệp |
|---|---|---|---|---|
| 1a | Title and abstract | Design named with a common term in title or abstract. | có | `00-tom-tat.md` |
| 1b | Title and abstract | Abstract gives a balanced summary of methods and findings. | có | `00-tom-tat.md` |
| 2 | Introduction | Why the study was needed: background and rationale. | có | `00-dat-van-de.md` |
| 3 | Introduction | Specific aims and any hypotheses fixed in advance. | có | `00-dat-van-de.md` |
| 4 | Methods | Design stated early in the methods. | có | `ch2-methods.md` |
| 5 | Methods | Where and when: site, recruitment period, exposure, follow-up, data collection. | có | `ch2-methods.md` |
| 6a | Methods | Who was eligible, how selected, and how followed up. | có | `ch2-methods.md` |
| 6b | Methods | Matching, sampling or follow-up details, as the design requires. | không áp dụng | Đoàn hệ không ghép cặp, lấy mẫu toàn bộ (`ch2-methods.md`, mục 2.3.2) — không có tiêu chí ghép cặp để báo cáo. |
| 7 | Methods | Operational definitions of outcome, exposure, confounders, effect modifiers and diagnoses. | có | `ch2-methods.md` |
| 8 | Methods | Data source and measurement for each variable; comparability across groups. | có | `ch2-methods.md` |
| 9 | Methods | Steps taken against likely sources of bias. | có | `ch2-methods.md` |
| 10 | Methods | Justification of the sample size. | có | `ch2-methods.md` |
| 11 | Methods | Treatment of quantitative variables, and reasons for any groupings. | có | `ch2-methods.md` |
| 12a | Methods | Every statistical method, including confounding control. | có | `ch2-methods.md` |
| 12b | Methods | Methods for subgroup and interaction analyses. | có | `ch2-methods.md` |
| 12c | Methods | Approach to missing data. | có | `ch2-methods.md` |
| 12d | Methods | How loss to follow-up or non-response was handled, per design. | có | `ch2-methods.md` |
| 12e | Methods | Any sensitivity analyses. | có | `ch2-methods.md` |
| 13a | Results | Participant numbers at each stage, from eligible to analysed. | một phần | `ch3-results.md` |
| 13b | Results | Why participants dropped out at each stage. | một phần | `ch3-results.md` |
| 13c | Results | A participant flow diagram, if useful. | một phần | `ch3-results.md` |
| 14a | Results | Participant characteristics, exposures and potential confounders. | có | `ch3-results.md` |
| 14b | Results | Count of missing values per variable of interest. | có | `ch3-results.md` |
| 14c | Results | Follow-up duration or time at risk, where the design has it. | có | `ch3-results.md` |
| 15 | Results | Outcome counts or summary measures, suited to the design. | có | `ch3-results.md` |
| 16a | Results | Crude and adjusted estimates with CIs; which confounders and why. | có | `ch3-results.md` |
| 16b | Results | Cut-points used when continuous variables were grouped. | có | `ch1-literature-review.md` |
| 16c | Results | Absolute risk translation of relative estimates, where meaningful. | có | `ch4-discussion.md` |
| 17 <!-- not-a-result: số thứ tự mục STROBE --> | Results | Results of other analyses: subgroups, interactions, sensitivity. | có | `ch3-results.md` |
| 18 | Discussion | Main findings related back to the objectives. | có | `ch4-discussion.md` |
| 19 | Discussion | Limitations: bias and imprecision, with likely direction and size. | có | `ch4-discussion.md` |
| 20 | Discussion | Cautious overall reading given limitations, multiplicity and outside evidence. | có | `ch4-discussion.md` |
| 21 | Discussion | Whether results apply beyond the study population (external validity). | có | `ch4-discussion.md` |
| 22 | Other information | Who funded the study and what the funder did. | có | `ch2-methods.md` |

## Phụ lục 2. Bảng biến số nghiên cứu (biểu mẫu trích xuất dữ liệu)

Nguồn dữ liệu cho mọi biến: hồ sơ bệnh án điện tử (EMR) và hệ thống thông tin bệnh viện (HIS) của
Bệnh viện Mô phỏng — không có nguồn dữ liệu ngoài hai hệ thống này. Bảng này là cơ sở của biểu mẫu
trích xuất dữ liệu dùng trong nghiên cứu (dẫn từ `03_protocol/variables.md`); đây là trích xuất từ
dữ liệu điện tử đã có sẵn, không phải một bộ công cụ thu thập trực tiếp trên người bệnh (CRF giấy).

**Biến phơi nhiễm**

| Biến | Định nghĩa / cách đo | Loại | Giá trị / đơn vị | Vai trò |
|---|---|---|---|---|
| HbA1c lúc nhập viện (phân nhóm) | Giá trị HbA1c đo trong 24–48 giờ đầu nhập viện, phân 3 nhóm | Thứ tự/phân loại | < 7% / 7–9% / > 9% (nhóm < 7% tham chiếu) | Phơi nhiễm chính |
| HbA1c lúc nhập viện (liên tục) | Giá trị HbA1c đo trong 24–48 giờ đầu nhập viện | Liên tục | % (NGSP) | Phơi nhiễm (phân tích phụ) |

**Biến kết cục**

| Biến | Định nghĩa / cách đo | Loại | Giá trị / đơn vị | Vai trò |
|---|---|---|---|---|
| Tái nhập viện 1 năm (mọi nguyên nhân) | ≥ 1 lần nhập viện nội trú tại BV Mô phỏng trong 365 <!-- not-a-result: mốc theo dõi của đề tài --> ngày kể từ ngày xuất viện của lần nhập viện chỉ số | Nhị giá | Có / Không | Kết cục chính |
| Tái nhập viện liên quan ĐTĐ | Tái nhập viện trong 1 năm có chẩn đoán chính/kèm theo thuộc khối ICD-10 liên quan ĐTĐ hoặc biến chứng đường huyết | Nhị giá | Có / Không | Kết cục phụ |
| Thời gian đến lần tái nhập viện đầu tiên | Số ngày từ ngày xuất viện đến ngày nhập viện của lần tái nhập viện đầu tiên (censored tại 365 <!-- not-a-result: mốc theo dõi của đề tài --> ngày nếu không tái nhập viện) | Thời gian-đến-sự kiện | Ngày | Kết cục phụ |
| Tử vong trong 1 năm (trong viện) | HIS chỉ ghi nhận tử vong trong viện; không xác định được tử vong ngoài viện | Nhị giá (trong viện) | Có / Không | Kết cục phụ — không đầy đủ, chỉ dùng cho phân tích độ nhạy |

**Biến nhiễu đưa vào mô hình chính**

| Biến | Định nghĩa / cách đo | Loại | Giá trị / đơn vị | Vai trò |
|---|---|---|---|---|
| Tuổi | Tuổi tại thời điểm nhập viện chỉ số, tính theo năm hoàn chỉnh | Liên tục | Năm | Mô tả / nhiễu |
| Giới | Giới ghi trong hồ sơ | Phân loại nhị giá | Nam / Nữ | Mô tả / nhiễu |
| Thời gian mắc ĐTĐ | Số năm từ ngày được chẩn đoán ĐTĐ type 2 đến ngày nhập viện chỉ số | Liên tục | Năm | Mô tả / nhiễu |
| Bệnh đồng mắc chính | Có/không ≥ 1 trong: tăng huyết áp, bệnh thận mạn, bệnh tim mạch — ghi nhận trước hoặc tại thời điểm nhập viện chỉ số | Nhị giá | Có / Không | Nhiễu |

**Biến không đưa vào mô hình chính (trung gian/vai trò nhân quả chưa rõ)**

| Biến | Định nghĩa / cách đo | Loại | Giá trị / đơn vị | Vai trò |
|---|---|---|---|---|
| Sử dụng insulin trong thời gian nằm viện | Có/không chỉ định insulin trong lần nhập viện chỉ số | Nhị giá | Có / Không | Mô tả / trung gian nghi ngờ |
| Thời gian nằm viện (lần nhập viện chỉ số) | Số ngày từ nhập viện đến xuất viện | Liên tục | Ngày | Mô tả / vai trò nhân quả chưa rõ |

**Biến thăm dò, có điều kiện (dự kiến ở đề cương, không có trong bộ dữ liệu mô phỏng của dự án này)**

| Biến | Định nghĩa / cách đo | Tình trạng |
|---|---|---|
| Tỷ số bạch cầu trung tính/lympho (NLR) | Tính từ công thức máu lúc nhập viện | Không có trong bộ dữ liệu trích xuất của dự án mô phỏng này |
| Chỉ số viêm tổng hợp (SII/SIRI) | Tính từ công thức máu lúc nhập viện | Như trên |
| Nguy cơ dinh dưỡng lúc nhập viện | Thang đánh giá dinh dưỡng thường quy (nếu có) | Như trên |

## Phụ lục 3. Từ điển biến (data dictionary) của tệp dữ liệu phân tích

Từ điển biến dưới đây mô tả cách mã hóa từng biến trong tệp dữ liệu phân tích đã khử định danh
(`04_data/cohort.deid.csv`, dữ liệu MÔ PHỎNG, n = 1070). Không có họ tên, số hồ sơ, ngày
tháng thật hay định danh cá nhân nào trong tệp này hoặc trong bảng dưới đây.

| Biến | Loại | Đơn vị | Mã hóa | Ghi chú |
|---|---|---|---|---|
| hba1c | Liên tục | % (NGSP) | 1 chữ số thập phân | Phơi nhiễm phụ (phân tích liên tục, mỗi 1%) |
| hba1c_group | Thứ tự/phân loại | — | `<7` / `7-9` / `>9` (nhóm `<7` tham chiếu) | Phơi nhiễm chính |
| readmit_1y | Nhị giá | — | 0 = Không, 1 = Có | Kết cục chính |
| readmit_dm_1y | Nhị giá | — | 0 = Không, 1 = Có | Kết cục phụ; chỉ = 1 khi readmit_1y = 1 |
| time_to_readmit_days | Liên tục | Ngày | 1–365 <!-- not-a-result: thiết kế biến, giới hạn theo dõi 365 ngày của đề tài -->; = 365 <!-- not-a-result: thiết kế biến --> khi không tái nhập viện (censored) | Kết cục phụ, thời gian-đến-sự kiện |
| death_inhosp_1y | Nhị giá | — | 0 = Không, 1 = Có | Kết cục phụ, chỉ tử vong trong viện, không đầy đủ |
| age | Liên tục | Năm | Số nguyên | — |
| sex | Phân loại nhị giá | — | `Nam` / `Nữ` | — |
| dm_duration_years | Liên tục | Năm | 1 chữ số thập phân; để trống nếu không ghi nhận | ~2,5% thiếu theo thiết kế; không suy diễn giá trị |
| htn / ckd / cvd | Nhị giá | — | 0/1 | Thành phần của biến dẫn xuất "bệnh đồng mắc chính" |
| *comorb_any* (dẫn xuất) | Nhị giá | — | = 1 nếu htn=1 hoặc ckd=1 hoặc cvd=1 | Tính ở bước phân tích, không có cột riêng trong tệp dữ liệu |
| insulin | Nhị giá | — | 0 = Không, 1 = Có | Mô tả/trung gian nghi ngờ |
| los_days | Liên tục | Ngày | Số nguyên dương | Mô tả, vai trò nhân quả chưa rõ |
| pid | Định danh nghiên cứu | — | `P0001`…`P1070` | Mã số nghiên cứu, không dùng trong phân tích thống kê, không phải số hồ sơ gốc |
