#!/usr/bin/env python3
"""Build a print poster from 07_present/poster/poster.json: HTML, then PDF + PNG + DOM dump through headless
Chrome or Edge, and an editable PPTX.

  python poster_build.py PROJECT [SPEC] [--layout editorial|pathway|figure-led] [--browser PATH]
                         [--no-pptx] [--pptx-required]

SPEC defaults to <PROJECT>/07_present/poster/poster.json; every layout in its "layouts" is built unless --layout
is given. {{R-...}} placeholders are rendered from the results ledger (an unknown id exits 2, nothing is written).
Writes 07_present/poster/<layout>.{html,pdf,png,dom.html,spec.json,pptx}. Format: references/presenting/poster-spec.md.
Exit 0 = everything written; 2 = bad spec, placeholder problem, no browser (HTML and PPTX are still written) or
a failed required step.
"""
from __future__ import annotations

import argparse
import html
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import quote

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crolib import projectcfg  # noqa: E402
import render_results  # noqa: E402

TEMPLATES = Path(__file__).resolve().parent.parent / "templates" / "poster"
LAYOUTS = ("editorial", "pathway", "figure-led")
SPEC_REL = Path("07_present") / "poster" / "poster.json"
PX_PER_CM = 37.7953
PT_CM = 2.54 / 72
DEFAULT_FONT = 'Arial, "Liberation Sans", sans-serif'
BROWSER_NAMES = ("msedge", "chrome", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser")
BROWSER_PATHS = (
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
)
LABELS = {
    "vi": {"key": "Thông điệp chính", "refs": "Tài liệu tham khảo", "test": "Xét nghiệm", "value": "Kết quả", "unit": "Đơn vị"},
    "en": {"key": "Key message", "refs": "References", "test": "Test", "value": "Result", "unit": "Unit"},
}
# Fixed grid per layout, as fractions of the trimmed poster height (title/key/footer) or width.
GRID = {
    "editorial": {"title": 0.14, "foot": 0.08, "key": 0.0},
    "pathway": {"title": 0.14, "foot": 0.08, "key": 0.09},
    "figure-led": {"title": 0.14, "foot": 0.08, "key": 0.0},
}
BODY_PT = {"editorial": 38, "pathway": 36, "figure-led": 30}  # body size at 90 cm
HERO_SHARE = 0.46  # figure-led: the hero box covers at least this share of the body area


class PosterError(Exception):
    pass


# ------------------------------------------------------------------ small helpers
def num(v: float) -> str:
    return f"{v:.4f}".rstrip("0").rstrip(".")


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def inline_html(s: str) -> str:
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\*\w])\*(?!\s)(.+?)(?<!\s)\*(?![\*\w])", r"<em>\1</em>", s)
    return s


def inline_runs(s: str) -> list[tuple[str, bool, bool]]:
    """Split Markdown inline marks into (text, bold, italic) runs."""
    runs = []
    for part in re.split(r"(\*\*.+?\*\*)", s):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            runs.append((part[2:-2], True, False))
            continue
        for sub in re.split(r"((?<![\*\w])\*(?!\s).+?(?<!\s)\*(?![\*\w]))", part):
            if not sub:
                continue
            if sub.startswith("*") and sub.endswith("*") and len(sub) > 2:
                runs.append((sub[1:-1], False, True))
            else:
                runs.append((sub, False, False))
    return runs


_TABLE_SEP = re.compile(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$")


def _cells(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def md_blocks(text: str) -> list[tuple]:
    """Markdown subset of build_docx: headings, paragraphs, **bold**, *italic*, lists, pipe tables."""
    lines = (text or "").replace("\r\n", "\n").split("\n")
    out: list[tuple] = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", ln)
        if m:
            out.append(("h", len(m.group(1)), m.group(2).strip()))
            i += 1
            continue
        if ln.lstrip().startswith("|") and i + 1 < len(lines) and _TABLE_SEP.match(lines[i + 1]):
            head = _cells(ln)
            i += 2
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append(_cells(lines[i]))
                i += 1
            out.append(("table", head, rows))
            continue
        m = re.match(r"^\s*([-*+])\s+(.*)$", ln)
        if m:
            items = []
            while i < len(lines) and re.match(r"^\s*[-*+]\s+", lines[i]):
                items.append(re.sub(r"^\s*[-*+]\s+", "", lines[i]).strip())
                i += 1
            out.append(("ul", items))
            continue
        if re.match(r"^\s*\d+[.)]\s+", ln):
            items = []
            while i < len(lines) and re.match(r"^\s*\d+[.)]\s+", lines[i]):
                items.append(re.sub(r"^\s*\d+[.)]\s+", "", lines[i]).strip())
                i += 1
            out.append(("ol", items))
            continue
        para = []
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,6}\s|\s*[-*+]\s|\s*\d+[.)]\s)", lines[i]) \
                and not lines[i].lstrip().startswith("|"):
            para.append(lines[i].strip())
            i += 1
        if not para:  # a stray "|" line that is not a table
            para.append(lines[i].strip())
            i += 1
        out.append(("p", " ".join(para)))
    return out


