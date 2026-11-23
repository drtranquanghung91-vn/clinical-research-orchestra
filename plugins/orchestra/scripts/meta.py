#!/usr/bin/env python3
"""Meta-analysis for a systematic review (standard library only), with an optional cross-check in R metafor.

  python meta.py <project> run           pooled estimates from 04_data/sr/extraction.csv and the register
  python meta.py <project> forest-spec   forest-plot entries F-A<n> in 07_present/figures/figures.json
  python meta.py <project> r-script      writes 05_analysis/meta/metafor.R (reads the files `run` wrote)
  python meta.py <project> r-status      where Rscript is and whether metafor is installed
  python meta.py <project> r-check       runs metafor.R and compares with the Python values (E-META warn)

The register is the "## Analysis register" table of 03_protocol/sr-protocol.md (columns ID, Type, Outcome,
Timepoint, Measure, Model, HKSJ, Experimental, Comparator, Factor; Type pool | subgroup | leave-one-out; A0 =
PRISMA counts, skipped). Measures: OR, RR, RD (2x2 counts; 0.5 added to every cell of a study with a zero cell;
studies with no events, or only events, in both groups excluded with a log line), MD, SMD (Hedges' g, exact
correction), GEN (es, se), GEN-OR / GEN-RR / GEN-HR (log-scale es, se). Models: RE-REML (default), RE-DL,
CE-IV, CE-MH (OR, RR); HKSJ yes = Hartung-Knapp-Sidik-Jonkman interval. Reported: estimate and 95% CI, tau²,
I², Q and its p, 95% prediction interval (random effects, k >= 3), Egger's test (k >= 10), one subgroup factor
(test for subgroup differences), leave-one-out. Fewer than 2 studies: no pooling, a narrative log line.
Results go to 05_analysis/output/meta-log.txt (P2 log format) and are merged into the results ledger as
R-A<n>-NNN (status prespecified, or deviation when decisions.md has "DEVIATION A<n>:"). A scoping review is
refused (PRISMA-ScR: chart, do not pool).
R is optional: Rscript is looked for in project.yaml tools.rscript, PATH, R_HOME, then the usual install folders
of the OS. The Python engine stays the reference for the ledger; r-check only reports differences (rel. tol. 1e-4).
Exit codes: 0 = done (r-check: warnings allowed); 1 = refused (scoping review, ledger locked by G3, label change);
2 = usage error, bad register or extraction, R or metafor missing (r-status, r-check), I/O error.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from statistics import NormalDist

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crolib import derived, projectcfg, resultlog  # noqa: E402
import analysis_plan  # noqa: E402
import results_ledger  # noqa: E402

EXTRACTION = "04_data/sr/extraction.csv"
LOG_REL = "05_analysis/output/meta-log.txt"
DOC_REL = "05_analysis/output/meta-results.json"
PY_REL = "05_analysis/meta/python-results.json"
INPUT_REL = "05_analysis/meta/meta-input.csv"
PLAN_REL = "05_analysis/meta/meta-plan.csv"
R_SCRIPT = "05_analysis/meta/metafor.R"
R_OUT = "05_analysis/meta/metafor-results.json"
FIG_REL = "07_present/figures/figures.json"
MEASURES = ("OR", "RR", "RD", "MD", "SMD", "GEN", "GEN-OR", "GEN-RR", "GEN-HR")
MODELS = ("RE-REML", "RE-DL", "CE-IV", "CE-MH")
TYPES = ("pool", "subgroup", "leave-one-out")
RATIO = {"OR", "RR", "GEN-OR", "GEN-RR", "GEN-HR"}
KIND = {"OR": "or", "RR": "rr", "RD": "rd", "MD": "md", "SMD": "smd", "GEN": "other", "GEN-OR": "or",
        "GEN-RR": "rr", "GEN-HR": "hr"}
MODEL_TEXT = {"RE-REML": "random effects, REML", "RE-DL": "random effects, DerSimonian-Laird",
              "CE-IV": "common effect, inverse variance", "CE-MH": "common effect, Mantel-Haenszel"}
INPUT_COLS = ["key", "study", "a", "n1", "c", "n2", "m1", "sd1", "m2", "sd2", "yi", "vi"]
Z = NormalDist()
Z975 = Z.inv_cdf(0.975)


class Refused(Exception):
    """exit 1"""


def read_csv(path: Path) -> list[dict]:
    """Rows of a UTF-8 CSV as dicts (local reader; keeps this script independent of other scripts)."""
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return [dict(r) for r in csv.DictReader(fh)]


def write_csv(path: Path, cols: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


# ---------------------------------------------------------------- distributions (stdlib)

def _betacf(a: float, b: float, x: float) -> float:
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 500):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        de = d * c
        h *= de
        if abs(de - 1.0) < 3e-16:
            break
    return h


def betai(a: float, b: float, x: float) -> float:
    """Regularised incomplete beta I_x(a, b)."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1) / (a + b + 2):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def t_p2(t: float, df: float) -> float:
    """Two-sided p of Student's t."""
    return betai(df / 2, 0.5, df / (df + t * t))


