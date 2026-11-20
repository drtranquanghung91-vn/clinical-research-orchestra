"""Ledger schemas and helpers for a research project folder.

Files (in <project>/ledgers/):
  references.json     {"references": [...]}
  results-ledger.json {"results": [...]}
  claims.json         {"claims": [...]}
CLI: python ledgers.py check <project_dir>
"""
from __future__ import annotations

import json
import string
import sys
from pathlib import Path

CLAIM_KINDS = {"observed", "derived", "recommendation", "background"}
CLAIM_STATUS = {"verified-fulltext", "verified-abstract", "unverified"}
FILES = {"references": "references.json", "results": "results-ledger.json", "claims": "claims.json"}


def _req(rec: dict, fields: list[str]) -> list[str]:
    return [f"missing '{f}'" for f in fields if rec.get(f) in (None, "")]


def validate_reference(rec: dict) -> list[str]:
    errs = _req(rec, ["id", "title"])
    pmid, doi = str(rec.get("pmid") or ""), str(rec.get("doi") or "")
    if not pmid and not doi:
        errs.append("needs a PMID or DOI")
    if pmid and not pmid.isdigit():
        errs.append(f"PMID '{pmid}' is not numeric")
    if doi and not doi.startswith("10."):
        errs.append(f"DOI '{doi}' must start with '10.'")
    if not isinstance(rec.get("used_in", []), list):
        errs.append("'used_in' must be a list")
    return errs


def validate_result(rec: dict) -> list[str]:
    return _req(rec, ["id", "label", "value", "source_file", "locator", "raw"])


def validate_claim(rec: dict) -> list[str]:
    errs = _req(rec, ["id", "file", "text", "kind", "status"])
    if rec.get("kind") and rec["kind"] not in CLAIM_KINDS:
        errs.append(f"kind '{rec['kind']}' not in {sorted(CLAIM_KINDS)}")
    if rec.get("status") and rec["status"] not in CLAIM_STATUS:
        errs.append(f"status '{rec['status']}' not in {sorted(CLAIM_STATUS)}")
    return errs


def _load(path: Path, key: str) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8")).get(key, [])


def load_references(path: Path) -> list[dict]:
    return _load(Path(path), "references")


def save_references(path: Path, refs: list[dict]) -> None:
    Path(path).write_text(json.dumps({"references": refs}, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")


def unique_id(base: str, taken: set[str]) -> str:
    if base not in taken:
        return base
    for ch in string.ascii_lowercase:
        if base + ch not in taken:
            return base + ch
    n = 2
    while f"{base}{n}" in taken:
        n += 1
    return f"{base}{n}"


def _load_checked(path: Path, key: str) -> tuple[list, list[str]]:
    """Like _load, but reports malformed data as error strings instead of raising."""
    fname = path.name
    if not path.exists():
        return [], []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as e:
        return [], [f"{fname}: invalid JSON: {e}"]
    if not isinstance(data, dict):
        return [], [f"{fname}: top level must be an object with key '{key}'"]
    recs = data.get(key, [])
    if not isinstance(recs, list):
        return [], [f"{fname}: '{key}' must be a list"]
    return recs, []


def check_project(project: Path) -> list[str]:
    led = Path(project) / "ledgers"
    checks = [("references", validate_reference), ("results", validate_result), ("claims", validate_claim)]
    errs: list[str] = []
    for key, fn in checks:
        fname = FILES[key]
        recs, load_errs = _load_checked(led / fname, key)
        errs += load_errs
        seen: set[str] = set()
        for n, rec in enumerate(recs, start=1):
            if not isinstance(rec, dict):
                errs.append(f"{fname}: record {n} is not an object")
                continue
            rid = rec.get("id")
            label = rid if isinstance(rid, str) and rid else f"record {n}"
            if rid not in (None, "") and not isinstance(rid, str):
                errs.append(f"{fname}: {label}: id must be a string")
            elif isinstance(rid, str) and rid:
                if rid in seen:
                    errs.append(f"{fname}: duplicate id '{rid}'")
                seen.add(rid)
            errs += [f"{fname}: {label}: {e}" for e in fn(rec)]
    return errs


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2 or argv[0] != "check":
        print("usage: python ledgers.py check <project_dir>")
        return 2
    errs = check_project(Path(argv[1]))
    for e in errs:
        print(e)
    print(f"ledgers: {len(errs)} problems")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