def md_to_html(text: str) -> str:
    parts = []
    for b in md_blocks(text):
        if b[0] == "h":
            lvl = min(5, b[1] + 2)
            parts.append(f"<h{lvl}>{inline_html(b[2])}</h{lvl}>")
        elif b[0] == "p":
            parts.append(f"<p>{inline_html(b[1])}</p>")
        elif b[0] in ("ul", "ol"):
            parts.append(f"<{b[0]}>" + "".join(f"<li>{inline_html(x)}</li>" for x in b[1]) + f"</{b[0]}>")
        else:
            head = "".join(f"<th>{inline_html(c)}</th>" for c in b[1])
            body = "".join("<tr>" + "".join(f"<td>{inline_html(c)}</td>" for c in r) + "</tr>" for r in b[2])
            parts.append(f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>")
    return "\n".join(parts)


# ------------------------------------------------------------------ spec loading
def _walk_render(obj, by_id, lang, path, probs):
    if isinstance(obj, str):
        out, p = render_results.render_text(obj, by_id, lang)
        for x in p:
            probs.append(f"{path}: {x.partition(': ')[2]}")
        return out
    if isinstance(obj, list):
        return [_walk_render(v, by_id, lang, f"{path}[{i}]", probs) for i, v in enumerate(obj)]
    if isinstance(obj, dict):
        return {k: _walk_render(v, by_id, lang, f"{path}.{k}" if path else k, probs) for k, v in obj.items()}
    return obj


def load_spec(project: Path, spec_path: Path) -> dict:
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8-sig"))
    except OSError as e:
        raise PosterError(f"cannot read {spec_path}: {e}")
    except ValueError as e:
        raise PosterError(f"{spec_path} is not valid JSON: {e}")
    if not isinstance(spec, dict):
        raise PosterError(f"{spec_path}: top level must be an object")
    lang = spec.get("lang") or projectcfg.output_lang(project)
    if lang not in LABELS:
        lang = "en"
    try:
        ledger = json.loads((project / "ledgers" / "results-ledger.json").read_text(encoding="utf-8-sig"))
        results = ledger.get("results")
        by_id = {r["id"]: r for r in results}
    except FileNotFoundError:
        by_id = {}
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as e:
        raise PosterError(f"results ledger unreadable: {e}")
    probs: list[str] = []
    spec = _walk_render(spec, by_id, lang, "", probs)
    if probs:
        raise PosterError("placeholders cannot be rendered:\n  " + "\n  ".join(f"{spec_path.name}: {p}" for p in probs))
    spec["lang"] = lang
    size = spec.get("size_cm")
    if size is None:
        raw = projectcfg.read_project_yaml(project).get("target", {})
        raw = raw.get("poster_size_cm") if isinstance(raw, dict) else None
        try:
            size = json.loads(raw) if raw else [90, 120]
        except ValueError:
            size = [90, 120]
    if (not isinstance(size, list) or len(size) != 2
            or not all(isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0 for v in size)):
        raise PosterError('"size_cm" must be [width, height] in centimetres')
    if max(size) > 142:
        raise PosterError('"size_cm" is at most 142 cm per side (the PowerPoint limit)')
    spec["size_cm"] = [float(size[0]), float(size[1])]
    bleed = spec.get("bleed_mm", 3)
    if not isinstance(bleed, (int, float)) or isinstance(bleed, bool) or bleed < 0 or bleed > 20:
        raise PosterError('"bleed_mm" must be a number from 0 to 20')
    spec["bleed_mm"] = float(bleed)
    layouts = spec.get("layouts") or list(LAYOUTS)
    bad = [x for x in layouts if x not in LAYOUTS] if isinstance(layouts, list) else ["?"]
    if bad:
        raise PosterError(f"unknown layout {bad[0]!r} (allowed: {', '.join(LAYOUTS)})")
    spec["layouts"] = layouts
    secs = spec.get("sections")
    if not isinstance(secs, list) or not secs or not all(isinstance(s, dict) for s in secs):
        raise PosterError('"sections" must be a non-empty list of objects')
    if not isinstance(spec.get("title"), str) or not spec["title"].strip():
        raise PosterError('"title" is required')
    return spec


# ------------------------------------------------------------------ figures
def _prefix_ids(svg: str, prefix: str) -> str:
    ids = set(re.findall(r'\bid="([^"]+)"', svg))
    if not ids:
        return svg
    svg = re.sub(r'\bid="([^"]+)"', lambda m: f'id="{prefix}-{m.group(1)}"', svg)
    svg = re.sub(r"url\(#([^)]+)\)", lambda m: f"url(#{prefix}-{m.group(1)})" if m.group(1) in ids else m.group(0), svg)
    svg = re.sub(r'((?:xlink:)?href)="#([^"]+)"',
                 lambda m: f'{m.group(1)}="#{prefix}-{m.group(2)}"' if m.group(2) in ids else m.group(0), svg)
    return svg


def inline_svg(text: str, fid: str, raster_rel: str | None, alt: str) -> str:
    svg = re.sub(r"<\?xml.*?\?>", "", text, flags=re.S)
    svg = re.sub(r"<!DOCTYPE.*?>", "", svg, flags=re.S)
    svg = re.sub(r"<metadata>.*?</metadata>", "", svg, flags=re.S)
    m = re.search(r"<svg\b[^>]*>", svg)
    if not m:
        raise PosterError(f"{fid}: not an SVG file")
    root = re.sub(r'\s(?:width|height)="[^"]*"', "", m.group(0))
    extra = f' class="fig-svg fig-svg-{esc(fid)}" role="img" aria-label="{esc(alt)}"'
    if raster_rel:
        extra += f' data-raster="{esc(raster_rel)}"'
    root = root[:-1] + extra + ">"
    svg = svg[:m.start()] + root + svg[m.end():]
    svg = svg.replace("*{", f".fig-svg-{fid} *{{")
    return _prefix_ids(svg, f"{fid}")


def rel_url(target: Path, start: Path) -> str:
    rel = os.path.relpath(target, start).replace("\\", "/")
    return quote(rel, safe="/")


class Assets:
    def __init__(self, project: Path, out_dir: Path):
        self.project, self.out_dir = project, out_dir
        self.fig_dir = project / "07_present" / "figures"

    def figure(self, fid: str) -> dict:
        svg, png = self.fig_dir / f"{fid}.svg", self.fig_dir / f"{fid}.png"
        if not svg.is_file() and not png.is_file():
            raise PosterError(f"figure {fid}: neither {svg.name} nor {png.name} found in 07_present/figures (run figures.py)")
        info = {"id": fid, "svg": svg if svg.is_file() else None, "png": png if png.is_file() else None, "aspect": None}
        if info["png"]:
            info["aspect"] = _png_aspect(png)
        if info["aspect"] is None and info["svg"]:
            m = re.search(r'viewBox="[\d.\-]+ [\d.\-]+ ([\d.]+) ([\d.]+)"', svg.read_text(encoding="utf-8"))
            if m and float(m.group(1)) > 0:
                info["aspect"] = float(m.group(2)) / float(m.group(1))
        info["aspect"] = info["aspect"] or 0.6
        return info


def _png_aspect(path: Path):
    try:
        with open(path, "rb") as fh:
            head = fh.read(24)
        if head[:8] == b"\x89PNG\r\n\x1a\n":
            w = int.from_bytes(head[16:20], "big")
            h = int.from_bytes(head[20:24], "big")
            return h / w if w else None
    except OSError:
        pass
    return None


# ------------------------------------------------------------------ sections to HTML
def figure_ref(sec: dict) -> dict | None:
    f = sec.get("figure")
    if not f:
        return None
    if isinstance(f, str):
        return {"id": f}
    if isinstance(f, dict) and isinstance(f.get("id"), str):
        return f
    raise PosterError(f"section {sec.get('heading', '?')!r}: 'figure' must be an id or an object with an id")


def lab_rows(sec: dict) -> list[dict]:
    rows = sec.get("lab_table") or []
    if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows):
        raise PosterError("'lab_table' must be a list of {test, value, unit, flag}")
    return rows


