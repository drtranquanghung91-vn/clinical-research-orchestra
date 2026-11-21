#!/usr/bin/env python3
"""Print preflight for a built poster (E-PRINT): PDF page size and bleed, embedded fonts, effective image dpi,
overflowing boxes, alt text and small text.

  python poster_preflight.py PROJECT [--layout editorial|pathway|figure-led ...] [--spec poster.json]

Reads 07_present/poster/<layout>.pdf and <layout>.dom.html written by poster_build.py, and the poster size and
bleed from the spec (--spec, else the one poster_build recorded in <layout>.build.json, else
07_present/poster/poster.json). Findings go to stderr, one per line:
  E-PRINT block|warn <file>:<line>: <message>
A check that cannot run (missing PDF or DOM dump, a PDF the parser cannot read, a DOM dump without the
preflight markers) is a warn line "not checked by script (<reason>)", never a pass.
Summary per layout (stdout): poster_preflight: <layout>: <b> block, <w> warn.
Exit 0 = no block; 1 = at least one block; 2 = bad usage or spec.
Effective dpi = natural pixels / placed width in inches (< 100 block, < 150 warn). Small text: a warning below
24 pt x min(width_cm / 90, height_cm / 120) (the scale poster_build uses). SVG and PDF figures (inline svg or
<img src=*.svg|*.pdf>) are vector: no dpi finding; they are listed in a "vector figures (no dpi)" stdout line.
Figure text: for every figure drawn by figures.py, printed pt = font_pt x placed width / drawn width (the render
record of its profile in F<n>.data.json); a warn below the same threshold.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import zlib
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
import poster_build  # noqa: E402

LAYOUTS = poster_build.LAYOUTS
POSTER_DIR = Path("07_present") / "poster"
TOL_MM = 1.0
DPI_BLOCK = 100.0
DPI_WARN = 150.0
FONT_PT_90 = 24.0
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
NUM = rb"(-?\d+(?:\.\d+)?)"


# ---------------------------------------------------------------- PDF

def _object_stream_texts(data: bytes, every_flate: bool = False) -> list[bytes]:
    """Inflated contents of the PDF's object streams (/ObjStm); with every_flate, of every FlateDecode stream."""
    out = []
    for m in re.finditer(rb"stream\r?\n", data):
        start = m.end()
        head = data[max(0, m.start() - 400):m.start()]
        head = head[head.rfind(b"obj") + 3:] if b"obj" in head else head
        if b"FlateDecode" not in head:
            continue
        if not every_flate and b"/ObjStm" not in head:
            continue
        end = data.find(b"endstream", start)
        if end < 0:
            continue
        blob = data[start:end]
        try:
            d = zlib.decompressobj().decompress(blob, 16 * 1024 * 1024)
        except zlib.error:
            try:
                d = zlib.decompressobj().decompress(blob.rstrip(b"\r\n"), 16 * 1024 * 1024)
            except zlib.error:
                continue
        out.append(d)
    return out


def _texts(data: bytes, need) -> list[bytes]:
    """Plain PDF bytes first, then inflated object streams, then (last resort) every Flate stream, until
    need(texts) is true."""
    texts = [data]
    if need(texts):
        return texts
    texts += _object_stream_texts(data)
    if need(texts):
        return texts
    texts += _object_stream_texts(data, every_flate=True)
    return texts


def media_box(data: bytes):
    """(width_pt, height_pt) of the first page's /MediaBox, or None."""
    pat = re.compile(rb"/MediaBox\s*\[\s*" + NUM + rb"\s+" + NUM + rb"\s+" + NUM + rb"\s+" + NUM + rb"\s*\]")
    for t in _texts(data, lambda ts: any(pat.search(x) for x in ts)):
        m = pat.search(t)
        if m:
            x0, y0, x1, y1 = (float(v) for v in m.groups())
            return abs(x1 - x0), abs(y1 - y0)
    return None


