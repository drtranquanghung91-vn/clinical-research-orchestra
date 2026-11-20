#!/usr/bin/env python3
"""Verify every reference record and every in-text citation of a project.

Records: PMID → PubMed esummary; DOI only → Crossref. Title (fuzzy ≥ 0.85), year, first-author
surname and PMID↔DOI agreement are compared. Retracted publications are reported as RETRACTED.
Statuses: VERIFIED · MISMATCH · NOT_FOUND · RETRACTED · NO_IDENTIFIER · ERROR.
Citations: every [@id] in the given Markdown files must exist in the ledger and not be retracted.
Adapted from grand-rounds verify_refs.py (MIT).

  python verify_refs.py <project_dir|references.json> [--write] [--json] [--cite FILE ...]
"""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crolib import ledgers  # noqa: E402
from crolib.http import get as _get  # noqa: E402


def fetch_pubmed(pmid: str) -> dict | None:
    time.sleep(0.34)
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?" + urllib.parse.urlencode(
        {"db": "pubmed", "id": pmid, "retmode": "json", "tool": "clinical-research-orchestra"})
    s = json.loads(_get(url)).get("result", {}).get(str(pmid))
    if not s or "error" in s:
        return None
    ids = {a.get("idtype"): a.get("value") for a in s.get("articleids", [])}
    year = re.match(r"\d{4}", s.get("pubdate", "") or "")
    return {"title": s.get("title", ""), "year": int(year.group(0)) if year else None,
            "first_author": s.get("sortfirstauthor", ""), "doi": ids.get("doi", ""),
            "journal": s.get("source", ""), "pubtypes": s.get("pubtype", [])}


def fetch_crossref(doi: str) -> dict | None:
    try:
        m = json.loads(_get("https://api.crossref.org/works/" + urllib.parse.quote(doi)))["message"]
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    year = (m.get("issued", {}).get("date-parts") or [[None]])[0][0]
    authors = m.get("author", [])
    retracted = any(u.get("type") == "retraction" for u in m.get("updated-by", []) or [])
    return {"title": (m.get("title") or [""])[0], "year": year,
            "first_author": authors[0].get("family", "") if authors else "", "doi": m.get("DOI", doi),
            "journal": (m.get("short-container-title") or m.get("container-title") or [""])[0],
            "pubtypes": ["Retracted Publication"] if retracted else []}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", s).split())


def surname(author: str) -> str:
    a = norm(author)
    return a.split(" ")[0] if a else ""


def compare(rec: dict, found: dict) -> list[str]:
    problems = []
    if rec.get("title"):
        ratio = difflib.SequenceMatcher(None, norm(rec["title"]), norm(found["title"])).ratio()
        if ratio < 0.85:
            problems.append(f"title differs ({ratio:.2f}): found '{found['title'][:90]}'")
    if rec.get("year") and found.get("year") and int(rec["year"]) != int(found["year"]):
        problems.append(f"year {rec['year']} != {found['year']}")
    first = (rec.get("authors") or [""])[0]
    if first and found.get("first_author") and surname(first) != surname(found["first_author"]):
        problems.append(f"first author '{first}' != '{found['first_author']}'")
    return problems


def verify(rec: dict, pubmed=None, crossref=None) -> tuple[str, list[str]]:
    pubmed = pubmed or fetch_pubmed
    crossref = crossref or fetch_crossref
    pmid, doi = str(rec.get("pmid") or "").strip(), str(rec.get("doi") or "").strip()
    if not pmid and not doi:
        return "NO_IDENTIFIER", ["no PMID or DOI: cannot be checked"]
    try:
        notes: list[str] = []
        if pmid:
            found = pubmed(pmid)
            if not found:
                return "NOT_FOUND", [f"PMID {pmid} not found on PubMed"]
            if doi and found.get("doi") and found["doi"].lower() != doi.lower():
                notes.append(f"PMID {pmid} has DOI {found['doi']}, record says {doi}")
        else:
            found = crossref(doi)
            if not found:
                return "NOT_FOUND", [f"DOI {doi} not found on Crossref"]
        notes += compare(rec, found)
        if "Retracted Publication" in (found.get("pubtypes") or []):
            return "RETRACTED", notes + ["publication is retracted"]
        return ("MISMATCH" if notes else "VERIFIED"), notes
    except Exception as e:  # network or parse problem: never report as verified
        return "ERROR", [f"{type(e).__name__}: {e}"]


CITE_BLOCK = re.compile(r"\[([^\[\]]*@[^\[\]]*)\]")
CITE_KEY = re.compile(r"@([A-Za-z0-9_:\-]+)")


def cite_keys(text: str) -> list[str]:
    keys: list[str] = []
    for block in CITE_BLOCK.findall(text):
        for k in CITE_KEY.findall(block):
            if k not in keys:
                keys.append(k)
    return keys


def check_citations(files: list[Path], refs: list[dict]) -> list[dict]:
    by_id = {r.get("id"): r for r in refs}
    findings = []
    for f in files:
        for key in cite_keys(Path(f).read_text(encoding="utf-8")):
            rec = by_id.get(key)
            if rec is None:
                problem = "cited key not in ledgers/references.json"
            elif rec.get("retracted"):
                problem = "cited work is retracted"
            else:
                continue
            findings.append({"code": "E-REF", "severity": "block", "file": str(f), "key": key, "problem": problem})
    return findings


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", help="project folder or references.json")
    ap.add_argument("--write", action="store_true", help="record status in the ledger")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--cite", nargs="*", default=[], help="Markdown files whose [@id] citations to check")
    a = ap.parse_args(argv)
    target = Path(a.target)
    path = target / "ledgers" / "references.json" if target.is_dir() else target
    refs = ledgers.load_references(path)
    today = dt.date.today().isoformat()
    results = []
    for r in refs:
        status, notes = verify(r)
        results.append({"id": r.get("id"), "status": status, "notes": notes})
        if a.write and status != "ERROR":
            r["verified_by"] = f"verify_refs.py {today} {status}"
            r["retracted"] = status == "RETRACTED"
    if a.write:
        ledgers.save_references(path, refs)
    cites = check_citations([Path(f) for f in a.cite], refs)
    if a.json:
        print(json.dumps({"references": results, "citations": cites}, ensure_ascii=False, indent=2))
    else:
        print(f"# verify_refs: {len(results)} references, {len(cites)} citation findings")
        for x in results:
            print(f"- {x['id']}: {x['status']}" + "".join(f"\n    · {n}" for n in x["notes"]))
        for c in cites:
            print(f"- {c['code']} {c['file']}: [@{c['key']}] {c['problem']}")
    ok = all(x["status"] == "VERIFIED" for x in results) and not cites
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