def checklist_items(sec: dict) -> list[tuple[str, bool]]:
    items = sec.get("checklist") or []
    out = []
    for it in items:
        if isinstance(it, str):
            out.append((it, False))
        elif isinstance(it, dict) and "text" in it:
            out.append((str(it["text"]), bool(it.get("checked", it.get("done", False)))))
        else:
            raise PosterError("'checklist' items are strings or {text, checked}")
    return out


ARROW = {"high": "↑", "low": "↓"}


def figure_html(fref: dict, assets: Assets, out_dir: Path) -> str:
    info = assets.figure(fref["id"])
    caption = fref.get("caption", "")
    alt = fref.get("alt") or caption or fref["id"]
    raster = rel_url(info["png"], out_dir) if info["png"] else None
    if info["svg"]:
        body = inline_svg(info["svg"].read_text(encoding="utf-8"), fref["id"], raster, alt)
    else:
        body = f'<img src="{raster}" alt="{esc(alt)}">'
    cap = f"<figcaption>{inline_html(caption)}</figcaption>" if caption else ""
    return f'<figure class="fig" data-fig="{esc(fref["id"])}">{body}{cap}</figure>'


def lab_html(rows: list[dict], lang: str) -> str:
    lb = LABELS[lang]
    out = [f'<table class="lab"><thead><tr><th>{lb["test"]}</th><th>{lb["value"]}</th><th>{lb["unit"]}</th></tr></thead><tbody>']
    for r in rows:
        flag = r.get("flag", "normal")
        arrow = ARROW.get(flag, "")
        out.append(f'<tr class="{esc(flag)}"><td>{esc(r.get("test", ""))}</td>'
                   f'<td class="val">{esc(r.get("value", ""))} <span class="arrow">{arrow}</span></td>'
                   f'<td>{esc(r.get("unit", ""))}</td></tr>')
    out.append("</tbody></table>")
    return "".join(out)


def checklist_html(items: list[tuple[str, bool]]) -> str:
    return '<ul class="checklist">' + "".join(
        f'<li><span class="mark">{"☑" if done else "☐"}</span>{inline_html(t)}</li>' for t, done in items) + "</ul>"


def section_inner(sec: dict, assets: Assets, out_dir: Path, lang: str, skip_figure=False) -> str:
    parts = []
    if sec.get("heading"):
        parts.append(f"<h2>{inline_html(sec['heading'])}</h2>")
    fref = figure_ref(sec)
    if fref and not skip_figure:
        parts.append(figure_html(fref, assets, out_dir))
    if sec.get("body"):
        parts.append(f'<div class="body">{md_to_html(sec["body"])}</div>')
    if sec.get("lab_table"):
        parts.append(lab_html(lab_rows(sec), lang))
    if sec.get("checklist"):
        parts.append(checklist_html(checklist_items(sec)))
    return "\n".join(parts)


def section_weight(sec: dict, hero_fig_weight=0) -> float:
    w = 90 + len(sec.get("body") or "") * 1.0
    for b in md_blocks(sec.get("body") or ""):
        if b[0] == "table":
            w += 70 * (len(b[2]) + 1)
    if figure_ref(sec):
        w += 650
    w += 75 * len(sec.get("lab_table") or []) + 90 * len(sec.get("checklist") or [])
    return w


