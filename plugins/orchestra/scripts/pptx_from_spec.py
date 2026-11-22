#!/usr/bin/env python3
"""Build an editable .pptx from a JSON slide spec, optionally inside an institution's template.

  python pptx_from_spec.py SPEC OUT [--project DIR]

With "template": the template's masters, backgrounds and layouts are kept; its own sample
slides are removed; each spec slide uses the layout named in the spec (or a sensible
default). Without a template: a clean 16:9 deck drawn from the theme colours and fonts.
"size_cm": [w, h] sets the slide size (a one-slide poster); fonts and margins scale with the width.

Diagrams (trial schema, CONSORT, timelines) are built from native shapes and connectors;
charts are native PowerPoint charts (bar, column, line, Kaplan-Meier, forest), so the presenter
can edit them. Chart and diagram slides may take "data": the path of a figures.py F<n>.data.json.

--project DIR renders every string in the spec ({{R-A1-001}}, {{R-A1-001.ci}} ...) from the
results ledger in the project language (or the spec's "lang"). An unknown id exits 2 and lists
the known ids. Paths in the spec resolve against the spec's folder.
Exit codes: 0 built; 2 usage error, bad spec, unreadable input, unknown placeholder or missing
python-pptx. Spec reference: references/presenting/pptx-spec.md.

Adapted from grand-rounds 0.2.0 (pptx_from_spec.py, MIT, same owner). Requires python-pptx.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):  # Windows consoles default to cp1252
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    from lxml import etree  # python-pptx depends on lxml
    from pptx import Presentation
    from pptx.chart.data import CategoryChartData, XyChartData
    from pptx.dml.color import RGBColor
    from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION, XL_MARKER_STYLE
    from pptx.enum.dml import MSO_LINE
    from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
    from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
    from pptx.oxml.ns import qn
    from pptx.util import Cm, Emu, Inches, Pt
except ImportError:
    print("pptx_from_spec needs python-pptx: python -m pip install python-pptx", file=sys.stderr)
    sys.exit(2)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crolib import numfmt, projectcfg  # noqa: E402
import render_results  # noqa: E402

DEFAULT_THEME = {
    "fonts": {"heading": "Arial", "body": "Arial"},
    "colors": {"primary": "#0F5E7A", "ink": "#1B2430", "muted": "#66707C", "line": "#C9CED4",
               "intervention": "#C8372D", "control": "#56677F", "bg": "#FFFFFF", "title_text": "#1B2430"},
    "type_pt": {"title": 32, "body": 20, "small": 14, "footer": 11},
}
LABELS = {
    "vi": {"at_risk": "Số người còn nguy cơ", "event_free": "Xác suất chưa có biến cố"},
    "en": {"at_risk": "Number at risk", "event_free": "Event-free probability"},
}
GROUP_COLORS = ["primary", "intervention", "control", "#2E7D5B", "#B8860B", "#7B4EA3"]
BASE_W_IN = 13.333


class SpecError(Exception):
    """A problem with the spec or the files it names; the CLI reports it and exits 2."""


def rgb(hexstr: str) -> RGBColor:
    return RGBColor.from_string(hexstr.lstrip("#").upper())


class Builder:
    def __init__(self, spec: dict, base: Path, lang: str = "en"):
        self.spec, self.base, self.lang = spec, base, lang
        self.theme = merge(DEFAULT_THEME, spec.get("theme", {}))
        tpl = spec.get("template")
        if tpl:
            self.prs = Presentation(str(base / tpl))
            self._drop_existing_slides()
        else:
            self.prs = Presentation()
            self.prs.slide_width, self.prs.slide_height = Inches(BASE_W_IN), Inches(7.5)
        self.k = 1.0  # scale for margins, fonts and line widths; only a custom size changes it
        size = spec.get("size_cm")
        if size is not None:
            if (not isinstance(size, (list, tuple)) or len(size) != 2
                    or not all(isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0 for v in size)):
                raise SpecError('"size_cm" must be [width, height] in centimetres')
            if max(size) > 142:
                raise SpecError('"size_cm" is at most 142 cm per side (the PowerPoint limit is 142.24 cm); '
                                f"got {size[0]} x {size[1]}")
            self.prs.slide_width, self.prs.slide_height = Cm(size[0]), Cm(size[1])
            self.k = size[0] / 2.54 / BASE_W_IN
        self.W, self.H = self.prs.slide_width, self.prs.slide_height
        # Layouts of every master, addressable by name ("Title and Content"; first match wins)
        # or by part name ("slideLayout13"), which is unambiguous when masters share names.
        self.layout_names = {}
        for master in self.prs.slide_masters:
            for lay in master.slide_layouts:
                self.layout_names.setdefault(lay.name, lay)
                self.layout_names[Path(lay.part.partname).stem] = lay

    # ------------------------------------------------------------ helpers
    def I(self, v: float):  # noqa: E743  (scaled inches)
        return Inches(v * self.k)

    def lw(self, pt: float):  # scaled line width
        return Pt(pt * self.k)

    def tp(self, name: str) -> float:
        return self.theme["type_pt"][name]

    def _drop_existing_slides(self):
        sldIdLst = self.prs.slides._sldIdLst
        for sldId in list(sldIdLst):
            self.prs.part.drop_rel(sldId.rId)
            sldIdLst.remove(sldId)

    def color(self, key: str) -> RGBColor:
        c = self.theme["colors"]
        return rgb(c.get(key, key if key.startswith("#") else c["ink"]))

    def layout(self, kind: str, wanted: str | None):
        if wanted and wanted in self.layout_names:
            return self.layout_names[wanted]
        names = self.spec.get("layouts", {})
        if names.get(kind) in self.layout_names:
            return self.layout_names[names[kind]]
        if not self.spec.get("template"):
            return self.prs.slide_layouts[6]  # blank in the default template
        prefs = {"title": ["Title Slide"], "closing": ["Title Slide"],
                 "content": ["Title Only", "Title and Content"]}.get(kind, ["Title Only", "Title and Content"])
        for p in prefs:
            if p in self.layout_names:
                return self.layout_names[p]
        return self.prs.slide_layouts[0]

    def font(self, run, size=None, bold=None, color=None, heading=False, italic=None):
        f = run.font
        f.name = self.theme["fonts"]["heading" if heading else "body"]
        if size:
            f.size = Pt(size * self.k)
        if bold is not None:
            f.bold = bold
        if italic is not None:
            f.italic = italic
        if color:
            f.color.rgb = self.color(color)

    def apply_style(self, shape, key: str, default: dict | None = None):
        """Format every run of a placeholder with spec["styles"][key] (or `default`)."""
        st = self.spec.get("styles", {}).get(key, default)
        if not st:
            return
        if st.get("box_in"):  # move the placeholder, as the template's own slides do
            shape.left, shape.top, shape.width, shape.height = (Inches(v) for v in st["box_in"])
        if st.get("anchor"):
            shape.text_frame.vertical_anchor = {"top": MSO_ANCHOR.TOP, "middle": MSO_ANCHOR.MIDDLE,
                                                "bottom": MSO_ANCHOR.BOTTOM}[st["anchor"]]
        for p in shape.text_frame.paragraphs:
            if st.get("align"):
                p.alignment = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT}[st["align"]]
            for r in p.runs:
                if st.get("caps"):
                    r.text = r.text.upper()
                self.font(r, st.get("size"), st.get("bold"), st.get("color"), heading=True, italic=st.get("italic"))
                if st.get("font"):
                    r.font.name = st["font"]

    def textbox(self, x, y, w, h, text, size, color="ink", bold=False, align=None, italic=False,
                anchor=MSO_ANCHOR.TOP, heading=False, name=None):
        tb = self.cur.shapes.add_textbox(x, y, w, h)
        if name:
            tb.name = name
        tf = tb.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = anchor
        tf.margin_left = tf.margin_right = Emu(0)
        lines = text if isinstance(text, list) else [text]
        for i, line in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = align if align is not None else PP_ALIGN.LEFT
            r = p.add_run()
            r.text = line
            self.font(r, size, bold, color, heading, italic)
        return tb

    def title(self, s: dict):
        t = s.get("title", "")
        ph = self.cur.shapes.title
        size = self.tp("title")
        if ph is not None:
            ph.text_frame.text = t
            self.apply_style(ph, "title", None if self.spec.get("template") else
                             {"size": size, "bold": True, "color": "title_text"})
            return ph.top + ph.height
        self.textbox(self.I(0.7), self.I(0.45), self.W - self.I(1.4), self.I(1.2), t, size, "title_text",
                     True, heading=True, name="Title")
        return self.I(1.75)

    def content_box(self, top):
        top = max(top + self.I(0.25), self.I(1.6))
        bottom = self.H - self.I(float(self.spec.get("footer_reserve_in", 0.85)))
        return self.I(0.7), top, self.W - self.I(1.4), bottom - top

    def footer(self, s: dict, idx: int):
        cite = s.get("cite", self.spec.get("cite", ""))
        size = self.tp("footer")
        y = self.H - self.I(float(self.spec.get("footer_y_from_bottom_in", 0.55)))
        if cite:
            self.textbox(self.I(0.7), y, self.W - self.I(2.6), self.I(0.4), cite, size, "muted", italic=True,
                         name="Source")
        if self.spec.get("page_numbers", True):
            self.textbox(self.W - self.I(1.7), y, self.I(1.0), self.I(0.4), str(idx), size, "muted",
                         align=PP_ALIGN.RIGHT, name="Page")

    def notes(self, s):
        if s.get("notes"):
            self.cur.notes_slide.notes_text_frame.text = s["notes"]

    def image(self, path, x, y, w, h, alt=""):
        from PIL import Image  # python-pptx depends on Pillow
        p = self.base / path
        try:
            with Image.open(p) as im:
                iw, ih = im.size
        except OSError as e:
            raise SpecError(f"cannot read image {path}: {e}")
        scale = min(w / iw, h / ih)
        pw, ph = int(iw * scale), int(ih * scale)
        pic = self.cur.shapes.add_picture(str(p), x + (w - pw) // 2, y + (h - ph) // 2, pw, ph)
        pic._element.nvPicPr.cNvPr.set("descr", alt or Path(path).stem)
        return pic

    def bullets(self, items, x, y, w, h, size=None):
        size = size or self.tp("body")
        tb = self.cur.shapes.add_textbox(x, y, w, h)
        tb.name = "Body"
        tf = tb.text_frame
        tf.word_wrap = True
        for i, it in enumerate(items):
            it = it if isinstance(it, dict) else {"text": it}
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.level = it.get("level", 0)
            p.space_after = Pt(8 * self.k)
            pPr = p._p.get_or_add_pPr()
            pPr.set("marL", str(int(self.I(0.3 + 0.35 * p.level))))
            pPr.set("indent", str(int(-self.I(0.28))))
            bu = etree.SubElement(pPr, qn("a:buChar"))  # after spcAft: schema order holds
            bu.set("char", "•")
            r = p.add_run()
            r.text = it["text"]
            self.font(r, size - 2 * p.level, it.get("bold", False), it.get("color", "ink"))
        return tb

    # ------------------------------------------------------------ slide types
    def s_title(self, s, idx):
        self.cur = self.prs.slides.add_slide(self.layout("title", s.get("layout")))
        phs = {p.placeholder_format.type: p for p in self.cur.placeholders}
        t = self.cur.shapes.title
        if t is not None:
            t.text_frame.text = s.get("title", "")
            self.apply_style(t, "title_slide")
        else:
            self.textbox(self.I(0.9), self.I(2.2), self.W - self.I(1.8), self.I(2.0), s.get("title", ""), 40,
                         "title_text", True, heading=True, name="Title")
        sub = "\n".join(x for x in (s.get("subtitle"), s.get("presenter")) if x)
        body = next((p for k, p in phs.items() if p != t), None)
        if body is not None and sub:
            body.text_frame.text = sub
            self.apply_style(body, "subtitle")
        elif sub:
            self.textbox(self.I(0.9), self.I(4.5), self.W - self.I(1.8), self.I(1.4), sub.split("\n"), 22, "primary")
        for p in list(self.cur.placeholders):
            if p != t and not p.text_frame.text.strip():
                p._element.getparent().remove(p._element)

    s_closing = s_title

    def s_bullets(self, s, idx):
        self.cur = self.prs.slides.add_slide(self.layout("content", s.get("layout")))
        x, y, w, h = self.content_box(self.title(s))
        self._clear_body_placeholders()
        self.bullets(s.get("bullets", []), x, y, w, h)

    def s_figure(self, s, idx):
        self.cur = self.prs.slides.add_slide(self.layout("content", s.get("layout")))
        x, y, w, h = self.content_box(self.title(s))
        self._clear_body_placeholders()
        credit_h = self.I(0.35) if s.get("credit") else 0
        if s.get("labels"):
            self.labelled_image(s, x, y, w, h - credit_h)
        else:
            self.image(s["image"], x, y, w, h - credit_h, s.get("alt", ""))
        if s.get("credit"):
            self.textbox(x, y + h - credit_h, w, credit_h, s["credit"], self.tp("small"), "muted",
                         italic=True, name="Credit")

    def labelled_image(self, s, x, y, w, h):
        """Picture in the middle, editable labels in columns either side, leader lines and dots.
        Same `labels` format as medical-figures/scripts/label_figure.py ("at" = fractions of the image)."""
        from PIL import Image
        with Image.open(self.base / s["image"]) as im:
            iw, ih = im.size
        ml, mr = s.get("margin", [0.5, 0.5])
        scale = min(w / ((ml + 1 + mr) * iw), h / ih)
        pw, ph = int(iw * scale), int(ih * scale)
        x0 = x + (w - int((ml + 1 + mr) * pw)) // 2
        px0 = x0 + int(ml * pw)
        pic = self.cur.shapes.add_picture(str(self.base / s["image"]), px0, y, pw, ph)
        pic._element.nvPicPr.cNvPr.set("descr", s.get("alt", Path(s["image"]).stem))
        size = s.get("label_pt", self.tp("small") + 2)
        line_h = Pt(size * 1.55 * self.k)
        for side in ("left", "right"):
            items = [lab for lab in s["labels"] if lab.get("side", "left") == side]
            if not items:
                continue
            ys = [y + int(lab["at"][1] * ph) for lab in items]
            order = sorted(range(len(ys)), key=lambda i: ys[i])
            v = [ys[i] for i in order]
            for i in range(len(v)):  # spread apart, then pull back inside the picture height
                v[i] = max(v[i], y + line_h // 2 if i == 0 else v[i - 1] + line_h)
            for i in range(len(v) - 1, -1, -1):
                v[i] = min(v[i], y + ph - line_h // 2 if i == len(v) - 1 else v[i + 1] - line_h)
            placed = [0] * len(ys)
            for k, i in enumerate(order):
                placed[i] = v[k]
            col_w = int((ml if side == "left" else mr) * pw) - self.I(0.15)
            for lab, ly in zip(items, placed):
                tx = px0 - self.I(0.15) - col_w if side == "left" else px0 + pw + self.I(0.15)
                tb = self.textbox(tx, ly - line_h // 2, col_w, line_h, lab["text"], size, "ink",
                                  align=PP_ALIGN.RIGHT if side == "left" else PP_ALIGN.LEFT,
                                  anchor=MSO_ANCHOR.MIDDLE, name=f"Label {lab['text']}")
                tb.text_frame.word_wrap = False
                tb.text_frame.margin_top = tb.text_frame.margin_bottom = Emu(0)
                ax = px0 - self.I(0.08) if side == "left" else px0 + pw + self.I(0.08)
                tx_pt, ty_pt = px0 + int(lab["at"][0] * pw), y + int(lab["at"][1] * ph)
                ln = self.cur.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, ax, ly, tx_pt, ty_pt)
                ln.line.color.rgb = rgb("#5F6B78")
                ln.line.width = self.lw(1)
                ln.name = f"Leader {lab['text']}"
                r = self.lw(4)
                d = self.cur.shapes.add_shape(MSO_SHAPE.OVAL, tx_pt - r, ty_pt - r, 2 * r, 2 * r)
                d.fill.solid()
                d.fill.fore_color.rgb = rgb("#1B2430")
                d.line.color.rgb = rgb("#FFFFFF")
                d.line.width = self.lw(1)
                d.name = f"Dot {lab['text']}"

    def s_figure_text(self, s, idx):
        self.cur = self.prs.slides.add_slide(self.layout("content", s.get("layout")))
        x, y, w, h = self.content_box(self.title(s))
        self._clear_body_placeholders()
        left = int(w * s.get("split", 0.58))
        credit_h = self.I(0.35) if s.get("credit") else 0
        self.image(s["image"], x, y, left - self.I(0.3), h - credit_h, s.get("alt", ""))
        if s.get("credit"):
            self.textbox(x, y + h - credit_h, left, credit_h, s["credit"], self.tp("small"), "muted",
                         italic=True, name="Credit")
        self.bullets(s.get("bullets", []), x + left, y, w - left, h)

    def s_big_number(self, s, idx):
        self.cur = self.prs.slides.add_slide(self.layout("content", s.get("layout")))
        x, y, w, h = self.content_box(self.title(s))
        self._clear_body_placeholders()
        nums = s.get("numbers", [])
        cw = w // max(1, len(nums))
        for i, n in enumerate(nums):
            cx = x + i * cw
            self.textbox(cx, y + self.I(0.6), cw - self.I(0.3), self.I(1.4), n["value"], 54,
                         n.get("color", "intervention"), True, name=f"Number {i + 1}")
            self.textbox(cx, y + self.I(2.0), cw - self.I(0.3), self.I(1.2), n.get("label", ""), 20, "muted",
                         name=f"Label {i + 1}")
        if s.get("bullets"):
            self.bullets(s["bullets"], x, y + self.I(3.3), w, h - self.I(3.3), 18)

    def s_table(self, s, idx):
        self.cur = self.prs.slides.add_slide(self.layout("content", s.get("layout")))
        x, y, w, h = self.content_box(self.title(s))
        self._clear_body_placeholders()
        self.table(x, y, w, s["columns"], s["rows"], s.get("col_widths"))

    def table(self, x, y, w, cols, rows, widths=None, name=None, row_h=0.45):
        shp = self.cur.shapes.add_table(len(rows) + 1, len(cols), x, y, w, self.I(row_h) * (len(rows) + 1))
        if name:
            shp.name = name
        tbl = shp.table
        for j, c in enumerate(cols):
            if widths:
                tbl.columns[j].width = int(w * widths[j] / sum(widths))
            self._cell(tbl.cell(0, j), str(c), True)
        for i, row in enumerate(rows, 1):
            for j, v in enumerate(row):
                self._cell(tbl.cell(i, j), str(v), False)
        return shp

    def _cell(self, cell, text, header):
        cell.text = text
        cell.fill.solid()
        cell.fill.fore_color.rgb = self.color("primary") if header else rgb("#FFFFFF")
        for p in cell.text_frame.paragraphs:
            for r in p.runs:
                self.font(r, self.tp("small") + 2, header, "#FFFFFF" if header else "ink")

    def s_diagram(self, s, idx):
        self.cur = self.prs.slides.add_slide(self.layout("content", s.get("layout")))
        x, y, w, h = self.content_box(self.title(s))
        self._clear_body_placeholders()
        data = self.load_data(s, idx) if s.get("data") else None
        if data is not None and data.get("kind") != "diagram":
            raise SpecError(f"slide {idx}: data file {s['data']} is a {data.get('kind')!r} chart, not a diagram")
        nodes = s.get("nodes") or (data or {}).get("nodes", [])
        from_data = not s.get("edges")
        edges = s.get("edges") or (data or {}).get("edges", [])
        geom = {n["id"]: n for n in nodes}
        shapes = {}
        styles = {"default": ("#FFFFFF", "primary", "ink"), "int": ("#FBEAE8", "intervention", "ink"),
                  "ctl": ("#EEF1F5", "control", "ink"), "primary": ("primary", "primary", "#FFFFFF"),
                  "muted": ("#F4F5F7", "line", "muted")}
        for n in nodes:
            fill, line, ink = styles.get(n.get("style", "default"), styles["default"])
            rounded = n.get("rounded", s.get("rounded", False))  # square corners unless the spec opts in
            kind = (MSO_SHAPE.OVAL if n.get("shape") == "circle"
                    else MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE)
            shp = self.cur.shapes.add_shape(kind, x + int(w * n["x"]), y + int(h * n["y"]), int(w * n["w"]), int(h * n["h"]))
            shp.name = f"Node {n['id']}"
            shp.fill.solid()
            shp.fill.fore_color.rgb = self.color(fill)
            shp.line.color.rgb = self.color(line)
            shp.line.width = self.lw(1.75)
            if kind == MSO_SHAPE.ROUNDED_RECTANGLE:
                shp.adjustments[0] = 0.12
            tf = shp.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_right = self.I(0.12)
            lines = n["text"] if isinstance(n["text"], list) else str(n["text"]).split("\n")
            for i, line_text in enumerate(lines):
                p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                p.alignment = PP_ALIGN.CENTER if n.get("align", "center") == "center" else PP_ALIGN.LEFT
                r = p.add_run()
                r.text = line_text
                self.font(r, n.get("size", self.tp("small") + 2), i == 0 and n.get("bold_first", True), ink)
            shapes[n["id"]] = shp
        for e in edges:
            if e["from"] not in shapes or e["to"] not in shapes:
                raise SpecError(f"slide {idx}: edge {e['from']} -> {e['to']} names an unknown node")
            a, b = shapes[e["from"]], shapes[e["to"]]
            if from_data:  # figures.py edges: its side numbers differ from ours, so use the geometry
                fs, ts, elbow = infer_sides(geom[e["from"]], geom[e["to"]])
            else:
                fs, ts, elbow = e.get("from_side", 3), e.get("to_side", 1), e.get("elbow")
            con = self.cur.shapes.add_connector(MSO_CONNECTOR.ELBOW if elbow else MSO_CONNECTOR.STRAIGHT, 0, 0, 0, 0)
            con.begin_connect(a, fs)
            con.end_connect(b, ts)
            con.line.color.rgb = self.color("primary")
            con.line.width = self.lw(2)
            ln = con.line._get_or_add_ln()
            tail = etree.SubElement(ln, qn("a:tailEnd"))
            tail.set("type", "triangle")

    # ------------------------------------------------------------ charts
    def load_data(self, s, idx) -> dict:
        """The `chart` object of a figures.py F<n>.data.json (plus the figure's `source`)."""
        rel = s["data"]
        try:
            with open(self.base / rel, encoding="utf-8-sig") as fh:
                d = json.load(fh)
        except (OSError, ValueError) as e:
            raise SpecError(f"slide {idx}: cannot read data file {rel}: {type(e).__name__}: {e}")
        ch = d.get("chart") if isinstance(d, dict) else None
        if not isinstance(ch, dict) or not ch.get("kind"):
            raise SpecError(f"slide {idx}: data file {rel} has no chart object with a kind")
        out = dict(ch)
        if d.get("source"):
            out["_source"] = d["source"]
        if isinstance(d.get("values"), list):
            out["_values"] = d["values"]
        return out

    def style_chart(self, chart, legend=False):
        chart.has_title = False
        chart.has_legend = legend
        if legend:
            chart.legend.position = XL_LEGEND_POSITION.TOP
            chart.legend.include_in_layout = False
            chart.legend.font.size = Pt(self.tp("small") * self.k)
        chart.font.size = Pt(self.tp("small") * self.k)
        chart.font.name = self.theme["fonts"]["body"]

    def axis_title(self, axis, text, size=None):
        if not text:
            return
        axis.has_title = True
        tf = axis.axis_title.text_frame
        tf.text = str(text)
        for r in tf.paragraphs[0].runs:
            r.font.size = Pt((size or self.tp("small")) * self.k)
            r.font.bold = False
            r.font.name = self.theme["fonts"]["body"]

    @staticmethod
    def plot_layout(chart, x, y, w, h):
        """Fix the inner plot area (fractions of the chart frame) so text columns can line up with it."""
        pa = chart._chartSpace.chart.plotArea
        old = pa.find(qn("c:layout"))
        if old is not None:
            pa.remove(old)
        lay = etree.Element(qn("c:layout"))
        ml = etree.SubElement(lay, qn("c:manualLayout"))
        for tag, val in (("layoutTarget", "inner"), ("xMode", "edge"), ("yMode", "edge"),
                         ("x", x), ("y", y), ("w", w), ("h", h)):
            etree.SubElement(ml, qn("c:" + tag)).set("val", str(val))
        pa.insert(0, lay)

    def alt_text(self, gf, text):
        gf._element.nvGraphicFramePr.cNvPr.set("descr", text)

    def s_chart(self, s, idx):
        self.cur = self.prs.slides.add_slide(self.layout("content", s.get("layout")))
        x, y, w, h = self.content_box(self.title(s))
        self._clear_body_placeholders()
        data = self.load_data(s, idx) if s.get("data") else None
        kind = s.get("chart") or (data["kind"] if data else "bar")
        if kind not in ("bar", "column", "line", "km", "forest"):
            raise SpecError(f"slide {idx}: unknown chart kind {kind!r}")
        if kind in ("km", "forest") and data is None:
            raise SpecError(f'slide {idx}: chart "{kind}" needs "data": the path of a figures.py F<n>.data.json')
        if data is not None and kind in ("km", "forest") and data["kind"] != kind:
            raise SpecError(f"slide {idx}: data file {s['data']} holds a {data['kind']!r} chart, not {kind!r}")
        credit = s.get("credit") or (data or {}).get("_source", "")
        credit_h = self.I(0.35) if credit else 0
        alt = s.get("alt") or s.get("title", "")
        if kind == "km":
            gf = self.chart_km(s, data, x, y, w, h - credit_h - (self.I(0.05) if credit else 0), idx)
        elif kind == "forest":
            gf = self.chart_forest(data, x, y, w, h - credit_h, idx)
        else:
            gf = self.chart_category(s, data, kind, x, y, w, h - credit_h, idx)
        self.alt_text(gf, alt)
        if credit:
            self.textbox(x, y + h - credit_h, w, credit_h, credit, self.tp("small"), "muted",
                         italic=True, name="Credit")

    def chart_category(self, s, data, kind, x, y, w, h, idx):
        src = dict(data or {})
        for key in ("categories", "series", "labels"):
            if key in s:
                src[key] = s[key]
        if not src.get("categories") or not src.get("series"):
            raise SpecError(f"slide {idx}: a {kind} chart needs categories and series")
        cd = CategoryChartData()
        cd.categories = src["categories"]
        for ser in src["series"]:
            cd.add_series(ser["name"], ser["values"])
        ctype = {"bar": XL_CHART_TYPE.BAR_CLUSTERED, "column": XL_CHART_TYPE.COLUMN_CLUSTERED,
                 "line": XL_CHART_TYPE.LINE_MARKERS}[kind]
        gf = self.cur.shapes.add_chart(ctype, x, y, w, h, cd)
        ch = gf.chart
        if ctype == XL_CHART_TYPE.BAR_CLUSTERED:
            ch.category_axis.reverse_order = True  # first category at the top, as listed
        self.style_chart(ch, legend=len(src["series"]) > 1)
        labels = src.get("labels")
        for plot in ch.plots:
            if labels:
                plot.has_data_labels = False
            else:
                plot.has_data_labels = True
                plot.data_labels.number_format = s.get("number_format", "0.0")
                plot.data_labels.number_format_is_linked = False
        for ser, spec_ser in zip(ch.series, src["series"]):
            fmt = ser.format
            if ctype == XL_CHART_TYPE.LINE_MARKERS:
                fmt.line.color.rgb = self.color(spec_ser.get("color", "primary"))
            else:
                fmt.fill.solid()
                fmt.fill.fore_color.rgb = self.color(spec_ser.get("color", "primary"))
        if labels:  # custom text per bar ("21,1% (16,1–27,1)"), on the first series; editable in PowerPoint
            first = ch.series[0]
            for i, text in enumerate(labels):
                dl = first.points[i].data_label
                dl.text_frame.text = str(text)
                for r in dl.text_frame.paragraphs[0].runs:
                    r.font.size = Pt(self.tp("small") * self.k)
                    r.font.name = self.theme["fonts"]["body"]
                dl.position = XL_LABEL_POSITION.OUTSIDE_END
            vals = [v for v in src["series"][0]["values"] if v is not None]
            if vals and min(vals) >= 0:
                ch.value_axis.minimum_scale = 0
                ch.value_axis.maximum_scale = max(vals) * 1.4 or 1
        return gf

    def chart_km(self, s, ch, x, y, w, h, idx):
        series = ch.get("series")
        if not series:
            raise SpecError(f"slide {idx}: Kaplan-Meier data has no series")
        pct = bool(s.get("percent"))
        mult = 100 if pct else 1
        cd = XyChartData()
        xmax = 0.0
        for ser in series:
            sr = cd.add_series(ser["name"])
            for px, py in ser["points"]:
                sr.add_data_point(px, round(py * mult, 6))
                xmax = max(xmax, px)
        ar = ch.get("at_risk")
        rows = (ar or {}).get("rows") or []
        times = (ar or {}).get("times") or []
        row_h = 0.28  # inches; at-risk table rows
        tbl_h = self.I(row_h) * (len(rows) + 1) if rows and times else 0
        gap = self.I(0.08) if tbl_h else 0
        gf = self.cur.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER_LINES_NO_MARKERS, x, y, w, h - tbl_h - gap, cd)
        chart = gf.chart
        legend = len(series) > 1
        self.style_chart(chart, legend=legend)
        px0, pw = 0.24, 0.74  # inner plot area, fractions of the frame width: the at-risk columns line up with it
        if tbl_h and len(times) > 1 and xmax:  # leave room right of the plot for half of the last column
            g = (times[-1] - times[-2]) / xmax
            pw = min(pw, (1 - px0 - 0.01) / (1 + g / 2))
        py0 = 0.13 if legend else 0.04  # the legend sits in the strip above the plot, off the curves
        self.plot_layout(chart, px0, py0, pw, 0.97 - py0 - 0.25)
        for i, (ser, spec_ser) in enumerate(zip(chart.plots[0].series, series)):
            ser.format.line.color.rgb = self.color(spec_ser.get("color", GROUP_COLORS[i % len(GROUP_COLORS)]))
            ser.format.line.width = self.lw(2.25)
            ser.smooth = False
        va, ca = chart.value_axis, chart.category_axis
        va.minimum_scale, va.maximum_scale = 0, (100 if pct else 1)
        va.major_unit = 20 if pct else 0.2
        va.has_major_gridlines = True
        va.major_gridlines.format.line.color.rgb = self.color("line")
        va.tick_labels.number_format = '0"%"' if pct else "0.0"
        va.tick_labels.number_format_is_linked = False
        ca.minimum_scale, ca.maximum_scale = 0, xmax
        ca.has_major_gridlines = False
        if len(times) > 1:
            step = times[1] - times[0]
            steps = [b - a for a, b in zip(times, times[1:])]
            # ticks line up with the at-risk columns; a last step up to a quarter longer (90 ... 270, 365) still counts
            if step > 0 and all(abs(d - step) < 1e-9 for d in steps[:-1]) and step - 1e-9 <= steps[-1] <= step * 1.25:
                ca.major_unit = step
        self.axis_title(ca, s.get("x_label") or ch.get("x_label"))
        self.axis_title(va, s.get("y_label") or ch.get("y_label") or LABELS[self.lang]["event_free"], self.tp("small") - 2)
        if tbl_h:
            cols = [LABELS[self.lang]["at_risk"]] + [self.num(t) for t in times]
            body = [[r["name"]] + [str(v) for v in r["n"]] for r in rows]
            widths = self.at_risk_widths(times, xmax, w, px0, pw)
            self.at_risk_table(x, y + h - tbl_h, int(sum(widths)), cols, body, widths, row_h)
        return gf

    def at_risk_table(self, x, y, w, cols, body, widths, row_h):
        """Compact native table: one line per row, no fill, time columns centred under their ticks."""
        shp = self.cur.shapes.add_table(len(body) + 1, len(cols), x, y, w, self.I(row_h) * (len(body) + 1))
        shp.name = "Number at risk"
        tbl = shp.table
        tbl.first_row = False
        tbl.horz_banding = False
        for j in range(len(cols)):
            tbl.columns[j].width = int(w * widths[j] / sum(widths))
        for i in range(len(body) + 1):
            tbl.rows[i].height = self.I(row_h)
            for j in range(len(cols)):
                text = str(cols[j] if i == 0 else body[i - 1][j])
                cell = tbl.cell(i, j)
                cell.text = text
                cell.fill.background()
                cell.margin_top = cell.margin_bottom = self.I(0.02)
                cell.margin_left = cell.margin_right = self.I(0.04)
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                for p in cell.text_frame.paragraphs:
                    p.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
                    for r in p.runs:
                        # the header label is the longest text in the narrow first column: 11 pt keeps it on one line
                        self.font(r, 11 if (i == 0 and j == 0) else 12, i == 0, "muted" if i == 0 else "ink")
        return shp

    @staticmethod
    def at_risk_widths(times, xmax, w, px0, pw):
        """Column widths (EMU, summing to the table width) that centre each time column on its x position
        in the plot area; the label column takes what is left of the first column (at least 10 % of w)."""
        if len(times) < 2 or not xmax:
            return [3] + [1] * len(times)
        c = [w * (px0 + pw * t / xmax) for t in times]
        mid = [(a + b) / 2 for a, b in zip(c, c[1:])]
        left = max(c[0] - (mid[0] - c[0]), 0.10 * w)
        right = min(c[-1] + (c[-1] - mid[-1]), float(w))
        edges = [left] + mid + [right]
        cols = [max(1.0, b - a) for a, b in zip(edges, edges[1:])]
        return [left] + cols

    def num(self, v) -> str:
        s = str(int(v)) if float(v) == int(v) else str(v)
        return s.replace(".", ",") if self.lang == "vi" else s

    def chart_forest(self, ch, x, y, w, h, idx):
        rows = ch.get("rows")
        if not rows:
            raise SpecError(f"slide {idx}: forest data has no rows")
        n = len(rows)
        null = ch.get("null", 1)
        log = bool(ch.get("log"))
        dec = int(ch.get("decimals", 2))
        label_w, text_w = int(w * 0.30), int(w * 0.18)
        chart_w = w - label_w - text_w
        py0, ph = 0.03, 0.80  # inner plot area, fractions of the chart frame height
        cd = XyChartData()
        est = cd.add_series("Estimate")
        for i, r in enumerate(rows):
            est.add_data_point(r["est"], n - i)  # first row at the top
        for i, r in enumerate(rows):
            sr = cd.add_series(f"CI {r['label']}")
            sr.add_data_point(r["lo"], n - i)
            sr.add_data_point(r["hi"], n - i)
        nl = cd.add_series("No-effect line")
        nl.add_data_point(null, 0.5)
        nl.add_data_point(null, n + 0.5)
        gf = self.cur.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER_LINES_NO_MARKERS, x + label_w, y, chart_w, h, cd)
        chart = gf.chart
        self.style_chart(chart, legend=False)
        self.plot_layout(chart, 0.03, py0, 0.94, ph)
        sers = list(chart.plots[0].series)
        e = sers[0]
        e.format.line.fill.background()
        e.marker.style = XL_MARKER_STYLE.SQUARE
        e.marker.size = max(2, min(72, round(8 * self.k)))
        e.marker.format.fill.solid()
        e.marker.format.fill.fore_color.rgb = self.color("primary")
        e.marker.format.line.color.rgb = self.color("primary")
        for ser in sers[1:-1]:
            ser.format.line.color.rgb = self.color("ink")
            ser.format.line.width = self.lw(1.75)
            ser.marker.style = XL_MARKER_STYLE.NONE
        nser = sers[-1]
        nser.format.line.color.rgb = self.color("muted")
        nser.format.line.width = self.lw(1.25)
        nser.format.line.dash_style = MSO_LINE.DASH
        nser.marker.style = XL_MARKER_STYLE.NONE
        for ser in sers:
            ser.smooth = False
        ca, va = chart.category_axis, chart.value_axis  # x axis, y axis
        va.minimum_scale, va.maximum_scale = 0.5, n + 0.5
        va.has_major_gridlines = False
        va.visible = False
        ca.has_major_gridlines = False
        self.axis_title(ca, ch.get("x_label"))
        if log:
            vals = [r[k] for r in rows for k in ("lo", "est", "hi")] + [null]
            if min(vals) <= 0:
                raise SpecError(f"slide {idx}: a log-scale forest plot needs positive values")
            ca.minimum_scale = 10 ** math.floor(math.log10(min(vals)))
            ca.maximum_scale = 10 ** math.ceil(math.log10(max(vals)))
            scaling = ca._element.find(qn("c:scaling"))
            lb = etree.Element(qn("c:logBase"))
            lb.set("val", "10")
            scaling.insert(0, lb)  # schema order: logBase, orientation, max, min
        # Native text columns: row labels at left, "est (lo–hi)" at right, aligned to the fixed plot area.
        row_h = h * ph / n
        label_pt = min(self.tp("small") + 2, row_h / 12700 * 0.6 / self.k)
        longest = max(len(r["label"]) for r in rows)
        label_pt = min(label_pt, (label_w - self.I(0.1)) / 12700 / self.k / (0.5 * max(1, longest)))
        # The estimate column prints what the figure prints: the row's own text, else values[i].text
        # (figures.py writes it there, in the ledger's precision), else a plain re-format.
        vals = ch.get("_values") or []
        texts = []
        for i, r in enumerate(rows):
            t = r.get("text")
            if not t and len(vals) == len(rows) and isinstance(vals[i], dict):
                t = vals[i].get("text")
            texts.append(t or (f"{numfmt.fmt(r['est'], dec, self.lang)} "
                               f"({numfmt.fmt_range(r['lo'], r['hi'], dec, self.lang)})"))
        text_pt = min(label_pt, (text_w - self.I(0.1)) / 12700 / self.k / (0.5 * max(1, max(len(t) for t in texts))))
        for i, r in enumerate(rows):
            cy = y + int(h * py0 + row_h * i)
            self.textbox(x, cy, label_w - self.I(0.1), int(row_h), r["label"], label_pt, "ink",
                         anchor=MSO_ANCHOR.MIDDLE, name=f"Forest label {i + 1}").text_frame.word_wrap = False
            self.textbox(x + label_w + chart_w + self.I(0.1), cy, text_w - self.I(0.1), int(row_h), texts[i],
                         text_pt, "ink", anchor=MSO_ANCHOR.MIDDLE,
                         name=f"Forest estimate {i + 1}").text_frame.word_wrap = False
        return gf

    def s_references(self, s, idx):
        self.cur = self.prs.slides.add_slide(self.layout("content", s.get("layout")))
        x, y, w, h = self.content_box(self.title(s))
        self._clear_body_placeholders()
        tb = self.cur.shapes.add_textbox(x, y, w, h)
        tf = tb.text_frame
        tf.word_wrap = True
        for i, ref in enumerate(s.get("items", [])):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.space_after = Pt(6 * self.k)
            r = p.add_run()
            r.text = f"{i + 1}. {ref}"
            self.font(r, self.tp("small"), color="ink")

    def _clear_body_placeholders(self):
        title = self.cur.shapes.title
        for p in list(self.cur.placeholders):
            if p != title and not (p.has_text_frame and p.text_frame.text.strip()):
                p._element.getparent().remove(p._element)

    # ------------------------------------------------------------ build
    def build(self, out: Path):
        slides = self.spec.get("slides")
        if not isinstance(slides, list) or not slides:
            raise SpecError('the spec needs a non-empty "slides" list')
        for idx, s in enumerate(slides, 1):
            if not isinstance(s, dict) or "type" not in s:
                raise SpecError(f"slide {idx}: needs a \"type\"")
            fn = getattr(self, "s_" + str(s["type"]).replace("-", "_"), None)
            if fn is None:
                raise SpecError(f"slide {idx}: unknown type {s['type']!r}")
            try:
                fn(s, idx)
            except (KeyError, TypeError, IndexError) as e:
                raise SpecError(f"slide {idx} ({s['type']}): bad or missing field {e!r}")
            if s["type"] not in ("title", "closing"):
                self.footer(s, idx)
            self.notes(s)
        out.parent.mkdir(parents=True, exist_ok=True)
        self.prs.save(str(out))
        return len(slides)