def t_ppf(q: float, df: float) -> float:
    """Quantile of Student's t for q in (0.5, 1), by bisection on the CDF."""
    lo, hi = 0.0, 1.0
    while 1 - 0.5 * t_p2(hi, df) < q:
        hi *= 2
    for _ in range(200):
        mid = (lo + hi) / 2
        if 1 - 0.5 * t_p2(mid, df) < q:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def _gammaincc(a: float, x: float) -> float:
    if x <= 0:
        return 1.0
    lead = -x + a * math.log(x) - math.lgamma(a)
    if x < a + 1:
        ap, s = a, 1.0 / a
        d = s
        for _ in range(2000):
            ap += 1
            d *= x / ap
            s += d
            if abs(d) < abs(s) * 1e-16:
                break
        return max(0.0, 1.0 - s * math.exp(lead))
    tiny = 1e-300
    b = x + 1 - a
    c, d = 1 / tiny, 1 / b
    h = d
    for i in range(1, 2000):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        d = 1 / (d if abs(d) > tiny else tiny)
        c = b + an / c
        c = c if abs(c) > tiny else tiny
        de = d * c
        h *= de
        if abs(de - 1) < 1e-16:
            break
    return math.exp(lead) * h


def chi2_sf(x: float, df: float) -> float:
    return _gammaincc(df / 2, x / 2)


# ---------------------------------------------------------------- effect sizes and pooling

def _double_zero(s: dict) -> bool:
    return (s["a"] == 0 and s["c"] == 0) or (s["a"] == s["n1"] and s["c"] == s["n2"])


def study_effect(measure: str, s: dict) -> tuple[float, float] | None:
    if measure in ("OR", "RR", "RD"):
        a, n1, c, n2 = (float(s[k]) for k in ("a", "n1", "c", "n2"))
        b, d = n1 - a, n2 - c
        if min(a, b, c, d) < 0:
            raise ValueError(f"{s.get('study', '?')}: events larger than the group size")
        if _double_zero(s):
            return None
        if 0 in (a, b, c, d):
            a, b, c, d = a + 0.5, b + 0.5, c + 0.5, d + 0.5
            n1, n2 = a + b, c + d
        if measure == "OR":
            return math.log(a * d / (b * c)), 1 / a + 1 / b + 1 / c + 1 / d
        if measure == "RR":
            return math.log((a / n1) / (c / n2)), 1 / a - 1 / n1 + 1 / c - 1 / n2
        return a / n1 - c / n2, a * b / n1 ** 3 + c * d / n2 ** 3
    if measure in ("MD", "SMD"):
        m1, sd1, n1, m2, sd2, n2 = (float(s[k]) for k in ("m1", "sd1", "n1", "m2", "sd2", "n2"))
        if measure == "MD":
            return m1 - m2, sd1 ** 2 / n1 + sd2 ** 2 / n2
        m = n1 + n2 - 2
        j = math.exp(math.lgamma(m / 2) - 0.5 * math.log(m / 2) - math.lgamma((m - 1) / 2))
        sp = math.sqrt(((n1 - 1) * sd1 ** 2 + (n2 - 1) * sd2 ** 2) / m)
        g = j * (m1 - m2) / sp
        return g, 1 / n1 + 1 / n2 + g * g / (2 * (n1 + n2))
    if measure.startswith("GEN"):
        return float(s["yi"]), float(s["vi"])
    raise ValueError(f"unknown measure {measure!r}")


def tau2_dl(y: list[float], v: list[float]) -> float:
    w = [1 / x for x in v]
    sw = sum(w)
    mu = sum(a * b for a, b in zip(w, y)) / sw
    q = sum(wi * (yi - mu) ** 2 for wi, yi in zip(w, y))
    return max(0.0, (q - (len(y) - 1)) / (sw - sum(x * x for x in w) / sw))


def tau2_reml(y: list[float], v: list[float], tol: float = 1e-12, maxit: int = 10000) -> float:
    """REML fixed point tau² = Σw²((y-μ)² - v)/Σw² + 1/Σw, truncated at 0, started at DL."""
    t = tau2_dl(y, v)
    for _ in range(maxit):
        w = [1 / (vi + t) for vi in v]
        sw = sum(w)
        mu = sum(a * b for a, b in zip(w, y)) / sw
        new = max(0.0, sum(wi * wi * ((yi - mu) ** 2 - vi) for wi, yi, vi in zip(w, y, v)) / sum(x * x for x in w) + 1 / sw)
        if abs(new - t) < tol * max(1.0, t):
            return new
        t = new
    raise ValueError("REML did not converge")