def distribute(secs: list[dict], n: int) -> list[list[int]]:
    """Indexes of sections per column. Honours a section's explicit 'column' (1-based); the rest go in reading
    order to contiguous columns of about equal weight."""
    cols: list[list[int]] = [[] for _ in range(n)]
    free = []
    for i, s in enumerate(secs):
        c = s.get("column")
        if c is None:
            free.append(i)
        elif isinstance(c, int) and 1 <= c <= n:
            cols[c - 1].append(i)
        else:
            raise PosterError(f"section {s.get('heading', i)!r}: 'column' must be 1..{n}")
    if not any(s.get("column") for s in secs):
        weights = [section_weight(secs[i]) for i in free]
        target = sum(weights) / n if weights else 0
        c, acc = 0, 0.0
        for i, w in zip(free, weights):
            if c < n - 1 and acc > 0 and acc + w / 2 > target:
                c += 1
                acc = 0.0
            cols[c].append(i)
            acc += w
    else:
        load = [sum(section_weight(secs[i]) for i in col) for col in cols]
        for i in free:
            k = load.index(min(load))
            cols[k].append(i)
            load[k] += section_weight(secs[i])
        for col in cols:
            col.sort()
    return cols


# ------------------------------------------------------------------ geometry
def geometry(layout: str, spec: dict) -> dict:
    W, H = spec["size_cm"]
    k = W / 90.0
    b = spec["bleed_mm"] / 10.0
    g = GRID[layout]
    title = g["title"] * H
    foot = g["foot"] * H if spec.get("references") else 0.0
    key = g["key"] * H
    inner_w = W - 6 * k
    main_h = H - title - foot - 5 * k
    geo = {"W": W, "H": H, "k": k, "bleed": b, "title": title, "foot": foot, "key": key, "inner_w": inner_w,
           "main_h": main_h, "pad": 3 * k, "gap": 3 * k}
    if layout == "figure-led":
        hero_w = (inner_w - 3 * k) * 0.72
        hero_h = HERO_SHARE * 1.01 * inner_w * main_h / hero_w
        hero_h = min(hero_h, main_h * 0.78)
        geo.update({"hero_w": hero_w, "hero_h": hero_h})
    return geo


def css_vars(layout: str, spec: dict, geo: dict) -> str:
    v = {
        "--k": num(geo["k"]), "--bleed": f"{num(geo['bleed'])}cm",
        "--sheet-w": f"{num(geo['W'] + 2 * geo['bleed'])}cm", "--sheet-h": f"{num(geo['H'] + 2 * geo['bleed'])}cm",
        "--title-h": f"{num(geo['title'] + geo['bleed'])}cm",
        "--foot-h": f"{num(geo['foot'] + geo['bleed'])}cm", "--key-h": f"{num(geo['key'])}cm",
        "--font": spec.get("font") or DEFAULT_FONT,
    }
    if "hero_h" in geo:
        v["--hero-h"] = f"{num(geo['hero_h'])}cm"
    v["--body-pt"] = num(float(spec.get("body_pt") or BODY_PT[layout]))
    colors = spec.get("colors") or {}
    for key, var in (("accent", "--accent"), ("tint", "--tint"), ("ink", "--ink")):
        if isinstance(colors.get(key), str) and re.fullmatch(r"#[0-9a-fA-F]{6}", colors[key]):
            v[var] = colors[key]
    return "; ".join(f"{a}: {b}" for a, b in v.items())