def infer_sides(a: dict, b: dict) -> tuple[int, int, bool]:
    """Connector sites (0 top, 1 left, 2 bottom, 3 right) from node geometry, for edges that carry none.

    A target clear of the source horizontally is joined side to side (elbow when the rows differ);
    otherwise bottom to top (target below) or top to bottom (target above)."""
    eps = 1e-6
    if b["x"] >= a["x"] + a["w"] - eps:
        sites = (3, 1)
    elif b["x"] + b["w"] <= a["x"] + eps:
        sites = (1, 3)
    elif b["y"] >= a["y"]:
        return 2, 0, False
    else:
        return 0, 2, False
    same_row = abs((a["y"] + a["h"] / 2) - (b["y"] + b["h"] / 2)) < 1e-3
    return sites[0], sites[1], not same_row


def merge(a: dict, b: dict) -> dict:
    out = copy.deepcopy(a)
    for k, v in (b or {}).items():
        out[k] = merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def render_spec(obj, by_id: dict, lang: str, probs: list, path: str = "spec"):
    """Render {{R-…}} placeholders in every string of the spec; collect problems as (path, message)."""
    if isinstance(obj, str):
        out, pr = render_results.render_text(obj, by_id, lang)
        probs.extend((path, p.partition(": ")[2]) for p in pr)
        return out
    if isinstance(obj, list):
        return [render_spec(v, by_id, lang, probs, f"{path}[{i}]") for i, v in enumerate(obj)]
    if isinstance(obj, dict):
        return {k: render_spec(v, by_id, lang, probs, f"{path}.{k}") for k, v in obj.items()}
    return obj


