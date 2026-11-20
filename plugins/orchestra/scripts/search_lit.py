#!/usr/bin/env python3
"""Search the literature and add verified-identifier records to a project's reference ledger.

Every identifier this tool prints comes from a live lookup. Never type a PMID or DOI from memory.

  python search_lit.py search "polycystic ovary syndrome[tiab] AND lifestyle" --max 20
  python search_lit.py search "PMOS lifestyle" --source europepmc
  python search_lit.py fetch 41234567 40123456
  python search_lit.py add <project_dir> 41234567 40123456
  python search_lit.py doi 10.1136/bmj-2024-081123
  python search_lit.py trial NCT01234567

Exit codes: 0 = ok; 1 = some PMID/DOI/NCT not found (listed on stderr; records found are still
printed or added); 2 = usage error (e.g. a PMID that is not all digits), missing or unreadable
ledger, or network/API error.
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


def add_pmids(project: Path, pmids: list[str]) -> tuple[list[str], list[str]]:
    """Add the PMIDs not yet in the ledger. Returns (ids added, PMIDs PubMed does not know)."""
    path = Path(project) / "ledgers" / "references.json"
    refs = ledgers.load_references(path)
    have = {str(r.get("pmid")) for r in refs if r.get("pmid")}
    new = [p for p in pmids if p not in have]
    if not new:
        return [], []
    abstracts = litapi.abstracts(new)
    taken = {r.get("id") for r in refs if r.get("id")}
    added, found = [], set()
    for rec in litapi.summaries(new):
        r = to_ledger_record(rec, abstracts.get(str(rec.get("pmid")), ""))
        r["id"] = ledgers.unique_id(r["id"] or "ref", taken)
        taken.add(r["id"])
        refs.append(r)
        added.append(r["id"])
        found.add(str(rec.get("pmid")))
    if added:
        ledgers.save_references(path, refs)
    return added, [p for p in new if p not in found]


def add_to_ledger(project: Path, pmids: list[str]) -> list[str]:
    return add_pmids(project, pmids)[0]


def _check_pmids(pmids: list[str]) -> list[str]:
    return [p for p in pmids if not p.isdigit()]


def _run(args) -> tuple[object, list[str]]:
    """Do the command; return (output, identifiers not found)."""
    if args.cmd == "search":
        if args.source == "europepmc":
            return litapi.epmc_search(args.query, args.max), []
        try:
            pmids = litapi.search(args.query, args.max)
            return (litapi.summaries(pmids) if pmids else litapi.epmc_search(args.query, args.max)), []
        except (OSError, ValueError, ET.ParseError) as e:
            print(f"# PubMed unavailable ({e}); using Europe PMC", file=sys.stderr)
            return litapi.epmc_search(args.query, args.max), []
    if args.cmd == "fetch":
        recs = litapi.summaries(args.pmids)
        abs_ = litapi.abstracts(args.pmids)
        found = {str(r.get("pmid")) for r in recs}
        return ([to_ledger_record(r, abs_.get(str(r.get("pmid")), "")) for r in recs],
                [p for p in args.pmids if p not in found])
    if args.cmd == "add":
        added, missing = add_pmids(Path(args.project), args.pmids)
        return {"added": added, "not_found": missing}, missing
    try:
        return (litapi.crossref(args.doi) if args.cmd == "doi" else litapi.trial(args.nct)), []
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
    a = sub.add_parser("add"); a.add_argument("project"); a.add_argument("pmids", nargs="+")
    d = sub.add_parser("doi"); d.add_argument("doi")
    t = sub.add_parser("trial"); t.add_argument("nct")
    args = ap.parse_args(argv)
    if args.cmd in ("fetch", "add"):
        bad = _check_pmids(args.pmids)
        if bad:
            print(f"search_lit: not a PMID (digits only): {', '.join(bad)}", file=sys.stderr)
            return 2
    if args.cmd == "add":
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
    try:
        out, missing = _run(args)
    except NotFound as e:
        print(f"search_lit: {e} not found", file=sys.stderr)
        return 1
    except (OSError, ValueError, ET.ParseError, KeyError) as e:
        print(f"search_lit: {args.cmd} failed ({type(e).__name__}: {e}); nothing was changed. "
              "Check the network and retry; never type an identifier from memory instead.", file=sys.stderr)
        return 2
    print(json.dumps(out, ensure_ascii=False, indent=2))
    if missing:
        print(f"search_lit: not found on PubMed: {', '.join(missing)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
