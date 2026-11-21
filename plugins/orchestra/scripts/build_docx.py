#!/usr/bin/env python3
"""Build a .docx from a Markdown subset (standard library only).

  python build_docx.py <input.md> <output.docx> [--project DIR]

Supports #/##/### headings, paragraphs with **bold** and *italic*, "- " bullets, "1. " lines, pipe tables
with a caption line above (Bảng 3.1. … / Table 1. …) and Nguồn:/Note: lines below, and \\newpage.
Page setup from project.yaml → docx (font, size_pt, line_spacing, margins_cm [top, bottom, left, right]);
defaults: Times New Roman 13 pt, 1.5 lines, 2/2/3/2 cm, A4. Approach adapted from Amelia Le's md2docx.py.
Exit codes: 0 = written; 2 = usage or I/O error.
"""
from __future__ import annotations

import argparse
import html
import io
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crolib import projectcfg  # noqa: E402

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
DEFAULTS = {"font": "Times New Roman", "size_pt": 13.0, "line_spacing": 1.5, "margins_cm": (2.0, 2.0, 3.0, 2.0)}
CAPTION = re.compile(r"^(Bảng|Table)\s+\d+(\.\d+)*\.?\s")
NOTE = re.compile(r"^(Nguồn|Ghi chú|Note|Notes|Source)\s*:", re.I)
COMMENT = re.compile(r"<!--.*?-->")
INLINE = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*)")


def settings_from_project(project: Path | None) -> dict:
    s = dict(DEFAULTS)
    if project is None:
        return s
    block = projectcfg.read_project_yaml(project).get("docx", {})
    if not isinstance(block, dict):
        return s
    if block.get("font"):
        s["font"] = block["font"]
    for key in ("size_pt", "line_spacing"):
        if block.get(key):
            s[key] = float(block[key])
    if block.get("margins_cm"):
        nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", block["margins_cm"])]
        if len(nums) == 4:
            s["margins_cm"] = tuple(nums)
    return s


def _runs(text: str, bold_all: bool = False) -> str:
    out = []
    for part in INLINE.split(text):
        if not part:
            continue
        bold = bold_all or (part.startswith("**") and part.endswith("**"))
        italic = not bold and part.startswith("*") and part.endswith("*") and len(part) > 1
        body = part.strip("*") if (bold and not bold_all) or italic else part
        props = ("<w:b/>" if bold else "") + ("<w:i/>" if italic else "")
        out.append(f'<w:r><w:rPr>{props}</w:rPr><w:t xml:space="preserve">{html.escape(body)}</w:t></w:r>')
    return "".join(out)


def _p(text: str, style: str | None = None, indent: bool = False) -> str:
    ppr = (f'<w:pStyle w:val="{style}"/>' if style else "") + ('<w:ind w:left="567" w:hanging="283"/>' if indent else "")
    return f"<w:p><w:pPr>{ppr}</w:pPr>{_runs(text)}</w:p>"


def _table(rows: list[str]) -> str:
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    cells = [r for r in cells if not all(re.fullmatch(r":?-{3,}:?", c) for c in r)]
    ncol = max(len(r) for r in cells)
    width = 9000 // ncol
    border = "".join(f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
                     for s in ("top", "left", "bottom", "right", "insideH", "insideV"))
    grid = "".join(f'<w:gridCol w:w="{width}"/>' for _ in range(ncol))
    trs = []
    for i, row in enumerate(cells):
        tcs = "".join(f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/></w:tcPr>'
                      f'<w:p>{_runs(c, bold_all=(i == 0))}</w:p></w:tc>' for c in row + [""] * (ncol - len(row)))
        trs.append(f"<w:tr>{tcs}</w:tr>")
    return (f'<w:tbl><w:tblPr><w:tblW w:w="{width * ncol}" w:type="dxa"/><w:tblBorders>{border}</w:tblBorders>'
            f"</w:tblPr><w:tblGrid>{grid}</w:tblGrid>{''.join(trs)}</w:tbl>")