def pool(y: list[float], v: list[float], model: str, hksj: bool = False) -> dict:
    k = len(y)
    if k < 2:
        raise ValueError("pooling needs at least 2 studies")
    w = [1 / x for x in v]
    sw = sum(w)
    mu_ce = sum(a * b for a, b in zip(w, y)) / sw
    q = sum(wi * (yi - mu_ce) ** 2 for wi, yi in zip(w, y))
    df = k - 1
    if model == "CE-IV":
        tau2 = 0.0
        i2 = max(0.0, (q - df) / q) * 100 if q > 0 else 0.0
    elif model in ("RE-DL", "RE-REML"):
        tau2 = tau2_dl(y, v) if model == "RE-DL" else tau2_reml(y, v)
        s2 = df * sw / (sw ** 2 - sum(x * x for x in w))
        i2 = 100 * tau2 / (tau2 + s2)
    else:
        raise ValueError(f"model {model!r} needs pool_mh or is unknown")
    ws = [1 / (vi + tau2) for vi in v]
    sws = sum(ws)
    mu = sum(a * b for a, b in zip(ws, y)) / sws
    se = math.sqrt(1 / sws)
    if hksj:
        qh = sum(wi * (yi - mu) ** 2 for wi, yi in zip(ws, y)) / df
        se = math.sqrt(qh / sws)
        crit, p = t_ppf(0.975, df), t_p2(mu / se, df) if se > 0 else None   # se = 0: no test, no p
    else:
        crit, p = Z975, 2 * Z.cdf(-abs(mu / se)) if se > 0 else None
    out = {"k": k, "estimate": mu, "se": se, "ci": [mu - crit * se, mu + crit * se], "p": p, "tau2": tau2,
           "i2": i2, "q": q, "q_df": df, "q_p": chi2_sf(q, df), "pi": None}
    if model != "CE-IV" and k >= 3:
        h = t_ppf(0.975, k - 2) * math.sqrt(tau2 + se ** 2)
        out["pi"] = [mu - h, mu + h]
    return out


def pool_mh(studies: list[dict], measure: str) -> dict:
    keep = [s for s in studies if not _double_zero(s)]
    k = len(keep)
    if k < 2:
        raise ValueError("pooling needs at least 2 studies")
    if measure == "OR":
        r_ = s_ = pr = psqr = qs = 0.0
        for s in keep:
            a, n1, c, n2 = (float(s[x]) for x in ("a", "n1", "c", "n2"))
            b, d, n = n1 - a, n2 - c, n1 + n2
            ri, si = a * d / n, b * c / n
            pi_, qi = (a + d) / n, (b + c) / n
            r_, s_ = r_ + ri, s_ + si
            pr, psqr, qs = pr + pi_ * ri, psqr + pi_ * si + qi * ri, qs + qi * si
        if r_ <= 0 or s_ <= 0:
            raise ValueError("Mantel-Haenszel OR is not estimable (zero sums)")
        est = math.log(r_ / s_)
        var = pr / (2 * r_ * r_) + psqr / (2 * r_ * s_) + qs / (2 * s_ * s_)
    elif measure == "RR":
        r_ = s_ = vv = 0.0
        for s in keep:
            a, n1, c, n2 = (float(s[x]) for x in ("a", "n1", "c", "n2"))
            n = n1 + n2
            r_, s_ = r_ + a * n2 / n, s_ + c * n1 / n
            vv += (n1 * n2 * (a + c) - a * c * n) / (n * n)
        if r_ <= 0 or s_ <= 0:
            raise ValueError("Mantel-Haenszel RR is not estimable (zero sums)")
        est = math.log(r_ / s_)
        var = vv / (r_ * s_)
    else:
        raise ValueError("Mantel-Haenszel is for OR and RR only")
    se = math.sqrt(var)
    eff = [study_effect(measure, s) for s in keep]
    q = sum((yi - est) ** 2 / vi for yi, vi in eff)
    df = k - 1
    return {"k": k, "estimate": est, "se": se, "ci": [est - Z975 * se, est + Z975 * se],
            "p": 2 * Z.cdf(-abs(est / se)), "tau2": 0.0, "i2": max(0.0, (q - df) / q) * 100 if q > 0 else 0.0,
            "q": q, "q_df": df, "q_p": chi2_sf(q, df), "pi": None}


def egger(y: list[float], v: list[float]) -> dict:
    """Weighted regression of y on se (weights 1/v); the slope on se is Egger's intercept (plan D14)."""
    k = len(y)
    if k < 3:
        raise ValueError("Egger's test needs at least 3 studies")
    x = [math.sqrt(vi) for vi in v]
    w = [1 / vi for vi in v]
    sw, sx = sum(w), sum(a * b for a, b in zip(w, x))
    sxx = sum(a * b * b for a, b in zip(w, x))
    sy = sum(a * b for a, b in zip(w, y))
    sxy = sum(a * b * c for a, b, c in zip(w, x, y))
    det = sw * sxx - sx * sx
    b1 = (sw * sxy - sx * sy) / det
    b0 = (sxx * sy - sx * sxy) / det
    s2 = sum(wi * (yi - b0 - b1 * xi) ** 2 for wi, xi, yi in zip(w, x, y)) / (k - 2)
    se = math.sqrt(s2 * sw / det)
    t = b1 / se
    return {"intercept": b1, "se": se, "t": t, "p": t_p2(t, k - 2)}


def subgroup_test(fits: list[dict]) -> dict:
    w = [1 / f["se"] ** 2 for f in fits]
    mu = sum(a * f["estimate"] for a, f in zip(w, fits)) / sum(w)
    q = sum(a * (f["estimate"] - mu) ** 2 for a, f in zip(w, fits))
    df = len(fits) - 1
    return {"q": q, "df": df, "p": chi2_sf(q, df)}


# ---------------------------------------------------------------- register and data

