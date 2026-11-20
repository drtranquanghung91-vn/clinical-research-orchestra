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
from phi_scan import STRONG, WEAK  # noqa: E402

VALUE_RX = [rx for _, rx in STRONG] + [rx for label, rx in WEAK if label in ("phone number", "email")]

PSEUDO = ["ho ten", "ho va ten", "ten benh nhan", "name", "patient", "ma bn", "ma benh an", "so ho so", "mrn", "pid",
          "nguoi benh", "benh nhan", "ten bn", "ma nguoi benh", "ma ho so", "so vao vien", "so luu tru"]
YEAR = ["ngay sinh", "dob", "date of birth", "birth"]
DROP = ["cccd", "cmnd", "bhyt", "dien thoai", "sdt", "phone", "email", "dia chi", "address",
        "e mail", "mail", "dt", "di dong", "mobile", "tel", "lien he", "noi sinh", "que quan"]
YEAR_RX = re.compile(r"(19|20)\d{2}")


def _plain(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.replace("đ", "d").replace("Đ", "D"))
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", s).split())


def _has(h: str, words: list[str]) -> bool:
    return any(re.search(rf"\b{re.escape(w)}\b", h) for w in words)


def _unique(header: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    out = []
    for n, c in enumerate(header, start=1):
        name = c if c.strip() else f"col_{n}"
        seen[name] = seen.get(name, 0) + 1
        out.append(name if seen[name] == 1 else f"{name}_{seen[name]}")
    return out


def _classify(header: list[str], rows: list[list[str]]) -> list[str]:
    acts = []
    for i, col in enumerate(header):
        h = _plain(col)
        if _has(h, DROP):
            acts.append("drop")
        elif _has(h, YEAR):
            acts.append("year-only")
        elif _has(h, PSEUDO):
            acts.append("pseudonymise")
        else:
            vals = [r[i] for r in rows if i < len(r) and r[i].strip()][:200]
            hits = sum(1 for v in vals if any(rx.search(v) for rx in VALUE_RX))
            acts.append("drop" if vals and hits / len(vals) >= 0.3 else "keep")
    return acts


def classify_columns(header: list[str], rows: list[list[str]]) -> dict[str, str]:
    return dict(zip(_unique(header), _classify(header, rows)))


def _read(src: Path) -> list[list[str]]:
    if src.suffix.lower() in (".xlsx", ".xlsm"):
        try:
            import openpyxl
        except ImportError:
            raise SystemExit("deidentify: reading .xlsx needs openpyxl (pip install openpyxl), or save as CSV")
        wb = openpyxl.load_workbook(src, read_only=True, data_only=True)
        try:
            ws = wb.active
            if len(wb.sheetnames) > 1:
                print(f"deidentify: only the first sheet '{ws.title}' was read; "
                      f"{len(wb.sheetnames) - 1} other sheet(s) ignored", file=sys.stderr)
            return [["" if v is None else str(v) for v in row] for row in ws.iter_rows(values_only=True)]
        finally:
            wb.close()
    with src.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.reader(fh))


def deidentify_csv(src: Path, out_dir: Path) -> dict:
    src, out_dir = Path(src), Path(out_dir)
    table = _read(src)
    if not table:
        raise SystemExit("deidentify: empty file")
    header, rows = _unique(table[0]), table[1:]
    acts_l = _classify(header, rows)
    acts = dict(zip(header, acts_l))
    keep_idx = [i for i, a in enumerate(acts_l) if a != "drop"]
    key_idx = [i for i, a in enumerate(acts_l) if a in ("pseudonymise", "drop")]
    deid_rows, key_rows = [], []
    for n, r in enumerate(rows, start=1):
        pid = f"P{n:04d}"
        out = []
        for i in keep_idx:
            v = r[i] if i < len(r) else ""
            if acts_l[i] == "pseudonymise":
                v = pid
            elif acts_l[i] == "year-only":
                m = YEAR_RX.search(v)
                v = m.group(0) if m else ""
            out.append(v)
        deid_rows.append(out)
        key_rows.append([pid] + [r[i] if i < len(r) else "" for i in key_idx])
    out_dir.mkdir(parents=True, exist_ok=True)
    deid, key = out_dir / f"{src.stem}.deid.csv", out_dir / f"{src.stem}.key.csv"
    with deid.open("w", encoding="utf-8-sig", newline="") as fh:
        csv.writer(fh).writerows([[header[i] for i in keep_idx]] + deid_rows)
    with key.open("w", encoding="utf-8-sig", newline="") as fh:
        csv.writer(fh).writerows([["pseudonym"] + [header[i] for i in key_idx]] + key_rows)
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
