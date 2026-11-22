orchestra-role: abstract

# Role: abstract (Tóm tắt / Abstract)

Written last, from the finished sections.

## Output files
- Thesis: `06_writing/thesis/00-tom-tat.md` (Tóm tắt, optional).
- Manuscript: `06_writing/manuscript/01-abstract.md`.

## Shape
- Structured headings. vi: Mục tiêu, Đối tượng và phương pháp, Kết quả, Kết luận.
  en: Background, Methods, Results, Conclusions, or the journal's own headings.
- Name the design in the first sentence (STROBE item 1a or the matching guideline item).
- Results as `{{R-….full}}` placeholders, for example `{{R-A1-004.full}}`.
- Manuscript: add a keywords line.

## Rules
- Word limit is `target.word_limit`. When it is null, use the default of 250 (`judgement-defaults.md`).
  Count with `python "${CLAUDE_PLUGIN_ROOT}/scripts/lint_prose.py" --count-words <file>`.
- No citation (no `[@id]`). Nothing that is not in the finished sections.

## Shared rules (every role)
- Every number from results is a `{{R-…}}` placeholder (parts value, ci, p, n, count, full) or carries
  `<!-- derived: R-… expression -->`; any other number carries `<!-- not-a-result: source -->` right after it
  (another study, eligibility, dates, sample-size calculation). Never type a number from memory.
- Every citation is `[@id]` from `ledgers/references.json`; never an id that is not there, never a reference,
  PMID or DOI from memory. No citation inside an HTML comment.
- Captions are typed and checked by `assemble.py` (E-FMT): thesis "Bảng c.n." above tables, "Hình c.n." or
  "Biểu đồ c.n." in an image line `![Hình 3.1. …](figure.png)`; manuscript "Table n." / "Figure n." (vi: "Bảng n.",
  "Hình n.") across the paper; every mention points to an existing caption.
- Facts only the author knows (ethics approval number, funding, affiliations, dates not in the project) are
  written `[[TÁC GIẢ: …]]` / `[[AUTHOR: …]]` and listed for the author; never invented.
- Language: `project.yaml → language.output` (manuscript: `target.language` when set).
