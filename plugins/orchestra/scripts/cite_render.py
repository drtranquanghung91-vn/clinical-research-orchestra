#!/usr/bin/env python3
"""Turn [@id] citations in a Markdown draft into Vancouver numbers.

Usage:
  python cite_render.py <project_dir> <draft.md> <out.md> [--start-marker TEXT]

Records come from <project_dir>/ledgers/references.json. A citation is [@id] or [@id1; @id2]
(same syntax as verify_refs.py). Numbers follow order of first appearance; a group is sorted and
compressed: [1,2], [1-3] (en dash), [1-3,5]. A line that is exactly {REFERENCES} becomes the numbered list.

--start-marker TEXT: numbering starts at the first citation after the first line containing TEXT.
Citations before it reuse those numbers; ids seen only before it are numbered after all others.

A cited record with no authors is rendered without them and warned about on stderr
("cite_render: <id> has no authors; check the record"); the exit code is unchanged.

Exit codes: 0 written; 1 findings (E-REF <id>: not in references.json / retracted), nothing written;
2 usage, I/O or JSON error (stderr).

Adapted from Amelia Le's cite_render.py (MIT): numbering and compress logic. Stdlib only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crolib import ledgers  # noqa: E402

# Same citation syntax as verify_refs.py.
CITE_BLOCK = re.compile(r"\[([^\[\]]*@[^\[\]]*)\]")
CITE_KEY = re.compile(r"(?:^|(?<=[;,\s]))@([A-Za-z0-9_:\-]+)")
USAGE = "usage: cite_render.py <project_dir> <draft.md> <out.md> [--start-marker TEXT]"


def compress(nums: list[int]) -> str:
    out, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        out.append(str(nums[i]) if j == i else (f"{nums[i]},{nums[j]}" if j == i + 1 else f"{nums[i]}–{nums[j]}"))
        i = j + 1
    return "[" + ",".join(out) + "]"


def _end(s: str) -> str:
    s = s.strip()
    return s if s.endswith(".") else s + "."


def author_names(rec: dict) -> list[str]:
    """Non-empty author names; None and blank entries are skipped (never rendered as "None")."""
    return [str(a).strip() for a in (rec.get("authors") or []) if a is not None and str(a).strip()]


def vancouver(rec: dict) -> str:
    parts: list[str] = []
    authors = author_names(rec)
    if authors:
        names = authors[:6] + (["et al."] if len(authors) > 6 else [])
        parts.append(_end(", ".join(names)))
    parts.append(_end(str(rec.get("title") or "")))
    journal, year = str(rec.get("journal") or "").strip(), str(rec.get("year") or "").strip()
    vol, issue, pages = (str(rec.get(k) or "").strip() for k in ("volume", "issue", "pages"))
    tail = year
    if vol or issue:
        tail += ";" + vol + (f"({issue})" if issue else "")
    if pages:
        tail += ":" + pages
    if journal and tail:
        parts.append(f"{journal.rstrip('.')}. {tail}.")
    elif journal:
        parts.append(_end(journal))
    elif tail:
        parts.append(_end(tail))
    entry = " ".join(parts)
    if rec.get("doi"):
        entry += f" doi:{str(rec['doi']).strip()}."
    if rec.get("pmid"):
        entry += f" PMID: {str(rec['pmid']).strip()}."
    return entry


def cited_ids(text: str) -> list[str]:
    ids: list[str] = []
    for block in CITE_BLOCK.findall(text):
        for k in CITE_KEY.findall(block):
            if k not in ids:
                ids.append(k)
    return ids


def render(text: str, by_id: dict[str, dict], marker: str | None = None) -> tuple[str, list[str]]:
    """Return (rendered text, ordered ids). Caller must have checked every id exists."""
    scan = text
    if marker:
        pos = 0
        for line in text.splitlines(keepends=True):
            if marker in line:
                scan = text[pos:] + text[:pos]
                break
            pos += len(line)
    order = cited_ids(scan)

    def rep(m: re.Match) -> str:
        nums = sorted({order.index(k) + 1 for k in CITE_KEY.findall(m.group(1))})
        return compress(nums) if nums else m.group(0)

    text = CITE_BLOCK.sub(rep, text)
    listing = "\n".join(f"{i + 1}. {vancouver(by_id[k])}" for i, k in enumerate(order))
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.strip() == "{REFERENCES}":
            lines[i] = listing + line[len(line.rstrip("\r\n")):]
    return "".join(lines), order


def main(argv: list[str] | None = None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass
    args = list(sys.argv[1:] if argv is None else argv)
    marker = None
    if "--start-marker" in args:
        k = args.index("--start-marker")
        if k + 1 >= len(args):
            print(USAGE, file=sys.stderr)
            return 2
        marker = args[k + 1]
        del args[k:k + 2]
    if len(args) != 3:
        print(USAGE, file=sys.stderr)
        return 2
    project, draft, out = Path(args[0]), Path(args[1]), Path(args[2])
    try:
        ledger = project / "ledgers" / "references.json"
        if not ledger.is_file():
            print(f"cite_render: {ledger} not found", file=sys.stderr)
            return 2
        refs = ledgers.load_references(ledger)
        with open(draft, encoding="utf-8", newline="") as fh:  # Path.read_text(newline=) needs 3.13
            text = fh.read()
    except (OSError, ValueError, AttributeError) as e:
        print(f"cite_render: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    if marker and not any(marker in ln for ln in text.splitlines()):
        print(f"cite_render: start marker not found in draft: {marker!r}", file=sys.stderr)
        return 2
    by_id = {r.get("id"): r for r in refs if isinstance(r, dict)}
    bad = []
    for k in cited_ids(text):
        if k not in by_id:
            bad.append(f"E-REF {k}: not in references.json")
        elif by_id[k].get("retracted"):
            bad.append(f"E-REF {k}: retracted")
    if bad:
        print("\n".join(bad))
        return 1
    result, order = render(text, by_id, marker)
    for k in order:
        if not author_names(by_id[k]):
            print(f"cite_render: {k} has no authors; check the record", file=sys.stderr)
    try:
        out.write_text(result, encoding="utf-8", newline="")
    except OSError as e:
        print(f"cite_render: cannot write {out}: {e}", file=sys.stderr)
        return 2
    unused = [i for i in by_id if i not in order]
    print(f"{len(order)} references numbered; unused: {', '.join(map(str, unused)) or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
