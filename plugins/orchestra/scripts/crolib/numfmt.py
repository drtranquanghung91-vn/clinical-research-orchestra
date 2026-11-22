"""Number formatting and matching shared by render_results.py, check_numbers.py and results_ledger.py.

Standard library only. Rounding is half up (Decimal), not Python's round-half-even.
"""
from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal

PRECISION = {"n": 0, "count": 0, "percent": 1, "mean": 1, "sd": 1, "median": 1, "iqr": 1,
             "md": 2, "or": 2, "rr": 2, "hr": 2, "rd": 2, "beta": 2, "auc": 3, "p": 3, "other": 2,
             "smd": 2, "tau2": 3, "absolute": 0, "measure": 1}
KINDS = frozenset(k for k in PRECISION if k != "count")
EN_DASH = "–"
_TOKEN = {
    "en": re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?%?(?!\w)"),
    "vi": re.compile(r"(?<![\w,])-?\d+(?:,\d+)?%?(?!\w)"),
    "any": re.compile(r"(?<![\w.,])-?(?:\d+(?:[.,]\d+)?|[.,]\d+)%?(?!\w)"),
}


def round_half_up(x: float, decimals: int) -> Decimal:
    return Decimal(str(x)).quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)


def fmt(x: float, decimals: int, lang: str = "en") -> str:
    s = format(round_half_up(x, decimals), "f")
    if s.startswith("-") and not s.strip("-0."):
        s = s[1:]  # never print negative zero
    return s.replace(".", ",") if lang == "vi" else s


def fmt_p(p: float, lang: str = "en") -> str:
    return "< " + fmt(0.001, 3, lang) if p < 0.001 else fmt(p, 3, lang)


def fmt_range(lo: float, hi: float, decimals: int, lang: str = "en") -> str:
    a, b = fmt(lo, decimals, lang), fmt(hi, decimals, lang)
    if a.startswith("-") or b.startswith("-"):  # an en dash next to a minus sign is unreadable
        return f"{a}{' đến ' if lang == 'vi' else ' to '}{b}"
    return f"{a}{EN_DASH}{b}"


def _precision(kind: str) -> int:
    return PRECISION.get(kind, 2)


def _decimals(rec: dict, kind: str) -> int:
    """A record's own `decimals` (int 0-4, case facts) wins over the kind's precision."""
    d = rec.get("decimals")
    if isinstance(d, int) and not isinstance(d, bool) and 0 <= d <= 4:
        return d
    return _precision(kind)


def render(rec: dict, part: str, lang: str) -> str:
    kind = rec.get("kind") or "other"
    d = _decimals(rec, kind)
    if part == "value":
        if kind == "p":
            return fmt_p(rec["value"], lang)
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
    if part == "count":
        if rec.get("count") is None:
            raise KeyError("count")
        return fmt(rec["count"], 0, lang)
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