def fonts(data: bytes):
    """(embedded, unembedded, found_any): font names from /FontDescriptor dictionaries; base fonts without any
    descriptor (e.g. the standard 14) count as unembedded."""
    desc_re = re.compile(r"<<((?:(?!<<|>>).)*?/Type\s*/FontDescriptor(?![\w])(?:(?!<<|>>).)*?)>>", re.S)
    font_re = re.compile(r"<<((?:(?!<<|>>).)*?/Type\s*/Font(?![\w])(?:(?!<<|>>).)*?)>>", re.S)
    embedded, missing = [], []
    seen = set()
    for t in [data] + _object_stream_texts(data):
        s = t.decode("latin-1")
        for m in desc_re.finditer(s):
            body = m.group(1)
            name = re.search(r"/FontName\s*/([^\s/\[\]<>()]+)", body)
            nm = name.group(1) if name else "(unnamed)"
            key = (nm, bool(re.search(r"/FontFile[23]?(?![\w])", body)))
            if key in seen:
                continue
            seen.add(key)
            (embedded if key[1] else missing).append(nm)
        for m in font_re.finditer(s):
            body = m.group(1)
            if "/FontDescriptor" in body or re.search(r"/Subtype\s*/(Type0|Type3|CIDFontType\d)", body):
                continue
            if re.search(r"/Subtype\s*/(Type1|TrueType|MMType1)", body):
                name = re.search(r"/BaseFont\s*/([^\s/\[\]<>()]+)", body)
                nm = name.group(1) if name else "(unnamed)"
                if (nm, False) not in seen:
                    seen.add((nm, False))
                    missing.append(nm)
    return embedded, missing, bool(embedded or missing)


# ---------------------------------------------------------------- DOM dump

class Dom(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, int | None]] = []
        self.images: list[dict] = []
        self.boxes: list[dict] = []
        self.figs: list[dict] = []  # first img / svg of every <figure data-fig>
        self._fig = None
        self._fig_done = False
        self.done = False
        self._head: list[int] = []  # index of the heading being read, per open h1/h2
        self._text: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = {k: (v if v is not None else "") for k, v in attrs}
        if tag == "body" and a.get("data-preflight") == "done":
            self.done = True
        box_i = None
        if tag == "figure" and a.get("data-fig"):
            self._fig = (a["data-fig"], a.get("data-fig-profile", "document"))
            self._fig_done = False
        if self._fig and not self._fig_done and (tag == "img" or tag == "svg"):
            self.figs.append({"id": self._fig[0], "profile": self._fig[1], "attrs": a, "line": self.getpos()[0],
                              "tag": tag})
            self._fig_done = True
        classes = a.get("class", "").split()
        if "box" in classes:
            self.boxes.append({"attrs": a, "headings": [], "line": self.getpos()[0]})
            box_i = len(self.boxes) - 1
        if tag == "img" or (tag == "svg" and "data-raster" in a):
            src = a.get("src") if tag == "img" else a.get("data-raster")
            self.images.append({"tag": tag, "attrs": a, "src": unquote((src or "").split("?")[0]),
                                "line": self.getpos()[0]})
        if tag in ("h1", "h2"):
            self._text = []
            self._head.append(1)
        if tag not in VOID:
            self.stack.append((tag, box_i))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_data(self, data):
        if self._head:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag == "figure":
            self._fig = None
        if tag in ("h1", "h2") and self._head:
            self._head.pop()
            txt = " ".join("".join(self._text).split())
            for _t, bi in self.stack:
                if bi is not None and txt:
                    self.boxes[bi]["headings"].append(txt)
        if tag in VOID:
            return
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break


def parse_dom(text: str) -> Dom:
    d = Dom()
    d.feed(text)
    d.close()
    return d


