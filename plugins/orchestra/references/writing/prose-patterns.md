# Prose-pattern catalog (P01–P30)

`scripts/lint_prose.py` measures these patterns in academic prose, Vietnamese and English. It counts and reports;
it never rewrites. The ideas are adapted from the humanizer skill (v4.0.0, MIT) and the grand-rounds slop catalog
(owner's MIT code), narrowed to what shows up in theses, abstracts and papers.

Density defaults live in `judgement-defaults.md` ("Prose pattern density"): a paragraph is flagged above 3 hits per
100 words; a document is blocked above 2 per 100 words. A hit is a pattern, not a verdict: a flagged sentence can
stay when the author means it.

| Code | Pattern | Language | Regex/heuristic | Academic exception |
|---|---|---|---|---|
| P01 | "không chỉ … mà còn …", "not only … but also" | vi, en | both halves within one sentence (up to 140 characters apart) | Two truly separate findings joined to correct a belief |
| P02 | "đóng vai trò quan trọng", "plays a crucial/pivotal/key role" | vi, en | role phrase plus an intensifier (quan trọng, then chốt, thiết yếu, quyết định; crucial, pivotal, vital, key) | "đóng vai trò là yếu tố nhiễu" (a defined analytic role) is not matched |
| P03 | Stock scene-setting opener: "Trong bối cảnh", "In the context of", "In today's" | vi, en | at the start of a sentence only | Mid-sentence "in the context of a trial" |
| P04 | "ngày càng", "increasingly", "ever-growing" stacked | vi, en | two or more in one paragraph; every occurrence is a hit | A single use backed by a cited trend |
| P05 | "góp phần", "contributes to (a broader/growing/overall …)" | vi, en | phrase; English only with an inflating continuation | "contributes to the variance" |
| P06 | Summary opener: "Tóm lại,", "In conclusion,", "Overall,", "Ultimately," | vi, en | sentence opener followed by a comma | The standard heading "Kết luận" / "Conclusion" is a heading, never matched |
| P07 | Em-dash or spaced dash overuse | vi, en | more than 2 per paragraph (`—`, `–` between words, ` - `, ` -- `); one hit per paragraph | Numeric ranges (5–10 mg), list markers, minus signs |
| P08 | One-sentence closing paragraph that restates | vi, en | last paragraph of a section, one sentence of at most 35 words, led by "Như vậy", "Do đó", "Thus", "Ultimately", "This shows"; the paragraph before has at least 40 words | A real one-sentence conclusion that adds a claim |
| P09 | Forced triad of stock adjectives ("hiệu quả, an toàn và bền vững") | vi, en | three comma-joined items, at least two on a stock adjective list | A triad of defined variables or outcomes ("age, sex and BMI") |
| P10 | Emphasis opener: "đáng chú ý", "notably", "importantly", "interestingly" | vi, en | sentence opener | None needed; state the point without the opener |
| P11 | "hơn bao giờ hết", "more than ever" | vi, en | phrase | A dated comparison with a number |
| P12 | Stock AI words: delve, tapestry, realm, landscape, underscore, pivotal, seamless, holistic, multifaceted, myriad, intricate, robust; vi: bức tranh toàn cảnh, đa chiều, kỷ nguyên | vi, en | word list; "robust" skipped near statistical terms, "landscape" skipped before orientation/mode/page | "robust standard errors", "robust regression", "landscape orientation" |
| P13 | Filler announcement: "it is worth noting", "it is important to note", "cần lưu ý rằng", "đáng lưu ý là" | vi, en | phrase | A real safety or scope caveat can be stated directly instead |
| P14 | Rhetorical question opener | vi, en | paragraph's first sentence ends with "?" and begins with Why/What/How/Could/Liệu/Tại sao/Làm thế nào | A research question quoted in a protocol or objectives section |
| P15 | Bold label inside prose ("**Điểm mấu chốt:** …") | vi, en | `**Label:**` that is not at paragraph start, or a non-standard label | Structured-abstract labels at paragraph start (Background, Methods, Results, Conclusion, Mục tiêu, Phương pháp, Kết quả, Kết luận) |
| P16 | Staged run-up: "here's the thing", "the truth is", "thành thật mà nói", "sự thật là" | vi, en | phrase | None |
| P17 | Sayings that sound deep: "at its core", "at the heart of", "cornerstone", "xương sống của", "cốt lõi của vấn đề" | vi, en | phrase | A literal anatomy or system "cornerstone of treatment" cited from a guideline |
| P18 | Contrast that argues with nobody: "it's not X, it's Y", "không phải là X, mà là Y" | vi, en | "it's/this is not … , but/it's"; "không phải là … , mà là" | A correction of a belief the text has already quoted |
| P19 | Dramatic fragment run: three one-word sentences in a row ("Fast. Safe. Cheap.") | vi, en | three capitalised words of 3–12 letters each ending in a full stop | Abbreviation lists, table captions |
| P20 | Repeated sentence openings | vi, en | three consecutive sentences with the same first word (3+ letters), except nhóm/group/bệnh nhân/patients/we/the/this/các | Parallel results sentences that name different groups |
| P21 | Intensifier padding: "vô cùng quan trọng", "incredibly …", "extremely …" | vi, en | intensifier plus a vague adjective; "extremely preterm/low/rare/obese" skipped | Clinical categories (extremely low birth weight) |
| P22 | Inflated significance: "a testament to", "marks a pivotal moment", "paradigm shift", "đánh dấu bước ngoặt" | vi, en | phrase | None |
| P23 | Promotional vocabulary: groundbreaking, cutting-edge, state-of-the-art, revolutionary, transformative, đột phá, tiên tiến hàng đầu | vi, en | word list | "state-of-the-art" in a named benchmark title |
| P24 | Trailing "-ing" gloss: ", highlighting the importance of …", ", qua đó góp phần …" | vi, en | comma plus highlighting/underscoring/emphasizing/showcasing/fostering plus an inflating noun | A participial phrase that names a measured result |
| P25 | Vague attribution: "studies show", "experts believe", "nhiều nghiên cứu cho thấy" | vi, en | phrase in a sentence with no citation marker (`[@…]`, `[1]`, `(Author 2020)`, `{{…}}`) | Any sentence that carries a citation |
| P26 | Inflated copula: "serves as a testament/reminder/cornerstone", "là một minh chứng/cầu nối" | vi, en | phrase | "serves as the reference category" |
| P27 | Chatbot residue: "I hope this helps", "let me know if", "as an AI", "dưới đây là tổng quan" | vi, en | phrase | None |
| P28 | Padding: "due to the fact that", "at this point in time", "has the ability to", "nhằm mục đích", "tại thời điểm hiện tại" | vi, en | phrase | "in order to" is not counted; it is ordinary academic English |
| P29 | Emoji or pictograph in prose | any | Unicode pictograph ranges | None |
| P30 | Hopeful future closer: "the future looks bright", "tương lai đầy hứa hẹn", "mở ra nhiều cơ hội mới" | vi, en | phrase | "Further research is needed to …" is a standard limitation and is not matched |

## Slide checks (`lint_prose.py --slides`)

| Code | Check | Heuristic |
|---|---|---|
| S17 | Topic title instead of a claim | A title of at most 4 words with no verb or copula from a small vi/en list ("Results", "Kết quả chính"); a PPTX title-slide layout is skipped |
| S20 | Explaining the obvious | "This chart shows", "As shown in the figure", "Biểu đồ này cho thấy" |
| S21 | Hype without a hedge in a medical claim | "dramatically improves", "cures", "proven to", "vượt trội", "rõ rệt" in a sentence with no hedge (may, suggests, có thể, gợi ý) |

Speaker notes are never read.

## Academic exceptions (never counted)

The linter has no pattern for any of these, and a new pattern must not catch them:

- Passive voice ("was assessed", "được ghi nhận"); it is the normal voice of a methods section.
- Hedges: may, might, could, suggest, appear, possibly, có thể, gợi ý, có xu hướng, dường như. Calibrated language
  is a requirement, not a tell.
- Reporting-guideline wording (STROBE, CONSORT, PRISMA and similar item phrases) and "Further research is needed".
- Standard headings: Limitations, Hạn chế, Kết luận, Kiến nghị, Conclusion, and structured-abstract labels.
- Defined abbreviations and statistical terms (robust standard errors, extremely preterm).
- Headings, table rows, fenced code, HTML comments and `{{R-…}}` placeholders: skipped before any matching.

Word counts (`--count-words`) leave out headings, tables, code, comments, citation groups (`[@key]`) and a leading
`**Label:**`; a placeholder counts as one word.
