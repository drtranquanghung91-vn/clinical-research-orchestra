# Chuỗi tìm kiếm (search strings)

> **LƯU Ý:** Tổng quan hệ thống HƯ CẤU. Nguồn duy nhất để tìm nghiên cứu đưa vào là "Simulated database" (nền
> tảng: fictional), vì bản thân các nghiên cứu là mô phỏng, không tồn tại trên các cơ sở dữ liệu y văn thật.
> PubMed không tìm nghiên cứu đưa vào; chỉ dùng để tìm tài liệu nền/phương pháp luận THẬT (xem dưới).

## Simulated database (fictional)

- Mã chuỗi: **S1**
- Chuỗi: `("thuốc X" OR "drug X") AND ("bệnh nội khoa cấp" OR "acute medical illness" OR hospitalized adults) AND ("tử vong 30 ngày" OR "30-day mortality" OR "all-cause mortality") AND (randomized controlled trial OR RCT OR placebo-controlled)`
- Giới hạn (limits): không giới hạn ngôn ngữ; không giới hạn năm công bố.
- Ngày chạy lần cuối: 23/11/2026
- Người chạy: tác giả (Example author), tự chạy và xuất tệp; không có tool nào trong dự án chạy nguồn này.
- Số kết quả (hits): 24
- Tệp xuất (export_file): exports/simulated-export.ris (đường dẫn tính từ 02_evidence/sr/)

## PubMed (chỉ tài liệu nền/phương pháp luận thật — không tìm nghiên cứu đưa vào)

- Mã chuỗi: không áp dụng mã Sn cho mục này (không phải nguồn tìm nghiên cứu đưa vào); các tra cứu riêng lẻ chạy
  qua `search_lit.py` và được kiểm bằng `verify_refs.py`.
- Mục đích: tìm các tài liệu phương pháp luận thật để trích dẫn trong đề cương/bài viết, ví dụ PRISMA 2020,
  RoB 2 (Cochrane risk-of-bias tool), GRADE, thống kê I² và khoảng dự đoán (prediction interval), phương pháp
  REML cho mô hình hiệu ứng ngẫu nhiên.
- Ví dụ chủ đề tra cứu (chạy riêng từng chủ đề bằng `search_lit.py`, không gộp thành một chuỗi Sn):
  - `"PRISMA 2020"[tiab] AND statement[tiab]`
  - `"Cochrane risk-of-bias tool"[tiab] OR "RoB 2"[tiab]`
  - `GRADE[tiab] AND "quality of evidence"[tiab]`
  - `heterogeneity[tiab] AND ("I2"[tiab] OR "prediction interval"[tiab])`
  - `"restricted maximum likelihood"[tiab] OR REML[tiab]`
- Quy tắc bắt buộc: không bao giờ gán số liệu hư cấu (ví dụ số liệu của "thuốc X") cho một bài báo PubMed thật
  tìm được qua các tra cứu này.

## Nhật ký tìm kiếm

Mỗi lượt chạy — nguồn S1 (tự chạy) hoặc các tra cứu PubMed phương pháp luận — được ghi một dòng vào
`02_evidence/sr/search-log.csv` (`database,platform,date_run,string_id,hits,export_file`), theo đúng mẫu ở
`references/review/search-strings.md`. Số hits của S1 phải khớp với số bản ghi mà `screening.py . import`
đọc được từ tệp xuất.