def load_register(project: Path) -> list[dict]:
    path = analysis_plan.register_path(project)
    out = []
    for r in analysis_plan.parse_register(path.read_text(encoding="utf-8-sig")):
        typ = (r.get("type") or "").strip().casefold()
        if r["id"] == "A0" or typ == "counts":
            continue
        a = {"id": r["id"], "type": typ, "outcome": (r.get("outcome") or "").strip(),
             "timepoint": (r.get("timepoint") or "").strip(), "measure": (r.get("measure") or "").strip().upper(),
             "model": (r.get("model") or "RE-REML").strip().upper(),
             "hksj": (r.get("hksj") or "").strip().casefold() in ("yes", "y", "true", "có"),
             "experimental": (r.get("experimental") or "").strip(), "comparator": (r.get("comparator") or "").strip(),
             "factor": (r.get("factor") or "").strip()}
        if typ not in TYPES:
            raise ValueError(f"{a['id']}: Type {typ!r} must be one of {', '.join(TYPES)} (or counts for A0)")
        if a["measure"] not in MEASURES:
            raise ValueError(f"{a['id']}: Measure {a['measure']!r} must be one of {', '.join(MEASURES)}")
        if a["model"] not in MODELS:
            raise ValueError(f"{a['id']}: Model {a['model']!r} must be one of {', '.join(MODELS)}")
        if a["model"] == "CE-MH" and a["measure"] not in ("OR", "RR"):
            raise ValueError(f"{a['id']}: Mantel-Haenszel is for OR and RR only")
        if typ == "subgroup" and not a["factor"]:
            raise ValueError(f"{a['id']}: a subgroup analysis needs the Factor column (an extraction column)")
        if not a["experimental"] or (not a["measure"].startswith("GEN") and not a["comparator"]):
            raise ValueError(f"{a['id']}: Experimental and Comparator name the extraction 'group' values")
        out.append(a)
    return out


def _num(text, what: str) -> float:
    t = (text or "").strip().replace(",", ".")
    try:
        return float(t)
    except ValueError:
        raise ValueError(f"{what}: {text!r} is not a number") from None


def studies_for(rows: list[dict], a: dict) -> list[dict]:
    by: dict[str, dict[str, dict]] = {}
    for r in rows:
        if (r.get("outcome") or "").strip().casefold() == a["outcome"].casefold() and \
                (r.get("timepoint") or "").strip().casefold() == a["timepoint"].casefold():
            by.setdefault((r.get("study_id") or "").strip(), {})[(r.get("group") or "").strip().casefold()] = r
    out = []
    for sid, groups in by.items():
        e, c = groups.get(a["experimental"].casefold()), groups.get(a["comparator"].casefold())
        where = f"{a['id']} {sid}"
        s: dict = {"study": sid}
        if a["measure"].startswith("GEN"):
            if e is None:
                raise ValueError(f"{where}: no '{a['experimental']}' row with es and se")
            se = _num(e.get("se"), f"{where} se")
            if not se > 0:
                raise ValueError(f"{where}: se must be greater than 0 (got {se:g})")
            s.update(yi=_num(e.get("es"), f"{where} es"), vi=se ** 2)
            s["n"] = int(_num(e.get("n"), f"{where} n")) if (e.get("n") or "").strip() else 0
        else:
            if e is None or c is None:
                raise ValueError(f"{where}: needs rows for '{a['experimental']}' and '{a['comparator']}'")
            if a["measure"] in ("OR", "RR", "RD"):
                s.update(a=int(_num(e.get("events"), f"{where} events")), n1=int(_num(e.get("n"), f"{where} n")),
                         c=int(_num(c.get("events"), f"{where} events")), n2=int(_num(c.get("n"), f"{where} n")))
            else:
                s.update(m1=_num(e.get("mean"), f"{where} mean"), sd1=_num(e.get("sd"), f"{where} sd"),
                         n1=int(_num(e.get("n"), f"{where} n")), m2=_num(c.get("mean"), f"{where} mean"),
                         sd2=_num(c.get("sd"), f"{where} sd"), n2=int(_num(c.get("n"), f"{where} n")))
            if min(s["n1"], s["n2"]) < 1:
                raise ValueError(f"{where}: each group needs n of at least 1 (got {s['n1']} and {s['n2']})")
            if a["measure"] not in ("OR", "RR", "RD"):
                if not (s["sd1"] > 0 and s["sd2"] > 0):
                    raise ValueError(f"{where}: sd must be greater than 0 in both groups (got {s['sd1']:g} and {s['sd2']:g})")
                if a["measure"] == "SMD" and s["n1"] + s["n2"] <= 3:
                    raise ValueError(f"{where}: SMD needs n1 + n2 greater than 3 (got {s['n1'] + s['n2']})")
            s["n"] = s["n1"] + s["n2"]
        if a["factor"]:
            level = ((e or {}).get(a["factor"]) or "").strip()
            if not level:
                raise ValueError(f"{where}: no value in the factor column {a['factor']!r}")
            s["level"] = level
        out.append(s)
    return out


# ---------------------------------------------------------------- run

