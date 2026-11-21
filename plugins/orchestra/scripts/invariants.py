#!/usr/bin/env python3
"""INV: a prose rewrite must not change what a paragraph asserts.

  python invariants.py BEFORE AFTER [--merge OUT] [--lang vi|en]

Paragraphs (split on blank lines) are paired by position. Per pair these must be equal as multisets:
numbers (Unicode minus and vi/en decimal separators normalised), citation keys (bracketed [@a; @b]
and narrative @key, each key separately), {{R-...}} placeholders, and <!-- derived: ... --> /
<!-- not-a-result: ... --> comments (whole text). The hedge count must not decrease (text is NFC
normalised; multi-word hedges tolerate line breaks; "may" counts only in lower case; with --lang only
that language's list is used, without it both).
Output per failing paragraph: INV block <AFTER>:<line>: paragraph <k>: <problem>.
A different paragraph count -> one "paragraph structure changed" block (with --merge, OUT = BEFORE).
--merge OUT writes AFTER with each failing paragraph replaced by its BEFORE text; line endings of
untouched paragraphs are kept byte for byte.
Without --lang a comma or dot between digits is a decimal separator; with --lang, a thousands
grouping (en 1,070 / vi 1.070) is read as one integer.
Exit codes: 0 = clean; 1 = INV block findings; 2 = usage or I/O error (including non-UTF-8 input).
"""
from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from collections import Counter
from decimal import Decimal, InvalidOperation

for _stream in (sys.stdout, sys.stderr):  # arrows must not crash a cp1252 console
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

PLACEHOLDER = re.compile(r"\{\{R-[^{}]*?\}\}")
MARKER = re.compile(r"<!--\s*(?:derived|not-a-result):.*?-->", re.DOTALL)
COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
CITE_GROUP = re.compile(r"\[[^\[\]]*@[^\[\]]*\]")
CITE_KEY = re.compile(r"@([\w:.\-]*\w)")
NARRATIVE_KEY = re.compile(r"(?<![\w.@])@([\w:.\-]*\w)")  # not an e-mail address
# a number not glued to a word; "COVID-19" keeps its 19 out, "18-65" yields 18 and 65
NUMBER = re.compile(r"(?<![\w.,])(?<![^\W\d_]-)-?\d+(?:[.,]\d+)*")
HEDGES = {
    "vi": ["có thể", "gợi ý", "có xu hướng", "dường như", "khả năng", "chưa đủ bằng chứng"],
    "en": ["may", "might", "could", "suggest(?:s|ed)?", "appears? to", "possibly", "likely",
           "is compatible with"],
}


def _hedge_re(langs) -> "re.Pattern":
    alts = []
    for lang in langs:
        for h in HEDGES[lang]:
            # words joined by \s+ so reflowed lines and double spaces still match; "may" only lower-case
            alts.append(r"\s+".join("(?-i:may)" if w == "may" else w for w in h.split(" ")))
    return re.compile(r"(?<!\w)(?:" + "|".join(alts) + r")(?!\w)", re.IGNORECASE)


_HEDGE_RES = {None: _hedge_re(("vi", "en")), "vi": _hedge_re(("vi",)), "en": _hedge_re(("en",))}


def split_paragraphs(text: str) -> list[tuple[int, str]]:
    """[(1-based start line, paragraph text)] split on blank lines."""
    out, cur, start = [], [], 0
    for i, line in enumerate(text.split("\n"), 1):
        if line.strip() == "":
            if cur:
                out.append((start, "\n".join(cur)))
                cur = []
        else:
            if not cur:
                start = i
            cur.append(line)
    if cur:
        out.append((start, "\n".join(cur)))
    return out


def _canon(tok: str, lang: str | None) -> str:
    neg = tok.startswith("-")
    t = tok.lstrip("-")
    if lang == "en" and re.fullmatch(r"\d{1,3}(?:,\d{3})+", t):
        t = t.replace(",", "")
    elif lang == "vi" and re.fullmatch(r"\d{1,3}(?:\.\d{3})+", t):
        t = t.replace(".", "")
    t = t.replace(",", ".")
    try:
        s = str(Decimal(t))
    except InvalidOperation:
        s = t
    return ("-" if neg else "") + s


def facts(par: str, lang: str | None = None) -> dict:
    par = unicodedata.normalize("NFC", par)
    markers = [re.sub(r"\s+", " ", m.group(0)).strip() for m in MARKER.finditer(par)]
    ph = PLACEHOLDER.findall(par)
    cites = [k for g in CITE_GROUP.findall(par) for k in CITE_KEY.findall(g)]
    scrub = COMMENT.sub(" ", par)
    scrub = PLACEHOLDER.sub(" ", scrub)
    scrub = CITE_GROUP.sub(" ", scrub).replace("−", "-")
    cites += NARRATIVE_KEY.findall(scrub)
    written: dict[str, str] = {}
    nums = []
    for m in NUMBER.finditer(scrub):
        c = _canon(m.group(0), lang)
        written.setdefault(c, m.group(0))
        nums.append(c)
    return {"numbers": Counter(nums), "written": written, "cites": Counter(cites),
            "placeholders": Counter(ph), "markers": Counter(markers),
            "hedges": len(_HEDGE_RES[lang].findall(scrub))}


