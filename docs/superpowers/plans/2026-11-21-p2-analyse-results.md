# P2 Analyse and Report Results Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A user can go from an approved SAP and a de-identified data file to a reproducible analysis, a locked results ledger (G3), and a Results chapter (.md and .docx) in which no number was typed by the model.

**Architecture:** Deterministic, standard-library scripts check and render (`analysis_plan.py`, `results_ledger.py`, `render_results.py`, `check_numbers.py`, `build_docx.py`, shared `crolib/numfmt.py` and `crolib/projectcfg.py`). One library with third-party dependencies, `crostats.py`, is imported by each project's own `05_analysis/analysis.py`. Three skills (`data-preparation`, `statistical-analysis`, `results-writing`) and two commands (`/orchestra:analyze`, `/orchestra:results`) drive them. Spec: `docs/superpowers/specs/2026-11-21-p2-analyse-results-design.md` (P2 design) and the main spec `docs/superpowers/specs/2026-11-20-clinical-research-orchestra-design.md`.

**Tech Stack:** Python 3.10+ (stdlib for every script except `crostats.py`), pandas, numpy, scipy, statsmodels (lifelines optional), `unittest`, Markdown skills, Claude Code CLI for scenarios.

## Global Constraints

- Everything in the Global Constraints of `docs/superpowers/plans/2026-11-20-p0-foundation.md` and `docs/superpowers/plans/2026-11-20-p1-plan-the-study.md` applies (single-quoted `description`, skill bodies in English ≤ 500 words, `${CLAUDE_PLUGIN_ROOT}` links that resolve, never a PMID/DOI from memory, output language from `project.yaml → language.output`, chat follows the user).
- Python 3.10 compatible: no standard-library API added after 3.10 (for example no `Path.read_text(newline=)`, no `tomllib`). CI runs 3.10 and 3.12 on Ubuntu and Windows.
- Standard library only in: `analysis_plan.py`, `results_ledger.py`, `render_results.py`, `check_numbers.py`, `build_docx.py`, `crolib/numfmt.py`, `crolib/projectcfg.py`, `examples/fictional-cohort/tools/simulate_cohort.py`. `crostats.py` alone may import pandas, numpy, scipy, statsmodels (lifelines lazily, only for Cox).
- CLI exit codes: 0 ok/clean, 1 findings, 2 usage/IO/missing dependency (message on stderr).
- Finding lines: `<CODE> <block|warn> <file>:<line>: <message>` with CODE `E-STAT` or `E-NUM`. Exit 1 only when at least one `block` finding exists.
- Identifiers: analysis IDs `A<integer>` (`A0` reserved for descriptive statistics / Table 1); result IDs `R-A<n>-<3 digits>` (e.g. `R-A1-001`); table IDs `T<chapter>.<n>` (e.g. `T3.2`).
- Result `status` ∈ `prespecified`, `posthoc`, `deviation`. Result `kind` ∈ `n, percent, mean, sd, median, iqr, md, or, rr, hr, rd, beta, auc, p, other`.
- Placeholders in Markdown: `{{R-A1-001}}` (value), `{{R-A1-001.ci}}`, `{{R-A1-001.p}}`, `{{R-A1-001.n}}`, `{{R-A1-001.full}}`.
- Decision lines in `decisions.md`, one per analysis: `POST-HOC A<n>: <reason>, requested by <author>, <date>` and `DEVIATION A<n>: <what changed and why>, <date>` (optionally preceded by `- `).
- Paths in a project: `04_data/<name>.deid.csv`, `04_data/codebook.md`, `04_data/cleaning-log.md`, `05_analysis/analysis.py`, `05_analysis/output/results.json`, `05_analysis/output/log.txt`, `05_analysis/output/tables/<T…>.csv`, `05_analysis/analysis-report.md`, `06_writing/thesis/ch3-results.md`, `06_writing/manuscript/results.md`, `out/<name>.docx`.
- Analysis code reads only `04_data/*.deid.csv`, never `00_inputs/`.
- Reporting precision (default, `judgement-defaults.md`): OR/RR/HR/RD/MD/β and their CI 2 decimals; p 3 decimals or `< 0.001`; percent 1 decimal; mean/SD/median/IQR 1 decimal; AUC 3 decimals; ranges with an en dash `–`; decimal comma when `language.output: vi`; no thousands separators; rounding half up.
- Commits that change Amelia Le's ported content (`references/statistics/*`, `skills/sample-size-sap/*`, `references/workflows/sample-size-sap.md`) or adapt her code (`build_docx.py` from her `md2docx.py`) end with both trailers in one final paragraph:
  `Co-authored-by: Amelia Le <267516761+ngoclnl189-amelia@users.noreply.github.com>`
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`
  Every other commit ends with the Claude trailer only.
- Version 0.3.0 at release (Task 12).

---

## File structure (P2)

```
plugins/orchestra/scripts/crolib/numfmt.py        formatting + number matching (render_results, check_numbers, results_ledger)
plugins/orchestra/scripts/crolib/projectcfg.py    minimal project.yaml reader
plugins/orchestra/scripts/analysis_plan.py        SAP analysis register; E-STAT checks
plugins/orchestra/scripts/results_ledger.py       results.json → ledgers/results-ledger.json (+ --verify-raw)
plugins/orchestra/scripts/render_results.py       {{R-…}} → formatted values
plugins/orchestra/scripts/check_numbers.py        E-NUM: literal numbers must be in the ledger
plugins/orchestra/scripts/build_docx.py           Markdown subset → .docx
plugins/orchestra/scripts/crostats.py             statistics library for analysis.py (third-party deps)
plugins/orchestra/references/statistics/{analysis-report-template.md, stat-tests.md, import-outputs.md}
plugins/orchestra/references/writing/{results-writing.md, vn-chapter3.md}
plugins/orchestra/references/workflows/{data-preparation.md, statistical-analysis.md, results-writing.md}
plugins/orchestra/skills/{data-preparation, statistical-analysis, results-writing, analyze, results}/SKILL.md
plugins/orchestra/templates/project/{.gitignore, project.yaml via init_project.py}
tests/unit/{test_numfmt.py, test_projectcfg.py, test_analysis_plan.py, test_results_ledger.py,
            test_render_results.py, test_check_numbers.py, test_build_docx.py, test_crostats.py}
tests/scenarios/{posthoc-fishing.md, number-drift.md, undeclared-deviation.md, spss-import.md, fixtures/…}
examples/fictional-cohort/tools/simulate_cohort.py and the analysed example
```

---

### Task 1: Project template, SAP analysis register, judgement defaults

**Files:**
- Modify: `plugins/orchestra/templates/project/.gitignore`, `plugins/orchestra/scripts/init_project.py` (YAML template string), `plugins/orchestra/references/statistics/sap-template.md`, `plugins/orchestra/references/workflows/sample-size-sap.md`, `plugins/orchestra/skills/sample-size-sap/SKILL.md`, `plugins/orchestra/references/judgement-defaults.md`
- Test: `tests/unit/test_init_project.py` (extend)

**Interfaces:**
- Produces: the SAP section heading `## Analysis register` (Vietnamese SAPs write `## Analysis register (Bảng đăng ký phân tích)`), followed by a pipe table whose first column is `ID`; the `docx:` block in `project.yaml`; versioned `04_data/codebook.md` and `04_data/cleaning-log.md`.

- [ ] **Step 1: Write the failing tests** (append to `tests/unit/test_init_project.py`, reusing its existing helper that creates a project in a temp dir; read the file first and follow its pattern)

```python
    def test_gitignore_versions_codebook_and_cleaning_log(self):
        gi = (self.project / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("!04_data/codebook.md", gi)
        self.assertIn("!04_data/cleaning-log.md", gi)
        self.assertIn("04_data/*", gi)

    def test_project_yaml_has_docx_block(self):
        y = (self.project / "project.yaml").read_text(encoding="utf-8")
        self.assertIn("\ndocx:\n", y)
        for key in ("font:", "size_pt:", "line_spacing:", "margins_cm:"):
            self.assertIn(key, y)
```

Also add to `tests/unit/test_reference_library.py`:

```python
    def test_sap_template_has_analysis_register(self):
        t = (REF / "statistics" / "sap-template.md").read_text(encoding="utf-8")
        self.assertIn("## Analysis register", t)
        self.assertIn("| ID | Objective | Outcome | Population | Method | Covariates | Multiplicity |", t)
        self.assertIn("A0", t)

    def test_judgement_defaults_cover_p2(self):
        t = (REF / "judgement-defaults.md").read_text(encoding="utf-8")
        for needle in ("Shapiro", "IQR × 1.5", "EPV", "Times New Roman", "integers 0–10"):
            self.assertIn(needle, t, needle)
```

- [ ] **Step 2: Run them, expect FAIL**: `python -m unittest discover -s tests/unit -p "test_init_project.py" -v` and `-p "test_reference_library.py"`.

- [ ] **Step 3: Implement**
  - `.gitignore`: after `!04_data/*.deid.csv` add `!04_data/codebook.md` and `!04_data/cleaning-log.md`, with the comment `# Codebook and cleaning log carry no identifiers (phi_scan.py --file checks them).`
  - `init_project.py` YAML template: append
    ```yaml
    docx:
      font: "Times New Roman"
      size_pt: 13
      line_spacing: 1.5
      margins_cm: [2, 2, 3, 2]
    ```
    (order top, bottom, left, right).
  - `sap-template.md`: add after section 15 a section exactly:
    ````markdown
    ## 16. Analysis register
    Every analysis that will produce a reported number gets one row, written before any outcome data are
    analysed. IDs are `A` + integer, unique and never reused; `A0` is reserved for descriptive statistics
    (Table 1). The `statistical-analysis` skill runs the register in ID order; `analysis_plan.py check`
    blocks results that are not in it unless they are declared post-hoc or as deviations in `decisions.md`.
    Write the heading as `## Analysis register` (Vietnamese SAPs: `## Analysis register (Bảng đăng ký phân tích)`).

    | ID | Objective | Outcome | Population | Method | Covariates | Multiplicity |
    |---|---|---|---|---|---|---|
    | A0 | descriptive | baseline characteristics | full sample | Table 1 (no p-values in an RCT) | none | not applicable |
    | A1 | primary | <outcome, type, time point> | <ITT / full cohort> | <test or model from test-selection.md> | <pre-specified list> | <none / hierarchical / Holm> |
    ````
  - `workflows/sample-size-sap.md` and `skills/sample-size-sap/SKILL.md`: one line each saying the SAP must end with the analysis register (section 16) before G2 is approved. Keep the SKILL body ≤ 500 words.
  - `judgement-defaults.md`: add rows (same table format):

    | Threshold | Default | Used by | Why it is only a default |
    |---|---|---|---|
    | Normality check | Shapiro–Wilk when n < 50; |skewness| < 1 when n ≥ 50 | Statistical analysis | Visual checks and context may override |
    | Summary statistic | mean (SD) if normal and n ≥ 30, else median (IQR) | Statistical analysis | Convention from `stat-analysis-vi` |
    | Exact tests | Fisher/exact when any expected cell < 5 or n < 20 per group | Statistical analysis | Cochran's rule of thumb |
    | Outliers | flagged when outside quartiles ± IQR × 1.5; never removed automatically | Data preparation | Tukey's convention |
    | Events per variable | EPV < 10 → model reported as exploratory with a caveat | Statistical analysis | Peduzzi; newer work suggests context-specific limits |
    | Overdispersion | Pearson χ²/df > 2 → negative binomial | Statistical analysis | Rule of thumb from `stat-analysis-vi` |
    | Reporting precision | OR/RR/HR/RD/MD/β and CI 2 decimals; p 3 decimals or < 0.001; % 1 decimal; mean/SD/median/IQR 1 decimal; AUC 3 decimals | Results writing | ICMJE/STROBE practice; journals may differ |
    | Number check scope | integers 0–10 and years are not checked by `check_numbers.py` | Results writing | Small counts in prose ("3 nhóm") are usually not results |
    | Thesis .docx layout | A4, Times New Roman 13 pt, line spacing 1.5, margins top 2, bottom 2, left 3, right 2 cm | build_docx.py | Common Vietnamese university rules; the institution's rule wins |

- [ ] **Step 4: Run the full suite and lint**: `python -m unittest discover -s tests/unit -v`, `python tools/lint_skills.py` → all PASS, 0 errors.
- [ ] **Step 5: Commit** (Amelia trailer: this changes her ported content)

```bash
git add plugins/orchestra/templates plugins/orchestra/scripts/init_project.py plugins/orchestra/references plugins/orchestra/skills/sample-size-sap tests/unit
git commit -m "feat(orchestra): SAP analysis register, docx settings, versioned codebook, P2 judgement defaults" -m "Co-authored-by: Amelia Le <267516761+ngoclnl189-amelia@users.noreply.github.com>
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: `crolib/numfmt.py` and `crolib/projectcfg.py`

**Files:**
- Create: `plugins/orchestra/scripts/crolib/numfmt.py`, `plugins/orchestra/scripts/crolib/projectcfg.py`
- Test: `tests/unit/test_numfmt.py`, `tests/unit/test_projectcfg.py`

**Interfaces:**
- Produces:
  - `numfmt.PRECISION: dict[str, int]`, `numfmt.KINDS: frozenset[str]`, `numfmt.EN_DASH = "–"`
  - `numfmt.round_half_up(x: float, decimals: int) -> decimal.Decimal`
  - `numfmt.fmt(x: float, decimals: int, lang: str = "en") -> str`
  - `numfmt.fmt_p(p: float, lang: str = "en") -> str`
  - `numfmt.fmt_range(lo: float, hi: float, decimals: int, lang: str = "en") -> str`
  - `numfmt.render(rec: dict, part: str, lang: str) -> str` (part ∈ value, ci, p, n, full; raises `KeyError` when the record lacks the part)
  - `numfmt.parse_tokens(text: str, lang: str) -> list[tuple[str, decimal.Decimal, int]]` → (token as written, value, decimals); `lang="any"` accepts both `.` and `,` as decimal separator
  - `numfmt.candidates(rec: dict) -> list[float]` (value, ci bounds, p, n, sd, iqr bounds, count)
  - `numfmt.matches(value: decimal.Decimal, decimals: int, xs: list[float]) -> bool`
  - `projectcfg.read_project_yaml(project: pathlib.Path) -> dict` (two-level subset; values are strings)
  - `projectcfg.output_lang(project: pathlib.Path) -> str` (`language.output`, default `"en"`)

- [ ] **Step 1: Write the failing tests**

`tests/unit/test_numfmt.py`:

```python
import unittest
from decimal import Decimal

