# P1 Plan the Study Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A user can go from a clinical idea to a verified evidence base, an appraised literature set, a written Chapter 1 / background, a protocol, a sample size with SAP and a list of current guidelines, inside one project folder.

**Architecture:** Port Amelia Le's five research-methods skills (version 18 Nov 2026) into English skill bodies of at most 500 words, with every rule preserved in plugin-level `references/`. Add `guideline-check`, `literature-review` (modes a and b), `samplesize.py` and `review_lint.py`. Spec: `docs/superpowers/specs/2026-11-20-clinical-research-orchestra-design.md`. Depends on P0 (`docs/superpowers/plans/2026-11-20-p0-foundation.md`) being complete.

**Tech Stack:** Markdown skills, Python 3.10+ stdlib scripts, `unittest`, Claude Code CLI for scenarios.

## Global Constraints

- Everything in P0's Global Constraints applies.
- Frontmatter `description` values are single-quoted YAML strings (escape ' as ''); `tools/lint_skills.py` rejects unquoted values containing `: ` or ` #`.
- Skill names drop the `-vi` suffix: `research-question`, `literature-search`, `critical-appraisal`, `protocol-design`, `sample-size-sap`.
- Skill bodies in English, ≤ 500 words (enforced by `tools/lint_skills.py`). Descriptions carry Vietnamese and English triggers.
- Output language of research documents follows `project.yaml → language.output`; chat follows the user.
- Every ported skill begins its body with the line: `Methods content by Amelia Le (co-author), adapted for clinical-research-orchestra.`
- No rule, step, threshold, error row or citation from the source skills may be lost. Each port task proves this with a traceability table (`_sources/inventory/<skill>.md`, not committed) where every source item points to its new location.
- Judgement-call thresholds are written as defaults the author may override, never as standards.
- Output paths in a project: `01_question/question.md`; `02_evidence/search-strategy.md`, `02_evidence/evidence-table.md`, `02_evidence/evidence-map.md`, `02_evidence/gaps.md`, `02_evidence/appraisal/<ref-id>.md`, `02_evidence/guidelines.md`; `03_protocol/protocol.md`, `03_protocol/variables.md`, `03_protocol/sample-size.md`, `03_protocol/sap.md`; `06_writing/thesis/ch1-literature-review.md` or `06_writing/manuscript/background.md`.
- Every reference that enters a project goes through `search_lit.py add` and `verify_refs.py`; skills never write a PMID or DOI from memory.

---

## File structure (P1)

```
plugins/orchestra/references/
  evidence-policy.md                 source order, verification rules, nomenclature check (shared)
  judgement-defaults.md              labelled default thresholds
  appraisal-tools/{design-tree.md, tools-by-design.md, tool-domains.md, tool-references.md, source-credibility.md}
  design/{design-selection.md, bias-confounding.md, protocol-template.md}
  statistics/{sample-size-formulas.md, test-selection.md, sap-template.md, evidence-queries.md}
  literature/{search-strategy.md, evidence-output-template.md, review-writing.md, vn-chapter1.md}
  reporting-guidelines/{index.md, guidelines.json}
  workflows/{research-question.md, literature-search.md, critical-appraisal.md, protocol-design.md, sample-size-sap.md}
plugins/orchestra/scripts/samplesize.py
plugins/orchestra/scripts/review_lint.py
plugins/orchestra/skills/{research-question, literature-search, critical-appraisal, protocol-design,
                          sample-size-sap, guideline-check, literature-review, review, appraise}/SKILL.md
tests/unit/{test_samplesize.py, test_review_lint.py, test_reference_library.py}
tests/scenarios/{pmos-nomenclature.md, sample-size-lower-ci.md, reverse-causation.md, chapter1-paper-by-paper.md}
examples/fictional-cohort/
```

`workflows/<skill>.md` holds the full step-by-step procedure that does not fit in the 500-word body; the body names the steps and links to it with `${CLAUDE_PLUGIN_ROOT}/references/workflows/<skill>.md`.

---

### Task 1: Import sources and build rule inventories

**Files:**
- Create (not committed, `_sources/` is git-ignored): `_sources/amelia/<skill>/...`, `_sources/amelia-change-notes.txt`, `_sources/inventory/<skill>.md`

- [ ] **Step 1: Unzip the five skills into `_sources/amelia/`**

```bash
mkdir -p _sources/amelia _sources/inventory
for z in research-question-refinement-vi literature-evidence-research-vi protocol-design-vi sample-size-planning-vi critical-appraisal-vi; do
  unzip -o -q "C:/Users/Admin/Downloads/$z.zip" -d "_sources/amelia/$z"
done
find _sources/amelia -type f | sort
```

Expected: 5 `SKILL.md` files, 17 reference files, `scripts/samplesize.py`.

- [ ] **Step 2: Extract the change notes to text**

```bash
python -I -c "
import zipfile,re,sys
sys.stdout.reconfigure(encoding='utf-8')
x=zipfile.ZipFile(sys.argv[1]).read('word/document.xml').decode('utf8')
for p in re.findall(r'<w:p[ >].*?</w:p>',x,re.S):
  t=''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>',p))
  if t.strip(): print(t)
" "C:/Users/Admin/Downloads/Skill changes and justification-AI tools in medical research.docx" > _sources/amelia-change-notes.txt
```

Expected: about 270 lines, starting "Vietnamese Health-Research Skills: Summary of Changes and Justification".

- [ ] **Step 3: Write one inventory per skill**

For each source `SKILL.md` and each of its reference files, write `_sources/inventory/<new-skill-name>.md` as a table with one row per atomic item: every numbered step, every rule sentence that uses "must/không được/luôn/never/bắt buộc", every threshold, every row of every error/pitfall table, every citation, every output-file instruction, every "Giả định" rule. Columns: `#`, `source file:line`, `item (Vietnamese, verbatim or near-verbatim)`, `new location` (left empty now).
Also add, to the matching inventory, every item from `_sources/amelia-change-notes.txt` sections "research-question-refinement-vi changes", "literature-evidence-research-vi changes", "protocol-design-vi changes", "sample-size-planning-vi changes", "critical-appraisal-vi (new)", "Judgement-call thresholds".

Expected: five inventory files; each has at least as many rows as the source has numbered steps plus error-table rows.

No commit (sources are not part of the repo).

---

### Task 2: Shared evidence policy and judgement defaults

**Files:**
- Create: `plugins/orchestra/references/evidence-policy.md`, `plugins/orchestra/references/judgement-defaults.md`
- Test: `tests/unit/test_reference_library.py`

**Interfaces:**
- Produces: the two files every later skill links to.

- [ ] **Step 1: Write the failing test**

```python
import json
import re
import unittest

import _paths  # noqa: F401
from _paths import ROOT

REF = ROOT / "plugins" / "orchestra" / "references"


class TestReferenceLibrary(unittest.TestCase):
    def test_evidence_policy_has_required_rules(self):
        t = (REF / "evidence-policy.md").read_text(encoding="utf-8")
        for needle in ["search_lit.py", "verify_refs.py", "Nomenclature check", "retract",
                       "abstract only", "OpenEvidence", "Europe PMC", "Crossref"]:
            self.assertIn(needle, t, needle)

    def test_judgement_defaults_are_labelled_defaults(self):
        t = (REF / "judgement-defaults.md").read_text(encoding="utf-8")
        self.assertIn("default", t.lower())
        self.assertIn("override", t.lower())
        for needle in ["5 studies", "300 participants", "12–20", "10–20"]:
            self.assertIn(needle, t, needle)

    def test_every_skill_link_to_references_resolves(self):
        for skill in (ROOT / "plugins" / "orchestra" / "skills").glob("*/SKILL.md"):
            for rel in re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/(references/[\w/\-.]+\.(?:md|json))", skill.read_text(encoding="utf-8")):
                self.assertTrue((ROOT / "plugins" / "orchestra" / rel).is_file(), f"{skill}: {rel}")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s tests/unit -p "test_reference_library.py" -v`
Expected: FAIL / ERROR (`FileNotFoundError` for `evidence-policy.md`).

- [ ] **Step 3: Write `evidence-policy.md`**

Build it from `_sources/amelia/literature-evidence-research-vi/.../reference/evidence-tools.md` (translate to English, keep every rule, including the 5-question self-appraisal gate) plus these sections, written in full:

```markdown
# Evidence policy

## Source order
1. OpenEvidence MCP, if installed and the user has not excluded it.
2. PubMed via `search_lit.py search` (E-utilities).
3. Europe PMC via `search_lit.py search --source europepmc` (also open-access full text).
4. Crossref via `search_lit.py doi` for DOIs without a PMID.
If the user names one source as the only one allowed (for example "chỉ dùng OpenEvidence"), use
only that source and record what could not be checked as a limitation.

## Identifiers
- A work may be cited only if it is in `ledgers/references.json`, added by `search_lit.py add`
  (or by a lookup tool in this session), and checked by `verify_refs.py --write`.
- Never type a PMID or DOI from memory. If a lookup fails, say so; do not substitute.
- `RETRACTED`, `NOT_FOUND` and `MISMATCH` records are not cited until resolved.

## Reading level
Record what was read: abstract only → claims status `verified-abstract`; full text → `verified-fulltext`.
Never describe methods or subgroup results that only the full text contains when you read the abstract only.

## Nomenclature check (step 0 of every search)
Before searching: list current and former names of the condition and intervention, MeSH terms and
their recent changes, Vietnamese and English terms, abbreviations. Search old and new names.
Regression case: PCOS was renamed PMOS (2026) and a 2026 PLoS Medicine meta-analysis was indexed
under "Metabolic Syndrome", so a standard PCOS query missed it.

## Search plans
Separate planning from writing. Targeted searches find one named primary source (a trial, a scale,
a guideline). Exploratory searches return ranked lists for context. Record both in
`02_evidence/search-strategy.md` with PRISMA-S fields (databases, dates, full strings, limits, counts).

## Self-appraisal gate
(the five questions from the source evidence-tools.md, translated)
```

- [ ] **Step 4: Write `judgement-defaults.md`**

Translate the "Judgement-call thresholds" section of `_sources/amelia-change-notes.txt` into a table with columns `Threshold | Default | Used by | Why it is only a default`. It must contain: fewer than 5 studies or fewer than 300 participants = premature review; n above about 3 × feasible recruitment = infeasible; outcome ≥ 10% = common; 12–20 interviews; pilot questionnaire on 10–20 people; illustrative RR ≤ 0.90 / ≥ 1.10. Open with: "These are defaults from experience, not standards. The author may override any of them; record the override in decisions.md."

- [ ] **Step 5: Run tests**

Run: `python -m unittest discover -s tests/unit -v`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add plugins/orchestra/references/evidence-policy.md plugins/orchestra/references/judgement-defaults.md tests/unit/test_reference_library.py
git commit -m "docs(orchestra): shared evidence policy and judgement defaults" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: `samplesize.py`

**Files:**
- Create: `plugins/orchestra/scripts/samplesize.py` (copied unchanged), `tests/unit/test_samplesize.py`

**Interfaces:**
- Produces: CLI `samplesize.py <design> [options] --json` with designs `two-means, two-props, one-prop, one-mean, paired, correlation, survival, noninf-props, noninf-means, equiv-means, diag, prevalence, regression-epv, power, sensitivity`. JSON keys include `n1_final`, `n2_final`, `n_total_final`.

- [ ] **Step 1: Write the failing test**

```python
import json
import subprocess
import sys
import unittest

import _paths  # noqa: F401
from _paths import ORCH_SCRIPTS

SCRIPT = ORCH_SCRIPTS / "samplesize.py"


def run(*args):
    r = subprocess.run([sys.executable, str(SCRIPT), *args, "--json"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


class TestSampleSize(unittest.TestCase):
    def test_two_means(self):
        out = run("two-means", "--delta", "5", "--sd", "12")
        self.assertEqual((out["n1_final"], out["n_total_final"]), (92, 184))

    def test_dropout_inflates_raw_n_before_rounding(self):
        out = run("two-means", "--delta", "5", "--sd", "12", "--dropout", "0.15")
        self.assertEqual(out["n1_final"], 108)

    def test_two_props(self):
        self.assertEqual(run("two-props", "--p1", "0.30", "--p2", "0.45")["n1_final"], 163)

    def test_prevalence(self):
        self.assertEqual(run("prevalence", "--p", "0.15", "--width", "0.05")["n_total_final"], 196)

    def test_every_documented_example_runs(self):
        doc = SCRIPT.read_text(encoding="utf-8").split('"""')[1]
        for line in doc.splitlines():
            line = line.strip()
            if line.startswith("python samplesize.py "):
                args = line.split()[2:]
                r = subprocess.run([sys.executable, str(SCRIPT), *args, "--json"], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, f"{line}\n{r.stderr}")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s tests/unit -p "test_samplesize.py" -v`
Expected: FAIL (`AssertionError` from non-zero return code: file not found).

- [ ] **Step 3: Copy the script unchanged**

```bash
cp _sources/amelia/sample-size-planning-vi/sample-size-planning-vi/scripts/samplesize.py plugins/orchestra/scripts/samplesize.py
```

- [ ] **Step 4: Run tests**

Run: `python -m unittest discover -s tests/unit -v`
Expected: all PASS. If `test_every_documented_example_runs` fails for an example, do not change the script's maths: report the failing example to the owner and mark that example skipped with the reason.

- [ ] **Step 5: Commit**

```bash
git add plugins/orchestra/scripts/samplesize.py tests/unit/test_samplesize.py
git commit -m "feat(orchestra): sample size calculator (Amelia Le) with golden tests" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Port `research-question`

**Files:**
- Create: `plugins/orchestra/skills/research-question/SKILL.md`, `plugins/orchestra/references/workflows/research-question.md`
- Source: `_sources/amelia/research-question-refinement-vi/.../SKILL.md`, inventory `_sources/inventory/research-question.md`

- [ ] **Step 1: Write the SKILL.md frontmatter exactly**

```markdown
---
name: research-question
description: 'Use when a medical student, doctor or health worker has a clinical idea, observation or topic and needs a researchable question, PICO/PECO, objectives, hypotheses or a title, or asks whether a topic is feasible, or when stated objectives do not match the design. Triggers: "ý tưởng nghiên cứu", "câu hỏi nghiên cứu", "PICO", "PECO", "mục tiêu nghiên cứu", "giả thuyết nghiên cứu", "đặt tên đề tài", "chọn đề tài luận văn", "đề tài cơ sở", "đề tài này có làm được không", "FINER", "tôi muốn nghiên cứu về", "research question", "research idea", "is this topic feasible".'
---
```

- [ ] **Step 2: Write the body (≤ 500 words) with these sections, in this order**

1. Attribution line (Global Constraints).
2. **Core rule**: the question must be answerable with data the user can actually collect and must not already be answered by a textbook, guideline or recent systematic review (a "lookup question" is not a research question).
3. **Inputs**: `project.yaml`; nothing else required. Use the Skill tool with `research-project-setup` first if no project exists.
4. **Steps** (one line each, details in the workflow file): 0 one combined intake question (six items: clinical idea, site, purpose, time, data sources, patient numbers; do not re-ask what was given); 1 broad topic → explore 3–5 angles; 2.0 renamed-condition check (`evidence-policy.md` nomenclature check); 2 regular vs research question test; 3 hypothesis first, then PICO/PECO; 4 FINER with the data × idea novelty matrix; 5 "So what?" with the AND/BUT/HOW story; 6 assumptions list; 7 qualitative questions and the "n = 30" myth check; 8 objectives aligned with design; 9 title options.
5. **"Just do it" rule**: proceed with an **Assumptions / Giả định** box and record it in `decisions.md`.
6. **Output**: `01_question/question.md` in `language.output`; update `STATUS.md` row 1 to `doing`; ask the author to approve, then `gate.py open <project> G1 --by "<author>"`.
7. **Hand-off**: next skill `literature-search`.
8. **Workflow link**: `${CLAUDE_PLUGIN_ROOT}/references/workflows/research-question.md`.

- [ ] **Step 3: Write `references/workflows/research-question.md`**

Translate every inventory item not already in the body into English under headings that match the body's step numbers. Keep Vietnamese example phrases in quotes where they are trigger phrases or sample wording for Vietnamese output. Keep all citations (for example Nguyễn Văn Tuấn 2018; *Critical Thinking in Academic Research*; *Choosing & Using Sources*, ch. 1) with their original wording.

- [ ] **Step 4: Fill the traceability column and lint**

Fill `new location` for every row of `_sources/inventory/research-question.md` (`SKILL.md §n` or `workflows/research-question.md §n`).
Run: `python tools/lint_skills.py` and `python -m unittest discover -s tests/unit -v`
Expected: 0 lint errors; all tests PASS; no inventory row with an empty `new location`.

- [ ] **Step 5: Commit**

```bash
git add plugins/orchestra/skills/research-question plugins/orchestra/references/workflows/research-question.md
git commit -m "feat(orchestra): research-question skill (ported from Amelia Le)" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Port `literature-search`

**Files:**
- Create: `plugins/orchestra/skills/literature-search/SKILL.md`, `plugins/orchestra/references/workflows/literature-search.md`, `plugins/orchestra/references/literature/search-strategy.md`, `plugins/orchestra/references/literature/evidence-output-template.md`
- Source: `literature-evidence-research-vi` SKILL.md, `reference/search-strategy.md`, `reference/output-template.md` (its `evidence-tools.md` already went to `evidence-policy.md` in Task 2).

- [ ] **Step 1: Frontmatter**

```markdown
---
name: literature-search
description: 'Use when a research question or topic needs its literature found, verified and organised: search strategy, evidence table, evidence map, research gaps, or "what have previous studies done". Triggers: "tìm tài liệu cho đề tài", "tìm y văn", "chiến lược tìm kiếm", "bảng tổng hợp nghiên cứu", "evidence table", "bản đồ bằng chứng", "evidence map", "research gap", "khoảng trống nghiên cứu", "các nghiên cứu trước đã làm gì", "search strategy", "find studies on"; or after the research question is approved and before the protocol.'
---
```

Writing the review as prose is out of scope here: the body ends with "To write Chapter 1 or a background section, use the Skill tool with `literature-review`."

- [ ] **Step 2: Body (≤ 500 words), sections in order**

1. Attribution line. 2. Core rule: every claim traces to a PMID/DOI returned by a tool in this session (`evidence-policy.md`). 3. Scope: structured narrative or scoping evidence synthesis; a true systematic review needs PROSPERO, two independent screeners and PRISMA 2020 → say so and point to `systematic-review` (phase P3). 4. Steps: 0 nomenclature check; 1 search plan (targeted vs exploratory) → `02_evidence/search-strategy.md`; 2 run searches with `search_lit.py search`, add chosen records with `search_lit.py add <project> <pmids>`; 3 `verify_refs.py <project> --write`; 4a evidence table with RoB column; 4b source credibility (retractions, predatory journals, COI); 4c appraise key studies with the Skill tool `critical-appraisal`; 5 GRADE / GRADE-CERQual certainty; 6 apples-vs-pears (I², prediction interval); 7 read CIs by clinical importance; 8 evidence map and gaps → `02_evidence/evidence-map.md`, `02_evidence/gaps.md`; 9 PRISMA-S fields and ICMJE AI-use note. 5. "Just do it" rule. 6. Outputs and `STATUS.md` row 2. 7. Workflow link.

- [ ] **Step 3: Workflow and literature references**

`workflows/literature-search.md`: all remaining inventory items, in English, by step. `literature/search-strategy.md` and `literature/evidence-output-template.md`: translations of the source reference files with every row and example kept; output templates show both a Vietnamese and an English heading set.

- [ ] **Step 4: Traceability, lint, tests**

Fill the inventory; run `python tools/lint_skills.py` and `python -m unittest discover -s tests/unit -v`.
Expected: 0 lint errors, all PASS (including `test_every_skill_link_to_references_resolves`), no empty inventory row.

- [ ] **Step 5: Commit**

```bash
git add plugins/orchestra/skills/literature-search plugins/orchestra/references/workflows/literature-search.md plugins/orchestra/references/literature
git commit -m "feat(orchestra): literature-search skill (ported from Amelia Le)" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Port `critical-appraisal` and add `/orchestra:appraise`

**Files:**
- Create: `plugins/orchestra/skills/critical-appraisal/SKILL.md`, `plugins/orchestra/skills/appraise/SKILL.md`, `plugins/orchestra/references/workflows/critical-appraisal.md`, `plugins/orchestra/references/appraisal-tools/{design-tree.md, tools-by-design.md, tool-domains.md, tool-references.md, source-credibility.md}`

- [ ] **Step 1: Frontmatter (model-invoked)**

```markdown
---
name: critical-appraisal
description: 'Use when a research paper or a body of evidence must be appraised for trustworthiness, value and relevance before it is used, with the tool matched to the real study design, including journal club. Triggers: "thẩm định y văn", "đánh giá chất lượng bài báo", "bài này có tin được không", "đánh giá phê bình", "critical appraisal", "risk of bias", "nguy cơ sai lệch", "RoB 2", "ROBINS-I", "ROBINS-E", "Newcastle-Ottawa", "NOS", "AXIS", "CASP", "JBI", "AMSTAR 2", "QUADAS", "PROBAST", "GRADE", "CERQual", "journal club"; or when literature-search reaches its appraisal step.'
---
```

- [ ] **Step 2: Body (≤ 500 words)**

Sections: attribution; three questions (trustworthy? valuable — effect size with 95% CI and clinical meaning? relevant?); rule "appraise the real design, not the label" with `design-tree.md`; tool by design (`tools-by-design.md`); rule "a reporting checklist (CONSORT, STROBE, PRISMA, SRQR) is not an appraisal tool; never sum items into a score; missing reporting = 'unclear / Không rõ'"; inputs (ledger record; full text if available, else "preliminary appraisal from abstract" stated at the top); 7-step workflow summary; output `02_evidence/appraisal/<ref-id>.md` and update the reference record's `design` and `rob` fields; standalone journal-club mode (no project: write `appraisal-<first-author><year>.md` next to the PDF, and a .docx via the `docx` skill if the user asks); workflow link.

- [ ] **Step 3: References**

Translate the five reference files into `references/appraisal-tools/`, keeping every tool, domain and citation. Apply the correction in the change notes: QUADAS-3 cited as Whiting et al., Ann Intern Med, February 2026, four domains (Participants, Index Test, Target Condition, Analysis). Write `workflows/critical-appraisal.md` from the remaining inventory items.

- [ ] **Step 4: `/orchestra:appraise` command**

```markdown
---
name: appraise
description: 'Appraise one research paper (PDF, PMID or DOI) for journal club or for the project''s evidence table (thẩm định một bài báo).'
disable-model-invocation: true
---

Use the Skill tool with `critical-appraisal` on the paper the user gives. If a project folder exists,
first add the paper with `search_lit.py add` and verify it; otherwise run in standalone journal-club mode.
Reply in the user's language with the three-question verdict first.
```

- [ ] **Step 5: Traceability, lint, tests, commit**

Run lint and tests as in Task 5 (expected 0 errors, all PASS, no empty inventory row).

```bash
git add plugins/orchestra/skills/critical-appraisal plugins/orchestra/skills/appraise plugins/orchestra/references/appraisal-tools plugins/orchestra/references/workflows/critical-appraisal.md
git commit -m "feat(orchestra): critical-appraisal skill and /orchestra:appraise (ported from Amelia Le)" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Port `protocol-design`

**Files:**
- Create: `plugins/orchestra/skills/protocol-design/SKILL.md`, `plugins/orchestra/references/workflows/protocol-design.md`, `plugins/orchestra/references/design/{design-selection.md, bias-confounding.md, protocol-template.md}`

- [ ] **Step 1: Frontmatter**

```markdown
---
name: protocol-design
description: 'Use when a study must be designed or a protocol drafted or reviewed: design choice, population, inclusion and exclusion criteria, sampling, outcomes, variables, bias and confounding, "đề cương nghiên cứu" or "chương 2 đối tượng và phương pháp". Triggers: "thiết kế nghiên cứu", "chọn thiết kế", "đề cương", "protocol", "tiêu chuẩn lựa chọn", "tiêu chuẩn loại trừ", "biến số nghiên cứu", "bảng biến số", "sai số", "yếu tố nhiễu", "confounder", "bias", "cohort hay case-control", "hồi cứu hay tiến cứu", "SPIRIT", "bảng dự kiến kết quả", "study design", "review my protocol".'
---
```

- [ ] **Step 2: Body (≤ 500 words)**

Sections: attribution; core rule "design follows the question; every choice states why and what it costs"; scope (sample size → `sample-size-sap`; ethics/CRF → `ethics-and-crf`, phase P4); inputs `01_question/question.md`, `02_evidence/*`, gate G1 open (`gate.py check <project> G1`; if closed, say so and stop unless waived); steps: 1 design on two axes (time direction vs design type; "prospective" ≠ "cohort") via `design/design-selection.md`; 2 diagnostic criteria with citations (e.g. ADA, KDIGO, DSM-5 current versions via `guideline-check`); 3 population, eligibility, sampling, representativeness only for prevalence aims; 4 outcomes and variables table → `03_protocol/variables.md`; 5 measurement and questionnaire rules; 6 bias, confounding, reverse causation (`design/bias-confounding.md`), Bradford Hill; 7 intervention reporting (TIDieR, CERT) and STROBE-Equity where relevant; 8 qualitative protocol essentials; 9 SPIRIT 2025 map (34 items) and CONSORT 2025 for trials, with the open caveat that the full SPIRIT 2013→2025 numbering map is unverified; 10 dummy tables. Output `03_protocol/protocol.md`; gate G2 after `sample-size-sap`; workflow link.

- [ ] **Step 3: References, traceability, lint, tests, commit**

Translate the three reference files into `references/design/`, all rows and the 5 new error rows kept. Write the workflow file. Fill inventory, run lint and tests (0 errors, all PASS).

```bash
git add plugins/orchestra/skills/protocol-design plugins/orchestra/references/design plugins/orchestra/references/workflows/protocol-design.md
git commit -m "feat(orchestra): protocol-design skill (ported from Amelia Le)" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 8: Port `sample-size-sap`

**Files:**
- Create: `plugins/orchestra/skills/sample-size-sap/SKILL.md`, `plugins/orchestra/references/workflows/sample-size-sap.md`, `plugins/orchestra/references/statistics/{sample-size-formulas.md, test-selection.md, sap-template.md, evidence-queries.md}`

- [ ] **Step 1: Frontmatter**

```markdown
---
name: sample-size-sap
description: 'Use when a sample size must be calculated, explained or justified, power computed, a Statistical Analysis Plan (SAP) written, or a statistical test chosen for a clinical or epidemiological study. Triggers: "tính cỡ mẫu", "cỡ mẫu bao nhiêu", "n bao nhiêu là đủ", "công thức cỡ mẫu", "giải thích cỡ mẫu cho hội đồng", "kế hoạch phân tích thống kê", "chọn test thống kê", "dùng test gì", "sample size", "power", "SAP", "effect size", "MCID", "non-inferiority margin", "cluster ICC"; or when a protocol lacks a sample-size section.'
---
```

- [ ] **Step 2: Body (≤ 500 words)**

Sections: attribution; core rule (n follows design, outcome type, effect size, variability, α and power; "30 is enough" is a myth; every parameter has a source; the test is in the SAP); inputs `03_protocol/protocol.md`, `02_evidence/*`; 7-step chain (question → primary outcome → effect measure → target difference via DELTA2 source order MCID > stakeholder opinion > pilot > cautious prior evidence → α/power/dropout → n with sensitivity → test and SAP); script use exactly:

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/samplesize.py" <design> [options] --json
python "${CLAUDE_PLUGIN_ROOT}/scripts/samplesize.py" sensitivity --design <design> --vary <param> --values a,b,c
```

with the rule "report n exactly as the script returns it; the script divides the unrounded n by (1 − dropout) and then rounds up; never round first"; always run a sensitivity table on the most uncertain parameter and `power` when n is fixed; descriptive and analytic aims both → compute both, take the larger; qualitative studies → information power and saturation (Malterud 2016; Hennink & Kaiser 2022), no formula; pilot/feasibility trials sized by precision, no efficacy power; ANCOVA n × (1 − r²); matched case-control caveat; infeasibility rule (n above about 3 × feasible recruitment, a default from `judgement-defaults.md`). Outputs `03_protocol/sample-size.md` (with a "how to explain this to the committee" paragraph in `language.output`) and `03_protocol/sap.md`; then ask the author to approve and run `gate.py open <project> G2 --by "<author>"`. Workflow link.

- [ ] **Step 3: References, traceability, lint, tests, commit**

Translate the four reference files (`openevidence-queries.md` becomes `statistics/evidence-queries.md`, generalised to "evidence source" while keeping every query). Write the workflow file with the 5 new error rows. Fill inventory, run lint and tests.

```bash
git add plugins/orchestra/skills/sample-size-sap plugins/orchestra/references/statistics plugins/orchestra/references/workflows/sample-size-sap.md
git commit -m "feat(orchestra): sample-size-sap skill (ported from Amelia Le)" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 9: Reporting-guideline library and `guideline-check`

**Files:**
- Create: `plugins/orchestra/references/reporting-guidelines/guidelines.json`, `plugins/orchestra/references/reporting-guidelines/index.md`, `plugins/orchestra/skills/guideline-check/SKILL.md`
- Modify: `tests/unit/test_reference_library.py`

**Interfaces:**
- Produces: `guidelines.json` = `{"references": [record, ...]}` in the ledger schema (so `verify_refs.py` can check it), each record with extra fields `guideline` (the `reporting_guideline` code used in `project.yaml`), `designs` (list), `version`, `items`.

- [ ] **Step 1: Add the failing test**

Append to `TestReferenceLibrary` in `tests/unit/test_reference_library.py`:

```python
    def test_guideline_library_covers_every_project_guideline(self):
        import init_project
        lib = json.loads((REF / "reporting-guidelines" / "guidelines.json").read_text(encoding="utf-8"))
        codes = {r["guideline"] for r in lib["references"]}
        for code in set(init_project.GUIDELINE_BY_DESIGN.values()):
            self.assertIn(code, codes, code)
        from crolib import ledgers
        for r in lib["references"]:
            self.assertEqual(ledgers.validate_reference(r), [], r["id"])
            self.assertTrue(r["verified_by"] and "VERIFIED" in r["verified_by"], r["id"])
```

Run: `python -m unittest discover -s tests/unit -p "test_reference_library.py" -v`
Expected: ERROR (`FileNotFoundError` for `guidelines.json`).

- [ ] **Step 2: Build `guidelines.json` from live lookups**

Required guideline codes: `CONSORT-2025`, `SPIRIT-2025`, `STROBE`, `STARD-2015`, `TRIPOD+AI`, `PRISMA-2020`, `PRISMA-ScR`, `PRISMA-S`, `CARE`, `SRQR`, `COREQ`, `GRAMMS`, `SANRA`, `CHEERS-2022`, `TIDieR`, `CERT`, `STROBE-Equity`. Starting points to look up (confirm every one; do not trust these strings): CONSORT 2025 BMJ 2025;388:e081123; SPIRIT 2025 BMJ 2025;389:e081477; PRISMA-S Syst Rev 2021;10:39; STARD 2015 BMJ 2015;351:h5527; PRISMA 2020 BMJ 2021;372:n71; TRIPOD+AI BMJ 2024;385:e078378; CHEERS 2022 BMJ 2022;376:e067975.
For each: `python plugins/orchestra/scripts/search_lit.py search "<guideline name> statement" --max 5`, pick the primary statement paper, then collect records with `python plugins/orchestra/scripts/search_lit.py fetch <pmid>` and add the extra fields by hand. Then:

Run: `python plugins/orchestra/scripts/verify_refs.py plugins/orchestra/references/reporting-guidelines/guidelines.json --write`
Expected: every record `VERIFIED`. A record that is not verified is fixed or removed before commit.

- [ ] **Step 3: Write `index.md`**

A table `Code | Full name | Version/year | Designs | Items | Citation (from guidelines.json)`, plus a short "How to use" block: the reporting guideline is chosen from the design in `project.yaml`; a checklist is filled with item, page/section location, and `present / absent / not applicable`; it is never summed into a score.

- [ ] **Step 4: Write `guideline-check/SKILL.md`**

```markdown
---
name: guideline-check
description: 'Use when the user asks which clinical or reporting guidelines apply to a study, whether a cited guideline is still current, or needs the reporting checklist for their design; also before a protocol or manuscript is finalised. Triggers: "guideline mới nhất", "cập nhật guideline", "hướng dẫn điều trị mới nhất", "khuyến cáo hiện hành", "checklist báo cáo", "dùng checklist nào", "CONSORT", "STROBE", "PRISMA", "STARD", "TRIPOD", "CARE", "SPIRIT", "reporting guideline", "is this guideline current", "which checklist".'
---

# Guideline check

Requested by Amelia Le: keep the guidelines a study relies on current.

## Two kinds of guideline
- **Clinical guidelines** used for definitions, diagnostic criteria and comparators (for example ADA,
  KDIGO, ESC, Bộ Y tế). Find the newest version through the evidence sources in
  `${CLAUDE_PLUGIN_ROOT}/references/evidence-policy.md`; record issuing body, year, version, DOI or
  official URL, and the date you checked.
- **Reporting guidelines** chosen from `project.yaml → design` using
  `${CLAUDE_PLUGIN_ROOT}/references/reporting-guidelines/index.md`; citations come from
  `guidelines.json` (already verified).

## Steps
1. Read `project.yaml`, `01_question/question.md`, `03_protocol/protocol.md` if present.
2. List every guideline the project cites or should cite. For each clinical guideline, search for a
   newer version or a published update; never state "latest" without a lookup made today.
3. Flag outdated guidelines anywhere in the project (`grep` the project for the guideline name and year).
4. Write `02_evidence/guidelines.md` in `language.output`: table `Guideline | Kind | Version used |
   Current version | Checked on | Action`.
5. Add clinical-guideline papers to the ledger with `search_lit.py add` and verify them.
6. If a reporting-guideline item mapping is uncertain (for example SPIRIT 2013 → 2025 numbering),
   say so in the table instead of guessing.
```

- [ ] **Step 5: Run tests and lint**

Run: `python -m unittest discover -s tests/unit -v` and `python tools/lint_skills.py`
Expected: all PASS, 0 lint errors.

- [ ] **Step 6: Commit**

```bash
git add plugins/orchestra/references/reporting-guidelines plugins/orchestra/skills/guideline-check tests/unit/test_reference_library.py
git commit -m "feat(orchestra): verified reporting-guideline library and guideline-check skill" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 10: `review_lint.py`

**Files:**
- Create: `plugins/orchestra/scripts/review_lint.py`
- Test: `tests/unit/test_review_lint.py`

**Interfaces:**
- Produces:
  - `review_lint.paragraphs(text: str) -> list[str]` (prose paragraphs; skips headings `#`, tables `|`, list items `-`/`*`/`1.`, code fences)
  - `review_lint.sentences(par: str) -> list[str]`
  - `review_lint.author_led(sentence: str) -> bool`
  - `review_lint.lint(text: str) -> dict` → `{"paragraphs": n, "flagged": [{"index": i, "start": "first 60 chars"}], "blocking": bool}`
  - CLI `review_lint.py FILE [--json]` → exit 1 when `blocking`.
- Rule: a paragraph is flagged when it has ≥ 2 author-led sentences and they are ≥ 50% of its sentences. `blocking` is true when ≥ 2 paragraphs are flagged and flagged paragraphs are ≥ 30% of prose paragraphs. Finding code `E-LIT`.

- [ ] **Step 1: Write the failing test**

```python
import unittest

import _paths  # noqa: F401
import review_lint as rl

LISTING_EN = ("Smith et al. (2019) studied 120 women and found lower weight. "
              "Nguyen and Tran (2021) reported improved ovulation. "
              "Le et al. (2022) showed no change in insulin.")
LISTING_VI = ("Tác giả Nguyễn Văn A (2019) nghiên cứu 120 phụ nữ và thấy cân nặng giảm. "
              "Năm 2021, Trần Thị B báo cáo tỉ lệ rụng trứng tăng. "
              "Nghiên cứu của Lê C (2022) không thấy thay đổi insulin.")
THEMATIC = ("Lifestyle programmes reduce weight by 3 to 5 kg across trials [@smith2019; @le2022]. "
            "Effects on ovulation are less consistent and depend on baseline BMI [@nguyen2021]. "
            "No trial was powered for live birth, which leaves the key outcome untested.")


class TestReviewLint(unittest.TestCase):
    def test_author_led(self):
        self.assertTrue(rl.author_led("Smith et al. (2019) studied 120 women."))
        self.assertTrue(rl.author_led("Tác giả Nguyễn Văn A (2019) nghiên cứu 120 phụ nữ."))
        self.assertTrue(rl.author_led("Năm 2021, Trần Thị B báo cáo tỉ lệ tăng."))
        self.assertTrue(rl.author_led("Nghiên cứu của Lê C (2022) không thấy thay đổi."))
        self.assertFalse(rl.author_led("Lifestyle programmes reduce weight by 3 to 5 kg [@a]."))

    def test_sentences_do_not_split_et_al(self):
        self.assertEqual(len(rl.sentences(LISTING_EN)), 3)

    def test_paragraphs_skip_headings_tables_lists(self):
        text = "# Heading\n\n" + THEMATIC + "\n\n| a | b |\n|---|---|\n\n- item\n\n" + LISTING_EN
        self.assertEqual(len(rl.paragraphs(text)), 2)

    def test_listing_chapter_blocks(self):
        rep = rl.lint("\n\n".join([LISTING_EN, LISTING_VI, THEMATIC]))
        self.assertEqual(len(rep["flagged"]), 2)
        self.assertTrue(rep["blocking"])

    def test_thematic_chapter_passes(self):
        rep = rl.lint("\n\n".join([THEMATIC, THEMATIC, LISTING_EN, THEMATIC, THEMATIC, THEMATIC, THEMATIC]))
        self.assertEqual(len(rep["flagged"]), 1)
        self.assertFalse(rep["blocking"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s tests/unit -p "test_review_lint.py" -v`
Expected: ERROR `No module named 'review_lint'`.

- [ ] **Step 3: Write the implementation**

```python
#!/usr/bin/env python3
"""Flag literature reviews written paper by paper ("Author A found... Author B found...").

A paragraph is flagged when >= 2 sentences, and >= 50% of its sentences, open with an author or
study as the subject. The file blocks (E-LIT) when >= 2 paragraphs and >= 30% of prose paragraphs
are flagged.  python review_lint.py chapter1.md [--json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

UP = "A-ZÀ-ỸĐ"
PATTERNS = [
    re.compile(rf"^[{UP}][\w'’\-]+(?:\s+[{UP}][\w'’\-]+)*\s+(?:et al\.?|and [{UP}][\w'’\-]+|&\s*[{UP}][\w'’\-]+|và cộng sự|và cs\.?)?\s*\(\d{{4}}[a-z]?\)"),
    re.compile(rf"^[{UP}][\w'’\-]+\s+et al\."),
    re.compile(rf"^(?:In\s+)?(?:a|the|their|his|her)\s+(?:\d{{4}}\s+)?(?:study|trial|cohort|review)\s+(?:by|of)\s+[{UP}]", re.I),
    re.compile(rf"^(?:Tác giả|Nghiên cứu của|Theo nghiên cứu của|Theo tác giả)\s+[{UP}]"),
    re.compile(rf"^Năm\s+\d{{4}},?\s+(?:tác giả\s+)?[{UP}]"),
]
SPLIT = re.compile(rf"(?<=[.!?])\s+(?=[{UP}])")


def paragraphs(text: str) -> list[str]:
    out, in_code = [], False
    for block in re.split(r"\n\s*\n", text):
        b = block.strip()
        if b.startswith("```"):
            in_code = not in_code if b.count("```") == 1 else in_code
            continue
        if in_code or not b or b[0] in "#|>" or re.match(r"^([-*+]|\d+[.)])\s", b):
            continue
        out.append(" ".join(b.split()))
    return out


def sentences(par: str) -> list[str]:
    return [s for s in SPLIT.split(par) if s.strip()]


def author_led(sentence: str) -> bool:
    s = sentence.strip()
    return any(p.search(s) for p in PATTERNS)


def lint(text: str) -> dict:
    pars = paragraphs(text)
    flagged = []
    for i, p in enumerate(pars):
        ss = sentences(p)
        led = sum(author_led(s) for s in ss)
        if led >= 2 and led / len(ss) >= 0.5:
            flagged.append({"index": i, "start": p[:60]})
    blocking = len(flagged) >= 2 and len(flagged) / max(len(pars), 1) >= 0.3
    return {"paragraphs": len(pars), "flagged": flagged, "blocking": blocking}


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    rep = lint(Path(a.file).read_text(encoding="utf-8"))
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        print(f"review_lint: {len(rep['flagged'])}/{rep['paragraphs']} paragraphs written paper by paper"
              + (" -> E-LIT (block)" if rep["blocking"] else ""))
        for f in rep["flagged"]:
            print(f"  - paragraph {f['index'] + 1}: {f['start']}...")
    return 1 if rep["blocking"] else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests**

Run: `python -m unittest discover -s tests/unit -v`
Expected: all PASS. If `test_author_led` fails on a Vietnamese case, adjust only the pattern list, then re-run.

- [ ] **Step 5: Add `E-LIT` to the spec's error-code table**

In `docs/superpowers/specs/2026-11-20-clinical-research-orchestra-design.md` section 9.2, add the row:
`| E-LIT | literature review structure | review written paper by paper (review_lint.py) |`

- [ ] **Step 6: Commit**

```bash
git add plugins/orchestra/scripts/review_lint.py tests/unit/test_review_lint.py docs/superpowers/specs/2026-11-20-clinical-research-orchestra-design.md
git commit -m "feat(orchestra): review_lint flags paper-by-paper literature reviews" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 11: `literature-review` skill (modes a and b) and `/orchestra:review`

**Files:**
- Create: `plugins/orchestra/skills/literature-review/SKILL.md`, `plugins/orchestra/skills/review/SKILL.md`, `plugins/orchestra/references/literature/review-writing.md`, `plugins/orchestra/references/literature/vn-chapter1.md`

**Interfaces:**
- Consumes: `ledgers/references.json` (verified), `02_evidence/evidence-table.md`, `02_evidence/gaps.md`, `review_lint.py`, `verify_refs.py --cite`.

- [ ] **Step 1: Write `literature-review/SKILL.md`**

```markdown
---
name: literature-review
description: 'Use when literature must be written up as prose: thesis Chapter 1 (tổng quan tài liệu), the background or introduction of a paper, or a narrative review. Triggers: "tổng quan tài liệu", "viết tổng quan", "chương 1 tổng quan", "tổng quan y văn", "viết phần đặt vấn đề", "viết phần mở đầu bài báo", "background", "introduction section", "literature review", "narrative review", "viết bài tổng quan".'
---

# Literature review

Write synthesis, not a catalogue. Every sentence that carries a citation is supported by the cited
record's abstract or full text in the ledger.

## Before writing
1. Require verified evidence: `ledgers/references.json` checked by `verify_refs.py`, an evidence table
   with risk of bias and certainty, and `02_evidence/gaps.md`. If missing, use the Skill tool with
   `literature-search` first.
2. Choose the mode:
   - **a. Thesis Chapter 1** (`06_writing/thesis/ch1-literature-review.md`): structure from
     `${CLAUDE_PLUGIN_ROOT}/references/literature/vn-chapter1.md`, including studies in Vietnam and abroad.
   - **b. Manuscript background** (`06_writing/manuscript/background.md`): 3–5 paragraphs, funnel from
     burden to gap to aim.
   - Scoping or systematic reviews are separate study types (phase P3); say so if asked.
3. Plan in `ledgers/outline.json → section_plan`: one claim per paragraph, its supporting reference ids,
   the certainty from the evidence table.

## Writing rules (detail: `${CLAUDE_PLUGIN_ROOT}/references/literature/review-writing.md`)
- Organise by theme or question, never paper by paper.
- Compare: where studies agree, where they disagree, and why (design, population, risk of bias, measurement).
- Claim strength follows certainty: high → "reduces"; low → "may reduce"; very low → "it is uncertain whether".
- Cite with `[@id]`; only ids that exist in the ledger.
- End on the gap that justifies this study (mode a and b).
- Write in `project.yaml → language.output`. Vietnamese text follows Vietnamese academic conventions.

## Checks before handing back
1. `python "${CLAUDE_PLUGIN_ROOT}/scripts/review_lint.py" <file>`: must not block (E-LIT). Rewrite
   flagged paragraphs thematically and re-run.
2. `python "${CLAUDE_PLUGIN_ROOT}/scripts/verify_refs.py" <project> --cite <file>`: no E-REF findings.
3. Add a claims row for each substantive claim to `ledgers/claims.json` (`kind: background`, status from
   reading level).
4. Report to the author what was checked and anything that could not be verified.
```

- [ ] **Step 2: Write `references/literature/review-writing.md`**

Content (write fully): (1) thematic synthesis method: cluster the evidence table by question → for each cluster state the pooled direction, the range, the certainty, the main disagreement and its likely reason; (2) paragraph template "claim → evidence with comparison → qualification → link"; (3) before/after example in English and in Vietnamese turning a paper-by-paper paragraph into a thematic one (use fictional citations `[@a2019]` style); (4) hedging by certainty table (GRADE high/moderate/low/very low → English and Vietnamese verbs); (5) what not to do: quote abstracts, list sample sizes study by study, cite a review for a primary finding, cite a retracted or unverified work.

- [ ] **Step 3: Write `references/literature/vn-chapter1.md`**

Content (write fully): typical Chapter 1 outline for Vietnamese theses (1.1 concepts and definitions with current guideline criteria; 1.2 epidemiology worldwide and in Vietnam; 1.3 pathophysiology/mechanisms as needed by the question; 1.4 diagnosis and management relevant to the variables; 1.5 studies abroad; 1.6 studies in Vietnam; 1.7 gaps and how this study addresses them), the note that sections 1.5–1.6 must still be synthesised by theme within each section, numbering conventions (1.1, 1.1.1; Bảng 1.1; Hình 1.1), typical length guidance by degree as a default the institution may override, and the rule that Vietnamese and English references follow `project.yaml → citation_style`.

- [ ] **Step 4: Write `/orchestra:review`**

```markdown
---
name: review
description: 'Write the literature review for the current project: thesis Chapter 1 or a manuscript background (viết tổng quan tài liệu).'
disable-model-invocation: true
---

Use the Skill tool with `literature-review` for the project in the current folder. If the evidence is not
yet verified, run the Skill tool with `literature-search` first and say so. Finish with the review_lint and
verify_refs results in the user's language.
```

- [ ] **Step 5: Lint, tests, commit**

Run: `python tools/lint_skills.py` and `python -m unittest discover -s tests/unit -v`
Expected: 0 lint errors; all PASS.

```bash
git add plugins/orchestra/skills/literature-review plugins/orchestra/skills/review plugins/orchestra/references/literature/review-writing.md plugins/orchestra/references/literature/vn-chapter1.md
git commit -m "feat(orchestra): literature-review skill (thesis chapter 1, background) and /orchestra:review" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 12: P1 scenarios (RED/GREEN)

**Files:**
- Create: `tests/scenarios/pmos-nomenclature.md`, `tests/scenarios/sample-size-lower-ci.md`, `tests/scenarios/reverse-causation.md`, `tests/scenarios/chapter1-paper-by-paper.md`, `tests/scenarios/fixtures/chapter1-paper-by-paper/ch1.md`
- Modify: `tests/scenarios/BASELINE.md`

- [ ] **Step 1: Write the four scenario files**

`pmos-nomenclature.md`:

```markdown
# pmos-nomenclature: renamed condition is searched under old and new names
Skill under test: literature-search (step 0 nomenclature check)
Fixtures: a project created with init_project.py, design rct, title "Lifestyle intervention for reproductive-age women with PCOS in Vietnam"
Prompt: Tìm tài liệu cho đề tài này, tập trung vào can thiệp lối sống ở phụ nữ PCOS.
Expected (GREEN):
- The search strategy lists PCOS and PMOS (polyendocrine metabolic ovarian syndrome) and notes MeSH drift.
- The 2026 PLoS Medicine meta-analysis (PMID 42776991) is found by a lookup and enters the ledger verified.
- No PMID appears that was not returned by a tool in the transcript.
Baseline (RED): searches "PCOS" only and misses the 2026 meta-analysis.
```

`sample-size-lower-ci.md`: build the prompt from the "Key test-run failures" section of `_sources/amelia-change-notes.txt` (the case where using the lower CI bound of a pooled OR 4.03 with I² = 73% produced n = 8,230). Expected (GREEN): the skill uses the DELTA2 source order for the target difference, does not use the lower CI bound by default, runs `samplesize.py` (sensitivity table present), and flags infeasibility against expected recruitment using the default in `judgement-defaults.md`. Baseline (RED): reports n ≈ 8,230 without comment.

`reverse-causation.md`: Prompt: "Tôi muốn làm nghiên cứu bệnh chứng: chế độ ăn nhiều đường có làm tăng nguy cơ PCOS không? Thiết kế giúp tôi." Expected (GREEN): protocol-design warns that diet measured after diagnosis may change because of the diagnosis (reverse causation), proposes measuring pre-diagnosis diet or a cohort, and records the limitation. Baseline (RED): accepts the case-control design without the warning.

`chapter1-paper-by-paper.md` with fixture `fixtures/chapter1-paper-by-paper/ch1.md` containing six paragraphs, five of them written "Tác giả X (năm) ... Năm YYYY, Y báo cáo ..." with fictional `[@...]` keys. Prompt: "Sửa lại chương 1 này cho tốt hơn." Expected (GREEN): `review_lint.py` is run, reports E-LIT, the rewrite is thematic, `review_lint.py` passes on the result, and no new citation key is invented. Baseline (RED): polishes wording but keeps the paper-by-paper structure.

- [ ] **Step 2: Run each scenario RED then GREEN**

Follow `tests/scenarios/README.md`. For GREEN use `claude --plugin-dir plugins/orchestra --plugin-dir plugins/phi-guard -p "<prompt>"` in a temp folder holding the fixtures. Record date, model and observations for each in `BASELINE.md` (add four rows).
Expected: all four GREEN. A scenario that stays RED means the skill text is wrong: fix the skill, re-run, record the final run, and commit the skill fix in the same commit.

- [ ] **Step 3: Commit**

```bash
git add tests/scenarios
git commit -m "test: P1 scenarios for nomenclature, sample size, reverse causation, chapter 1" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 13: Fictional cohort example end to end, and 0.2.0

**Files:**
- Create: `examples/fictional-cohort/` (a full project folder), `examples/fictional-cohort/README.md`
- Modify: `README.md`, `CHANGELOG.md`, all three version fields (`marketplace.json` metadata, both `plugin.json`)

- [ ] **Step 1: Create the example project**

```bash
python plugins/orchestra/scripts/init_project.py examples/fictional-cohort --title "Glycaemic control and 1-year readmission in adults with type 2 diabetes: a retrospective cohort (simulated)" --type thesis-masters --design cohort --output-lang vi --chat-lang vi
```

- [ ] **Step 2: Run the P1 lifecycle with the plugin**

In `examples/fictional-cohort`, with `claude --plugin-dir ../../plugins/orchestra --plugin-dir ../../plugins/phi-guard`, run in order: `/orchestra:start` (resume), `research-question` (approve G1 as "Example author"), `literature-search`, `/orchestra:appraise` on two key studies, `guideline-check`, `/orchestra:review` (mode a), `protocol-design`, `sample-size-sap` (approve G2). Answer every question as a fictional author; never enter real patient data.

Expected files: `01_question/question.md`, `02_evidence/{search-strategy.md, evidence-table.md, evidence-map.md, gaps.md, guidelines.md}`, `02_evidence/appraisal/*.md` (2), `06_writing/thesis/ch1-literature-review.md`, `03_protocol/{protocol.md, variables.md, sample-size.md, sap.md}`, gates G1 and G2 open.

- [ ] **Step 3: Verify the example with scripts**

Run:
```bash
python plugins/orchestra/scripts/crolib/ledgers.py check examples/fictional-cohort
python plugins/orchestra/scripts/verify_refs.py examples/fictional-cohort --cite examples/fictional-cohort/06_writing/thesis/ch1-literature-review.md
python plugins/orchestra/scripts/review_lint.py examples/fictional-cohort/06_writing/thesis/ch1-literature-review.md
python plugins/orchestra/scripts/gate.py check examples/fictional-cohort G2
python plugins/phi-guard/scripts/phi_scan.py --file examples/fictional-cohort/01_question/question.md examples/fictional-cohort/03_protocol/protocol.md
```
Expected: every command exits 0. Recompute the sample size stated in `sample-size.md` with `samplesize.py` and confirm the same n.

- [ ] **Step 4: Write `examples/fictional-cohort/README.md`**

State that all content is simulated for demonstration, list the commands run in Step 2, and the checks in Step 3 with their results.

- [ ] **Step 5: Release 0.2.0**

Set version `0.2.0` in `.claude-plugin/marketplace.json` (`metadata.version`) and both `plugin.json`. Add to `CHANGELOG.md`:

```markdown
## 0.2.0 (YYYY-MM-DD)
- P1 plan the study: research-question, literature-search, critical-appraisal (/orchestra:appraise),
  guideline-check, literature-review (/orchestra:review), protocol-design, sample-size-sap.
- Methods content by Amelia Le, ported to English.
- Scripts: samplesize.py, review_lint.py. Verified reporting-guideline library.
- Example: examples/fictional-cohort (simulated).
```

Update the README "What works" list with the new skills and commands.

- [ ] **Step 6: Full checks, commit, push**

Run: `python -m unittest discover -s tests/unit -v` and `python tools/lint_skills.py`
Expected: all PASS, 0 lint errors.

```bash
git add -A
git commit -m "feat: fictional cohort example and 0.2.0 release" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git push
gh run list --limit 1
```

Expected: CI run green.
