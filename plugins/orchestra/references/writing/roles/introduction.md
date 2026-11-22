orchestra-role: introduction

# Role: introduction (Đặt vấn đề / Introduction)

## Sources
- `01_question/question.md` (objectives, copied verbatim).
- The gap: thesis `06_writing/thesis/ch1-*.md`, section "Khoảng trống", or `02_evidence/gaps.md`.
- `ledgers/references.json` (every `[@id]` comes from here) and `02_evidence/evidence-table.md`.

## Output files
- Thesis: `06_writing/thesis/00-dat-van-de.md`.
- Manuscript: `06_writing/manuscript/02-introduction.md`. It builds on `literature-review` mode b, which writes the same file.

## Shape
- Thesis: the clinical problem and why it matters in this setting; what is known (synthesised by theme, cited with
  `[@id]`); what is not known (the gap); why this study; then the heading "Mục tiêu nghiên cứu" with the objectives
  numbered and copied verbatim.
- Manuscript: 3 to 4 paragraphs. Burden, then what is known, then the gap, then the aim in the last sentence.

## Rules
- No results of this study.
- Claim strength follows the certainty in the evidence table: high "reduces", moderate "probably", low "may",
  very low "uncertain whether". Causal verbs such as "reduces" are for randomised evidence of an intervention only.
  For observational exposure-outcome evidence, even at high certainty, write "associated with".
- Synthesise by theme. Never go paper by paper (`review_lint.py` E-LIT).
- Do not restate Chương 1 at length.

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
