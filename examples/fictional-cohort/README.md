# Fictional cohort: a simulated P1 project

**Everything in this folder is simulated for demonstration.** The author ("Example author"), the
site ("Bệnh viện Mô phỏng", a fictional provincial hospital), the study period and the expected
recruitment were invented to drive the skills. No patient data was entered or used at any point.
The literature references are real records retrieved from PubMed during the run and verified by
`verify_refs.py`; the sample-size parameters that have no source are labelled GIẢ ĐỊNH (assumption).

The project is a Vietnamese master's thesis plan: *HbA1c lúc nhập viện và nguy cơ tái nhập viện
trong 1 năm ở người bệnh đái tháo đường type 2 xuất viện tại Bệnh viện Mô phỏng (2021–2023): một
nghiên cứu đoàn hệ hồi cứu* (admission HbA1c and 1-year readmission in adults with type 2 diabetes,
a retrospective cohort). Output language `vi`, chat language `vi`, design `cohort`, reporting
guideline STROBE.

## How it was produced (21 November 2026)

The project was created outside the repository and driven with non-interactive Claude Code runs,
one conversation carried through with `--continue`, then copied here without the run transcripts.

```bash
python plugins/orchestra/scripts/init_project.py <dest>/fictional-cohort \
  --title "Glycaemic control and 1-year readmission in adults with type 2 diabetes: a retrospective cohort (simulated)" \
  --type thesis-masters --design cohort --output-lang vi --chat-lang vi
cd <dest>/fictional-cohort
claude -p "<stage prompt>" [--continue] --model sonnet \
  --plugin-dir "$REPO/plugins/orchestra" --plugin-dir "$REPO/plugins/phi-guard" \
  --allowedTools "Bash,Read,Write,Edit,Glob,Grep,Skill" --setting-sources "" --strict-mcp-config \
  --mcp-config '{"mcpServers":{}}' --no-chrome --output-format stream-json --verbose < /dev/null > ../stage-N.jsonl
```

Claude Code 2.1.226, model Sonnet. Every stage's init event was clean (`plugins: orchestra, phi-guard`;
`mcp_servers: []`; a fresh memory folder), checked with `tests/scenarios/summarize_run.py`. No
phi-guard or permission denials occurred.

| Stage | Prompt (short form) | Skill used | Files written |
|---|---|---|---|
| 1 | `/orchestra:start` | research-project-setup (resume) | none; reported gates G1–G4 closed, ledgers clean, next skill research-question |
| 2 | the six intake facts (idea, site, purpose, 12 months, EMR + HIS 2021–2023, ~600 discharges a year) | research-question | `01_question/question.md`, 3 references added and verified |
| 3 | answers to the three confirmation items, title option 2, "G1 opened", then a full literature search | literature-search (with critical-appraisal of all 5 records, step 4c) | `02_evidence/search-strategy.md`, `evidence-table.md`, `evidence-map.md`, `gaps.md`, `appraisal/*.md` |
| 4 | `/orchestra:appraise` on hu2026 (PMID 42068438) and robbins2021 (PMID 33948220), then guideline-check | critical-appraisal, guideline-check | `02_evidence/appraisal/hu2026.md`, `robbins2021.md` (rewritten, ROBINS-E), `02_evidence/guidelines.md`, ADA 2026 §16 added |
| 5 | `/orchestra:review` mode a (thesis Chapter 1) | literature-review | `06_writing/thesis/ch1-literature-review.md` and its `.numbered.md` render, `ledgers/outline.json`, `ledgers/claims.json` |
| 6 | site, period, ~50 discharges a month, no randomisation, EMR + HIS only, small budget | protocol-design | `03_protocol/protocol.md`, `03_protocol/variables.md` |
| 7 | answers to the three protocol items, then sample size and SAP ("label unsourced parameters as assumptions, do not ask again") | sample-size-sap | `03_protocol/sample-size.md`, `03_protocol/sap.md` |
| 8 | "protocol, sample size and SAP approved, G2 opened" | none (STATUS, decisions, gate and ledger checks) | `STATUS.md`, `decisions.md` |

The author's approvals were the author's own acts: `gate.py open <project> G1 --by "Example author"`
before stage 3 and `gate.py open <project> G2 --by "Example author"` before stage 8, run outside the
agent.

## Checks (run from the repository root)