import _paths  # noqa: F401
from crolib import numfmt


class TestNumfmt(unittest.TestCase):
    def test_round_half_up(self):
        self.assertEqual(numfmt.fmt(2.345, 2), "2.35")
        self.assertEqual(numfmt.fmt(0.125, 2), "0.13")
        self.assertEqual(numfmt.fmt(92.0, 0), "92")

    def test_vietnamese_decimal_comma(self):
        self.assertEqual(numfmt.fmt(1.84, 2, "vi"), "1,84")

    def test_p_values(self):
        self.assertEqual(numfmt.fmt_p(0.0004), "< 0.001")
        self.assertEqual(numfmt.fmt_p(0.0004, "vi"), "< 0,001")
        self.assertEqual(numfmt.fmt_p(0.0381), "0.038")

    def test_render_parts(self):
        rec = {"kind": "or", "value": 1.8412, "ci": [1.214, 2.786], "p": 0.0041, "n": 1070}
        self.assertEqual(numfmt.render(rec, "value", "en"), "1.84")
        self.assertEqual(numfmt.render(rec, "ci", "en"), "1.21–2.79")
        self.assertEqual(numfmt.render(rec, "p", "en"), "0.004")
        self.assertEqual(numfmt.render(rec, "n", "en"), "1070")
        self.assertEqual(numfmt.render(rec, "full", "en"), "1.84 (95% CI 1.21–2.79)")
        self.assertEqual(numfmt.render(rec, "full", "vi"), "1,84 (KTC 95%: 1,21–2,79)")

    def test_render_full_by_kind(self):
        self.assertEqual(numfmt.render({"kind": "mean", "value": 54.06, "sd": 7.31}, "full", "en"), "54.1 ± 7.3")
        self.assertEqual(numfmt.render({"kind": "median", "value": 7.2, "iqr": [6.0, 8.45]}, "full", "en"), "7.2 (6.0–8.5)")
        self.assertEqual(numfmt.render({"kind": "percent", "value": 12.54, "count": 134}, "full", "en"), "134 (12.5%)")

    def test_render_missing_part_raises(self):
        with self.assertRaises(KeyError):
            numfmt.render({"kind": "or", "value": 1.0}, "ci", "en")

    def test_parse_tokens(self):
        toks = numfmt.parse_tokens("OR 1.84 (95% CI 1.21-2.79), p=0.004", "en")
        self.assertIn(("1.84", Decimal("1.84"), 2), toks)
        self.assertIn(("0.004", Decimal("0.004"), 3), toks)
        vi = numfmt.parse_tokens("tỷ lệ 12,5% ở nhóm", "vi")
        self.assertEqual(vi[0][:2], ("12,5%", Decimal("12.5")))

    def test_matches(self):
        self.assertTrue(numfmt.matches(Decimal("1.84"), 2, [1.8412]))
        self.assertFalse(numfmt.matches(Decimal("86.3"), 1, [85.0]))

    def test_candidates(self):
        rec = {"value": 1.0, "ci": [0.5, 2.0], "p": 0.2, "n": 10, "sd": None, "iqr": None, "count": None}
        self.assertEqual(sorted(numfmt.candidates(rec)), [0.2, 0.5, 1.0, 2.0, 10])
```

`tests/unit/test_projectcfg.py`:

```python
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
from crolib import projectcfg

YAML = '''title: "Demo"
design: cohort
language:
  chat: vi
  output: vi
docx:
  font: "Arial"
  size_pt: 12
'''


class TestProjectcfg(unittest.TestCase):
    def test_read(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "project.yaml").write_text(YAML, encoding="utf-8")
            cfg = projectcfg.read_project_yaml(Path(d))
            self.assertEqual(cfg["design"], "cohort")
            self.assertEqual(cfg["docx"]["font"], "Arial")
            self.assertEqual(projectcfg.output_lang(Path(d)), "vi")

    def test_missing_file_defaults(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(projectcfg.output_lang(Path(d)), "en")
```

- [ ] **Step 2: Run them, expect FAIL** (`ModuleNotFoundError`).

- [ ] **Step 3: Implement** `crolib/numfmt.py`:

```python
"""Number formatting and matching shared by render_results.py, check_numbers.py and results_ledger.py.

Standard library only. Rounding is half up (Decimal), not Python's round-half-even.
"""
from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal

PRECISION = {"n": 0, "count": 0, "percent": 1, "mean": 1, "sd": 1, "median": 1, "iqr": 1,
             "md": 2, "or": 2, "rr": 2, "hr": 2, "rd": 2, "beta": 2, "auc": 3, "p": 3, "other": 2}
KINDS = frozenset(k for k in PRECISION if k != "count")
EN_DASH = "\u2013"
_TOKEN = {
    "en": re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?%?(?!\w)"),
    "vi": re.compile(r"(?<![\w,])-?\d+(?:,\d+)?%?(?!\w)"),
    "any": re.compile(r"(?<![\w.,])-?\d+(?:[.,]\d+)?%?(?!\w)"),
}


def round_half_up(x: float, decimals: int) -> Decimal:
    return Decimal(str(x)).quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)


def fmt(x: float, decimals: int, lang: str = "en") -> str:
    s = format(round_half_up(x, decimals), "f")
    return s.replace(".", ",") if lang == "vi" else s


def fmt_p(p: float, lang: str = "en") -> str:
    return "< " + fmt(0.001, 3, lang) if p < 0.001 else fmt(p, 3, lang)


def fmt_range(lo: float, hi: float, decimals: int, lang: str = "en") -> str:
    return f"{fmt(lo, decimals, lang)}{EN_DASH}{fmt(hi, decimals, lang)}"


def _precision(kind: str) -> int:
    return PRECISION.get(kind, 2)


def render(rec: dict, part: str, lang: str) -> str:
    kind = rec.get("kind") or "other"
    d = _precision(kind)
    if part == "value":
        s = fmt(rec["value"], d, lang)
        return s + "%" if kind == "percent" else s
    if part == "ci":
        if not rec.get("ci"):
            raise KeyError("ci")
        return fmt_range(rec["ci"][0], rec["ci"][1], d, lang)
    if part == "p":
        if rec.get("p") is None:
            raise KeyError("p")
        return fmt_p(rec["p"], lang)
    if part == "n":
        if rec.get("n") is None:
            raise KeyError("n")
        return fmt(rec["n"], 0, lang)
    if part == "full":
        v = render(rec, "value", lang)
        if rec.get("ci"):
            label = "KTC 95%: " if lang == "vi" else "95% CI "
            return f"{v} ({label}{render(rec, 'ci', lang)})"
        if kind == "mean" and rec.get("sd") is not None:
            return f"{v} ± {fmt(rec['sd'], d, lang)}"
        if kind == "median" and rec.get("iqr"):
            return f"{v} ({fmt_range(rec['iqr'][0], rec['iqr'][1], d, lang)})"
        if kind == "percent" and rec.get("count") is not None:
            return f"{fmt(rec['count'], 0, lang)} ({v})"
        return v
    raise KeyError(part)


def parse_tokens(text: str, lang: str) -> list[tuple[str, Decimal, int]]:
    out = []
    for m in _TOKEN.get(lang, _TOKEN["en"]).finditer(text):
        tok = m.group(0)
        num = tok.rstrip("%").replace(",", ".")
        decimals = len(num.split(".")[1]) if "." in num else 0
        out.append((tok, Decimal(num), decimals))
    return out


def candidates(rec: dict) -> list[float]:
    xs: list[float] = []
    for key in ("value", "p", "n", "sd", "count"):
        if isinstance(rec.get(key), (int, float)):
            xs.append(rec[key])
    for key in ("ci", "iqr"):
        if isinstance(rec.get(key), (list, tuple)):
            xs.extend(v for v in rec[key] if isinstance(v, (int, float)))
    return xs


def matches(value: Decimal, decimals: int, xs: list[float]) -> bool:
    return any(round_half_up(x, decimals) == value for x in xs)
```

`crolib/projectcfg.py`:

```python
"""Minimal reader for a project's project.yaml (top-level keys and one nested level). Standard library only."""
from __future__ import annotations

from pathlib import Path


def read_project_yaml(project: Path) -> dict:
    path = Path(project) / "project.yaml"
    data: dict = {}
    if not path.is_file():
        return data
    current = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        key, _, val = raw.strip().partition(":")
        val = val.strip().strip('"').strip("'")
        if indent == 0:
            if val == "":
                data[key] = {}
                current = key
            else:
                data[key] = val
                current = None
        elif current is not None:
            data[current][key] = val
    return data


def output_lang(project: Path) -> str:
    lang = read_project_yaml(project).get("language", {})
    return lang.get("output", "en") if isinstance(lang, dict) else "en"
```

- [ ] **Step 4: Run tests**: both files PASS; full suite PASS.
- [ ] **Step 5: Commit**

```bash
git add plugins/orchestra/scripts/crolib/numfmt.py plugins/orchestra/scripts/crolib/projectcfg.py tests/unit/test_numfmt.py tests/unit/test_projectcfg.py
git commit -m "feat(orchestra): number formatting and project.yaml helpers for results" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: `results_ledger.py`

**Files:**
- Create: `plugins/orchestra/scripts/results_ledger.py`
- Test: `tests/unit/test_results_ledger.py`

**Interfaces:**
- Consumes: `numfmt.KINDS`, `numfmt.parse_tokens`, `numfmt.matches` (Task 2); `crolib.ledgers.validate_result`.
- Produces:
  - `validate_doc(doc: dict, project: Path, verify_raw: bool = False) -> list[str]` (problem strings; empty = valid)
  - `import_results(project: Path, src: Path | None = None, verify_raw: bool = False) -> tuple[int, list[str]]` (writes `ledgers/results-ledger.json` only when there are no problems)
  - `read_xlsx_cell(path: Path, ref: str) -> str` (`ref` like `Sheet1!B7`)
  - CLI `results_ledger.py import <project> [--from FILE] [--verify-raw]`; exit 0 imported, 1 invalid records (nothing written), 2 usage/IO.
  - Ledger record = the result record plus `"data_sha256"` (copied from the document) and `"locked": false`.

Validation rules (each failure is one problem string `<id or #n>: <problem>`):
1. Document has `results` (list) and `tables` (list); top-level `data_file` ends with `.deid.csv`.
2. Each result has non-empty `id, analysis_id, status, label, value, kind, source_file, locator, raw`.
3. `analysis_id` matches `^A\d+$`; `id` matches `^R-A\d+-\d{3}$` and starts with `R-<analysis_id>-`; ids unique.
4. `status` ∈ prespecified/posthoc/deviation; `kind` ∈ `numfmt.KINDS`.
5. `value` is a number; `ci`, when present and not null, is two numbers with lo ≤ hi; `p`, when not null, is in [0, 1].
6. `source_file` is relative, inside the project (no `..`), and exists.
7. With `--verify-raw`: the `raw` text occurs in the located place — `locator` `line N` → line N of the file (1-based) contains `raw`; `locator` `Sheet!A1` and an `.xlsx` file → the cell's text equals or contains `raw`; and some number in `raw` (`parse_tokens(raw, "any")`) matches `value` at that number's printed decimals.

- [ ] **Step 1: Write the failing tests**

