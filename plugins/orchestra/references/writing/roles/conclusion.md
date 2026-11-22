orchestra-role: conclusion

# Role: conclusion (Kết luận, Kiến nghị / Conclusion)

## Output files
- Thesis: `06_writing/thesis/05-ket-luan.md` and `06-kien-nghi.md`. Manuscript: `06_writing/manuscript/06-conclusion.md`.

## Shape
- One conclusion per objective in `01_question/question.md`, same order and numbering.
- Each conclusion ends with the ledger ids it rests on, in an HTML comment:
  `<!-- results: R-A1-004 -->`.
- Numbers only as `{{R-…}}` placeholders, for example `{{R-A1-004.full}}`.
- Kiến nghị, practice: drawn from the results and the limitations only, within the studied population.
- Kiến nghị, research: drawn from the limitations and from the gap named in Chương 1.
- Manuscript: one paragraph.

## Never
- Causal verbs for observational designs (gây ra, dẫn đến, làm tăng, làm giảm, causes, leads to, increases).
  Write "liên quan" / "associated with".
- An ordered trend unless a ledger row reports a trend test.
- Generalisation beyond the studied population.
- A claim stronger than the evidence supports.

## Rules
- If the CI includes the null, say the association was not shown and the estimate is imprecise.
- If an objective was not met, say so.
- A conclusion resting on a `POST-HOC` or `DEVIATION` result is labelled exploratory.
- No citations (no `[@id]`), no new data, no speculation.
- Do not repeat the discussion. State what the data support and stop.

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