class Run:
    def __init__(self, project: Path):
        self.project = project
        self.log = resultlog.ResultLog(project, EXTRACTION, LOG_REL, "meta.py")
        self.dump: dict = {}
        self.plan: list[dict] = []
        self.inputs: list[dict] = []

    def out(self, a: dict, x: float) -> float:
        return math.exp(x) if a["measure"] in RATIO else x

    def fit(self, a: dict, kept: list) -> dict:
        if a["model"] == "CE-MH":
            return pool_mh([s for s, _ in kept], a["measure"])
        return pool([e[0] for _, e in kept], [e[1] for _, e in kept], a["model"], a["hksj"])

    def remember(self, key: str, a: dict, kept: list, f: dict) -> None:
        self.dump[key] = {"estimate": f["estimate"], "ci": f["ci"], "tau2": f["tau2"], "i2": f["i2"], "q": f["q"],
                          "pi": f["pi"], "k": f["k"]}
        self.plan.append({"key": key, "measure": a["measure"], "model": a["model"], "hksj": "yes" if a["hksj"] else "no"})
        for s, _ in kept:
            self.inputs.append({"key": key, **{c: s.get(c, "") for c in INPUT_COLS if c not in ("key", "vi")},
                                "vi": s.get("vi", "")})

    def add_pooled(self, a, status, f, kept, number, label) -> None:
        n = sum(s.get("n") or 0 for s, _ in kept)
        if f["p"] is None:
            self.log.log(f"{a['id']}: the pooled standard error is 0, so no p-value is given for '{label}'")
        self.log.add(a["id"], status, label, self.out(a, f["estimate"]), KIND[a["measure"]],
                     ci=[self.out(a, f["ci"][0]), self.out(a, f["ci"][1])], p=f["p"], n=n or None, count=f["k"],
                     number=number)

    def add_het(self, a, status, f, base: int, scope: str = "") -> None:
        if a["model"] in ("RE-REML", "RE-DL"):
            scale = ", log scale" if a["measure"] in RATIO else ""
            self.log.add(a["id"], status, f"tau² (between-study variance{scale}){scope}", f["tau2"], "tau2", number=base + 1)
        self.log.add(a["id"], status, f"I² (heterogeneity){scope}", f["i2"], "percent", number=base + 2)

    def pool_analysis(self, a: dict, status: str, kept: list) -> None:
        kind = KIND[a["measure"]]
        for j, (s, (yi, vi)) in enumerate(kept, start=11):
            se = math.sqrt(vi)
            self.log.add(a["id"], status, f"{s['study']} {a['measure']}", self.out(a, yi), kind,
                         ci=[self.out(a, yi - Z975 * se), self.out(a, yi + Z975 * se)], n=s.get("n") or None, number=j)
        k = len(kept)
        if k < 2:
            self.log.log(f"{a['id']} {a['outcome']}: {k} {'study' if k == 1 else 'studies'}; not pooled (narrative synthesis)")
            return
        f = self.fit(a, kept)
        self.remember(a["id"], a, kept, f)
        self.add_pooled(a, status, f, kept, 1, f"pooled {a['measure']} ({MODEL_TEXT[a['model']]}"
                                               f"{', HKSJ' if a['hksj'] else ''}, {k} studies)")
        self.add_het(a, status, f, 1)
        self.log.add(a["id"], status, "Q (heterogeneity)", f["q"], "other", p=f["q_p"], number=4)
        if f["pi"]:
            self.log.add(a["id"], status, "95% prediction interval", self.out(a, f["estimate"]), kind,
                         ci=[self.out(a, f["pi"][0]), self.out(a, f["pi"][1])], number=5)
        if k >= 10:
            eg = egger([e[0] for _, e in kept], [e[1] for _, e in kept])
            self.log.add(a["id"], status, "Egger's test intercept", eg["intercept"], "other", p=eg["p"], number=6)

    def subgroup_analysis(self, a: dict, status: str, kept: list) -> None:
        levels = sorted({s["level"] for s, _ in kept})
        if len(levels) > 98:
            raise ValueError(f"{a['id']}: too many subgroup levels")
        fits = []
        for j, lev in enumerate(levels, start=1):
            sub = [(s, e) for s, e in kept if s["level"] == lev]
            if len(sub) < 2:
                (s, (yi, vi)), = sub
                self.log.log(f"{a['id']} {a['factor']} = {lev}: 1 study; not pooled")
                fits.append({"estimate": yi, "se": math.sqrt(vi)})
                continue
            f = self.fit(a, sub)
            self.remember(f"{a['id']}|{lev}", a, sub, f)
            self.add_pooled(a, status, f, sub, 10 * j + 1,
                            f"pooled {a['measure']} in {a['factor']} = {lev} ({len(sub)} studies)")
            self.add_het(a, status, f, 10 * j + 1, f" in {a['factor']} = {lev}")
            fits.append(f)
        if len(fits) >= 2:
            t = subgroup_test(fits)
            self.log.add(a["id"], status, f"test for subgroup differences ({a['factor']}, Q between)", t["q"], "other",
                         p=t["p"], number=1)

    def loo_analysis(self, a: dict, status: str, kept: list) -> None:
        for j, (s, _) in enumerate(kept, start=1):
            rest = [x for x in kept if x[0] is not s]
            if len(rest) < 2:
                continue
            f = self.fit(a, rest)
            self.remember(f"{a['id']}|-{s['study']}", a, rest, f)
            self.add_pooled(a, status, f, rest, j, f"pooled {a['measure']} without {s['study']}")

    def write_side_files(self) -> None:
        base = self.project / "05_analysis" / "meta"
        base.mkdir(parents=True, exist_ok=True)
        with open(self.project / PY_REL, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(self.dump, indent=2) + "\n")
        write_csv(self.project / INPUT_REL, INPUT_COLS, self.inputs)
        write_csv(self.project / PLAN_REL, ["key", "measure", "model", "hksj"], self.plan)


