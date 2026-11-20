# Evidence output templates

Methods content by Amelia Le (co-author), adapted for clinical-research-orchestra. Translated from
`literature-evidence-research-vi/reference/output-template.md` (v3). Each template is shown with a
Vietnamese and an English heading set; use the set that matches `project.yaml → language.output`.
Cells and examples are shapes only: fill them from papers a tool returned in this session.

## Evidence table / Bảng bằng chứng
File: `02_evidence/evidence-table.md`.

English headings:

| # | Author, year [ref] | Country | Design (real) | n | Population | Intervention / Exposure | Comparator | Outcome | Main result (effect, 95% CI) | Main limitation | Risk of bias (tool) |
|---|---|---|---|---|---|---|---|---|---|---|---|

Vietnamese headings:

| # | Tác giả, năm [ref] | Quốc gia | Thiết kế (thật) | n | Quần thể | Can thiệp / Phơi nhiễm | So sánh | Outcome | Kết quả chính (effect, 95% CI) | Hạn chế chính | Nguy cơ sai lệch (công cụ) |
|---|---|---|---|---|---|---|---|---|---|---|---|

Conventions: write an SR/MA as "SR/MA (k studies, total n)" (Vietnamese: "SR/MA (k nghiên cứu, n tổng)").
A result that is not in the abstract is written "not reported in the abstract" ("không báo cáo trong
abstract"). Risk of bias is low / moderate / high / unclear (thấp / trung bình / cao / không rõ) with the
tool name.

## Evidence map / Bản đồ bằng chứng
File: `02_evidence/evidence-map.md`. Example by design:

| Sub-topic \ Design (Chủ đề con \ Thiết kế) | SR/MA | RCT | Cohort | Case-control / Cross-sectional (Cắt ngang) | Vietnam (Việt Nam) |
|---|---|---|---|---|---|
| Prevalence (Tỷ lệ mắc) | 2 [1,2] | — | 5 [3–7] | 4 [8–11] | 0 |
| Associated factors (Yếu tố liên quan) | 1 [12] | — | 6 [...] | 3 [...] | 1 [...] |
| Effect of intervention X (Hiệu quả can thiệp X) | 3 [...] | 12 (within SR) | 1 | — | 0 |

A "0" or "—" in the Vietnam column, or a cell with only weak evidence, is a gap candidate and must pass
the counter-check. In a real file the numbers in brackets come from `cite_render.py`, never by hand.

## Research gap / Khoảng trống nghiên cứu
File: `02_evidence/gaps.md`, one block per gap.

English:

**Gap {n}: {one-sentence statement}**
- Type: {population / evidence / conflicting / methodological / outcome / implementation / outdated}
- Evidence: {empty cell in the map; SR [n] concludes "..."; conflicting results [a] vs [b]}
- Counter-check: {query run aimed at this gap, source, number of results, conclusion}
- Suggested research question (PICO/PECO): {...}
- Feasibility for the user: {high / medium / low + reason}

Vietnamese:

**Gap {n}: {phát biểu một câu}**
- Loại: {population / evidence / conflicting / methodological / outcome / implementation / outdated}
- Bằng chứng: {ô trống trong map; SR [n] kết luận "..."; kết quả trái chiều [a] vs [b]}
- Kiểm tra phản chứng: {truy vấn đã chạy nhắm gap này, nguồn, số kết quả, kết luận}
- Câu hỏi nghiên cứu gợi ý (PICO/PECO): {...}
- Mức khả thi cho người dùng: {cao / trung bình / thấp + lý do}

## Chapter structure (Vietnamese thesis or proposal) / Cấu trúc chương Tổng quan tài liệu
(The prose itself is written with `literature-review`.)

1.1. General background of the disease or problem (definition, current diagnostic criteria,
epidemiology worldwide, in Asia, in Vietnam) / Đại cương về bệnh/vấn đề
1.2. Pathogenesis or theoretical basis, just enough to explain the variables and hypotheses / Cơ chế
bệnh sinh / cơ sở lý thuyết
1.3. Core content of the question (associated factors, treatments or diagnostic tools): the longest
part / Nội dung trọng tâm của câu hỏi
1.4. Measurement tools for the main outcome (scales, questionnaires, reliability, whether a
standardised Vietnamese version exists) / Công cụ đo lường outcome chính
1.5. Research worldwide and in Vietnam (synthesised by theme, leading into the gap) / Tình hình
nghiên cứu trên thế giới và tại Việt Nam
1.6. Research gap and rationale for the study / Khoảng trống nghiên cứu và lý do thực hiện đề tài

Background for an international article: 3–5 paragraphs: burden of the problem → what is known → what
is not known (the gap) → study aim.

## References (Vancouver) / Tài liệu tham khảo
Format example from the source (illustrative, copy none into a project; real entries are rendered by
`cite_render.py` from ledger records created by `search_lit.py add`):

```
1. Li A, Wu H, Zhang K, Ying J. Efficacy and hemodynamic safety of perioperative dexmedetomidine for the prevention of postoperative delirium in elderly patients undergoing cardiac surgery: an updated systematic review and meta-analysis of randomized controlled trials. Front Neurol. 2026;17:1895312. doi:10.3389/fneur.2026.1895312. PMID: 42656262.
```

Rules: up to 6 authors list all; more than 6 list the first 6 then "et al."; journal names abbreviated
as the `iso_abbreviation` PubMed returns; numbered in order of first appearance in the text.
