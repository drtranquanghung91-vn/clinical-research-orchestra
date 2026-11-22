#!/usr/bin/env python3
"""E-RG: verify the reporting-guideline checklist written by the reporting-guideline-checker agent.

  python guideline_checklist.py <project> [--guideline CODE] [--deliverable thesis|manuscript] [--table] [--json]

Item lists: references/reporting-guidelines/items/<CODE>.json ({"code", "version", "items": [{"id", "section",
"text"}]}; text paraphrased, never copied). Checklist: <project>/reviews/guideline-checklist.json
({"guideline", "deliverable", "items": {"1a": {"status": "present|partial|absent|na", "file", "line", "quote",
"reason"}}}). Block: an item of the guideline missing from the checklist, "absent", "na" without a reason, an
unknown status, a wrong guideline, or "present" whose quote is not within ±3 lines of file:line (in the draft or
in that window rendered from the results ledger). Warn: "partial"; an id that is not in the guideline.
The guideline defaults to project.yaml → reporting_guideline. --table prints the checklist as a Markdown table
for the appendix. Exit codes: 0 = no block; 1 = block findings; 2 = usage, missing project, checklist or item
list, unreadable JSON. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crolib import projectcfg  # noqa: E402
import render_results  # noqa: E402

ITEMS_DIR = Path(__file__).resolve().parents[1] / "references" / "reporting-guidelines" / "items"
CHECKLIST = "reviews/guideline-checklist.json"
STATUSES = ("present", "partial", "absent", "na")
WINDOW = 3
STATUS_VI = {"present": "có", "partial": "một phần", "absent": "không có", "na": "không áp dụng"}


class InputError(Exception):
    """Exit 2."""


class NoItemList(InputError):
    """The project's guideline has no item list in this release."""


class _Outside(Exception):
    """The file points outside the project folder."""


class _NotUtf8(Exception):
    """The source file is not valid UTF-8."""


def _norm(s: str) -> str:
    s = re.sub(r"[*_`]", "", unicodedata.normalize("NFC", s))
    return " ".join(s.split()).casefold()


def guideline_code(project: Path, override: str | None) -> str:
    code = override or projectcfg.read_project_yaml(project).get("reporting_guideline", "")
    if not code or not isinstance(code, str):
        raise InputError("no reporting_guideline in project.yaml; pass --guideline")
    return code


def load_items(code: str) -> dict:
    p = ITEMS_DIR / f"{code}.json"
    if not p.is_file():
        have = ", ".join(sorted(x.stem for x in ITEMS_DIR.glob("*.json"))) or "none"
        raise NoItemList(f"no item list for {code} (available: {have})")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except ValueError as e:
        raise InputError(f"{p.name} is not valid JSON: {e}") from e
    return data


def load_checklist(project: Path, path: Path | None = None) -> tuple[dict, str]:
    p = Path(path) if path else Path(project) / CHECKLIST
    if not p.is_file():
        raise InputError(f"{CHECKLIST} not found: run the reporting-guideline-checker agent first")
    text = p.read_text(encoding="utf-8-sig")
    try:
        data = json.loads(text)
    except ValueError as e:
        raise InputError(f"{p.name} is not valid JSON: {e}") from e
    if not isinstance(data, dict) or not isinstance(data.get("items"), dict):
        raise InputError(f"{p.name} must be an object with an 'items' object")
    return data, text


def _json_line(text: str, item_id: str) -> int:
    m = re.search(r'"' + re.escape(item_id) + r'"\s*:', text)
    return text.count("\n", 0, m.start()) + 1 if m else 1


def _ledger(project: Path) -> dict:
    p = Path(project) / "ledgers" / "results-ledger.json"
    if not p.is_file():
        return {}
    try:
        recs = json.loads(p.read_text(encoding="utf-8-sig")).get("results", [])
    except (ValueError, AttributeError):
        return {}
    return {r.get("id"): r for r in recs if isinstance(r, dict)}


def _windows(project: Path, rel: str, line: int, by_id: dict, lang: str) -> list[str] | None:
    root = Path(project).resolve()
    p = (root / rel).resolve()
    if not p.is_relative_to(root):
        raise _Outside
    if not p.is_file():
        return None
    try:
        lines = p.read_text(encoding="utf-8-sig").splitlines()
    except UnicodeDecodeError as e:
        raise _NotUtf8 from e
    chunk = "\n".join(lines[max(0, line - 1 - WINDOW):min(len(lines), line + WINDOW)])
    return [chunk, render_results.render_text(chunk, by_id, lang)[0]] if by_id else [chunk]


