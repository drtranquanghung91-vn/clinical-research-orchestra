"""Statistics library for a project's own analysis script (crostats = clinical-research-orchestra stats).

Dependencies: pandas, numpy, scipy, statsmodels (python -m pip install pandas scipy statsmodels openpyxl);
lifelines only for fit_cox, imported lazily (python -m pip install lifelines).

Imported by the project's 05_analysis/analysis.py; never reads 00_inputs. Self-contained: a project
vendors this one file into 05_analysis/ (no import of crolib or any other plugin module).
Data come only from 04_data/*.deid.csv (load_data refuses anything else). Every test choice is written to
05_analysis/output/log.txt with its reason (Recorder.log) and every estimate is recorded with
Recorder.add, which writes one log line per result; that line is the record's `raw` text and its
`locator` is "line <k>", so results_ledger.py --verify-raw can find it.

Every compare_* and fit_* function takes a keyword-only `label` prefix: when given (e.g. a subgroup,
label="nữ"), each label it records starts with "<label>: "; without it the labels are unchanged.

Labelled defaults (judgement-defaults.md) are in DEFAULTS. Choices the brief leaves open, and the
standard option taken:
  - quartiles: pandas linear interpolation (R type 7); SPSS uses type 6, so Q1/Q3 can differ slightly;
  - skewness (n >= 50): adjusted Fisher-Pearson G1 (scipy.stats.skew(bias=False), as SPSS/Excel);
  - Mann-Whitney U: scipy default method "auto" (exact for small samples without ties, else normal
    approximation with continuity correction), two-sided;
  - mean difference in compare_two: first minus second group of `order`, default numeric-aware ascending
    (0 before 1, 9 before 10), stated in the label as "<first> − <second>";
  - exact tests: Fisher exact for a 2x2 table when an expected count < 5 or a group has n < 20; Monte
    Carlo permutation test of the chi-square (10 000 permutations, seed 20261121) for larger tables with
    an expected count < 5; compare_k: classic Levene (mean-centred) to choose one-way vs Welch ANOVA;
  - a failed model (separation, non-convergence, collinearity) records nothing and logs
    "MODEL FAILED A<n>: <reason>; <advice>" after its warnings;
  - Haldane correction (0.5 added to every cell when any cell is 0) applies to OR and RR only; the risk
    difference uses the observed counts (Wald);
  - all CIs are 95% (z = 1.959964 for crude effects and GLM/logit Wald CIs, t for OLS and Welch).
Numbers in log lines use 10 significant digits rounded half up and never exponent notation (a `.10g`
format would print 1.2e-05, which the ledger's number parser cannot read).
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
import platform
import re
import warnings
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

try:
    import numpy as np
    import pandas as pd
    import scipy
    import scipy.stats as stats
    import statsmodels
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
    from statsmodels.stats.diagnostic import het_breuschpagan
    from statsmodels.stats.oneway import anova_oneway
except ImportError as e:  # pragma: no cover - exercised only without the dependencies
    raise ImportError("crostats needs pandas, numpy, scipy and statsmodels: "
                      "python -m pip install pandas scipy statsmodels openpyxl") from e

# Number formatting identical to crolib/numfmt.py, inlined so that a project can vendor this single file
# (tests/unit/test_crostats.py checks that the two agree).
KINDS = frozenset({"n", "percent", "mean", "sd", "median", "iqr", "md", "or", "rr", "hr", "rd", "beta", "auc",
                   "p", "other"})
EN_DASH = "–"


def _round_half_up(x, decimals: int) -> Decimal:
    return Decimal(str(x)).quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)


def _fmt(x, decimals: int) -> str:
    """x with `decimals` decimals, rounded half up (numfmt.fmt, English)."""
    return format(_round_half_up(x, decimals), "f")


def _fmt_p(p) -> str:
    """p with 3 decimals or "< 0.001" (numfmt.fmt_p, English)."""
    return "< " + _fmt(0.001, 3) if p < 0.001 else _fmt(p, 3)


DEFAULTS = {"shapiro_max_n": 50, "mean_min_n": 30, "exact_min_expected": 5, "epv_min": 10,
            "outlier_iqr_k": 1.5, "overdispersion_max": 2.0}
Z95 = 1.959964
STATUSES = ("prespecified", "posthoc", "deviation")
LOG_FILE = "05_analysis/output/log.txt"
MW = "Mann–Whitney U"
EXACT_MIN_GROUP_N = 20       # 2x2 tables: Fisher exact when a group has fewer (judgement-defaults "Exact tests")
PERMUTATIONS = 10000         # Monte Carlo exact test for r x c tables with an expected count < 5
PERM_SEED = 20261121
SEPARATION_BETA_SD = 10.0    # |coef x SD of the design column| above this is read as separation / sparse data
try:
    from statsmodels.tools.sm_exceptions import PerfectSeparationError as _PSE
except ImportError:  # pragma: no cover - removed in some statsmodels versions
    _PSE = None
_FIT_ERRORS = tuple(e for e in (np.linalg.LinAlgError, _PSE) if e is not None)


# ---------------------------------------------------------------- helpers
def _num_str(v) -> str:
    """Format a number for a log line: ints as is; floats with 10 significant digits (never fewer than the
    integer digits), rounded half up like numfmt, positional (no exponent)."""
    if isinstance(v, (int, np.integer)) and not isinstance(v, bool):
        return str(int(v))
    d = Decimal(repr(float(v)))
    if d == 0:
        return "0"
    q = d.quantize(Decimal(1).scaleb(min(d.adjusted() - 9, 0)), rounding=ROUND_HALF_UP)
    s = format(q, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _finite(x) -> float | None:
    """float(x) when finite, else None."""
    if x is None:
        return None
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def _level(v) -> str:
    """Readable text for a category level (1.0 -> '1')."""
    if isinstance(v, (float, np.floating)) and float(v).is_integer():
        return str(int(v))
    return str(v)


def _fmt1(x) -> str:
    """One decimal, half up (numfmt); a negative value that rounds to zero prints as 0.0."""
    t = _fmt(x, 1)
    return "0.0" if t == "-0.0" else t


def _prefixed(label, text: str) -> str:
    """`<label>: <text>` when a label prefix is given (e.g. a subgroup), else text unchanged."""
    if label is None:
        return text
    if not isinstance(label, str) or not label.strip():
        raise ValueError(f"label must be non-empty text, got {label!r}")
    return f"{label.strip()}: {text}"


def _columns(df, exprs) -> list:
    """Data columns named in formula terms (for complete-case selection)."""
    text = " ".join(str(e) for e in exprs)
    return [c for c in df.columns if re.search(r"(?<![\w.])" + re.escape(str(c)) + r"(?![\w])", text)]


def _rank_auc(y, score) -> float:
    """AUC by the rank (Mann-Whitney) formula with average ranks for ties."""
    y = np.asarray(y, dtype=float)
    s = np.asarray(score, dtype=float)
    n1 = int((y == 1).sum())
    n0 = int((y == 0).sum())
    if n1 == 0 or n0 == 0:
        raise ValueError("AUC needs both outcome classes")
    r = stats.rankdata(s)
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def _sm_warnings(caught, package="statsmodels") -> list:
    """Distinct warnings raised by `package`, one line each, in order of first appearance."""
    out = []
    for w in caught:
        if getattr(w.category, "__module__", "").startswith(package):
            text = f"{w.category.__name__}: " + " ".join(str(w.message).split())
            if text not in out:
                out.append(text)
    return out


# ---------------------------------------------------------------- data
def load_data(path) -> "pd.DataFrame":
    """Read a de-identified 04_data/<name>.deid.csv file; refuse raw data and 00_inputs."""
    p = Path(path)
    if not p.name.endswith(".deid.csv") or "00_inputs" in p.parts:
        raise ValueError(f"crostats reads only de-identified 04_data/*.deid.csv files, not {p.name}")
    return pd.read_csv(p, encoding="utf-8-sig")


class Recorder:
    """Collect log lines, results and tables; save() writes log.txt and results.json."""

    def __init__(self, project, data_file):
        self.project = Path(project)
        root = self.project.resolve()
        df_path = Path(data_file)
        if not df_path.is_absolute():
            df_path = self.project / df_path
        df_path = df_path.resolve()
        try:
            rel = df_path.relative_to(root).as_posix()
        except ValueError:
            raise ValueError(f"data file {data_file} is not inside the project") from None
        if not (rel.startswith("04_data/") and rel.endswith(".deid.csv")):
            raise ValueError(f"data file must be 04_data/<name>.deid.csv, got {rel}")
        self.data_path = df_path
        self.data_file = rel
        self.out = self.project / "05_analysis" / "output"
        (self.out / "tables").mkdir(parents=True, exist_ok=True)
        self.lines: list = []
        self.results: list = []
        self.tables: list = []
        self._next: dict = {}

    def log(self, text) -> int:
        """Append text to log.txt (one line per text line); return the line number of its first line."""
        parts = str(text).splitlines() or [""]
        first = len(self.lines) + 1
        self.lines.extend(parts)
        return first

    def add(self, analysis_id, status, label, value, kind, *, ci=None, p=None, n=None, unit="", table=None,
            sd=None, iqr=None, count=None) -> str:
        """Record one result; returns its id R-A<n>-<NNN> (numbered per analysis from 001)."""
        if status not in STATUSES:
            raise ValueError(f"status '{status}' not in {STATUSES}")
        if not (isinstance(analysis_id, str) and re.fullmatch(r"A\d+", analysis_id)):
            raise ValueError(f"analysis_id '{analysis_id}' must be A<n>")
        if kind not in KINDS:
            raise ValueError(f"kind '{kind}' not in {sorted(KINDS)}")
        if table is not None and not re.fullmatch(r"T\d+\.\d+", str(table)):
            raise ValueError(f"table id '{table}' must be T<chapter>.<n>")
        label = " ".join(str(label).split())
        if not label:
            raise ValueError("label is empty")
        v = _finite(value)
        if v is None:
            raise ValueError(f"{label}: value {value!r} is not a finite number")
        if kind == "n":
            if v != int(v):
                raise ValueError(f"{label}: kind n needs a whole number, got {value!r}")
            v = int(v)
        k = self._next.get(analysis_id, 0) + 1
        if k > 999:
            raise ValueError(f"{analysis_id}: more than 999 results")
        rid = f"R-{analysis_id}-{k:03d}"
        rec = {"id": rid, "analysis_id": analysis_id, "status": status, "label": label, "value": v}
        line = f"{rid} {label}: value={_num_str(v)}"
        if ci is not None:
            lo, hi = _finite(ci[0]), _finite(ci[1])
            if lo is None or hi is None or lo > hi:
                raise ValueError(f"{label}: ci {ci!r} must be finite [lo, hi] with lo <= hi")
            rec["ci"] = [lo, hi]
            line += f" ci={_num_str(lo)},{_num_str(hi)}"
        if p is not None:
            pv = _finite(p)
            if pv is None or not 0 <= pv <= 1:
                raise ValueError(f"{label}: p {p!r} must be between 0 and 1")
            rec["p"] = pv
            line += f" p={_num_str(pv)}"
        if n is not None:
            rec["n"] = int(n)
            line += f" n={int(n)}"
        rec["unit"] = str(unit)
        rec["kind"] = kind
        if table is not None:
            rec["table"] = str(table)
        if sd is not None and _finite(sd) is not None:
            rec["sd"] = _finite(sd)
        if iqr is not None:
            q1, q3 = _finite(iqr[0]), _finite(iqr[1])
            if q1 is None or q3 is None:
                raise ValueError(f"{label}: iqr {iqr!r} must be finite [q1, q3]")
            rec["iqr"] = [q1, q3]
        if count is not None:
            rec["count"] = int(count)
        lineno = self.log(line)
        rec.update({"source_file": LOG_FILE, "locator": f"line {lineno}", "raw": line})
        self._next[analysis_id] = k
        self.results.append(rec)
        return rid

    def add_table(self, table_id, title, df, analysis_ids) -> Path:
        """Write 05_analysis/output/tables/<table_id>.csv and register it."""
        if not re.fullmatch(r"T\d+\.\d+", str(table_id)):
            raise ValueError(f"table id '{table_id}' must be T<chapter>.<n>")
        ids = list(analysis_ids)
        bad = [a for a in ids if not re.fullmatch(r"A\d+", str(a))]
        if bad:
            raise ValueError(f"analysis ids {bad} must be A<n>")
        path = self.out / "tables" / f"{table_id}.csv"
        df.to_csv(path, index=False, encoding="utf-8", lineterminator="\n")
        entry = {"id": str(table_id), "title": str(title), "file": f"05_analysis/output/tables/{table_id}.csv",
                 "analysis_ids": ids}
        self.tables = [t for t in self.tables if t["id"] != entry["id"]] + [entry]
        self.log(f"TABLE {table_id} {title}: {entry['file']} ({len(df)} rows; analyses {', '.join(ids)})")
        return path

    def save(self) -> Path:
        """Write log.txt then results.json; return the results.json path."""
        with open(self.out / "log.txt", "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(self.lines) + "\n")
        doc = {
            "engine": (f"Python {platform.python_version()}; pandas {pd.__version__}; numpy {np.__version__}; "
                       f"scipy {scipy.__version__}; statsmodels {statsmodels.__version__}"),
            "data_file": self.data_file,
            "data_sha256": hashlib.sha256(self.data_path.read_bytes()).hexdigest(),
            "run_at": _dt.datetime.now().isoformat(timespec="seconds"),
            "results": self.results,
            "tables": self.tables,
        }
        path = self.out / "results.json"
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(doc, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
        return path


# ---------------------------------------------------------------- description
def audit(df) -> dict:
    """Rows, duplicate rows, missing per column and Tukey outliers (outside Q1 - k*IQR, Q3 + k*IQR, k = 1.5)
    per numeric column with more than 2 distinct values."""
    k = DEFAULTS["outlier_iqr_k"]
    outliers = {}
    for c in df.columns:
        s = df[c].dropna()
        if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s) and s.nunique() > 2:
            q1, q3 = s.quantile(0.25), s.quantile(0.75)
            iqr = q3 - q1
            outliers[str(c)] = int(((s < q1 - k * iqr) | (s > q3 + k * iqr)).sum())
    return {"rows": int(len(df)), "duplicates": int(df.duplicated().sum()),
            "missing": {str(c): int(df[c].isna().sum()) for c in df.columns}, "outliers": outliers}


def describe(x) -> dict:
    """n, mean, sd, median, q1, q3, shapiro_p, skew, normal, use_mean of the non-missing values.

    Normality: Shapiro-Wilk when 3 <= n < 50 (normal if p >= 0.05); |skewness G1| < 1 when n >= 50;
    not assessable (normal False) when n < 3. use_mean = normal and n >= 30.
    """
    s = pd.Series(x).dropna().astype(float)
    n = int(len(s))
    out = {"n": n, "mean": None, "sd": None, "median": None, "q1": None, "q3": None,
           "shapiro_p": None, "skew": None, "normal": False, "use_mean": False}
    if n == 0:
        return out
    out.update(mean=float(s.mean()), sd=_finite(s.std(ddof=1)) if n > 1 else None, median=float(s.median()),
               q1=float(s.quantile(0.25)), q3=float(s.quantile(0.75)))
    if 3 <= n < DEFAULTS["shapiro_max_n"]:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            sp = _finite(stats.shapiro(s.to_numpy())[1])
        out["shapiro_p"] = sp
        out["normal"] = sp is not None and sp >= 0.05
    elif n >= DEFAULTS["shapiro_max_n"]:
        sk = _finite(stats.skew(s.to_numpy(), bias=False))
        out["skew"] = sk
        out["normal"] = sk is not None and abs(sk) < 1
    out["use_mean"] = bool(out["normal"] and n >= DEFAULTS["mean_min_n"])
    out["normal"] = bool(out["normal"])
    return out


def crude_effect(a, b, c, d) -> dict:
    """Crude OR, RR, RD from a 2x2 table: exposed a events / b non-events, unexposed c / d.

    OR with Woolf (log) CI, RR with Katz log CI, RD with Wald CI; z = 1.959964. When any cell is 0,
    0.5 is added to every cell for OR and RR (Haldane), `corrected` = True; RD uses the observed counts.
    """
    corrected = min(a, b, c, d) == 0
    A, B, C, D = (x + 0.5 for x in (a, b, c, d)) if corrected else (float(a), float(b), float(c), float(d))
    lor = math.log(A * D / (B * C))
    se_or = math.sqrt(1 / A + 1 / B + 1 / C + 1 / D)
    lrr = math.log((A / (A + B)) / (C / (C + D)))
    se_rr = math.sqrt(1 / A - 1 / (A + B) + 1 / C - 1 / (C + D))
    n1, n0 = a + b, c + d
    p1, p0 = a / n1, c / n0
    rd = p1 - p0
    se_rd = math.sqrt(p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0)
    return {"or": (math.exp(lor), math.exp(lor - Z95 * se_or), math.exp(lor + Z95 * se_or)),
            "rr": (math.exp(lrr), math.exp(lrr - Z95 * se_rr), math.exp(lrr + Z95 * se_rr)),
            "rd": (rd, rd - Z95 * se_rd, rd + Z95 * se_rd), "corrected": corrected}


# ---------------------------------------------------------------- comparisons
def _level_key(v):
    """Numeric-aware sort key: numbers and numeric text ascending by value (0 before 1, 9 before 10), then text."""
    try:
        return (0, float(v), str(v))
    except (TypeError, ValueError):
        return (1, 0.0, str(v))


def _sorted_levels(values) -> list:
    return sorted(values, key=_level_key)


def _ordered_levels(values, order, rec, group) -> list:
    """Levels of `group` in the order given by `order` (first = reference). Without `order`: numeric-aware sort,
    and a GROUP ORDER line is logged when the levels are non-numeric text (the reference is then the text sort)."""
    present = _sorted_levels(values)
    if order is None:
        if rec is not None and any(_level_key(v)[0] == 1 for v in present):
            rec.log(f"GROUP ORDER {group}: {', '.join(_level(v) for v in present)} "
                    "(text sort; pass order= to set the reference)")
        return present
    order = list(order)
    missing = [v for v in present if not any(v == o for o in order)]
    if missing or len(set(map(_level, order))) != len(order):
        raise ValueError(f"order {order!r} must list every group of {group} once: {[_level(v) for v in present]}")
    return [o for o in order if any(o == v for v in present)]


def _range_text(lo, hi, decimals=1) -> str:
    """'lo–hi' with an en dash; ' to ' when a bound is negative (shared contract: -1.2 to -0.5)."""
    def one(x):
        t = _fmt(x, decimals)
        return t[1:] if t.startswith("-") and set(t[1:]) <= set("0.") else t

    a, b = one(lo), one(hi)
    return f"{a} to {b}" if a.startswith("-") or b.startswith("-") else f"{a}{EN_DASH}{b}"


def compare_two(df, outcome, group, rec, analysis_id, status="prespecified", table=None, order=None, *,
                label=None) -> dict:
    """Compare a numeric outcome between 2 groups: Welch t-test (mean difference, Welch CI) when both
    groups use_mean, else Mann-Whitney U (p only, kind p).

    The difference is first minus second group of `order` (a tuple of the two group values); by default
    the groups are in numeric-aware ascending order (0 before 1, 9 before 10). The label states it as
    "<first> − <second>"."""
    _prefixed(label, "")
    d = df[[outcome, group]].dropna()
    present = _sorted_levels(d[group].unique())
    if len(present) != 2:
        raise ValueError(f"{group} must have exactly 2 groups with {outcome} values, has {len(present)}")
    if order is None:
        g0, g1 = _ordered_levels(present, None, rec, group)
    else:
        if len(order) != 2 or any(not (d[group] == g).any() for g in order) or order[0] == order[1]:
            raise ValueError(f"order {tuple(order)!r} must name the 2 groups of {group}: {present}")
        g0, g1 = order
    x0 = d.loc[d[group] == g0, outcome].astype(float).to_numpy()
    x1 = d.loc[d[group] == g1, outcome].astype(float).to_numpy()
    n0, n1 = len(x0), len(x1)
    d0, d1 = describe(x0), describe(x1)
    tag = f"{outcome} by {group}"
    if d0["use_mean"] and d1["use_mean"]:
        test = "Welch t-test"
        reason = (f"both groups approximately normal and n >= {DEFAULTS['mean_min_n']} "
                  f"(n {n0}/{n1}); unequal variances allowed")
        v0, v1 = x0.var(ddof=1) / n0, x1.var(ddof=1) / n1
        se = math.sqrt(v0 + v1)
        dfw = (v0 + v1) ** 2 / (v0 ** 2 / (n0 - 1) + v1 ** 2 / (n1 - 1))
        md = float(x0.mean() - x1.mean())
        p = float(2 * stats.t.sf(abs(md / se), dfw))
        tc = float(stats.t.ppf(0.975, dfw))
        ci = (md - tc * se, md + tc * se)
        rec.log(f"{analysis_id} {tag} ({_level(g0)} − {_level(g1)}): {test}; reason: {reason}; "
                f"Welch df={_num_str(dfw)}")
        rid = rec.add(analysis_id, status, _prefixed(label, f"{outcome} mean difference {_level(g0)} − {_level(g1)} "
                                                     f"by {group}, Welch t-test"), md, "md", ci=ci, p=p, n=n0 + n1, table=table)
        return {"test": test, "reason": reason, "p": p, "md": md, "ci": ci, "df": dfw, "order": (g0, g1),
                "ids": [rid]}
    test = MW
    why = [f"{_level(g)}: " + ("n < 3" if dd["n"] < 3 else f"n={dd['n']}" + ("" if dd["normal"] else ", not normal"))
           for g, dd in ((g0, d0), (g1, d1)) if not dd["use_mean"]]
    reason = (f"mean not appropriate in {'; '.join(why)} (needs normal and n >= {DEFAULTS['mean_min_n']}); "
              "two-sided, scipy method auto")
    p = float(stats.mannwhitneyu(x0, x1, alternative="two-sided")[1])
    rec.log(f"{analysis_id} {tag} ({_level(g0)} vs {_level(g1)}): {test}; reason: {reason}")
    rid = rec.add(analysis_id, status, _prefixed(label, f"{tag} ({_level(g0)} vs {_level(g1)}) p, {test}"), p, "p", p=p,
                  n=n0 + n1, table=table)
    return {"test": test, "reason": reason, "p": p, "order": (g0, g1), "ids": [rid]}


def compare_k(df, outcome, group, rec, analysis_id, status="prespecified", table=None, order=None, *,
              label=None) -> dict:
    """Compare a numeric outcome across 3 or more groups. When every group use_mean: Levene test (classic,
    centred on the mean); Levene p >= 0.05 gives one-way ANOVA (scipy f_oneway), else Welch ANOVA
    (statsmodels anova_oneway, use_var="unequal"). Otherwise Kruskal-Wallis (scipy, tie-corrected).
    Records p (kind p)."""
    _prefixed(label, "")
    d = df[[outcome, group]].dropna()
    levels = _ordered_levels(d[group].unique(), order, rec, group)
    if len(levels) < 3:
        raise ValueError(f"{group} must have at least 3 groups with {outcome} values, has {len(levels)}")
    xs = [d.loc[d[group] == g, outcome].astype(float).to_numpy() for g in levels]
    descs = [describe(x) for x in xs]
    n = int(sum(len(x) for x in xs))
    tag = f"{outcome} by {group} ({', '.join(_level(g) for g in levels)})"
    lev_p = None
    if all(dd["use_mean"] for dd in descs):
        lev_p = _finite(stats.levene(*xs, center="mean")[1])
        base = (f"every group approximately normal with n >= {DEFAULTS['mean_min_n']} "
                f"(n {'/'.join(str(len(x)) for x in xs)})")
        if lev_p is not None and lev_p >= 0.05:
            test = "One-way ANOVA"
            reason = f"{base}; equal variances (Levene p={lev_p:.3f} >= 0.05)"
            p = float(stats.f_oneway(*xs)[1])
        else:
            test = "Welch ANOVA"
            reason = f"{base}; unequal variances (Levene p={'n/a' if lev_p is None else f'{lev_p:.3f}'} < 0.05)"
            p = float(anova_oneway(xs, use_var="unequal").pvalue)
    else:
        test = "Kruskal–Wallis"
        why = [f"{_level(g)}: " + ("n < 3" if dd["n"] < 3 else f"n={dd['n']}" + ("" if dd["normal"] else ", not normal"))
               for g, dd in zip(levels, descs) if not dd["use_mean"]]
        reason = (f"mean not appropriate in {'; '.join(why)} (needs normal and n >= {DEFAULTS['mean_min_n']}); "
                  "tie-corrected")
        p = float(stats.kruskal(*xs)[1])
    rec.log(f"{analysis_id} {tag}: {test}; reason: {reason}")
    rid = rec.add(analysis_id, status, _prefixed(label, f"{tag} p, {test}"), p, "p", p=p, n=n, table=table)
    return {"test": test, "reason": reason, "p": p, "levene_p": lev_p, "ids": [rid]}


def _chi2_permutation_p(g_codes, y_codes, shape, expected, stat, permutations, seed) -> float:
    """Monte Carlo permutation p of the Pearson chi-square statistic: the outcome labels are shuffled
    against the groups (both margins fixed); p = (1 + #{X2* >= X2 (1 - 64 eps)}) / (B + 1), as R's
    chisq.test(simulate.p.value = TRUE)."""
    rng = np.random.default_rng(seed)
    r, c = shape
    n = len(y_codes)
    thr = stat * (1 - 64 * np.finfo(float).eps)
    base = g_codes.astype(np.int64) * c
    y = y_codes.astype(np.int64)
    batch = max(1, min(permutations, 2_000_000 // max(n, 1)))
    hits = done = 0
    while done < permutations:
        b = min(batch, permutations - done)
        perm = rng.permuted(np.tile(y, (b, 1)), axis=1)
        idx = (np.arange(b, dtype=np.int64)[:, None] * (r * c) + base[None, :] + perm).ravel()
        counts = np.bincount(idx, minlength=b * r * c).reshape(b, r, c)
        x2 = (((counts - expected) ** 2) / expected).sum(axis=(1, 2))
        hits += int((x2 >= thr).sum())
        done += b
    return (hits + 1) / (permutations + 1)


def compare_props(df, outcome, group, rec, analysis_id, status="prespecified", table=None, order=None, *,
                  permutations=PERMUTATIONS, seed=PERM_SEED, label=None) -> dict:
    """Compare a categorical outcome across groups (rows = groups). 2x2 table: Fisher exact (two-sided) when
    any expected count < 5 or a group has n < 20. Larger table with any expected count < 5: Monte Carlo
    exact test (permutation distribution of the Pearson chi-square, `permutations` resamples, numpy seed
    `seed`, both logged). Otherwise Pearson chi-square without continuity correction. Records p (kind p)."""
    _prefixed(label, "")
    d = df[[outcome, group]].dropna()
    tab = pd.crosstab(d[group], d[outcome])
    if tab.shape[0] < 2 or tab.shape[1] < 2:
        raise ValueError(f"{outcome} by {group}: needs at least 2 groups and 2 outcome levels")
    tab = tab.loc[_ordered_levels(tab.index, order, rec, group), _sorted_levels(tab.columns)]
    obs = tab.to_numpy()
    expected = stats.contingency.expected_freq(obs)
    emin = float(expected.min())
    gmin = int(obs.sum(axis=1).min())
    small = emin < DEFAULTS["exact_min_expected"]
    shape = f"{obs.shape[0]}x{obs.shape[1]}"
    tag = f"{outcome} by {group}"
    stat = float(((obs - expected) ** 2 / expected).sum())
    if obs.shape == (2, 2) and (small or gmin < EXACT_MIN_GROUP_N):
        test = "Fisher exact"
        why = []
        if small:
            why.append(f"an expected count < {DEFAULTS['exact_min_expected']} (min {emin:.2f})")
        if gmin < EXACT_MIN_GROUP_N:
            why.append(f"a group with n < {EXACT_MIN_GROUP_N} (min {gmin})")
        reason = f"2x2 table with {' and '.join(why)}; two-sided"
        p = float(stats.fisher_exact(obs, alternative="two-sided")[1])
    elif small:
        test = f"Monte Carlo exact (chi-square, {permutations} permutations)"
        reason = (f"{shape} table with an expected count < {DEFAULTS['exact_min_expected']} (min {emin:.2f}); "
                  f"permutation distribution of the Pearson chi-square (X2={stat:.4f}), {permutations} permutations, "
                  f"seed {seed}")
        g_codes = pd.Categorical(d[group], categories=tab.index).codes
        y_codes = pd.Categorical(d[outcome], categories=tab.columns).codes
        p = float(_chi2_permutation_p(np.asarray(g_codes), np.asarray(y_codes), obs.shape, expected, stat,
                                       permutations, seed))
    else:
        test = "Chi-square"
        chi2, p, dof, _ = stats.chi2_contingency(obs, correction=False)
        p = float(p)
        reason = (f"{shape} table, all expected counts >= {DEFAULTS['exact_min_expected']} (min {emin:.2f})"
                  + (f", every group n >= {EXACT_MIN_GROUP_N}" if obs.shape == (2, 2) else "")
                  + f"; Pearson, no continuity correction; chi2={chi2:.4f}, df={dof}")
    rec.log(f"{analysis_id} {tag}: {test}; reason: {reason}")
    rid = rec.add(analysis_id, status, _prefixed(label, f"{tag} p, {test}"), p, "p", p=p, n=int(obs.sum()),
                  table=table)
    return {"test": test, "reason": reason, "p": p, "ids": [rid]}


# ---------------------------------------------------------------- models
ADVICE = {
    "logistic": "consider Firth or exact logistic as a declared deviation",
    "linear": "remove or combine collinear terms as a declared deviation",
    "poisson": "merge sparse categories or use a penalised or negative binomial model as a declared deviation",
    "cox": "consider Firth-penalised Cox regression or merging sparse categories as a declared deviation",
}


def _fail(rec, analysis_id, reason, warn, model, **extra) -> dict:
    """Log the warnings, then `MODEL FAILED A<n>: <reason>; <advice>`; nothing is recorded for the model."""
    for w in warn:
        rec.log(f"{analysis_id} WARNING: {w}")
    rec.log(f"MODEL FAILED {analysis_id}: {reason}; {ADVICE[model]}")
    out = {"failed": True, "reason": reason, "warnings": warn, "ids": []}
    out.update(extra)
    return out


def _design_sds(names, X) -> dict:
    X = np.asarray(X, dtype=float)
    if X.ndim != 2 or X.shape[0] < 2:
        return {}
    return {str(nm): float(X[:, j].std(ddof=1)) for j, nm in enumerate(names)}


def _estimate_problems(params, bse, sds, ratio=True) -> list:
    """Signs of separation or sparse data: a non-finite coefficient or SE; for ratio models also a
    non-finite or zero exp(coef) or CI bound, or |coef x SD of its design column| > 10 (a ratio above
    e^10 per SD is not a real effect)."""
    probs = []
    for term in params.index:
        if term == "Intercept":
            continue
        b, se = float(params[term]), float(bse[term])
        if not (math.isfinite(b) and math.isfinite(se)):
            probs.append(f"non-finite coefficient for {term} or its SE")
            continue
        if not ratio:
            continue
        with np.errstate(over="ignore", under="ignore"):
            vals = np.exp(np.array([b, b - Z95 * se, b + Z95 * se]))
        if not np.isfinite(vals).all() or (vals == 0).any():
            probs.append(f"coefficient for {term} has a non-finite ratio or CI (b={b:.3g}, SE={se:.3g})")
            continue
        sd = sds.get(str(term))
        if sd is not None and math.isfinite(sd) and abs(b * sd) > SEPARATION_BETA_SD:
            probs.append(f"implausibly large coefficient for {term} (|b x SD| = {abs(b * sd):.1f} > "
                         f"{SEPARATION_BETA_SD:g})")
    return probs


def _model_problems(m, caught, family) -> list:
    """Failure signs of a fitted statsmodels model, shared by fit_logistic, fit_linear, fit_poisson and
    interaction. logit: PerfectSeparationWarning, non-convergence; poisson: non-convergence; linear:
    rank-deficient design. Then _estimate_problems (ratio rule and |coef x SD| > 10 for logit/poisson,
    non-finite coefficient or SE for linear)."""
    probs = []
    if family == "logit":
        if any("PerfectSeparation" in w.category.__name__ for w in caught):
            probs.append("perfect separation (statsmodels PerfectSeparationWarning)")
        if not m.mle_retvals.get("converged", True):
            probs.append("model did not converge")
    elif family == "poisson":
        if not getattr(m, "converged", True):
            probs.append("model did not converge")
    if family == "linear":
        X = np.asarray(m.model.exog, dtype=float)
        rank = int(np.linalg.matrix_rank(X))
        if rank < X.shape[1]:
            probs.append(f"collinear terms (design matrix rank {rank} < {X.shape[1]} columns)")
        probs += _estimate_problems(m.params, m.bse, {}, ratio=False)
    else:
        probs += _estimate_problems(m.params, m.bse, _design_sds(m.model.exog_names, m.model.exog))
    return probs


def _fit_ratio_terms(m, rec, analysis_id, status, table, kind, name, formula, n, conf=None, prefix=None):
    """Record exp(coef) of every non-intercept term; returns ({term: (est, lo, hi, p)}, ids)."""
    ci = m.conf_int() if conf is None else conf
    est, ids = {}, []
    for term in m.params.index:
        if term == "Intercept":
            continue
        e, lo, hi, p = (float(np.exp(m.params[term])), float(np.exp(ci.loc[term, 0])),
                        float(np.exp(ci.loc[term, 1])), float(m.pvalues[term]))
        est[term] = (e, lo, hi, p)
        ids.append(rec.add(analysis_id, status, _prefixed(prefix, f"{name} {term}, {formula}"), e, kind, ci=(lo, hi),
                           p=p, n=n,
                           table=table))
    return est, ids


def _hosmer_lemeshow(y, phat, groups=10):
    """Hosmer-Lemeshow: deciles of predicted risk, sum (O-E)^2 / (E (1 - E/n_g)), df = groups - 2."""
    g = pd.qcut(phat, groups, labels=False, duplicates="drop")
    frame = pd.DataFrame({"y": y, "p": phat, "g": g})
    agg = frame.groupby("g").agg(o=("y", "sum"), e=("p", "sum"), n=("y", "size"))
    k = len(agg)
    if k < 3:
        return None, None, k
    stat = float((((agg.o - agg.e) ** 2) / (agg.e * (1 - agg.e / agg.n))).sum())
    return stat, float(stats.chi2.sf(stat, k - 2)), k


def _fit_caught(fit):
    """Run fit() recording every warning; returns (result, caught warnings)."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        res = fit()
    return res, caught


def fit_logistic(df, outcome, terms, rec, analysis_id, status="prespecified", table=None, *, label=None) -> dict:
    """Logistic regression (statsmodels Logit, ML): OR with Wald 95% CI and p for each non-intercept term
    (kind or), AUC (kind auc), Hosmer-Lemeshow p (10 groups), EPV = min(events, non-events) / parameters.

    Separation (statsmodels PerfectSeparationWarning or error, non-convergence, a non-finite OR/CI, or
    |coef x SD| > 10) records nothing for the model: warnings are logged, then
    `MODEL FAILED A<n>: <reason>; consider Firth or exact logistic as a declared deviation`, and the result
    is {"failed": True, "reason", "warnings", "ids": []}."""
    _prefixed(label, "")
    formula = f"{outcome} ~ {' + '.join(terms)}"
    try:
        m, caught = _fit_caught(lambda: smf.logit(formula, df).fit(disp=0))
    except _FIT_ERRORS as e:
        rec.log(f"{analysis_id} logistic regression {formula}: reason: binary outcome")
        return _fail(rec, analysis_id, f"fit error ({type(e).__name__}: {e})", [], "logistic")
    warn = _sm_warnings(caught)
    y = np.asarray(m.model.endog, dtype=float)
    n = int(m.nobs)
    events = int(y.sum())
    k = sum(1 for t in m.params.index if t != "Intercept")
    epv = min(events, n - events) / k if k else float("inf")
    rec.log(f"{analysis_id} logistic regression {formula}: reason: binary outcome; n={n}, events={events}, "
            f"non-events={n - events}, parameters={k}, EPV={epv:.1f}")
    if epv < DEFAULTS["epv_min"]:
        warn.append(f"EPV {epv:.1f} < {DEFAULTS['epv_min']:g}: model is exploratory")
    problems = _model_problems(m, caught, "logit")
    if problems:
        return _fail(rec, analysis_id, "; ".join(problems), warn, "logistic", epv=epv, n=n, events=events)
    for w in warn:
        rec.log(f"{analysis_id} WARNING: {w}")
    est, ids = _fit_ratio_terms(m, rec, analysis_id, status, table, "or", "OR", formula, n, prefix=label)
    phat = np.asarray(m.predict(), dtype=float)
    auc = _rank_auc(y, phat)
    hl, hl_p, groups = _hosmer_lemeshow(y, phat)
    diag = []
    if hl_p is None:
        diag.append(f"Hosmer-Lemeshow not computed: only {groups} distinct risk groups")
    elif hl_p < 0.05:
        diag.append(f"Hosmer-Lemeshow p={hl_p:.3f} < 0.05: calibration is poor")
    rec.log(f"{analysis_id} diagnostics: AUC={_num_str(auc)}; Hosmer-Lemeshow "
            + (f"chi2={_num_str(hl)} df={groups - 2} p={_num_str(hl_p)}" if hl_p is not None else "not computed"))
    ids.append(rec.add(analysis_id, status, _prefixed(label, f"AUC (apparent), {formula}"), auc, "auc", n=n,
                       table=table))
    for w in diag:
        rec.log(f"{analysis_id} WARNING: {w}")
    return {"failed": False, "reason": None, "or": est, "epv": epv, "auc": auc, "hl_p": hl_p, "n": n,
            "events": events, "warnings": warn + diag, "ids": ids, "model": m}


def fit_linear(df, outcome, terms, rec, analysis_id, status="prespecified", table=None, *, label=None) -> dict:
    """Linear regression (OLS): beta with t-based 95% CI and p (kind beta), R^2 (kind other), Shapiro-Wilk on
    residuals when n < 5000, Breusch-Pagan (LM test) for heteroscedasticity. A rank-deficient design
    (collinear terms), a fit error or a non-finite estimate records nothing and logs MODEL FAILED."""
    _prefixed(label, "")
    formula = f"{outcome} ~ {' + '.join(terms)}"
    try:
        m, caught = _fit_caught(lambda: smf.ols(formula, df).fit())
    except _FIT_ERRORS as e:
        rec.log(f"{analysis_id} linear regression (OLS) {formula}: reason: continuous outcome")
        return _fail(rec, analysis_id, f"fit error ({type(e).__name__}: {e})", [], "linear")
    n = int(m.nobs)
    warn = _sm_warnings(caught)
    rec.log(f"{analysis_id} linear regression (OLS) {formula}: reason: continuous outcome; n={n}")
    problems = _model_problems(m, caught, "linear")
    if problems:
        return _fail(rec, analysis_id, "; ".join(problems), warn, "linear", n=n)
    for w in warn:
        rec.log(f"{analysis_id} WARNING: {w}")
    ci = m.conf_int()
    est, ids = {}, []
    for term in m.params.index:
        if term == "Intercept":
            continue
        b, lo, hi, p = float(m.params[term]), float(ci.loc[term, 0]), float(ci.loc[term, 1]), float(m.pvalues[term])
        est[term] = (b, lo, hi, p)
        ids.append(rec.add(analysis_id, status, _prefixed(label, f"beta {term}, {formula}"), b, "beta", ci=(lo, hi),
                           p=p, n=n,
                           table=table))
    r2 = float(m.rsquared)
    sw = _finite(stats.shapiro(m.resid)[1]) if 3 <= n < 5000 else None
    bp = _finite(het_breuschpagan(m.resid, m.model.exog)[1])
    diag = []
    if sw is not None and sw < 0.05:
        diag.append(f"residuals not normal (Shapiro-Wilk p={sw:.3f}); check the Q-Q plot")
    if bp is not None and bp < 0.05:
        diag.append(f"Breusch-Pagan p={bp:.3f} < 0.05: heteroscedasticity, consider robust (HC3) SE")
    rec.log(f"{analysis_id} diagnostics: R2={_num_str(r2)}; residual Shapiro-Wilk p="
            + (_num_str(sw) if sw is not None else "not computed") + "; Breusch-Pagan p="
            + (_num_str(bp) if bp is not None else "not computed"))
    ids.append(rec.add(analysis_id, status, _prefixed(label, f"R2, {formula}"), r2, "other", n=n, table=table))
    for w in diag:
        rec.log(f"{analysis_id} WARNING: {w}")
    return {"failed": False, "reason": None, "beta": est, "r2": r2, "resid_shapiro_p": sw, "bp_p": bp, "n": n,
            "warnings": warn + diag, "ids": ids, "model": m}


def fit_poisson(df, outcome, terms, rec, analysis_id, status="prespecified", table=None, *, exposure=None,
                label=None) -> dict:
    """Poisson GLM (log link): IRR with Wald 95% CI and p (kind rr, label "IRR ..."); dispersion = Pearson
    chi2 / residual df, warning when > 2. `exposure` names a person-time column (log offset).
    Non-convergence, a fit error, a non-finite IRR/CI or |coef x SD| > 10 records nothing and logs
    MODEL FAILED."""
    _prefixed(label, "")
    formula = f"{outcome} ~ {' + '.join(terms)}"
    d = df
    kw = {}
    if exposure is not None:
        d = df.dropna(subset=_columns(df, [outcome] + list(terms) + [exposure]))
        kw["exposure"] = d[exposure].astype(float)
    head = f"{analysis_id} Poisson regression {formula}" + (f", exposure {exposure}" if exposure else "")
    try:
        m, caught = _fit_caught(lambda: smf.glm(formula, d, family=sm.families.Poisson(), **kw).fit())
    except _FIT_ERRORS as e:
        rec.log(f"{head}: reason: count outcome")
        return _fail(rec, analysis_id, f"fit error ({type(e).__name__}: {e})", [], "poisson")
    n = int(m.nobs)
    warn = _sm_warnings(caught)
    rec.log(f"{head}: reason: count outcome; n={n}")
    problems = _model_problems(m, caught, "poisson")
    if problems:
        return _fail(rec, analysis_id, "; ".join(problems), warn, "poisson", n=n)
    for w in warn:
        rec.log(f"{analysis_id} WARNING: {w}")
    est, ids = _fit_ratio_terms(m, rec, analysis_id, status, table, "rr", "IRR", formula, n, prefix=label)
    disp = float(m.pearson_chi2 / m.df_resid) if m.df_resid > 0 else float("nan")
    diag = []
    if math.isfinite(disp) and disp > DEFAULTS["overdispersion_max"]:
        diag.append(f"Pearson chi2/df = {disp:.2f} > {DEFAULTS['overdispersion_max']:g}: overdispersion, "
                    "consider negative binomial or robust SE")
    rec.log(f"{analysis_id} diagnostics: dispersion (Pearson chi2/df)={_num_str(disp) if math.isfinite(disp) else 'n/a'}")
    for w in diag:
        rec.log(f"{analysis_id} WARNING: {w}")
    return {"failed": False, "reason": None, "irr": est, "dispersion": disp, "n": n, "warnings": warn + diag,
            "ids": ids, "model": m}


def fit_cox(df, duration, event, terms, rec, analysis_id, status="prespecified", table=None, *,
            label=None) -> dict:
    """Cox proportional hazards (lifelines CoxPHFitter, Efron ties): HR with 95% CI and p (kind hr); PH check
    by Schoenfeld-residual test (rank time transform), minimum p in `ph_min_p`; EPV = events / parameters.
    A convergence error, a non-finite HR/CI or |coef x SD| > 10 records nothing and logs MODEL FAILED."""
    _prefixed(label, "")
    try:
        from lifelines import CoxPHFitter
        from lifelines.statistics import proportional_hazard_test
    except ImportError as e:
        raise ImportError("fit_cox needs lifelines: python -m pip install lifelines") from e
    try:
        from lifelines.exceptions import ConvergenceError
    except ImportError:  # older lifelines
        from lifelines.utils import ConvergenceError
    cols = list(dict.fromkeys([duration, event] + _columns(df, terms)))
    d = df[cols].dropna()
    rhs = " + ".join(terms)
    model_txt = f"Surv({duration}, {event}) ~ {rhs}"
    n = int(len(d))
    events = int(d[event].sum())
    cph = CoxPHFitter()
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            cph.fit(d, duration_col=duration, event_col=event, formula=rhs)
    except (ConvergenceError, np.linalg.LinAlgError) as e:
        rec.log(f"{analysis_id} Cox regression {model_txt}: reason: time-to-event outcome; n={n}, events={events}")
        return _fail(rec, analysis_id, f"fit error ({type(e).__name__}: {e})", [], "cox", n=n, events=events)
    warn = _sm_warnings(caught, "lifelines")
    s = cph.summary
    k = len(s)
    epv = events / k if k else float("inf")
    rec.log(f"{analysis_id} Cox regression {model_txt}: reason: time-to-event outcome; n={n}, events={events}, "
            f"parameters={k}, EPV={epv:.1f}")
    if epv < DEFAULTS["epv_min"]:
        warn.append(f"EPV {epv:.1f} < {DEFAULTS['epv_min']:g}: model is exploratory")
    norm_sd = getattr(cph, "_norm_std", None)
    sds = {str(i): float(v) for i, v in norm_sd.items()} if norm_sd is not None else {}
    problems = _estimate_problems(cph.params_, cph.standard_errors_, sds)
    if problems:
        return _fail(rec, analysis_id, "; ".join(problems), warn, "cox", epv=epv, n=n, events=events)
    for w in warn:
        rec.log(f"{analysis_id} WARNING: {w}")
    est, ids = {}, []
    for term in s.index:
        e, lo, hi, p = (float(s.loc[term, "exp(coef)"]), float(s.loc[term, "exp(coef) lower 95%"]),
                        float(s.loc[term, "exp(coef) upper 95%"]), float(s.loc[term, "p"]))
        est[str(term)] = (e, lo, hi, p)
        ids.append(rec.add(analysis_id, status, _prefixed(label, f"HR {term}, {model_txt}"), e, "hr", ci=(lo, hi), p=p, n=n, table=table))
    ph = None
    diag = []
    try:
        ph = _finite(proportional_hazard_test(cph, d, time_transform="rank").summary["p"].min())
    except Exception as e:  # noqa: BLE001 - report, do not hide
        diag.append(f"proportional-hazards test failed: {e}")
    if ph is not None and ph < 0.05:
        diag.append(f"proportional-hazards test min p={ph:.3f} < 0.05: check Schoenfeld residuals")
    rec.log(f"{analysis_id} diagnostics: concordance={_num_str(cph.concordance_index_)}; PH test min p="
            + (_num_str(ph) if ph is not None else "not computed"))
    for w in diag:
        rec.log(f"{analysis_id} WARNING: {w}")
    return {"failed": False, "reason": None, "hr": est, "ph_min_p": ph, "concordance": float(cph.concordance_index_),
            "epv": epv, "n": n, "events": events, "warnings": warn + diag, "ids": ids, "model": cph}


def _need_id(rec, analysis_id, fn):
    if rec is not None and not (isinstance(analysis_id, str) and re.fullmatch(r"A\d+", analysis_id)):
        raise ValueError(f"{fn}: analysis_id A<n> is required when rec is given")


def roc_youden(y, score, *, rec=None, analysis_id=None, status="prespecified", label=None) -> dict:
    """ROC AUC (rank formula, average ranks) and the Youden-optimal cut-off over the unique scores, with
    score >= cutoff read as positive; ties in J go to the lower cut-off.

    With `rec` (and `analysis_id`): logs n, cut-off, sensitivity, specificity and J, records the AUC (kind
    auc, label `label` or "AUC (ROC)", n = pairs used), and when AUC < 0.5 logs "score direction inverted:
    AUC < 0.5; consider 1 − score" (the score is never flipped silently). Returns also `warnings`, `ids`."""
    _need_id(rec, analysis_id, "roc_youden")
    y = np.asarray(y, dtype=float)
    s = np.asarray(score, dtype=float)
    keep = np.isfinite(y) & np.isfinite(s)
    y, s = y[keep], s[keep]
    if not np.isin(y, (0, 1)).all():
        raise ValueError("y must be 0/1")
    auc = _rank_auc(y, s)
    n1, n0 = (y == 1).sum(), (y == 0).sum()
    best = None
    for c in np.unique(s):
        pos = s >= c
        sens = float((pos & (y == 1)).sum() / n1)
        spec = float((~pos & (y == 0)).sum() / n0)
        j = sens + spec - 1
        if best is None or j > best["j"] + 1e-12:
            best = {"cutoff": float(c), "sens": sens, "spec": spec, "j": j}
    warn = ["score direction inverted: AUC < 0.5; consider 1 − score"] if auc < 0.5 else []
    ids = []
    if rec is not None:
        n = int(len(y))
        rec.log(f"{analysis_id} ROC {label or 'AUC (ROC)'}: n={n}, positives={int(n1)}, negatives={int(n0)}; "
                f"AUC by the rank formula; Youden cutoff={_num_str(best['cutoff'])} (score >= cutoff positive), "
                f"sens={_num_str(best['sens'])}, spec={_num_str(best['spec'])}, J={_num_str(best['j'])}")
        for w in warn:
            rec.log(f"{analysis_id} WARNING: {w}")
        ids.append(rec.add(analysis_id, status, label or "AUC (ROC)", auc, "auc", n=n))
    return {"auc": auc, **best, "warnings": warn, "ids": ids}


_FAMILIES = {
    "logit": ("logit", "logistic", lambda f, d: smf.logit(f, d).fit(disp=0)),
    "linear": ("linear", "linear", lambda f, d: smf.ols(f, d).fit()),
    "ols": ("linear", "linear", lambda f, d: smf.ols(f, d).fit()),
    "poisson": ("poisson", "poisson", lambda f, d: smf.glm(f, d, family=sm.families.Poisson()).fit()),
}


def interaction(df, outcome, exposure, modifier, covariates, family="logit", *, rec=None, analysis_id=None,
                status="prespecified", label=None) -> float:
    """Likelihood-ratio p for exposure x modifier: reduced `outcome ~ exposure + modifier + covariates` vs full
    (`+ exposure:modifier`), same family (logit, linear/ols, poisson), same complete cases;
    LR = 2 (llf_full - llf_reduced), df = difference in number of parameters.

    Both models get the guards of fit_logistic / fit_linear / fit_poisson (_model_problems: separation,
    non-convergence, |coef x SD| > 10, non-finite estimates, collinearity, fit errors). On failure it returns
    float("nan"); with `rec` it logs the warnings and `MODEL FAILED A<n>: interaction <exposure>×<modifier>:
    <reason>; <advice>` and records nothing. On success with `rec` (and `analysis_id`) it logs the test and
    df and records the p (kind p, label `label` or "p-interaction <exposure>×<modifier>", n = rows used)."""
    if family not in _FAMILIES:
        raise ValueError(f"family must be one of {sorted(_FAMILIES)}")
    _need_id(rec, analysis_id, "interaction")
    kind, advice, fit = _FAMILIES[family]
    name = f"{exposure}×{modifier}"
    rhs = [exposure, modifier] + list(covariates)
    d = df.dropna(subset=_columns(df, [outcome] + rhs))
    n = int(len(d))
    f_red = f"{outcome} ~ {' + '.join(rhs)}"
    f_full = f"{outcome} ~ {' + '.join(rhs + [f'{exposure}:{modifier}'])}"
    warn, problems, models = [], [], {}
    for which, formula in (("reduced", f_red), ("full", f_full)):
        try:
            m, caught = _fit_caught(lambda: fit(formula, d))
        except _FIT_ERRORS as e:
            problems.append(f"{which} model: fit error ({type(e).__name__}: {e})")
            continue
        warn += [f"{which} model: {w}" for w in _sm_warnings(caught)]
        probs = _model_problems(m, caught, kind)
        if probs:
            problems.append(f"{which} model: " + "; ".join(probs))
        models[which] = m
    if problems:
        if rec is not None:
            rec.log(f"{analysis_id} interaction {name} ({family}): likelihood-ratio test, {f_red} vs {f_full}; n={n}")
            for w in warn:
                rec.log(f"{analysis_id} WARNING: {w}")
            rec.log(f"MODEL FAILED {analysis_id}: interaction {name}: {'; '.join(problems)}; {ADVICE[advice]}")
        return float("nan")
    red, full = models["reduced"], models["full"]
    ddf = len(full.params) - len(red.params)
    if ddf <= 0:
        raise ValueError("the interaction term adds no parameter")
    lr = max(0.0, 2 * (float(full.llf) - float(red.llf)))
    p = float(stats.chi2.sf(lr, ddf))
    if rec is not None:
        rec.log(f"{analysis_id} interaction {name} ({family}): likelihood-ratio test, {f_red} vs {f_full}; "
                f"n={n}, LR={_num_str(lr)}, df={ddf}; reason: effect modification tested on the same complete cases")
        for w in warn:
            rec.log(f"{analysis_id} WARNING: {w}")
        rec.add(analysis_id, status, label or f"p-interaction {name}", p, "p", n=n)
    return p


# ---------------------------------------------------------------- Table 1
def table1(df, variables, by, rec, table_id, title, analysis_id="A0", show_p=True, order=None) -> "pd.DataFrame":
    """Descriptive table by group. A numeric column with more than 2 distinct values is continuous, anything
    else categorical (n (%) of non-missing per level).

    A continuous row is shown as mean ± SD when every group (with values) use_mean, else as median (Q1–Q3);
    the overall column follows the groups. The p value follows what is shown: a mean ± SD row is tested
    parametrically (Welch t-test for 2 groups, one-way or Welch ANOVA for more, compare_two / compare_k),
    a median row non-parametrically (Mann–Whitney U / Kruskal–Wallis); both functions use the same
    every-group use_mean rule, so the test always matches the display. Categorical rows use compare_props
    (2x2 or r x c). Groups are in `order` (a list of levels, first = reference) or, by default, numeric-aware
    ascending order (text-coded groups then log a GROUP ORDER line). Rows with missing `by` are excluded and
    counted in the log; all records go under analysis_id."""
    sub = df[df[by].notna()]
    groups = _ordered_levels(sub[by].unique(), order, rec, by)
    cols = [("overall", sub)] + [(_level(g), sub[sub[by] == g]) for g in groups]
    header = ["Characteristic"] + [f"{'Overall' if name == 'overall' else name} (n={len(part)})"
                                   for name, part in cols]
    if show_p:
        header += ["p", "Test"]
    rec.log(f"{analysis_id} Table {table_id} {title}: by {by}, N={len(sub)}, groups "
            + ", ".join(f"{name}={len(part)}" for name, part in cols[1:])
            + f"; {len(df) - len(sub)} rows with missing {by} excluded")
    st = "prespecified"
    rows = []

    def ptest(var, numeric):
        if not show_p:
            return []
        if len(groups) < 2:
            rec.log(f"{analysis_id} {var}: p not computed (needs at least 2 groups, has {len(groups)})")
            return ["", ""]
        fn = (compare_two if len(groups) == 2 else compare_k) if numeric else compare_props
        try:
            r = fn(sub, var, by, rec, analysis_id, st, table=table_id, order=tuple(groups) if len(groups) == 2 else groups)
        except ValueError as e:
            rec.log(f"{analysis_id} {var}: p not computed ({e})")
            return ["", ""]
        return [_fmt_p(r["p"]), r["test"]]

    for var in variables:
        s = sub[var]
        nonmiss = s.dropna()
        miss = int(s.isna().sum())
        if miss:
            rec.log(f"{analysis_id} {var}: {miss} missing values excluded")
        numeric = (pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s)
                   and nonmiss.nunique() > 2)
        if numeric:
            descs = [(name, describe(part[var])) for name, part in cols]
            filled = [dd for name, dd in descs[1:] if dd["n"] > 0]
            use_mean = bool(filled) and all(dd["use_mean"] for dd in filled)
            rec.log(f"{analysis_id} {var}: " + ("mean ± SD (every group normal with n >= "
                                                 f"{DEFAULTS['mean_min_n']})" if use_mean else
                                                 "median (Q1–Q3) (a group is not normal or has n < "
                                                 f"{DEFAULTS['mean_min_n']})"))
            cells = []
            for name, dd in descs:
                if dd["n"] == 0:
                    cells.append("")
                    continue
                lab = f"{var} [{name}]"
                if use_mean:
                    sd = dd["sd"]
                    cells.append(_fmt1(dd["mean"]) + (f" ± {_fmt1(sd)}" if sd is not None else ""))
                    rec.add(analysis_id, st, lab, dd["mean"], "mean", n=dd["n"], sd=sd, table=table_id)
                else:
                    cells.append(f"{_fmt1(dd['median'])} ({_range_text(dd['q1'], dd['q3'])})")
                    rec.add(analysis_id, st, lab, dd["median"], "median", n=dd["n"], iqr=(dd["q1"], dd["q3"]),
                            table=table_id)
            name_cell = f"{var}, mean ± SD" if use_mean else f"{var}, median (Q1–Q3)"
            rows.append([name_cell] + cells + ptest(var, True))
        else:
            levels = _sorted_levels(nonmiss.unique())
            rows.append([f"{var}, n (%)"] + [""] * len(cols) + ptest(var, False))
            for lev in levels:
                cells = []
                for name, part in cols:
                    col = part[var].dropna()
                    denom = len(col)
                    cnt = int((col == lev).sum())
                    if denom == 0:
                        cells.append("")
                        continue
                    pct = 100.0 * cnt / denom
                    cells.append(f"{cnt} ({_fmt1(pct)})")
                    rec.add(analysis_id, st, f"{var} = {_level(lev)} [{name}]", pct, "percent", n=denom, count=cnt,
                            table=table_id)
                rows.append([f"  {_level(lev)}"] + cells + (["", ""] if show_p else []))
    out = pd.DataFrame(rows, columns=header)
    rec.add_table(table_id, title, out, [analysis_id])
    return out
