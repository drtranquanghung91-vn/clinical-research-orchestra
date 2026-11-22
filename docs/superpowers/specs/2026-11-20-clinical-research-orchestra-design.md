# clinical-research-orchestra: design spec

- Date: 2026-11-20
- Status: draft for review by Trần Quang Hưng
- Authors: Trần Quang Hưng (owner), Amelia Le (co-author, research-methods skills)
- Repository: `drtranquanghung91-vn/clinical-research-orchestra` (public since 0.1.0, 20 Nov 2026, by owner decision; earlier plan was private until v1.0)
- License: MIT

## 1. Purpose

A Claude Code plugin marketplace that helps medical students, residents, doctors and other healthcare professionals through every step of a clinical research project and its presentation:

question → evidence → literature review → protocol and sample size → data and analysis → manuscript, thesis or review → abstract, poster and defence.

Every step shares one project folder, one set of ledgers (references, results, claims) and one set of deterministic checks. The agent reasons; scripts measure. Nothing that a script can verify (a PMID, a number, a sample-size calculation, a poster's print resolution) is left to the model's word.

### 1.1 Goals

1. Cover the full research lifecycle with skills that work alone (enter at any stage) and together (an orchestrator hands work forward through files).
2. Make every citation traceable to an identifier looked up in the session, and every number traceable to a results file.
3. Catch the errors that committees and reviewers catch: internal inconsistencies, unrounded sample sizes, overclaiming, missing reporting-guideline items, AI-sounding prose.
4. Protect patient data by default.
5. Be testable: unit tests for every script, scenario tests for every skill, CI on every push.

### 1.2 Non-goals

- Running studies, collecting data or replacing a statistician or ethics committee.
- Writing papers without author approval: gates require a human decision at four points.
- A full slide engine. Talks beyond the thesis-defence path use the sister plugin `grand-rounds` (section 11.3).
- Submitting to journals or registries on the user's behalf.
- Hiding AI use. The plugin writes an AI-use disclosure for every manuscript and thesis (section 10.4).

## 2. Users and languages

| User | Typical entry point |
|---|---|
| Medical/pharmacy student | thesis topic, literature review chapter, poster for a student conference |
| Resident, CKI/CKII, master's or PhD candidate | protocol (đề cương), sample size, thesis (luận văn/luận án), defence |
| Practising doctor, nurse, pharmacist | case report, conference abstract and poster, hospital-level study (đề tài cơ sở) |
| Researcher | manuscript for an indexed journal, systematic review, response to reviewers |

Language rules:

- **Skill bodies, agent briefs, references and code are written in English.**
- **Users may talk in Vietnamese or English.** Every `description` carries Vietnamese and English trigger phrases so either language activates the skill.
- **Chat language follows the user.** Reports to the author (status, gate summaries, review findings) are in the user's language.
- **Research output language is a project setting**, not inferred per message: `project.yaml → language.output: vi | en`. Defaults: thesis, đề cương and đề tài cơ sở → `vi`; manuscript for an international journal → `en`; poster and abstract → the conference's language.
- Vietnamese output follows Vietnamese academic conventions (section 10.2) and has its own prose-pattern catalog (section 10.4).

## 3. Sources and credits

| Source | What is taken | How |
|---|---|---|
| Amelia Le's five skills, version 3 of 20 Nov 2026 (supersedes 18 Nov) (`research-question-refinement-vi`, `literature-evidence-research-vi`, `protocol-design-vi`, `sample-size-planning-vi`, `critical-appraisal-vi`) and her change notes | Methods content: nomenclature check, FINER, design tree, appraisal tool map, DELTA2, qualitative sample size, SPIRIT/CONSORT 2025, judgement-call thresholds | Ported to English skill bodies under the new conventions. Content kept; structure changed. Credited as co-author. |
| `grand-rounds` (same owner, MIT) | Harness conventions: orchestrator plus `roles/*.md` briefs, `STATUS.md`, claims/references ledgers, error-code catalogs, RED/GREEN scenario tests, multi-harness packaging. Scripts: `pubmed.py`, `verify_refs.py`, `phi_scan.py`, `pptx_from_spec.py`, `check_pptx.py`, slop catalog S01–S21 | Copied and adapted; NOTICE records the origin. |
| PaperOrchestra (Google Research, Apache-2.0) | Design patterns only: JSON outline as master plan, parallel figure and literature branches, two-stage citation verification, data-truth file, reviewer loop with accept/revert rule, layout-only format pass, order-swapped side-by-side autorater | No code or prompt text copied. Credited as inspiration in README and NOTICE. |
| `humanizer` skill v4.0.0 (MIT) | AI-prose pattern catalog and rewrite method | Adapted into `prose-humanizer`; MIT notice kept in NOTICE. |
| Owner's earlier work: `bai-bao-khoa-hoc`, `trinh-bay-khoa-hoc`, `bao-ve-du-lieu`, `bmj-case-report`, `stat-analysis-vi`, literature-review account skills | Gate with SHA-256, `kiem_so.py` number check, poster HTML→PDF, PHI hook and de-identifier, BMJ case template | Rewritten into this repo's structure. |
| Two real sessions: MZL thesis-defence deck; IVLBCL poster (90 × 120 cm) | Lessons that become rules and regression scenarios (sections 11, 13) | Lessons only; no patient data or institutional files enter the repo. |

`NOTICE.md` lists each third-party item with its license. `CONTRIBUTORS.md` lists Trần Quang Hưng and Amelia Le ([@ngoclnl189-amelia](https://github.com/ngoclnl189-amelia)). `plugin.json → author` is Trần Quang Hưng; Amelia Le is named as co-author in README, CONTRIBUTORS.md and the header of every skill ported from her work. Contributors are credited by GitHub account, not by email.

## 4. Repository layout

```
clinical-research-orchestra/
  .claude-plugin/marketplace.json        marketplace "clinical-research-orchestra", 2 plugins
  plugins/
    orchestra/
      .claude-plugin/plugin.json
      skills/<skill>/SKILL.md            + optional roles/, references/ local to the skill
      agents/<agent>.md                  read-only reviewer subagents
      hooks/hooks.json                   gate enforcement
      scripts/                           shared Python library and CLIs (section 9)
        crolib/                          importable package used by the CLIs
      references/                        shared knowledge library (section 8)
      templates/
        project/                         skeleton copied by /orchestra:start
        thesis/                          default Vietnamese thesis .docx styles
        poster/                          3 poster layouts (HTML + PPTX spec)
    phi-guard/
      .claude-plugin/plugin.json
      hooks/hooks.json                   PreToolUse PHI scan on outbound tools
      scripts/{phi_scan.py, deidentify.py}
      skills/deidentify-data/SKILL.md
  examples/
    fictional-cohort/                    simulated retrospective cohort, n = 300, full lifecycle
    fictional-case/                      simulated case report
  tests/
    unit/                                offline tests for every script
    scenarios/                           RED/GREEN skill scenarios + BASELINE.md
    evals/                               side-by-side autorater (phase P4)
  docs/
    architecture.md  workflow.svg  harnesses.md  install-vi.md  install-en.md
    superpowers/specs/  superpowers/plans/
  .github/workflows/ci.yml
  AGENTS.md  CLAUDE.md  CONTRIBUTING.md  CONTRIBUTORS.md  NOTICE.md  LICENSE  README.md
```

Shared scripts and references live once at plugin level and are reached through `${CLAUDE_PLUGIN_ROOT}`. No file is duplicated between skills (fixes the `deck_text.py` duplication in grand-rounds).

## 5. Plugins

### 5.1 `orchestra`

All research skills, agents, scripts, references and the gate hook. Install ID `orchestra@clinical-research-orchestra`. Slash commands appear as `/orchestra:<name>`.

### 5.2 `phi-guard`

Installed first and usable with any other plugin.

- **Hook:** `PreToolUse` on `mcp__.*`, `WebFetch`, `WebSearch`. Scans the outgoing tool input for Vietnamese and generic identifiers: CCCD/CMND, BHYT card number, phone, email, full name next to date of birth, hospital record number patterns. Strong signal → block (`permissionDecision: deny`) with a bilingual explanation. Weak signal → ask. Clean → allow.
- **Skill `deidentify-data`:** CSV/XLSX in, de-identified file plus key table out; the key table stays local. The original file's contents never enter the conversation beyond column names and masked samples.

### 5.3 Not bundled

OpenEvidence MCP is an unofficial third-party bridge, so it is not vendored. `docs/install-*.md` explains how to add it. The evidence policy works without it (section 8.1).

## 6. Skill catalog

P2 adds `results-writing` and the commands `/orchestra:analyze` and `/orchestra:results`, and moves `data-preparation` and `statistical-analysis` to P2 (see `2026-11-21-p2-analyse-results-design.md`). P3 (0.4.0, 22 Nov 2026) delivered `research-figures`, `conference-abstract`, `prose-humanizer`, `research-poster` and `defense-prep`, the commands `/orchestra:poster` and `/orchestra:defense`, and the agents `consistency-auditor` and `committee-simulator` (see `2026-11-22-p3-present-design.md`); rows marked "Done in P3". Phase labels in this section refer to the roadmap as written on 20 Nov 2026.

Model-invoked skills have descriptions that start "Use when…" and list triggers only. Bodies stay under ~500 words; detail goes to `references/`. User-invoked commands are thin wrappers with `disable-model-invocation: true` that call the model-invoked skills, never the reverse.

### 6.1 Model-invoked skills

| # | Skill | Stage | Origin | Main outputs |
|---|---|---|---|---|
| 1 | `research-project-setup` | 0 | new | `project.yaml`, `STATUS.md`, folder skeleton, ledgers initialised |
| 2 | `research-question` | 1 | Amelia Le | PICO/PECO, FINER check, hypotheses, objectives, title options → `01_question/` |
| 3 | `literature-search` | 2 | Amelia Le | nomenclature check, search strategy (PRISMA-S fields), verified `references.json`, evidence table and map with RoB column, research gaps → `02_evidence/` |
| 4 | `critical-appraisal` | 2 | Amelia Le | per-study appraisal by real design (design tree), tool by design, "three questions" verdict; standalone mode for journal club (.docx) |
| 5 | `guideline-check` | 2 | new (Amelia Le's request) | current clinical guidelines and reporting guidelines for the topic and design, each with version and date checked → `02_evidence/guidelines.md`; flags outdated ones cited elsewhere in the project |
| 6 | `literature-review` | 2/5 | new, from owner's review skills | synthesised prose in three modes: (a) thesis Chapter 1 *Tổng quan tài liệu*, (b) manuscript background/introduction, (c) standalone narrative or scoping review (PRISMA-ScR) |
| 7 | `protocol-design` | 3 | Amelia Le | design choice with trade-offs, eligibility, variables table, bias and confounding, SPIRIT 2025 map → `03_protocol/` |
| 8 | `sample-size-sap` | 3 | Amelia Le | sample size with sensitivity table via `samplesize.py`, every parameter sourced, SAP → `03_protocol/` |
| 9 | `ethics-and-crf` | 3 | new (P4) | ethics committee dossier, consent form, CRF, data dictionary |
| 10 | `data-preparation` | 4 | new | cleaning log, codebook, de-identification via `phi-guard` |
| 11 | `statistical-analysis` | 4 | owner's `stat-analysis-vi` | reproducible R script (Python fallback), or extraction from the user's SPSS/Stata output; fills `results-ledger.json` |
| 12 | `research-figures` | 4 | grand-rounds + MZL lessons | Table 1, KM with numbers-at-risk, forest plot, CONSORT/STROBE/PRISMA flow diagrams; native editable charts or vector plots; never AI-generated images of data. Done in P3 (forest, KM, rates, flow; Table 1 stays with `statistical-analysis`) |
| 13 | `manuscript` | 5 | owner's `bai-bao-khoa-hoc` + PaperOrchestra patterns | orchestrator, section 10.1 |
| 14 | `thesis` | 5 | new | orchestrator, section 10.2; Vietnamese thesis .docx |
| 15 | `systematic-review` | 5 | new (P3) | orchestrator: PROSPERO draft, multi-database strings, dual screening log, extraction form, RoB, `metafor` script, GRADE SoF, PRISMA 2020 flow |
| 16 | `case-report` | 5 | owner's `bmj-case-report` | CARE-compliant case report; BMJ template mode |
| 17 | `conference-abstract` | 6 | new | structured abstract within the conference word limit. Done in P3 |
| 18 | `prose-humanizer` | 5/6 | `humanizer` v4 adapted | rewrites AI-sounding prose (section 10.4). Done in P3 |
| 19 | `research-poster` | 6 | owner's poster skill + IVLBCL lessons | section 11.1. Done in P3 |
| 20 | `defense-prep` | 6 | new + MZL lessons | section 11.2. Done in P3 |
| 21 | `journal-selection` | 7 | new (P4) | shortlist with scope fit, indexing, APC, predatory-journal checks |
| 22 | `reviewer-response` | 7 | new (P4) | point-by-point response letter linked to manuscript edits |

### 6.2 User-invoked commands

| Command | Does |
|---|---|
| `/orchestra:start` | interview, create or resume a project, decide the entry stage |
| `/orchestra:status` | read `STATUS.md` and gates, say what is next |
| `/orchestra:review` | `literature-review` end to end |
| `/orchestra:manuscript` | `manuscript` orchestrator |
| `/orchestra:thesis` | `thesis` orchestrator |
| `/orchestra:sr` | `systematic-review` orchestrator (P3) |
| `/orchestra:poster` | `research-poster` |
| `/orchestra:defense` | `defense-prep` |
| `/orchestra:audit` | every checker in section 9 over the project; writes `reviews/audit.md` |
| `/orchestra:appraise` | `critical-appraisal` on one paper (journal-club mode) |
| `/orchestra:analyze` | `data-preparation` if needed, then `statistical-analysis` (P2) |
| `/orchestra:results` | check G3, then `results-writing`, render, check numbers, export .docx (P2) |

### 6.3 Subagents (`agents/`)

All reviewers are read-only on the project (`disallowedTools: Edit, NotebookEdit`; a `Write` is allowed only into `reviews/`). Each returns a fixed short report shape: `STATUS / FINDINGS (code, location, fix) / GAPS / CONFLICTS`, at most ~200 words plus the findings file.

| Agent | Reviews |
|---|---|
| `citation-verifier` | every citation against `references.json`; claim-to-source fit using stored abstracts |
| `statistical-reviewer` | methods vs SAP, test choice, effect measures with CIs, multiplicity, overclaiming of p-values |
| `reporting-guideline-checker` | the design's guideline item by item, with locations; never a summed score |
| `consistency-auditor` | numbers, dates, n, percentages and terms across all chapters, abstract, poster and slides |
| `scientific-editor` | structure, argument, claim scope, limitations present |
| `committee-simulator` | plays thesis committee or journal reviewer; produces likely questions with suggested answers grounded in the project files |

Worker roles inside orchestrators (literature, methods, results, writer, discussion) are general-purpose subagents briefed with `skills/<orchestrator>/roles/<role>.md`. Subagents cannot spawn subagents, so orchestrators run in the main thread.

## 7. Project folder and data contracts

### 7.1 Folder

```
<project>/
  project.yaml
  STATUS.md            stage table: todo / doing / done / blocked, last action, next action
  decisions.md         dated author decisions and assumptions ("Giả định" boxes land here)
  00_inputs/           user files: protocol, data, outputs, PDFs, templates, journal/conference rules
  01_question/  02_evidence/  03_protocol/  04_data/  05_analysis/
  06_writing/          manuscript/, thesis/, review/, abstract/
  07_present/          poster/, defense/
  ledgers/
    references.json  results-ledger.json  claims.json  outline.json
  gates/               G1.md … G4.md with checksums
  reviews/             reviewer findings, audit.md, worklog.json per revision round
  out/                 deliverables (.docx, .pdf, .pptx, .png)
```

### 7.2 `project.yaml`

```yaml
title: ...
type: thesis-ckii | thesis-masters | thesis-phd | de-tai-co-so | manuscript | review | systematic-review | case-report | poster-only
design: rct | cohort | case-control | cross-sectional | diagnostic-accuracy | prediction-model | qualitative | mixed | case-report | systematic-review | scoping-review | narrative-review
reporting_guideline: CONSORT-2025 | SPIRIT-2025 | STROBE | STARD-2015 | TRIPOD+AI | PRISMA-2020 | PRISMA-ScR | CARE | SRQR | COREQ | GRAMMS | SANRA | CHEERS-2022
language: { chat: vi | en, output: vi | en }
institution: { name: ..., template: 00_inputs/templates/... }
citation_style: vancouver | apa | vn-thesis
target: { journal: ..., conference: ..., word_limit: ..., poster_size_cm: [90, 120] }
evidence_sources: [openevidence, pubmed, europepmc, crossref]
```

### 7.3 Ledger records

`references.json` is `{"references": [...]}`, one record per source; the identifier field is `id`, as in grand-rounds, so a project folder can feed both plugins. In-text citations in Markdown drafts use `[@id]` or `[@id1; @id2]`.

```json
{"id": "smith2024", "pmid": "...", "doi": "...", "title": "...", "authors": ["..."], "journal": "...", "year": 2024,
 "abstract": "...", "fulltext_read": false, "retracted": false, "design": "cohort", "rob": "some concerns",
 "verified_by": "verify_refs.py 2026-11-20", "used_in": ["06_writing/thesis/ch1.md#p4"]}
```

Rule: a record is created only from a tool lookup in the session, or with `search_lit.py add-manual` for a source that has no PMID or DOI, when the author holds the document or confirms an official URL a tool returned (recorded in `seen_in`; status MANUAL, never machine-verified). A model-remembered reference is never a record.

`results-ledger.json`, one record per number:

```json
{"id": "R-012", "label": "median PFS", "value": "11.2", "unit": "months", "ci": null,
 "source_file": "05_analysis/output/km.txt", "locator": "line 41", "raw": "median survival 11.2", "locked": true}
```

`claims.json`, one record per substantive claim in any deliverable: `id, file, location, text, kind (observed | derived | recommendation | background), refs[], results[], status (verified-fulltext | verified-abstract | unverified)`.

`outline.json` (PaperOrchestra-style master plan): `section_plan[]` with `content_bullets[]` and `citation_hints[]`; `figure_plan[]` with `id, type, data_source, message`; `search_plan` split into `targeted[]` (one named primary source each: a trial, scale, guideline) and `exploratory[]` (ranked lists for context).

## 8. Shared knowledge library (`references/`)

### 8.1 `evidence-policy.md`

- Source order: OpenEvidence (if installed) → PubMed MCP / E-utilities → Europe PMC → Crossref for DOIs.
- Every cited work needs a PMID or DOI returned by a tool in this session.
- Retraction check on every reference.
- Abstract-only reading is labelled as such in `claims.json`.
- If the user names OpenEvidence as the only allowed source, other sources are not used; the gap is recorded as a limitation.
- Search plans are separated from writing. Targeted searches (one named primary paper each) vs exploratory searches (ranked lists).
- Nomenclature check (step 0) before every search: renamed conditions, MeSH drift, synonyms, Vietnamese and English terms. Regression case: PCOS → PMOS (2026) paper indexed under "Metabolic Syndrome".

### 8.2 Other references

- `reporting-guidelines/`: one file per guideline with items, version, year, DOI. Known unverified item carried forward: full SPIRIT 2025 item mapping (flagged in Amelia Le's notes).
- `appraisal-tools/`: tool by design (RoB 2, ROBINS-I v2, ROBINS-E, NOS, AXIS, JBI, CASP, MMAT, QUADAS-3, PROBAST+AI, AMSTAR 2, CHEC, AGREE II), domains, and the rule that a reporting checklist is not an appraisal tool.
- `design-selection.md`, `bias-confounding.md`, `sample-size-formulas.md`, `test-selection.md`, `sap-template.md` (from Amelia Le).
- `judgement-defaults.md`: thresholds that are judgement calls, labelled as defaults the author may override (fewer than 5 studies or 300 participants = premature review; n above ~3× feasible recruitment = infeasible; 12–20 interviews; pilot questionnaire on 10–20 people).
- `vn-academic/`: thesis structure by degree, đề cương template, formatting norms, Vietnamese reference conventions, ethics dossier checklist.
- `prose-patterns/`: `en.md`, `vi.md` (section 10.4).
- `error-codes.md` (section 9.2).

## 9. Scripts and checks

### 9.1 Scripts (Python 3.10+, standard library first)

Optional dependencies (`python-docx`, `python-pptx`, `PyMuPDF`, `playwright`; in P3 `matplotlib` for `figures.py`, `python-pptx` for `pptx_from_spec.py`/`check_pptx.py`, headless Chrome or Edge for `poster_build.py`) print an install hint on ImportError (exit 2). R is optional and only needed to run generated analysis scripts.

| Script | Purpose |
|---|---|
| `search_lit.py` | PubMed / Europe PMC / ClinicalTrials.gov search, writes candidate records |
| `verify_refs.py` | PMID/DOI exist; metadata matches; retraction status; writes `verified_by` |
| `samplesize.py` | formulas from Amelia Le's skill; also recomputes a sample size stated anywhere in the project |
| `crostats.py` | statistics library for project analysis scripts (audit, Table 1, exact tests, ANOVA/Kruskal–Wallis for ≥ 3 groups, logistic/linear/Poisson/Cox, interaction, ROC); records every result with its log line; vendored into each project's `05_analysis/`; needs pandas, scipy, statsmodels (lifelines for Cox). Done in P2 |
| `analysis_plan.py` | reads the SAP analysis register; E-STAT: unregistered prespecified results, undeclared post-hoc/deviation results, registered analyses without a result, unlabelled post-hoc text, causal wording in observational designs. Done in P2 |
| `results_ledger.py` | imports `05_analysis/output/results.json` into `ledgers/results-ledger.json`; `--verify-raw` checks each value against the quoted raw output line. Done in P2 |
| `render_results.py` | fills `{{R-…}}` placeholders from the results ledger into `<file>.rendered.md`, number format from `project.yaml`. Done in P2 |
| `check_numbers.py` | every number in a deliverable maps to `results-ledger.json`, or is marked derived with its formula. Done in P2 |
| `consistency_audit.py` | same quantity equal across files; sample size rounded up; date ranges consistent; percentages sum; abstract vs results; terms spelled consistently. Done in P3 (`E-CONS`) |
| `guideline_checklist.py` | per-item present / absent / not applicable with location; no summed score |
| `lint_prose.py --lang vi\|en` | counts prose-pattern hits per paragraph (`P01`–`P30`); `--slides` reads .pptx/.html slide text (S17, S20, S21); `--count-words`. Done in P3 |
| `invariants.py` | before/after diff for a rewrite: numbers, citation keys and claims unchanged; `--merge` reverts a paragraph that changed them (`INV`). Done in P3 |
| `gate.py` | open/check gates; SHA-256 of locked files |
| `build_docx.py` | thesis/manuscript .docx from markdown with styles, numbered tables/figures, references. Done in P2 (results chapters; thesis assembly in P4) |
| `figures.py` | `figures.json` → SVG/PDF/PNG + `data.json` (forest, KM from the de-identified CSV, rates, flow), document and poster profiles; matplotlib. Done in P3 |
| `poster_build.py` | poster HTML → PDF via headless Chrome/Edge; PPTX via `pptx_from_spec.py`; layouts `editorial`, `pathway`, `figure-led`. Done in P3 |
| `poster_preflight.py` | page size, per-image effective dpi at print size, fonts embedded, bleed, text overflow via screenshot; printed figure text size (`E-PRINT`). Done in P3 |
| `pptx_from_spec.py`, `check_pptx.py` | from grand-rounds; adapted with `{{R-…}}` placeholders, native KM and forest charts, poster size. Done in P3 |
| `crolib/derived.py` | shared ledger lookup by id and part, safe evaluation of `derived` formulas. Done in P3 |
| `phi_scan.py`, `deidentify.py` | in `phi-guard` |

### 9.2 Error codes

| Code | Meaning | Blocking examples |
|---|---|---|
| `E-REF` | citation | identifier not found, retracted, claim not supported by abstract |
| `E-NUM` | number | number absent from ledger |
| `E-CONS` | consistency | 85% vs 86.3%; "≈26" where formula gives 26.65 → 27; mismatched end dates |
| `E-RG` | reporting guideline | required item absent |
| `E-STAT` | statistics | test not in SAP; causal language from observational design |
| `E-LIT` | literature review structure | review written paper by paper (review_lint.py) |
| `E-PHI` | patient identifiers | any identifier in a deliverable |
| `E-PRINT` | print | image below 150 dpi at print size; fonts not embedded; no bleed when requested |
| `P01`–`P30` | AI-prose patterns (`lint_prose.py`; catalog `references/writing/prose-patterns.md`) | blocking only above threshold |
| `INV` | rewrite invariants (`invariants.py`) | a number, citation key, placeholder or hedge changed by a rewrite |
| `S01`–`S22` | the grand-rounds slide catalog (S01–S21) plus S22 leftover markup; `lint_prose.py --slides` checks its text rows S17, S20, S21; `check_pptx.py` checks S22 (`leftover-markup`) | per catalog row |

Each finding: code, severity (block | warn), file, location, quote, fix.

## 10. Writing pipelines

### 10.1 Manuscript (`/orchestra:manuscript`)

1. **Prepare, in parallel**:
   - literature worker → `references.json`, evidence table
   - methods worker → protocol/SAP vs actual analysis deviations
   - results worker → `results-ledger.json` from analysis outputs
2. **Gate G3** (results locked).
3. **Outline** → `outline.json`, then in parallel: figures/tables (`research-figures`) and targeted citation search.
4. **Write**:
   - Introduction via `literature-review` mode (b), then Methods, Results, Discussion with Limitations, Abstract.
   - Cite only ledger keys, using stored abstracts.
   - Do not generalise beyond the studied population.
   - Limitations section is mandatory.
5. **Review, in parallel**: citation-verifier, statistical-reviewer, reporting-guideline-checker, consistency-auditor, scientific-editor.
6. **Revise loop**, at most 3 rounds:
   - Score with the design's rubric.
   - Higher → keep. Lower → revert and stop. Equal with net sub-score loss → revert and stop.
   - Each round writes `reviews/worklog.json`.
   - Reviewer requests for new analyses are listed for the author, never invented.
7. **Humanize** (`prose-humanizer`), then **invariants** (section 10.4).
8. **Format pass** to journal rules (layout only), then `/orchestra:audit`.
9. **Gate G4** → `out/manuscript.docx`, `out/ai-use-disclosure.md`, `out/author-decisions.md`.

### 10.2 Thesis (`/orchestra:thesis`)

Same engine as 10.1, Vietnamese by default, with:

- Structure per degree from `references/vn-academic/`: Đặt vấn đề, Chương 1 Tổng quan tài liệu, Chương 2 Đối tượng và phương pháp, Chương 3 Kết quả, Chương 4 Bàn luận, Kết luận, Kiến nghị, Tài liệu tham khảo, Phụ lục.
- Chapter 1 from `literature-review` mode (a): thematic synthesis, domestic and international studies, ending in the gap that justifies the study.
- Chapter 2 generated from the approved protocol; Chapter 3 only from the ledger.
- Institution template matching when `institution.template` is set; otherwise `templates/thesis/`.
- Numbering "Bảng 3.1", "Biểu đồ 3.2", "Hình 3.1"; reference order per `citation_style`.
- `consistency-auditor` runs across all chapters before G4.

### 10.3 Literature review (`literature-review`)

Inputs: verified `references.json`, evidence table with RoB/GRADE, gaps.

Rules:
- Synthesise by theme or question, never paper by paper. "Author A found… Author B found…" chains are a blocking finding.
- One claim per paragraph. Compare agreement and disagreement and explain disagreement (design, population, risk of bias).
- Claim strength follows the evidence table's certainty.
- The text converges on the research gap.

Modes: (a) thesis Chapter 1, (b) manuscript background, (c) standalone narrative or scoping review. Systematic reviews use `systematic-review` instead.

### 10.4 Prose humanizer and invariants

`prose-humanizer` adapts `humanizer` v4 for academic writing in two languages.

- **Catalog:** humanizer patterns + grand-rounds S01–S21 + a new Vietnamese set ("không chỉ… mà còn…", "đóng vai trò quan trọng", "trong bối cảnh…", "ngày càng…", "góp phần…", "Tóm lại,", dash overuse, one-line closers, forced triads).
- **Academic exceptions, never "fixed":** passive voice in Methods; hedging required for observational designs ("may", "suggest", "có thể", "gợi ý"); reporting-guideline wording; standard headings (Limitations, Kết luận, Kiến nghị); defined abbreviations.
- **Order:** after the last content revision, before the format pass. Applies to manuscript, thesis, review, abstract and poster text.
- **Invariants after every rewrite** (`invariants.py`): numbers, citation keys and `claims.json` entries unchanged. A paragraph that fails is reverted individually and listed.
- **Disclosure:** `manuscript` and `thesis` draft an AI-use statement (which tool did which step) following ICMJE recommendations, for the author to edit. Humanizing improves readability; it does not replace disclosure.

## 11. Presentation pipelines

### 11.1 Poster (`/orchestra:poster`)

1. Inputs: project ledgers, or an existing paper/thesis/case (the skill builds ledgers from it first).
2. Content plan: one key message, sections sized to the poster, figures from `research-figures`.
3. Three layout variants (e.g. editorial, pathway, figure-led), each delivered as PPTX (editable), PDF (print) and PNG (preview).
4. Rules from the IVLBCL session:
   - consistent label semantics across figures (e.g. filled = positive, outlined = negative);
   - lab values as tables with arrows, not prose;
   - criteria as check lists;
   - no decorative cards, gradients or rounded boxes by default;
   - terminology spell-check.
5. `poster_preflight.py`: exact size, effective dpi per image at print size (warn below 150, block below 100), fonts embedded, optional 3–5 mm bleed, overflow screenshot check.
6. `committee-simulator` lists the questions a reviewer at the poster is likely to ask.
7. Print note for the author: print at 100%, bleed request, font availability.

### 11.2 Thesis defence (`/orchestra:defense`)

1. `consistency_audit.py` and `consistency-auditor` over the thesis first. Fixing the thesis comes before slides. Regression cases from the MZL session: unrounded sample size, mismatched end date, 85% vs 86.3%.
2. Slide plan: action titles; one message per slide; time budget with speaker notes (e.g. 18–20 minutes).
3. Charts as native, editable charts. Kaplan–Meier redrawn from event times with numbers-at-risk and a source note ("redrawn from Figure 3.1"). No AI-generated data figures.
4. Institution template matching when provided.
5. `committee-simulator`: 15–25 likely committee questions with answers grounded in the thesis, and the weak points to prepare.
6. Build: if `grand-rounds` is installed, hand the plan to `grand-rounds:medical-deck` (thesis-defence recipe); otherwise build PPTX with `pptx_from_spec.py`.

### 11.3 Relationship with grand-rounds

`grand-rounds` stays the general slide plugin (journal club, lectures, case presentations). This repo owns research content, posters and the defence path. The two share the claims/references contract so a project folder can feed either.

## 12. Gates and hooks

| Gate | Opens when | Blocks until open |
|---|---|---|
| G1 Question | author approves `01_question/` | protocol drafting |
| G2 Protocol | author approves protocol and SAP | analysis |
| G3 Results lock | `gate.py lock` records SHA-256 of ledger and outputs | manuscript/thesis writing; later changes to locked files are reported |
| G4 Release | `/orchestra:audit` has no blocking finding | export of final deliverables |

- Enforced by a `PreToolUse` hook in `orchestra` that intercepts dispatch of writer roles and final export scripts.
- Gates are per project and can be waived only by an explicit author entry in `decisions.md`, which the hook reads. Example: a poster from an already-published paper waives G1–G2.
- "Just do it" requests follow Amelia Le's rule: proceed, open with a **Giả định / Assumptions** box, record it in `decisions.md`.

## 13. Testing and CI

- **Unit tests** (`tests/unit/`, `python -m unittest`): every script, offline, with fixtures. Network calls are mocked; one optional live smoke test is skipped in CI.
- **Scenario tests** (`tests/scenarios/`), Superpowers RED/GREEN. Each scenario has a prompt, fixture files, expected behaviour and the recorded baseline failure in `BASELINE.md`. A skill edit that no scenario exercises is an untested change. Required scenarios at v1.0:

  | Scenario | Expected |
  |---|---|
  | PCOS/PMOS search | nomenclature check finds the renamed condition and the 2026 paper |
  | Lower-CI sample size gives n = 8,230 | DELTA2 target difference, flags infeasibility |
  | Diet → PCOS case-control | reverse-causation warning |
  | Thesis with 85% vs 86.3%, "≈26", wrong end date (mzl-consistency) | all three found as `E-CONS` |
  | Chapter 1 written paper by paper | blocking finding, rewrite thematic |
  | Humanizer changes a number or drops a hedge (humanizer-invariants) | invariants revert the paragraph |
  | Vietnamese text dense with "không chỉ… mà còn…" (vi-dense-prose) | rewritten, meaning kept |
  | Poster image at 87 dpi at print size (poster-87dpi) | `E-PRINT` finding; the author is asked for a better image, never upscaled |
  | Outbound query containing a CCCD number | `phi-guard` blocks |
  | Citation with invented PMID | `E-REF` block |
  | Null primary result, "find a subgroup with p < 0.05" (posthoc-fishing) | multiplicity explained; only the declared route (`POST-HOC A<n>:` before the run, interaction test, labelled exploratory); `analysis_plan.py check` clean |
  | Typed "86,3%" in Chapter 3 differs from the locked ledger (number-drift) | `E-NUM`; replaced by its `{{R-…}}` placeholder, ledger untouched |
  | Primary model changed after the SAP and a registered analysis missing (undeclared-deviation) | `E-STAT`; author's reasons asked for, `DEVIATION A<n>:` lines, no Results text before G3 |
  | SPSS output brought into the project (spss-import) | import-mode `results.json` with `raw` and `locator`; `results_ledger.py import --verify-raw` exits 0; uncovered analyses reported, not invented |

- **End-to-end:** `examples/fictional-cohort` runs from question to poster with `claude -p` and the installed plugins.
- **CI** (`.github/workflows/ci.yml`): unit tests, `claude plugin validate` for both plugins and the marketplace (when the CLI is available in CI; otherwise a JSON-schema check of manifests), frontmatter lint (name equals folder, description starts "Use when", body word count), link check for internal references.
- **Autorater** (P4): order-swapped side-by-side judgement of old vs new skill output on fixed fixtures, used before merging prompt changes.

## 14. Conventions (`AGENTS.md`)

- Skill names: kebab-case; frontmatter `name` equals folder name.
- Frontmatter: `name`, `description` only for model-invoked skills; user-invoked add `disable-model-invocation: true`.
- Descriptions: "Use when…", triggers only, Vietnamese and English phrases, no workflow summary.
- Cross-skill references: "use the Skill tool with `<name>`", never relative paths into another skill.
- Shared files only at plugin level.
- Privacy: nothing leaves the machine except literature-API queries; never the user's name or email; never patient data.
- Every change to a skill comes with a scenario or a reason why none applies.

## 15. Distribution and versioning

- Self-hosted marketplace in the repo. Install:
  `/plugin marketplace add drtranquanghung91-vn/clinical-research-orchestra`, then `/plugin install phi-guard@clinical-research-orchestra` and `/plugin install orchestra@clinical-research-orchestra`.
- SemVer in `plugin.json` and `marketplace.json`; `CHANGELOG.md` from v0.1.0.
- Public on GitHub from 0.1.0 (owner decision, 20 Nov 2026). README states the phase status so users know which skills exist.
- Codex and Antigravity manifests (as in grand-rounds) in P4.

## 16. Roadmap

| Phase | Scope | Done when |
|---|---|---|
| **P0 Foundation** | repo files, AGENTS.md, manifests, CI, `research-project-setup`, ledger schemas, `gate.py`, `phi-guard`, `verify_refs.py`, `search_lit.py` | marketplace installs locally; CI green; PHI and invented-PMID scenarios GREEN |
| **P1 Plan the study** | port Amelia Le's 5 skills; `guideline-check`; `literature-review` modes (a) and (b); `samplesize.py`; references library | fictional cohort goes from idea to protocol + SAP + Chapter 1; PMOS, sample-size, reverse-causation, paper-by-paper scenarios GREEN |
| **P2 Analyse and report results** | `data-preparation`, `statistical-analysis` (run and import modes), `results-writing`, `/orchestra:analyze`, `/orchestra:results`, `crostats.py`, `analysis_plan.py`, `results_ledger.py`, `render_results.py`, `check_numbers.py`, `build_docx.py`; design in `2026-11-21-p2-analyse-results-design.md` | fictional cohort goes from synthetic data to locked results (G3) and Chapter 3 .docx; posthoc-fishing, number-drift, undeclared-deviation, spss-import scenarios GREEN |
| **P3 Present** | `research-figures`, `research-poster`, `defense-prep`, `conference-abstract`, `prose-humanizer`, `consistency_audit.py`, `poster_preflight.py`, `lint_prose.py`, `invariants.py`, `committee-simulator` | poster with 3 layouts and defence deck built from fictional cohort; MZL and 87-dpi scenarios GREEN. Done (0.4.0, 22 Nov 2026) |
| **P4 Write** | `manuscript`, `thesis`, `case-report`, `systematic-review`, `literature-review` mode (c), remaining reviewer agents, G4 hook | fictional cohort yields manuscript .docx and thesis .docx passing `/orchestra:audit` |
| **P5 Extend** | `ethics-and-crf`, `journal-selection`, `reviewer-response`, Codex/Antigravity manifests, autorater, landing page; v1.0 release | owner sign-off |

Each phase gets its own implementation plan in `docs/superpowers/plans/`. Phases were re-ordered on 21 Nov 2026 (statistical analysis moved from P3 to a new P2; old P2–P4 became P3–P5).

## 17. Risks and assumptions

| Risk | Mitigation |
|---|---|
| Vietnamese thesis rules differ by school and degree | template matching plus `vn-academic/` defaults the author can override in `project.yaml` |
| Literature APIs rate-limit or change | backoff, cached results in `ledgers/`, clear "not verified" status instead of silent pass |
| Users without Python or R | skills still work; any check that could not run is reported as "not checked by script", never as passed |
| Hook false positives in `phi-guard` | weak signals ask instead of block; tool allowlist in `~/.claude/phi-guard-allow.txt` |
| Humanizer altering meaning | invariants plus per-paragraph revert |
| Skill count raises context cost | short descriptions; detail in references; scenario tests for activation |
| Content in Amelia Le's skills becomes outdated (guidelines change) | `guideline-check` dates each guideline; CHANGELOG entry required for reference updates |
| Claude Code plugin features change | CI validates manifests; `docs/harnesses.md` records the features relied on (skills, agents, hooks, `${CLAUDE_PLUGIN_ROOT}`) |