def check(project: Path, guideline: str | None = None, checklist_path: Path | None = None,
          deliverable: str | None = None) -> list[tuple[str, str, str]]:
    project = Path(project)
    code = guideline_code(project, guideline)
    items = load_items(code)
    data, text = load_checklist(project, checklist_path)
    entries, found = data["items"], []
    if str(data.get("guideline", "")).upper() != code.upper():
        found.append(("block", f"{CHECKLIST}:1", f"the checklist is for {data.get('guideline')!r}; the project uses {code}"))
    if deliverable and data.get("deliverable") != deliverable:
        found.append(("warn", f"{CHECKLIST}:1",
                      f"the checklist's deliverable is {data.get('deliverable')!r}; expected {deliverable!r}"))
    by_id, lang = _ledger(project), projectcfg.output_lang(project)
    ids = [it["id"] for it in items["items"]]
    section = {it["id"]: it["section"] for it in items["items"]}
    for iid in ids:
        e, loc = entries.get(iid), f"{CHECKLIST}:{_json_line(text, iid)}"
        if not isinstance(e, dict):
            found.append(("block", f"{CHECKLIST}:1", f"item {iid} ({section[iid]}) is missing from the checklist"))
            continue
        st = e.get("status")
        rel, line, quote = e.get("file"), e.get("line"), str(e.get("quote") or "")
        has_loc = isinstance(rel, str) and rel and isinstance(line, int) and not isinstance(line, bool) and line >= 1
        if st not in STATUSES:
            found.append(("block", loc, f"item {iid}: unknown status {st!r} (present, partial, absent, na)"))
        elif st == "absent":
            found.append(("block", loc, f"item {iid} ({section[iid]}) is absent: add it to the draft or record why it does not apply"))
        elif st == "na":
            if not (isinstance(e.get("reason"), str) and e["reason"].strip()):
                found.append(("block", loc, f"item {iid} is marked NA without a reason"))
        elif st == "partial":
            found.append(("warn", f"{rel}:{line}" if has_loc else loc,
                          f"item {iid} is only partly reported: {e.get('reason') or 'see the checklist'}"))
        elif not has_loc or not quote.strip():
            found.append(("block", loc, f"item {iid} is present but has no file, line or quote"))
        elif not _norm(quote):
            found.append(("block", loc, f"item {iid} has an empty quote"))
        else:
            try:
                wins = _windows(project, rel, line, by_id, lang)
            except _Outside:
                found.append(("block", loc, f"item {iid}: {rel} is outside project folder"))
                continue
            except _NotUtf8:
                found.append(("block", loc, f"item {iid}: {rel} is unreadable (not UTF-8)"))
                continue
            if wins is None:
                found.append(("block", loc, f"item {iid}: {rel} not found"))
            elif not any(_norm(quote) in _norm(w) for w in wins):
                found.append(("block", f"{rel}:{line}",
                              f"item {iid} is present, but its quote is not within ±{WINDOW} lines of {rel}:{line}"))
    for extra in sorted(set(entries) - set(ids)):
        found.append(("warn", f"{CHECKLIST}:{_json_line(text, extra)}", f"item {extra} is not an item of {code}"))
    return found


def absent_count(project: Path, guideline: str | None = None, checklist_path: Path | None = None) -> int:
    code = guideline_code(Path(project), guideline)
    ids = [it["id"] for it in load_items(code)["items"]]
    entries = load_checklist(Path(project), checklist_path)[0]["items"]
    return sum(1 for i in ids if not isinstance(entries.get(i), dict) or entries[i].get("status") == "absent")


def _loc(e: dict) -> str:
    line = e.get("line")
    return f"{e['file']}:{line}" if isinstance(line, int) and not isinstance(line, bool) else str(e["file"])


def table(project: Path, guideline: str | None = None, checklist_path: Path | None = None) -> str:
    project = Path(project)
    code = guideline_code(project, guideline)
    items = load_items(code)["items"]
    data = load_checklist(project, checklist_path)[0]
    if str(data.get("guideline", "")).upper() != code.upper():
        raise InputError(f"the checklist is for {data.get('guideline')!r}; the project uses {code}")
    entries = data["items"]
    vi = projectcfg.output_lang(project) == "vi"
    head = ("| Mục | Phần | Nội dung (diễn giải) | Trạng thái | Vị trí |" if vi
            else "| Item | Section | Recommendation (paraphrase) | Status | Location |")
    rows = [head, "|---|---|---|---|---|"]
    for it in items:
        e = entries.get(it["id"]) if isinstance(entries.get(it["id"]), dict) else {}
        st = e.get("status", "absent")
        where = e.get("reason", "") if st == "na" else (_loc(e) if e.get("file") else "")
        label = STATUS_VI.get(st, st) if vi else ("NA" if st == "na" else st)
        rows.append(f"| {it['id']} | {it['section']} | {it['text']} | {label} | {str(where).replace('|', '/')} |")
    return "\n".join(rows) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--guideline")
    ap.add_argument("--deliverable", choices=("thesis", "manuscript"))
    ap.add_argument("--table", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    project = Path(a.project)
    if not project.is_dir():
        print(f"guideline_checklist: project folder {a.project} not found", file=sys.stderr)
        return 2
    try:
        if a.table:
            print(table(project, a.guideline), end="")
            return 0
        code = guideline_code(project, a.guideline)
        found = check(project, a.guideline, deliverable=a.deliverable)
    except (InputError, OSError) as e:
        print(f"guideline_checklist: {e}", file=sys.stderr)
        return 2
    blocks = sum(1 for lvl, _, _ in found if lvl == "block")
    if a.json:
        print(json.dumps({"guideline": code, "findings": [{"code": "E-RG", "level": l, "location": loc, "msg": m}
                                                          for l, loc, m in found]}, ensure_ascii=False, indent=2))
    else:
        for lvl, loc, msg in found:
            print(f"E-RG {lvl} {loc}: {msg}")
        print(f"guideline_checklist: {code}, {blocks} block, {len(found) - blocks} warn")
    return 1 if blocks else 0


if __name__ == "__main__":
    sys.exit(main())