def _diff(label: str, a: Counter, b: Counter, show_a=lambda x: x, show_b=lambda x: x) -> list[str]:
    ka, kb = list((a - b).elements()), list((b - a).elements())  # order of appearance
    out = []
    if label == "number":
        n = min(len(ka), len(kb))
        out += [f"number {show_a(x)} → {show_b(y)}" for x, y in zip(ka[:n], kb[:n])]
        ka, kb = ka[n:], kb[n:]
    out += [f"{label} {show_a(x)} dropped" for x in ka]
    out += [f"{label} {show_b(x)} added" for x in kb]
    return out


def _paragraph_problems(before: str, after: str, lang: str | None) -> list[str]:
    fb, fa = facts(before, lang), facts(after, lang)
    cite = lambda x: f"[@{x}]"  # noqa: E731
    probs = _diff("number", fb["numbers"], fa["numbers"],
                  lambda x: fb["written"].get(x, x), lambda x: fa["written"].get(x, x))
    probs += _diff("citation", fb["cites"], fa["cites"], cite, cite)
    probs += _diff("placeholder", fb["placeholders"], fa["placeholders"])
    probs += _diff("comment", fb["markers"], fa["markers"])
    if fa["hedges"] < fb["hedges"]:
        probs.append(f"hedges {fb['hedges']} → {fa['hedges']}")
    return probs


def compare(before: str, after: str, lang: str | None = None) -> list[dict]:
    """[{"index", "line", "problems"}] for each failing AFTER paragraph (1-based index).

    A changed paragraph count gives one item with index 0."""
    before, after = before.replace("\r\n", "\n"), after.replace("\r\n", "\n")
    pb, pa = split_paragraphs(before), split_paragraphs(after)
    if len(pb) != len(pa):
        return [{"index": 0, "line": 1,
                 "problems": [f"paragraph structure changed ({len(pb)} → {len(pa)}); compare by hand"]}]
    out = []
    for k, ((_, tb), (la, ta)) in enumerate(zip(pb, pa), 1):
        probs = _paragraph_problems(tb, ta, lang)
        if probs:
            out.append({"index": k, "line": la, "problems": probs})
    return out


def merge(before: str, after: str, failed_indexes) -> str:
    """AFTER with each failing paragraph (1-based index) replaced by its BEFORE text.

    Untouched AFTER paragraphs keep their bytes (incl. CRLF); a restored paragraph takes the line
    ending of the AFTER paragraph it replaces. Paragraph count differs -> BEFORE unchanged."""
    pb = split_paragraphs(before.replace("\r\n", "\n"))
    pa = split_paragraphs(after.replace("\r\n", "\n"))
    if len(pb) != len(pa):
        return before
    lines = after.split("\n")  # same line numbering as the normalised text
    for k in sorted(set(failed_indexes), reverse=True):  # bottom-up keeps earlier line numbers valid
        start, ta = pa[k - 1]
        cr = "\r" if lines[start - 1].endswith("\r") else ""
        lines[start - 1:start - 1 + len(ta.split("\n"))] = [x + cr for x in pb[k - 1][1].split("\n")]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("before")
    ap.add_argument("after")
    ap.add_argument("--merge", metavar="OUT")
    ap.add_argument("--lang", choices=["vi", "en"])
    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    try:
        with open(args.before, encoding="utf-8", newline="") as fh:
            before = fh.read()
        with open(args.after, encoding="utf-8", newline="") as fh:
            after = fh.read()
    except (OSError, UnicodeDecodeError) as e:
        print(f"invariants: {e}", file=sys.stderr)
        return 2
    fails = compare(before, after, args.lang)
    structure = bool(fails) and fails[0]["index"] == 0
    for f in fails:
        if structure:
            print(f"INV block {args.after}:1: {f['problems'][0]}")
        else:
            for p in f["problems"]:
                print(f"INV block {args.after}:{f['line']}: paragraph {f['index']}: {p}")
    if args.merge:
        total = len(split_paragraphs(after.replace("\r\n", "\n")))
        if structure:
            out_text, k = before, 0
        else:
            idx = [f["index"] for f in fails]
            out_text, k = merge(before, after, idx), len(idx)
        try:
            with open(args.merge, "w", encoding="utf-8", newline="") as fh:
                fh.write(out_text)
        except OSError as e:
            print(f"invariants: {e}", file=sys.stderr)
            return 2
        print(f"invariants: {k} of {total} paragraphs reverted")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