def run(project: Path) -> tuple[int, list[str]]:
    if projectcfg.read_project_yaml(project).get("design") == "scoping-review":
        raise Refused("scoping reviews chart and summarise sources; they do not pool or rate risk of bias "
                      "(PRISMA-ScR). To pool, convert to a systematic review protocol and lock it again (G2).")
    analyses = load_register(project)
    if not analyses:
        raise ValueError("the analysis register has no pool, subgroup or leave-one-out row")
    rows = read_csv(project / EXTRACTION)
    if not rows:
        raise ValueError(f"no {EXTRACTION}: the consensus extraction is needed (extract_check.py)")
    dec_path = project / "decisions.md"
    deviations = analysis_plan.declared(dec_path.read_text(encoding="utf-8-sig") if dec_path.is_file() else "")["DEVIATION"]
    r = Run(project)
    for a in analyses:
        status = "deviation" if a["id"] in deviations else "prespecified"
        kept = []
        for s in studies_for(rows, a):
            e = study_effect(a["measure"], s)
            if e is None:
                r.log.log(f"{a['id']} {s['study']}: excluded from pooling (no events, or only events, in both groups)")
            else:
                kept.append((s, e))
        {"pool": r.pool_analysis, "subgroup": r.subgroup_analysis, "leave-one-out": r.loo_analysis}[a["type"]](a, status, kept)
    doc = r.log.save(DOC_REL)
    r.write_side_files()
    return resultlog.import_merged(project, doc)


# ---------------------------------------------------------------- figures and R

def forest_spec(project: Path) -> list[str]:
    led = derived.ledger_by_id(project)
    spec_path = project / FIG_REL
    spec = json.loads(spec_path.read_text(encoding="utf-8-sig")) if spec_path.is_file() else {"figures": []}
    figs = {f.get("id"): f for f in spec.get("figures", [])}
    order = [f.get("id") for f in spec.get("figures", [])]
    made = []
    for a in (x for x in load_register(project) if x["type"] == "pool"):
        pooled = f"R-{a['id']}-001"
        if pooled not in led:
            continue
        rows = [{"label": led[rid]["label"].rsplit(" ", 1)[0], "result": rid}
                for rid in sorted(led) if rid.startswith(f"R-{a['id']}-") and 11 <= int(rid[-3:]) < 900]
        fig = {"id": f"F-{a['id']}", "type": "forest", "title": f"{a['outcome']} ({a['timepoint']})",
               "null": 1 if a["measure"] in RATIO else 0, "log_scale": a["measure"] in RATIO,
               "x_label": f"{a['measure']} (95% CI)", "source": LOG_REL, "rows": rows, "pooled": pooled}
        if f"R-{a['id']}-005" in led:
            fig["prediction"] = f"R-{a['id']}-005"
        if fig["id"] not in figs:
            order.append(fig["id"])
        figs[fig["id"]] = fig
        made.append(fig["id"])
    spec["figures"] = [figs[i] for i in order]
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    with open(spec_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(spec, ensure_ascii=False, indent=2) + "\n")
    return made