def build_html(layout: str, spec: dict, assets: Assets, out_dir: Path) -> str:
    lang = spec["lang"]
    secs = spec["sections"]
    geo = geometry(layout, spec)
    tpl = (TEMPLATES / f"{layout}.html").read_text(encoding="utf-8")
    css = (TEMPLATES / "poster.css").read_text(encoding="utf-8")
    js = (TEMPLATES / "preflight.js").read_text(encoding="utf-8")
    key_html = (f'<span class="label">{LABELS[lang]["key"]}</span>'
                f'<span class="text">{inline_html(spec.get("key_message", ""))}</span>') if spec.get("key_message") else ""
    rep = {
        "LANG": lang, "DOC_TITLE": esc(spec["title"]),
        "PAGE_W": num(geo["W"] + 2 * geo["bleed"]), "PAGE_H": num(geo["H"] + 2 * geo["bleed"]),
        "CSS": css, "JS": js, "VARS": esc(css_vars(layout, spec, geo)),
        "TITLE": inline_html(spec["title"]),
        "AUTHORS": f'<p class="authors">{inline_html(spec["authors"])}</p>' if spec.get("authors") else "",
        "AFFIL": f'<p class="affil">{inline_html(spec["affiliation"])}</p>' if spec.get("affiliation") else "",
        "LOGO": "", "KEY": key_html, "REFS": "",
    }
    if spec.get("logo"):
        logo = (assets.project / spec["logo"]).resolve()
        if not logo.is_file():
            raise PosterError(f"logo not found: {spec['logo']}")
        rep["LOGO"] = f'<img class="logo" src="{rel_url(logo, out_dir)}" alt="{esc(spec.get("logo_alt", "Logo"))}">'
    if spec.get("references"):
        refs = "".join(f"<li>{inline_html(r)}</li>" for r in spec["references"])
        contact = f'<div class="contact">{inline_html(spec["contact"])}</div>' if spec.get("contact") else ""
        two = " cols-2"
        rep["REFS"] = f'<footer class="refs box{two}"><h2>{LABELS[lang]["refs"]}</h2><ol>{refs}</ol>{contact}</footer>'

    def sec_html(i, kind="plain", number=None):
        inner = section_inner(secs[i], assets, out_dir, lang)
        if kind == "step":
            return f'<section class="step" id="sec-{i + 1}"><div class="num">{number}</div><div class="step-body">{inner}</div></section>'
        return f'<section class="sec" id="sec-{i + 1}">{inner}</section>'

    if layout == "editorial":
        cols = distribute(secs, 3)
        for n, col in enumerate(cols, 1):
            rep[f"COL{n}"] = "\n".join(sec_html(i) for i in col)
    elif layout == "pathway":
        cols = distribute(secs, 2)
        for n, col in enumerate(cols, 1):
            rep[f"COL{n}"] = "\n".join(sec_html(i, "step", i + 1) for i in col)
    else:
        hero_i = hero_index(spec)
        hero_sec = secs[hero_i]
        hero_ref = figure_ref(hero_sec)
        hero_inner = []
        if hero_sec.get("heading"):
            hero_inner.append(f"<h2>{inline_html(hero_sec['heading'])}</h2>")
        hero_inner.append(figure_html({**hero_ref, "hero": True}, assets, out_dir).replace('class="fig"', 'class="fig hero"', 1))
        rest = section_inner({k: v for k, v in hero_sec.items() if k not in ("heading", "figure")}, assets, out_dir, lang)
        if rest:
            hero_inner.append(rest)
        rep["HERO"] = "\n".join(hero_inner)
        others = [s for j, s in enumerate(secs) if j != hero_i]
        idx_map = [j for j in range(len(secs)) if j != hero_i]
        cols = distribute(others, 3)
        for n, col in enumerate(cols, 1):
            rep[f"COL{n}"] = "\n".join(sec_html(idx_map[i]) for i in col)
    out = tpl
    for k_, v in rep.items():
        out = out.replace(f"%%{k_}%%", v)
    return out


def hero_index(spec: dict) -> int:
    secs = spec["sections"]
    want = spec.get("hero")
    for i, s in enumerate(secs):
        f = figure_ref(s)
        if f and (want is None or f["id"] == want):
            return i
    raise PosterError("the figure-led layout needs a section with a figure" + (f" (hero {want!r} not found)" if want else ""))


# ------------------------------------------------------------------ browser
def find_browser(explicit: str | None) -> str | None:
    if explicit:
        return explicit if Path(explicit).is_file() else None
    for name in BROWSER_NAMES:
        p = shutil.which(name)
        if p:
            return p
    for p in BROWSER_PATHS:
        if Path(p).is_file():
            return p
    return None


def _browser_cmd(browser: str, user_dir: str, extra: list[str]) -> list[str]:
    return [browser, "--headless=new", "--disable-gpu", "--no-first-run", "--allow-file-access-from-files",
            "--virtual-time-budget=10000", f"--user-data-dir={user_dir}"] + extra


def run_browser(browser: str, html_path: Path, out_base: Path, geo: dict) -> list[str]:
    """PDF, PNG and DOM dump. Returns the paths written; raises PosterError on a failed command."""
    url = html_path.resolve().as_uri()
    page_w = (geo["W"] + 2 * geo["bleed"]) * PX_PER_CM
    page_h = (geo["H"] + 2 * geo["bleed"]) * PX_PER_CM
    scale = 2000.0 / max(page_w, page_h)
    pdf, png, dom = (out_base.with_name(out_base.name + s) for s in (".pdf", ".png", ".dom.html"))
    jobs = [
        (pdf, [f"--print-to-pdf={pdf}", "--no-pdf-header-footer", url], False),
        (png, [f"--screenshot={png}", f"--window-size={int(round(page_w))},{int(round(page_h))}",
               f"--force-device-scale-factor={scale:.5f}", url], False),
        (dom, ["--dump-dom", url], True),
    ]
    written = []
    for target, extra, capture in jobs:
        user_dir = tempfile.mkdtemp(prefix="poster-browser-")
        try:
            if target.exists():
                target.unlink()
            try:
                r = subprocess.run(_browser_cmd(browser, user_dir, extra), capture_output=True, timeout=120)
            except subprocess.TimeoutExpired:
                raise PosterError(f"browser timed out after 120 s writing {target.name}")
            except OSError as e:
                raise PosterError(f"cannot run browser {browser}: {e}")
            if capture:
                if r.returncode == 0 and r.stdout:
                    target.write_bytes(r.stdout)
            if r.returncode != 0 or not target.is_file() or target.stat().st_size == 0:
                tail = r.stderr.decode("utf-8", "replace").strip().splitlines()[-3:]
                raise PosterError(f"browser failed for {target.name} (exit {r.returncode}) {' | '.join(tail)}")
            written.append(str(target))
        finally:
            shutil.rmtree(user_dir, ignore_errors=True)
    return written


# ------------------------------------------------------------------ PPTX
def _est_height(text: str, pt: float, width_cm: float, bold=False) -> float:
    cw = pt * PT_CM * (0.56 if bold else 0.52)
    per = max(1, int(width_cm / cw))
    lines = sum(max(1, math.ceil(len(par) / per)) for par in (text.split("\n") if text else [""]))
    return lines * pt * PT_CM * 1.3


