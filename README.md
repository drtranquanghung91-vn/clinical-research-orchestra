<h1 align="center">Clinical Research Orchestra: A Multi-Agent Harness for<br>Evidence-First Clinical Research</h1>

<p align="center">
  <b>From bedside question to podium, with every citation and number checked.</b><br>
  Claude Code plugins that take medical students, residents, doctors and other healthcare
  professionals through a research project: question, evidence, protocol, analysis,
  manuscript or thesis, poster and defence.
</p>

<p align="center">
  <a href="LICENSE"><img alt="MIT licence" src="https://img.shields.io/badge/licence-MIT-0F5E7A"></a>
  <img alt="Claude Code" src="https://img.shields.io/badge/Claude%20Code-plugin-C8372D">
  <img alt="Languages" src="https://img.shields.io/badge/languages-English%20%7C%20Vietnamese-56677F">
  <img alt="Status" src="https://img.shields.io/badge/status-0.3.0%20analyse%20and%20report-B7791F">
  <a href="https://github.com/drtranquanghung91-vn/clinical-research-orchestra/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/drtranquanghung91-vn/clinical-research-orchestra/actions/workflows/ci.yml/badge.svg"></a>
</p>

> **Status: early.** Version 0.3.0 adds the P2 "analyse and report results" skills (data
> preparation, statistical analysis per the SAP, results writing with a Chapter 3 .docx) to the
> P1 "plan the study" skills (research question, literature search, critical appraisal, guideline
> check, literature review, protocol design, sample size and SAP) and the 0.1.0 foundation (project
> folder, ledgers, gates, reference verification and patient-data protection). Presentation and
> writing skills arrive phase by phase; see [Roadmap](#roadmap). A simulated project run through
> every P1 and P2 skill is in [`examples/fictional-cohort/`](examples/fictional-cohort/). Do not
> rely on it for real studies yet.

---

## Why this exists

Ask a general-purpose agent to "write the literature review for my thesis" or "calculate the
sample size" and you get fluent text in minutes. It is often wrong in the ways that a
supervisor, an ethics committee or a journal reviewer will catch:

- **References are recalled, not retrieved.** A PMID or DOI "from memory" ends up in the
  reference list, or a real paper is cited for a claim it does not make.
- **Numbers drift.** 85% in the abstract, 86.3% in the results; a sample size of "≈26"
  that was never rounded up; a confidence-interval bound used in place of the point estimate.
- **The review is a list of papers.** Chapter 1 reads "Smith found… Nguyen found…" instead
  of a synthesis organised by question.
- **Patient data leaks.** A name, a national ID number or a record number goes into a web
  search or an external tool.
- **The prose sounds machine-written**, and nothing says how AI was used.

Clinical Research Orchestra turns these steps into a method with files, checks and gates,
in the spirit of [Superpowers](https://github.com/obra/superpowers) and
[PaperOrchestra](https://github.com/google-research/paper-orchestra). The agent reasons;
scripts measure. Anything a script can verify (an identifier, a number, a sample-size
calculation, a poster's print resolution) is not left to the model's word.

## How it works

Every project lives in one folder with stage directories (`01_question/` to `07_present/`),
ledgers for references, results and claims, and four human gates:

| Gate | Stops before | You decide |
|---|---|---|
| G1 Question | searching and protocol work | the research question, PICO/PECO and objectives |
| G2 Protocol | data collection | design, eligibility, variables, sample size, analysis plan |
| G3 Results lock | writing | the analysis outputs, locked with a SHA-256 hash |
| G4 Release | sending anything out | the manuscript, thesis, poster or deck after all checks pass |

Skills hand work forward through these files, not through the conversation, so you can
enter at any stage (a thesis already half written, a poster due next week) and resume later
with `/orchestra:status`. A gate can be waived only with a written reason in `decisions.md`.

Two plugins ship from this marketplace:

- **`orchestra`**: the research skills, commands, scripts and reference library.
- **`phi-guard`**: a hook that scans outbound tool calls (web search, fetch, MCP tools,
  network commands) for patient identifiers and blocks or asks, plus a
  `deidentify-data` skill for CSV and Excel files. Install it on its own if you only want
  the protection.

## The skills

| Stage | Skill | What it produces | Phase |
|---|---|---|---|
| 0 | `research-project-setup`, `/orchestra:start`, `/orchestra:status` | project folder, ledgers, gates, next step | 0.1.0 |
| 0 | `deidentify-data` (phi-guard) | de-identified data file and a separate key file | 0.1.0 |
| 1 | `research-question` | PICO/PECO, FINER check, objectives, hypotheses, title options | 0.2.0 |
| 2 | `literature-search` | nomenclature check, search strategy, verified references, evidence table and map, gaps | 0.2.0 |
| 2 | `critical-appraisal`, `/orchestra:appraise` | appraisal by the study's real design, with the matching tool | 0.2.0 |
| 2 | `guideline-check` | current clinical and reporting guidelines, each with version and date | 0.2.0 |
| 2 | `literature-review`, `/orchestra:review` | thesis Chapter 1 or manuscript background, synthesised by question (`review_lint.py`, `cite_render.py`) | 0.2.0 |
| 3 | `protocol-design` | design with trade-offs, eligibility, variables table, bias and confounding | 0.2.0 |
| 3 | `sample-size-sap` | sample size with a sensitivity table (`samplesize.py`) and a statistical analysis plan with an analysis register | 0.2.0 |
| 4 | `data-preparation` | codebook, data audit, cleaning log, de-identified data in `04_data/` | 0.3.0 |
| 4 | `statistical-analysis`, `/orchestra:analyze` | analysis per the SAP register with a vendored `crostats.py`, or SPSS/Stata/R output imported; declared post-hoc analyses; results ledger (`analysis_plan.py`, `results_ledger.py`) | 0.3.0 |
| 5 | `results-writing`, `/orchestra:results` | thesis Chapter 3 or manuscript Results from the locked ledger, with .docx (`render_results.py`, `check_numbers.py`, `build_docx.py`) | 0.3.0 |
| 4 | `research-figures` | Table 1, Kaplan–Meier with numbers at risk, forest plots, flow diagrams | P3 |
| 6 | `research-poster`, `defense-prep`, `conference-abstract` | poster with print preflight, thesis-defence deck, abstract | P3 |
| 5–6 | `prose-humanizer` | rewrites AI-sounding prose, keeps every number and citation | P3 |
| 5 | `manuscript`, `thesis`, `case-report`, `systematic-review` | manuscript and thesis .docx, CARE case report, PRISMA review | P4 |
| 3, 7 | `ethics-and-crf`, `journal-selection`, `reviewer-response` | ethics dossier and CRF, journal shortlist, response to reviewers | P5 |

You can talk to the skills in Vietnamese or English. The language of research documents is
a project setting (`project.yaml → language.output`), so a thesis can be written in
Vietnamese while the manuscript from the same study is in English.

## What makes it different

- **Verified references only.** Every reference enters through `search_lit.py add` and is
  checked by `verify_refs.py` against PubMed, Europe PMC or Crossref. Citations in text use
  `[@id]` keys that must exist in the ledger, and `cite_render.py` numbers them in Vancouver
  style from the ledger. A source with no PMID or DOI enters only as an author-supplied record
  (`add-manual`) and is listed as MANUAL, never as verified.
- **Numbers from files.** Results come from a results ledger, not from the model's memory, and a
  sample size comes from `samplesize.py` with a sensitivity table, every parameter sourced or
  labelled as an assumption.
  Results enter text only as `{{R-…}}` placeholders filled from the locked ledger, and
  `check_numbers.py` blocks any typed number the ledger does not hold, at its printed precision (see
  `judgement-defaults.md`). A consistency audit that
  flags numbers disagreeing between sections arrives in P3.
- **Patient data protected by default.** `phi-guard` knows Vietnamese identifier formats
  (CCCD/CMND, BHYT, record numbers, labelled names, dates of birth, addresses) as well as
  phones and emails. Detection is heuristic and not proof that a text is clean.
- **Tested like code.** Unit tests for every script, and behaviour scenarios that were run
  first without the skills (RED) and then with them (GREEN).
- **Honest about AI.** Manuscripts and theses get an AI-use disclosure; the humanizer
  removes tells of machine prose without hiding that AI helped.

## Install

### Claude Code

```
/plugin marketplace add drtranquanghung91-vn/clinical-research-orchestra
/plugin install phi-guard@clinical-research-orchestra
/plugin install orchestra@clinical-research-orchestra
```

Then start a project:

```
/orchestra:start
```

### Tools the scripts use

Python 3.10 or later. The harness scripts use the standard library only. Literature lookups call
the public PubMed, Europe PMC and Crossref APIs; no API key is needed. Analysis scripts written by
`statistical-analysis` need `pandas`, `scipy` and `statsmodels` (`lifelines` for Cox models):
`python -m pip install pandas scipy statsmodels openpyxl lifelines`.

## Roadmap

| Phase | Scope | State |
|---|---|---|
| P0 Foundation | project folder, ledgers, gates, `phi-guard`, `verify_refs.py`, `search_lit.py`, CI | done (0.1.0) |
| P1 Plan the study | research question, literature search, appraisal, guideline check, literature review, protocol, sample size and SAP | done (0.2.0) |
| P2 Analyse and report results | data preparation, statistical analysis (run and import), results ledger, results writing, Chapter 3 .docx | done (0.3.0) |
| P3 Present | figures, poster, defence deck, abstract, prose humanizer, consistency audit | next |
| P4 Write | manuscript, thesis, case report, systematic review | planned |
| P5 Extend | ethics and CRF, journal selection, reviewer response, Codex and Antigravity packaging | planned |

The design spec is in [`docs/superpowers/specs/`](docs/superpowers/specs/) and each phase
has its implementation plan in [`docs/superpowers/plans/`](docs/superpowers/plans/).

## Repository layout

```
.claude-plugin/marketplace.json   marketplace manifest (plugins: orchestra, phi-guard)
plugins/orchestra/                research skills, commands, scripts/, templates/project/
plugins/phi-guard/                outbound PHI hook, phi_scan.py, deidentify.py, deidentify-data skill
examples/fictional-cohort/        a simulated project run through every P1 and P2 skill, with its checks
tests/unit/                       tests for every script
tests/scenarios/                  RED/GREEN behaviour scenarios and the baseline record
tools/lint_skills.py              skill frontmatter and length checks
docs/superpowers/                 design spec and phase plans
AGENTS.md                         conventions for agents working on this repository
```

## Testing

```bash
python -m unittest discover -s tests/unit -v
python tools/lint_skills.py
```

CI runs both on Linux and Windows with Python 3.10 and 3.12 on every push.

The skills are written test-first, as Superpowers prescribes. Each behaviour is first run on
an agent without the plugin, and the failures are recorded in
[`tests/scenarios/BASELINE.md`](tests/scenarios/BASELINE.md). The skills are then written to
fix those failures and the scenarios re-run with them loaded
([`tests/scenarios/README.md`](tests/scenarios/README.md)).

## Authors

- **Trần Quang Hưng**: owner, architecture, harness and scripts.
- **Amelia Le** ([@ngoclnl189-amelia](https://github.com/ngoclnl189-amelia)): co-author of the research-methods skills (research question, literature and
  evidence, critical appraisal, protocol design, sample size and SAP) and their reference
  material.

See [CONTRIBUTORS.md](CONTRIBUTORS.md).

## Acknowledgements

- [google-research/paper-orchestra](https://github.com/google-research/paper-orchestra):
  outline-as-plan, two-stage citation verification, reviewer accept/revert loop (ideas only;
  no code or prompt text copied)
- [obra/superpowers](https://github.com/obra/superpowers): skills as methodology, TDD for
  skills, subagent-driven development
- [drtranquanghung91-vn/grand-rounds](https://github.com/drtranquanghung91-vn/grand-rounds):
  the literature API client, reference verification and PHI patterns this harness builds on;
  use it for medical talks beyond the thesis-defence path
- The `humanizer` skill: the pattern catalog behind `prose-humanizer`

Details and licences are in [NOTICE.md](NOTICE.md).

## Disclaimer

Clinical Research Orchestra helps plan, write and present research. It does not give medical
advice and does not replace a supervisor, a statistician or an ethics committee. The author
is responsible for the study, for checking every claim against its source, for ethics
approval and patient consent, for de-identifying data, and for disclosing AI use as their
institution and journal require.

## Licence

[MIT](LICENSE) © 2026 Trần Quang Hưng and contributors.