R_TEXT = r'''# Generated by meta.py r-script: cross-check of the Python meta-analysis with the R package metafor.
# Run from the project folder: Rscript 05_analysis/meta/metafor.R   (meta.py r-check does this)
suppressPackageStartupMessages(library(metafor))
inp <- read.csv("05_analysis/meta/meta-input.csv", stringsAsFactors = FALSE)
plan <- read.csv("05_analysis/meta/meta-plan.csv", stringsAsFactors = FALSE)
num <- function(x) if (length(x) == 0 || is.null(x) || is.na(x[1])) "null" else formatC(x[1], digits = 15, format = "g")
fit <- function(d, measure, model, hksj) {
  method <- switch(model, "RE-REML" = "REML", "RE-DL" = "DL", "CE-IV" = "FE", "CE-MH" = "MH")
  if (method == "MH") return(rma.mh(ai = d$a, bi = d$n1 - d$a, ci = d$c, di = d$n2 - d$c, measure = measure,
                                    add = 1/2, to = "only0", drop00 = TRUE))
  if (measure %in% c("OR", "RR", "RD")) {
    es <- escalc(measure = measure, ai = d$a, bi = d$n1 - d$a, ci = d$c, di = d$n2 - d$c, add = 1/2,
                 to = "only0", drop00 = TRUE)
  } else if (measure %in% c("MD", "SMD")) {
    es <- escalc(measure = measure, m1i = d$m1, sd1i = d$sd1, n1i = d$n1, m2i = d$m2, sd2i = d$sd2, n2i = d$n2)
  } else {
    es <- data.frame(yi = d$yi, vi = d$vi)
  }
  rma(yi, vi, data = es, method = method, test = if (hksj == "yes") "knha" else "z",
      control = list(threshold = 1e-10, maxiter = 1000))
}
out <- character(0)
for (i in seq_len(nrow(plan))) {
  p <- plan[i, ]
  r <- fit(inp[inp$key == p$key, ], p$measure, p$model, p$hksj)
  tau2 <- if (is.null(r$tau2)) 0 else r$tau2
  # The prediction interval is computed by hand with qt(k - 2), matching the Python definition; it is not metafor's predict().
  pi <- if (p$model %in% c("RE-REML", "RE-DL") && r$k >= 3) r$b[1] + c(-1, 1) * qt(0.975, r$k - 2) * sqrt(tau2 + r$se^2) else c(NA, NA)
  out <- c(out, sprintf('  "%s": {"estimate": %s, "ci": [%s, %s], "tau2": %s, "i2": %s, "q": %s, "pi": [%s, %s], "k": %d}',
                        p$key, num(r$b[1]), num(r$ci.lb), num(r$ci.ub), num(tau2), num(r$I2), num(r$QE),
                        num(pi[1]), num(pi[2]), as.integer(r$k)))
}
eng <- sprintf('  "engine": "%s; metafor %s"', R.version.string, as.character(packageVersion("metafor")))
con <- file("05_analysis/meta/metafor-results.json", open = "wb")
writeLines(c("{", paste(c(eng, out), collapse = ",\n"), "}"), con, sep = "\n")
close(con)
'''


def write_r_script(project: Path) -> Path:
    if not (project / PLAN_REL).is_file():
        raise ValueError(f"no {PLAN_REL}: run meta.py run first")
    path = project / R_SCRIPT
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(R_TEXT)
    return path


def _version_key(p: Path) -> tuple:
    return tuple(int(x) for x in re.findall(r"\d+", p.name))


def rscript_candidates(project: Path, env=None, system=None, which=shutil.which) -> list[Path]:
    env = os.environ if env is None else env
    system = system or platform.system()
    exe = "Rscript.exe" if system == "Windows" else "Rscript"
    out: list[Path] = []
    cfg = projectcfg.get(project, "tools.rscript")
    if isinstance(cfg, str) and cfg:
        p = Path(cfg).expanduser()
        if not p.is_absolute() and len(p.parts) > 1:
            p = Path(project) / p            # a relative path is relative to the project folder
        out.append(p)
    w = which(exe) or which("Rscript")
    if w:
        out.append(Path(w))
    if env.get("R_HOME"):
        out.append(Path(env["R_HOME"]) / "bin" / exe)
    if system == "Windows":
        for var, sub in (("LOCALAPPDATA", ("Programs", "R")), ("ProgramFiles", ("R",))):
            if env.get(var):
                root = Path(env[var]).joinpath(*sub)
                if root.is_dir():
                    out += [d / "bin" / exe for d in sorted(root.glob("R-*"), key=_version_key, reverse=True)]
    elif system == "Darwin":
        out += [Path("/Library/Frameworks/R.framework/Resources/bin/Rscript"), Path("/opt/homebrew/bin/Rscript"),
                Path("/usr/local/bin/Rscript")]
    else:
        out += [Path("/usr/bin/Rscript"), Path("/usr/local/bin/Rscript")]
    return out


def find_rscript(project: Path, env=None, system=None, which=shutil.which, is_file=None) -> Path | None:
    is_file = is_file or (lambda p: p.is_file())
    return next((c for c in rscript_candidates(project, env, system, which) if is_file(c)), None)


def r_versions(rscript: Path) -> tuple[str, str | None]:
    code = ("cat(paste(R.version$major, R.version$minor, sep = '.'), "
            "if (requireNamespace('metafor', quietly = TRUE)) as.character(packageVersion('metafor')) else 'none')")
    r = subprocess.run([str(rscript), "-e", code], capture_output=True, text=True, timeout=120)
    parts = r.stdout.split()
    if r.returncode != 0 or len(parts) != 2:
        raise RuntimeError(f"{rscript} did not run: {r.stderr.strip()[:200]}")
    return parts[0], (None if parts[1] == "none" else parts[1])


def install_hint(system: str) -> str:
    get_r = {"Windows": "install R from https://cran.r-project.org/bin/windows/base/",
             "Darwin": "install R from https://cran.r-project.org/bin/macosx/ (or with Homebrew: brew install r)",
             }.get(system, "install R with your package manager (for example: sudo apt install r-base) or from "
                           "https://cran.r-project.org/")
    return (f"R is optional; every result is computed in Python. To cross-check with metafor: {get_r}, then in R run "
            'install.packages("metafor"). If R is installed somewhere unusual, set project.yaml → tools.rscript '
            "to the full path of Rscript. This tool never installs software.")


STORE_HINT = ("This Python comes from the Microsoft Store: R started from it may not see your R user library. In R "
              'run Sys.getenv("R_LIBS_USER") and set the environment variable R_LIBS_USER to that folder before '
              "running meta.py, or set project.yaml → tools.rscript to the full path of Rscript, or use a Python "
              "installed from python.org.")