def plan_items(layout: str, spec: dict, assets: Assets) -> list[dict]:
    """Fixed-grid canvas for the PPTX: rectangles, text, native tables and figure PNGs, in trimmed-poster cm."""
    lang = spec["lang"]
    geo = geometry(layout, spec)
    W, H, k = geo["W"], geo["H"], geo["k"]
    font = (spec.get("font") or "Arial").split(",")[0].strip().strip('"')
    colors = {"accent": "#1f4e79", "tint": "#e3ebf3", "ink": "#111111", "muted": "#444444"}
    colors.update({k_: v for k_, v in (spec.get("colors") or {}).items() if k_ in colors and isinstance(v, str)})
    body_pt = float(spec.get("body_pt") or BODY_PT[layout]) * k
    secs = spec["sections"]
    items: list[dict] = []

    def rect(x, y, w, h, fill=None, line=None):
        items.append({"kind": "rect", "x": x, "y": y, "w": w, "h": h, "fill": fill, "line": line})

    def text(x, y, w, h, paras, name="text"):
        items.append({"kind": "text", "name": name, "x": x, "y": y, "w": w, "h": h, "paragraphs": paras})

    def para(t, size, bold=False, color=None, bullet=None, after=0.0, italic=False):
        return {"text": t, "size": size, "bold": bold, "italic": italic, "color": color or colors["ink"], "bullet": bullet,
                "space_after": after}

    # title band
    title_h = geo["title"]
    rect(0, 0, W, title_h, fill=colors["accent"])
    tp = [para(spec["title"], 92 * k, True, "#ffffff")]
    if spec.get("authors"):
        tp.append(para(spec["authors"], 40 * k, True, "#ffffff", after=0))
    if spec.get("affiliation"):
        tp.append(para(spec["affiliation"], 30 * k, False, "#ffffff"))
    text(3 * k, 1.5 * k, W - 6 * k, title_h - 3 * k, tp, "Title")
    y0 = title_h + 2.5 * k
    inner_w = geo["inner_w"]
    x0 = 3 * k

    def key_paras(color):
        return [para(LABELS[lang]["key"].upper(), 28 * k, True, color, after=6 * k),
                para(spec.get("key_message", ""), 54 * k, True, color)]

    def section_blocks(sec, x, y, w, number=None, skip_heading=False, skip_figure=False) -> float:
        """Lay a section's blocks down a column from y; returns the y after the last block."""
        if sec.get("heading") and not skip_heading:
            head = (f"{number}  " if number else "") + sec["heading"]
            hh = _est_height(head, 50 * k, w, True)
            text(x, y, w, hh, [para(head, 50 * k, True, colors["accent"])], "Heading")
            y += hh + 0.6 * k
        fref = figure_ref(sec)
        if fref and not skip_figure:
            info = assets.figure(fref["id"])
            if not info["png"]:
                raise PosterError(f"figure {fref['id']}: the PPTX needs {fref['id']}.png (run figures.py)")
            ph = w * info["aspect"]
            items.append({"kind": "image", "x": x, "y": y, "w": w, "h": ph, "path": str(info["png"]),
                          "alt": fref.get("alt") or fref.get("caption") or fref["id"]})
            y += ph + 0.4 * k
            if fref.get("caption"):
                ch = _est_height(fref["caption"], 26 * k, w)
                text(x, y, w, ch, [para(fref["caption"], 26 * k, False, colors["muted"])], "Caption")
                y += ch + 0.8 * k
        pending: list[dict] = []
        pending_h = [0.0]

        def flush():
            nonlocal y
            if pending:
                text(x, y, w, pending_h[0], list(pending), "Body")
                y += pending_h[0] + 0.5 * k
                pending.clear()
                pending_h[0] = 0.0

        for b in md_blocks(sec.get("body") or ""):
            if b[0] == "table":
                flush()
                rows = [b[1]] + b[2]
                th = (len(rows)) * (28 * k * PT_CM * 1.9)
                items.append({"kind": "table", "x": x, "y": y, "w": w, "h": th, "columns": b[1], "rows": b[2], "size": 28 * k})
                y += th + 0.8 * k
            elif b[0] == "h":
                pending.append(para(b[2], 36 * k, True, after=4 * k))
                pending_h[0] += _est_height(b[2], 36 * k, w, True) + 4 * k * PT_CM
            elif b[0] == "p":
                pending.append(para(b[1], body_pt, after=7 * k))
                pending_h[0] += _est_height(b[1], body_pt, w) + 7 * k * PT_CM
            else:
                for n_, it in enumerate(b[1], 1):
                    pending.append(para(it, body_pt, bullet="•" if b[0] == "ul" else f"{n_}.", after=4 * k))
                    pending_h[0] += _est_height("• " + it, body_pt, w - 1.2 * k) + 4 * k * PT_CM
        flush()
        if sec.get("lab_table"):
            rows = lab_rows(sec)
            lb = LABELS[lang]
            data = [[str(r.get("test", "")), f"{r.get('value', '')} {ARROW.get(r.get('flag', 'normal'), '')}".strip(),
                     str(r.get("unit", ""))] for r in rows]
            th = (len(data) + 1) * (28 * k * PT_CM * 1.9)
            items.append({"kind": "table", "x": x, "y": y, "w": w, "h": th, "columns": [lb["test"], lb["value"], lb["unit"]],
                          "rows": data, "size": 28 * k})
            y += th + 0.8 * k
        if sec.get("checklist"):
            ps, hh = [], 0.0
            for t, done in checklist_items(sec):
                ps.append(para(t, body_pt, bullet="☑" if done else "☐", after=4 * k))
                hh += _est_height("☐ " + t, body_pt, w - 1.2 * k) + 4 * k * PT_CM
            text(x, y, w, hh, ps, "Checklist")
            y += hh + 0.5 * k
        return y + 2.2 * k

    def put_columns(cols, idx_map, x, y, width, n, step=False):
        cw = (width - (n - 1) * 3 * k) / n
        for c, col in enumerate(cols):
            cx = x + c * (cw + 3 * k)
            yy = y
            for i in col:
                j = idx_map[i]
                if step:
                    rect(cx, yy, 5.5 * k, 5.5 * k, fill=colors["accent"])
                    text(cx, yy, 5.5 * k, 5.5 * k, [para(str(j + 1), 54 * k, True, "#ffffff")], "Step number")
                    yy = section_blocks(secs[j], cx + 7.3 * k, yy, cw - 7.3 * k)
                else:
                    yy = section_blocks(secs[j], cx, yy, cw)

    foot = geo["foot"]
    if layout == "editorial":
        cols = distribute(secs, 3)
        cw = (inner_w - 6 * k) / 3
        ky = y0
        kh = _est_height(spec.get("key_message", ""), 54 * k, cw) + 6 * k
        rect(x0, ky, cw, 0.5 * k, fill=colors["accent"])
        text(x0, ky + 1 * k, cw, kh, key_paras(colors["ink"]), "Key message")
        for c, col in enumerate(cols):
            cx = x0 + c * (cw + 3 * k)
            if c:
                rect(cx - 1.5 * k, y0, 0.12 * k, H - foot - y0 - 2.5 * k, fill="#9aa8b6")
            yy = y0 + (kh + 3 * k if c == 0 else 0)
            for i in col:
                yy = section_blocks(secs[i], cx, yy, cw)
    elif layout == "pathway":
        rect(x0, y0, inner_w, geo["key"], fill=colors["tint"])
        rect(x0, y0, 1.2 * k, geo["key"], fill=colors["accent"])
        text(x0 + 3.6 * k, y0 + 1.2 * k, inner_w - 6 * k, geo["key"] - 2.4 * k, key_paras(colors["ink"]), "Key message")
        put_columns(distribute(secs, 2), list(range(len(secs))), x0, y0 + geo["key"] + 2.5 * k, inner_w, 2, step=True)
    else:
        hi = hero_index(spec)
        hs = secs[hi]
        hw, hh = geo["hero_w"], geo["hero_h"]
        rect(x0, y0, hw, hh, fill=None, line=colors["accent"])
        yy = section_blocks(hs, x0 + 1.6 * k, y0 + 1.6 * k, hw - 3.2 * k)
        kx = x0 + hw + 3 * k
        rect(kx, y0, inner_w - hw - 3 * k, hh, fill=colors["accent"])
        text(kx + 2.4 * k, y0 + 2.4 * k, inner_w - hw - 3 * k - 4.8 * k, hh - 4.8 * k,
             [para(LABELS[lang]["key"].upper(), 28 * k, True, "#ffffff", after=6 * k),
              para(spec.get("key_message", ""), 58 * k, True, "#ffffff")], "Key message")
        others = [j for j in range(len(secs)) if j != hi]
        put_columns(distribute([secs[j] for j in others], 3), others, x0, y0 + hh + 2.5 * k, inner_w, 3)
    if spec.get("references"):
        fy = H - foot
        rect(0, fy, W, foot, fill=colors["tint"])
        refs = [para(LABELS[lang]["refs"], 30 * k, True, colors["accent"], after=3 * k)] + [
            para(r, 24 * k, bullet=f"{i}.", after=2 * k) for i, r in enumerate(spec["references"], 1)]
        if spec.get("contact"):
            refs.append(para(spec["contact"], 24 * k))
        text(3 * k, fy + 1.6 * k, W - 6 * k, foot - 2.2 * k, refs, "References")
    return items


