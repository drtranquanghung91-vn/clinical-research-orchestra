#!/usr/bin/env python3
"""Check a .pptx for problems an audience would see, and render it for a visual look.

Checks per slide: shapes outside the slide; text likely to overflow its box (estimated
from characters, font size and box area); text below the size floor; pictures without
alt text; missing speaker notes.
--poster scales the size floors by the slide width (24 pt body at 90 cm wide) and skips the
notes check. --render DIR exports PNGs via PowerPoint (Windows) or LibreOffice + PyMuPDF.

Usage: python check_pptx.py talk.pptx [--min-body 18] [--min-any 10] [--poster] [--render build/render]
Exit codes: 0 no serious issue (off-slide, may-overflow, tiny-text); 1 serious issues listed;
2 usage error, unreadable file or missing python-pptx.
Adapted from grand-rounds 0.2.0 (check_pptx.py, MIT, same owner). Requires python-pptx.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):  # Windows consoles default to cp1252
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    from pptx import Presentation
    from pptx.util import Emu
except ImportError:
    print("check_pptx needs python-pptx: python -m pip install python-pptx", file=sys.stderr)
    sys.exit(2)

EMU_PER_PT = 12700
EMU_PER_CM = 360000
POSTER_BODY_PT, POSTER_REF_CM = 24.0, 90.0  # poster floor: 24 pt at 90 cm wide, scaled by width
DEFAULT_MIN_BODY, DEFAULT_MIN_ANY = 18.0, 10.0


def est_overflow(shape) -> float:
    """Ratio of estimated text height to box height (>1.05 means it probably overflows)."""
    tf = shape.text_frame
    w_pt = max(1, (shape.width - (tf.margin_left or 0) - (tf.margin_right or 0)) / EMU_PER_PT)
    h_pt = max(1, (shape.height - (tf.margin_top or 0) - (tf.margin_bottom or 0)) / EMU_PER_PT)
    total = 0.0
    nowrap = tf.word_wrap is False
    for p in tf.paragraphs:
        size = next((r.font.size.pt for r in p.runs if r.font.size), 18.0)
        chars = sum(len(r.text) for r in p.runs) or 1
        per_line = max(1, w_pt / (size * 0.5))  # average glyph ≈ 0.5 em
        lines = 1 if nowrap else -(-chars // per_line)
        total += lines * size * 1.2 + (p.space_after.pt if p.space_after else 0)
    return total / h_pt


def render(path: Path, rdir: Path, size_emu=None) -> str:
    """size_emu = (slide width, slide height): PNGs are exported 1920 px wide at the slide's aspect ratio."""
    rdir.mkdir(parents=True, exist_ok=True)
    px_w = 1920
    px_h = round(px_w * size_emu[1] / size_emu[0]) if size_emu and size_emu[0] else 1080
    if sys.platform == "win32":
        ps = (f"$a=New-Object -ComObject PowerPoint.Application;$p=$a.Presentations.Open('{path.resolve()}',$true,$false,$false);"
              f"foreach($s in $p.Slides){{$s.Export('{rdir.resolve()}\\slide-'+$s.SlideIndex.ToString('00')+'.png','PNG',{px_w},{px_h})}};$p.Close();$a.Quit()")
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True)
        if r.returncode == 0 and any(rdir.glob("*.png")):
            return f"rendered with PowerPoint to {rdir}"
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice:
        subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(rdir), str(path)], capture_output=True)
        pdf = rdir / (path.stem + ".pdf")
        try:
            try:
                import pymupdf as fitz  # type: ignore
            except ImportError:
                import fitz  # type: ignore
            for i, page in enumerate(fitz.open(pdf), 1):
                page.get_pixmap(dpi=144).save(rdir / f"slide-{i:02d}.png")
            return f"rendered with LibreOffice to {rdir} (fonts may differ from PowerPoint)"
        except Exception as e:
            return f"LibreOffice made {pdf}, but PNG export failed: {e}"
    return "no renderer: install LibreOffice or open in PowerPoint"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pptx")
    ap.add_argument("--min-body", type=float, default=None, help=f"body text floor in pt (default {DEFAULT_MIN_BODY:g})")
    ap.add_argument("--min-any", type=float, default=None, help=f"any text floor in pt (default {DEFAULT_MIN_ANY:g})")
    ap.add_argument("--poster", action="store_true",
                    help="scale the default floors by slide width (24 pt body at 90 cm wide); skip the notes check")
    ap.add_argument("--render")
    a = ap.parse_args(argv)
    try:
        prs = Presentation(a.pptx)
    except Exception as e:  # missing file, not a zip, not a presentation
        print(f"check_pptx: cannot open {a.pptx}: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    W, H = prs.slide_width, prs.slide_height
    min_body = a.min_body if a.min_body is not None else DEFAULT_MIN_BODY
    min_any = a.min_any if a.min_any is not None else DEFAULT_MIN_ANY
    if a.poster:
        factor = (POSTER_BODY_PT / DEFAULT_MIN_BODY) * (W / EMU_PER_CM / POSTER_REF_CM)
        if a.min_body is None:
            min_body = DEFAULT_MIN_BODY * factor
        if a.min_any is None:
            min_any = DEFAULT_MIN_ANY * factor
    issues = []
    for i, slide in enumerate(prs.slides, 1):
        for shp in slide.shapes:
            name = shp.name
            if shp.left is not None and (shp.left < -Emu(9525) or shp.top < -Emu(9525) or
                                         shp.left + shp.width > W + Emu(9525) or shp.top + shp.height > H + Emu(9525)):
                issues.append((i, "off-slide", name))
            if shp.has_text_frame and shp.text_frame.text.strip():
                ratio = est_overflow(shp)
                if ratio > 1.05 and not shp.is_placeholder:
                    issues.append((i, "may-overflow", f"{name} (text ≈ {ratio:.0%} of box height)"))
                for p in shp.text_frame.paragraphs:
                    for r in p.runs:
                        if r.font.size and r.text.strip():
                            if r.font.size.pt < min_any:
                                issues.append((i, "tiny-text", f"{name}: {r.font.size.pt:g} pt '{r.text[:30]}'"))
                            elif r.font.size.pt < min_body and name.startswith("Body"):
                                issues.append((i, "small-body", f"{name}: {r.font.size.pt:g} pt"))
            if shp.shape_type == 13:  # picture
                descr = shp._element.nvPicPr.cNvPr.get("descr")
                if not descr:
                    issues.append((i, "no-alt-text", name))
        if not a.poster and not (slide.has_notes_slide and slide.notes_slide.notes_text_frame.text.strip()):
            issues.append((i, "no-notes", ""))
    print(f"# check_pptx: {Path(a.pptx).name}, {len(prs.slides)} slides, {len(issues)} issue(s)")
    for s, kind, what in issues:
        print(f"- slide {s}: {kind} {what}")
    if a.render:
        print(render(Path(a.pptx), Path(a.render), (W, H)))
    serious = [x for x in issues if x[1] in ("off-slide", "may-overflow", "tiny-text")]
    return 1 if serious else 0


if __name__ == "__main__":
    sys.exit(main())
