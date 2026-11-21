# Chiến lược tìm kiếm

> **Dự án mô phỏng** (Example author). Đây là một tổng quan có cấu trúc dạng scoping
> (structured/scoping evidence synthesis), **không phải tổng quan hệ thống (systematic review)**:
> không có đề cương PROSPERO, không có hai người sàng lọc độc lập, không theo đầy đủ PRISMA 2020.
> Nếu cần một SR/MA thật, phải làm lại từ đầu theo `systematic-review` (phase P3).

## Câu hỏi và khung PECO (từ `01_question/question.md`)

- **P**: người lớn (≥ 18 tuổi) ĐTĐ type 2, xuất viện tại Khoa Nội tiết (giả định cho dự án mô phỏng).
- **E**: HbA1c lúc nhập viện cao (kiểm soát đường huyết kém); phân tích chính 3 nhóm < 7% / 7–9% / > 9%.
- **C**: nhóm HbA1c < 7% (tham chiếu).
- **O**: tái nhập viện mọi nguyên nhân trong 1 năm (chính); tái nhập viện liên quan ĐTĐ, thời gian đến
  tái nhập viện, tử vong 1 năm (phụ).

## Bước 0 — Kiểm tra đổi tên/định nghĩa thuật ngữ

Đã thực hiện ở bước `research-question` (2026-11-21) và được tái sử dụng ở đây: "đái tháo đường type
2", "HbA1c" (glycated hemoglobin A), "tái nhập viện" (readmission/rehospitalization) không có ghi
nhận đổi tên hoặc thay đổi tiêu chuẩn chẩn đoán gần đây ảnh hưởng đến chiến lược tìm kiếm. Không phát
hiện MeSH drift cần xử lý. Khối P dùng cả MeSH `"Diabetes Mellitus, Type 2"` và từ tự do
`type 2 diabetes[tiab]`/`T2DM[tiab]`; khối E dùng MeSH `"Glycated Hemoglobin A"` và từ tự do
`HbA1c[tiab]`; khối O dùng MeSH `"Patient Readmission"` và từ tự do
`readmission[tiab]`/`rehospitalization[tiab]`/`rehospitalisation[tiab]`.

## Nguồn đã dùng và nguồn không khả dụng trong phiên này

- **Đã dùng**: PubMed/Europe PMC qua `search_lit.py search` (E-utilities, có dự phòng Europe PMC khi
  NCBI không phản hồi).
- **Không khả dụng trong phiên này** (ghi nhận như hạn chế, không phải "không có bằng chứng"):
  OpenEvidence MCP, Consensus, ClinicalTrials.gov MCP/registry tool. Chỉ có `search_lit.py` và
  `WebSearch` chung (không dùng WebSearch cho tra cứu y văn có trích dẫn, vì không trả về PMID/DOI
  xác minh được). Vì vậy **không chạy được** câu hỏi tổng hợp OpenEvidence/Consensus và **không kiểm
  tra được** ClinicalTrials.gov cho các thử nghiệm đang chạy/chưa công bố liên quan đến chủ đề này —
  đây là một hạn chế của tổng quan này, không phải bằng chứng "không có nghiên cứu nào".
- Tạp chí tiếng Việt (Tạp chí Y học Việt Nam, Y học TP.HCM…) không được lập chỉ mục trên PubMed và
  chưa được tìm trong phiên này (Google Scholar/thư viện trường cần được tác giả tìm thêm).

## Nhật ký tìm kiếm (PRISMA-S)

Cơ sở dữ liệu: PubMed (qua `search_lit.py`, dùng E-utilities của NCBI, dự phòng Europe PMC). Ngày
tìm kiếm: 2026-11-21. Không giới hạn năm xuất bản trừ khi ghi chú; không giới hạn ngôn ngữ (kết quả
trả về chủ yếu tiếng Anh). Loại bỏ trùng lặp: thủ công theo PMID khi hợp nhất các câu lệnh.

