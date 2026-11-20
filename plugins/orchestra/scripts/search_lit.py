#!/usr/bin/env python3
"""Search the literature and add verified-identifier records to a project's reference ledger.

Every identifier this tool prints comes from a live lookup. Never type a PMID or DOI from memory.

  python search_lit.py search "polycystic ovary syndrome[tiab] AND lifestyle" --max 20
  python search_lit.py search "PMOS lifestyle" --source europepmc
  python search_lit.py fetch 41234567 40123456
  python search_lit.py add <project_dir> 41234567 40123456
  python search_lit.py doi 10.1136/bmj-2024-081123
  python search_lit.py trial NCT01234567
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crolib import ledgers, litapi  # noqa: E402


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


def add_to_ledger(project: Path, pmids: list[str]) -> list[str]:
    path = Path(project) / "ledgers" / "references.json"
    refs = ledgers.load_references(path)
    have = {str(r.get("pmid")) for r in refs if r.get("pmid")}
    new = [p for p in pmids if p not in have]
    if not new:
        return []
    abstracts = litapi.abstracts(new)
    taken = {r["id"] for r in refs}
    added = []
    for rec in litapi.summaries(new):
        r = to_ledger_record(rec, abstracts.get(str(rec.get("pmid")), ""))
        r["id"] = ledgers.unique_id(r["id"], taken)
        taken.add(r["id"])
        refs.append(r)
        added.append(r["id"])
    ledgers.save_references(path, refs)
    return added


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
    if args.cmd == "search":
        if args.source == "europepmc":
            out = litapi.epmc_search(args.query, args.max)
        else:
            pmids = litapi.search(args.query, args.max)
            out = litapi.summaries(pmids) if pmids else litapi.epmc_search(args.query, args.max)
    elif args.cmd == "fetch":
        recs = litapi.summaries(args.pmids)
        abs_ = litapi.abstracts(args.pmids)
        out = [to_ledger_record(r, abs_.get(str(r.get("pmid")), "")) for r in recs]
    elif args.cmd == "add":
        out = {"added": add_to_ledger(Path(args.project), args.pmids)}
    elif args.cmd == "doi":
        out = litapi.crossref(args.doi)
    else:
        out = litapi.trial(args.nct)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
