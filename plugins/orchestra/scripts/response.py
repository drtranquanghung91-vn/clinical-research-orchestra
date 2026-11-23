#!/usr/bin/env python3
"""Reviewer response: split the comments, snapshot the submitted drafts, verify every claimed change, build the letter.

  python response.py <project> init <comments-file> [--deliverable manuscript|case-report|review] [--unapproved]
  python response.py <project> check
  python response.py <project> build

init splits pasted editor/reviewer comments into items E1, E2 …, R1.1, R1.2 …, R2.1 … (an "Editor" line starts the
editor's section, "Reviewer N"/"Referee N"/"Phản biện N" reviewer N's; numbered or bulleted lines start items,
otherwise blank lines do) into 09_revision/comments.json, and copies the deliverable's drafts (and order.txt) into
09_revision/submitted/<same paths> with their sha256. It refuses when comments.json exists, and when G4 is not open
for the deliverable unless --unapproved (the snapshot must be the submitted version).
09_revision/response.md has one "## <id>" section per item: lines starting ">" quote the comment; a change is
[[CHANGE: <project-relative file> | "<exact new text>"]].
check (E-RESP; numbers E-NUM) blocks: an item without a response; an id not in comments.json; a CHANGE file not in
the project; a CHANGE quote not in the current draft, or already in the submitted snapshot; a response that says
the manuscript was changed with no CHANGE locator; a NEW-ANALYSIS: line (the author decides; never sent); a number
not in the results ledger ({{R-…}} placeholders are rendered; item ids and page/line references are ignored).
Warns: no CHANGE and no "no change because …".
build writes out/response-letter.docx (comments, responses, change locations with section names) only when
gate.final_problems(project, "response-letter.docx") is empty: G4 open for the deliverable after a fresh audit of
the revised drafts and no check block.
Exit codes: 0 = done / no block; 1 = refused or a block; 2 = usage, missing project, comments.json or file, I/O error.
Standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crolib import drafts, reviews  # noqa: E402
import build_docx  # noqa: E402
import check_numbers  # noqa: E402
import gate  # noqa: E402
import render_results  # noqa: E402

COMMENTS = "09_revision/comments.json"
RESPONSE = "09_revision/response.md"
SUBMITTED = "09_revision/submitted"
LETTER = "out/response-letter.docx"
PUBLISHING = ("manuscript", "case-report", "review")
EDITOR = re.compile(r"(?i)^\s*(?:#+\s*)?(?:\*\*)?\s*(?:(?:associate|academic|handling|section|deputy)\s+)?editor(?:'s)?"
                    r"\s*(?:comments?)?\s*[:.]?\s*(?:\*\*)?\s*:?\s*$"
                    r"|^\s*(?:#+\s*)?(?:\*\*)?\s*(?:(?:ý kiến|nhận xét)\s+(?:của\s+)?)?(?:ban\s+)?biên tập(?:\s+viên)?"
                    r"\s*[:.]?\s*(?:\*\*)?\s*$")
REVIEWER = re.compile(r"(?i)^\s*(?:#+\s*)?(?:\*\*)?\s*(?:reviewer|referee|người phản biện|phản biện)\s*#?\s*(\d+)"
                      r"\s*(?:'s)?\s*(?:comments?|nhận xét)?\s*[:.)]?\s*(?:\*\*)?\s*:?\s*$")
ITEM = re.compile(r"^\s*(?:\(?\d{1,3}[.)]|[-*•]|comment\s+\d+\s*[:.])\s+", re.IGNORECASE)
SECTION = re.compile(r"^##\s+(E\d+|R\d+\.\d+)\b")
CHANGE = re.compile(r'\[\[CHANGE:\s*([^|\]]+?)\s*\|\s*"([^"]+)"\s*\]\]')
NO_CHANGE = re.compile(r"(?i)\bno change\b|\bnot changed\b|\bunchanged\b|không (?:sửa|thay đổi|chỉnh sửa)")
CLAIM = re.compile(r"(?i)\bwe (?:have )?(?:now )?(?:revised|changed|added|updated|rewritten|rewrote|clarified|expanded|"
                   r"removed|deleted|moved|corrected|amended|modified|included|shortened)\b|"
                   r"\b(?:has|have) been (?:revised|changed|added|updated|rewritten|clarified|expanded|removed|deleted|"
                   r"moved|corrected|amended|modified|shortened)\b|"
                   r"đã (?:sửa|thêm|bổ sung|chỉnh|viết lại|xoá|xóa|cập nhật|làm rõ|thay đổi|điều chỉnh|rút gọn)")
MASK = re.compile(r"\b(?:E\d+|R\d+\.\d+)\b|(?i:\b(?:pages?|p\.|lines?|l\.|dòng|trang)\s*\d+(?:\s*[–-]\s*\d+)?)")
LETTER_TEXT = {"en": {"title": "Response to the editor and reviewers", "changed": "Changed in"},
               "vi": {"title": "Thư trả lời biên tập viên và người phản biện", "changed": "Đã sửa tại"}}


class InputError(Exception):
    """Exit 2."""


class Refused(Exception):
    """Exit 1."""


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def _chunks(lines: list[str]) -> list[str]:
    numbered = any(ITEM.match(ln) for ln in lines)
    out: list[str] = []
    cur: list[str] = []

    def flush() -> None:
        text = "\n".join(cur).strip()
        if text:
            out.append(text)
        cur.clear()
    for ln in lines:
        if numbered:
            if ITEM.match(ln):
                flush()
                cur.append(ITEM.sub("", ln, count=1))
            else:
                cur.append(ln)
        elif ln.strip():
            cur.append(ln)
        else:
            flush()
    flush()
    return out


def split_comments(text: str) -> list[dict]:
    sections: list[list] = [["E", "Editor", []]]
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)      # labels such as "fictional" are not comments
    for line in text.replace("\r\n", "\n").split("\n"):
        m = REVIEWER.match(line)
        if m:
            sections.append([f"R{int(m.group(1))}", f"Reviewer {int(m.group(1))}", []])
        elif EDITOR.match(line):
            sections.append(["E", "Editor", []])
        else:
            sections[-1][2].append(line)
    items, count = [], {}
    for key, who, lines in sections:
        for text in _chunks(lines):
            count[key] = count.get(key, 0) + 1
            items.append({"id": f"E{count[key]}" if key == "E" else f"{key}.{count[key]}", "who": who, "text": text})
    return items


def init(project: Path, comments_file: str, deliverable: str = "manuscript", unapproved: bool = False) -> dict:
    project = Path(project)
    if deliverable not in PUBLISHING:
        raise InputError(f"deliverable must be one of {', '.join(PUBLISHING)}")
    if (project / COMMENTS).exists():
        raise Refused(f"{COMMENTS} exists: the revision is already initialised (the snapshot must stay the "
                      "submitted version)")
    if not drafts.draft_files(project, deliverable):
        raise InputError(f"no drafts in 06_writing/{deliverable}/")
    ok, why = gate.check_gate(project, "G4", deliverable)
    if not ok and not unapproved:
        raise Refused("the drafts are not the G4-approved version (" + "; ".join(why) + "); if the submitted "
                      "version was exported another way and these drafts are exactly it, rerun with --unapproved")
    src = Path(comments_file)
    if not src.is_file():
        raise InputError(f"{comments_file} not found")
    raw = src.read_bytes()
    items = split_comments(raw.decode("utf-8-sig"))
    if not items:
        raise InputError(f"no comments found in {comments_file}")
    root = project.resolve()
    submitted = {}
    for f in drafts.tracked_files(project, deliverable):
        rel = f.resolve().relative_to(root).as_posix()
        dst = project / SUBMITTED / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(f, dst)
        submitted[rel] = gate.sha256(dst)
    try:
        source = src.resolve().relative_to(root).as_posix()
    except ValueError:
        source = src.name
    data = {"deliverable": deliverable, "source": source, "source_sha256": hashlib.sha256(raw).hexdigest(),
            "created": dt.datetime.now().isoformat(timespec="seconds"), "approved": ok, "items": items,
            "submitted": submitted}
    _write(project / COMMENTS, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    return data


def load_comments(project: Path) -> dict:
    p = Path(project) / COMMENTS
    if not p.is_file():
        raise InputError(f"{COMMENTS} not found: run response.py <project> init <comments-file>")
    try:
        data = json.loads(p.read_text(encoding="utf-8-sig"))
    except ValueError as e:
        raise InputError(f"{COMMENTS} is unreadable: {e}") from e
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        raise InputError(f"{COMMENTS} has no 'items' list")
    return data


def parse_response(text: str) -> dict:
    out: dict = {}
    cur = None
    for n, line in enumerate(text.splitlines(), 1):
        m = SECTION.match(line)
        if m:
            cur = out.setdefault(m.group(1), {"line": n, "lines": []})
        elif re.match(r"^#{1,2}\s", line):
            cur = None
        elif cur is not None:
            cur["lines"].append((n, line))
    return out


def locate(text: str, quote: str):
    words = unicodedata.normalize("NFC", quote).split()
    if not words:
        return None
    return re.search(r"\s+".join(map(re.escape, words)), unicodedata.normalize("NFC", text))


def section_of(text: str, start: int, fallback: str) -> str:
    before = re.findall(r"(?m)^#{1,6}\s+(.+?)\s*$", text[:start])
    if before:
        return before[-1]
    first = re.search(r"(?m)^#{1,6}\s+(.+?)\s*$", text)
    return first.group(1) if first else fallback


def _ledger(project: Path) -> list[dict]:
    p = Path(project) / "ledgers" / "results-ledger.json"
    if not p.is_file():
        return []
    data = json.loads(p.read_text(encoding="utf-8-sig"))
    return [r for r in (data.get("results") or []) if isinstance(r, dict)] if isinstance(data, dict) else []


def _short(q: str) -> str:
    return q if len(q) <= 60 else q[:57] + "…"


def deliverable_of(data: dict) -> str:
    return data.get("deliverable") if data.get("deliverable") in PUBLISHING else "manuscript"


def check(project: Path) -> list[tuple[str, str, str, str]]:
    project = Path(project)
    data = load_comments(project)
    rp = project / RESPONSE
    if not rp.is_file():
        return [("E-RESP", "block", f"{RESPONSE}:1", "not written: one '## <id>' section per comment")]
    sections = parse_response(rp.read_text(encoding="utf-8-sig"))
    ids = [i.get("id") for i in data["items"]]
    found: list[tuple[str, str, str, str]] = []

    def add(code: str, level: str, n: int, msg: str) -> None:
        found.append((code, level, f"{RESPONSE}:{n}", msg))
    for sid, sec in sections.items():
        if sid not in ids:
            add("E-RESP", "block", sec["line"], f"{sid} is not a comment in {COMMENTS}")
    ledger = _ledger(project)
    by_id = {r["id"]: r for r in ledger if isinstance(r.get("id"), str)}
    lang = drafts.lang_of(project, deliverable_of(data))
    root = project.resolve()
    for iid in ids:
        sec = sections.get(iid)
        body = [(n, ln) for n, ln in (sec["lines"] if sec else []) if ln.strip() and not ln.lstrip().startswith(">")]
        if not body:
            add("E-RESP", "block", sec["line"] if sec else 1, f"{iid} has no response")
            continue
        locators = [(n, m.group(1).strip().replace("\\", "/"), m.group(2)) for n, ln in body for m in CHANGE.finditer(ln)]
        for n, rel, quote in locators:
            path = project / rel
            if Path(rel).is_absolute() or not path.resolve().is_relative_to(root) or not path.is_file():
                add("E-RESP", "block", n, f"{iid}: CHANGE file {rel} is not a file in the project")
                continue
            if locate(path.read_text(encoding="utf-8-sig"), quote) is None:
                add("E-RESP", "block", n, f'{iid}: "{_short(quote)}" is not in the current {rel}: the claimed change '
                                          "is not in the draft")
                continue
            sub = project / SUBMITTED / rel
            if sub.is_file() and locate(sub.read_text(encoding="utf-8-sig"), quote):
                add("E-RESP", "block", n, f'{iid}: "{_short(quote)}" was already in the submitted {rel}: the change '
                                          "was not made")
        prose = CHANGE.sub(" ", "\n".join(ln for _, ln in body))
        for n, ln in body:
            m = reviews.REQUEST.match(ln)
            if m and not reviews.is_none(m.group(1)):
                add("E-RESP", "block", n, f"{iid}: NEW-ANALYSIS awaits the author's decision (if accepted: a POST-HOC "
                                          "line in decisions.md and the statistical-analysis route; never run here); "
                                          "the letter cannot go out with it")
        if not locators and CLAIM.search(prose):
            add("E-RESP", "block", body[0][0], f'{iid}: the response says the manuscript was changed but gives no '
                                               '[[CHANGE: <file> | "<new text>"]] locator')
        elif not locators and not NO_CHANGE.search(prose):
            add("E-RESP", "warn", body[0][0], f"{iid}: no change and no 'no change because …': say what changed or why "
                                              "nothing did")
        for n, ln in body:
            if reviews.REQUEST.match(ln):
                continue
            rendered, probs = render_results.render_text(MASK.sub(" ", CHANGE.sub(" ", ln)), by_id, lang)
            for p in probs:
                add("E-NUM", "block", n, f"{iid}: {p.partition(': ')[2] or p}")
            for _, tok in check_numbers.find_unmatched(rendered, ledger, lang):
                add("E-NUM", "block", n, f"{iid}: {tok} is not in the results ledger (use a {{{{R-…}}}} placeholder)")
    return found


def letter_markdown(project: Path, data: dict, lang: str) -> str:
    project = Path(project)
    t = LETTER_TEXT.get(lang, LETTER_TEXT["en"])
    sections = parse_response((project / RESPONSE).read_text(encoding="utf-8-sig"))
    by_id = {r["id"]: r for r in _ledger(project) if isinstance(r.get("id"), str)}

    def where(m) -> str:
        rel, quote = m.group(1).strip().replace("\\", "/"), m.group(2)
        text = (project / rel).read_text(encoding="utf-8-sig")
        hit = locate(text, quote)
        name = section_of(text, hit.start() if hit else 0, Path(rel).stem)
        return f"*{t['changed']} {name} ({Path(rel).name}):* “{quote}”"
    out = [f"# {t['title']}", ""]
    for item in data["items"]:
        out += [f"## {item['who']} — {item['id']}", ""]
        out += [f"> {ln}" if ln.strip() else ">" for ln in item["text"].splitlines()] + [""]
        for _, ln in sections.get(item["id"], {"lines": []})["lines"]:
            if ln.lstrip().startswith(">") or reviews.REQUEST.match(ln):
                continue
            out.append(render_results.render_text(CHANGE.sub(where, ln), by_id, lang)[0])
        out.append("")
    return "\n".join(out)


def build(project: Path) -> Path:
    project = Path(project)
    data = load_comments(project)
    why = gate.final_problems(project, "response-letter.docx")
    if why:
        raise Refused(f"the response letter is a final export (G4 open for the {deliverable_of(data)} after a fresh "
                      "audit of the revised drafts, and a clean response.py check): " + "; ".join(why))
    lang = drafts.lang_of(project, deliverable_of(data))
    out = project / LETTER
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(build_docx.build(letter_markdown(project, data, lang), build_docx.settings_from_project(project),
                                     template=build_docx.template_from_project(project)))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("cmd", choices=["init", "check", "build"])
    ap.add_argument("comments", nargs="?", help="init: the file with the pasted editor and reviewer comments")
    ap.add_argument("--deliverable", choices=PUBLISHING, default="manuscript")
    ap.add_argument("--unapproved", action="store_true")
    a = ap.parse_args(argv)
    project = Path(a.project)
    if not project.is_dir():
        print(f"response: project folder {a.project} not found", file=sys.stderr)
        return 2
    try:
        if a.cmd == "init":
            if not a.comments:
                print("response: init needs the comments file", file=sys.stderr)
                return 2
            data = init(project, a.comments, a.deliverable, a.unapproved)
            print(f"response: {len(data['items'])} comments → {COMMENTS}; {len(data['submitted'])} files in {SUBMITTED}/")
            return 0
        if a.cmd == "build":
            print(f"response: wrote {build(project).relative_to(project).as_posix()}")
            return 0
        found = check(project)
    except Refused as e:
        print(f"response: refused — {e}")
        return 1
    except (InputError, OSError, UnicodeDecodeError, ValueError) as e:
        print(f"response: {e}", file=sys.stderr)
        return 2
    for code, lv, loc, msg in found:
        print(f"{code} {lv} {loc}: {msg}")
    blocks = sum(1 for _, lv, _, _ in found if lv == "block")
    print(f"response: {blocks} block, {len(found) - blocks} warn")
    return 1 if blocks else 0


if __name__ == "__main__":
    sys.exit(main())
