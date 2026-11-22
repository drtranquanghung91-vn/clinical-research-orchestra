# Vietnamese thesis: structure, numbering, references

Read before drafting or assembling a thesis (`assemble.py <project> thesis`). Section names stay in Vietnamese.

## 1. Order of the whole thesis
1. Bìa chính, bìa phụ
2. Lời cam đoan
3. Lời cảm ơn
4. Mục lục
5. Danh mục chữ viết tắt
6. Danh mục bảng
7. Danh mục hình / biểu đồ
8. Tóm tắt (optional; `00-tom-tat.md`, role `abstract`)
9. Đặt vấn đề (ends with "Mục tiêu nghiên cứu")
10. Chương 1. Tổng quan tài liệu
11. Chương 2. Đối tượng và phương pháp nghiên cứu
12. Chương 3. Kết quả nghiên cứu
13. Chương 4. Bàn luận
14. Kết luận
15. Kiến nghị
16. Tài liệu tham khảo
17. Phụ lục: the reporting-guideline checklist (STROBE or the matching one), the case report form, the data dictionary.
    Never patient data or identifiers.

## 2. Who writes what
- Orchestra drafts the files named in `references/writing/roles/`: Đặt vấn đề, Chương 1 (literature review),
  Chương 2, Chương 3, Chương 4, Kết luận, Kiến nghị, and optionally Tóm tắt.
- The author or the institution template supplies the cover pages, Lời cam đoan, Lời cảm ơn and the abbreviation
  list. See `institution.template` in `project.yaml` and `templates/thesis/README.md`. Write
  `[[TÁC GIẢ: …]]` where the author must fill in text.
- Mục lục is a `{TOC}` field that `assemble.py` inserts. Lists of tables and figures are inserted in Word from the
  `caption` and `figure caption` styles.

## 3. Numbering
- Headings: `1.1.`, `1.1.1.`, down to four levels (`####`). Chapter numbers restart the numbering of tables and figures.
- Table captions go above the table: `Bảng 3.1. <tiêu đề>`. A `Nguồn:` line and a `Ghi chú:` line sit directly below it.
- Figure captions go below the image: `Hình 3.1. <tiêu đề>` for diagrams and photographs,
  `Biểu đồ 3.1. <tiêu đề>` for charts. Hình and Biểu đồ are separate sequences (decision D9). Bảng is one sequence.
- Mention each table or figure in the text before it appears.
- Appendix captions (files `9*`) are not sequence-checked. A line with `<!-- fmt-ok: reason -->` is skipped, for example
  when the text mentions another paper's figure.

## 4. References
- Numbered by first citation: `[1]`, `[1–3]`. `cite_render.py` does the numbering from `[@id]` keys.
- One list for the whole thesis, headed "TÀI LIỆU THAM KHẢO", placed before Phụ lục.
- Vietnamese author names in full; other names in Vancouver style.
- Institution-specific sort orders (Vietnamese sources first, then foreign) are a known limitation. Tell the author.

## 5. Page setup
Defaults come from `project.yaml → docx`: Times New Roman 13 pt, line spacing 1.5, margins 2 / 2 / 3 / 2 cm
(top / bottom / left / right), A4, page numbers bottom centre. The institution template overrides these.

## 6. Language rules
- Decimal comma in Vietnamese text (`render_results.py` does this for placeholders).
- "KTC 95%" for the confidence interval, "tỷ số chênh" for OR. Units with a space (`5 mg`).
- Define each abbreviation at first use and list it in the abbreviation list.
- In Chương 2 and Chương 3 describe completed actions with wording such as "đã thu thập", "đã phân tích". This is wording guidance, not a tense rule.
