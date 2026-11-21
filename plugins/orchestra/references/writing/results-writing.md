# Writing results: patterns and wording

Used by `results-writing` for thesis Chapter 3 and manuscript Results. Vietnamese Chapter 3 layout:
`vn-chapter3.md` (same folder). Full procedure and the check sequence:
`${CLAUDE_PLUGIN_ROOT}/references/workflows/results-writing.md`.

Every number below is a placeholder from `ledgers/results-ledger.json`: `{{R-A1-001}}` (value),
`{{R-A1-001.ci}}`, `{{R-A1-001.p}}`, `{{R-A1-001.n}}`, `{{R-A1-001.count}}`, `{{R-A1-001.full}}`.
`render_results.py` formats them by `kind` (OR/MD 2 decimals, percent and mean 1 decimal, p 3 decimals or
`< 0.001`, `.count` an integer with 0 decimals and no thousands separator, decimal comma in Vietnamese, CI
with an en dash). A range with a negative bound uses " to " (English) or " đến " (Vietnamese) instead of
the en dash (`-1.20 to -0.50`; `-0,18 đến 1,42`) so the minus sign is not read as a dash; write the same
way in prose. What `.full` gives:

| kind | `.full` (en) | `.full` (vi) |
|---|---|---|
| or, rr, hr, md, rd, beta, auc with a CI | `1.84 (95% CI 1.21–2.79)` | `1,84 (KTC 95%: 1,21–2,79)` |
| mean with SD | `61.4 ± 10.2` | `61,4 ± 10,2` |
| median with IQR | `7.0 (5.0–11.0)` | `7,0 (5,0–11,0)` |
| percent with count | `63 (31.5%)` | `63 (31,5%)` |
| percent with count and CI | the CI form, not the count: take the count from `.count` | same |

## 1. Paragraph pattern

One paragraph per analysis, in register order: (1) what was compared, in whom; (2) the estimate with its
CI, then p; (3) at most one plain sentence on direction and precision. No interpretation, mechanism or
comparison with other studies: that is Discussion.

Estimate-first sentence templates:

| Situation | English | Tiếng Việt |
|---|---|---|
| Proportion by group | Readmission occurred in {{R-A1-002.full}} patients in group A and {{R-A1-003.full}} in group B. | Tỷ lệ tái nhập viện là {{R-A1-002}} ở nhóm A và {{R-A1-003}} ở nhóm B. |
| Ratio measure | X was associated with higher odds of Y (adjusted OR {{R-A1-001}}, 95% CI {{R-A1-001.ci}}; p = {{R-A1-001.p}}). | X liên quan với tỷ số chênh Y cao hơn (OR hiệu chỉnh {{R-A1-001}}; KTC 95%: {{R-A1-001.ci}}; p = {{R-A1-001.p}}). |
| Mean difference | The mean Y was {{R-A2-001}} units higher in group A (95% CI {{R-A2-001.ci}}; p = {{R-A2-001.p}}). | Y trung bình ở nhóm A cao hơn {{R-A2-001}} đơn vị (KTC 95%: {{R-A2-001.ci}}; p = {{R-A2-001.p}}). |
| Derived difference | … an absolute difference of 11.2 <!-- derived: R-A1-002 - R-A1-003 --> percentage points. | … chênh lệch 11,2 <!-- derived: R-A1-002 - R-A1-003 --> điểm phần trăm. |