def ms_store_python(executable: str | None = None, system: str | None = None, base: tuple | list | None = None) -> bool:
    """True for the Microsoft Store Python on Windows (it runs from a WindowsApps folder in an app container).
    A venv made from it runs from the venv, so the base interpreter and prefix are checked too."""
    if (system or platform.system()) != "Windows":
        return False
    if base is None:
        base = (getattr(sys, "_base_executable", None), getattr(sys, "base_prefix", None))
    paths = (executable or sys.executable, *base)
    return any("\\windowsapps\\" in str(p).replace("/", "\\").lower() + "\\" for p in paths if p)


def _close(a, b) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= 1e-4 * max(abs(a), abs(b)) or abs(a - b) <= 1e-8


def compare(py: dict, rr: dict) -> list[tuple[str, str, str]]:
    found = []
    for key, p in py.items():
        r = rr.get(key)
        if r is None:
            found.append(("warn", f"{R_OUT}:1", f"{key}: missing from the metafor results"))
            continue
        pairs = [("estimate", p["estimate"], r.get("estimate")), ("ci lower", p["ci"][0], (r.get("ci") or [None, None])[0]),
                 ("ci upper", p["ci"][1], (r.get("ci") or [None, None])[1]), ("tau2", p["tau2"], r.get("tau2")),
                 ("i2", p["i2"], r.get("i2")), ("q", p["q"], r.get("q"))]
        rpi = r.get("pi") or [None, None]
        ppi = p.get("pi") or [None, None]
        pairs += [("pi lower", ppi[0], rpi[0]), ("pi upper", ppi[1], rpi[1])]
        for name, a, b in pairs:
            if not _close(a, b):
                found.append(("warn", f"{PY_REL}:1", f"{key} {name}: Python {a!r}, metafor {b!r}"))
    return found


def r_check(project: Path) -> tuple[list, str]:
    rs = find_rscript(project)
    if rs is None:
        raise FileNotFoundError("R not found. " + install_hint(platform.system()))
    rv, mf = r_versions(rs)
    if mf is None:
        raise FileNotFoundError(f"metafor not installed for R {rv}. " + install_hint(platform.system()))
    if not (project / PY_REL).is_file():
        raise ValueError(f"no {PY_REL}: run meta.py run first")
    write_r_script(project)
    r = subprocess.run([str(rs), R_SCRIPT], cwd=project, capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        raise RuntimeError(f"metafor.R failed: {r.stderr.strip()[:500]}")
    rr = json.loads((project / R_OUT).read_text(encoding="utf-8"))
    py = json.loads((project / PY_REL).read_text(encoding="utf-8"))
    return compare(py, rr), f"R {rv}; metafor {mf}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("cmd", choices=["run", "forest-spec", "r-script", "r-status", "r-check"])
    a = ap.parse_args(argv)
    project = Path(a.project)
    if not (project / "project.yaml").is_file():
        print(f"meta: {a.project} is not a project folder (no project.yaml)", file=sys.stderr)
        return 2
    try:
        if a.cmd == "run":
            n, bad = run(project)
            for x in bad:
                print(x)
            if bad:
                return 1
            print(f"meta: {n} results written to {LOG_REL} and merged into the results ledger")
            return 0
        if a.cmd == "forest-spec":
            made = forest_spec(project)
            print(f"meta: forest entries {', '.join(made) or 'none'} in {FIG_REL}")
            return 0
        if a.cmd == "r-script":
            print(f"meta: wrote {write_r_script(project).relative_to(project).as_posix()}")
            return 0
        if a.cmd == "r-status":
            rs = find_rscript(project)
            if rs is None:
                print("r-status: R not found. " + install_hint(platform.system())
                      + (" " + STORE_HINT if ms_store_python() else ""), file=sys.stderr)
                return 2
            rv, mf = r_versions(rs)
            if mf is None:
                print(f"r-status: Rscript {rs} (R {rv}); metafor not installed. " + install_hint(platform.system())
                      + (" " + STORE_HINT if ms_store_python() else ""), file=sys.stderr)
                return 2
            print(f"r-status: Rscript {rs} (R {rv}); metafor {mf}; r-check is available")
            return 0
        found, engine = r_check(project)
        for sev, loc, msg in found:
            print(f"E-META {sev} {loc}: {msg}")
        print(f"r-check: {len(found)} mismatches ({engine}; Python stays the reference for the ledger)")
        return 0
    except Refused as e:
        print(f"meta: {e}")
        return 1
    except results_ledger.LockedError as e:
        print(f"meta: {e}", file=sys.stderr)
        return 1
    except results_ledger.RelabelError as e:
        print(f"{e}\nmeta: labels changed; ledger not written", file=sys.stderr)
        return 1
    except FileNotFoundError as e:
        print(f"meta: {e}", file=sys.stderr)
        return 2
    except (OSError, ValueError, KeyError, RuntimeError, csv.Error, subprocess.TimeoutExpired,
            ZeroDivisionError) as e:
        print(f"meta: {type(e).__name__}: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
