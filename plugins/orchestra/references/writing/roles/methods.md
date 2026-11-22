orchestra-role: methods

# Role: methods (Chương 2 / Methods)

## Sources
- `03_protocol/protocol.md`, **Part B only**. Do not copy Part A (quick summary) or Part C (handoff).
- `03_protocol/sap.md`, `03_protocol/sample-size.md`, `03_protocol/variables.md`.
- `decisions.md`: lines starting `POST-HOC A<n>:` and `DEVIATION A<n>:`.
- `python "${CLAUDE_PLUGIN_ROOT}/scripts/analysis_plan.py" register .` lists the prespecified register only.
  Deviations and post-hoc analyses come from `decisions.md`, not from the register.
- `05_analysis/output/results.json → engine` for the software name.

## Output files
- Thesis: `06_writing/thesis/ch2-methods.md`. Manuscript: `06_writing/manuscript/03-methods.md`.

## Shape
- Thesis: 2.1 Đối tượng nghiên cứu (tiêu chuẩn lựa chọn, tiêu chuẩn loại trừ); 2.2 Thời gian và địa điểm;
  2.3 Phương pháp nghiên cứu (thiết kế; cỡ mẫu và chọn mẫu; biến số và định nghĩa; công cụ và quy trình thu thập;
  xử lý và phân tích số liệu; kiểm soát sai số); 2.4 Đạo đức nghiên cứu.
- Manuscript: follow the Methods items of the reporting guideline in order (design, setting, participants,
  variables, data sources, bias, study size, quantitative variables, statistical methods, ethics).

## Rules
- Use the past tense throughout ("đã thu thập", "were collected").
- State every deviation and post-hoc analysis with its reason in a labelled paragraph: "Thay đổi so với đề cương" /
  "Changes from the protocol".
- Statistical methods match the register row by row.
- Sample-size numbers carry `<!-- not-a-result: sample-size.md -->`. Any result is a `{{R-…}}` placeholder.
- Ethics approval body and number only as the author wrote them; otherwise `[[TÁC GIẢ: …]]`.
- Cite methods papers or tools only with `[@id]` from the ledger.

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
