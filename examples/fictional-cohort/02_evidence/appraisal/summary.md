# Bảng tổng hợp thẩm định (nhiều bài báo)

Đánh giá sơ bộ, chỉ từ abstract (preliminary, from abstract). Chi tiết từng bài: xem file cùng tên
trong thư mục này.

| # | Bài báo [ref] | Thiết kế thật | Công cụ | Miền đáng quan ngại chính | Nguy cơ sai lệch tổng thể | Hiệu ứng (95% CI) | Liên quan đến Việt Nam/đề tài | Ghi chú |
|---|---|---|---|---|---|---|---|---|
| 1 | Chakraborty A, et al. 2021 [1] | Tổng quan hệ thống (narrative, không gộp số) | AMSTAR 2 | Hầu hết hạng mục trọng yếu không rõ (đề cương, tìm kiếm, RoB của nghiên cứu gộp vào) | Không đủ thông tin để kết luận | Không báo cáo trong abstract | Thấp — câu hỏi khác (hiệu quả can thiệp, không phải HbA1c) | Chỉ dùng làm bối cảnh |
| 2 | Hu X, et al. 2026 [2] | Đoàn hệ hồi cứu (phơi nhiễm) | NOS (ROBINS-E là công cụ chính thức hơn) | Danh sách biến nhiễu hiệu chỉnh không đầy đủ; mất dấu tái nhập viện ngoài hệ thống không rõ | Một số quan ngại | HbA1c mỗi 1%: aOR 1,15 (1,03–1,29); 30 ngày | Gián tiếp — mốc 30 ngày, tuổi 18–59, Trung Quốc | Dùng có cân nhắc; tham khảo thận trọng cho cỡ mẫu |
| 3 | Robbins T, et al. 2021 [3] | Đoàn hệ hồi cứu (phơi nhiễm) | NOS (ROBINS-E là công cụ chính thức hơn) | Không rõ có hiệu chỉnh đa biến; n rất nhỏ cho đúng phơi nhiễm "lúc nhập viện" (399/46.357) | Một số quan ngại đến cao | Cohen's D 0,28 (HbA1c), chiều ngược với giả thuyết | Gián tiếp — phơi nhiễm khác thời điểm đo (sau xuất viện), gộp T1DM+T2DM, Anh | Không dùng làm bằng chứng/tham số trực tiếp; chỉ minh họa Gap 3 |
| 4 | Li L, Jiang S 2026 [4] | Mô hình dự báo (học máy) | PROBAST+AI | Không rõ HbA1c có trong tập biến; kiểm định thời gian cho mô hình 365 ngày không rõ | Không rõ | Không có OR/HR; định tính qua SHAP | Gián tiếp — đúng mốc 1 năm, sai loại câu hỏi (dự báo, không phải ước lượng hiệu ứng) | Dùng có cân nhắc, minh họa Gap 1 |
| 5 | Cao J, et al. 2026 [5] | Mô hình dự báo (nomogram, LASSO) | PROBAST+AI | Chỉ kiểm định nội bộ, chưa kiểm định ngoài (tác giả tự nêu) | Một số quan ngại | AUC 0,846 (0,814–0,878); không có OR riêng cho HbA1c | Gián tiếp — mốc 31 ngày, Trung Quốc | Dùng có cân nhắc; tỷ lệ tái nhập viện 18,5% tham khảo thận trọng cho cỡ mẫu |

## GRADE sơ bộ (preliminary) cho kết cục chính của đề tài

**Kết cục:** tái nhập viện mọi nguyên nhân trong 1 năm, theo HbA1c lúc nhập viện, ở ĐTĐ type 2 nói
chung.

| Yếu tố | Nhận định |
|---|---|
| Số nghiên cứu đo đúng phơi nhiễm + đúng outcome + đúng mốc thời gian | **0** |
| Bằng chứng gần nhất (gián tiếp) | [2] (30 ngày, đúng phơi nhiễm, sai mốc thời gian, sai độ tuổi); [5] (31 ngày, đúng phơi nhiễm trong mô hình, không có hiệu ứng riêng); [4] (đúng mốc 1 năm, sai loại câu hỏi/phương pháp) |
| Hạ bậc — tính gián tiếp (indirectness) | Có, nghiêm trọng — không nghiên cứu nào khớp cả 3 yếu tố (phơi nhiễm đúng lúc nhập viện + outcome đúng 1 năm + dân số ĐTĐ type 2 nói chung) |
| Hạ bậc — không nhất quán (inconsistency) | Không áp dụng được đầy đủ (không có ≥ 2 nghiên cứu cùng đo một hiệu ứng để so I²); tuy nhiên chiều hướng giữa [2] (HbA1c nhập viện cao → tái nhập viện cao, 30 ngày) và [3] (HbA1c sau xuất viện thấp → tái nhập viện cao) gợi ý sự phụ thuộc vào thời điểm đo |
| Hạ bậc — nguy cơ sai lệch (risk of bias) | Có, một phần — [2] và [5] còn một số quan ngại (xem bảng trên) |
| Hạ bậc — thiếu chính xác (imprecision) | Có — hiệu ứng của [2] có cận dưới KTC 95% rất gần 1 (1,03) |
| **Mức độ tin cậy tổng thể: RẤT THẤP (very low)** | Phù hợp với kết luận ở Gap 1: đây là khoảng trống thật, không phải "đã biết câu trả lời" |

**Diễn giải cho đề tài:** mức độ tin cậy rất thấp của bằng chứng gián tiếp hiện có **ủng hộ, không
phải cản trở**, việc thực hiện đề tài — đây chính xác là loại khoảng trống (thiếu bằng chứng trực
tiếp, đúng mốc thời gian) mà một nghiên cứu đoàn hệ hồi cứu mới có thể lấp đầy.

## Tài liệu tham khảo

1. Chakraborty A, Pearson O, Schwartzkopff KM, O'rourke I, Ranasinghe I, Mah PM, et al. The effectiveness of in-hospital interventions on reducing hospital length of stay and readmission of patients with Type 2 Diabetes Mellitus: A systematic review. Diabetes Res Clin Pract. 2021;174:108363. doi:10.1016/j.diabres.2020.108363. PMID: 32771487.
2. Hu X, Su X, Chen S, Wang Q, He F, Zhang R. Predictors of 30-day readmission in young and middle-aged T2DM patients: a retrospective cohort study. Endocrine. 2026;91(1). doi:10.1007/s12020-026-04626-3. PMID: 42068438.
3. Robbins T, Sankaranarayanan S, Randeva H, Keung SNLC, Arvanitis TN. Association between glycosylated haemoglobin and outcomes for patients discharged from hospital with diabetes: A health informatics approach. Digit Health. 2021;7:20552076211007661. doi:10.1177/20552076211007661. PMID: 33948220.
4. Li L, Jiang S. Dynamic evolution of readmission risk factors across short-, medium-, and long-term horizons in type 2 diabetes: a machine learning-based predictive modeling study with SHAP interpretability. Front Endocrinol (Lausanne). 2026;17:1827506. doi:10.3389/fendo.2026.1827506. PMID: 42440445.
5. Cao J, Shi Q, Yu Z, Xie H. A nomogram incorporating nutritional risk for predicting 31-day unplanned readmission in adults with type 2 diabetes mellitus using LASSO regression. Front Nutr. 2026;13:1863130. doi:10.3389/fnut.2026.1863130. PMID: 42876841.
