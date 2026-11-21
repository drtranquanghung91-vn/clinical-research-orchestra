# Vietnamese thesis Chapter 3 (Kết quả nghiên cứu)

Used by `results-writing` in thesis mode. Wording rules and sentence templates: `results-writing.md` (same
folder). Every number is a `{{R-…}}` placeholder; `render_results.py` writes the decimal comma
(`1,84`, `31,5%`, `KTC 95%: 1,21–2,79`) from `project.yaml → language.output: vi`.

## Outline
Sections follow the objectives in `01_question/` and the analysis-register order:
- **3.1 Đặc điểm chung của đối tượng nghiên cứu**: flow of participants (screened, excluded with reasons,
  analysed), then Table 1 (`A0`).
- **3.2 Kết quả theo mục tiêu 1**: the primary analysis, crude then adjusted.
- **3.3 Kết quả theo mục tiêu 2** (and so on): secondary analyses, one subsection per register row.
- **Last subsection: Phân tích thăm dò (hậu kiểm)**: post-hoc analyses and deviations, each paragraph
  labelled ("thăm dò", "hậu kiểm"), each quoting why it was done (`POST-HOC A<n>:` line in `decisions.md`).

Headings 3.1, 3.1.1. Section numbers follow the chapter, not the analysis IDs.

## Tables
- Caption **above**: `Bảng 3.n. <tiêu đề>` (numbered in order of appearance in the chapter; the source
  CSV's `T…` id need not match), directly followed by the pipe table.
- `Nguồn:` and `Ghi chú:` lines **directly below** the table, no blank line between (abbreviations, the
  model and its covariates, the test used).
- Every cell number is a placeholder; columns with n (%) use `.full` of a `percent` record, mean ± ĐLC
  use `.full` of a `mean` record.
- A literal `|` inside a cell is written `\|`, a literal `*` as `\*`.

## Nhận xét
After every table, one paragraph starting `Nhận xét:` with the 2–4 numbers that matter, as placeholders,
estimate and CI before p. It describes; it does not explain, compare with other studies or recommend
(that is Chapter 4, Bàn luận). Do not repeat every row of the table.

## Figures
Figures are captioned `Biểu đồ 3.n. <tiêu đề>` below the figure. They are produced by `research-figures`
(P3, not available yet): leave a line `[Biểu đồ 3.n: <nội dung> — chờ research-figures]` where it belongs.

## Numbers
Decimal comma, no thousands separator, en dash in ranges (all from `render_results.py`). Ngưỡng phân nhóm
or tiêu chuẩn chọn (HbA1c ≥ 8%, 18–65 tuổi) carry `<!-- not-a-result: … -->`; numbers computed from
results carry `<!-- derived: … -->`.

## Length
Follow the training institution's regulation on chapter length and table count. If none is given, ask
the author and record the decision in `decisions.md`.

## Example (fictional ids, `design: cohort`)

`R-A3-…` are `posthoc`. This block passes `render_results.py`, `check_numbers.py` on the rendered file,
`analysis_plan.py check --text` and `build_docx.py` (workflow, section 6).

```markdown
# CHƯƠNG 3. KẾT QUẢ NGHIÊN CỨU

## 3.1 Đặc điểm chung của đối tượng nghiên cứu

Bảng 3.1. Đặc điểm chung của đối tượng nghiên cứu (n = {{R-A0-001}})
| Đặc điểm | Chung |
|---|---|
| Tuổi (năm), trung bình ± ĐLC | {{R-A0-002.full}} |
| Nữ, n (%) | {{R-A0-003.full}} |
Nguồn: số liệu nghiên cứu.
Ghi chú: ĐLC: độ lệch chuẩn.

Nhận xét: Tuổi trung bình của {{R-A0-001}} người bệnh là {{R-A0-002.full}} năm; nữ chiếm {{R-A0-003}}.

## 3.2 Kết quả theo mục tiêu 1

Bảng 3.2. Tái nhập viện trong 1 năm theo nhóm HbA1c
| Nhóm HbA1c | n | Tái nhập viện, n (%) | OR hiệu chỉnh (KTC 95%) | p |
|---|---|---|---|---|
| ≥ 8% <!-- not-a-result: ngưỡng phân nhóm --> | {{R-A1-002.n}} | {{R-A1-002.full}} | {{R-A1-001}} ({{R-A1-001.ci}}) | {{R-A1-001.p}} |
| < 8% <!-- not-a-result: ngưỡng phân nhóm --> | {{R-A1-003.n}} | {{R-A1-003.full}} | 1 (tham chiếu) | |
Nguồn: số liệu nghiên cứu.
Ghi chú: OR hiệu chỉnh theo tuổi và giới (hồi quy logistic); KTC: khoảng tin cậy.

Nhận xét: Tỷ lệ tái nhập viện trong 1 năm là {{R-A1-002}} ở nhóm HbA1c ≥ 8% <!-- not-a-result: ngưỡng phân nhóm --> và {{R-A1-003}} ở nhóm còn lại, chênh lệch 11,2 <!-- derived: R-A1-002 − R-A1-003 --> điểm phần trăm. Sau hiệu chỉnh theo tuổi và giới, HbA1c ≥ 8% <!-- not-a-result: ngưỡng phân nhóm --> liên quan với odds tái nhập viện cao hơn (OR {{R-A1-001}}; KTC 95%: {{R-A1-001.ci}}; p = {{R-A1-001.p}}).

## 3.3 Phân tích thăm dò (hậu kiểm)

Phân tích thăm dò (hậu kiểm) theo giới, không có trong kế hoạch phân tích, cho thấy OR hiệu chỉnh là {{R-A3-001.full}} ở nữ và {{R-A3-002.full}} ở nam (p tương tác = {{R-A3-003}}); kết quả này chỉ mang tính tạo giả thuyết.
```