def write_pptx(items: list[dict], spec: dict, out: Path) -> None:
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.util import Cm, Pt

    font = (spec.get("font") or "Arial").split(",")[0].strip().strip('"')

    def rgb(h):
        h = h.lstrip("#")
        return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

    prs = Presentation()
    prs.slide_width, prs.slide_height = Cm(spec["size_cm"][0]), Cm(spec["size_cm"][1])
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    for it in list(slide.placeholders):
        it._element.getparent().remove(it._element)
    for it in items:
        k = it["kind"]
        if k == "rect":
            shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Cm(it["x"]), Cm(it["y"]), Cm(it["w"]), Cm(it["h"]))
            if it.get("fill"):
                shp.fill.solid()
                shp.fill.fore_color.rgb = rgb(it["fill"])
            else:
                shp.fill.background()
            if it.get("line"):
                shp.line.color.rgb = rgb(it["line"])
                shp.line.width = Cm(0.2)
            else:
                shp.line.fill.background()
            shp.shadow.inherit = False
        elif k == "text":
            tb = slide.shapes.add_textbox(Cm(it["x"]), Cm(it["y"]), Cm(it["w"]), Cm(it["h"]))
            tb.name = it.get("name", "text")
            tf = tb.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
            for n, p in enumerate(it["paragraphs"]):
                para = tf.paragraphs[0] if n == 0 else tf.add_paragraph()
                para.space_after = Pt(p.get("space_after", 0))
                runs = inline_runs(p["text"])
                if p.get("bullet"):
                    runs = [(p["bullet"] + " ", False, False)] + runs
                for t, b, i in runs:
                    r = para.add_run()
                    r.text = t
                    r.font.size = Pt(p["size"])
                    r.font.name = font
                    r.font.bold = bool(p.get("bold") or b)
                    r.font.italic = bool(p.get("italic") or i)
                    r.font.color.rgb = rgb(p["color"])
        elif k == "image":
            pic = slide.shapes.add_picture(it["path"], Cm(it["x"]), Cm(it["y"]), Cm(it["w"]), Cm(it["h"]))
            pic._element.nvPicPr.cNvPr.set("descr", it.get("alt", ""))
        elif k == "table":
            rows = [it["columns"]] + it["rows"]
            gf = slide.shapes.add_table(len(rows), len(it["columns"]), Cm(it["x"]), Cm(it["y"]), Cm(it["w"]), Cm(it["h"]))
            tbl = gf.table
            for ri, row in enumerate(rows):
                for ci, val in enumerate(row):
                    cell = tbl.cell(ri, ci)
                    cell.text = ""
                    para = cell.text_frame.paragraphs[0]
                    for t, b, i in inline_runs(str(val)):
                        r = para.add_run()
                        r.text = t
                        r.font.size = Pt(it["size"])
                        r.font.name = font
                        r.font.bold = b or ri == 0
                        r.font.italic = i
                        r.font.color.rgb = rgb("#ffffff" if ri == 0 else "#111111")
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = rgb("#1f4e79" if ri == 0 else "#ffffff")
    prs.save(str(out))


