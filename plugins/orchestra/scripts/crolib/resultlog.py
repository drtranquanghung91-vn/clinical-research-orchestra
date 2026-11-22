"""Stdlib twin of crostats.Recorder (P2 log format) for P5 tools: numbered results R-A<n>-NNN, one log line each,
saved as a log file plus a results document that `results_ledger.py import --merge` reads (plan D1, D6)."""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
import platform
import re
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from . import numfmt

STATUSES = ("prespecified", "posthoc", "deviation", "observed")


def num_str(v) -> str:
    """ints as is; floats with 10 significant digits, half up, positional (crostats._num_str)."""
    if isinstance(v, int) and not isinstance(v, bool):
        return str(v)
    d = Decimal(repr(float(v)))
    if d == 0:
        return "0"
    q = d.quantize(Decimal(1).scaleb(min(d.adjusted() - 9, 0)), rounding=ROUND_HALF_UP)
    s = format(q, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _finite(x):
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


class ResultLog:
    def __init__(self, project, data_file: str, log_rel: str, engine: str):
        self.project = Path(project)
        self.data_file = data_file
        self.log_rel = log_rel
        self.engine = engine
        self.lines: list[str] = []
        self.results: list[dict] = []
        self._next: dict[str, int] = {}
        self._used: set[str] = set()

    def log(self, text) -> int:
        parts = str(text).splitlines() or [""]
        first = len(self.lines) + 1
        self.lines.extend(parts)
        return first

    def add(self, analysis_id, status, label, value, kind, *, ci=None, p=None, n=None, count=None, unit="",
            number=None, decimals=None, extra=None) -> str:
        if status not in STATUSES:
            raise ValueError(f"status '{status}' not in {STATUSES}")
        if not (isinstance(analysis_id, str) and re.fullmatch(r"A\d+", analysis_id)):
            raise ValueError(f"analysis_id '{analysis_id}' must be A<n>")
        if status == "observed" and analysis_id != "A0":
            raise ValueError("status 'observed' is only for A0 (recorded data, not an analysis)")
        if kind not in numfmt.KINDS:
            raise ValueError(f"kind '{kind}' not in {sorted(numfmt.KINDS)}")
        label = " ".join(str(label).split())
        if not label:
            raise ValueError("label is empty")
        v = _finite(value)
        if v is None:
            raise ValueError(f"{label}: value {value!r} is not a finite number")
        if kind in ("n", "absolute") and v == int(v):
            v = int(v)
        k = number if number is not None else self._next.get(analysis_id, 0) + 1
        if not (isinstance(k, int) and 1 <= k <= 999):
            raise ValueError(f"{label}: result number {k!r} must be 1-999")
        rid = f"R-{analysis_id}-{k:03d}"
        if rid in self._used:
            raise ValueError(f"{rid} is already used")
        rec = {"id": rid, "analysis_id": analysis_id, "status": status, "label": label, "value": v}
        line = f"{rid} {label}: value={num_str(v)}"
        if ci is not None:
            lo, hi = _finite(ci[0]), _finite(ci[1])
            if lo is None or hi is None or lo > hi:
                raise ValueError(f"{label}: ci {ci!r} must be finite [lo, hi] with lo <= hi")
            rec["ci"] = [lo, hi]
            line += f" ci={num_str(lo)},{num_str(hi)}"
        if p is not None:
            pv = _finite(p)
            if pv is None or not 0 <= pv <= 1:
                raise ValueError(f"{label}: p {p!r} must be between 0 and 1")
            rec["p"] = pv
            line += f" p={num_str(pv)}"
        if n is not None:
            rec["n"] = int(n)
            line += f" n={int(n)}"
        if count is not None:
            rec["count"] = int(count)
            line += f" count={int(count)}"
        rec["unit"] = str(unit)
        rec["kind"] = kind
        if decimals is not None:
            rec["decimals"] = int(decimals)
        for key, val in (extra or {}).items():
            rec[key] = val
        lineno = self.log(line)
        rec.update({"source_file": self.log_rel, "locator": f"line {lineno}", "raw": line})
        self._used.add(rid)
        self._next[analysis_id] = max(k, self._next.get(analysis_id, 0))
        self.results.append(rec)
        return rid

    def save(self, results_rel: str) -> Path:
        log_path = self.project / self.log_rel
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(self.lines) + "\n")
        data = self.project / self.data_file
        doc = {"engine": f"{self.engine}; Python {platform.python_version()}", "data_file": self.data_file,
               "data_sha256": hashlib.sha256(data.read_bytes()).hexdigest() if data.is_file() else "",
               "run_at": _dt.datetime.now().isoformat(timespec="seconds"), "results": self.results, "tables": []}
        path = self.project / results_rel
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(doc, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
        return path


def import_merged(project, doc_path, accept_relabel: bool = False) -> tuple[int, list[str]]:
    import results_ledger  # scripts folder is on sys.path for every caller
    return results_ledger.import_results(Path(project), Path(doc_path), accept_relabel=accept_relabel, merge=True)
