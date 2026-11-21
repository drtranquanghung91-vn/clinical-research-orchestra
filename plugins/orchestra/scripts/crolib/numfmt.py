"""Number formatting and matching shared by render_results.py, check_numbers.py and results_ledger.py.

Standard library only. Rounding is half up (Decimal), not Python's round-half-even.
"""
from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal

PRECISION = {"n": 0, "count": 0, "percent": 1, "mean": 1, "sd": 1, "median": 1, "iqr": 1,
             "md": 2, "or": 2, "rr": 2, "hr": 2, "rd": 2, "beta": 2, "auc": 3, "p": 3, "other": 2}
KINDS = frozenset(k for k in PRECISION if k != "count")
EN_DASH = "–"
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