# ------------------------------------------------------------------ driver
def build(project, spec_path=None, layouts=None, browser=None, pptx=True, pptx_required=False,
          out=print, err=None) -> int:
    """Build the poster files. `browser` is a path to Chrome/Edge or None for no browser (HTML and PPTX are
    still written; exit 2). Returns the exit code."""
    err = err or (lambda m: print(m, file=sys.stderr))
    project = Path(project)
    spec_path = Path(spec_path) if spec_path else project / SPEC_REL
    try:
        spec = load_spec(project, spec_path)
        chosen = layouts or spec["layouts"]
        out_dir = project / "07_present" / "poster"
        out_dir.mkdir(parents=True, exist_ok=True)
        assets = Assets(project, out_dir)
        htmls = {}
        for layout in chosen:
            htmls[layout] = build_html(layout, spec, assets, out_dir)
    except PosterError as e:
        err(f"poster_build: {e}")
        return 2
    except OSError as e:
        err(f"poster_build: {type(e).__name__}: {e}")
        return 2
    rc = 0
    try:
        import pptx as _pptx  # noqa: F401
        have_pptx = True
    except ImportError:
        have_pptx = False
    if pptx and not have_pptx:
        err("poster_build: python-pptx is not installed, PPTX skipped (python -m pip install python-pptx)")
        if pptx_required:
            rc = 2
    if browser is None:
        err("poster_build: no Chrome or Edge found (use --browser PATH); wrote HTML, no PDF or PNG")
        rc = 2
    for layout in chosen:
        base = out_dir / layout
        html_path = base.with_name(layout + ".html")
        html_path.write_text(htmls[layout], encoding="utf-8", newline="\n")
        out(f"poster_build: wrote {html_path}")
        if browser:
            try:
                for p in run_browser(browser, html_path, base, geometry(layout, spec)):
                    out(f"poster_build: wrote {p}")
                dom = base.with_name(layout + ".dom.html").read_text(encoding="utf-8", errors="replace")
                n_over = dom.count('data-overflow="1"')
                if n_over:
                    err(f"poster_build: {layout}: {n_over} box(es) overflow (text or figures cut off); shorten the text "
                        f"or move a section (\"column\") and rebuild")
            except PosterError as e:
                err(f"poster_build: {layout}: {e}")
                rc = 2
        if pptx and have_pptx:
            try:
                items = plan_items(layout, spec, assets)
                spec_out = base.with_name(layout + ".spec.json")
                spec_out.write_text(json.dumps({"size_cm": spec["size_cm"], "layout": layout, "items": items},
                                               ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
                out(f"poster_build: wrote {spec_out}")
                pptx_path = base.with_name(layout + ".pptx")
                write_pptx(items, spec, pptx_path)
                out(f"poster_build: wrote {pptx_path}")
            except PosterError as e:
                err(f"poster_build: {layout}: {e}")
                rc = 2
    return rc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("spec", nargs="?")
    ap.add_argument("--layout", choices=LAYOUTS)
    ap.add_argument("--browser")
    ap.add_argument("--no-pptx", action="store_true")
    ap.add_argument("--pptx-required", action="store_true")
    a = ap.parse_args(argv)
    if not Path(a.project).is_dir():
        print(f"poster_build: project folder not found: {a.project}", file=sys.stderr)
        return 2
    if a.browser and not Path(a.browser).is_file():
        print(f"poster_build: browser not found: {a.browser}", file=sys.stderr)
        return 2
    return build(a.project, a.spec, [a.layout] if a.layout else None, find_browser(a.browser),
                 pptx=not a.no_pptx, pptx_required=a.pptx_required)


if __name__ == "__main__":
    sys.exit(main())
