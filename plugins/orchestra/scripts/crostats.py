"""Statistics library for a project's own analysis script (crostats = clinical-research-orchestra stats).

Dependencies: pandas, numpy, scipy, statsmodels (python -m pip install pandas scipy statsmodels openpyxl);
lifelines only for fit_cox, imported lazily (python -m pip install lifelines).

Imported by the project's 05_analysis/analysis.py; never reads 00_inputs. Data come only from
04_data/*.deid.csv (load_data refuses anything else). Every test choice is written to
05_analysis/output/log.txt with its reason (Recorder.log) and every estimate is recorded with
Recorder.add, which writes one log line per result; that line is the record's `raw` text and its
`locator` is "line <k>", so results_ledger.py --verify-raw can find it.

Labelled defaults (judgement-defaults.md) are in DEFAULTS. Choices the brief leaves open, and the
standard option taken:
  - quartiles: pandas linear interpolation (R type 7); SPSS uses type 6, so Q1/Q3 can differ slightly;
  - skewness (n >= 50): adjusted Fisher-Pearson G1 (scipy.stats.skew(bias=False), as SPSS/Excel);
  - Mann-Whitney U: scipy default method "auto" (exact for small samples without ties, else normal
    approximation with continuity correction), two-sided;
  - mean difference in compare_two: first level minus second level in sorted order;
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
import sys
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
except ImportError as e:  # pragma: no cover - exercised only without the dependencies
    raise ImportError("crostats needs pandas, numpy, scipy and statsmodels: "
                      "python -m pip install pandas scipy statsmodels openpyxl") from e

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crolib import numfmt  # noqa: E402

DEFAULTS = {"shapiro_max_n": 50, "mean_min_n": 30, "exact_min_expected": 5, "epv_min": 10,
            "outlier_iqr_k": 1.5, "overdispersion_max": 2.0}
Z95 = 1.959964
STATUSES = ("prespecified", "posthoc", "deviation")
LOG_FILE = "05_analysis/output/log.txt"
MW = "Mann–Whitney U"


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
    t = numfmt.fmt(x, 1)
    return "0.0" if t == "-0.0" else t


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


def _sm_warnings(caught) -> list:
    return [f"{w.category.__name__}: {w.message}" for w in caught
            if getattr(w.category, "__module__", "").startswith("statsmodels")]


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
        if kind not in numfmt.KINDS:
            raise ValueError(f"kind '{kind}' not in {sorted(numfmt.KINDS)}")
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
def _two_groups(df, outcome, group):
    d = df[[outcome, group]].dropna()
    levels = sorted(d[group].unique(), key=str)
    if len(levels) != 2:
        raise ValueError(f"{group} must have exactly 2 groups, has {len(levels)}")
    return d, levels


def compare_two(df, outcome, group, rec, analysis_id, status="prespecified", table=None) -> dict:
    """Compare a numeric outcome between 2 groups: Welch t-test (mean difference, Welch CI) when both
    groups use_mean, else Mann-Whitney U (p only, kind p). Difference = first minus second sorted level."""
    d, (g0, g1) = _two_groups(df, outcome, group)
    x0 = d.loc[d[group] == g0, outcome].astype(float).to_numpy()
    x1 = d.loc[d[group] == g1, outcome].astype(float).to_numpy()
    n0, n1 = len(x0), len(x1)
    if min(n0, n1) == 0:
        raise ValueError(f"{group}: a group has no values of {outcome}")
    d0, d1 = describe(x0), describe(x1)
    tag = f"{outcome} by {group} ({_level(g0)} vs {_level(g1)})"
    if d0["use_mean"] and d1["use_mean"] and n0 > 1 and n1 > 1:
        test = "Welch t-test"
        reason = (f"both groups approximately normal and n >= {DEFAULTS['mean_min_n']} "
                  f"(n {n0}/{n1}); unequal variances allowed")
        v0, v1 = x0.var(ddof=1) / n0, x1.var(ddof=1) / n1
        se = math.sqrt(v0 + v1)
        dfw = (v0 + v1) ** 2 / (v0 ** 2 / (n0 - 1) + v1 ** 2 / (n1 - 1))
        md = float(x0.mean() - x1.mean())
        p = float(2 * stats.t.sf(abs(md / se), dfw))
        tc = float(stats.t.ppf(0.975, dfw))
        rec.log(f"{analysis_id} {tag}: {test}; reason: {reason}; Welch df={_num_str(dfw)}")
        rid = rec.add(analysis_id, status, f"{tag} mean difference, Welch t-test", md, "md",
                      ci=(md - tc * se, md + tc * se), p=p, n=n0 + n1, table=table)
        return {"test": test, "reason": reason, "p": p, "md": md, "ci": (md - tc * se, md + tc * se),
                "df": dfw, "ids": [rid]}
    test = MW
    why = [f"{_level(g)}: " + ("n < 3" if dd["n"] < 3 else f"n={dd['n']}" + ("" if dd["normal"] else ", not normal"))
           for g, dd in ((g0, d0), (g1, d1)) if not dd["use_mean"]]
    reason = (f"mean not appropriate in {'; '.join(why) or 'a group with n < 2'} "
              f"(needs normal and n >= {DEFAULTS['mean_min_n']}); two-sided, scipy method auto")
    p = float(stats.mannwhitneyu(x0, x1, alternative="two-sided")[1])
    rec.log(f"{analysis_id} {tag}: {test}; reason: {reason}")
    rid = rec.add(analysis_id, status, f"{tag} p, {test}", p, "p", p=p, n=n0 + n1, table=table)
    return {"test": test, "reason": reason, "p": p, "ids": [rid]}


def compare_props(df, outcome, group, rec, analysis_id, status="prespecified", table=None) -> dict:
    """Compare a categorical outcome across groups: Fisher exact (two-sided) for a 2x2 table when any
    expected count < 5, else Pearson chi-square without continuity correction. Records p (kind p)."""
    d = df[[outcome, group]].dropna()
    tab = pd.crosstab(d[group], d[outcome])
    if tab.shape[0] < 2 or tab.shape[1] < 2:
        raise ValueError(f"{outcome} by {group}: needs at least 2 groups and 2 outcome levels")
    obs = tab.to_numpy()
    expected = stats.contingency.expected_freq(obs)
    emin = float(expected.min())
    small = emin < DEFAULTS["exact_min_expected"]
    shape = f"{obs.shape[0]}x{obs.shape[1]}"
    tag = f"{outcome} by {group}"
    if obs.shape == (2, 2) and small:
        test = "Fisher exact"
        reason = f"2x2 table with an expected count < {DEFAULTS['exact_min_expected']} (min {emin:.2f})"
        p = float(stats.fisher_exact(obs, alternative="two-sided")[1])
    else:
        test = "Chi-square"
        reason = (f"{shape} table, all expected counts >= {DEFAULTS['exact_min_expected']} (min {emin:.2f}); "
                  "Pearson, no continuity correction")
        if small:
            reason = (f"{shape} table larger than 2x2 with an expected count < {DEFAULTS['exact_min_expected']} "
                      f"(min {emin:.2f}): chi-square approximation may be poor, consider merging levels")
        chi2, p, dof, _ = stats.chi2_contingency(obs, correction=False)
        p = float(p)
        reason += f"; chi2={chi2:.4f}, df={dof}"
    rec.log(f"{analysis_id} {tag}: {test}; reason: {reason}")
    rid = rec.add(analysis_id, status, f"{tag} p, {test}", p, "p", p=p, n=int(obs.sum()), table=table)
    return {"test": test, "reason": reason, "p": p, "ids": [rid]}


# ---------------------------------------------------------------- models
def _fit_ratio_terms(m, rec, analysis_id, status, table, kind, name, formula, n, conf=None):
    """Record exp(coef) of every non-intercept term; returns ({term: (est, lo, hi, p)}, ids)."""
    ci = m.conf_int() if conf is None else conf
    est, ids = {}, []
    for term in m.params.index:
        if term == "Intercept":
            continue
        e, lo, hi, p = (float(np.exp(m.params[term])), float(np.exp(ci.loc[term, 0])),
                        float(np.exp(ci.loc[term, 1])), float(m.pvalues[term]))
        est[term] = (e, lo, hi, p)
        ids.append(rec.add(analysis_id, status, f"{name} {term}, {formula}", e, kind, ci=(lo, hi), p=p, n=n,
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


def fit_logistic(df, outcome, terms, rec, analysis_id, status="prespecified", table=None) -> dict:
    """Logistic regression (statsmodels Logit, ML): OR with Wald 95% CI and p for each non-intercept term
    (kind or), AUC (kind auc), Hosmer-Lemeshow p (10 groups), EPV = min(events, non-events) / parameters."""
    formula = f"{outcome} ~ {' + '.join(terms)}"
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        m = smf.logit(formula, df).fit(disp=0)
    warn = _sm_warnings(caught)
    if not m.mle_retvals.get("converged", True):
        warn.append("model did not converge")
    y = np.asarray(m.model.endog, dtype=float)
    n = int(m.nobs)
    events = int(y.sum())
    k = sum(1 for t in m.params.index if t != "Intercept")
    epv = min(events, n - events) / k if k else float("inf")
    rec.log(f"{analysis_id} logistic regression {formula}: reason: binary outcome; n={n}, events={events}, "
            f"non-events={n - events}, parameters={k}, EPV={epv:.1f}")
    if epv < DEFAULTS["epv_min"]:
        warn.append(f"EPV {epv:.1f} < {DEFAULTS['epv_min']:g}: model is exploratory")
    est, ids = _fit_ratio_terms(m, rec, analysis_id, status, table, "or", "OR", formula, n)
    phat = np.asarray(m.predict(), dtype=float)
    auc = _rank_auc(y, phat)
    hl, hl_p, groups = _hosmer_lemeshow(y, phat)
    if hl_p is None:
        warn.append(f"Hosmer-Lemeshow not computed: only {groups} distinct risk groups")
    elif hl_p < 0.05:
        warn.append(f"Hosmer-Lemeshow p={hl_p:.3f} < 0.05: calibration is poor")
    rec.log(f"{analysis_id} diagnostics: AUC={_num_str(auc)}; Hosmer-Lemeshow "
            + (f"chi2={_num_str(hl)} df={groups - 2} p={_num_str(hl_p)}" if hl_p is not None else "not computed"))
    ids.append(rec.add(analysis_id, status, f"AUC (apparent), {formula}", auc, "auc", n=n, table=table))
    for w in warn:
        rec.log(f"{analysis_id} WARNING: {w}")
    return {"or": est, "epv": epv, "auc": auc, "hl_p": hl_p, "n": n, "events": events, "warnings": warn,
            "ids": ids, "model": m}


def fit_linear(df, outcome, terms, rec, analysis_id, status="prespecified", table=None) -> dict:
    """Linear regression (OLS): beta with t-based 95% CI and p (kind beta), R^2 (kind other), Shapiro-Wilk on
    residuals when n < 5000, Breusch-Pagan (LM test) for heteroscedasticity."""
    formula = f"{outcome} ~ {' + '.join(terms)}"
    m = smf.ols(formula, df).fit()
    n = int(m.nobs)
    warn = []
    rec.log(f"{analysis_id} linear regression (OLS) {formula}: reason: continuous outcome; n={n}")
    ci = m.conf_int()
    est, ids = {}, []
    for term in m.params.index:
        if term == "Intercept":
            continue
        b, lo, hi, p = float(m.params[term]), float(ci.loc[term, 0]), float(ci.loc[term, 1]), float(m.pvalues[term])
        est[term] = (b, lo, hi, p)
        ids.append(rec.add(analysis_id, status, f"beta {term}, {formula}", b, "beta", ci=(lo, hi), p=p, n=n,
                           table=table))
    r2 = float(m.rsquared)
    sw = _finite(stats.shapiro(m.resid)[1]) if 3 <= n < 5000 else None
    bp = _finite(het_breuschpagan(m.resid, m.model.exog)[1])
    if sw is not None and sw < 0.05:
        warn.append(f"residuals not normal (Shapiro-Wilk p={sw:.3f}); check the Q-Q plot")
    if bp is not None and bp < 0.05:
        warn.append(f"Breusch-Pagan p={bp:.3f} < 0.05: heteroscedasticity, consider robust (HC3) SE")
    rec.log(f"{analysis_id} diagnostics: R2={_num_str(r2)}; residual Shapiro-Wilk p="
            + (_num_str(sw) if sw is not None else "not computed") + "; Breusch-Pagan p="
            + (_num_str(bp) if bp is not None else "not computed"))
    ids.append(rec.add(analysis_id, status, f"R2, {formula}", r2, "other", n=n, table=table))
    for w in warn:
        rec.log(f"{analysis_id} WARNING: {w}")
    return {"beta": est, "r2": r2, "resid_shapiro_p": sw, "bp_p": bp, "n": n, "warnings": warn, "ids": ids,
            "model": m}


def fit_poisson(df, outcome, terms, rec, analysis_id, status="prespecified", table=None, *, exposure=None) -> dict:
    """Poisson GLM (log link): IRR with Wald 95% CI and p (kind rr, label "IRR ..."); dispersion = Pearson
    chi2 / residual df, warning when > 2. `exposure` names a person-time column (log offset)."""
    formula = f"{outcome} ~ {' + '.join(terms)}"
    d = df
    kw = {}
    if exposure is not None:
        d = df.dropna(subset=_columns(df, [outcome] + list(terms) + [exposure]))
        kw["exposure"] = d[exposure].astype(float)
    m = smf.glm(formula, d, family=sm.families.Poisson(), **kw).fit()
    n = int(m.nobs)
    rec.log(f"{analysis_id} Poisson regression {formula}" + (f", exposure {exposure}" if exposure else "")
            + f": reason: count outcome; n={n}")
    est, ids = _fit_ratio_terms(m, rec, analysis_id, status, table, "rr", "IRR", formula, n)
    disp = float(m.pearson_chi2 / m.df_resid) if m.df_resid > 0 else float("nan")
    warn = []
    if math.isfinite(disp) and disp > DEFAULTS["overdispersion_max"]:
        warn.append(f"Pearson chi2/df = {disp:.2f} > {DEFAULTS['overdispersion_max']:g}: overdispersion, "
                    "consider negative binomial or robust SE")
    rec.log(f"{analysis_id} diagnostics: dispersion (Pearson chi2/df)={_num_str(disp) if math.isfinite(disp) else 'n/a'}")
    for w in warn:
        rec.log(f"{analysis_id} WARNING: {w}")
    return {"irr": est, "dispersion": disp, "n": n, "warnings": warn, "ids": ids, "model": m}


def fit_cox(df, duration, event, terms, rec, analysis_id, status="prespecified", table=None) -> dict:
    """Cox proportional hazards (lifelines CoxPHFitter, Efron ties): HR with 95% CI and p (kind hr); PH check
    by Schoenfeld-residual test (rank time transform), minimum p in `ph_min_p`; EPV = events / parameters."""
    try:
        from lifelines import CoxPHFitter
        from lifelines.statistics import proportional_hazard_test
    except ImportError as e:
        raise ImportError("fit_cox needs lifelines: python -m pip install lifelines") from e
    cols = list(dict.fromkeys([duration, event] + _columns(df, terms)))
    d = df[cols].dropna()
    rhs = " + ".join(terms)
    cph = CoxPHFitter()
    cph.fit(d, duration_col=duration, event_col=event, formula=rhs)
    n = int(len(d))
    events = int(d[event].sum())
    s = cph.summary
    k = len(s)
    epv = events / k if k else float("inf")
    label = f"Surv({duration}, {event}) ~ {rhs}"
    rec.log(f"{analysis_id} Cox regression {label}: reason: time-to-event outcome; n={n}, events={events}, "
            f"parameters={k}, EPV={epv:.1f}")
    warn = []
    if epv < DEFAULTS["epv_min"]:
        warn.append(f"EPV {epv:.1f} < {DEFAULTS['epv_min']:g}: model is exploratory")
    est, ids = {}, []
    for term in s.index:
        e, lo, hi, p = (float(s.loc[term, "exp(coef)"]), float(s.loc[term, "exp(coef) lower 95%"]),
                        float(s.loc[term, "exp(coef) upper 95%"]), float(s.loc[term, "p"]))
        est[str(term)] = (e, lo, hi, p)
        ids.append(rec.add(analysis_id, status, f"HR {term}, {label}", e, "hr", ci=(lo, hi), p=p, n=n, table=table))
    ph = None
    try:
        ph = _finite(proportional_hazard_test(cph, d, time_transform="rank").summary["p"].min())
    except Exception as e:  # noqa: BLE001 - report, do not hide
        warn.append(f"proportional-hazards test failed: {e}")
    if ph is not None and ph < 0.05:
        warn.append(f"proportional-hazards test min p={ph:.3f} < 0.05: check Schoenfeld residuals")
    rec.log(f"{analysis_id} diagnostics: concordance={_num_str(cph.concordance_index_)}; PH test min p="
            + (_num_str(ph) if ph is not None else "not computed"))
    for w in warn:
        rec.log(f"{analysis_id} WARNING: {w}")
    return {"hr": est, "ph_min_p": ph, "concordance": float(cph.concordance_index_), "epv": epv, "n": n,
            "events": events, "warnings": warn, "ids": ids, "model": cph}


def roc_youden(y, score) -> dict:
    """ROC AUC (rank formula, average ranks) and the Youden-optimal cut-off over the unique scores, with
    score >= cutoff read as positive; ties in J go to the lower cut-off."""
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
    return {"auc": auc, **best}


_FAMILIES = {
    "logit": lambda f, d: smf.logit(f, d).fit(disp=0),
    "linear": lambda f, d: smf.ols(f, d).fit(),
    "ols": lambda f, d: smf.ols(f, d).fit(),
    "poisson": lambda f, d: smf.glm(f, d, family=sm.families.Poisson()).fit(),
}


def interaction(df, outcome, exposure, modifier, covariates, family="logit") -> float:
    """Likelihood-ratio p for exposure x modifier: reduced `outcome ~ exposure + modifier + covariates` vs full
    (`+ exposure:modifier`), same family (logit, linear/ols, poisson), same complete cases;
    LR = 2 (llf_full - llf_reduced), df = difference in number of parameters."""
    if family not in _FAMILIES:
        raise ValueError(f"family must be one of {sorted(_FAMILIES)}")
    rhs = [exposure, modifier] + list(covariates)
    d = df.dropna(subset=_columns(df, [outcome] + rhs))
    fit = _FAMILIES[family]
    red = fit(f"{outcome} ~ {' + '.join(rhs)}", d)
    full = fit(f"{outcome} ~ {' + '.join(rhs + [f'{exposure}:{modifier}'])}", d)
    ddf = len(full.params) - len(red.params)
    if ddf <= 0:
        raise ValueError("the interaction term adds no parameter")
    lr = max(0.0, 2 * (float(full.llf) - float(red.llf)))
    return float(stats.chi2.sf(lr, ddf))


# ---------------------------------------------------------------- Table 1
def table1(df, variables, by, rec, table_id, title, analysis_id="A0", show_p=True) -> "pd.DataFrame":
    """Descriptive table by group. A numeric column with more than 2 distinct values is continuous: mean ± SD
    when the overall column and every group use_mean, else median (Q1–Q3); anything else is categorical,
    n (%) of non-missing per level. p (2 groups only) from compare_two / compare_props under analysis_id.
    Rows with missing `by` are excluded and counted in the log."""
    sub = df[df[by].notna()]
    groups = sorted(sub[by].unique(), key=str)
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
        if len(groups) != 2:
            rec.log(f"{analysis_id} {var}: p not computed (needs exactly 2 groups, has {len(groups)})")
            return ["", ""]
        try:
            r = (compare_two if numeric else compare_props)(sub, var, by, rec, analysis_id, st, table=table_id)
        except ValueError as e:
            rec.log(f"{analysis_id} {var}: p not computed ({e})")
            return ["", ""]
        return [numfmt.fmt_p(r["p"]), r["test"]]

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
            use_mean = all(dd["use_mean"] for _, dd in descs if dd["n"] > 0)
            rec.log(f"{analysis_id} {var}: " + ("mean ± SD (every column normal with n >= "
                                                 f"{DEFAULTS['mean_min_n']})" if use_mean else
                                                 "median (Q1–Q3) (a column is not normal or has n < "
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
                    cells.append(f"{_fmt1(dd['median'])} ({_fmt1(dd['q1'])}{numfmt.EN_DASH}{_fmt1(dd['q3'])})")
                    rec.add(analysis_id, st, lab, dd["median"], "median", n=dd["n"], iqr=(dd["q1"], dd["q3"]),
                            table=table_id)
            name_cell = f"{var}, mean ± SD" if use_mean else f"{var}, median (Q1–Q3)"
            rows.append([name_cell] + cells + ptest(var, True))
        else:
            try:
                levels = sorted(nonmiss.unique())
            except TypeError:
                levels = sorted(nonmiss.unique(), key=str)
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
