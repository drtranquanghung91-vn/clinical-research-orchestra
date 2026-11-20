#!/usr/bin/env python3
"""De-identify a CSV/XLSX file locally. Prints only column names, actions and counts, never cell values.

Outputs next to --out (default: the source folder):
  <stem>.deid.csv  data for analysis with AI tools
  <stem>.key.csv   pseudonym -> original identifiers; keep it local, never upload it
  python deidentify.py data.csv [--out DIR] [--header-row N]
Exit codes: 0 = done; 2 = missing, unreadable or empty input, or no header row found (nothing written).
The header row is the first of the first 10 rows with >= 2 recognised column names (or row N given with
--header-row, 1-based); rows above it (titles) are counted, not copied.
Column rules, in order: drop (contact, ID cards, address) -> year-only (birth date) -> record ID
(pseudonymise) -> name header (pseudonymise) -> clinical variable (keep) -> values: identifier-like or
name-like values -> drop (originals go to the key file). One pseudonym P0001... per patient, keyed on the
first record-ID column, else the name column(s) plus the birth-date column.
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
VALUE_SHARE = 0.3
HEADER_SCAN_ROWS = 10
NO_HEADER = "deidentify: could not find a header row; add one or pass --header-row N (1-based)"

# Headers are compared in plain form: no diacritics, lower case, words separated by single spaces.
# Substring lists match whole words anywhere in the header; EXACT sets must equal the whole header.
DROP = ["cccd", "cmnd", "bhyt", "bhxh", "dien thoai", "sdt", "so dt", "phone", "email", "dia chi", "address",
        "e mail", "mail", "di dong", "mobile", "tel", "lien he", "noi sinh", "que quan"]
EXACT_DROP = {"bhxh", "so bhxh", "so the", "ma the", "noi o", "cu tru", "noi cu tru", "dt", "ap"}
# Village / ward words drop only when the header has no clinical prefix. With diacritics they are matched in
# their Vietnamese spelling ("ấp" hamlet, not "áp" pressure; "xã" ward, not "xạ" radiation); headers typed
# without any diacritics fall back to the plain words (except "ap", exact only).
ADDRESS_VI = ["thôn", "xóm", "xã", "phường", "ấp", "tổ dân phố"]
ADDRESS_PLAIN = ["thon", "xom", "xa", "phuong", "to dan pho"]
YEAR = ["ngay sinh", "dob", "date of birth", "birth"]
RECORD_ID = ["ma bn", "ma so bn", "ma so benh nhan", "ma so nguoi benh", "ma benh nhan", "ma nguoi benh", "ma ba",
             "so ba", "ma benh an", "so benh an", "ma ho so", "so ho so", "so luu tru", "ma lk", "ma dieu tri",
             "ma tiep nhan", "ma y te", "ma dinh danh", "so vao vien", "so nhap vien", "mrn", "pid", "patient id"]
NAME_PARTS = {"ho", "ten", "ho dem", "ten dem", "ho va ten dem", "first name", "last name", "surname",
              "given name"}
EXACT_NAME = NAME_PARTS | {"full name", "name", "patient", "benh nhan", "nguoi benh", "ho ten", "ho va ten"}
NAME_PHRASES = ["ho ten", "ho va ten", "ten benh nhan", "ten nguoi benh", "ten bn", "patient name", "full name"]
# Clinical variables: kept when the header STARTS with one of these ("Tuổi bệnh nhân", not "Họ tên người giới thiệu").
CLINICAL = ["tuoi", "gioi", "nhom", "so luong", "can nang", "chieu cao", "chan doan", "age", "sex", "gender",
            "group", "weight", "height", "diagnosis", "number of"]
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


def _is_address_part(col: str, h: str) -> bool:
    low = unicodedata.normalize("NFC", col).lower()
    if any(ord(c) > 127 for c in low):
        return any(re.search(rf"(?<!\w){re.escape(w)}(?!\w)", low) for w in ADDRESS_VI)
    return _has(h, ADDRESS_PLAIN)


def header_kind(col: str) -> str | None:
    """drop | year-only | record | name | clinical | None (decide from the values)."""
    h = _plain(col)
    clinical = any(re.match(rf"{re.escape(w)}\b", h) for w in CLINICAL)
    if h in EXACT_DROP or _has(h, DROP) or (not clinical and _is_address_part(col, h)):
        return "drop"
    if _has(h, YEAR):
        return "year-only"
    if _has(h, RECORD_ID):
        return "record"
    if h in EXACT_NAME or _has(h, NAME_PHRASES):
        return "name"
    if clinical:
        return "clinical"
    return None


def _is_name(v: str) -> bool:
    return NAME_VALUE.fullmatch(unicodedata.normalize("NFC", v.strip())) is not None


def _is_suspect(v: str) -> bool:
    return _is_name(v) or any(rx.search(v) for rx in VALUE_RX)


def _classify_full(header: list[str], rows: list[list[str]]) -> tuple[list[str], list[str | None], dict[int, str]]:
    """Per column: action, header kind, and the reason for a value-based drop."""
    acts, kinds, reasons = [], [], {}
    for i, col in enumerate(header):
        kind = header_kind(col)
        kinds.append(kind)
        if kind in ("drop", "year-only"):
            acts.append(kind)
            continue
        if kind in ("record", "name"):
            acts.append("pseudonymise")
            continue
        vals = [r[i] for r in rows if i < len(r) and r[i].strip()][:200]
        if vals and sum(1 for v in vals if any(rx.search(v) for rx in VALUE_RX)) / len(vals) >= VALUE_SHARE:
            acts.append("drop")
            reasons[i] = "identifier-like values"
        elif kind != "clinical" and vals and sum(1 for v in vals if _is_name(v)) / len(vals) >= VALUE_SHARE:
            acts.append("drop")
            reasons[i] = "name-like values"
        else:
            acts.append("keep")
    return acts, kinds, reasons


def _classify(header: list[str], rows: list[list[str]]) -> list[str]:
    return _classify_full(header, rows)[0]


def classify_columns(header: list[str], rows: list[list[str]]) -> dict[str, str]:
    return dict(zip(_unique(header), _classify(header, rows)))


def find_header(table: list[list[str]]) -> int | None:
    """Index of the first row (of the first 10) with >= 2 cells that are recognised column names."""
    for n, row in enumerate(table[:HEADER_SCAN_ROWS]):
        if sum(1 for c in row if c.strip() and header_kind(c)) >= 2:
            return n
    return None


def _patient_key_columns(kinds: list[str | None], acts: list[str], header: list[str]) -> list[int]:
    """First record-ID column; else the name column(s) plus the birth-date column. Never value-only columns."""
    records = [i for i, k in enumerate(kinds) if k == "record"]
    if records:
        return records[:1]
    names = [i for i, k in enumerate(kinds) if k == "name"]
    if not names:
        return []
    parts = [i for i in names if _plain(header[i]) in NAME_PARTS]
    cols = parts if names[0] in parts else names[:1]  # split name (Họ + Tên) is one name
    dob = [i for i, a in enumerate(acts) if a == "year-only"]
    return cols + dob[:1]


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


def deidentify_csv(src: Path, out_dir: Path, header_row: int | None = None) -> dict:
    src, out_dir = Path(src), Path(out_dir)
    table = _read(src)
    if not table:
        raise SystemExit("deidentify: empty file")
    if header_row is not None:
        if not 1 <= header_row <= len(table):
            raise SystemExit(f"deidentify: --header-row {header_row} is outside the file (1..{len(table)})")
        h_idx = header_row - 1
    else:
        h_idx = find_header(table)
        if h_idx is None:
            raise SystemExit(NO_HEADER)
    header, rows = _unique(table[h_idx]), table[h_idx + 1:]
    acts_l, kinds, reasons = _classify_full(header, rows)
    acts = dict(zip(header, acts_l))
    keep_idx = [i for i, a in enumerate(acts_l) if a != "drop"]
    key_idx = [i for i, a in enumerate(acts_l) if a in ("pseudonymise", "drop")]
    pkey = _patient_key_columns(kinds, acts_l, header)
    cell = lambda r, i: r[i] if i < len(r) else ""  # noqa: E731
    deid_rows, key_rows = [], []
    by_patient: dict[tuple, str] = {}
    for r in rows:
        ident = tuple(cell(r, i).strip() for i in pkey)
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
    return {"deid_file": str(deid), "key_file": str(key), "columns": acts,
            "reasons": {header[i]: why for i, why in reasons.items()}, "suspect_values": suspect,
            "patient_key": [header[i] for i in pkey], "rows": len(rows), "rows_above_header": h_idx,
            "patients": len(key_rows)}


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--out")
    ap.add_argument("--header-row", type=int, help="1-based row number of the header (default: detect)")
    a = ap.parse_args(argv)
    src = Path(a.file)
    try:
        rep = deidentify_csv(src, Path(a.out) if a.out else src.parent, header_row=a.header_row)
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
