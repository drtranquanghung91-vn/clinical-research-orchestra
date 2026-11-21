# Bản đồ bằng chứng

Cột theo thiết kế **và** mốc thời gian theo dõi (vì đây là điểm phân biệt chính của khoảng trống).
Số trong [ ] là số thứ tự tài liệu tham khảo (xem mục Tài liệu tham khảo cuối file), được gán bằng
`cite_render.py`, không đánh số tay.

| Chủ đề con \ Thiết kế & mốc thời gian | SR/MA | Đoàn hệ — ngắn hạn (≤ 31 ngày) | Đoàn hệ — 1 năm / 365 ngày | Việt Nam |
|---|---|---|---|---|
| HbA1c lúc **nhập viện** → tái nhập viện ở ĐTĐ type 2 nói chung (không giới hạn bệnh đồng mắc) | 0 | 2 [1,2] (30 và 31 ngày; HbA1c là 1 trong nhiều yếu tố, không phải phơi nhiễm chính của nghiên cứu gốc) | 0 — **ô trống, ứng viên khoảng trống chính** | 0 |
| Yếu tố/mô hình dự báo tái nhập viện ở ĐTĐ type 2 nói chung (không riêng HbA1c) | 0 | 2 [1,2] | 1 [3] (mô hình học máy đa biến, không tách riêng hiệu ứng độc lập của HbA1c ở mốc 1 năm) | 0 |
| HbA1c đo **sau xuất viện**/theo dõi ngoại trú → tái nhập viện, tử vong | 0 | — | 1 [4] (không nêu mốc 1 năm cụ thể cho tái nhập viện; chiều hướng ngược với giả thuyết của đề tài) | 0 |
| Can thiệp trong bệnh viện làm giảm thời gian nằm viện/tái nhập viện ở ĐTĐ type 2 | 1 [5] | (trong SR) | (trong SR) | 0 |
| HbA1c/kiểm soát đường huyết & kết cục ở nhóm bệnh đồng mắc đặc thù (suy tim, đột quỵ, bệnh mạch vành, hậu phẫu) | — | nhiều (ngoài phạm vi bảng này — xem hạn chế sàng lọc trong `search-strategy.md`) | nhiều (ví dụ tái nhập viện 1 năm ở CAD+ĐTĐ, đột quỵ+ĐTĐ — không phải quần thể ĐTĐ type 2 nói chung) | 0 |

**Nhận xét:**
- Ô "HbA1c lúc nhập viện → tái nhập viện 1 năm, ĐTĐ type 2 nói chung" **trống hoàn toàn** — đây là
  khoảng trống chính mà đề tài hướng tới lấp đầy (xem `gaps.md`, Gap 1).
- Cột "Việt Nam" trống ở mọi dòng trên PubMed — khoảng trống về quần thể (Gap 2), nhưng cần tác giả
  tìm thêm ở tạp chí tiếng Việt trước khi khẳng định chắc chắn (xem hạn chế trong `search-strategy.md`).
- Bằng chứng ở mốc 1 năm hiện có ([3]) dùng mô hình học máy dự báo đa biến, không phải hồi quy
  truyền thống báo cáo OR/HR riêng cho HbA1c — khác về phương pháp với thiết kế đoàn hệ hồi cứu +
  hồi quy đa biến mà đề tài này dự định dùng (Gap 3, khoảng trống phương pháp).
- Không có SR/MA nào gộp số liệu định lượng cho câu hỏi "HbA1c nhập viện & tái nhập viện 1 năm ở ĐTĐ
  type 2" — không áp dụng việc đọc I²/prediction interval ở đây (không có phân tích gộp để đọc).

## Tài liệu tham khảo

1. Hu X, Su X, Chen S, Wang Q, He F, Zhang R. Predictors of 30-day readmission in young and middle-aged T2DM patients: a retrospective cohort study. Endocrine. 2026;91(1). doi:10.1007/s12020-026-04626-3. PMID: 42068438.
2. Cao J, Shi Q, Yu Z, Xie H. A nomogram incorporating nutritional risk for predicting 31-day unplanned readmission in adults with type 2 diabetes mellitus using LASSO regression. Front Nutr. 2026;13:1863130. doi:10.3389/fnut.2026.1863130. PMID: 42876841.
3. Li L, Jiang S. Dynamic evolution of readmission risk factors across short-, medium-, and long-term horizons in type 2 diabetes: a machine learning-based predictive modeling study with SHAP interpretability. Front Endocrinol (Lausanne). 2026;17:1827506. doi:10.3389/fendo.2026.1827506. PMID: 42440445.
4. Robbins T, Sankaranarayanan S, Randeva H, Keung SNLC, Arvanitis TN. Association between glycosylated haemoglobin and outcomes for patients discharged from hospital with diabetes: A health informatics approach. Digit Health. 2021;7:20552076211007661. doi:10.1177/20552076211007661. PMID: 33948220.
5. Chakraborty A, Pearson O, Schwartzkopff KM, O'rourke I, Ranasinghe I, Mah PM, et al. The effectiveness of in-hospital interventions on reducing hospital length of stay and readmission of patients with Type 2 Diabetes Mellitus: A systematic review. Diabetes Res Clin Pract. 2021;174:108363. doi:10.1016/j.diabres.2020.108363. PMID: 32771487.
