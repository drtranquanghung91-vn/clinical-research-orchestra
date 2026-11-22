#!/usr/bin/env python3
"""Assemble a thesis or manuscript from its section drafts and build the .docx.

  python assemble.py <project> thesis|manuscript [--final] [--lang vi|en]

Order: 06_writing/<deliverable>/order.txt (one file name or glob per line, # comments) or the default (thesis:
00-tom-tat, 00-dat-van-de, ch1-*, ch2-methods, ch3-results, ch4-discussion, 05-ket-luan, 06-kien-nghi, 90-phu-luc;
manuscript: 00-title, 01-abstract, 02-introduction, 03-methods, 04-results, 05-discussion, 06-conclusion). A
missing optional file is a warning; a missing required section (Chương 2/3/4 and Kết luận; Introduction,
Methods, Results, Discussion) is E-FMT block. {{R-…}} placeholders are rendered from the results ledger (E-NUM
block when one cannot be); per-section {REFERENCES} lines (and the heading right above) are dropped and the
citations are numbered once over the whole text (cite_render; E-REF block for an id not in references.json or
retracted), with the list under "TÀI LIỆU THAM KHẢO" / "References" (a thesis: before the appendix). Captions are
checked (E-FMT): "Bảng c.n" / "Hình c.n" / "Biểu đồ c.n" per thesis chapter, "Table n" / "Figure n" (or Bảng n /
Hình n) across a manuscript; numbers start at 1 without gaps or duplicates and every mention has a caption; a
line with <!-- fmt-ok: reason --> is skipped. Images must exist and be PNG.
Writes 06_writing/<d>/<d>.assembled.md and <d>.draft.docx (draft notice first). --final needs gate G4 open for the
deliverable and reviews/audit.json still matching (gate.py), then writes out/<d>.docx without the notice.
Exit codes: 0 = written; 1 = blocking findings or --final refused (nothing written); 2 = usage, I/O or missing input.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crolib import drafts, ledgers  # noqa: E402
import build_docx  # noqa: E402
import cite_render  # noqa: E402
import gate  # noqa: E402
import render_results  # noqa: E402

KIND = {"Bảng": "table", "Table": "table", "Hình": "figure", "Figure": "figure", "Biểu đồ": "chart"}
# "Bảng 3.1. …", "![Biểu đồ 3.1. …](f.png)", and a pending slot "[Biểu đồ 3.1: … — chờ research-figures]"
# (a leading ** or * is allowed; "![Biểu đồ 3.1](f.png)" with no title is a caption too)
CAP = re.compile(r"^(?:!?\[|\*{1,2}|_)?(Bảng|Table|Hình|Biểu đồ|Figure)\s+(\d+(?:\.\d+)?)(?:\s*\([^)]*\))?"
                 r"(?:\.(?:\*{1,2}|_)?(?:\s|$)|:\s|\](?=\())")
MENTION = re.compile(r"(?<!\w)(Bảng|Table|Hình|Biểu đồ|Figure)\s+(\d+(?:\.\d+)?)")
CHAPTER_FILE = re.compile(r"^ch(\d+)-")
CHAPTER_HEAD = re.compile(r"(?im)^#\s+(?:chương|chapter)\s+(\d+)\b")
IMAGE = re.compile(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$")
COMMENT = re.compile(r"<!--.*?-->", re.S)
REF_HEAD = re.compile(r"^#{1,4}\s*(?:tài liệu tham khảo|references?)\s*$", re.I)
AUTHOR_TODO = re.compile(r"\[\[(?:AUTHOR|TÁC GIẢ)\s*:[^\]]*\]\]")
NOTICE = {"vi": "**BẢN NHÁP – chưa xuất qua cổng G4; không nộp bản này.**",
          "en": "**DRAFT – not released through gate G4; do not submit this version.**"}
REF_TITLE = {"vi": "TÀI LIỆU THAM KHẢO", "en": "References"}
TOC_TITLE = {"vi": "**MỤC LỤC**", "en": "**CONTENTS**"}


def _mask(text: str) -> str:
    return COMMENT.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)


def chapter_of(name: str, text: str) -> int | None:
    m = CHAPTER_FILE.match(name) or CHAPTER_HEAD.search(text)
    return int(m.group(1)) if m else None


def caption_findings(sections: list[tuple[str, str]], deliverable: str,
                     strict: bool = False) -> list[tuple[str, str, str, str]]:
    found: list = []
    seen: dict = {}
    last: dict = {}
    masked = [(rel, text, _mask(text)) for rel, text in sections]
    for rel, text, mtext in masked:
        name = rel.rsplit("/", 1)[-1]
        chap = chapter_of(name, text) if deliverable == "thesis" else None
        appendix = deliverable == "thesis" and name[:1] == "9"
        for i, (line, mline) in enumerate(zip(text.splitlines(), mtext.splitlines()), 1):
            if "fmt-ok" in line:
                continue
            m = CAP.match(mline.strip())
            if not m:
                continue
            word, num = m.group(1), m.group(2)
            kind, loc, parts = KIND[word], f"{rel}:{i}", num.split(".")
            if mline.strip().startswith("[") and not mline.strip().startswith("!["):
                found.append(("E-FMT", "block" if strict else "warn", loc,
                              f"{word} {num} is a pending figure slot, not yet inserted"))
            if appendix:
                seen.setdefault((kind, num), loc)
                continue
            if deliverable == "thesis":
                if chap is None:
                    found.append(("E-FMT", "warn", loc, f"{word} {num} is outside a numbered chapter"))
                    seen.setdefault((kind, num), loc)
                    continue
                if len(parts) != 2 or int(parts[0]) != chap:
                    found.append(("E-FMT", "block", loc, f"{word} {num} in chapter {chap} must be numbered {word} {chap}.n"))
                    continue
                scope, n = chap, int(parts[1])
            else:
                if len(parts) != 1:
                    found.append(("E-FMT", "block", loc, f"{word} {num}: a manuscript numbers {word} 1, 2, 3 … across the paper"))
                    continue
                scope, n = 0, int(parts[0])
            if (kind, num) in seen:
                found.append(("E-FMT", "block", loc, f"{word} {num} is used twice (first at {seen[(kind, num)]})"))
                continue
            seen[(kind, num)] = loc
            expected = last.get((scope, kind), 0) + 1
            if n != expected:
                want = f"{scope}.{expected}" if deliverable == "thesis" else str(expected)
                found.append(("E-FMT", "block", loc,
                              f"{word} {num} out of sequence: expected {word} {want} (numbers start at 1, no gaps)"))
            last[(scope, kind)] = max(n, last.get((scope, kind), 0))
    for rel, text, mtext in masked:
        for i, (line, mline) in enumerate(zip(text.splitlines(), mtext.splitlines()), 1):
            if "fmt-ok" in line:
                continue
            cap = CAP.match(mline.strip())
            rest = mline.strip()[cap.end():] if cap else mline
            for m in MENTION.finditer(rest):
                if (KIND[m.group(1)], m.group(2)) not in seen:
                    found.append(("E-FMT", "block", f"{rel}:{i}",
                                  f"{m.group(1)} {m.group(2)} is mentioned but no caption has that number"))
    return found


def image_findings(base: Path, sections: list[tuple[str, str]]) -> list[tuple[str, str, str, str]]:
    found = []
    for rel, text in sections:
        for i, line in enumerate(text.splitlines(), 1):
            m = IMAGE.match(line.strip())
            if not m:
                continue
            src = m.group(2).strip()
            p = Path(src) if Path(src).is_absolute() else Path(base) / src
            if not p.is_file():
                found.append(("E-FMT", "block", f"{rel}:{i}", f"image not found: {src}"))
                continue
            try:
                build_docx.png_size(p.read_bytes()[:32])
            except ValueError:
                found.append(("E-FMT", "block", f"{rel}:{i}", f"only PNG images are supported: {src}"))
    return found


def format_findings(project: Path, deliverable: str, strict: bool = False) -> list[tuple[str, str, str, str]]:
    project = Path(project)
    files, missing, required = drafts.ordered(project, deliverable)
    base_rel = f"06_writing/{deliverable}"
    found = [("E-FMT", "block", f"{base_rel}/{n}:1", f"required section missing: {drafts.REQUIRED[deliverable][n]} ({n})")
             for n in required]
    found += [("E-FMT", "warn", f"{base_rel}/{e}:1", "in the section order but not found; skipped")
              for e in missing if e not in drafts.REQUIRED[deliverable]]
    listed = {p.name for p in files}
    found += [("E-FMT", "warn", f"{base_rel}/{p.name}:1", "draft not in the section order; not assembled")
              for p in drafts.draft_files(project, deliverable) if p.name not in listed]
    sections = [(f"{base_rel}/{p.name}", p.read_text(encoding="utf-8-sig")) for p in files]
    for rel, text in sections:
        for i, line in enumerate(text.splitlines(), 1):
            for m in AUTHOR_TODO.finditer(line):
                found.append(("E-FMT", "block" if strict else "warn", f"{rel}:{i}",
                              f"author placeholder not filled: {m.group(0)}"))
    return found + caption_findings(sections, deliverable, strict) + image_findings(drafts.folder(project, deliverable), sections)


def _drop_reference_lists(text: str) -> str:
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        if ln.strip() == "{REFERENCES}":
            lines[i] = ""
            j = i - 1
            while j >= 0 and not lines[j].strip():
                j -= 1
            if j >= 0 and REF_HEAD.match(lines[j].strip()):
                lines[j] = ""
    return "\n".join(lines)


def _results(project: Path) -> dict:
    p = Path(project) / "ledgers" / "results-ledger.json"
    if not p.is_file():
        return {}
    data = json.loads(p.read_text(encoding="utf-8-sig"))
    recs = data.get("results") if isinstance(data, dict) else None
    if not isinstance(recs, list):
        raise ValueError("results ledger must be an object with a 'results' list")
    return {r.get("id"): r for r in recs if isinstance(r, dict)}


def _join(parts: list[tuple[str, str]], deliverable: str, lang: str) -> str:
    ref_block = f"# {REF_TITLE[lang]}\n\n{{REFERENCES}}"
    chunks: list[tuple[str, bool]] = []
    if deliverable == "thesis" and not any(ln.strip() == "{TOC}" for _, t in parts for ln in t.splitlines()):
        chunks.append((f"{TOC_TITLE[lang]}\n\n{{TOC}}", False))
    placed = not any(cite_render.cited_ids(t) for _, t in parts)
    prev = None
    for name, t in parts:
        if deliverable == "thesis" and name.startswith("9") and not placed:
            chunks.append((ref_block, True))
            placed = True
        brk = bool(chunks) and (deliverable == "thesis" or prev in ("00-title.md", "01-abstract.md"))
        chunks.append((t, brk))
        prev = name
    if not placed:
        chunks.append((ref_block, True))
    out: list[str] = []
    for t, brk in chunks:
        if out:
            out.append("\n\n\\newpage\n\n" if brk else "\n\n")
        out.append(t)
    return "".join(out) + "\n"


def _citation_findings(rel: str, raw: str, refs: dict) -> list[tuple[str, str, str, str]]:
    """E-REF over the whole comment-masked text, so a citation split over lines is checked too."""
    masked = _mask(raw)
    found = []
    for blk in cite_render.CITE_BLOCK.finditer(masked):
        for key in cite_render.CITE_KEY.finditer(blk.group(1)):
            k = key.group(1)
            line = masked.count("\n", 0, blk.start(1) + key.start()) + 1
            if k not in refs:
                found.append(("E-REF", "block", f"{rel}:{line}", f"[@{k}] is not in ledgers/references.json"))
            elif refs[k].get("retracted"):
                found.append(("E-REF", "block", f"{rel}:{line}", f"[@{k}] is retracted"))
    return found


def build_text(project: Path, deliverable: str, lang: str) -> tuple[str, list, dict]:
    project = Path(project)
    findings = format_findings(project, deliverable)
    files, _, _ = drafts.ordered(project, deliverable)
    by_res = _results(project)
    refs = {r.get("id"): r for r in ledgers.load_references(project / "ledgers" / "references.json") if isinstance(r, dict)}
    parts = []
    for p in files:
        rel = f"06_writing/{deliverable}/{p.name}"
        raw = p.read_text(encoding="utf-8-sig")
        rendered, probs = render_results.render_text(_drop_reference_lists(raw), by_res, lang)
        for x in probs:
            line, _, msg = x.partition(": ")
            findings.append(("E-NUM", "block", f"{rel}:{line}", msg))
        findings += _citation_findings(rel, raw, refs)
        rendered = COMMENT.sub(lambda m: cite_render.CITE_BLOCK.sub("", m.group(0)), rendered)
        parts.append((p.name, rendered.strip("\n")))
    stats = {"sections": len(parts), "references": 0}
    if any(f[1] == "block" for f in findings):
        return "", findings, stats
    text, order = cite_render.render(_join(parts, deliverable, lang), refs)
    stats["references"] = len(order)
    return text, findings, stats


def final_problems(project: Path, deliverable: str) -> list[str]:
    return gate.export_problems(project, deliverable)


def _write_text(path: Path, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def assemble(project: Path, deliverable: str, final: bool = False, lang: str | None = None) -> int:
    project = Path(project)
    lang = lang or drafts.lang_of(project, deliverable)
    if lang not in NOTICE:
        raise ValueError(f"unsupported output language {lang!r}: use vi or en (project.yaml language.output, "
                         "target.language or --lang)")
    if final:
        problems = final_problems(project, deliverable)
        if problems:
            print(f"assemble: G4: closed for the {deliverable} — " + "; ".join(problems))
            print("assemble: nothing written; run audit.py, fix every block, then the author opens G4")
            return 1
    text, findings, stats = build_text(project, deliverable, lang)
    for code, level, loc, msg in findings:
        print(f"{code} {level} {loc}: {msg}")
    blocks = sum(1 for f in findings if f[1] == "block")
    print(f"assemble: {deliverable}: {stats['sections']} sections, {stats['references']} references, "
          f"{blocks} block, {len(findings) - blocks} warn")
    if blocks:
        print("assemble: nothing written")
        return 1
    base = drafts.folder(project, deliverable)
    md = base / f"{deliverable}.assembled.md"
    settings, template = build_docx.settings_from_project(project), build_docx.template_from_project(project)
    if final:
        dest = project / "out" / f"{deliverable}.docx"
        data = build_docx.build(text, settings, base_dir=base, template=template)
    else:
        dest = base / f"{deliverable}.draft.docx"
        data = build_docx.build(NOTICE[lang] + "\n\n" + text, settings, base_dir=base, template=template)
    _write_text(md, text)           # nothing is written when the build above fails
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    print(f"assemble: wrote {md.relative_to(project).as_posix()}")
    print(f"assemble: wrote {dest.relative_to(project).as_posix()}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("deliverable", choices=drafts.DELIVERABLES)
    ap.add_argument("--final", action="store_true")
    ap.add_argument("--lang", choices=["vi", "en"])
    a = ap.parse_args(argv)
    project = Path(a.project)
    if not project.is_dir():
        print(f"assemble: project folder {a.project} not found", file=sys.stderr)
        return 2
    if not drafts.folder(project, a.deliverable).is_dir():
        print(f"assemble: no folder 06_writing/{a.deliverable}/ in {a.project}", file=sys.stderr)
        return 2
    try:
        return assemble(project, a.deliverable, a.final, a.lang)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as e:
        print(f"assemble: {type(e).__name__}: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
