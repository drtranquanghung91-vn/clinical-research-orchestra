#!/usr/bin/env python3
"""Search the literature and add verified-identifier records to a project's reference ledger.

Every identifier this tool prints comes from a live lookup. Never type a PMID or DOI from memory.

  python search_lit.py search "polycystic ovary syndrome[tiab] AND lifestyle" --max 20
  python search_lit.py search "PMOS lifestyle" --source europepmc
  python search_lit.py fetch 41234567 40123456
  python search_lit.py add <project_dir> 41234567 10.1136/bmj-2024-081123 https://doi.org/10.x/y
  python search_lit.py add-manual <project_dir> --title T --authors "Nguyen VA; Le TB" --journal J \
      --year 2023 --seen-in "00_inputs/tapchi-yhvn-2023.pdf p. 45" [--volume V --issue I --pages P --url U]
  python search_lit.py doi 10.1136/bmj-2024-081123
  python search_lit.py trial NCT01234567

`add` takes PMIDs (digits) and DOIs (10.x/..., a doi.org URL prefix is stripped; looked up on Crossref).
`add-manual` records a source the author holds but that has no PMID/DOI (source "manual", no identifier).
PubMed lookups (fetch, add) fall back to Europe PMC when NCBI is unreachable. A PMID that Europe PMC
does not have is then "not checked", never "not found" (Europe PMC lags PubMed): exit 2, retry later.

Exit codes: 0 = ok; 1 = some PMID/DOI/NCT not found (listed on stderr; records found are still
printed or added); 2 = usage error (e.g. an id that is neither a PMID nor a DOI, empty --seen-in),
missing or unreadable ledger, network/API error, or a PMID not checked because PubMed was unreachable.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crolib import ledgers, litapi  # noqa: E402


class NotFound(Exception):
    pass


def to_ledger_record(rec: dict, abstract: str) -> dict:
    out = {k: rec.get(k, "") for k in ("id", "title", "authors", "journal", "year", "volume", "issue",
                                       "pages", "doi", "pmid", "pmcid")}
    out["abstract"] = abstract or ""
    out["fulltext_read"] = False
    out["retracted"] = "Retracted Publication" in (rec.get("pubtypes") or [])
    out["design"] = ""
    out["rob"] = ""
    out["retrieved_with"] = rec.get("retrieved_with", "")
    out["verified_by"] = None
    out["used_in"] = []
    return out


def clean_doi(x: str) -> str:
    x = x.strip()
    for pre in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "http://dx.doi.org/", "doi:"):
        if x.lower().startswith(pre):
            return x[len(pre):].strip()
    return x


def classify_id(x: str) -> tuple[str, str] | None:
    """('pmid', digits) or ('doi', doi); None when it is neither."""
    x = x.strip()
    if x.isdigit():
        return "pmid", x
    d = clean_doi(x)
    if d.startswith("10.") and "/" in d:
        return "doi", d
    return None


def pubmed_records(pmids: list[str]) -> tuple[list[dict], dict[str, str], bool]:
    """PubMed summaries + abstracts; Europe PMC when PubMed raises a network/HTTP error.

    The third value (fallback_used) is True when Europe PMC answered instead of PubMed: a PMID
    missing from the result was then not checked, not shown to be absent."""
    if not pmids:
        return [], {}, False
    try:
        return litapi.summaries(pmids), litapi.abstracts(pmids), False
    except (OSError, ValueError, ET.ParseError) as e:
        print(f"# PubMed unavailable ({e}); using Europe PMC", file=sys.stderr)
        recs = litapi.epmc_by_pmid(pmids)
        return recs, {str(r.get("pmid")): r.get("abstract", "") for r in recs}, True


def add_ids(project: Path, ids: list[str]) -> tuple[list[str], list[str], list[str]]:
    """Add PMIDs and DOIs not yet in the ledger.

    Returns (ids added, identifiers not found, PMIDs not checked because PubMed was unreachable
    and Europe PMC had no record)."""
    path = Path(project) / "ledgers" / "references.json"
    refs = ledgers.load_references(path)
    have_pmid = {str(r.get("pmid")) for r in refs if r.get("pmid")}
    have_doi = {str(r.get("doi")).lower() for r in refs if r.get("doi")}
    no_pmid_doi = {str(r.get("doi")).lower() for r in refs if r.get("doi") and not r.get("pmid")}
    pmids, dois = [], []
    for i in ids:
        kind, v = classify_id(i)
        if kind == "pmid" and v not in have_pmid and v not in pmids:
            pmids.append(v)
        elif kind == "doi" and v.lower() not in have_doi and v.lower() not in [d.lower() for d in dois]:
            dois.append(v)
    if not pmids and not dois:
        return [], [], []
    recs: list[tuple[dict, str]] = []
    missing: list[str] = []
    unchecked: list[str] = []
    if pmids:
        found, abstracts, fallback_used = pubmed_records(pmids)
        got = {str(r.get("pmid")) for r in found}
        recs += [(r, abstracts.get(str(r.get("pmid")), "")) for r in found]
        (unchecked if fallback_used else missing).extend(p for p in pmids if p not in got)
    for d in dois:
        try:
            recs.append((litapi.crossref(d), ""))
        except urllib.error.HTTPError as e:
            e.close()
            if e.code != 404:
                raise
            missing.append(d)
    taken = {r.get("id") for r in refs if r.get("id")}
    added = []
    for rec, abstract in recs:
        doi = str(rec.get("doi") or "").lower()
        if (rec.get("pmid") and str(rec["pmid"]) in have_pmid) or (doi and doi in no_pmid_doi):
            continue  # same work already in the ledger under its other identifier
        r = to_ledger_record(rec, abstract)
        r["id"] = ledgers.unique_id(r["id"] or "ref", taken)
        taken.add(r["id"])
        refs.append(r)
        added.append(r["id"])
        if r.get("pmid"):
            have_pmid.add(str(r["pmid"]))
        if r.get("doi"):
            have_doi.add(str(r["doi"]).lower())
            if not r.get("pmid"):
                no_pmid_doi.add(str(r["doi"]).lower())
    if added:
        ledgers.save_references(path, refs)
    return added, missing, unchecked


def add_pmids(project: Path, pmids: list[str]) -> tuple[list[str], list[str]]:
    added, missing, unchecked = add_ids(project, pmids)
    return added, missing + unchecked


def add_to_ledger(project: Path, pmids: list[str]) -> list[str]:
    return add_ids(project, pmids)[0]


def manual_record(title: str, authors: str, journal: str, year: int, seen_in: str, volume: str = "",
                  issue: str = "", pages: str = "", url: str = "") -> dict:
    names = [a.strip() for a in authors.split(";") if a.strip()]
    rec = {"id": litapi.make_id(names[0] if names else "", str(year)), "title": title.strip(),
           "authors": names, "journal": journal.strip(), "year": year, "volume": volume, "issue": issue,
           "pages": pages, "abstract": "", "fulltext_read": False, "retracted": False, "design": "",
           "rob": "", "retrieved_with": "add-manual", "source": "manual", "seen_in": seen_in.strip(),
           "verified_by": "author-supplied, not machine-verifiable", "used_in": []}
    if url:
        rec["url"] = url
    return rec


def add_manual(project: Path, **fields) -> str:
    path = Path(project) / "ledgers" / "references.json"
    refs = ledgers.load_references(path)
    rec = manual_record(**fields)
    rec["id"] = ledgers.unique_id(rec["id"], {r.get("id") for r in refs if r.get("id")})
    refs.append(rec)
    ledgers.save_references(path, refs)
    return rec["id"]


def _check_pmids(pmids: list[str]) -> list[str]:
    return [p for p in pmids if not p.isdigit()]


def _run(args) -> tuple[object, list[str], list[str]]:
    """Do the command; return (output, identifiers not found, PMIDs not checked)."""
    if args.cmd == "search":
        if args.source == "europepmc":
            return litapi.epmc_search(args.query, args.max), [], []
        try:
            pmids = litapi.search(args.query, args.max)
            return (litapi.summaries(pmids) if pmids else litapi.epmc_search(args.query, args.max)), [], []
        except (OSError, ValueError, ET.ParseError) as e:
            print(f"# PubMed unavailable ({e}); using Europe PMC", file=sys.stderr)
            return litapi.epmc_search(args.query, args.max), [], []
    if args.cmd == "fetch":
        recs, abs_, fallback_used = pubmed_records(args.pmids)
        found = {str(r.get("pmid")) for r in recs}
        gone = [p for p in args.pmids if p not in found]
        return ([to_ledger_record(r, abs_.get(str(r.get("pmid")), "")) for r in recs],
                ([] if fallback_used else gone), (gone if fallback_used else []))
    if args.cmd == "add":
        added, missing, unchecked = add_ids(Path(args.project), args.ids)
        out = {"added": added, "not_found": missing}
        if unchecked:
            out["not_checked"] = unchecked
        return out, missing, unchecked
    try:
        return (litapi.crossref(args.doi) if args.cmd == "doi" else litapi.trial(args.nct)), [], []
    except urllib.error.HTTPError as e:
        e.close()
        if e.code == 404:
            raise NotFound(args.doi if args.cmd == "doi" else args.nct) from None
        raise


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search"); s.add_argument("query"); s.add_argument("--max", type=int, default=10)
    s.add_argument("--source", choices=["pubmed", "europepmc"], default="pubmed")
    f = sub.add_parser("fetch"); f.add_argument("pmids", nargs="+")
    a = sub.add_parser("add"); a.add_argument("project"); a.add_argument("ids", nargs="+", metavar="id")
    m = sub.add_parser("add-manual"); m.add_argument("project")
    m.add_argument("--title", required=True); m.add_argument("--authors", required=True)
    m.add_argument("--journal", required=True); m.add_argument("--year", required=True)
    m.add_argument("--seen-in", required=True, dest="seen_in")
    for o in ("volume", "issue", "pages", "url"):
        m.add_argument("--" + o, default="")
    d = sub.add_parser("doi"); d.add_argument("doi")
    t = sub.add_parser("trial"); t.add_argument("nct")
    args = ap.parse_args(argv)
    if args.cmd == "fetch":
        bad = _check_pmids(args.pmids)
        if bad:
            print(f"search_lit: not a PMID (digits only): {', '.join(bad)}", file=sys.stderr)
            return 2
    if args.cmd == "add":
        bad = [i for i in args.ids if classify_id(i) is None]
        if bad:
            print(f"search_lit: not a PMID (digits only) or DOI (10.x/...): {', '.join(bad)}", file=sys.stderr)
            return 2
    if args.cmd == "add-manual":
        if not (args.seen_in.strip() and args.title.strip() and args.authors.strip() and args.journal.strip()):
            print("search_lit: add-manual needs non-empty --title, --authors, --journal and --seen-in "
                  "(the document the author holds, e.g. a PDF path and page)", file=sys.stderr)
            return 2
        if not (args.year.isdigit() and len(args.year) == 4):
            print(f"search_lit: --year must be four digits, got '{args.year}'", file=sys.stderr)
            return 2
    if args.cmd in ("add", "add-manual"):
        led = Path(args.project) / "ledgers"
        if not led.is_dir():
            print(f"search_lit: {led} not found; give the project folder (run init_project.py first)",
                  file=sys.stderr)
            return 2
        try:
            ledgers.load_references(led / "references.json")
        except (OSError, ValueError, AttributeError) as e:
            print(f"search_lit: cannot read {led / 'references.json'}: {e}", file=sys.stderr)
            return 2
    if args.cmd == "add-manual":
        try:
            new_id = add_manual(Path(args.project), title=args.title, authors=args.authors,
                                journal=args.journal, year=int(args.year), seen_in=args.seen_in,
                                volume=args.volume, issue=args.issue, pages=args.pages, url=args.url)
        except (OSError, ValueError, AttributeError) as e:
            print(f"search_lit: add-manual failed ({type(e).__name__}: {e}); nothing was changed.",
                  file=sys.stderr)
            return 2
        print(new_id)
        return 0
    try:
        out, missing, unchecked = _run(args)
    except NotFound as e:
        print(f"search_lit: {e} not found", file=sys.stderr)
        return 1
    except (OSError, ValueError, ET.ParseError, KeyError) as e:
        print(f"search_lit: {args.cmd} failed ({type(e).__name__}: {e}); nothing was changed. "
              "Check the network and retry; never type an identifier from memory instead.", file=sys.stderr)
        return 2
    print(json.dumps(out, ensure_ascii=False, indent=2))
    if missing:
        print(f"search_lit: not found (PubMed/Europe PMC/Crossref): {', '.join(missing)}", file=sys.stderr)
    if unchecked:
        print(f"search_lit: could not be checked (PubMed unreachable; Europe PMC has no record): "
              f"{', '.join(unchecked)}. Retry later; never type an identifier from memory instead.",
              file=sys.stderr)
        return 2
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
