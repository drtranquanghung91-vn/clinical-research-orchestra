#!/usr/bin/env python3
"""Case facts → results ledger (A0, status observed), so drafts cite {{R-A0-NNN}} and E-NUM works.

  python case_facts.py <project> [--accept-relabel]

Reads 01_case/facts.csv (id,label,value,unit,day,source), one row per reportable value; `day` is relative
(0, +3, -14), never a date. Kind from the unit: % → percent; an empty/count unit with an integer → n; else
measure, printed with the decimals written in the CSV. Writes 05_analysis/output/case-facts-log.txt and
case-facts.json and merges them into ledgers/results-ledger.json as R-A0-001… in row order.
Exit codes: 0 = written (or unchanged); 1 = invalid rows (listed, nothing written), the ledger is locked by G3,
or a label change refused; 2 = usage error, missing project/file or missing column.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crolib import resultlog  # noqa: E402
import results_ledger  # noqa: E402

FACTS = "01_case/facts.csv"
LOG_REL = "05_analysis/output/case-facts-log.txt"
DOC_REL = "05_analysis/output/case-facts.json"
COLUMNS = ("id", "label", "value", "unit", "day", "source")
COUNT_UNITS = {"", "n", "cases", "case", "ca", "lần", "times", "episodes", "đợt"}
NUMBER = re.compile(r"-?\d+(?:[.,]\d+)?")
DAY = re.compile(r"[+-]?\d{1,5}")
FACT_ID = re.compile(r"[A-Za-z][\w-]*")


def _decimals(text: str) -> int:
    t = text.strip().replace(",", ".")
    return len(t.split(".")[1]) if "." in t else 0


def kind_for(unit: str, text: str) -> tuple[str, int | None]:
    u = unit.strip().casefold()
    if u in ("%", "percent", "phần trăm"):
        return "percent", _decimals(text)
    if u in COUNT_UNITS and _decimals(text) == 0:
        return "n", None
    return "measure", _decimals(text)


def read_rows(project: Path) -> tuple[list[dict], list[str]]:
    path = project / FACTS
    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{FACTS} lacks column(s) {', '.join(missing)} (needs {','.join(COLUMNS)})")
        rows = list(reader)
    probs, seen = [], set()
    if not rows:
        probs.append(f"{FACTS}: no fact rows (needs at least one; an empty file would drop the recorded A0 facts)")
    for i, r in enumerate(rows, start=2):
        fid = (r.get("id") or "").strip() or f"line {i}"
        if None in r or any(v is None for v in r.values()):
            got = len(r.get(None) or []) + sum(v is not None for k, v in r.items() if k is not None)
            probs.append(f"{fid}: row has {got} fields, expected {len(COLUMNS)}; quote a decimal comma, "
                         f'e.g. "1,25" ({FACTS}:{i})')
            continue
        if not FACT_ID.fullmatch((r.get("id") or "").strip()):
            probs.append(f"{fid}: id must start with a letter and use letters, digits, _ or - ({FACTS}:{i})")
        if fid in seen:
            probs.append(f"{fid}: duplicate id ({FACTS}:{i})")
        seen.add(fid)
        if not (r.get("label") or "").strip():
            probs.append(f"{fid}: label is empty ({FACTS}:{i})")
        if not NUMBER.fullmatch((r.get("value") or "").strip()):
            probs.append(f"{fid}: value must be a number, got {r.get('value')!r} ({FACTS}:{i})")
        day = (r.get("day") or "").strip()
        if day and not DAY.fullmatch(day):
            probs.append(f"{fid}: day must be relative (0, +3, -14), never a date; got {day!r} ({FACTS}:{i})")
    return rows, probs


def build(project: Path, rows: list[dict]) -> tuple[Path, list[str]]:
    log = resultlog.ResultLog(project, FACTS, LOG_REL, "case_facts.py")
    mapping = []
    for r in rows:
        fid, text, unit = r["id"].strip(), r["value"].strip(), (r.get("unit") or "").strip()
        kind, dec = kind_for(unit, text)
        day = (r.get("day") or "").strip()
        extra = {"day": int(day)} if day else {}
        rid = log.add("A0", "observed", f"{r['label'].strip()} [{fid}]", float(text.replace(",", ".")), kind,
                      unit=unit, decimals=dec, extra=extra)
        mapping.append(f"{fid} → {rid} ({kind}{'' if dec is None else f', {dec} dp'})")
    return log.save(DOC_REL), mapping


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--accept-relabel", action="store_true")
    a = ap.parse_args(argv)
    project = Path(a.project)
    if not (project / "ledgers").is_dir():
        print(f"case_facts: {a.project} is not a project folder (no ledgers/)", file=sys.stderr)
        return 2
    try:
        rows, probs = read_rows(project)
    except (OSError, ValueError) as e:
        print(f"case_facts: {e}", file=sys.stderr)
        return 2
    if probs:
        for x in probs:
            print(x)
        print(f"case_facts: {len(probs)} problems; nothing written")
        return 1
    snap = {rel: ((project / rel).read_bytes() if (project / rel).is_file() else None) for rel in (LOG_REL, DOC_REL)}

    def restore() -> None:  # a refused run leaves the log and results document as they were
        for rel, data in snap.items():
            f = project / rel
            if data is None:
                f.unlink(missing_ok=True)
            else:
                f.write_bytes(data)

    try:
        doc, mapping = build(project, rows)
        n, bad = resultlog.import_merged(project, doc, a.accept_relabel)
    except results_ledger.LockedError as e:
        restore()
        print(f"case_facts: {e}", file=sys.stderr)
        return 1
    except results_ledger.RelabelError as e:
        restore()
        print(str(e), file=sys.stderr)
        print("case_facts: labels changed; ledger not written (re-run with --accept-relabel)", file=sys.stderr)
        return 1
    except (OSError, ValueError) as e:
        restore()
        print(f"case_facts: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    if bad:
        restore()
        for x in bad:
            print(x)
        return 1
    for line in mapping:
        print(line)
    print(f"case_facts: {n} facts in the results ledger (A0, observed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
