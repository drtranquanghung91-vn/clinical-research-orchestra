#!/usr/bin/env python3
"""De-identify a CSV/XLSX file locally. Prints only column names, actions and counts, never cell values.

Outputs next to --out (default: the source folder):
  <stem>.deid.csv  data for analysis with AI tools
  <stem>.key.csv   pseudonym -> original identifiers; keep it local, never upload it
  python deidentify.py data.csv [--out DIR]
Exit codes: 0 = done, 2 = missing, unreadable or empty input.
The header row is the first of the first 10 rows with >= 2 recognised column names; rows above it
(titles) are counted, not copied. Each patient (same identifier values) gets one pseudonym P0001...
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
from phi_scan import STRONG, VI_LOWER, VI_UPPER, WEAK  # noqa: E402

VALUE_RX = [rx for _, rx in STRONG] + [rx for label, rx in WEAK if label in ("phone number", "email")]
NAME_VALUE = re.compile(rf"[{VI_UPPER}][{VI_UPPER}{VI_LOWER}]*(?:\s+[{VI_UPPER}][{VI_UPPER}{VI_LOWER}]*){{1,4}}")
NAME_SHARE = 0.3
HEADER_SCAN_ROWS = 10

# Substring (whole-word) lists: multi-word phrases and unambiguous words.
PSEUDO = ["ho ten", "ho va ten", "ten benh nhan", "name", "patient", "ma bn", "ma benh an", "so ho so", "mrn", "pid",
          "nguoi benh", "benh nhan", "ten bn", "ma nguoi benh", "ma ho so", "so vao vien", "so luu tru", "so benh an"]
YEAR = ["ngay sinh", "dob", "date of birth", "birth"]
DROP = ["cccd", "cmnd", "bhyt", "dien thoai", "sdt", "so dt", "phone", "email", "dia chi", "address",
        "e mail", "mail", "di dong", "mobile", "tel", "lien he", "noi sinh", "que quan", "bhxh"]
# Exact lists: the whole normalised header must equal one of these (so "Ho khan" or "Thoi gian DT" are not caught).
EXACT_PSEUDO = {"ho", "ten", "ho dem", "ten dem", "ho va ten dem", "first name", "last name", "surname",
                "given name", "full name"}
EXACT_DROP = {"bhxh", "so bhxh", "so the", "ma the", "noi o", "cu tru", "noi cu tru", "dt"}
# Clinical variables that mention the patient but are not identifiers: never pseudonymised by header or name shape.
CLINICAL = ["tuoi", "gioi", "nhom", "so luong", "can nang", "chieu cao", "chan doan", "so benh nhan",
            "so nguoi benh", "age", "sex", "gender", "group", "weight", "height", "diagnosis", "number of"]
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


def _header_action(h: str) -> str | None:
    if h in EXACT_DROP or _has(h, DROP):
        return "drop"
    if _has(h, YEAR):
        return "year-only"
    if _has(h, CLINICAL):
        return "clinical"
    if h in EXACT_PSEUDO or _has(h, PSEUDO):
        return "pseudonymise"
    return None


def _is_name(v: str) -> bool:
    return NAME_VALUE.fullmatch(unicodedata.normalize("NFC", v.strip())) is not None


def _is_suspect(v: str) -> bool:
    return _is_name(v) or any(rx.search(v) for rx in VALUE_RX)


def _classify(header: list[str], rows: list[list[str]]) -> list[str]:
    acts = []
    for i, col in enumerate(header):
        act = _header_action(_plain(col))
        if act in ("drop", "year-only", "pseudonymise"):
            acts.append(act)
            continue
        vals = [r[i] for r in rows if i < len(r) and r[i].strip()][:200]
        if vals and sum(1 for v in vals if any(rx.search(v) for rx in VALUE_RX)) / len(vals) >= 0.3:
            acts.append("drop")
        elif act != "clinical" and vals and sum(1 for v in vals if _is_name(v)) / len(vals) >= NAME_SHARE:
            acts.append("pseudonymise")
        else:
            acts.append("keep")
    return acts


def classify_columns(header: list[str], rows: list[list[str]]) -> dict[str, str]:
    return dict(zip(_unique(header), _classify(header, rows)))


def find_header(table: list[list[str]]) -> int | None:
    """Index of the first row (of the first 10) with >= 2 cells that are recognised column names."""
    for n, row in enumerate(table[:HEADER_SCAN_ROWS]):
        if sum(1 for c in row if c.strip() and _header_action(_plain(c))) >= 2:
            return n
    return None


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
    h_idx = find_header(table)
    if h_idx is None:
        print("deidentify: no header row recognised in the first 10 rows; using row 1 as the header. "
              "Check the column actions.", file=sys.stderr)
        h_idx = 0
    header, rows = _unique(table[h_idx]), table[h_idx + 1:]
    acts_l = _classify(header, rows)
    acts = dict(zip(header, acts_l))
    keep_idx = [i for i, a in enumerate(acts_l) if a != "drop"]
    pseudo_idx = [i for i, a in enumerate(acts_l) if a == "pseudonymise"]
    key_idx = [i for i, a in enumerate(acts_l) if a in ("pseudonymise", "drop")]
    cell = lambda r, i: r[i] if i < len(r) else ""  # noqa: E731
    deid_rows, key_rows = [], []
    by_patient: dict[tuple, str] = {}
    for r in rows:
        ident = tuple(cell(r, i).strip() for i in pseudo_idx)
        if any(ident) and ident in by_patient:
            pid = by_patient[ident]
        else:
            pid = f"P{len(key_rows) + 1:04d}"
            if any(ident):
                by_patient[ident] = pid
            key_rows.append([pid] + [cell(r, i) for i in key_idx])
        out = []
        for i in keep_idx:
            v = cell(r, i)
            if acts_l[i] == "pseudonymise":
                v = pid
            elif acts_l[i] == "year-only":
                m = YEAR_RX.search(v)
                v = m.group(0) if m else ""
            out.append(v)
        deid_rows.append(out)
    suspect = {header[i]: sum(1 for r in rows if cell(r, i).strip() and _is_suspect(cell(r, i)))
               for i, a in enumerate(acts_l) if a == "keep"}
    out_dir.mkdir(parents=True, exist_ok=True)
    deid, key = out_dir / f"{src.stem}.deid.csv", out_dir / f"{src.stem}.key.csv"
    with deid.open("w", encoding="utf-8-sig", newline="") as fh:
        csv.writer(fh).writerows([[header[i] for i in keep_idx]] + deid_rows)
    with key.open("w", encoding="utf-8-sig", newline="") as fh:
        csv.writer(fh).writerows([["pseudonym"] + [header[i] for i in key_idx]] + key_rows)
    return {"deid_file": str(deid), "key_file": str(key), "columns": acts, "suspect_values": suspect,
            "rows": len(rows), "rows_above_header": h_idx, "patients": len(key_rows)}


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
    try:
        rep = deidentify_csv(src, Path(a.out) if a.out else src.parent)
    except SystemExit as e:
        if isinstance(e.code, str):
            print(e.code, file=sys.stderr)
            return 2
        raise
    except (OSError, UnicodeDecodeError, csv.Error) as e:
        print(f"deidentify: cannot read {src}: {type(e).__name__}", file=sys.stderr)
        return 2
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
