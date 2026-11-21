# Kiểm tra guideline

Kiểm tra ngày 2026-11-21. Hai loại: **guideline báo cáo** (reporting guideline — chọn theo thiết kế
trong `project.yaml`) và **guideline lâm sàng** (clinical guideline — dùng cho định nghĩa/tiêu chuẩn
chẩn đoán/ngưỡng so sánh). Không có OpenEvidence/Consensus/ClinicalTrials.gov trong phiên này; mọi
tra cứu dưới đây dùng `search_lit.py` (PubMed, dự phòng Europe PMC) — ghi nhận như hạn chế.

| Guideline | Loại | Phiên bản đang dùng trong dự án | Phiên bản hiện hành (tra cứu hôm nay) | Ngày kiểm tra | Hành động |
|---|---|---|---|---|---|
| STROBE | Báo cáo | STROBE (ghi trong `project.yaml → reporting_guideline`) | **Vẫn là bản 2007** (von Elm E, et al. PLoS Med 2007;4:e296, PMID 17941714) — tra PubMed hôm nay không thấy có bản sửa đổi lõi (core revision) mới hơn, chỉ có các **phần mở rộng** theo chủ đề (ví dụ STROBE-Equity 2025, PMID 40903054; STROBE-D cho đuối nước 2026, PMID 42463202) | 2026-11-21 | **Giữ nguyên STROBE.** Không cần đổi. Phần mở rộng STROBE-Equity là tùy chọn, không bắt buộc cho đề tài này (không phải trọng tâm công bằng y tế) — không áp dụng trừ khi tác giả muốn thêm |
| ADA Standards of Care in Diabetes — mục 16 "Diabetes Care in the Hospital" [1] | Lâm sàng | *Chưa trích dẫn trong dự án trước đây* | **Bản 2026** — đây là bản thường niên mới nhất (ADA cập nhật Standards of Care mỗi năm) | 2026-11-21 | **Nên trích dẫn** trong phần tổng quan/đặt vấn đề như nguồn khuyến cáo chung về kiểm soát đường huyết nội viện (bối cảnh), **không trích số liệu/ngưỡng cụ thể** từ guideline này vì chỉ đọc được tóm tắt chung (abstract PubMed cho các chương Standards of Care không có nội dung thật, chỉ là đoạn giới thiệu chuẩn — cần đọc full-text nếu muốn trích một khuyến cáo/ngưỡng cụ thể) |

## Ghi chú quan trọng

- **Không có guideline nào (ADA hay guideline khác) đưa ra khuyến cáo cụ thể về ngưỡng HbA1c lúc
  nhập viện để dự phòng tái nhập viện dài hạn** — khớp với Gap 4 đã ghi trong `02_evidence/gaps.md`.
  Mục 16 ADA chủ yếu khuyến cáo chung về mục tiêu đường huyết nội viện, lập kế hoạch xuất viện và
  chuyển tiếp chăm sóc (transition of care), không phải một ngưỡng dự báo tái nhập viện 1 năm.
- Kiểm tra lại SR về can thiệp giảm tái nhập viện [2] (đã có trong ledger từ bước
  `literature-search`) cho thấy **không có khuyến cáo thực hành dựa trên guideline** nào được trích
  trong abstract của SR đó — nhất quán với kết luận ở đây.
- Đã kiểm tra bài ADA 2026 không nằm trong danh sách thu hồi (không áp dụng câu lệnh thu hồi riêng vì
  đây là tài liệu hướng dẫn của hội chuyên khoa, không phải một nghiên cứu nguyên bản).
- **Hạn chế:** không có OpenEvidence/ClinicalTrials.gov trong phiên này để kiểm tra chéo; không đọc
  full-text ADA 2026 nên không trích dẫn số liệu/ngưỡng cụ thể từ đó — nếu luận văn cần trích một
  khuyến cáo cụ thể (ví dụ mục tiêu đường huyết nội viện), tác giả cần đọc bản đầy đủ tại
  `doi.org/10.2337/dc26-S016`.
- `grep` toàn dự án cho "STROBE" và "ADA"/"Standards of Care": chưa có file nào khác trích dẫn các
  guideline này ngoài `project.yaml` (STROBE) và file này — không phát hiện phiên bản cũ nào bị trích
  nhầm ở nơi khác trong dự án.

## Tài liệu tham khảo

1. 16. Diabetes Care in the Hospital: Standards of Care in Diabetes-2026. Diabetes Care. 2026;49(Supplement_1):S339-S355. doi:10.2337/dc26-S016. PMID: 41358892.
2. Chakraborty A, Pearson O, Schwartzkopff KM, O'rourke I, Ranasinghe I, Mah PM, et al. The effectiveness of in-hospital interventions on reducing hospital length of stay and readmission of patients with Type 2 Diabetes Mellitus: A systematic review. Diabetes Res Clin Pract. 2021;174:108363. doi:10.1016/j.diabres.2020.108363. PMID: 32771487.
