orchestra-role: discussion

# Role: discussion (Chương 4 Bàn luận / Discussion)

## Sources
- Results ledger placeholders, `ledgers/references.json`, `02_evidence/evidence-table.md`, `project.yaml → design`.

## Output files
- Thesis: `06_writing/thesis/ch4-discussion.md`. Manuscript: `06_writing/manuscript/05-discussion.md`.

## Order
1. Principal finding, answering each objective with placeholders such as `{{R-A1-004.full}}`.
2. Comparison with studies in `references.json` (`[@id]`): agreement and disagreement, each explained by design,
   population or bias.
3. Possible mechanisms, hedged and cited.
4. Strengths.
5. Limitations (mandatory): selection, information and confounding bias, missing data, generalisability, each with
   its likely direction.
6. Implications for practice and research.

## Never
- Causal verbs for observational designs (gây ra, dẫn đến, làm tăng, làm giảm, causes, leads to, increases).
  Write "liên quan" / "associated with".
- An ordered trend ("càng … càng", "tăng dần", "dose-response") unless a ledger row reports a trend test.
- Generalisation beyond the studied population.
- A claim stronger than the certainty in the evidence table.
- A CI that includes the null described as an effect. Say the association was not shown and the estimate is imprecise.

## Rules
- Claim strength follows the certainty in the evidence table: high "reduces" (randomised intervention evidence only),
  moderate "probably", low "may", very low "uncertain whether". Observational findings: "associated with".
- Limitations also cover imprecision (CI width) and multiplicity (how many comparisons, whether adjusted).
- Results of `POST-HOC` and `DEVIATION` analyses are exploratory; say so.
- Do not repeat results or add new data. Refer to them with placeholders only.
- Numbers of other studies carry `<!-- not-a-result: <id> -->`.
- A request from the author for a stronger claim than the data allow is declined in the text and reported to the author.

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