In Vietnamese, OR is "tỷ số chênh" (define it in the table's `Ghi chú:`); never write "odds" in Vietnamese
text. Prefer a placeholder to a `derived` comment (counts: `.count`; CI bounds are in `.ci`). A `derived`
comment must name its ledger ids (`R-A1-002 - R-A1-003`, parts `.value|.n|.count|.p|.lo|.hi`); a pure
formula is evaluated and must equal the printed number at its decimals, and a comment with no id blocks.
Put a `derived` or `not-a-result` marker right after the number (before any unit word), or
`check_numbers.py` cannot see it. Integers 1900–2100 are read as years and not checked: write a cohort
size in that range through a placeholder.

## 2. Wording by confidence interval

| The 95% CI … | Write | Do not write |
|---|---|---|
| excludes the null (1 for ratios, 0 for differences) | "was associated with higher odds (OR …, 95% CI …)"; "… cao hơn (OR …; KTC 95%: …)" | "significantly higher" without the estimate; "proves"; causal verbs (observational design) |
| includes the null, and is narrow around it | "the CI is compatible with at most a small difference (…–…)"; "KTC tương thích với khác biệt nhỏ hoặc không có khác biệt" | "there was no difference"; "không có sự khác biệt" as a finding |
| includes the null and is wide | "the estimate was imprecise; the data are compatible with anything from a … to a …"; "ước lượng kém chính xác (KTC rộng); KTC tương thích với cả … lẫn …" | "no effect"; "a trend towards significance"; "gần có ý nghĩa thống kê" |
| excludes the null but is wide | "associated with higher odds, though the estimate was imprecise (…)" | "a strong effect" from the point estimate alone |

Observational designs (cohort, case-control, cross-sectional, diagnostic accuracy, prediction model):
"associated with", "liên quan với", "higher/lower in", never "causes", "leads to", "prevents", "gây ra",
"dẫn đến", "làm tăng", "làm giảm", "phòng ngừa" (`analysis_plan.py check --text` warns on these).

## 3. Post-hoc and deviations

Own subsection after the secondary results, heading labelled ("Exploratory post-hoc analyses" / "Phân
tích thăm dò (hậu kiểm)"). Every paragraph that uses a `posthoc` result says so again in the same paragraph
(`analysis_plan.py check --text` blocks it otherwise):
- "In an exploratory post-hoc analysis, not specified in the analysis plan, …; this finding needs
  confirmation."
- "Phân tích thăm dò (hậu kiểm), không có trong kế hoạch phân tích, cho thấy …; kết quả này chỉ mang tính
  tạo giả thuyết."

Subgroups: the effect in each subgroup plus the p for interaction, never a separate significance claim per
subgroup. A deviation states what changed (from its `DEVIATION A<n>:` line), and every paragraph or table
that uses a `deviation` result says so ("deviating from the analysis plan", "thay đổi so với kế hoạch
phân tích"); it is never reported as the primary result without that label.

## 4. What not to do

- Repeat a whole table in prose: give 2–4 key numbers and point to the table.
- Report p alone ("p = 0.004") or "significantly higher" without the estimate and CI.
- "Trend towards significance", "borderline significant", "gần có ý nghĩa".
- "No difference" or "không khác biệt" from p ≥ 0.05.
- Baseline p-values in an RCT; percentages without their denominator in a table.
- Type a number, even one copied from the ledger: use the placeholder.

## 5. Before and after (fictional ids)

Fictional cohort, `design: cohort`, English text (`--lang en`); `R-A3-…` are `posthoc` (declared in
`decisions.md`). The blocks below are checked with the scripts (expected output in the workflow, section 7).

Before:

```markdown
Of {{R-A0-001}} patients, 31.6% of those with HbA1c ≥ 8% were readmitted. High HbA1c leads to readmission (p = {{R-A1-001.p}}), and readmission was significantly higher in this group.

Length of stay showed a trend towards significance (p = {{R-A2-001.p}}), so there was no difference between the groups.

Among women, the odds of readmission were {{R-A3-001.full}}.
```

What the checks and the reviewer find:
- `check_numbers.py` (rendered file): E-NUM block on "31.6%" (the ledger has 31.5) and on "8%" (a cut-off
  with no `not-a-result` marker).
- `analysis_plan.py check --text`: E-STAT block, `R-A3-001` is post-hoc but not labelled; E-STAT warn,
  causal "leads to" in a cohort.
- Reviewer only (no script catches these): p without the estimate, "significantly higher" without a
  number, "trend towards significance", "no difference" from a non-significant p.

After:

```markdown
Of the {{R-A0-001}} patients analysed, readmission within one year occurred in {{R-A1-002.full}} of those with HbA1c ≥ 8% <!-- not-a-result: exposure cut-off --> and in {{R-A1-003.full}} of those with lower HbA1c, an absolute difference of 11.2 <!-- derived: R-A1-002 - R-A1-003 --> percentage points. After adjustment for age and sex, HbA1c ≥ 8% <!-- not-a-result: exposure cut-off --> was associated with higher odds of readmission (adjusted OR {{R-A1-001}}, 95% CI {{R-A1-001.ci}}; p = {{R-A1-001.p}}).

The mean index length of stay was {{R-A2-001}} days longer in the higher-HbA1c group (95% CI {{R-A2-001.ci}}; p = {{R-A2-001.p}}); the interval is compatible with a slightly shorter to a moderately longer stay.

In an exploratory post-hoc analysis by sex, suggested by the supervisor after the primary analysis and not specified in the analysis plan, the adjusted OR was {{R-A3-001.full}} in women and {{R-A3-002.full}} in men (p for interaction = {{R-A3-003}}); this difference may be due to chance and needs confirmation.
```

In the .docx (comments removed), the first sentence reads: "Of the 412 patients analysed, readmission
within one year occurred in 63 (31.5%) of those with HbA1c ≥ 8% and in 43 (20.3%) of those with lower
HbA1c, an absolute difference of 11.2 percentage points."
