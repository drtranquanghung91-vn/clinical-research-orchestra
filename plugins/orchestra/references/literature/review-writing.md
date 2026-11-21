# Writing a literature review: method and examples

All citation keys below (`[@a2019]` and so on) are fictional and only illustrate the form.

## 1. Thematic synthesis method
1. Cluster the rows of `02_evidence/evidence-table.md` by question (for example: how common is it, what
   raises the risk, does the intervention work, how is it measured), not by author or year.
2. For each cluster write down five things before drafting: the pooled direction, the range of effects,
   the certainty (GRADE from the evidence table), the main disagreement, and its likely reason (design,
   population, risk of bias, measurement, setting).
3. Order clusters from background to the gap: burden, mechanism or risk, what has been tried, what is
   still unknown.
4. Draft one paragraph per claim, then check that the gap paragraph follows from the earlier ones.

## 2. Paragraph template
**Claim** (one sentence, strength set by certainty), then **evidence with comparison** (the studies that
agree, the ones that differ, and the reason), then **qualification** (certainty, limits, applicability to
this population), then **link** (what this leaves open, leading to the next paragraph).

## 3. Before and after
`review_lint.py` flags a paragraph when at least two sentences, and half or more of them, open with an
author or study as the subject; a file blocks (E-LIT) when at least two paragraphs and 30% of prose
paragraphs are flagged. Each "before" below has two flagged paragraphs and blocks on its own.

### English
Before (paper by paper, flagged):

```text
Smith et al. (2019) [@a2019] studied 120 adults with condition X and found that drug D lowered pain scores. Jones and Lee (2020) [@b2020] enrolled 300 patients and reported a non-significant difference between drug D and placebo.

In a 2021 study by Park [@c2021], 85 patients on drug D improved at six weeks. Nguyen et al. (2022) [@d2022] found a modest benefit in 210 older adults.
```

After (thematic, passes):

```text
Drug D may reduce pain in adults with condition X, although the trials disagree. Three of four trials found lower scores on drug D [@a2019; @c2021; @d2022], whereas the largest trial's estimate was imprecise, with a confidence interval compatible with both benefit and harm (for example, a mean difference of -0.3 points, 95% CI -1.2 to 0.6) [@b2020]. The null trial enrolled people with longer disease duration and used a 12-week endpoint, while the positive trials measured at six weeks, so the benefit may fade or may be limited to early disease. Certainty is low because of small samples and unblinded outcome assessment in two trials. No trial studied the Vietnamese outpatient setting, which leaves the question open for this study.
```

### Vietnamese
Trước (theo từng bài, bị đánh dấu):

```text
Nghiên cứu của Nguyễn và cộng sự (2019) [@a2019] trên 120 người lớn mắc bệnh X cho thấy thuốc D làm giảm điểm đau. Theo nghiên cứu của Trần (2020) [@b2020], 300 bệnh nhân có chênh lệch không có ý nghĩa thống kê giữa thuốc D và giả dược.

Năm 2021, tác giả Lê [@c2021] ghi nhận 85 bệnh nhân dùng thuốc D cải thiện sau sáu tuần. Tác giả Phạm [@d2022] báo cáo lợi ích nhỏ ở 210 người cao tuổi.
```

Sau (theo chủ đề, đạt):

```text
Thuốc D có thể làm giảm đau ở người lớn mắc bệnh X, nhưng các thử nghiệm chưa thống nhất. Ba trong bốn thử nghiệm ghi nhận điểm đau thấp hơn ở nhóm dùng thuốc D [@a2019; @c2021; @d2022], trong khi ước lượng của thử nghiệm lớn nhất thiếu chính xác, khoảng tin cậy phù hợp với cả lợi ích lẫn tác hại (ví dụ chênh lệch trung bình -0,3 điểm, KTC 95% từ -1,2 đến 0,6) [@b2020]. Thử nghiệm âm tính tuyển người bệnh có thời gian bệnh dài hơn và đo ở tuần 12, còn các thử nghiệm dương tính đo ở tuần 6, nên lợi ích có thể giảm dần hoặc chỉ giới hạn ở giai đoạn sớm. Độ chắc chắn thấp do cỡ mẫu nhỏ và đánh giá kết cục không làm mù ở hai thử nghiệm. Chưa có thử nghiệm nào thực hiện trên người bệnh ngoại trú tại Việt Nam, đây là khoảng trống mà nghiên cứu này hướng tới.
```

## 4. Hedging by certainty (GRADE)
| Certainty | English | Tiếng Việt |
|---|---|---|
| High | reduces, increases, is associated with | làm giảm, làm tăng, có liên quan đến |
| Moderate | probably reduces, likely | nhiều khả năng làm giảm, thường |
| Low | may reduce, suggests | có thể làm giảm, gợi ý |
| Very low | it is uncertain whether | chưa rõ liệu |

Hedge by certainty, not by the writer's mood. Never write "no difference" from a non-significant p;
report the interval and which effect sizes it excludes.

## 5. What not to do
- Quote abstracts or paste their sentences; paraphrase and compare.
- List sample sizes study by study; give them only when they explain a disagreement.
- Cite a review for a primary finding; cite the primary study, or say "a review reported".
- Cite a retracted or unverified work. Any `verify_refs.py` status other than VERIFIED or MANUAL must be
  resolved first.
- Cite a MANUAL record (author-supplied, no PMID or DOI, added with `search_lit.py add-manual`) for more
  than the author's own copy shows, and tell the author it is listed as not machine-verifiable.