| # | Ngày | Nguồn | Câu lệnh | Bộ lọc | Số kết quả | Số giữ lại |
|---|---|---|---|---|---|---|
| 1 | 2026-11-21 | PubMed | `HbA1c[tiab] AND readmission[tiab] AND diabetes[tiab] AND (systematic review[pt] OR meta-analysis[pt])` | SR/MA | 2 | 1 (chakraborty2021; rollins2016 không liên quan — về phẫu thuật) |
| 2 | 2026-11-21 | PubMed | `"HbA1c"[tiab] AND ("readmission"[tiab] OR "rehospitalization"[tiab] OR "rehospitalisation"[tiab]) AND "type 2 diabetes"[tiab]` | không | 21 | 2 (hu2026; phần còn lại là nhóm bệnh đồng mắc đặc thù — suy tim, đột quỵ, phẫu thuật — xem mục "sàng lọc") |
| 3 | 2026-11-21 | PubMed | `"HbA1c"[tiab] AND "readmission"[tiab] AND ("one year"[tiab] OR "1-year"[tiab] OR "12-month"[tiab] OR "12 months"[tiab])` | mốc 1 năm | 21 (trùng lặp lớn với #2) | 0 mới |
| 4 | 2026-11-21 | PubMed | `"type 2 diabetes"[tiab] AND "readmission"[tiab] AND (Vietnam[Affiliation] OR Vietnam[tiab] OR "Viet Nam"[tiab])` | Việt Nam | 1 | 0 (người Việt nhập cư ở Úc — không phải nghiên cứu thực hiện tại Việt Nam, đọc abstract để xác nhận) |
| 5 | 2026-11-21 | PubMed | `"HbA1c"[tiab] AND ("readmission"[tiab] OR "rehospitalization"[tiab]) AND "type 2 diabetes"[tiab] AND (China[Affiliation] OR Thailand[Affiliation] OR Korea[Affiliation] OR Japan[Affiliation] OR Singapore[Affiliation] OR Malaysia[Affiliation] OR Indonesia[Affiliation] OR Philippines[Affiliation])` | khu vực châu Á | 20 | 1 mới (cao2026; phần còn lại trùng #2 hoặc là nhóm bệnh đồng mắc đặc thù) |
| 6 | 2026-11-21 | PubMed | `"type 2 diabetes"[tiab] AND "readmission"[tiab] AND ("risk factors"[tiab] OR "predictors"[tiab] OR "associated factors"[tiab]) AND ("retrospective"[tiab] OR "cohort"[tiab])` | yếu tố liên quan, đoàn hệ hồi cứu | 30 | 1 mới (li2026; phần còn lại là nhóm bệnh đồng mắc đặc thù hoặc ngoài chủ đề — xem mục "sàng lọc") |
| 7 | 2026-11-21 | PubMed | `"diabetes"[tiab] AND ("transitional care"[tiab] OR "transition of care"[tiab] OR "hospital discharge"[tiab]) AND (guideline[tiab] OR "standards of care"[tiab])` | tìm guideline | 15 | 0 (không có guideline nào trả lời trực tiếp câu hỏi về HbA1c nhập viện và tái nhập viện 1 năm) |
| 8 | 2026-11-21 | PubMed | `(33948220[pmid] OR 42068438[pmid] OR 32771487[pmid] OR 42440445[pmid] OR 42876841[pmid]) AND (Retracted Publication[pt] OR Retraction of Publication[pt] OR "Expression of Concern"[pt])` | kiểm tra thu hồi | 0 | — (không bài nào bị thu hồi) |

**Sàng lọc:** các câu lệnh #2, #5, #6 có nhiều kết quả trùng lặp giữa nhau; sau khi hợp nhất theo
PMID, tổng số bài duy nhất được rà tiêu đề/abstract ước tính ~55 bài. Phần lớn bị loại vì tập trung
vào nhóm bệnh đồng mắc đặc thù không phải đối tượng của đề tài (suy tim, đột quỵ, bệnh mạch vành,
hậu phẫu chỉnh hình/cột sống/bắc cầu, nhiễm trùng, viêm tụy…) hoặc về hiệu quả thuốc
(SGLT2i, GLP-1 RA) — không phải câu hỏi về HbA1c nhập viện như yếu tố nguy cơ tái nhập viện ở ĐTĐ
type 2 nói chung. **5 bài được giữ lại** sau sàng lọc (xem `evidence-table.md`); đây là rà theo mức
độ liên quan trực tiếp (not toàn bộ ~55 bài đều được đọc full-text, chỉ đọc title/abstract qua
metadata).

**Guideline:** không tìm thấy guideline cụ thể nào khuyến cáo một ngưỡng HbA1c lúc nhập viện để dự
phòng tái nhập viện 1 năm ở ĐTĐ type 2 (câu lệnh #7). ADA Standards of Care có khuyến cáo chung về
kiểm soát đường huyết nội viện nhưng không được đọc full-text trong phiên này nên không trích dẫn số
liệu cụ thể từ đó.

## Kiểm tra phản chứng cho khoảng trống "chưa có ở Việt Nam"

Câu lệnh #4 (Vietnam[Affiliation] hoặc Vietnam[tiab]) chỉ trả về 1 kết quả, và đó là nghiên cứu ở
người Việt nhập cư tại Úc — không phải nghiên cứu thực hiện tại Việt Nam. Không có công cụ
ClinicalTrials.gov trong phiên này để kiểm tra thêm thử nghiệm đang đăng ký tại Việt Nam liên quan
đến chủ đề (hạn chế, xem trên). **Kết luận có điều kiện:** "chưa tìm thấy trên PubMed", không viết
"chưa ai làm ở Việt Nam" — cần tác giả tìm thêm trên Google Scholar/Tạp chí Y học Việt Nam.

## Công bố sử dụng AI (ICMJE)

Việc tìm kiếm, sàng lọc sơ bộ theo tiêu đề/abstract, tổng hợp bảng bằng chứng và soạn thảo văn bản
trong các file ở `02_evidence/` được thực hiện với sự hỗ trợ của Claude (Anthropic) thông qua công cụ
`search_lit.py` (PubMed/Europe PMC E-utilities) trong phiên làm việc ngày 2026-11-21. Tác giả (Example
author) chịu trách nhiệm kiểm tra lại toàn bộ trích dẫn, số liệu và nhận định trước khi dùng cho bất
kỳ mục đích công bố.

## Hạn chế của tìm kiếm này

- Không dùng được OpenEvidence, Consensus, ClinicalTrials.gov trong phiên này (xem trên).
- Chỉ rà title/abstract qua metadata PubMed, chưa đọc full-text bài nào (đánh giá chất lượng ở mức
  "preliminary appraisal from abstract" — xem `appraisal/`).
- Tạp chí tiếng Việt chưa được tìm trong phiên này.
- IEEE/arXiv không áp dụng (chủ đề không thuộc AI/kỹ thuật) nên không tìm.
- Đây là tổng quan dạng scoping, không phải SR/MA; không tính I²/prediction interval vì không có
  phân tích gộp (meta-analysis) nào được thực hiện hoặc trích dẫn trực tiếp cho câu hỏi này.
