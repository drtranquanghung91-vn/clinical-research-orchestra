#!/usr/bin/env python3
"""Import an analysis's results.json into the project's results ledger.

  python results_ledger.py import <project> [--from FILE] [--verify-raw]

FILE defaults to <project>/05_analysis/output/results.json. --verify-raw checks that each record's `raw`
text is found at its `locator` in `source_file` ("line N" for text/CSV, "Sheet!A1" for .xlsx) and that
its `value` appears in `raw` at the printed precision. The ledger is written only when every record is valid.
Exit codes: 0 = imported; 1 = invalid records (listed, nothing written); 2 = usage or I/O error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crolib import numfmt  # noqa: E402

STRING_FIELDS = ("id", "analysis_id", "status", "kind", "source_file", "locator", "raw")
REQUIRED = ("id", "analysis_id", "status", "label", "value", "kind", "source_file", "locator", "raw")
STATUSES = ("prespecified", "posthoc", "deviation")
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
RNS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"


def read_xlsx_cell(path: Path, ref: str) -> str:
    sheet, _, cell = ref.partition("!")
    with zipfile.ZipFile(path) as z:
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rid = next((s.get(RNS) for s in wb.iter("{%s}sheet" % NS["m"]) if s.get("name") == sheet), None)
        if rid is None:
            raise KeyError(f"sheet '{sheet}' not found")
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        target = next((r.get("Target") for r in rels if r.get("Id") == rid), None)
        if target is None:
            raise KeyError(f"relationship '{rid}' for sheet '{sheet}' not found")
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter("{%s}si" % NS["m"]):
                shared.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
        ws = ET.fromstring(z.read("xl/" + target.lstrip("/").removeprefix("xl/")))
        for c in ws.iter("{%s}c" % NS["m"]):
            if c.get("r") == cell:
                if c.get("t") == "inlineStr":
                    return "".join(t.text or "" for t in c.iter("{%s}t" % NS["m"]))
                v = c.find("m:v", NS)
                text = v.text if v is not None else ""
                return shared[int(text)] if c.get("t") == "s" else (text or "")
    raise KeyError(f"cell '{ref}' not found")


def _located_text(project: Path, rec: dict) -> str:
    src = project / rec["source_file"]
    loc = str(rec["locator"])
    m = re.fullmatch(r"line (\d+)", loc)
    if m:
        lines = src.read_text(encoding="utf-8", errors="replace").splitlines()
        n = int(m.group(1))
        return lines[n - 1] if 1 <= n <= len(lines) else ""
    if "!" in loc and src.suffix.lower() == ".xlsx":
        return read_xlsx_cell(src, loc)
    raise ValueError(f"locator '{loc}' is neither 'line N' nor 'Sheet!A1' for an .xlsx file")


def _num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def validate_doc(doc: dict, project: Path, verify_raw: bool = False) -> list[str]:
    probs: list[str] = []
    if not isinstance(doc, dict):
        return ["document: must be a JSON object with 'results' and 'tables' lists"]
    if not isinstance(doc.get("results"), list) or not isinstance(doc.get("tables", []), list):
        return ["document: needs 'results' and 'tables' lists"]
    data_file = doc.get("data_file", "")
    if not (isinstance(data_file, str) and data_file.startswith("04_data/") and data_file.endswith(".deid.csv")):
        probs.append("document: data_file must be a de-identified 04_data/*.deid.csv file")
    seen: set[str] = set()
    root = project.resolve()
    for n, rec in enumerate(doc["results"], start=1):
        if not isinstance(rec, dict):
            probs.append(f"#{n}: result must be an object")
            continue
        rid = rec.get("id") if isinstance(rec.get("id"), str) and rec.get("id") else f"#{n}"
        missing = [f for f in REQUIRED if rec.get(f) in (None, "")]
        if missing:
            probs.append(f"{rid}: missing {', '.join(missing)}")
            continue
        wrong = [f for f in STRING_FIELDS if not isinstance(rec[f], str)]
        if wrong:
            probs.append(f"{rid}: {', '.join(wrong)} must be text")
            continue
        if not re.fullmatch(r"A\d+", rec["analysis_id"]):
            probs.append(f"{rid}: analysis_id '{rec['analysis_id']}' must be A<n>")
        if not re.fullmatch(r"R-A\d+-\d{3}", rid) or not rid.startswith(f"R-{rec['analysis_id']}-"):
            probs.append(f"{rid}: id must be R-<analysis_id>-<3 digits>")
        if rid in seen:
            probs.append(f"{rid}: duplicate id")
        seen.add(rid)
        if rec["status"] not in STATUSES:
            probs.append(f"{rid}: status '{rec['status']}' not in {STATUSES}")
        if rec["kind"] not in numfmt.KINDS:
            probs.append(f"{rid}: kind '{rec['kind']}' not allowed")
        if not _num(rec["value"]):
            probs.append(f"{rid}: value must be a number")
        ci = rec.get("ci")
        if ci is not None and not (isinstance(ci, list) and len(ci) == 2 and all(map(_num, ci)) and ci[0] <= ci[1]):
            probs.append(f"{rid}: ci must be [lo, hi] with lo <= hi")
        p = rec.get("p")
        if p is not None and not (_num(p) and 0 <= p <= 1):
            probs.append(f"{rid}: p must be between 0 and 1")
        src = Path(rec["source_file"])
        target = (project / src).resolve()
        if src.anchor or ".." in src.parts or not target.is_relative_to(root) or not target.is_file():
            probs.append(f"{rid}: source_file '{rec['source_file']}' must be an existing file inside the project")
            continue
        if verify_raw:
            try:
                text = _located_text(project, rec)
            except (KeyError, ValueError, OSError, IndexError, StopIteration, ET.ParseError, zipfile.BadZipFile) as e:
                probs.append(f"{rid}: raw cannot be located ({str(e) or type(e).__name__})")
                continue
            if str(rec["raw"]) not in text:
                probs.append(f"{rid}: raw text not found at {rec['locator']}")
            elif _num(rec["value"]) and not any(
                    numfmt.matches(v, d, [rec["value"]]) for _, v, d in numfmt.parse_tokens(str(rec["raw"]), "any")):
                probs.append(f"{rid}: value {rec['value']} does not appear in raw")
    return probs


def import_results(project: Path, src: Path | None = None, verify_raw: bool = False) -> tuple[int, list[str]]:
    src = src or project / "05_analysis" / "output" / "results.json"
    doc = json.loads(src.read_text(encoding="utf-8"))
    probs = validate_doc(doc, project, verify_raw)
    if probs:
        return 0, probs
    records = [dict(r, data_sha256=doc.get("data_sha256", ""), locked=False) for r in doc["results"]]
    out = project / "ledgers" / "results-ledger.json"
    out.write_text(json.dumps({"results": records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(records), []


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["import"])
    ap.add_argument("project")
    ap.add_argument("--from", dest="src")
    ap.add_argument("--verify-raw", action="store_true")
    a = ap.parse_args(argv)
    project = Path(a.project)
    if not (project / "ledgers").is_dir():
        print(f"results_ledger: {project} has no ledgers/ folder", file=sys.stderr)
        return 2
    src = Path(a.src) if a.src else None
    try:
        n, probs = import_results(project, src, a.verify_raw)
    except (OSError, ValueError) as e:
        print(f"results_ledger: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    for x in probs:
        print(x)
    if probs:
        print(f"results_ledger: {len(probs)} problems; ledger not written")
        return 1
    print(f"results_ledger: {n} results imported")
    return 0


if __name__ == "__main__":
    sys.exit(main())
