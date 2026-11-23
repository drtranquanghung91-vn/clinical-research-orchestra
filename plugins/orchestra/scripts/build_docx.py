#!/usr/bin/env python3
"""Build a .docx from a Markdown subset (standard library only).

  python build_docx.py <input.md> [<more.md> ...] <output.docx> [--project DIR] [--template FILE.docx]

Supports #/##/###/#### headings, paragraphs with **bold** and *italic*, "- " bullets and "1. " lists (Word list
numbering; each run of numbered lines restarts at its first number), pipe tables with a caption line above
(Bảng 3.1. … / Table 1. …) and Nguồn:/Note: lines below, PNG images on their own line
`![Hình 3.1. Caption](figure.png)` (fitted to the text width, aspect kept, caption below), a `{TOC}` line
(table-of-contents field; Word fills it on open, "Update field"), \\newpage, and a centred page-number footer.
Several inputs are joined in order with a blank line; image paths are relative to their own .md file.
Page setup from project.yaml → docx (font, size_pt, line_spacing, margins_cm [top, bottom, left, right]);
defaults: Times New Roman 13 pt, 1.5 lines, 2/2/3/2 cm, A4. --template FILE.docx (default: project.yaml →
institution.template, relative to the project) replaces the styles and the page setup with the template's
styles.xml and last w:sectPr; content still comes from the Markdown (templates/thesis/README.md).
Approach adapted from Amelia Le's md2docx.py.
A final export, <project>/out/thesis.docx (manuscript.docx, case-report.docx, review.docx, response-letter.docx) in a folder with
project.yaml (or with --project), is refused while gate.final_problems lists reasons (G4 not open for the revision deliverable, a stale audit, or a response.py check block).
Exit codes: 0 = written; 1 = final export refused (reasons on stderr); 2 = usage or I/O error (missing input, image
or template; image not PNG; output not .docx).
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
DOC_NS = (W + ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
          ' xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"'
          ' xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
          ' xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"')
RELS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CT = "application/vnd.openxmlformats-officedocument.wordprocessingml"
XML_HEAD = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
DEFAULTS = {"font": "Times New Roman", "size_pt": 13.0, "line_spacing": 1.5, "margins_cm": (2.0, 2.0, 3.0, 2.0)}
A4 = (11906, 16838)  # twips
EMU_PER_TWIP = 635
CAPTION = re.compile(r"^(Bảng|Table)\s+\d+(\.\d+)*\.?\s")
NOTE = re.compile(r"^(Nguồn|Ghi chú|Note|Notes|Source)\s*:", re.I)
COMMENT = re.compile(r"<!--.*?-->")
# Emphasis needs a non-space right inside both markers and no letter, digit or asterisk right outside them,
# so statistical asterisks ("Mean* 5", "5*3", "*p<0,05; **p<0,01") stay literal; "\*" is an escaped asterisk.
INLINE = re.compile(r"(?<![\w*])(\*\*(?=[^\s*])[^*]+(?<=\S)\*\*|\*(?=[^\s*])[^*]+(?<=\S)\*)(?![\w*])")
CTRL = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff]")
ESC_STAR, ESC_PIPE = "\ue000", "\ue001"
CODE = re.compile(r"`([^`\n]+)`")
QUOTE = re.compile(r"^>\s?(.*)")
IMAGE = re.compile(r"^!\[([^\]]*)\]\((.+)\)\s*$")
BULLET = re.compile(r"^[-*]\s+")
NUMBERED = re.compile(r"^(\d+)\.\s+")
PNG_SIG = b"\x89PNG\r\n\x1a\n"
OUR_STYLES = ("Normal", "Heading1", "Heading2", "Heading3", "Heading4", "Caption", "FigureCaption", "Figure",
              "TableNote", "ListParagraph")


class _Ctx:
    """State collected while the body is written: images, numbered lists, TOC."""

    def __init__(self, base_dir: Path | None, text_w: int, text_h: int):
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.text_w, self.text_h = text_w, text_h  # twips
        self.images: list[bytes] = []
        self.num_starts: list[int] = []  # one start value per numbered list; numId = index + 2
        self.toc = False


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


def template_from_project(project: Path | None) -> Path | None:
    if project is None:
        return None
    inst = projectcfg.read_project_yaml(project).get("institution", {})
    rel = inst.get("template", "") if isinstance(inst, dict) else ""
    if not rel:
        return None
    p = Path(rel)
    return p if p.is_absolute() else Path(project) / p


def png_size(data: bytes) -> tuple[int, int]:
    if data[:8] != PNG_SIG or data[12:16] != b"IHDR":
        raise ValueError("not a PNG file (only PNG images are supported)")
    w, h = int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
    if not w or not h:
        raise ValueError("PNG with zero width or height")
    return w, h


def absolutize_images(text: str, base: Path) -> str:
    def rep(m: re.Match) -> str:
        src = m.group(2).strip()
        return m.group(0) if Path(src).is_absolute() else f"![{m.group(1)}]({(Path(base) / src).as_posix()})"
    return re.sub(r"(?m)^!\[([^\]]*)\]\((.+)\)[ \t]*$", rep, text)


def load_template(path: Path) -> tuple[str, str]:
    """(styles.xml, page setup) of an institution template .docx; header/footer references are dropped."""
    if not Path(path).is_file():
        raise ValueError(f"template not found: {path}")
    try:
        with zipfile.ZipFile(path) as z:
            styles = z.read("word/styles.xml").decode("utf-8")
            doc = z.read("word/document.xml").decode("utf-8")
    except (zipfile.BadZipFile, KeyError) as e:
        raise ValueError(f"template {path} is not a usable .docx: {e}") from e
    sects = re.findall(r"<w:sectPr\b[^>]*>.*?</w:sectPr>", doc, re.S)
    if not sects:
        raise ValueError(f"template {path} has no page setup (w:sectPr) in word/document.xml")
    sect = re.sub(r"<w:(?:headerReference|footerReference|printerSettings)\b[^>]*/>", "", sects[-1])
    sect = re.sub(r'\s(?!w:)[A-Za-z][\w.-]*:[\w.-]+="[^"]*"', "", sect)  # attributes of undeclared namespaces
    return styles, sect


def _page(sect: str) -> tuple[int, int]:
    """Text-block width and height (twips) from a w:sectPr."""
    def attr(tag: str, name: str, default: int) -> int:
        m = re.search(rf'<w:{tag}\b[^>]*\bw:{name}="(\d+)"', sect)
        return int(m.group(1)) if m else default
    w, h = attr("pgSz", "w", A4[0]), attr("pgSz", "h", A4[1])
    return (w - attr("pgMar", "left", 1701) - attr("pgMar", "right", 1134),
            h - attr("pgMar", "top", 1134) - attr("pgMar", "bottom", 1134))


def _merge_styles(tpl: str, ours: str) -> str:
    have = set(re.findall(r'w:styleId="([^"]+)"', tpl))
    extra = [s for s in re.findall(r"<w:style\b.*?</w:style>", ours, re.S)
             if re.search(r'w:styleId="([^"]+)"', s).group(1) not in have]
    k = tpl.rfind("</w:styles>")
    if k < 0:
        raise ValueError("template styles.xml has no </w:styles>")
    return tpl[:k] + "".join(extra) + tpl[k:]


def _runs(text: str, bold_all: bool = False) -> str:
    """Runs for text; `code` spans lose their backticks and become monospace runs."""
    out = []
    for idx, part in enumerate(CODE.split(text)):
        if not part:
            continue
        if idx % 2 == 1:
            bold = "<w:b/>" if bold_all else ""
            out.append(f'<w:r><w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas"/>{bold}</w:rPr>'
                       f'<w:t xml:space="preserve">{html.escape(part)}</w:t></w:r>')
        else:
            out.append(_emph_runs(part, bold_all))
    return "".join(out)


def _emph_runs(text: str, bold_all: bool = False) -> str:
    out = []
    for idx, part in enumerate(INLINE.split(text.replace("\\*", ESC_STAR))):
        if not part:
            continue
        emph = idx % 2 == 1
        bold = bold_all or (emph and part.startswith("**"))
        italic = emph and not bold and part.startswith("*")
        body = part.strip("*") if emph else part
        props = ("<w:b/>" if bold else "") + ("<w:i/>" if italic else "")
        out.append(f'<w:r><w:rPr>{props}</w:rPr><w:t xml:space="preserve">'
                   f'{html.escape(body.replace(ESC_STAR, "*"))}</w:t></w:r>')
    return "".join(out)


def _p(text: str, style: str | None = None, indent: bool = False, quote: bool = False, num: int | None = None) -> str:
    ppr = f'<w:pStyle w:val="{style}"/>' if style else ""
    if num is not None:
        ppr += f'<w:numPr><w:ilvl w:val="0"/><w:numId w:val="{num}"/></w:numPr>'
    if indent:
        ppr += '<w:ind w:left="567" w:hanging="283"/>'
    if quote:
        ppr += '<w:ind w:left="567"/>'
    return f"<w:p><w:pPr>{ppr}</w:pPr>{_runs(text)}</w:p>"


def _table(rows: list[str]) -> str:
    cells = [[c.strip().replace(ESC_PIPE, "|") for c in r.strip().replace("\\|", ESC_PIPE).strip("|").split("|")]
             for r in rows]
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


def _toc() -> str:
    return ('<w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/></w:r>'
            '<w:r><w:instrText xml:space="preserve"> TOC \\o "1-3" \\h \\z \\u </w:instrText></w:r>'
            '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
            '<w:r><w:t xml:space="preserve">Update field to build the table of contents / '
            'Cập nhật trường (Update field) để tạo mục lục</w:t></w:r>'
            '<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>')


def _drawing(n: int, cx: int, cy: int, name: str) -> str:
    return (f'<w:p><w:pPr><w:pStyle w:val="Figure"/></w:pPr><w:r><w:drawing>'
            f'<wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/>'
            f'<wp:docPr id="{n}" name="Picture {n}" descr="{html.escape(name, quote=True)}"/>'
            '<wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
            '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            f'<pic:pic><pic:nvPicPr><pic:cNvPr id="{n}" name="image{n}.png"/><pic:cNvPicPr/></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="rIdImg{n}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
            '</a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>')


def _image(src: str, ctx: _Ctx) -> str:
    path = Path(src.strip())
    if not path.is_absolute():
        path = ctx.base_dir / path
    if not path.is_file():
        raise ValueError(f"image not found: {src.strip()}")
    data = path.read_bytes()
    w, h = png_size(data)
    cx = ctx.text_w * EMU_PER_TWIP
    cy = cx * h // w
    max_cy = ctx.text_h * EMU_PER_TWIP * 9 // 10
    if cy > max_cy:
        cx, cy = cx * max_cy // cy, max_cy
    ctx.images.append(data)
    return _drawing(len(ctx.images), cx, cy, path.name)


def _body(md_text: str, ctx: _Ctx | None = None) -> str:
    ctx = ctx or _Ctx(None, *_page(""))
    lines = [COMMENT.sub("", ln).rstrip() for ln in CTRL.sub("", md_text).splitlines()]
    out, i, after_table, prev_numbered = [], 0, False, False
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i])
                i += 1
            out.append(_table(rows))
            after_table, prev_numbered = True, False
            continue
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        numbered = False
        if not ln.strip():
            after_table = False
        elif ln.strip() == "\\newpage":
            out.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
        elif ln.strip() == "{TOC}":
            out.append(_toc())
            ctx.toc = True
        elif m := re.match(r"^(#{1,4})\s+(.*)", ln):
            out.append(_p(m.group(2), f"Heading{len(m.group(1))}"))
        elif m := IMAGE.match(ln.strip()):
            out.append(_image(m.group(2), ctx))
            if m.group(1).strip():
                out.append(_p(m.group(1).strip(), "FigureCaption"))
        elif CAPTION.match(ln) and nxt.startswith("|"):
            out.append(_p(ln, "Caption"))
        elif after_table and NOTE.match(ln):
            out.append(_p(ln, "TableNote"))
        elif QUOTE.match(ln):
            out.append(_p(QUOTE.match(ln).group(1), quote=True))
        elif BULLET.match(ln):
            out.append(_p(BULLET.sub("", ln), "ListParagraph", num=1))
        elif m := NUMBERED.match(ln):
            if not prev_numbered:
                ctx.num_starts.append(int(m.group(1)))
            out.append(_p(ln[m.end():], "ListParagraph", num=len(ctx.num_starts) + 1))
            numbered = True
        else:
            out.append(_p(ln))
        prev_numbered = numbered
        i += 1
    return "".join(out)


def _numbering(starts: list[int]) -> str:
    def abstract(aid: int, fmt: str, text: str) -> str:
        return (f'<w:abstractNum w:abstractNumId="{aid}"><w:multiLevelType w:val="singleLevel"/>'
                f'<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="{fmt}"/><w:lvlText w:val="{text}"/>'
                '<w:lvlJc w:val="left"/><w:pPr><w:ind w:left="567" w:hanging="283"/></w:pPr></w:lvl></w:abstractNum>')
    nums = '<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>'
    for k, start in enumerate(starts):
        nums += (f'<w:num w:numId="{k + 2}"><w:abstractNumId w:val="1"/>'
                 f'<w:lvlOverride w:ilvl="0"><w:startOverride w:val="{start}"/></w:lvlOverride></w:num>')
    return f"{XML_HEAD}<w:numbering {W}>" + abstract(0, "bullet", "–") + abstract(1, "decimal", "%1.") + nums + "</w:numbering>"


def _footer() -> str:
    return (f"{XML_HEAD}<w:ftr {DOC_NS}><w:p><w:pPr><w:jc w:val=\"center\"/></w:pPr>"
            '<w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
            '<w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>1</w:t></w:r>'
            '<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p></w:ftr>')


def _settings(toc: bool) -> str:
    return f"{XML_HEAD}<w:settings {W}>" + ('<w:updateFields w:val="true"/>' if toc else "") + "</w:settings>"


def _styles(s: dict) -> str:
    font, sz = html.escape(s["font"]), int(round(s["size_pt"] * 2))
    line = int(round(240 * s["line_spacing"]))
    fonts = f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}" w:cs="{font}" w:eastAsia="{font}"/>'

    def style(sid, name, extra_ppr="", extra_rpr=""):
        return (f'<w:style w:type="paragraph" w:styleId="{sid}"><w:name w:val="{name}"/><w:basedOn w:val="Normal"/>'
                f"<w:pPr>{extra_ppr}</w:pPr><w:rPr>{extra_rpr}</w:rPr></w:style>")
    return (f"{XML_HEAD}<w:styles {W}>"
            f'<w:docDefaults><w:rPrDefault><w:rPr>{fonts}<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/></w:rPr></w:rPrDefault>'
            f'<w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="{line}" w:lineRule="auto"/><w:jc w:val="both"/></w:pPr>'
            f"</w:pPrDefault></w:docDefaults>"
            f'<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>'
            + style("Heading1", "heading 1", '<w:keepNext/><w:spacing w:before="240"/><w:jc w:val="center"/><w:outlineLvl w:val="0"/>', f'<w:b/><w:sz w:val="{sz + 4}"/>')
            + style("Heading2", "heading 2", '<w:keepNext/><w:spacing w:before="200"/><w:outlineLvl w:val="1"/>', f'<w:b/><w:sz w:val="{sz + 2}"/>')
            + style("Heading3", "heading 3", '<w:keepNext/><w:outlineLvl w:val="2"/>', "<w:b/><w:i/>")
            + style("Heading4", "heading 4", '<w:keepNext/><w:outlineLvl w:val="3"/>', "<w:i/>")
            + style("Caption", "caption", '<w:keepNext/><w:jc w:val="center"/>', "<w:b/>")
            + style("FigureCaption", "figure caption", '<w:spacing w:after="240"/><w:jc w:val="center"/>', "<w:b/>")
            + style("Figure", "figure", '<w:keepNext/><w:jc w:val="center"/>')
            + style("TableNote", "table note", "", f'<w:i/><w:sz w:val="{max(sz - 4, 16)}"/>')
            + style("ListParagraph", "List Paragraph", '<w:spacing w:after="60"/>')
            + "</w:styles>")


def build(md_text: str, settings: dict, base_dir: Path | None = None, template: Path | None = None) -> bytes:
    if template is not None:
        tpl_styles, sect = load_template(Path(template))
    else:
        top, bottom, left, right = (int(round(x * 567)) for x in settings["margins_cm"])
        sect = (f'<w:sectPr><w:pgSz w:w="{A4[0]}" w:h="{A4[1]}"/><w:pgMar w:top="{top}" w:right="{right}" '
                f'w:bottom="{bottom}" w:left="{left}" w:header="709" w:footer="709" w:gutter="0"/></w:sectPr>')
    sect = re.sub(r"^<w:sectPr\b([^>]*)>",
                  lambda m: f'<w:sectPr{m.group(1)}><w:footerReference w:type="default" r:id="rId3"/>', sect, count=1)
    ctx = _Ctx(base_dir, *_page(sect))
    body = _body(md_text, ctx)
    styles = _styles(settings) if template is None else _merge_styles(tpl_styles, _styles(settings))
    image_rels = "".join(f'<Relationship Id="rIdImg{n}" Type="{RELS}/image" Target="media/image{n}.png"/>'
                         for n in range(1, len(ctx.images) + 1))
    files = {
        "[Content_Types].xml": XML_HEAD + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Default Extension="png" ContentType="image/png"/>'
            f'<Override PartName="/word/document.xml" ContentType="{CT}.document.main+xml"/>'
            f'<Override PartName="/word/styles.xml" ContentType="{CT}.styles+xml"/>'
            f'<Override PartName="/word/numbering.xml" ContentType="{CT}.numbering+xml"/>'
            f'<Override PartName="/word/footer1.xml" ContentType="{CT}.footer+xml"/>'
            f'<Override PartName="/word/settings.xml" ContentType="{CT}.settings+xml"/>'
            "</Types>",
        "_rels/.rels": XML_HEAD + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f'<Relationship Id="rId1" Type="{RELS}/officeDocument" Target="word/document.xml"/></Relationships>',
        "word/_rels/document.xml.rels": XML_HEAD + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f'<Relationship Id="rId1" Type="{RELS}/styles" Target="styles.xml"/>'
            f'<Relationship Id="rId2" Type="{RELS}/numbering" Target="numbering.xml"/>'
            f'<Relationship Id="rId3" Type="{RELS}/footer" Target="footer1.xml"/>'
            f'<Relationship Id="rId4" Type="{RELS}/settings" Target="settings.xml"/>'
            f"{image_rels}</Relationships>",
        "word/document.xml": f"{XML_HEAD}<w:document {DOC_NS}><w:body>{body}{sect}</w:body></w:document>",
        "word/styles.xml": styles,
        "word/numbering.xml": _numbering(ctx.num_starts),
        "word/footer1.xml": _footer(),
        "word/settings.xml": _settings(ctx.toc),
    }
    for n, data in enumerate(ctx.images, 1):
        files[f"word/media/image{n}.png"] = data
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, content in files.items():
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, content)
    return buf.getvalue()


FINAL_NAMES = ("thesis.docx", "manuscript.docx", "case-report.docx", "review.docx", "response-letter.docx")


def final_export_problems(output: Path, project: Path | None = None) -> list[str]:
    """Reasons writing `output` is refused: it is <project>/out/<thesis|manuscript|case-report|review>.docx (trailing
    dots and spaces ignored, as Windows does) and gate.final_problems is not empty for it. The project
    is the folder holding out/ when it has project.yaml, and --project when given."""
    out = Path(output).resolve()
    name = out.name.rstrip(". ").lower()
    if name not in FINAL_NAMES or out.parent.name.rstrip(". ").lower() != "out":
        return []
    import gate  # lazy: gate pulls in the drafts and audit modules
    why: list[str] = []
    for proj in dict.fromkeys(p.resolve() for p in (out.parent.parent, project) if p is not None):
        if (proj / "project.yaml").is_file():
            why += [w for w in gate.final_problems(proj, name) if w not in why]
    return why


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+", metavar="PATH", help="input .md file(s), then the output .docx")
    ap.add_argument("--project")
    ap.add_argument("--template")
    a = ap.parse_args(argv)
    if len(a.paths) < 2:
        print("build_docx: give at least one input .md and the output .docx", file=sys.stderr)
        return 2
    *inputs, output = a.paths
    if not output.lower().endswith(".docx"):
        print(f"build_docx: the output must end in .docx: {output}", file=sys.stderr)
        return 2
    try:
        why = final_export_problems(Path(output), Path(a.project) if a.project else None)
    except (OSError, ValueError) as e:
        why = [f"the G4 check could not run ({type(e).__name__}: {e})"]
    if why:
        print(f"build_docx: {output} is a final export and cannot be written: {'; '.join(why)}. Run /orchestra:audit, "
              "fix every block, then the author opens G4 (gate.py open <project> G4 --by NAME). / Xuất bản cuối cần "
              "cổng G4 mở.", file=sys.stderr)
        return 1
    try:
        project = Path(a.project) if a.project else None
        template = Path(a.template) if a.template else template_from_project(project)
        parts = [absolutize_images(Path(f).read_text(encoding="utf-8"), Path(f).resolve().parent) for f in inputs]
        data = build("\n\n".join(parts), settings_from_project(project), template=template)
        Path(output).write_bytes(data)
    except (OSError, ValueError) as e:
        print(f"build_docx: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    print(f"build_docx: wrote {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
