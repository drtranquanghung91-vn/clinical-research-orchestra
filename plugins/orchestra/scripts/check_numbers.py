#!/usr/bin/env python3
"""E-NUM: every literal number in a results document must come from the results ledger.

  python check_numbers.py <project> <file> [<file> ...] [--lang en|vi]

Numbers written as {{R-…}} placeholders are not checked here (render_results.py checks them). A number
computed from ledger values carries an inline comment right after it: 0.83 <!-- derived: R-A1-001.ci -->.
A number that is not a result (an age range in eligibility criteria, a ward code) carries a marker
right after it, same as derived: 18–65 <!-- not-a-result: eligibility --> (both numbers of a range are skipped).
Headings, citation groups, table/figure/section references, dates, "95%" in CI labels, integers 0–10 and
years are not checked (defaults in references/judgement-defaults.md).
Thousands separators are not parsed (this project never writes them): an author-typed "1,070" (en) or
"1.070" (vi) is expected to produce an E-NUM finding; the fix is a placeholder.
Exit codes: 0 = clean; 1 = numbers not in the ledger (E-NUM block, listed); 2 = usage or I/O error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crolib import numfmt, projectcfg  # noqa: E402

PLACEHOLDER = re.compile(r"\{\{R-A\d+-\d{3}(?:\.\w+)?\}\}")
DERIVED = re.compile(r"-?\d+(?:[.,]\d+)?%?\s*<!--\s*derived:.*?-->")
COMMENT = re.compile(r"<!--.*?-->")
CITE = re.compile(r"\[[^\[\]]*@[^\[\]]*\]|\[\d+(?:\s*[–,-]\s*\d+)*\]")
REFS = re.compile(r"(?:Bảng|Table|Hình|Figure|Biểu đồ|Sơ đồ|mục|Mục|section|Section|Chương|Chapter)\s+\d+(?:\.\d+)*")
DATES = re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b")
NOTRES = re.compile(r"-?\d+(?:[.,]\d+)?%?(?:\s*[–-]\s*-?\d+(?:[.,]\d+)?%?)?\s*<!--\s*not-a-result:.*?-->")
CI95 = re.compile(r"95\s*%\s*(?=CI\b|KTC|CrI\b|confidence interval|khoảng tin cậy)"
                  r"|(?:KTC|CI|CrI|khoảng tin cậy)\s*95\s*%", re.IGNORECASE)
THRESH = re.compile(r"(?:\bp|α|\balpha)\s*[<≤=>≥]\s*0[.,](?:05|01|1)(?!\d)", re.IGNORECASE)
NAMES = re.compile(r"(?<=[^\W\d_])-\d+(?!\d)")
PSMALL = re.compile(r"[<≤]\s*0[.,]001")


def find_unmatched(text: str, ledger_results: list[dict], lang: str) -> list[tuple[int, str]]:
    xs = [x for r in ledger_results if isinstance(r, dict) for x in numfmt.candidates(r)]
    has_small_p = any(isinstance(r, dict) and isinstance(r.get("p"), (int, float)) and r["p"] < 0.001
                      for r in ledger_results)
    found = []
    for n, line in enumerate(text.split("\n"), start=1):
        if line.lstrip().startswith("#"):
            continue
        s = PLACEHOLDER.sub(" ", line.replace("−", "-"))
        s = NOTRES.sub(" ", s)
        s = DERIVED.sub(" ", s)
        s = COMMENT.sub(" ", s)
        s = CITE.sub(" ", s)
        s = REFS.sub(" ", s)
        s = DATES.sub(" ", s)
        s = CI95.sub(" ", s)
        s = THRESH.sub(" ", s)
        s = NAMES.sub(" ", s)
        if has_small_p:
            s = PSMALL.sub(" ", s)
        for tok, value, decimals in numfmt.parse_tokens(s, lang):
            if decimals == 0 and not tok.endswith("%") and (0 <= value <= 10 or 1900 <= value <= 2100):
                continue
            if not numfmt.matches(value, decimals, xs):
                found.append((n, tok))
    return found


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--lang", choices=["en", "vi"])
    a = ap.parse_args(argv)
    project = Path(a.project)
    try:
        with open(project / "ledgers" / "results-ledger.json", encoding="utf-8-sig") as fh:
            ledger = json.load(fh)
        texts = {}
        for f in a.files:
            with open(f, encoding="utf-8", newline="") as fh:
                texts[f] = fh.read()
        lang = a.lang or projectcfg.output_lang(project)
    except (OSError, ValueError) as e:
        print(f"check_numbers: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    results = ledger.get("results") if isinstance(ledger, dict) else None
    if not isinstance(results, list) or not all(isinstance(r, dict) for r in results):
        print("check_numbers: results ledger must be an object with a 'results' list of objects",
              file=sys.stderr)
        return 2
    total = 0
    for f, text in texts.items():
        for n, tok in find_unmatched(text, results, lang):
            print(f"E-NUM block {f}:{n}: {tok} is not in the results ledger")
            total += 1
    print(f"check_numbers: {total} findings")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