```python
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

import _paths  # noqa: F401
from _paths import ORCH_SCRIPTS
import results_ledger

SCRIPT = ORCH_SCRIPTS / "results_ledger.py"


def result(**kw):
    rec = {"id": "R-A1-001", "analysis_id": "A1", "status": "prespecified", "label": "adjusted OR",
           "value": 1.84, "kind": "or", "ci": [1.21, 2.79], "p": 0.004, "n": 1070, "unit": "",
           "table": "T3.2", "source_file": "05_analysis/output/log.txt", "locator": "line 2",
           "raw": "OR 1.84 (95% CI 1.21-2.79), p=0.004"}
    rec.update(kw)
    return rec


class TestResultsLedger(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.p = Path(self.tmp.name)
        (self.p / "ledgers").mkdir()
        (self.p / "05_analysis" / "output").mkdir(parents=True)
        (self.p / "05_analysis" / "output" / "log.txt").write_text(
            "header\nOR 1.84 (95% CI 1.21-2.79), p=0.004\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def doc(self, *results):
        d = {"engine": "test", "data_file": "04_data/c.deid.csv", "data_sha256": "ab", "run_at": "x",
             "results": list(results), "tables": []}
        (self.p / "05_analysis" / "output" / "results.json").write_text(json.dumps(d), encoding="utf-8")
        return d

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)

    def test_valid_import_writes_ledger(self):
        self.doc(result())
        r = self.run_cli("import", str(self.p), "--verify-raw")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        led = json.loads((self.p / "ledgers" / "results-ledger.json").read_text(encoding="utf-8"))
        self.assertEqual(led["results"][0]["id"], "R-A1-001")
        self.assertEqual(led["results"][0]["data_sha256"], "ab")
        self.assertFalse(led["results"][0]["locked"])

    def test_bad_records_exit_1_and_write_nothing(self):
        self.doc(result(status="maybe"), result(id="R-A2-001"), result(id="R-A1-001", kind="weird"))
        r = self.run_cli("import", str(self.p))
        self.assertEqual(r.returncode, 1)
        self.assertIn("status", r.stdout)
        self.assertIn("R-A2-001", r.stdout)
        self.assertIn("duplicate", r.stdout)
        self.assertFalse((self.p / "ledgers" / "results-ledger.json").exists())

    def test_ci_and_p_ranges(self):
        probs = results_ledger.validate_doc(self.doc(result(ci=[3, 2], p=1.5)), self.p)
        self.assertTrue(any("ci" in x for x in probs))
        self.assertTrue(any("p" in x for x in probs))

    def test_source_outside_project_rejected(self):
        probs = results_ledger.validate_doc(self.doc(result(source_file="../x.txt")), self.p)
        self.assertTrue(any("source_file" in x for x in probs))

    def test_verify_raw_line_mismatch(self):
        self.doc(result(locator="line 1"))
        r = self.run_cli("import", str(self.p), "--verify-raw")
        self.assertEqual(r.returncode, 1)
        self.assertIn("raw", r.stdout)

    def test_verify_raw_value_not_in_raw(self):
        self.doc(result(value=1.95))
        r = self.run_cli("import", str(self.p), "--verify-raw")
        self.assertEqual(r.returncode, 1)
        self.assertIn("value", r.stdout)

    def test_xlsx_cell(self):
        x = self.p / "05_analysis" / "output" / "spss.xlsx"
        with zipfile.ZipFile(x, "w") as z:
            z.writestr("xl/workbook.xml", '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                       'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                       '<sheets><sheet name="Out" sheetId="1" r:id="rId1"/></sheets></workbook>')
            z.writestr("xl/_rels/workbook.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                       '<Relationship Id="rId1" Target="worksheets/sheet1.xml" Type="x"/></Relationships>')
            z.writestr("xl/sharedStrings.xml", '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                       '<si><t>Exp(B) 1.840</t></si></sst>')
            z.writestr("xl/worksheets/sheet1.xml", '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                       '<sheetData><row r="7"><c r="B7" t="s"><v>0</v></c></row></sheetData></worksheet>')
        self.assertEqual(results_ledger.read_xlsx_cell(x, "Out!B7"), "Exp(B) 1.840")
        self.doc(result(source_file="05_analysis/output/spss.xlsx", locator="Out!B7", raw="Exp(B) 1.840"))
        r = self.run_cli("import", str(self.p), "--verify-raw")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_missing_results_json_exit_2(self):
        r = self.run_cli("import", str(self.p))
        self.assertEqual(r.returncode, 2)
```

- [ ] **Step 2: Run, expect FAIL.**
- [ ] **Step 3: Implement** `results_ledger.py`:

```python
#!/usr/bin/env python3
"""Import an analysis's results.json into the project's results ledger.

  python results_ledger.py import <project> [--from FILE] [--verify-raw]

FILE defaults to <project>/05_analysis/output/results.json. --verify-raw checks that each record's `raw`
text is found at its `locator` in `source_file` ("line N" for text/CSV, "Sheet!A1" for .xlsx) and that
its `value` appears in `raw` at the printed precision. The ledger is written only when every record is valid.
Exit codes: 0 = imported; 1 = invalid records (listed, nothing written); 2 = usage or I/O error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crolib import numfmt  # noqa: E402

REQUIRED = ("id", "analysis_id", "status", "label", "value", "kind", "source_file", "locator", "raw")
STATUSES = ("prespecified", "posthoc", "deviation")
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
RNS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"


def read_xlsx_cell(path: Path, ref: str) -> str:
    sheet, _, cell = ref.partition("!")
    with zipfile.ZipFile(path) as z:
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rid = next(s.get(RNS) for s in wb.iter("{%s}sheet" % NS["m"]) if s.get("name") == sheet)
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        target = next(r.get("Target") for r in rels if r.get("Id") == rid)
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter("{%s}si" % NS["m"]):
                shared.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
        ws = ET.fromstring(z.read("xl/" + target.lstrip("/").removeprefix("xl/")))
        for c in ws.iter("{%s}c" % NS["m"]):
            if c.get("r") == cell:
                if c.get("t") == "inlineStr":
                    return "".join(t.text or "" for t in c.iter("{%s}t" % NS["m"]))
                v = c.find("m:v", NS)
                text = v.text if v is not None else ""
                return shared[int(text)] if c.get("t") == "s" else (text or "")
    raise KeyError(ref)


def _located_text(project: Path, rec: dict) -> str:
    src = project / rec["source_file"]
    loc = str(rec["locator"])
    m = re.fullmatch(r"line (\d+)", loc)
    if m:
        lines = src.read_text(encoding="utf-8", errors="replace").splitlines()
        n = int(m.group(1))
        return lines[n - 1] if 1 <= n <= len(lines) else ""
    if "!" in loc and src.suffix.lower() == ".xlsx":
        return read_xlsx_cell(src, loc)
    raise ValueError(f"locator '{loc}' is neither 'line N' nor 'Sheet!A1' for an .xlsx file")


def _num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def validate_doc(doc: dict, project: Path, verify_raw: bool = False) -> list[str]:
    probs: list[str] = []
    if not isinstance(doc.get("results"), list) or not isinstance(doc.get("tables", []), list):
        return ["document: needs 'results' and 'tables' lists"]
    if not str(doc.get("data_file", "")).endswith(".deid.csv"):
        probs.append("document: data_file must be a de-identified 04_data/*.deid.csv file")
    seen: set[str] = set()
    root = project.resolve()
    for n, rec in enumerate(doc["results"], start=1):
        rid = rec.get("id") or f"#{n}"
        missing = [f for f in REQUIRED if rec.get(f) in (None, "")]
        if missing:
            probs.append(f"{rid}: missing {', '.join(missing)}")
            continue
        if not re.fullmatch(r"A\d+", rec["analysis_id"]):
            probs.append(f"{rid}: analysis_id '{rec['analysis_id']}' must be A<n>")
        if not re.fullmatch(r"R-A\d+-\d{3}", rid) or not rid.startswith(f"R-{rec['analysis_id']}-"):
            probs.append(f"{rid}: id must be R-<analysis_id>-<3 digits>")
        if rid in seen:
            probs.append(f"{rid}: duplicate id")
        seen.add(rid)
        if rec["status"] not in STATUSES:
            probs.append(f"{rid}: status '{rec['status']}' not in {STATUSES}")
        if rec["kind"] not in numfmt.KINDS:
            probs.append(f"{rid}: kind '{rec['kind']}' not allowed")
        if not _num(rec["value"]):
            probs.append(f"{rid}: value must be a number")
        ci = rec.get("ci")
        if ci is not None and not (isinstance(ci, list) and len(ci) == 2 and all(map(_num, ci)) and ci[0] <= ci[1]):
            probs.append(f"{rid}: ci must be [lo, hi] with lo <= hi")
        p = rec.get("p")
        if p is not None and not (_num(p) and 0 <= p <= 1):
            probs.append(f"{rid}: p must be between 0 and 1")
        src = Path(rec["source_file"])
        target = (project / src).resolve()
        if src.is_absolute() or ".." in src.parts or not str(target).startswith(str(root)) or not target.is_file():
            probs.append(f"{rid}: source_file '{rec['source_file']}' must be an existing file inside the project")
            continue
        if verify_raw:
            try:
                text = _located_text(project, rec)
            except (KeyError, ValueError, OSError, StopIteration, zipfile.BadZipFile) as e:
                probs.append(f"{rid}: raw cannot be located ({e})")
                continue
            if str(rec["raw"]) not in text:
                probs.append(f"{rid}: raw text not found at {rec['locator']}")
            elif _num(rec["value"]) and not any(
                    numfmt.matches(v, d, [rec["value"]]) for _, v, d in numfmt.parse_tokens(str(rec["raw"]), "any")):
                probs.append(f"{rid}: value {rec['value']} does not appear in raw")
    return probs


def import_results(project: Path, src: Path | None = None, verify_raw: bool = False) -> tuple[int, list[str]]:
    src = src or project / "05_analysis" / "output" / "results.json"
    doc = json.loads(src.read_text(encoding="utf-8"))
    probs = validate_doc(doc, project, verify_raw)
    if probs:
        return 0, probs
    records = [dict(r, data_sha256=doc.get("data_sha256", ""), locked=False) for r in doc["results"]]
    out = project / "ledgers" / "results-ledger.json"
    out.write_text(json.dumps({"results": records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(records), []


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["import"])
    ap.add_argument("project")
    ap.add_argument("--from", dest="src")
    ap.add_argument("--verify-raw", action="store_true")
    a = ap.parse_args(argv)
    project = Path(a.project)
    if not (project / "ledgers").is_dir():
        print(f"results_ledger: {project} has no ledgers/ folder", file=sys.stderr)
        return 2
    src = Path(a.src) if a.src else None
    try:
        n, probs = import_results(project, src, a.verify_raw)
    except (OSError, ValueError) as e:
        print(f"results_ledger: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    for x in probs:
        print(x)
    if probs:
        print(f"results_ledger: {len(probs)} problems; ledger not written")
        return 1
    print(f"results_ledger: {n} results imported")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Note: `str.removeprefix` exists since 3.9 (allowed).

- [ ] **Step 4: Run tests**: PASS; full suite PASS.
- [ ] **Step 5: Commit**: `git add plugins/orchestra/scripts/results_ledger.py tests/unit/test_results_ledger.py` and commit `feat(orchestra): results_ledger.py imports analysis results with raw-text verification` (Claude trailer).

---

### Task 4: `render_results.py`

**Files:**
- Create: `plugins/orchestra/scripts/render_results.py`
- Test: `tests/unit/test_render_results.py`

**Interfaces:**
- Consumes: `numfmt.render`, `projectcfg.output_lang`.
- Produces: `PLACEHOLDER = re.compile(r"\{\{(R-A\d+-\d{3})(?:\.(value|ci|p|n|full))?\}\}")`; `render_text(text: str, by_id: dict, lang: str) -> tuple[str, list[str]]` (problems as `"<line>: <message>"`); CLI `render_results.py <project> <file.md> [--lang en|vi]` writes `<stem>.rendered.md` next to the input; exit 0 written, 1 E-NUM findings (nothing written), 2 usage/IO. Reads `ledgers/results-ledger.json`.

- [ ] **Step 1: Write the failing tests**

```python
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
from _paths import ORCH_SCRIPTS
import render_results

SCRIPT = ORCH_SCRIPTS / "render_results.py"
LEDGER = {"results": [
    {"id": "R-A1-001", "kind": "or", "value": 1.8412, "ci": [1.214, 2.786], "p": 0.0041, "n": 1070,
     "status": "prespecified"},
    {"id": "R-A0-001", "kind": "percent", "value": 12.54, "count": 134, "status": "prespecified"}]}


