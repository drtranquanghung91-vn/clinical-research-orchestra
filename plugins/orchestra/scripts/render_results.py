#!/usr/bin/env python3
"""Replace {{R-…}} placeholders in a Markdown file with values from the results ledger.

  python render_results.py <project> <file.md> [--lang en|vi]

Parts: {{R-A1-001}} value, .ci, .p, .n, .count (non-negative integer, 0 decimals), .full. Language defaults to project.yaml language.output.
Writes <stem>.rendered.md beside the input. Exit 0 = written; 1 = unknown id or missing part (E-NUM
findings listed, nothing written); 2 = usage or I/O error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crolib import numfmt, projectcfg  # noqa: E402

PLACEHOLDER = re.compile(r"\{\{(R-A\d+-\d{3})(?:\.(value|ci|p|n|count|full))?\}\}")
MALFORMED = re.compile(r"\{\{[^{}]*R-[^{}]*\}\}", re.IGNORECASE)


def render_text(text: str, by_id: dict, lang: str) -> tuple[str, list[str]]:
    probs: list[str] = []
    out_lines = []
    for n, line in enumerate(text.split("\n"), start=1):
        def rep(m, n=n):
            rec = by_id.get(m.group(1))
            if rec is None:
                probs.append(f"{n}: {m.group(0)} is not in the results ledger")
                return m.group(0)
            try:
                return numfmt.render(rec, m.group(2) or "value", lang)
            except KeyError:
                probs.append(f"{n}: {m.group(0)} has no '{m.group(2) or 'value'}' in the ledger record")
                return m.group(0)
            except (TypeError, ValueError, IndexError, ArithmeticError):
                probs.append(f"{n}: {m.group(0)} cannot be formatted from its ledger record")
                return m.group(0)
        for bad in MALFORMED.findall(PLACEHOLDER.sub(" ", line)):
            probs.append(f"{n}: malformed placeholder {bad}")
        out_lines.append(PLACEHOLDER.sub(rep, line))
    return "\n".join(out_lines), probs


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("file")
    ap.add_argument("--lang", choices=["en", "vi"])
    a = ap.parse_args(argv)
    project, src = Path(a.project), Path(a.file)
    try:
        with open(project / "ledgers" / "results-ledger.json", encoding="utf-8-sig") as fh:
            ledger = json.load(fh)
        with open(src, encoding="utf-8", newline="") as fh:
            text = fh.read()
        lang = a.lang or projectcfg.output_lang(project)
    except (OSError, ValueError) as e:
        print(f"render_results: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    results = ledger.get("results") if isinstance(ledger, dict) else None
    if not isinstance(results, list) or not all(
            isinstance(r, dict) and isinstance(r.get("id"), str) for r in results):
        print("render_results: results ledger must be an object with a 'results' list of objects with string ids",
              file=sys.stderr)
        return 2
    by_id = {r.get("id"): r for r in results}
    out, probs = render_text(text, by_id, lang)
    if probs:
        for x in probs:
            line, _, msg = x.partition(": ")
            print(f"E-NUM block {src}:{line}: {msg}")
        return 1
    dest = src.with_name(src.stem + ".rendered.md")
    try:
        with open(dest, "w", encoding="utf-8", newline="") as fh:
            fh.write(out)
    except OSError as e:
        print(f"render_results: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    print(f"render_results: wrote {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
