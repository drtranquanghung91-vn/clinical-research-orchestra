# Manuscript: IMRaD files, journal rules, declarations

Read before drafting or assembling a manuscript (`assemble.py <project> manuscript`).

## 1. Files in `06_writing/manuscript/`
| File | Content | Role brief |
|---|---|---|
| `00-title.md` | title naming the design, running title, authors, corresponding author, word counts, keywords | none |
| `01-abstract.md` | structured abstract | `roles/abstract.md` |
| `02-introduction.md` | 3 to 4 paragraphs | `roles/introduction.md` |
| `03-methods.md` | follows the reporting guideline | `roles/methods.md` |
| `04-results.md` | key estimates, Table 1 baseline | `roles/results.md` |
| `05-discussion.md` | six-part order | `roles/discussion.md` |
| `06-conclusion.md` | one paragraph | `roles/conclusion.md` |

This is the IMRaD order. Declarations follow the conclusion.

## 2. Title page
- The title names the design. Write `[[AUTHOR: authors and affiliations]]`, the corresponding author and
  the funding line as placeholders for the author. Never invent them.
- Word counts: abstract against `target.word_limit` (default 250 when null), main text against `target.text_words`
  or the journal's limit. When the limit is unknown, ask the author once. Count with
  `python "${CLAUDE_PLUGIN_ROOT}/scripts/lint_prose.py" --count-words <file>`.

## 3. Journal rules
Read `project.yaml → target.journal` and ask the author: reference style, abstract headings, limit on tables and
figures. This pipeline renders Vancouver only. If the journal wants another style, report it as a limitation.

## 4. Sections
- A structured abstract uses the journal's headings, else Background, Methods, Results, Conclusions (vi: Mục tiêu, Đối tượng và phương pháp, Kết quả, Kết luận).
- Introduction: funnel from burden to gap to aim.
- Methods: items of the guideline in order.
- Results: key estimates only. Tables and figures are numbered across the paper (Table 1, Figure 1; vi: Bảng 1, Hình 1).
- Discussion: the order in `roles/discussion.md`.
- Conclusion: one paragraph, answering the objectives.

## 5. Declarations
Write each as a placeholder the author completes: `[[AUTHOR: ethics approval body and number]]`,
`[[AUTHOR: consent]]`, `[[AUTHOR: funding]]`, `[[AUTHOR: conflicts of interest]]`, `[[AUTHOR: data availability]]`,
`[[AUTHOR: author contributions]]`. The AI-use statement comes from `out/ai-use-disclosure.md` (see `ai-disclosure.md`).

## 6. Language
The manuscript follows `target.language` when set, else `language.output`. For an English manuscript in a Vietnamese
project, set `target.language: en` and run `assemble.py … --lang en`. The fictional cohort example is a Vietnamese
manuscript for a domestic journal (spec decision 10).
