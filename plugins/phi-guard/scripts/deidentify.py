#!/usr/bin/env python3
"""De-identify a CSV/XLSX file locally. Prints only column names and actions, never cell values.

Outputs next to --out (default: the source folder):
  <stem>.deid.csv  data for analysis with AI tools
  <stem>.key.csv   pseudonym -> original identifiers; keep it local, never upload it
  python deidentify.py data.csv [--out DIR]
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from phi_scan import STRONG  # noqa: E402

PSEUDO = ["ho ten", "ho va ten", "ten benh nhan", "name", "patient", "ma bn", "ma benh an", "so ho so", "mrn", "pid"]
YEAR = ["ngay sinh", "dob", "date of birth", "birth"]
DROP = ["cccd", "cmnd", "bhyt", "dien thoai", "sdt", "phone", "email", "dia chi", "address"]
YEAR_RX = re.compile(r"(19|20)\d{2}")


def _plain(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.replace("đ", "d").replace("Đ", "D"))
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", s).split())


def _has(h: str, words: list[str]) -> bool:
    return any(re.search(rf"\b{re.escape(w)}\b", h) for w in words)


def classify_columns(header: list[str], rows: list[list[str]]) -> dict[str, str]:
    acts: dict[str, str] = {}
    for i, col in enumerate(header):
        h = _plain(col)
        if _has(h, DROP):
            acts[col] = "drop"
        elif _has(h, YEAR):
            acts[col] = "year-only"
        elif _has(h, PSEUDO):
            acts[col] = "pseudonymise"
        else:
            vals = [r[i] for r in rows if i < len(r) and r[i].strip()][:200]
            hits = sum(1 for v in vals if any(rx.search(v) for _, rx in STRONG))
            acts[col] = "drop" if vals and hits / len(vals) >= 0.3 else "keep"
    return acts


def _read(src: Path) -> list[list[str]]:
    if src.suffix.lower() in (".xlsx", ".xlsm"):
        try:
            import openpyxl
        except ImportError:
            raise SystemExit("deidentify: reading .xlsx needs openpyxl (pip install openpyxl), or save as CSV")
        ws = openpyxl.load_workbook(src, read_only=True, data_only=True).active
        return [["" if v is None else str(v) for v in row] for row in ws.iter_rows(values_only=True)]
    with src.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.reader(fh))


def deidentify_csv(src: Path, out_dir: Path) -> dict:
    src, out_dir = Path(src), Path(out_dir)
    table = _read(src)
    header, rows = table[0], table[1:]
    acts = classify_columns(header, rows)
    keep_idx = [i for i, c in enumerate(header) if acts[c] != "drop"]
    key_cols = [c for c in header if acts[c] in ("pseudonymise", "drop")]
    deid_rows, key_rows = [], []
    for n, r in enumerate(rows, start=1):
        pid = f"P{n:04d}"
        out = []
        for i in keep_idx:
            v = r[i] if i < len(r) else ""
            a = acts[header[i]]
            if a == "pseudonymise":
                v = pid
            elif a == "year-only":
                m = YEAR_RX.search(v)
                v = m.group(0) if m else ""
            out.append(v)
        deid_rows.append(out)
        key_rows.append([pid] + [r[header.index(c)] if header.index(c) < len(r) else "" for c in key_cols])
    out_dir.mkdir(parents=True, exist_ok=True)
    deid, key = out_dir / f"{src.stem}.deid.csv", out_dir / f"{src.stem}.key.csv"
    with deid.open("w", encoding="utf-8-sig", newline="") as fh:
        csv.writer(fh).writerows([[header[i] for i in keep_idx]] + deid_rows)
    with key.open("w", encoding="utf-8-sig", newline="") as fh:
        csv.writer(fh).writerows([["pseudonym"] + key_cols] + key_rows)
    return {"deid_file": str(deid), "key_file": str(key), "columns": acts, "rows": len(rows)}


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    src = Path(a.file)
    print(json.dumps(deidentify_csv(src, Path(a.out) if a.out else src.parent), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
