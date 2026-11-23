#!/usr/bin/env python3
"""E-CRF: case report form and data dictionary from the locked variables table.

  python crf.py <project> build     03_protocol/variables.md -> 03_protocol/ethics/crf.md + data-dictionary.csv
  python crf.py <project> check     E-CRF findings

build needs G2 open (the protocol is locked). It reads every Markdown table of 03_protocol/variables.md that has a
variable (or code) column and a type column, Vietnamese or English headers, and writes one CRF section per form
(column Form/Biểu mẫu/Visit/Lần thu thập; none = one form "main"), grouped by the variables.md heading, plus
data-dictionary.csv with the header variable,label,type,unit,values,range,source_form,required.
check blocks: CRF or dictionary not built; a dictionary row without a type; a coded variable (binary, categorical,
ordinal) without a value list; CRF and dictionary listing different variables; a term of the SAP analysis register
(Outcome, Covariates, Exposure, Factor cells; A0 skipped) that matches no dictionary variable;
03_protocol/ethics/crf-map.csv (term,variable) maps a term the matcher misses and must name a dictionary variable.
check warns: a variable with no objective that no register term uses (data minimisation); a direct identifier
without a stated need (column Need/Lý do thu thập); dossier.md missing or not listing crf.md, data-dictionary.csv
and consent-form.md.
Exit codes: 0 = built / no block; 1 = G2 not open (build) or a block (check); 2 = usage, missing project or
variables.md, unreadable file. Standard library only.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import re
import sys
import unicodedata
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crolib import projectcfg  # noqa: E402
import analysis_plan  # noqa: E402
import gate  # noqa: E402

VARIABLES = "03_protocol/variables.md"
SAP = "03_protocol/sap.md"
CRF = "03_protocol/ethics/crf.md"
DICT = "03_protocol/ethics/data-dictionary.csv"
MAP = "03_protocol/ethics/crf-map.csv"
DOSSIER = "03_protocol/ethics/dossier.md"
FIELDS = ("variable", "label", "type", "unit", "values", "range", "source_form", "required")
CODED = ("binary", "categorical", "ordinal")
HEADERS = {
    "code": {"code", "ma bien", "ma", "variable code", "variable_name"},
    "label": {"bien", "bien so", "variable", "ten bien", "name"},
    "definition": {"dinh nghia / cach do", "dinh nghia", "definition", "definition / measurement"},
    "type": {"loai", "loai bien", "kieu", "type"},
    "values": {"gia tri / don vi", "gia tri", "values", "values / unit", "unit or values"},
    "unit": {"don vi", "unit"},
    "range": {"range", "khoang", "khoang gia tri"},
    "source": {"nguon", "nguon trong emr/his", "source", "collection method", "cach thu thap", "phuong phap thu thap"},
    "role": {"vai tro", "role"},
    "objective": {"muc tieu", "objective", "objectives"},
    "form": {"form", "bieu mau", "visit", "lan thu thap", "thoi diem"},
    "required": {"required", "bat buoc"},
    "need": {"need", "justification", "ly do", "ly do thu thap"},
}
TYPES = [("time-to-event", ("thoi gian-den-su kien", "thoi gian den su kien", "time to event", "time-to-event", "survival")),
         ("binary", ("nhi gia", "binary", "dichotomous")),
         ("ordinal", ("thu tu", "ordinal")),
         ("categorical", ("phan loai", "categorical", "nominal", "danh muc")),
         ("count", ("dem", "count", "roi rac", "discrete")),
         ("continuous", ("lien tuc", "continuous", "numeric")),
         ("date", ("ngay thang", "ngay", "date")),
         ("text", ("van ban", "free text", "text", "dinh danh", "identifier"))]
REGISTER_CELLS = {"outcome", "ket cuc", "covariates", "bien hieu chinh", "exposure", "phoi nhiem", "factor", "yeu to"}
SKIP_TERM = re.compile(r"^(?:nhu|as in|same as|see|xem)\b|^(?:khong|none|no|n/?a|-)$")
SPLIT = re.compile(r"\s*[,;]\s*|\s+(?:và|and|hoặc|or)\s+", re.IGNORECASE)
VSPLIT = re.compile(r"\s+/\s+|\s*;\s*|\s*,\s*")
PAREN = re.compile(r"\([^()]*\)")
STOP = {"trong", "cua", "va", "voi", "theo", "cac", "nhung", "mot", "hoac", "the", "of", "and", "or", "in", "at",
        "to", "for", "by", "with", "on", "per", "as", "an"}
IDENT = re.compile(r"\b(?:ho ten|ho va ten|ten benh nhan|patient name|participant name|full name|dia chi|address|so dien thoai|dien thoai|"
                   r"phone|email|cccd|cmnd|can cuoc|national id|ngay sinh|date of birth|dob|so ho so|ma ho so|"
                   r"medical record number|mrn|so the bhyt|bhyt|insurance number)\b")
TEXT = {"en": {"title": "Case report form (CRF)", "form": "Form",
               "cols": "| Code | Field | Type | Unit | Allowed values / range | Required |",
               "note": "Built by crf.py from 03_protocol/variables.md on {date}; edit variables.md and rebuild."},
        "vi": {"title": "Phiếu thu thập số liệu (CRF)", "form": "Biểu mẫu",
               "cols": "| Mã | Trường | Loại | Đơn vị | Giá trị cho phép / khoảng | Bắt buộc |",
               "note": "Tạo bởi crf.py từ 03_protocol/variables.md ngày {date}; sửa variables.md rồi tạo lại."}}


class InputError(Exception):
    """Exit 2."""


class Refused(Exception):
    """Exit 1."""


def fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s).replace("đ", "d").replace("Đ", "D"))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().casefold()


def words(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", fold(s)) if len(w) >= 2 and w not in STOP and not w.isdigit()}


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _column(header: str) -> str | None:
    h = fold(re.sub(r"[*_`]", "", header))
    return next((k for k, names in HEADERS.items() if h in names), None)


def _type(text: str) -> str:
    f = fold(text)
    return next((t for t, keys in TYPES if any(k in f for k in keys)), "")


def _slug(label: str, taken: set) -> str:
    base = re.sub(r"[^a-z0-9]+", "_", fold(PAREN.sub(" ", label))).strip("_")[:32].strip("_") or "var"
    s, i = base, 2
    while s in taken:
        s, i = f"{base}_{i}", i + 1
    taken.add(s)
    return s


def _variable(rec: dict, heading: str, line: int, taken: set) -> dict:
    typ = _type(rec["type"])
    code = re.sub(r"[^A-Za-z0-9_]+", "_", rec["code"]).strip("_").lower()
    if code:
        code = _slug(code, taken)           # a duplicate code gets a _2 suffix
    else:
        code = _slug(rec["label"], taken)
    unit, values = rec["unit"], []
    if typ in CODED:
        values = [v for v in (x.strip() for x in VSPLIT.split(PAREN.sub(" ", rec["values"]))) if v]
    elif rec["values"] and not unit:
        unit = rec["values"]
    required = "no" if fold(rec["required"]) in ("no", "khong", "optional", "tuy chon") else "yes"
    return {"variable": code, "label": rec["label"] or rec["code"], "type": typ, "unit": unit, "values": values,
            "range": rec["range"], "source_form": rec["form"] or "main", "required": required, "section": heading,
            "objective": rec["objective"], "role": rec["role"], "need": rec["need"], "source": rec["source"],
            "line": line}


def parse_variables(text: str) -> list[dict]:
    rows: list[dict] = []
    taken: set = set()
    lines, heading, i = text.splitlines(), "", 0
    while i < len(lines):
        m = re.match(r"^#{1,6}\s+(.*\S)\s*$", lines[i])
        if m:
            heading, i = m.group(1), i + 1
            continue
        if lines[i].strip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{3,}", lines[i + 1]):
            cols = [_column(h) for h in _cells(lines[i])]
            j, body = i + 2, []
            while j < len(lines) and lines[j].strip().startswith("|"):
                body.append((j + 1, _cells(lines[j])))
                j += 1
            if ("label" in cols or "code" in cols) and "type" in cols:
                for n, cells in body:
                    rec = dict.fromkeys(HEADERS, "")
                    for k, v in zip(cols, cells):
                        if k and not rec[k]:
                            rec[k] = re.sub(r"\*\*|__|`", "", v).strip()
                    if rec["label"] or rec["code"]:
                        rows.append(_variable(rec, heading, n, taken))
            i = j
            continue
        i += 1
    return rows


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def _cell(s) -> str:
    return str(s).replace("|", "/").replace("\n", " ")


def crf_markdown(vs: list[dict], lang: str) -> str:
    t = TEXT.get(lang, TEXT["en"])
    out = [f"# {t['title']}", "", f"<!-- {t['note'].format(date=dt.date.today().isoformat())} -->", ""]
    for form in dict.fromkeys(v["source_form"] for v in vs):
        out += [f"## {t['form']}: {form}", ""]
        for sec in dict.fromkeys(v["section"] for v in vs if v["source_form"] == form):
            if sec:
                out += [f"### {sec}", ""]
            out += [t["cols"], "|---|---|---|---|---|---|"]
            for v in vs:
                if v["source_form"] == form and v["section"] == sec:
                    allowed = " · ".join(v["values"]) or v["range"]
                    out.append(f"| {v['variable']} | {_cell(v['label'])} | {v['type'] or '?'} | {_cell(v['unit'])} | "
                               f"{_cell(allowed)} | {v['required']} |")
            out.append("")
    return "\n".join(out)


def _load_variables(project: Path) -> list[dict]:
    path = project / VARIABLES
    if not path.is_file():
        raise InputError(f"{VARIABLES} not found: write the variables table first (protocol-design)")
    return parse_variables(path.read_text(encoding="utf-8-sig"))


def build(project: Path) -> tuple[int, list[str]]:
    project = Path(project)
    ok, why = gate.check_gate(project, "G2")
    if not ok:
        raise Refused("G2 is not open: the CRF is built from the locked protocol (" + "; ".join(why) + ")")
    vs = _load_variables(project)
    if not vs:
        raise InputError(f"{VARIABLES} has no table with a variable and a type column")
    _write(project / CRF, crf_markdown(vs, projectcfg.output_lang(project)))
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(FIELDS)
    for v in vs:
        w.writerow([v["variable"], v["label"], v["type"], v["unit"], "|".join(v["values"]), v["range"],
                    v["source_form"], v["required"]])
    _write(project / DICT, buf.getvalue())
    return len(vs), [CRF, DICT]


def _read_dict(project: Path) -> list[dict] | None:
    p = project / DICT
    if not p.is_file():
        return None
    with open(p, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _crf_codes(project: Path) -> set[str] | None:
    p = project / CRF
    if not p.is_file():
        return None
    codes = set()
    for line in p.read_text(encoding="utf-8-sig").splitlines():
        if line.strip().startswith("|"):
            c = _cells(line)[0]
            if c and not set(c) <= set("-: ") and fold(c) not in ("code", "ma"):
                codes.add(c)
    return codes


def register_terms(project: Path) -> list[tuple[str, str, str, int]]:
    """(analysis id, column, term, SAP line) for the register cells that name variables (A0 skipped)."""
    p = project / SAP
    if not p.is_file():
        return []
    text = p.read_text(encoding="utf-8-sig")
    try:
        reg = analysis_plan.parse_register(text)
    except ValueError:
        return []
    out = []
    for row in reg:
        if row.get("id") == "A0":
            continue
        m = re.search(rf"(?m)^\s*\|\s*{re.escape(row['id'])}\s*\|", text)
        line = text.count("\n", 0, m.start()) + 1 if m else 1
        for col, cell in row.items():
            if fold(col) not in REGISTER_CELLS:
                continue
            for term in SPLIT.split(PAREN.sub(" ", cell)):
                term = term.strip(" .")
                if term and not SKIP_TERM.search(fold(term)) and words(term):
                    out.append((row["id"], col, term, line))
    return out


def matches(term: str, row: dict) -> bool:
    tw = words(term)
    lw = words(row.get("label", "")) | words(str(row.get("variable", "")).replace("_", " "))
    return bool(tw) and len(tw & lw) / len(tw) >= 0.6


def _map(project: Path, names: set) -> tuple[dict, list]:
    p, out, problems = project / MAP, {}, []
    if p.is_file():
        with open(p, encoding="utf-8-sig", newline="") as fh:
            for i, r in enumerate(csv.DictReader(fh), 2):
                term, var = (r.get("term") or "").strip(), (r.get("variable") or "").strip()
                if var not in names:
                    problems.append(("block", f"{MAP}:{i}", f"maps '{term}' to '{var}', which is not in the data dictionary"))
                else:
                    out[fold(term)] = var
    return out, problems


def check(project: Path) -> list[tuple[str, str, str]]:
    project = Path(project)
    rows, codes = _read_dict(project), _crf_codes(project)
    if rows is None or codes is None:
        return [("block", f"{rel}:1", "not built: run crf.py <project> build")
                for rel, x in ((CRF, codes), (DICT, rows)) if x is None]
    found: list[tuple[str, str, str]] = []
    names = {r.get("variable", "") for r in rows}
    for i, r in enumerate(rows, 2):
        v, typ = r.get("variable", ""), (r.get("type") or "").strip()
        if not typ:
            found.append(("block", f"{DICT}:{i}", f"{v}: no type"))
        elif typ in CODED and not (r.get("values") or "").strip():
            found.append(("block", f"{DICT}:{i}", f"{v}: coded variable ({typ}) without a value list"))
    found += [("block", f"{CRF}:1", f"{v} is in the data dictionary but not in the CRF") for v in sorted(names - codes)]
    found += [("block", f"{DICT}:1", f"{v} is in the CRF but not in the data dictionary") for v in sorted(codes - names)]
    mapping, problems = _map(project, names)
    found += problems
    used: set = set()
    for aid, col, term, line in register_terms(project):
        hit = mapping.get(fold(term))
        hits = [hit] if hit else [r["variable"] for r in rows if matches(term, r)]
        if hits:
            used.update(hits)
            continue
        found.append(("block", f"{SAP}:{line}", f"register {aid} ({col}) uses '{term}', which matches no CRF variable: "
                                                f"the author adds it to variables.md (a protocol change), or map it in {MAP}"))
    src = {v["variable"]: v for v in _load_variables(project)} if (project / VARIABLES).is_file() else {}
    for i, r in enumerate(rows, 2):
        v = r.get("variable", "")
        s = src.get(v, {})
        if not s.get("objective") and v not in used:
            found.append(("warn", f"{DICT}:{i}", f"{v}: no objective and no analysis uses it; collect it only if "
                                                 "needed (data minimisation)"))
        if IDENT.search(fold(f"{r.get('label', '')} {v.replace('_', ' ')}")) and not s.get("need"):
            found.append(("warn", f"{DICT}:{i}", f"{v}: a direct identifier collected without a stated need (add a "
                                                 "Need / Lý do thu thập column in variables.md, or drop it)"))
    dossier = project / DOSSIER
    if not dossier.is_file():
        found.append(("warn", f"{DOSSIER}:1", "no dossier.md listing the ethics documents and their status"))
    else:
        text = dossier.read_text(encoding="utf-8-sig")
        found += [("warn", f"{DOSSIER}:1", f"dossier.md does not list {d}")
                  for d in ("crf.md", "data-dictionary.csv", "consent-form.md") if d not in text]
    return found


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("cmd", choices=["build", "check"])
    a = ap.parse_args(argv)
    project = Path(a.project)
    if not project.is_dir():
        print(f"crf: project folder {a.project} not found", file=sys.stderr)
        return 2
    try:
        if a.cmd == "build":
            n, files = build(project)
            print(f"crf: {n} variables → {', '.join(files)}")
            return 0
        found = check(project)
    except Refused as e:
        print(f"crf: refused — {e}")
        return 1
    except (InputError, OSError, UnicodeDecodeError, csv.Error) as e:
        print(f"crf: {e}", file=sys.stderr)
        return 2
    for lv, loc, msg in found:
        print(f"E-CRF {lv} {loc}: {msg}")
    blocks = sum(1 for lv, _, _ in found if lv == "block")
    print(f"crf: {blocks} block, {len(found) - blocks} warn")
    return 1 if blocks else 0


if __name__ == "__main__":
    sys.exit(main())