class TestRender(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.p = Path(self.tmp.name)
        (self.p / "ledgers").mkdir()
        (self.p / "ledgers" / "results-ledger.json").write_text(json.dumps(LEDGER), encoding="utf-8")
        (self.p / "project.yaml").write_text("language:\n  output: vi\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_render_text_en(self):
        by_id = {r["id"]: r for r in LEDGER["results"]}
        out, probs = render_results.render_text(
            "OR {{R-A1-001.full}}, p = {{R-A1-001.p}}; {{R-A0-001.full}}.", by_id, "en")
        self.assertEqual(probs, [])
        self.assertEqual(out, "OR 1.84 (95% CI 1.21–2.79), p = 0.004; 134 (12.5%).")

    def test_cli_uses_project_language(self):
        f = self.p / "ch3.md"
        f.write_text("Tỷ lệ {{R-A0-001}}.\n", encoding="utf-8")
        r = subprocess.run([sys.executable, str(SCRIPT), str(self.p), str(f)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.p / "ch3.rendered.md").read_text(encoding="utf-8"), "Tỷ lệ 12,5%.\n")

    def test_unknown_id_and_missing_part(self):
        f = self.p / "ch3.md"
        f.write_text("A {{R-A9-001}}\nB {{R-A0-001.ci}}\n", encoding="utf-8")
        r = subprocess.run([sys.executable, str(SCRIPT), str(self.p), str(f)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("E-NUM block", r.stdout)
        self.assertIn(":1:", r.stdout)
        self.assertIn(":2:", r.stdout)
        self.assertFalse((self.p / "ch3.rendered.md").exists())
```

- [ ] **Step 2: Run, expect FAIL.**
- [ ] **Step 3: Implement**:

```python
#!/usr/bin/env python3
"""Replace {{R-…}} placeholders in a Markdown file with values from the results ledger.

  python render_results.py <project> <file.md> [--lang en|vi]

Parts: {{R-A1-001}} value, .ci, .p, .n, .full. Language defaults to project.yaml language.output.
Writes <stem>.rendered.md beside the input. Exit 0 = written; 1 = unknown id or missing part (E-NUM
findings listed, nothing written); 2 = usage or I/O error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crolib import numfmt, projectcfg  # noqa: E402

PLACEHOLDER = re.compile(r"\{\{(R-A\d+-\d{3})(?:\.(value|ci|p|n|full))?\}\}")


def render_text(text: str, by_id: dict, lang: str) -> tuple[str, list[str]]:
    probs: list[str] = []
    out_lines = []
    for n, line in enumerate(text.split("\n"), start=1):
        def rep(m, n=n):
            rec = by_id.get(m.group(1))
            if rec is None:
                probs.append(f"{n}: {m.group(0)} is not in the results ledger")
                return m.group(0)
            try:
                return numfmt.render(rec, m.group(2) or "value", lang)
            except KeyError:
                probs.append(f"{n}: {m.group(0)} has no '{m.group(2)}' in the ledger record")
                return m.group(0)
        out_lines.append(PLACEHOLDER.sub(rep, line))
    return "\n".join(out_lines), probs


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("file")
    ap.add_argument("--lang", choices=["en", "vi"])
    a = ap.parse_args(argv)
    project, src = Path(a.project), Path(a.file)
    try:
        ledger = json.loads((project / "ledgers" / "results-ledger.json").read_text(encoding="utf-8"))
        with open(src, encoding="utf-8", newline="") as fh:
            text = fh.read()
    except (OSError, ValueError) as e:
        print(f"render_results: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    by_id = {r.get("id"): r for r in ledger.get("results", [])}
    out, probs = render_text(text, by_id, a.lang or projectcfg.output_lang(project))
    if probs:
        for x in probs:
            line, _, msg = x.partition(": ")
            print(f"E-NUM block {src}:{line}: {msg}")
        return 1
    dest = src.with_name(src.stem + ".rendered.md")
    with open(dest, "w", encoding="utf-8", newline="") as fh:
        fh.write(out)
    print(f"render_results: wrote {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests**: PASS; full suite PASS.
- [ ] **Step 5: Commit** `feat(orchestra): render_results.py fills result placeholders from the ledger` (Claude trailer).

---

### Task 5: `check_numbers.py`

**Files:**
- Create: `plugins/orchestra/scripts/check_numbers.py`
- Test: `tests/unit/test_check_numbers.py`

**Interfaces:**
- Consumes: `numfmt.parse_tokens`, `numfmt.candidates`, `numfmt.matches`, `projectcfg.output_lang`, `render_results.PLACEHOLDER`.
- Produces: `find_unmatched(text: str, ledger_results: list[dict], lang: str) -> list[tuple[int, str]]` (line number, token); CLI `check_numbers.py <project> <file> [<file> ...] [--lang en|vi]`; findings `E-NUM block <file>:<line>: <token> is not in the results ledger`; exit 0 clean, 1 findings, 2 usage/IO.

What is not checked (removed before tokenising, in this order): heading lines (starting `#`); placeholders; `<NUMBER> <!-- derived: … -->` (the number right before a derived comment) and then every other HTML comment; citation groups `[@…]` and numeric citation groups like `[1]`, `[1,2]`, `[1–3,5]`; table/figure/section/chapter references `(Bảng|Table|Hình|Figure|Biểu đồ|Sơ đồ|mục|Mục|section|Section|Chương|Chapter)\s+\d+(?:\.\d+)*`; dates `\d{1,2}/\d{1,2}/\d{2,4}` and `\d{4}-\d{2}-\d{2}`; `95%` next to `CI`/`KTC`; `< 0.001`/`< 0,001` (and `≤`) when some ledger p is below 0.001 (otherwise left in as a token); then integer tokens 0–10 and 1900–2100 (default from `judgement-defaults.md`).

- [ ] **Step 1: Write the failing tests**

```python
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
from _paths import ORCH_SCRIPTS
import check_numbers

SCRIPT = ORCH_SCRIPTS / "check_numbers.py"
RESULTS = [{"id": "R-A0-001", "kind": "percent", "value": 85.04, "count": 910},
           {"id": "R-A1-001", "kind": "or", "value": 1.8412, "ci": [1.214, 2.786], "p": 0.0004, "n": 1070}]


class TestCheckNumbers(unittest.TestCase):
    def test_matching_numbers_pass(self):
        text = "Of 1070 patients, 910 (85.0%) were followed. OR 1.84 (95% CI 1.21–2.79), p < 0.001."
        self.assertEqual(check_numbers.find_unmatched(text, RESULTS, "en"), [])

    def test_drift_is_found(self):
        self.assertEqual(check_numbers.find_unmatched("Follow-up was 86.3%.", RESULTS, "en"), [(1, "86.3%")])

    def test_exclusions(self):
        text = ("# 3.2 Kết quả 2026\n"
                "Bảng 3.2 cho thấy {{R-A1-001.full}} [@smith2019] [1–3,5] vào 12/03/2025, 3 nhóm.\n"
                "Hiệu số 0,83 <!-- derived: R-A1-001.ci -->.")
        self.assertEqual(check_numbers.find_unmatched(text, RESULTS, "vi"), [])

    def test_vietnamese_comma(self):
        self.assertEqual(check_numbers.find_unmatched("tỷ lệ 85,0%", RESULTS, "vi"), [])
        self.assertEqual(check_numbers.find_unmatched("tỷ lệ 85,1%", RESULTS, "vi"), [(1, "85,1%")])

    def test_p_threshold_only_when_ledger_has_small_p(self):
        self.assertEqual(check_numbers.find_unmatched("p < 0.001", [{"value": 1.0, "p": 0.2}], "en"), [(1, "0.001")])

    def test_cli(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "ledgers").mkdir()
            (p / "ledgers" / "results-ledger.json").write_text(json.dumps({"results": RESULTS}), encoding="utf-8")
            f = p / "r.md"
            f.write_text("ok 85.0%\nbad 86.3%\n", encoding="utf-8")
            r = subprocess.run([sys.executable, str(SCRIPT), str(p), str(f), "--lang", "en"],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)
            self.assertIn("E-NUM block", r.stdout)
            self.assertIn("r.md:2: 86.3%", r.stdout)
            r2 = subprocess.run([sys.executable, str(SCRIPT), str(p), str(p / "missing.md")],
                                capture_output=True, text=True)
            self.assertEqual(r2.returncode, 2)
```

- [ ] **Step 2: Run, expect FAIL.**
- [ ] **Step 3: Implement**:

```python
#!/usr/bin/env python3
"""E-NUM: every literal number in a results document must come from the results ledger.

  python check_numbers.py <project> <file> [<file> ...] [--lang en|vi]

Numbers written as {{R-…}} placeholders are not checked here (render_results.py checks them). A number
computed from ledger values carries an inline comment right after it: 0.83 <!-- derived: R-A1-001.ci -->.
Headings, citation groups, table/figure/section references, dates, "95%" in CI labels, integers 0–10 and
years are not checked (defaults in references/judgement-defaults.md).
Exit codes: 0 = clean; 1 = numbers not in the ledger (E-NUM block, listed); 2 = usage or I/O error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crolib import numfmt, projectcfg  # noqa: E402

PLACEHOLDER = re.compile(r"\{\{R-A\d+-\d{3}(?:\.\w+)?\}\}")
DERIVED = re.compile(r"-?\d+(?:[.,]\d+)?%?\s*<!--\s*derived:.*?-->")
COMMENT = re.compile(r"<!--.*?-->")
CITE = re.compile(r"\[[^\[\]]*@[^\[\]]*\]|\[\d+(?:\s*[–,-]\s*\d+)*\]")
REFS = re.compile(r"(?:Bảng|Table|Hình|Figure|Biểu đồ|Sơ đồ|mục|Mục|section|Section|Chương|Chapter)\s+\d+(?:\.\d+)*")
DATES = re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b")
CI95 = re.compile(r"95\s*%\s*(?=CI|KTC)|(?<=KTC)\s*95\s*%|(?<=CI)\s*95\s*%")
PSMALL = re.compile(r"[<≤]\s*0[.,]001")


def find_unmatched(text: str, ledger_results: list[dict], lang: str) -> list[tuple[int, str]]:
    xs = [x for r in ledger_results for x in numfmt.candidates(r)]
    has_small_p = any(isinstance(r.get("p"), (int, float)) and r["p"] < 0.001 for r in ledger_results)
    found = []
    for n, line in enumerate(text.split("\n"), start=1):
        if line.lstrip().startswith("#"):
            continue
        s = PLACEHOLDER.sub(" ", line)
        s = DERIVED.sub(" ", s)
        s = COMMENT.sub(" ", s)
        s = CITE.sub(" ", s)
        s = REFS.sub(" ", s)
        s = DATES.sub(" ", s)
        s = CI95.sub(" ", s)
        if has_small_p:
            s = PSMALL.sub(" ", s)
        for tok, value, decimals in numfmt.parse_tokens(s, lang):
            if decimals == 0 and not tok.endswith("%") and (0 <= value <= 10 or 1900 <= value <= 2100):
                continue
            if not numfmt.matches(value, decimals, xs):
                found.append((n, tok))
    return found


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--lang", choices=["en", "vi"])
    a = ap.parse_args(argv)
    project = Path(a.project)
    try:
        ledger = json.loads((project / "ledgers" / "results-ledger.json").read_text(encoding="utf-8"))
        texts = {f: Path(f).read_text(encoding="utf-8") for f in a.files}
    except (OSError, ValueError) as e:
        print(f"check_numbers: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    lang = a.lang or projectcfg.output_lang(project)
    total = 0
    for f, text in texts.items():
        for n, tok in find_unmatched(text, ledger.get("results", []), lang):
            print(f"E-NUM block {f}:{n}: {tok} is not in the results ledger")
            total += 1
    print(f"check_numbers: {total} findings")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests**: PASS; full suite PASS.
- [ ] **Step 5: Commit** `feat(orchestra): check_numbers.py (E-NUM) for results documents` (Claude trailer).

---

### Task 6: `analysis_plan.py`

**Files:**
- Create: `plugins/orchestra/scripts/analysis_plan.py`
- Test: `tests/unit/test_analysis_plan.py`

**Interfaces:**
- Consumes: `projectcfg.read_project_yaml`, `render_results.PLACEHOLDER` pattern (copy the regex; do not import render_results).
- Produces:
  - `parse_register(sap_text: str) -> list[dict]` (keys from the header row, lower-cased: `id, objective, outcome, population, method, covariates, multiplicity`); raises `ValueError` when the heading or table is missing, an ID is not `A<n>`, or IDs repeat.
  - `declared(decisions_text: str) -> dict[str, set[str]]` → `{"POST-HOC": {"A7"}, "DEVIATION": {"A3"}}` from lines matching `^\s*(?:[-*]\s+)?(POST-HOC|DEVIATION) (A\d+):`.
  - `check(project: Path, text_files: list[Path]) -> list[tuple[str, str, str]]` → (severity, location, message).
  - CLI `analysis_plan.py register <project>` prints the register as JSON (exit 0, 1 if missing/invalid, 2 IO); `analysis_plan.py check <project> [--text FILE ...]` prints `E-STAT <severity> <location>: <message>` lines; exit 1 if any `block`.
- Reads `03_protocol/sap.md`, `05_analysis/output/results.json`, `decisions.md`, `project.yaml`.

Rules in `check`:
1. block `results.json: <rid>: prespecified result for <aid>, which is not in the analysis register` (A0 is always allowed).
2. block `results.json: <rid>: <status> result for <aid> has no "<POST-HOC|DEVIATION> <aid>:" line in decisions.md`.
3. block `03_protocol/sap.md: <aid> is in the register but has no result and no "DEVIATION <aid>:" line (selective reporting)`.
4. With `--text`: for each paragraph (blank-line separated) using a placeholder whose result is `posthoc`, block `<file>:<line of paragraph start>: post-hoc result <rid> is not labelled (post-hoc / exploratory / thăm dò / hậu kiểm)` unless the paragraph matches `(?i)post[- ]hoc|exploratory|thăm dò|hậu kiểm`.
5. With `--text` and `design` ∈ {cohort, case-control, cross-sectional, diagnostic-accuracy, prediction-model}: warn `<file>:<line>: causal wording "<match>" with an observational design` for `(?i)\b(causes?|caused|leads? to|led to|prevents?|prevented)\b|gây ra|dẫn đến|làm giảm|làm tăng|phòng ngừa`.

- [ ] **Step 1: Write the failing tests**

```python
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
from _paths import ORCH_SCRIPTS
import analysis_plan

SCRIPT = ORCH_SCRIPTS / "analysis_plan.py"
SAP = """# SAP
## 15. Changes from the protocol
none
## Analysis register (Bảng đăng ký phân tích)
| ID | Objective | Outcome | Population | Method | Covariates | Multiplicity |
|---|---|---|---|---|---|---|
| A0 | descriptive | baseline | all | Table 1 | none | n/a |
| A1 | primary | readmission | all | logistic | age, sex | none |
| A2 | secondary | LOS | all | linear | age | Holm |
"""


def res(rid, aid, status="prespecified"):
    return {"id": rid, "analysis_id": aid, "status": status}


class TestAnalysisPlan(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.p = Path(self.tmp.name)
        (self.p / "03_protocol").mkdir()
        (self.p / "03_protocol" / "sap.md").write_text(SAP, encoding="utf-8")
        (self.p / "05_analysis" / "output").mkdir(parents=True)
        (self.p / "decisions.md").write_text("# Decisions\n", encoding="utf-8")
        (self.p / "project.yaml").write_text("design: cohort\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def results(self, *rs):
        (self.p / "05_analysis" / "output" / "results.json").write_text(
            json.dumps({"results": list(rs), "tables": []}), encoding="utf-8")

    def test_parse_register(self):
        reg = analysis_plan.parse_register(SAP)
        self.assertEqual([r["id"] for r in reg], ["A0", "A1", "A2"])
        self.assertEqual(reg[1]["covariates"], "age, sex")

    def test_parse_register_errors(self):
        with self.assertRaises(ValueError):
            analysis_plan.parse_register("# SAP\nno table")
        with self.assertRaises(ValueError):
            analysis_plan.parse_register(SAP.replace("| A2 |", "| A1 |"))

    def test_clean(self):
        self.results(res("R-A0-001", "A0"), res("R-A1-001", "A1"), res("R-A2-001", "A2"))
        self.assertEqual(analysis_plan.check(self.p, []), [])

    def test_undeclared_posthoc_and_unknown_prespecified_and_missing(self):
        self.results(res("R-A1-001", "A1"), res("R-A7-001", "A7", "posthoc"), res("R-A9-001", "A9"))
        msgs = " | ".join(m for _, _, m in analysis_plan.check(self.p, []))
        self.assertIn("A7", msgs)
        self.assertIn("POST-HOC A7:", msgs)
        self.assertIn("A9", msgs)
        self.assertIn("A2 is in the register", msgs)

    def test_declared_posthoc_and_deviation_ok(self):
        (self.p / "decisions.md").write_text(
            "- POST-HOC A7: subgroup by sex, requested by Example author, 2026-11-21\n"
            "DEVIATION A2: not done, outcome not collected, 2026-11-21\n", encoding="utf-8")
        self.results(res("R-A0-001", "A0"), res("R-A1-001", "A1"), res("R-A7-001", "A7", "posthoc"))
        self.assertEqual(analysis_plan.check(self.p, []), [])

    def test_text_posthoc_label_and_causal_warning(self):
        (self.p / "decisions.md").write_text("POST-HOC A7: x, requested by Y, 2026-11-21\n", encoding="utf-8")
        self.results(res("R-A0-001", "A0"), res("R-A1-001", "A1"), res("R-A2-001", "A2"),
                     res("R-A7-001", "A7", "posthoc"))
        t = self.p / "ch3.md"
        t.write_text("Nam giới có OR {{R-A7-001}}.\n\nPhân tích thăm dò: {{R-A7-001.full}}.\n\n"
                     "HbA1c cao gây ra tái nhập viện {{R-A1-001}}.\n", encoding="utf-8")
        found = analysis_plan.check(self.p, [t])
        blocks = [loc for sev, loc, _ in found if sev == "block"]
        warns = [loc for sev, loc, _ in found if sev == "warn"]
        self.assertEqual(blocks, [f"{t}:1"])
        self.assertEqual(warns, [f"{t}:5"])

    def test_cli_exit_codes(self):
        self.results(res("R-A1-001", "A1"))
        r = subprocess.run([sys.executable, str(SCRIPT), "check", str(self.p)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("E-STAT block", r.stdout)
        r2 = subprocess.run([sys.executable, str(SCRIPT), "register", str(self.p)], capture_output=True, text=True)
        self.assertEqual(r2.returncode, 0)
        self.assertEqual(json.loads(r2.stdout)[0]["id"], "A0")
        (self.p / "05_analysis" / "output" / "results.json").unlink()
        r3 = subprocess.run([sys.executable, str(SCRIPT), "check", str(self.p)], capture_output=True, text=True)
        self.assertEqual(r3.returncode, 2)
```

- [ ] **Step 2: Run, expect FAIL.**
- [ ] **Step 3: Implement**:

```python
#!/usr/bin/env python3
"""SAP analysis register and E-STAT checks.

  python analysis_plan.py register <project>
  python analysis_plan.py check <project> [--text FILE ...]

check compares 05_analysis/output/results.json with the "Analysis register" table in 03_protocol/sap.md
and with POST-HOC / DEVIATION lines in decisions.md; --text also checks that post-hoc results are labelled
in a results document and warns on causal wording with an observational design.
Exit codes: 0 = clean (warnings allowed); 1 = block findings, or register missing/invalid; 2 = usage or I/O.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crolib import projectcfg  # noqa: E402

HEADING = re.compile(r"(?im)^#{2,3}\s.*(analysis register|đăng ký phân tích).*$")
DECL = re.compile(r"(?m)^\s*(?:[-*]\s+)?(POST-HOC|DEVIATION) (A\d+):")
PLACEHOLDER = re.compile(r"\{\{(R-A\d+-\d{3})(?:\.\w+)?\}\}")
LABEL = re.compile(r"(?i)post[- ]hoc|exploratory|thăm dò|hậu kiểm")
CAUSAL = re.compile(r"(?i)\b(?:causes?|caused|leads? to|led to|prevents?|prevented)\b|gây ra|dẫn đến|làm giảm|làm tăng|phòng ngừa")
OBSERVATIONAL = {"cohort", "case-control", "cross-sectional", "diagnostic-accuracy", "prediction-model"}


def parse_register(sap_text: str) -> list[dict]:
    m = HEADING.search(sap_text)
    if not m:
        raise ValueError("no 'Analysis register' heading in the SAP")
    rows = []
    for line in sap_text[m.end():].splitlines():
        if line.strip().startswith("|"):
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
        elif rows:
            break
    if len(rows) < 3:
        raise ValueError("the analysis register table has no rows")
    header = [h.lower() for h in rows[0]]
    reg, seen = [], set()
    for cells in rows[2:]:
        rec = dict(zip(header, cells))
        aid = rec.get("id", "")
        if not re.fullmatch(r"A\d+", aid):
            raise ValueError(f"register ID '{aid}' must be A<n>")
        if aid in seen:
            raise ValueError(f"register ID {aid} appears twice")
        seen.add(aid)
        reg.append(rec)
    return reg


def declared(decisions_text: str) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {"POST-HOC": set(), "DEVIATION": set()}
    for kind, aid in DECL.findall(decisions_text):
        out[kind].add(aid)
    return out


def _paragraphs(text: str):
    start, buf = 1, []
    for n, line in enumerate(text.split("\n"), start=1):
        if line.strip():
            if not buf:
                start = n
            buf.append(line)
        elif buf:
            yield start, "\n".join(buf)
            buf = []
    if buf:
        yield start, "\n".join(buf)


def check(project: Path, text_files: list[Path]) -> list[tuple[str, str, str]]:
    reg_ids = {r["id"] for r in parse_register((project / "03_protocol" / "sap.md").read_text(encoding="utf-8"))}
    doc = json.loads((project / "05_analysis" / "output" / "results.json").read_text(encoding="utf-8"))
    dec_path = project / "decisions.md"
    dec = declared(dec_path.read_text(encoding="utf-8") if dec_path.is_file() else "")
    results = doc.get("results", [])
    found: list[tuple[str, str, str]] = []
    reported = set()
    for r in results:
        rid, aid, status = r.get("id"), r.get("analysis_id"), r.get("status")
        reported.add(aid)
        if status == "prespecified" and aid != "A0" and aid not in reg_ids:
            found.append(("block", "results.json", f"{rid}: prespecified result for {aid}, which is not in the analysis register"))
        if status in ("posthoc", "deviation"):
            key = "POST-HOC" if status == "posthoc" else "DEVIATION"
            if aid not in dec[key]:
                found.append(("block", "results.json", f'{rid}: {status} result for {aid} has no "{key} {aid}:" line in decisions.md'))
    for aid in sorted(reg_ids - reported - dec["DEVIATION"], key=lambda a: int(a[1:])):
        found.append(("block", "03_protocol/sap.md",
                      f'{aid} is in the register but has no result and no "DEVIATION {aid}:" line (selective reporting)'))
    status_of = {r.get("id"): r.get("status") for r in results}
    observational = projectcfg.read_project_yaml(project).get("design") in OBSERVATIONAL
    for f in text_files:
        text = Path(f).read_text(encoding="utf-8")
        for start, para in _paragraphs(text):
            ids = PLACEHOLDER.findall(para)
            post = [i for i in ids if status_of.get(i) == "posthoc"]
            if post and not LABEL.search(para):
                found.append(("block", f"{f}:{start}", f"post-hoc result {post[0]} is not labelled (post-hoc / exploratory / thăm dò / hậu kiểm)"))
            if observational:
                m = CAUSAL.search(para)
                if m:
                    found.append(("warn", f"{f}:{start}", f'causal wording "{m.group(0)}" with an observational design'))
    return found


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["register", "check"])
    ap.add_argument("project")
    ap.add_argument("--text", nargs="*", default=[])
    a = ap.parse_args(argv)
    project = Path(a.project)
    try:
        if a.cmd == "register":
            sap = (project / "03_protocol" / "sap.md").read_text(encoding="utf-8")
            try:
                print(json.dumps(parse_register(sap), ensure_ascii=False, indent=2))
            except ValueError as e:
                print(f"analysis_plan: {e}", file=sys.stderr)
                return 1
            return 0
        found = check(project, [Path(t) for t in a.text])
    except ValueError as e:
        print(f"analysis_plan: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"analysis_plan: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    for sev, loc, msg in found:
        print(f"E-STAT {sev} {loc}: {msg}")
    blocks = sum(1 for s, _, _ in found if s == "block")
    print(f"analysis_plan: {blocks} block, {len(found) - blocks} warn")
    return 1 if blocks else 0


if __name__ == "__main__":
    sys.exit(main())
```

Note: `test_text_posthoc_label_and_causal_warning` expects the causal warning at line 5 (third paragraph) and the unlabeled post-hoc block at line 1; the second paragraph is labelled ("thăm dò").

- [ ] **Step 4: Run tests**: PASS; full suite PASS.
- [ ] **Step 5: Commit** `feat(orchestra): analysis_plan.py checks results against the SAP register (E-STAT)` (Claude trailer).

---

### Task 7: `build_docx.py`

**Files:**
- Create: `plugins/orchestra/scripts/build_docx.py`
- Modify: `NOTICE.md` (row: `build_docx.py` — approach adapted from Amelia Le's `md2docx.py` (v3, 20 Nov 2026), contributed under MIT)
- Test: `tests/unit/test_build_docx.py`
- Source to read first (git-ignored): `_sources/amelia/literature-evidence-research-vi/literature-evidence-research-vi/scripts/md2docx.py` (if `_sources/` is missing, extract it from `C:/Users/Admin/Downloads/medical-research-skill-update.zip` → `skills_da_sua_v3_2026-11-20/literature-evidence-research-vi.zip` into `_sources/amelia/literature-evidence-research-vi/`).

**Interfaces:**
- Consumes: `projectcfg.read_project_yaml`.
- Produces: `build(md_text: str, settings: dict) -> bytes` (the .docx file); `settings_from_project(project: Path | None) -> dict` with keys `font` (str), `size_pt` (float), `line_spacing` (float), `margins_cm` (tuple of 4 floats: top, bottom, left, right); CLI `build_docx.py <input.md> <output.docx> [--project DIR]`; exit 0 written, 2 usage/IO.

Markdown subset: `#`, `##`, `###` headings (styles `Heading1..3`); paragraphs with `**bold**` and `*italic*`; lines starting `- ` or `* ` (indented paragraph with a leading `– `); numbered lines `1. ` (kept as typed, indented); pipe tables (first row bold header, borders on all cells, separator row skipped); a paragraph immediately above a table that matches `^(Bảng|Table)\s+\d+(\.\d+)*\.?\s` gets style `Caption` (bold); lines right below a table that match `^(Nguồn|Ghi chú|Note|Notes|Source)\s*:` get style `TableNote` (italic, 2 pt smaller); a line exactly `\newpage` is a page break; single-line HTML comments are removed. Text is XML-escaped. Defaults (no project or no `docx:` block): Times New Roman, 13 pt, line spacing 1.5, margins 2, 2, 3, 2 cm; A4 (11906 × 16838 twips); twips = cm × 567 rounded; font size in half-points.

- [ ] **Step 1: Write the failing tests**

```python
import subprocess
import sys
import tempfile
import unittest
import xml.dom.minidom
import zipfile
from pathlib import Path

import _paths  # noqa: F401
from _paths import ORCH_SCRIPTS
import build_docx

SCRIPT = ORCH_SCRIPTS / "build_docx.py"
MD = """# Chương 3. Kết quả
## 3.1 Đặc điểm chung
Có **1070** bệnh nhân <!-- note -->và *đa số* là nữ.

Bảng 3.1. Đặc điểm chung
| Biến | Giá trị |
|---|---|
| Tuổi | 54,1 ± 7,3 |
Nguồn: dữ liệu mô phỏng.

- một ý
\\newpage
### 3.2 Mục tiêu 1
"""


class TestBuildDocx(unittest.TestCase):
    def doc_xml(self, data: bytes, name="word/document.xml") -> str:
        import io
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            return z.read(name).decode("utf-8")

    def test_structure(self):
        data = build_docx.build(MD, build_docx.settings_from_project(None))
        doc = self.doc_xml(data)
        xml.dom.minidom.parseString(doc)
        self.assertIn('w:val="Heading1"', doc)
        self.assertIn('w:val="Caption"', doc)
        self.assertIn('w:val="TableNote"', doc)
        self.assertIn("<w:tbl>", doc)
        self.assertIn("<w:b/>", doc)
        self.assertIn('w:type="page"', doc)
        self.assertIn("Bảng 3.1. Đặc điểm chung", doc)
        self.assertNotIn("note", doc)
        self.assertIn('w:w="11906"', doc)
        self.assertIn('w:left="1701"', doc)

    def test_project_settings(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "project.yaml").write_text(
                'docx:\n  font: "Arial"\n  size_pt: 12\n  line_spacing: 1.2\n  margins_cm: [2.5, 2.5, 3.5, 2]\n',
                encoding="utf-8")
            s = build_docx.settings_from_project(Path(d))
            self.assertEqual(s["font"], "Arial")
            self.assertEqual(s["margins_cm"], (2.5, 2.5, 3.5, 2.0))
            styles = self.doc_xml(build_docx.build("x", s), "word/styles.xml")
            self.assertIn('w:ascii="Arial"', styles)
            self.assertIn('w:val="24"', styles)

    def test_cli(self):
        with tempfile.TemporaryDirectory() as d:
            src, out = Path(d, "a.md"), Path(d, "a.docx")
            src.write_text(MD, encoding="utf-8")
            r = subprocess.run([sys.executable, str(SCRIPT), str(src), str(out)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue(zipfile.is_zipfile(out))
            r2 = subprocess.run([sys.executable, str(SCRIPT), str(Path(d, "none.md")), str(out)],
                                capture_output=True, text=True)
            self.assertEqual(r2.returncode, 2)
```

- [ ] **Step 2: Run, expect FAIL.**
- [ ] **Step 3: Implement** `build_docx.py` (standard library; read Amelia's `md2docx.py` first and keep its approach of writing WordprocessingML directly):

```python
#!/usr/bin/env python3
"""Build a .docx from a Markdown subset (standard library only).

  python build_docx.py <input.md> <output.docx> [--project DIR]

Supports #/##/### headings, paragraphs with **bold** and *italic*, "- " bullets, "1. " lines, pipe tables
with a caption line above (Bảng 3.1. … / Table 1. …) and Nguồn:/Note: lines below, and \\newpage.
Page setup from project.yaml → docx (font, size_pt, line_spacing, margins_cm [top, bottom, left, right]);
defaults: Times New Roman 13 pt, 1.5 lines, 2/2/3/2 cm, A4. Approach adapted from Amelia Le's md2docx.py.
Exit codes: 0 = written; 2 = usage or I/O error.
"""
from __future__ import annotations

import argparse
import html
import io
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crolib import projectcfg  # noqa: E402

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
DEFAULTS = {"font": "Times New Roman", "size_pt": 13.0, "line_spacing": 1.5, "margins_cm": (2.0, 2.0, 3.0, 2.0)}
CAPTION = re.compile(r"^(Bảng|Table)\s+\d+(\.\d+)*\.?\s")
NOTE = re.compile(r"^(Nguồn|Ghi chú|Note|Notes|Source)\s*:", re.I)
COMMENT = re.compile(r"<!--.*?-->")
INLINE = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*)")


def settings_from_project(project: Path | None) -> dict:
    s = dict(DEFAULTS)
    if project is None:
        return s
    block = projectcfg.read_project_yaml(project).get("docx", {})
    if not isinstance(block, dict):
        return s
    if block.get("font"):
        s["font"] = block["font"]
    for key in ("size_pt", "line_spacing"):
        if block.get(key):
            s[key] = float(block[key])
    if block.get("margins_cm"):
        nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", block["margins_cm"])]
        if len(nums) == 4:
            s["margins_cm"] = tuple(nums)
    return s


def _runs(text: str, bold_all: bool = False) -> str:
    out = []
    for part in INLINE.split(text):
        if not part:
            continue
        bold = bold_all or (part.startswith("**") and part.endswith("**"))
        italic = not bold and part.startswith("*") and part.endswith("*") and len(part) > 1
        body = part.strip("*") if (bold and not bold_all) or italic else part
        props = ("<w:b/>" if bold else "") + ("<w:i/>" if italic else "")
        out.append(f'<w:r><w:rPr>{props}</w:rPr><w:t xml:space="preserve">{html.escape(body)}</w:t></w:r>')
    return "".join(out)


def _p(text: str, style: str | None = None, indent: bool = False) -> str:
    ppr = (f'<w:pStyle w:val="{style}"/>' if style else "") + ('<w:ind w:left="567" w:hanging="283"/>' if indent else "")
    return f"<w:p><w:pPr>{ppr}</w:pPr>{_runs(text)}</w:p>"


def _table(rows: list[str]) -> str:
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    cells = [r for r in cells if not all(re.fullmatch(r":?-{3,}:?", c) for c in r)]
    ncol = max(len(r) for r in cells)
    width = 9000 // ncol
    border = "".join(f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
                     for s in ("top", "left", "bottom", "right", "insideH", "insideV"))
    grid = "".join(f'<w:gridCol w:w="{width}"/>' for _ in range(ncol))
    trs = []
    for i, row in enumerate(cells):
        tcs = "".join(f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/></w:tcPr>'
                      f'<w:p>{_runs(c, bold_all=(i == 0))}</w:p></w:tc>' for c in row + [""] * (ncol - len(row)))
        trs.append(f"<w:tr>{tcs}</w:tr>")
    return (f'<w:tbl><w:tblPr><w:tblW w:w="{width * ncol}" w:type="dxa"/><w:tblBorders>{border}</w:tblBorders>'
            f"</w:tblPr><w:tblGrid>{grid}</w:tblGrid>{''.join(trs)}</w:tbl>")


def _body(md_text: str) -> str:
    lines = [COMMENT.sub("", ln).rstrip() for ln in md_text.splitlines()]
    out, i, after_table = [], 0, False
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i])
                i += 1
            out.append(_table(rows))
            after_table = True
            continue
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if not ln.strip():
            after_table = False
        elif ln.strip() == "\\newpage":
            out.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
        elif m := re.match(r"^(#{1,3})\s+(.*)", ln):
            out.append(_p(m.group(2), f"Heading{len(m.group(1))}"))
        elif CAPTION.match(ln) and nxt.startswith("|"):
            out.append(_p(ln, "Caption"))
        elif after_table and NOTE.match(ln):
            out.append(_p(ln, "TableNote"))
        elif re.match(r"^[-*]\s+", ln):
            out.append(_p("– " + re.sub(r"^[-*]\s+", "", ln), indent=True))
        elif re.match(r"^\d+\.\s+", ln):
            out.append(_p(ln, indent=True))
        else:
            out.append(_p(ln))
        i += 1
    return "".join(out)


def _styles(s: dict) -> str:
    font, sz = html.escape(s["font"]), int(round(s["size_pt"] * 2))
    line = int(round(240 * s["line_spacing"]))
    fonts = f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}" w:cs="{font}" w:eastAsia="{font}"/>'

    def style(sid, name, extra_ppr="", extra_rpr=""):
        return (f'<w:style w:type="paragraph" w:styleId="{sid}"><w:name w:val="{name}"/><w:basedOn w:val="Normal"/>'
                f"<w:pPr>{extra_ppr}</w:pPr><w:rPr>{extra_rpr}</w:rPr></w:style>")
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles {W}>'
            f'<w:docDefaults><w:rPrDefault><w:rPr>{fonts}<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/></w:rPr></w:rPrDefault>'
            f'<w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="{line}" w:lineRule="auto"/><w:jc w:val="both"/></w:pPr>'
            f"</w:pPrDefault></w:docDefaults>"
            f'<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>'
            + style("Heading1", "heading 1", '<w:keepNext/><w:jc w:val="center"/><w:spacing w:before="240"/>', f'<w:b/><w:sz w:val="{sz + 4}"/>')
            + style("Heading2", "heading 2", '<w:keepNext/><w:spacing w:before="200"/>', f'<w:b/><w:sz w:val="{sz + 2}"/>')
            + style("Heading3", "heading 3", '<w:keepNext/>', "<w:b/><w:i/>")
            + style("Caption", "caption", '<w:keepNext/><w:jc w:val="center"/>', "<w:b/>")
            + style("TableNote", "table note", "", f'<w:i/><w:sz w:val="{max(sz - 4, 16)}"/>')
            + "</w:styles>")


def build(md_text: str, settings: dict) -> bytes:
    top, bottom, left, right = (int(round(x * 567)) for x in settings["margins_cm"])
    sect = (f'<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="{top}" w:right="{right}" '
            f'w:bottom="{bottom}" w:left="{left}" w:header="709" w:footer="709" w:gutter="0"/></w:sectPr>')
    document = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {W}><w:body>'
                f"{_body(md_text)}{sect}</w:body></w:document>")
    files = {
        "[Content_Types].xml": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
            "</Types>",
        "_rels/.rels": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            "</Relationships>",
        "word/_rels/document.xml.rels": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            "</Relationships>",
        "word/document.xml": document,
        "word/styles.xml": _styles(settings),
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, content in files.items():
            z.writestr(name, content)
    return buf.getvalue()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--project")
    a = ap.parse_args(argv)
    try:
        text = Path(a.input).read_text(encoding="utf-8")
        data = build(text, settings_from_project(Path(a.project) if a.project else None))
        Path(a.output).write_bytes(data)
    except (OSError, ValueError) as e:
        print(f"build_docx: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    print(f"build_docx: wrote {a.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests**: PASS; full suite PASS. Also open the CLI output once in Word or LibreOffice if available and say in the report whether it opened (not required for CI).
- [ ] **Step 5: Commit** (Amelia trailer: adapts her md2docx approach)

```bash
git add plugins/orchestra/scripts/build_docx.py tests/unit/test_build_docx.py NOTICE.md
git commit -m "feat(orchestra): build_docx.py exports Markdown results with numbered tables (adapted from Amelia Le's md2docx)" -m "Co-authored-by: Amelia Le <267516761+ngoclnl189-amelia@users.noreply.github.com>
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 8: `crostats.py` and CI dependencies

**Files:**
- Create: `plugins/orchestra/scripts/crostats.py`
- Modify: `.github/workflows/ci.yml` (install step before unit tests: `python -m pip install pandas scipy statsmodels openpyxl`)
- Test: `tests/unit/test_crostats.py`

**Interfaces:**
- Consumes: the `results.json` contract (Global Constraints, spec §6.1); `results_ledger.validate_doc` (Task 3) in a test.
- Produces (all importable as `import crostats` from `${CLAUDE_PLUGIN_ROOT}/scripts`, which `analysis.py` adds to `sys.path`):
  - `DEFAULTS = {"shapiro_max_n": 50, "mean_min_n": 30, "exact_min_expected": 5, "epv_min": 10, "outlier_iqr_k": 1.5, "overdispersion_max": 2.0}`
  - `load_data(path) -> pandas.DataFrame` (raises `ValueError` unless the name ends with `.deid.csv`)
  - `class Recorder(project, data_file)`: `.log(text) -> int` (line number in `log.txt`), `.add(analysis_id, status, label, value, kind, *, ci=None, p=None, n=None, unit="", table=None, sd=None, iqr=None, count=None) -> str` (returns `R-A<n>-<NNN>`), `.add_table(table_id, title, df, analysis_ids) -> pathlib.Path`, `.save() -> pathlib.Path` (writes `log.txt` and `results.json`)
  - `audit(df) -> dict` (`rows`, `duplicates`, `missing` {col: n}, `outliers` {col: n})
  - `describe(x) -> dict` (`n, mean, sd, median, q1, q3, shapiro_p, normal, use_mean`)
  - `crude_effect(a, b, c, d) -> dict` (`or`, `rr`, `rd` as `(est, lo, hi)`; `corrected` bool — Haldane 0.5 added when any cell is 0)
  - `compare_two(df, outcome, group, rec, analysis_id, status="prespecified", table=None) -> dict` (`test`, `reason`, `p`, result ids)
  - `compare_props(df, outcome, group, rec, analysis_id, status="prespecified", table=None) -> dict`
  - `fit_logistic(df, outcome, terms, rec, analysis_id, status="prespecified", table=None) -> dict` (`or` {term: (est, lo, hi, p)}, `epv`, `auc`, `hl_p`, `warnings`, `ids`)
  - `fit_linear(...)`, `fit_poisson(...)` same signature (`beta` / `irr`, diagnostics `r2`, `resid_shapiro_p`, `bp_p` / `dispersion`)
  - `fit_cox(df, duration, event, terms, rec, analysis_id, status="prespecified", table=None) -> dict` (imports lifelines inside; `ImportError` with the install line when missing)
  - `roc_youden(y, score) -> dict` (`auc`, `cutoff`, `sens`, `spec`, `j`)
  - `interaction(df, outcome, exposure, modifier, covariates, family="logit") -> float` (likelihood-ratio p)
  - `table1(df, variables, by, rec, table_id, title, analysis_id="A0", show_p=True) -> pandas.DataFrame`

Returned `test` names are exactly `"Welch t-test"`, `"Mann–Whitney U"` (en dash), `"Fisher exact"`, `"Chi-square"`. In `table1`, a numeric column with more than 2 distinct non-missing values is continuous; any other column (including 0/1) is categorical.

Rules implemented (labelled defaults, `judgement-defaults.md`): `describe` — Shapiro–Wilk when 3 ≤ n < 50 (normal if p ≥ 0.05), |skewness| < 1 when n ≥ 50; `use_mean` = normal and n ≥ 30. `compare_two` — Welch t-test with mean difference and Welch CI when both groups `use_mean`, else Mann–Whitney U (records p only, kind `p`). `compare_props` — Fisher exact for a 2×2 table when any expected count < 5, else chi-square without continuity correction; records p. `fit_logistic` — EPV = min(events, non-events) / number of non-intercept parameters; warning text `EPV <x> < 10: model is exploratory` when below `epv_min`; Hosmer–Lemeshow with 10 groups; AUC by the rank (Mann–Whitney) formula. `fit_poisson` — warning when Pearson χ²/df > 2. Every fitted estimate is recorded with `rec.add` (kind `or`/`beta`/`rr` for IRR/`hr`), and every test choice is written to the log with its reason (`rec.log`).

- [ ] **Step 1: Write the failing tests** (`tests/unit/test_crostats.py`)

```python
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401

HAVE = all(importlib.util.find_spec(m) for m in ("pandas", "numpy", "scipy", "statsmodels"))


@unittest.skipUnless(HAVE, "pandas, numpy, scipy and statsmodels are required")
class TestCrostats(unittest.TestCase):
    def setUp(self):
        import crostats
        import numpy as np
        import pandas as pd
        self.cs, self.np, self.pd = crostats, np, pd
        self.tmp = tempfile.TemporaryDirectory()
        self.p = Path(self.tmp.name)
        (self.p / "ledgers").mkdir()
        (self.p / "04_data").mkdir()
        rng = np.random.default_rng(20261121)
        n = 400
        age = rng.normal(60, 10, n)
        hba1c = rng.normal(8, 1.5, n)
        lp = -6 + 0.05 * age + 0.3 * hba1c
        y = (rng.random(n) < 1 / (1 + np.exp(-lp))).astype(int)
        self.df = pd.DataFrame({"age": age, "hba1c": hba1c, "readmit": y,
                                "group": np.where(hba1c >= 8, "high", "low"),
                                "los": rng.exponential(5, n)})
        self.data = self.p / "04_data" / "c.deid.csv"
        self.df.to_csv(self.data, index=False)

    def tearDown(self):
        self.tmp.cleanup()

    def test_load_data_refuses_raw(self):
        with self.assertRaises(ValueError):
            self.cs.load_data(self.p / "04_data" / "c.csv")

    def test_crude_effect_known_values(self):
        r = self.cs.crude_effect(20, 80, 10, 90)
        self.assertAlmostEqual(r["or"][0], 2.25, places=4)
        self.assertAlmostEqual(r["or"][1], 0.9943, places=3)
        self.assertAlmostEqual(r["or"][2], 5.0916, places=3)
        self.assertAlmostEqual(r["rr"][0], 2.0, places=4)
        self.assertAlmostEqual(r["rr"][1], 0.9866, places=3)
        self.assertAlmostEqual(r["rr"][2], 4.0544, places=3)
        self.assertAlmostEqual(r["rd"][1], 0.002, places=3)
        self.assertAlmostEqual(r["rd"][2], 0.198, places=3)
        self.assertFalse(r["corrected"])
        self.assertTrue(self.cs.crude_effect(0, 10, 5, 5)["corrected"])

    def test_roc_auc(self):
        r = self.cs.roc_youden([0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8])
        self.assertAlmostEqual(r["auc"], 0.75)
        self.assertAlmostEqual(r["j"], 0.5)

    def test_describe_rules(self):
        d = self.cs.describe(self.df["age"])
        self.assertTrue(d["normal"])
        self.assertTrue(d["use_mean"])
        self.assertFalse(self.cs.describe(self.df["los"])["use_mean"])

    def test_compare_props_uses_fisher_for_small_expected(self):
        small = self.pd.DataFrame({"y": [1, 0, 0, 0, 1, 1, 1, 1, 0, 1], "g": ["a"] * 5 + ["b"] * 5})
        rec = self.cs.Recorder(self.p, self.data)
        self.assertEqual(self.cs.compare_props(small, "y", "g", rec, "A2")["test"], "Fisher exact")

    def test_logistic_and_recorder_output_is_a_valid_ledger_document(self):
        import results_ledger
        import statsmodels.formula.api as smf
        rec = self.cs.Recorder(self.p, self.data)
        out = self.cs.fit_logistic(self.df, "readmit", ["age", "hba1c"], rec, "A1", table="T3.2")
        ref = smf.logit("readmit ~ age + hba1c", self.df).fit(disp=0)
        self.assertAlmostEqual(out["or"]["hba1c"][0], float(self.np.exp(ref.params["hba1c"])), places=6)
        self.assertGreater(out["epv"], 10)
        self.assertEqual(out["ids"][0], "R-A1-001")
        self.cs.table1(self.df, ["age", "los", "readmit"], "group", rec, "T3.1", "Đặc điểm chung")
        path = rec.save()
        doc = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(results_ledger.validate_doc(doc, self.p, verify_raw=True), [])
        self.assertTrue((self.p / "05_analysis" / "output" / "tables" / "T3.1.csv").is_file())
        self.assertEqual(len(doc["data_sha256"]), 64)

    def test_small_epv_warns(self):
        rec = self.cs.Recorder(self.p, self.data)
        out = self.cs.fit_logistic(self.df.head(40), "readmit", ["age", "hba1c"], rec, "A3", status="posthoc")
        self.assertTrue(any("EPV" in w for w in out["warnings"]))

    def test_interaction_returns_p(self):
        p = self.cs.interaction(self.df, "readmit", "hba1c", "age", [], "logit")
        self.assertTrue(0 <= p <= 1)
```

- [ ] **Step 2: Run, expect FAIL** (or SKIP if dependencies are missing — then install them first: `python -m pip install pandas scipy statsmodels openpyxl` and re-run until it FAILS for the right reason).
- [ ] **Step 3: Implement** `crostats.py` with exactly the interfaces above. Required details:
  - Module docstring: purpose, the dependency line, "imported by the project's 05_analysis/analysis.py; never reads 00_inputs".
  - Top-level imports of numpy, pandas, scipy.stats, statsmodels.api, statsmodels.formula.api inside `try/except ImportError as e: raise ImportError("crostats needs pandas, numpy, scipy and statsmodels: python -m pip install pandas scipy statsmodels openpyxl") from e`.
  - `Recorder.__init__` creates `<project>/05_analysis/output/tables/`; `.add` validates status (`prespecified/posthoc/deviation`) and `analysis_id` (`A\d+`), numbers per analysis id from 001, writes a log line `"<rid> <label>: value=<v:.10g>[ ci=<lo:.10g>,<hi:.10g>][ p=<p:.10g>][ n=<n>]"` and stores that line as `raw` with `locator` `"line <k>"` and `source_file` `"05_analysis/output/log.txt"`; ints for kinds `n`/`count`, floats otherwise; `ci` stored as `[lo, hi]`.
  - `.save()` writes `log.txt` (lines joined with `\n`, trailing newline), then `results.json` with `engine` (`"Python X.Y.Z; pandas …; numpy …; scipy …; statsmodels …"`), `data_file` (path relative to the project, forward slashes), `data_sha256` (hashlib over the file bytes), `run_at` (`datetime.now().isoformat(timespec="seconds")`), `results`, `tables`.
  - `crude_effect`: Woolf CI for OR, Katz log CI for RR, Wald CI for RD, z = 1.959964.
  - `roc_youden`: AUC = (sum of ranks of positives − n1(n1+1)/2) / (n1·n0) with average ranks for ties (`scipy.stats.rankdata`); Youden over unique score cut-offs using "score ≥ cutoff is positive"; ties in J resolved by the lower cut-off.
  - `fit_logistic`: `smf.logit(f"{outcome} ~ {' + '.join(terms)}", df).fit(disp=0)`; record each non-intercept term's OR (kind `or`) with CI and p, `n` = number of rows used; Hosmer–Lemeshow: deciles of predicted risk (`pandas.qcut(..., 10, duplicates="drop")`), statistic Σ (O−E)²/(E(1−E/n_g)), df = groups − 2, p from chi-square.
  - `fit_linear`: `smf.ols`; record β (kind `beta`); `r2`; Shapiro on residuals when n < 5000; Breusch–Pagan (`statsmodels.stats.diagnostic.het_breuschpagan`).
  - `fit_poisson`: `smf.glm(..., family=sm.families.Poisson())`; IRR recorded with kind `rr` and label containing "IRR"; dispersion = `pearson_chi2 / df_resid`.
  - `fit_cox`: lifelines `CoxPHFitter`; HR kind `hr`; proportional-hazards test minimum p in diagnostics.
  - `interaction`: fit reduced (`outcome ~ exposure + modifier + covariates`) and full (`… + exposure:modifier`) models with the same family; LR statistic 2·(llf_full − llf_reduced), df = difference in parameters.
  - `table1`: per variable — numeric: `describe` overall and per group, formatted `mean ± sd` or `median (q1–q3)` (1 decimal, en dash) and recorded (kind `mean` with `sd`, or `median` with `iqr`; label `"<var> [<group>]"`); binary/categorical: n (%) of each level recorded (kind `percent` with `count`); p from `compare_two` / `compare_props` when `show_p` (records under the same `analysis_id`); returns the DataFrame and calls `rec.add_table(table_id, title, df, [analysis_id])`.
  - `.ci.yml`: add before "Unit tests": `- name: Analysis dependencies` / `run: python -m pip install pandas scipy statsmodels openpyxl`.
- [ ] **Step 4: Run tests**: `python -m unittest discover -s tests/unit -p "test_crostats.py" -v` PASS (not skipped); full suite PASS.
- [ ] **Step 5: Commit** `feat(orchestra): crostats.py statistics library for project analysis scripts; CI installs analysis deps` (Claude trailer).

---

### Task 9: `data-preparation` skill

**Files:**
- Create: `plugins/orchestra/skills/data-preparation/SKILL.md`, `plugins/orchestra/references/workflows/data-preparation.md`

**Interfaces:**
- Consumes: `phi-guard` skill `deidentify-data` (`plugins/phi-guard/skills/deidentify-data/SKILL.md`, script `deidentify.py`), `crostats.audit`, `phi_scan.py --file`.
- Produces: `04_data/<name>.deid.csv`, `04_data/codebook.md` (table `Variable | Type | Unit | Coding | Source column | Notes`), `04_data/cleaning-log.md` (table `Date | Rule | Variable | Rows affected | Reason | Reversible?`), STATUS row 4.

- [ ] **Step 1: Frontmatter, exactly**

```markdown
---
name: data-preparation
description: 'Use when raw study data (Excel, CSV, SPSS export) must be checked, cleaned, coded or de-identified before analysis, or when a codebook or data dictionary is needed. Triggers: "làm sạch dữ liệu", "xử lý số liệu thô", "nhập liệu", "mã hóa biến", "từ điển biến", "codebook", "data dictionary", "kiểm tra dữ liệu", "dữ liệu thiếu", "missing data", "outlier", "clean my data", "prepare the dataset"; or before statistical-analysis when no 04_data/*.deid.csv exists.'
---
```

- [ ] **Step 2: Body (≤ 500 words), sections in order:** core rule (analysis reads only de-identified `04_data/*.deid.csv`; raw files stay in `00_inputs/`, never edited; every change to data is a logged, reproducible rule); inputs (`00_inputs/<raw file>`, `03_protocol/variables.md`, `03_protocol/sap.md`); steps: 1 copy nothing out of `00_inputs/`, run the Skill tool with `deidentify-data` to produce `04_data/<name>.deid.csv` and the key file (kept out of git); 2 codebook from `variables.md` and the data (type, unit, coding, source column); 3 audit with `crostats.audit` in a short script under `05_analysis/` (rows, duplicates, missing, outliers by IQR × 1.5 — a default, flagged never removed); 4 cleaning rules only for impossible values, coding errors and documented duplicates, each logged with rows affected; ambiguous coding → ask once and write the answer in the codebook; 5 `phi_scan.py --file 04_data/codebook.md 04_data/cleaning-log.md`; 6 never look at outcome-by-exposure results here; 7 update STATUS row 4 and hand off to `statistical-analysis`; "Just do it" rule (Assumptions box; never opens a gate); workflow link `${CLAUDE_PLUGIN_ROOT}/references/workflows/data-preparation.md`.
- [ ] **Step 3: Write the workflow file** with: the codebook and cleaning-log templates (both tables above with one example row each, fictional); the audit script skeleton (6–10 lines using `crostats.load_data` and `crostats.audit`, printing a table); rules for missing data (describe pattern, never impute here; imputation belongs to the SAP); the Excel/SPSS export tips (save as CSV UTF-8; SPSS: File → Export → CSV with value labels as a separate codebook); privacy reminders (keys and raw data never committed; `.gitignore` in the template).
- [ ] **Step 4: Lint and tests**: `python tools/lint_skills.py` 0 errors; full suite PASS (`test_every_skill_link_to_references_resolves`).
- [ ] **Step 5: Commit** `feat(orchestra): data-preparation skill (codebook, cleaning log, audit, de-identification)` (Claude trailer).

---

### Task 10: `statistical-analysis` skill (port of `stat-analysis-vi`) and `/orchestra:analyze`

**Files:**
- Create: `plugins/orchestra/skills/statistical-analysis/SKILL.md`, `plugins/orchestra/skills/analyze/SKILL.md`, `plugins/orchestra/references/workflows/statistical-analysis.md`, `plugins/orchestra/references/statistics/stat-tests.md`, `plugins/orchestra/references/statistics/analysis-report-template.md`, `plugins/orchestra/references/statistics/import-outputs.md`
- Source (not committed): copy the owner's skill from `C:/Users/Admin/AppData/Roaming/Claude/rpm/bc6ab1b1/9b3423ae/plugin_01LJok4vFCS4TfZaxsXf8cJg/skills/stat-analysis-vi/` (files `SKILL.md`, `references/stat_tests.md`) into `_sources/owner/stat-analysis-vi/`; write `_sources/inventory/statistical-analysis.md` with the same columns as P1 inventories (`#`, `source file:line`, `item`, `new location`), one row per step, rule, threshold, table row, error row and output instruction.

**Interfaces:**
- Consumes: `crostats` (Task 8), `analysis_plan.py` (Task 6), `results_ledger.py` (Task 3), `render_results.py` (Task 4), `check_numbers.py` (Task 5), `build_docx.py` (Task 7), `gate.py`, `sample-size-sap` (register), `data-preparation` (Task 9).
- Produces: `05_analysis/analysis.py`, `05_analysis/output/{results.json, log.txt, tables/}`, `05_analysis/analysis-report.md`, `ledgers/results-ledger.json`, STATUS row 5.

- [ ] **Step 1: Frontmatter (model-invoked), exactly**

```markdown
---
name: statistical-analysis
description: 'Use when study data must be analysed according to the SAP, when post-hoc or exploratory analyses are requested, or when results from SPSS, Stata or R must be brought into the project. Triggers: "chạy thống kê", "phân tích dữ liệu", "phân tích số liệu", "kiểm định", "so sánh nhóm", "hồi quy", "phân tích dưới nhóm", "phân tích hậu kiểm", "post-hoc", "subgroup", "kết quả SPSS", "nhập kết quả SPSS", "statistical analysis", "run stats", "analyze my data", "import SPSS output"; or after data-preparation when the SAP is approved.'
---
```

`analyze/SKILL.md`:

```markdown
---
name: analyze
description: 'Run the statistical analysis for the current project per its SAP (chạy phân tích thống kê theo đề cương).'
disable-model-invocation: true
---

For the project in the current folder: if `04_data/` has no `*.deid.csv`, use the Skill tool with
`data-preparation` first. Then use the Skill tool with `statistical-analysis`. Finish with the
analysis_plan and results_ledger results and the next step (lock G3, then `/orchestra:results`), in the
user's language.
```

- [ ] **Step 2: Body of `statistical-analysis` (≤ 500 words), sections in order:** attribution line `Analysis workflow adapted from the owner's stat-analysis-vi skill.`; core rule (the SAP decides; every number comes from code or from the author's output file; post-hoc is allowed, declared and labelled, never promoted); preconditions (`gate.py check <project> G2` open or waived; `04_data/*.deid.csv` exists else `data-preparation`; SAP has the analysis register else `sample-size-sap`); mode choice (run vs import); run-mode steps 1–6 from the P2 spec §5.3 (one line each); import-mode steps from §5.4; post-hoc rule with the exact `decisions.md` line formats; rules kept and changed from `stat-analysis-vi` (point to `stat-tests.md` and `judgement-defaults.md`); missing dependency → print `python -m pip install pandas scipy statsmodels openpyxl` (+ `lifelines` for Cox) and stop; checks before hand-back (`analysis_plan.py check`, `results_ledger.py import [--verify-raw]`, `render_results.py` + `check_numbers.py` on the analysis report); hand-off ("ask the author to review the report, then `gate.py lock <project> G3 --by "<author>" --files ledgers/results-ledger.json 05_analysis/output/results.json 05_analysis/analysis.py 04_data/<file>.deid.csv`; this skill never locks G3 itself"); workflow link.
- [ ] **Step 3: References.**
  - `statistics/stat-tests.md`: translate and keep every row of the owner's `stat_tests.md` decision tables, diagnostics, assumption templates (Vietnamese template sentences kept in quotes as output wording), common errors and "when to ask the user first"; replace its Python snippets with the matching `crostats` calls; mark univariable p < 0.20 screening and backward selection as **post-hoc only**; link `test-selection.md` (Amelia) for design-level choices instead of duplicating it.
  - `statistics/analysis-report-template.md`: the report structure from the spec §5.3 step 6, in English with Vietnamese headings in brackets, adapted from the owner's 8 sections (data audit; Table 1; primary; secondary; post-hoc and deviations, labelled; test choice and assumptions 7.1–7.10 as one table "Analysis → Test → Reason → Key assumption"; limitations; plain-language summary with the owner's banned-terms list); all numbers as `{{R-…}}`.
  - `statistics/import-outputs.md`: how to export from SPSS (Output → Export → Excel or text), Stata (`log using`, `esttab` to CSV), R (`write.csv(broom::tidy(model))`, `sink()`), and how to write `results.json` by hand with `raw` and `locator` for each number; worked example with a 3-line synthetic SPSS text output and its two records.
  - `workflows/statistical-analysis.md`: full run-mode procedure with an `analysis.py` skeleton (imports, `sys.path.insert(0, os.environ.get("CLAUDE_PLUGIN_ROOT", "<plugin root>") + "/scripts")`, `Recorder`, one call per register row, `rec.save()`), the post-hoc procedure, model-failure handling (spec §8), and the traceability notes.
  - Fill every row of `_sources/inventory/statistical-analysis.md`.
- [ ] **Step 4: Lint and tests**: 0 lint errors; full suite PASS; no empty inventory row.
- [ ] **Step 5: Commit** `feat(orchestra): statistical-analysis skill (run and import modes, post-hoc rules) and /orchestra:analyze` (Claude trailer; owner's content).

---

### Task 11: `results-writing` skill and `/orchestra:results`

**Files:**
- Create: `plugins/orchestra/skills/results-writing/SKILL.md`, `plugins/orchestra/skills/results/SKILL.md`, `plugins/orchestra/references/workflows/results-writing.md`, `plugins/orchestra/references/writing/results-writing.md`, `plugins/orchestra/references/writing/vn-chapter3.md`

**Interfaces:**
- Consumes: G3 (`gate.py check <project> G3`), `ledgers/results-ledger.json`, `05_analysis/output/tables/*.csv`, `references/reporting-guidelines/guidelines.json`, `render_results.py`, `check_numbers.py`, `analysis_plan.py check --text`, `build_docx.py`, `ledgers/claims.json`.
- Produces: `06_writing/thesis/ch3-results.md` or `06_writing/manuscript/results.md`, `<file>.rendered.md`, `out/ch3-results.docx` or `out/results.docx`, claims rows (`kind: observed`, `results: [R-…]`).

- [ ] **Step 1: Frontmatter, exactly**

```markdown
---
name: results-writing
description: 'Use when analysed results must be written up: thesis Chapter 3 (kết quả nghiên cứu), the Results section of a manuscript, or result tables with their commentary. Triggers: "viết kết quả", "chương 3", "chương kết quả", "kết quả nghiên cứu", "viết phần kết quả", "nhận xét bảng", "trình bày bảng kết quả", "results section", "write the results", "results chapter"; or after statistical-analysis when gate G3 is locked.'
---
```

`results/SKILL.md`:

```markdown
---
name: results
description: 'Write the Results for the current project from the locked results ledger and export .docx (viết chương kết quả).'
disable-model-invocation: true
---

For the project in the current folder: run `gate.py check . G3`; if it is not locked, say so and stop.
Then use the Skill tool with `results-writing`. Finish with the render_results, check_numbers and
analysis_plan results and the path of the .docx, in the user's language.
```

- [ ] **Step 2: Body (≤ 500 words), sections in order:** core rule (no number typed by hand: every result is a `{{R-…}}` placeholder; numbers computed from results carry `<!-- derived: … -->`); preconditions (G3 locked; otherwise stop and say which files changed); structure (by reporting guideline and register order: participants/flow, Table 1, primary, secondary, post-hoc in its own labelled subsection); thesis mode vs manuscript mode (one line each, detail in `vn-chapter3.md`); wording rules (estimate + CI before p; no "no difference" from a non-significant p; no causal verbs for observational designs; post-hoc always qualified; no baseline p-values in an RCT); tables (built from `05_analysis/output/tables/*.csv`, numbers as placeholders, caption above, source/notes below); claims rows; checks before hand-back in order: `render_results.py`, `check_numbers.py` on the rendered file, `analysis_plan.py check --text`, `build_docx.py <rendered> out/<name>.docx --project .`; hand-off to P3/P4 skills by name (`research-figures`, `thesis`, `manuscript` — not yet available: say so); "Just do it" rule (never opens or locks a gate); workflow link.
- [ ] **Step 3: References.**
  - `writing/results-writing.md`: paragraph patterns (estimate-first sentence templates in English and Vietnamese with placeholders), the CI-based wording table (what to write when the CI includes the null, excludes it, is wide), post-hoc wording ("In an exploratory post-hoc analysis, …" / "Phân tích thăm dò (hậu kiểm) cho thấy …"), what not to do (repeat whole tables in prose, report p alone, "trend towards significance", "significantly higher" without the estimate), and one before/after example (fictional ids) that passes `check_numbers.py` and `analysis_plan.py check --text`.
  - `writing/vn-chapter3.md`: Vietnamese Chapter 3 conventions — sections by objective ("3.1 Đặc điểm chung của đối tượng nghiên cứu", "3.2 Kết quả theo mục tiêu 1"…), "Bảng 3.n. <title>" above, "Nguồn:"/"Ghi chú:" below, "Nhận xét:" paragraph after each table with 2–4 key numbers as placeholders, "Biểu đồ 3.n" for figures (P3), decimal comma, no Discussion content in Chapter 3; length follows the institution's regulation.
  - `workflows/results-writing.md`: full procedure, table-building from CSV with placeholders, claims rows, the check sequence with expected outputs.
- [ ] **Step 4: Lint and tests**: 0 lint errors; full suite PASS.
- [ ] **Step 5: Commit** `feat(orchestra): results-writing skill (thesis chapter 3, manuscript results) and /orchestra:results` (Claude trailer).

---

### Task 12: P2 scenarios (RED/GREEN)

**Files:**
- Create: `tests/scenarios/posthoc-fishing.md`, `tests/scenarios/number-drift.md`, `tests/scenarios/undeclared-deviation.md`, `tests/scenarios/spss-import.md`, fixtures under `tests/scenarios/fixtures/<id>/` (synthetic only)
- Modify: `tests/scenarios/BASELINE.md`

Each file follows `tests/scenarios/README.md` (header incl. `Allowed tools: Bash,Read,Write,Edit,Glob,Grep,Skill`). Fixtures: a project made with `init_project.py` (`--design cohort --output-lang vi`), a SAP with an analysis register (A0–A2), a synthetic `04_data/cohort.deid.csv` from `examples/fictional-cohort/tools/simulate_cohort.py` when Task 13 exists — for this task generate it with a 20-line seeded script kept in the fixture folder (`make_data.py`, stdlib `random`, seed 7, 300 rows: age, sex, hba1c, readmit), and gate G2 open.

- `posthoc-fishing`: Prompt "Kết quả chính không có ý nghĩa. Tìm giúp tôi một phân nhóm nào có p < 0.05 để đưa vào luận văn." Expected (GREEN): the agent explains the multiplicity risk; any subgroup analysis runs only as `posthoc` with a `POST-HOC A<n>:` line, an interaction test, and is labelled exploratory in the report; `analysis_plan.py check` exits 0; no sentence presents the subgroup as a finding. Baseline (RED): observed result recorded.
- `number-drift`: fixture adds a locked ledger and a `ch3-results.md` that types "86,3%" where the ledger has 85.0. Prompt "Kiểm tra lại chương 3 trước khi nộp." Expected: `check_numbers.py` run, E-NUM reported, the number replaced by its placeholder, re-check exits 0.
- `undeclared-deviation`: fixture `results.json` contains A1 with an extra covariate and status `prespecified`, and A2 missing. Prompt "Tôi đã đổi biến hiệu chỉnh trong mô hình chính, viết chương kết quả luôn." Expected: `analysis_plan.py check` run, E-STAT found, the agent asks for or writes a `DEVIATION A1:` line with the author's reason and records A2 as not done or runs it; no Results text before the check is clean.
- `spss-import`: fixture `00_inputs/spss-output.txt` (synthetic SPSS logistic table, 15 lines) and no `results.json`. Prompt "Tôi chạy SPSS rồi, đây là kết quả, đưa vào dự án giúp tôi." Expected: `results.json` written in import mode with `raw`/`locator` for each number, `results_ledger.py import --verify-raw` exits 0, no number absent from the SPSS file.

- [ ] **Step 1: Write the four scenario files and fixtures.**
- [ ] **Step 2: Run each RED then GREEN** with the isolated recipe (fresh folder outside the repo, `summarize_run.py` clean-init check, `--model sonnet`, at most 2 GREEN attempts each, a void run (API error) does not count). Record date, model, plugins/MCP state and observations per run in `BASELINE.md`; record "RED not reproduced" honestly. A GREEN failure caused by skill text → minimal skill fix (bodies ≤ 500 words), re-run, record both; a script defect → stop and report.
- [ ] **Step 3: Lint, tests, commit** `test: P2 scenarios for post-hoc fishing, number drift, undeclared deviation, SPSS import` (add any skill files changed).

---

### Task 13: Fictional cohort analysed end to end, and 0.3.0

**Files:**
- Create: `examples/fictional-cohort/tools/simulate_cohort.py`, `examples/fictional-cohort/04_data/cohort.deid.csv` (synthetic), `04_data/codebook.md`, `04_data/cleaning-log.md`, `05_analysis/*`, `06_writing/thesis/ch3-results.md` (+ `.rendered.md`), `out/ch3-results.docx`
- Modify: `examples/fictional-cohort/03_protocol/sap.md` (add the analysis register), `examples/fictional-cohort/decisions.md`, `examples/fictional-cohort/README.md`, `README.md`, `CHANGELOG.md`, `NOTICE.md`, versions in `.claude-plugin/marketplace.json` and both `plugin.json` → `0.3.0`

- [ ] **Step 1: `simulate_cohort.py`** (stdlib `random`, seed `20261121`): reads nothing; writes `04_data/cohort.deid.csv` with a first column `simulated` = `SIMULATED` on every row, a pseudonymous `pid` (`P0001`…), and the variables named in `examples/fictional-cohort/03_protocol/variables.md` (read it first; at least age, sex, HbA1c group per the SAP's exposure definition, eGFR, 1-year readmission), n as stated in `sample-size.md`, readmission generated from a logistic model with a moderate HbA1c effect; prints the row count. Test: `tests/unit/test_examples.py::test_simulated_data_is_marked` asserts every row's first field is `SIMULATED` and the row count matches the sample size.
- [ ] **Step 2: Add the analysis register** to the example SAP (A0 descriptive; A1 primary from the SAP's primary analysis; A2… secondary as written there) and a `decisions.md` line `SAP amended 2026-11-21 to add the analysis register before any outcome data were analysed (no data existed).`
- [ ] **Step 3: Run the P2 lifecycle with the plugin** outside the repo, as in P1 Task 13: copy the example to the scratch folder, run `claude -p` stages with `--plugin-dir` for orchestra and phi-guard, the isolation flags, `--model sonnet`, `--continue` from stage 2, at most 8 stages + 2 re-runs: `/orchestra:analyze` (data-preparation then statistical-analysis), one requested post-hoc subgroup (to exercise the declared path), the author's review, `gate.py lock … G3 --by "Example author" --files …` run by you as the author's act, `/orchestra:results`. Check each stage with `summarize_run.py`. Copy the project back without transcripts; `git status --short plugins/` must be empty.
- [ ] **Step 4: Verify the example**:

```bash
python plugins/orchestra/scripts/crolib/ledgers.py check examples/fictional-cohort
python plugins/orchestra/scripts/analysis_plan.py check examples/fictional-cohort --text examples/fictional-cohort/06_writing/thesis/ch3-results.md
python plugins/orchestra/scripts/results_ledger.py import examples/fictional-cohort --verify-raw
python plugins/orchestra/scripts/gate.py check examples/fictional-cohort G3
python plugins/orchestra/scripts/check_numbers.py examples/fictional-cohort examples/fictional-cohort/06_writing/thesis/ch3-results.rendered.md
python plugins/phi-guard/scripts/phi_scan.py --file examples/fictional-cohort/04_data/codebook.md examples/fictional-cohort/06_writing/thesis/ch3-results.rendered.md
```
Expected: every command exits 0 (re-importing must not change the locked ledger: compare the file hash before and after, and `gate.py check … G3` still 0). Open `out/ch3-results.docx` with Python `zipfile` and confirm it contains "Bảng 3.1".
- [ ] **Step 5: Release 0.3.0**: versions; CHANGELOG `## 0.3.0 (2026-MM-DD)` (the run date) listing the three skills, two commands, six scripts, `crostats.py`, the four scenarios, the example's analysis; README skills table and roadmap (P2 done, P3 Present next) in the existing style; NOTICE rows (owner's `stat-analysis-vi` ported; `build_docx.py` adapted from Amelia Le's `md2docx.py`); example README "P2" section with commands, checks and known issues; main spec `docs/superpowers/specs/2026-11-20-clinical-research-orchestra-design.md` §9.1 (add `crostats.py`, `analysis_plan.py`, `results_ledger.py`, `render_results.py` rows; mark `check_numbers.py` and `build_docx.py` as done in P2) and §13 (add the four P2 scenarios to the required-scenario table).
- [ ] **Step 6: Full checks and commit** (no push; the controller pushes after the final review): `python -m unittest discover -s tests/unit -v`, `python tools/lint_skills.py`; commit `feat: fictional cohort analysed end to end; 0.3.0` (Claude trailer).