def _body(md_text: str) -> str:
    lines = [COMMENT.sub("", ln).rstrip() for ln in md_text.splitlines()]
    out, i, after_table = [], 0, False
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i])
                i += 1
            out.append(_table(rows))
            after_table = True
            continue
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if not ln.strip():
            after_table = False
        elif ln.strip() == "\\newpage":
            out.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
        elif m := re.match(r"^(#{1,3})\s+(.*)", ln):
            out.append(_p(m.group(2), f"Heading{len(m.group(1))}"))
        elif CAPTION.match(ln) and nxt.startswith("|"):
            out.append(_p(ln, "Caption"))
        elif after_table and NOTE.match(ln):
            out.append(_p(ln, "TableNote"))
        elif re.match(r"^[-*]\s+", ln):
            out.append(_p("– " + re.sub(r"^[-*]\s+", "", ln), indent=True))
        elif re.match(r"^\d+\.\s+", ln):
            out.append(_p(ln, indent=True))
        else:
            out.append(_p(ln))
        i += 1
    return "".join(out)


def _styles(s: dict) -> str:
    font, sz = html.escape(s["font"]), int(round(s["size_pt"] * 2))
    line = int(round(240 * s["line_spacing"]))
    fonts = f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}" w:cs="{font}" w:eastAsia="{font}"/>'

    def style(sid, name, extra_ppr="", extra_rpr=""):
        return (f'<w:style w:type="paragraph" w:styleId="{sid}"><w:name w:val="{name}"/><w:basedOn w:val="Normal"/>'
                f"<w:pPr>{extra_ppr}</w:pPr><w:rPr>{extra_rpr}</w:rPr></w:style>")
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles {W}>'
            f'<w:docDefaults><w:rPrDefault><w:rPr>{fonts}<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/></w:rPr></w:rPrDefault>'
            f'<w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="{line}" w:lineRule="auto"/><w:jc w:val="both"/></w:pPr>'
            f"</w:pPrDefault></w:docDefaults>"
            f'<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>'
            + style("Heading1", "heading 1", '<w:keepNext/><w:jc w:val="center"/><w:spacing w:before="240"/>', f'<w:b/><w:sz w:val="{sz + 4}"/>')
            + style("Heading2", "heading 2", '<w:keepNext/><w:spacing w:before="200"/>', f'<w:b/><w:sz w:val="{sz + 2}"/>')
            + style("Heading3", "heading 3", '<w:keepNext/>', "<w:b/><w:i/>")
            + style("Caption", "caption", '<w:keepNext/><w:jc w:val="center"/>', "<w:b/>")
            + style("TableNote", "table note", "", f'<w:i/><w:sz w:val="{max(sz - 4, 16)}"/>')
            + "</w:styles>")


def build(md_text: str, settings: dict) -> bytes:
    top, bottom, left, right = (int(round(x * 567)) for x in settings["margins_cm"])
    sect = (f'<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="{top}" w:right="{right}" '
            f'w:bottom="{bottom}" w:left="{left}" w:header="709" w:footer="709" w:gutter="0"/></w:sectPr>')
    document = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {W}><w:body>'
                f"{_body(md_text)}{sect}</w:body></w:document>")
    files = {
        "[Content_Types].xml": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
            "</Types>",
        "_rels/.rels": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            "</Relationships>",
        "word/_rels/document.xml.rels": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            "</Relationships>",
        "word/document.xml": document,
        "word/styles.xml": _styles(settings),
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, content in files.items():
            z.writestr(name, content)
    return buf.getvalue()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--project")
    a = ap.parse_args(argv)
    try:
        text = Path(a.input).read_text(encoding="utf-8")
        data = build(text, settings_from_project(Path(a.project) if a.project else None))
        Path(a.output).write_bytes(data)
    except (OSError, ValueError) as e:
        print(f"build_docx: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    print(f"build_docx: wrote {a.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
