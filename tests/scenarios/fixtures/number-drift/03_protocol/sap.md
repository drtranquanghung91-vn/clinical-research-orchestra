# Kế hoạch phân tích thống kê (SAP)

Đề tài: tái nhập viện 30 ngày ở bệnh nhân đái tháo đường típ 2 (dữ liệu giả lập, dùng để thử kỹ năng).
Thiết kế: thuần tập hồi cứu. Kết cục chính: tái nhập viện trong 30 ngày (readmit, 0/1). Phơi nhiễm chính: HbA1c lúc nhập viện (hba1c, %).
Đơn vị phân tích: bệnh nhân (id). Cỡ mẫu: 300. Ngưỡng ý nghĩa hai phía 0,05.

## 15. Thay đổi so với đề cương
Không có.

## Analysis register (Bảng đăng ký phân tích)
| ID | Objective | Outcome | Population | Method | Covariates | Multiplicity |
|---|---|---|---|---|---|---|
| A0 | descriptive | đặc điểm nền (tuổi, giới, HbA1c) | all | Table 1 | none | n/a |
| A1 | primary | readmit | all | logistic regression, exposure hba1c | age | none |
| A2 | secondary | readmit | all | readmission by sex, chi-square and OR | none | none |

Không có phân tích dưới nhóm hay phân tích thăm dò nào được đăng ký.
