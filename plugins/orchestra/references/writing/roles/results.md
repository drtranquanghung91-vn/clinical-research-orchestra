orchestra-role: results

# Role: results (Chương 3 / Results)

Use the Skill tool with `results-writing`. It writes from ledger placeholders only. The rules in
`${CLAUDE_PLUGIN_ROOT}/references/writing/results-writing.md` and `vn-chapter3.md` apply unchanged.

## Output files
- Thesis: `06_writing/thesis/ch3-results.md` (reuse the accepted draft; do not rewrite it).
- Manuscript: `06_writing/manuscript/04-results.md`. Key estimates only. Do not repeat a table in prose.
  Number tables and figures across the paper.

## Rules
- Every number is a `{{R-…}}` placeholder, for example `{{R-A1-004.full}}`, or carries a `derived` comment.
- Figures are image lines with the path of `07_present/figures/F<n>.png` relative to the draft:
  `![Biểu đồ 3.1. …](../../07_present/figures/F1.png)` for a chart (`Hình 3.1.` for a diagram or photograph).
- Mention a table in the text before it appears.
- No interpretation here; it belongs to the discussion. Citations, if any, are `[@id]` from the ledger.

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