def _fnum(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _box_name(b: dict) -> str:
    a = b["attrs"]
    area = a.get("data-area") or a.get("class", "box").split()[0]
    heads = b["headings"]
    if area.startswith("col-") and heads:
        return f'{area} (sections: {"; ".join(heads)})'
    if heads:
        return f'"{heads[0]}"'
    return area


# ---------------------------------------------------------------- checks

class Report:
    def __init__(self, layout: str):
        self.layout = layout
        self.items: list[tuple[str, str, int, str]] = []
        self.vectors: list[str] = []

    def add(self, sev: str, file: str, line: int, msg: str):
        self.items.append((sev, file, line, msg))

    @property
    def blocks(self) -> int:
        return sum(1 for i in self.items if i[0] == "block")

    @property
    def warns(self) -> int:
        return sum(1 for i in self.items if i[0] == "warn")


def mm(pt: float) -> float:
    return pt * 25.4 / 72


def check_layout(layout: str, poster_dir: Path, size_cm, bleed_mm: float) -> Report:
    rep = Report(layout)
    pdf_path = poster_dir / f"{layout}.pdf"
    dom_path = poster_dir / f"{layout}.dom.html"
    W, H = size_cm[0] * 10, size_cm[1] * 10
    pdf_name, dom_name = pdf_path.name, dom_path.name

    # --- PDF
    if not pdf_path.is_file():
        rep.add("warn", pdf_name, 1, "not checked by script (no PDF: run poster_build.py with Chrome or Edge); "
                                    "page size, bleed and fonts are unchecked")
    else:
        try:
            data = pdf_path.read_bytes()
        except OSError as e:
            data = None
            rep.add("warn", pdf_name, 1, f"not checked by script (cannot read the PDF: {e})")
        if data is not None:
            box = media_box(data) if data.startswith(b"%PDF") else None
            if box is None:
                rep.add("warn", pdf_name, 1, "not checked by script (no readable /MediaBox: page size and bleed unchecked)")
            else:
                pw, ph = mm(box[0]), mm(box[1])
                ew, eh = W + 2 * bleed_mm, H + 2 * bleed_mm
                if abs(pw - ew) > TOL_MM or abs(ph - eh) > TOL_MM:
                    if bleed_mm > 0 and abs(pw - W) <= TOL_MM and abs(ph - H) <= TOL_MM:
                        rep.add("block", pdf_name, 1,
                                f"bleed requested ({bleed_mm:g} mm) but the page is the trim size {pw:.1f} x {ph:.1f} mm; "
                                f"it must be {ew:.1f} x {eh:.1f} mm")
                    else:
                        rep.add("block", pdf_name, 1,
                                f"page size {pw:.1f} x {ph:.1f} mm, expected {ew:.1f} x {eh:.1f} mm "
                                f"({W:.0f} x {H:.0f} mm + 2 x {bleed_mm:g} mm bleed, tolerance {TOL_MM:g} mm)")
            emb, missing, found = fonts(data)
            if missing:
                for nm in missing:
                    rep.add("block", pdf_name, 1, f"font not embedded: {nm}")
            elif not found:
                rep.add("warn", pdf_name, 1, "not checked by script (no /FontDescriptor found: fonts unchecked)")

    # --- DOM
    if not dom_path.is_file():
        rep.add("warn", dom_name, 1, "not checked by script (no DOM dump: image dpi, overflow, alt text and text size "
                                     "are unchecked)")
        return rep
    try:
        dom = parse_dom(dom_path.read_text(encoding="utf-8", errors="replace"))
    except Exception as e:  # noqa: BLE001
        rep.add("warn", dom_name, 1, f"not checked by script (DOM dump unreadable: {type(e).__name__})")
        return rep
    if not dom.done:
        rep.add("warn", dom_name, 1, "not checked by script (DOM dump has no preflight markers: rebuild with "
                                     "poster_build.py)")
        return rep

    for im in dom.images:
        a, line = im["attrs"], im["line"]
        name = Path(im["src"]).name or "(inline figure)"
        if im["tag"] == "img" and not a.get("alt", "").strip():
            rep.add("warn", dom_name, line, f"image {name} has no alt text")
        if im["tag"] == "svg":  # inline SVG (data-raster only names its PNG twin): vector, no pixel dpi
            rep.vectors.append(Path(im["src"]).stem + ".svg" if im["src"] else "(inline figure)")
            continue
        if Path(im["src"]).suffix.lower() in (".svg", ".pdf"):
            rep.vectors.append(name)
            continue
        nat, placed = _fnum(a.get("data-natural-w")), _fnum(a.get("data-placed-w-cm"))
        if not nat or not placed or placed <= 0:
            rep.add("warn", dom_name, line, f"image {name}: not checked by script (natural or placed size unknown; "
                                            "is the file missing?)")
            continue
        dpi = nat / (placed / 2.54)
        need = math.ceil(DPI_WARN * placed / 2.54)
        if dpi < DPI_BLOCK or dpi < DPI_WARN:
            sev = "block" if dpi < DPI_BLOCK else "warn"
            lim = DPI_BLOCK if sev == "block" else DPI_WARN
            rep.add(sev, dom_name, line,
                    f"image {name}: {nat:.0f} px over {placed:.1f} cm = {dpi:.0f} dpi (below {lim:.0f}); "
                    f"{need} px wide are needed for {DPI_WARN:.0f} dpi at this size")

    k = min(size_cm[0] / 90.0, size_cm[1] / 120.0)  # the same scale as poster_build
    thr = FONT_PT_90 * k
    fig_dir = poster_dir.parent / "figures"
    for fg in dom.figs:  # printed text size = recorded font_pt x placed width / drawn width
        data_path = fig_dir / f"{fg['id']}.data.json"
        if not data_path.is_file():
            continue  # not drawn by figures.py: nothing recorded to check
        placed = _fnum(fg["attrs"].get("data-placed-w-cm"))
        try:
            rec = json.loads(data_path.read_text(encoding="utf-8"))["render"][fg["profile"]]
            font_pt, drawn = float(rec["font_pt"]), float(rec["width_cm"])
        except (OSError, ValueError, KeyError, TypeError):
            rep.add("warn", dom_name, fg["line"],
                    f"figure {fg['id']}: not checked by script (no {fg['profile']} render size in "
                    f"{data_path.name}; rerun figures.py" + (" --profile poster)" if fg["profile"] == "poster" else ")"))
            continue
        if not placed or placed <= 0 or drawn <= 0:
            rep.add("warn", dom_name, fg["line"], f"figure {fg['id']}: not checked by script (placed width unknown)")
            continue
        printed = font_pt * placed / drawn
        if printed < thr - 0.05:
            rep.add("warn", dom_name, fg["line"],
                    f"figure {fg['id']} text prints at {printed:.1f} pt ({font_pt:g} pt drawn at {drawn:g} cm, placed "
                    f"{placed:g} cm), below {thr:.1f} pt; draw it with figures.py --profile poster at the width it "
                    f"is placed")
    for b in dom.boxes:
        a = b["attrs"]
        if a.get("data-overflow") == "1":
            rep.add("block", dom_name, b["line"], f"box {_box_name(b)} overflows: text or figure is cut off")
        fpt = _fnum(a.get("data-font-pt"))
        if fpt is not None and fpt < thr - 0.05:
            rep.add("warn", dom_name, b["line"],
                    f"text in {_box_name(b)} is {fpt:.1f} pt, below {thr:.1f} pt "
                    f"({FONT_PT_90:g} pt scaled by {k:.2f} = min(width / 90, height / 120))")
    return rep


# ---------------------------------------------------------------- CLI

def run(project, layouts=None, spec_path=None, out=print, err=None) -> int:
    err = err or (lambda m: print(m, file=sys.stderr))
    project = Path(project)
    if not spec_path:  # the spec poster_build recorded for the first built layout, else the default
        for lay in (layouts or LAYOUTS):
            try:
                rec = json.loads((project / POSTER_DIR / f"{lay}.build.json").read_text(encoding="utf-8"))
                spec_path = project / rec["spec"] if not Path(rec["spec"]).is_absolute() else rec["spec"]
                break
            except (OSError, ValueError, KeyError, TypeError):
                continue
    spec_path = Path(spec_path) if spec_path else project / poster_build.SPEC_REL
    if not spec_path.is_absolute() and not spec_path.exists() and (project / spec_path).exists():
        spec_path = project / spec_path
    try:
        spec = poster_build.load_spec(project, spec_path)
    except poster_build.PosterError as e:
        err(f"poster_preflight: {e}")
        return 2
    except (ValueError, TypeError, KeyError, AttributeError) as e:
        err(f"poster_preflight: invalid poster.json ({type(e).__name__}: {e})")
        return 2
    poster_dir = project / POSTER_DIR
    if layouts:
        chosen = list(layouts)
    else:
        chosen = list(spec["layouts"])
        built = [x for x in chosen if (poster_dir / f"{x}.pdf").exists() or (poster_dir / f"{x}.dom.html").exists()]
        chosen = built or chosen
    rc = 0
    for layout in chosen:
        rep = check_layout(layout, poster_dir, spec["size_cm"], spec["bleed_mm"])
        for sev, f, line, msg in rep.items:
            err(f"E-PRINT {sev} {f}:{line}: {msg}")
        out(f"poster_preflight: {layout}: {rep.blocks} block, {rep.warns} warn")
        if rep.vectors:
            out(f"poster_preflight: {layout}: vector figures (no dpi): {', '.join(rep.vectors)}")
        if rep.blocks:
            rc = 1
    return rc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--layout", action="append", choices=LAYOUTS)
    ap.add_argument("--spec")
    a = ap.parse_args(argv)
    if not Path(a.project).is_dir():
        print(f"poster_preflight: project folder not found: {a.project}", file=sys.stderr)
        return 2
    return run(a.project, a.layout, a.spec)


if __name__ == "__main__":
    sys.exit(main())
