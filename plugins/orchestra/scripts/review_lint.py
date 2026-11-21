#!/usr/bin/env python3
"""Flag literature reviews written paper by paper ("Author A found... Author B found...").

A paragraph is flagged when >= 2 sentences, and >= 50% of its sentences, open with an author or
study as the subject. The file blocks (E-LIT) when >= 2 paragraphs and >= 30% of prose paragraphs
are flagged.  python review_lint.py chapter1.md [--json]
Exit codes: 0 clean, 1 blocking (E-LIT), 2 usage or IO error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

UP = "A-ZÀ-ỸĐ"
PATTERNS = [
    re.compile(rf"^[{UP}][\w'’\-]+(?:\s+[{UP}][\w'’\-]+)*\s+(?:et al\.?|and [{UP}][\w'’\-]+|&\s*[{UP}][\w'’\-]+|và cộng sự|và cs\.?)?\s*\(\d{{4}}[a-z]?\)"),
    re.compile(rf"^[{UP}][\w'’\-]+\s+et al\."),
    re.compile(rf"^(?:In\s+)?(?:a|the|their|his|her)\s+(?:\d{{4}}\s+)?(?:study|trial|cohort|review)\s+(?:by|of)\s+[{UP}]", re.I),
    re.compile(rf"^(?:Tác giả|Nghiên cứu của|Theo nghiên cứu của|Theo tác giả)\s+[{UP}]"),
    re.compile(rf"^Năm\s+\d{{4}},?\s+(?:tác giả\s+)?[{UP}]"),
]
SPLIT = re.compile(rf"(?<=[.!?])\s+(?=[{UP}])")


def paragraphs(text: str) -> list[str]:
    out, in_code = [], False
    for block in re.split(r"\n\s*\n", text):
        b = block.strip()
        if b.startswith("```"):
            in_code = not in_code if b.count("```") == 1 else in_code
            continue
        if in_code or not b or b[0] in "#|>" or re.match(r"^([-*+]|\d+[.)])\s", b):
            continue
        out.append(" ".join(b.split()))
    return out


def sentences(par: str) -> list[str]:
    return [s for s in SPLIT.split(par) if s.strip()]


def author_led(sentence: str) -> bool:
    s = sentence.strip()
    return any(p.search(s) for p in PATTERNS)


def lint(text: str) -> dict:
    pars = paragraphs(text)
    flagged = []
    for i, p in enumerate(pars):
        ss = sentences(p)
        led = sum(author_led(s) for s in ss)
        if led >= 2 and led / len(ss) >= 0.5:
            flagged.append({"index": i, "start": p[:60]})
    blocking = len(flagged) >= 2 and len(flagged) / max(len(pars), 1) >= 0.3
    return {"paragraphs": len(pars), "flagged": flagged, "blocking": blocking}


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        text = Path(a.file).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        print(f"review_lint: cannot read {a.file}: {e}", file=sys.stderr)
        return 2
    rep = lint(text)
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        print(f"review_lint: {len(rep['flagged'])}/{rep['paragraphs']} paragraphs written paper by paper"
              + (" -> E-LIT (block)" if rep["blocking"] else ""))
        for f in rep["flagged"]:
            print(f"  - paragraph {f['index'] + 1}: {f['start']}...")
    return 1 if rep["blocking"] else 0


if __name__ == "__main__":
    sys.exit(main())