def load_ledger(project: Path) -> dict:
    with open(project / "ledgers" / "results-ledger.json", encoding="utf-8-sig") as fh:
        ledger = json.load(fh)
    results = ledger.get("results") if isinstance(ledger, dict) else None
    if not isinstance(results, list) or not all(isinstance(r, dict) and isinstance(r.get("id"), str) for r in results):
        raise ValueError("results ledger must be an object with a 'results' list of objects with string ids")
    return {r["id"]: r for r in results}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("out")
    ap.add_argument("--project", help="project folder: render {{R-…}} placeholders from its results ledger")
    a = ap.parse_args(argv)
    spec_path = Path(a.spec)
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8-sig"))
        if not isinstance(spec, dict):
            raise ValueError("the spec must be a JSON object")
        lang = spec.get("lang")
        if lang is not None and lang not in ("vi", "en"):
            raise SpecError('"lang" must be "vi" or "en"')
        if a.project:
            project = Path(a.project)
            by_id = load_ledger(project)
            lang = lang or ("vi" if projectcfg.output_lang(project).lower().startswith("vi") else "en")
            probs: list = []
            spec = render_spec(spec, by_id, lang, probs)
            if probs:
                for where, msg in probs:
                    print(f"pptx_from_spec: {where}: {msg}", file=sys.stderr)
                print("pptx_from_spec: known ids: " + (", ".join(sorted(by_id)) or "(none)"), file=sys.stderr)
                return 2
        else:
            left = sorted(set(re.findall(r"\{\{R-[^{}]*\}\}", json.dumps(spec, ensure_ascii=False))))
            if left:
                print(f"pptx_from_spec: warning: {len(left)} placeholder(s) left as typed because --project "
                      f"was not given: {', '.join(left)}", file=sys.stderr)
        n = Builder(spec, spec_path.parent, lang or "en").build(Path(a.out))
    except SpecError as e:
        print(f"pptx_from_spec: {e}", file=sys.stderr)
        return 2
    except (OSError, ValueError) as e:
        print(f"pptx_from_spec: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    print(f"{a.out}: {n} slides")
    return 0


if __name__ == "__main__":
    sys.exit(main())