| Command | Exit | Result |
|---|---|---|
| `python plugins/orchestra/scripts/crolib/ledgers.py check examples/fictional-cohort` | 0 | `ledgers: 0 problems` |
| `python plugins/orchestra/scripts/verify_refs.py examples/fictional-cohort --cite examples/fictional-cohort/06_writing/thesis/ch1-literature-review.md` | 0 | 6 references, all VERIFIED, 0 citation findings |
| `python plugins/orchestra/scripts/review_lint.py examples/fictional-cohort/06_writing/thesis/ch1-literature-review.md` | 0 | 0/20 paragraphs written paper by paper |
| `python plugins/orchestra/scripts/gate.py check examples/fictional-cohort G1` | 0 | G1: open |
| `python plugins/orchestra/scripts/gate.py check examples/fictional-cohort G2` | 0 | G2: open |
| `python plugins/phi-guard/scripts/phi_scan.py --file examples/fictional-cohort/01_question/question.md examples/fictional-cohort/03_protocol/protocol.md` | 0 | warnings only: "full date" on the study-period dates (01/01/2021, 31/12/2022, 31/12/2023); no strong identifier |

Sample size recomputed with the script, same n as `03_protocol/sample-size.md`:

```
python plugins/orchestra/scripts/samplesize.py two-props --p1 0.20 --p2 0.2727 --json
→ n1_final 535, n2_final 535, n_total_final 1070 (OR 1.5, RR 1.363)
python plugins/orchestra/scripts/samplesize.py regression-epv --predictors 6 --epv 10 --p-outcome 0.20 --json
→ events_required 60, n_total_final 300
```

## Edits made by hand after the run

- `03_protocol/sample-size.md` §7 and `03_protocol/sap.md`: the sensitivity range read "360 to more
  than 3,000 per extreme group", mixing per-group and total figures from the table; corrected to
  "180 to more than 1,600 per extreme group (360 to more than 3,300 for the two groups)".
- `STATUS.md` row 6: the next action still said protocol-design was to do; updated.
- `ledgers/references.json` `american2026.authors` and the `.numbered.md` render: refreshed after the
  group-author fix (see Known issues); no author name was typed by hand.

## Known issues

- **Gate naming in literature-search.** After the search the agent wrote "open gate G2" as the
  evidence-approval step in `STATUS.md` and `decisions.md`; G2 belongs to protocol and SAP. The
  author corrected it in stage 4 and the agent recorded the correction in `decisions.md`. The skill
  now states that no gate opens at that stage and hands off to `protocol-design`.
- **Appraisal ran twice.** literature-search step 4c already appraised all five records, so the
  `/orchestra:appraise` stage re-appraised the two key studies (NOS → ROBINS-E as primary tool).
  Step 4c now covers key studies only and takes the tool from `tools-by-design.md`.
- **Group author dropped (fixed after the run).** The ADA Standards of Care 2026 §16 record
  (`american2026`, PMID 41358892) entered the ledger with `authors: []` because `litapi.py` ignored
  PubMed's `CollectiveName` authors, so its Vancouver entry began with the title. After the fix the
  authors were refreshed from a live `search_lit.py fetch 41358892`, `verify_refs.py` re-run (VERIFIED)
  and the `.numbered.md` re-rendered; it now begins "American Diabetes Association Professional
  Practice Committee for Diabetes".
- **Hand-numbered references outside Chapter 1.** `01_question/question.md`, `02_evidence/*.md` and
  `03_protocol/*.md` were written with typed `[n]` numbers and reference lists, before evidence-policy §Citing sources
  required `[@id]` keys in every project document; only Chapter 1 goes through `verify_refs.py --cite`
  and `cite_render.py`. The files are kept as the run produced them.
- **Diagnostic criteria uncited.** protocol-design did not look up the ADA diagnosis section through
  guideline-check; `protocol.md` says the type 2 diabetes criteria have no verified citation yet.
- **Thin Chapter 1 background.** Sections 1.1–1.3 (definitions, epidemiology, mechanisms) have no
  citations because the six references cover only the HbA1c–readmission question; the chapter says
  so. Vietnamese journals, OpenEvidence, Consensus and ClinicalTrials.gov were not searched in this
  run (no MCP servers), recorded as limitations in `02_evidence/search-strategy.md`. literature-search
  step 2 asks for a ClinicalTrials.gov search filtered by country, but `search_lit.py trial` only
  looks up a known NCT number, so without an MCP server that counter-check cannot be run.
- **n computed by a simpler test.** n comes from a two-proportion comparison of the extreme HbA1c
  groups while the primary analysis is multivariable logistic regression; `sample-size.md` states
  this is the conservative approximation the test-selection reference allows.
- **Next step points ahead.** `STATUS.md` names `ethics-and-crf` as the next skill; it is planned
  for phase P4 and does not exist yet.
- `00_inputs/` is not in the repository: the project's own `.gitignore` keeps it out of git, as it
  should for real projects.
