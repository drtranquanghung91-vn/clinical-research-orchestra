import json
import re
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

import _paths  # noqa: F401
from _paths import ORCH_SCRIPTS

import poster_build as pb

try:
    import pptx  # noqa: F401
    HAVE_PPTX = True
except ImportError:  # pragma: no cover
    HAVE_PPTX = False

BROWSER = pb.find_browser(None)
CSS = ORCH_SCRIPTS.parent / "templates" / "poster" / "poster.css"

LEDGER = {"results": [
    {"id": "R-A1-003", "kind": "or", "value": 1.0975160894901683, "ci": [0.742276835802005, 1.6227659393254874],
     "p": 0.64, "n": 1043},
]}


def make_png(path: Path, w: int, h: int):
    raw = b"".join(b"\x00" + b"\x40\x80\xc0" * w for _ in range(h))

    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


SVG = ('<?xml version="1.0" encoding="utf-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
       'width="200pt" height="100pt" viewBox="0 0 200 100"><defs><clipPath id="p1"><rect width="200" height="100"/></clipPath></defs>'
       '<g clip-path="url(#p1)"><rect width="200" height="100" fill="#ccc"/></g></svg>')


def make_project(root: Path, size=(90, 120), extra=None, svg=False) -> Path:
    (root / "ledgers").mkdir(parents=True)
    (root / "ledgers" / "results-ledger.json").write_text(json.dumps(LEDGER), encoding="utf-8")
    (root / "project.yaml").write_text("language:\n  output: vi\n", encoding="utf-8")
    figs = root / "07_present" / "figures"
    figs.mkdir(parents=True)
    make_png(figs / "F1.png", 600, 300)
    if svg:
        (figs / "F1.svg").write_text(SVG, encoding="utf-8")
    poster = root / "07_present" / "poster"
    poster.mkdir(parents=True)
    spec = {
        "size_cm": list(size), "lang": "vi", "title": "Tiêu đề poster thử",
        "authors": "A, B", "affiliation": "Bệnh viện Mô phỏng",
        "key_message": "OR = {{R-A1-003}} (KTC {{R-A1-003.ci}})",
        "sections": [
            {"heading": "Đặt vấn đề", "body": "Một đoạn với **chữ đậm** và *chữ nghiêng*.\n\n- mục một\n- mục hai"},
            {"heading": "Kết quả", "body": "OR {{R-A1-003}}.\n\n| Chỉ số | Giá trị |\n|---|---|\n| AUC | 0,59 |",
             "figure": {"id": "F1", "caption": "Hình 1.", "alt": "Hình thử"}},
            {"heading": "Xét nghiệm", "lab_table": [
                {"test": "HbA1c", "value": "9,4", "unit": "%", "flag": "high"},
                {"test": "Hb", "value": "10,8", "unit": "g/dL", "flag": "low"},
                {"test": "Glucose", "value": "5,0", "unit": "mmol/L", "flag": "normal"}]},
            {"heading": "Việc cần làm", "checklist": [{"text": "xong", "checked": True}, "chưa xong"]},
            {"heading": "Kết luận", "body": "Hết."},
        ],
        "references": ["Tài liệu 1.", "Tài liệu 2."],
    }
    if extra:
        spec.update(extra)
    (poster / "poster.json").write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
    return root


def run(project, **kw):
    msgs, errs = [], []
    kw.setdefault("browser", None)
    kw.setdefault("pptx", False)
    rc = pb.build(project, out=msgs.append, err=errs.append, **kw)
    return rc, msgs, errs


class TestHtml(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = make_project(Path(self.tmp.name) / "p")
        self.poster = self.root / "07_present" / "poster"

    def tearDown(self):
        self.tmp.cleanup()

    def html(self, layout):
        return (self.poster / f"{layout}.html").read_text(encoding="utf-8")

    def test_page_size_with_bleed(self):
        rc, _, _ = run(self.root)
        self.assertEqual(rc, 2)  # no browser
        for layout in pb.LAYOUTS:
            h = self.html(layout)
            self.assertIn("@page { size: 90.6cm 120.6cm; margin: 0 }", h)
            self.assertIn("--bleed: 0.3cm", h)

    def test_zero_bleed_and_font(self):
        make = Path(self.tmp.name) / "q"
        make_project(make, size=(20, 30), extra={"bleed_mm": 0, "font": "Verdana"})
        run(make)
        h = (make / "07_present" / "poster" / "editorial.html").read_text(encoding="utf-8")
        self.assertIn("size: 20cm 30cm", h)
        self.assertIn("--font: Verdana", h)
        run(self.root)
        self.assertIn('Arial, &quot;Liberation Sans&quot;, sans-serif', self.html("editorial"))

    def test_no_browser_message_and_html_written(self):
        rc, msgs, errs = run(self.root)
        self.assertEqual(rc, 2)
        self.assertTrue(any("no Chrome or Edge" in e for e in errs))
        self.assertEqual(len([m for m in msgs if m.endswith(".html")]), 3)

    def test_placeholders_rendered(self):
        run(self.root)
        h = self.html("editorial")
        self.assertIn("1,10", h)  # vi decimal comma
        self.assertIn("0,74", h)
        self.assertNotIn("{{R-", h)

    def test_unknown_id_exits_2_and_writes_nothing(self):
        spec = json.loads((self.poster / "poster.json").read_text(encoding="utf-8"))
        spec["key_message"] = "{{R-A9-999}}"
        (self.poster / "poster.json").write_text(json.dumps(spec), encoding="utf-8")
        rc, _, errs = run(self.root)
        self.assertEqual(rc, 2)
        self.assertTrue(any("R-A9-999" in e for e in errs))
        self.assertFalse((self.poster / "editorial.html").exists())

    def test_layouts_differ(self):
        run(self.root)
        ed, pw, fl = (self.html(x) for x in pb.LAYOUTS)
        self.assertEqual(fl.count('class="hero-figure box"'), 1)
        self.assertEqual(ed.count("hero-figure box"), 0)
        self.assertEqual(ed.count('<div class="col box">'), 3)
        self.assertEqual(pw.count('<div class="col box">'), 2)
        self.assertEqual(fl.count('<div class="col box">'), 3)
        self.assertIn('class="step"', pw)
        self.assertNotIn('class="step"', ed)
        self.assertIn('class="key-band box"', pw)
        self.assertIn("figure-led", fl)
        self.assertEqual(len({ed, pw, fl}), 3)
        for h in (ed, pw, fl):
            self.assertIn('data-fig="F1"', h)
            self.assertIn("document.body.dataset.preflight", h)  # preflight.js inlined
            self.assertEqual(h.count("<style>"), 1)

    def test_layout_option(self):
        rc, msgs, _ = run(self.root, layouts=["pathway"])
        self.assertTrue((self.poster / "pathway.html").exists())
        self.assertFalse((self.poster / "editorial.html").exists())

    def test_layouts_from_spec(self):
        spec = json.loads((self.poster / "poster.json").read_text(encoding="utf-8"))
        spec["layouts"] = ["editorial"]
        (self.poster / "poster.json").write_text(json.dumps(spec), encoding="utf-8")
        run(self.root)
        self.assertTrue((self.poster / "editorial.html").exists())
        self.assertFalse((self.poster / "pathway.html").exists())

    def test_css_has_no_decoration(self):
        css = CSS.read_text(encoding="utf-8").lower()
        for bad in ("border-radius", "gradient", "box-shadow", "text-shadow"):
            self.assertNotIn(bad, css)

    def test_lab_table_arrows(self):
        run(self.root)
        h = self.html("editorial")
        self.assertIn('<tr class="high">', h)
        self.assertRegex(h, r'9,4 <span class="arrow">↑</span>')
        self.assertRegex(h, r'10,8 <span class="arrow">↓</span>')
        self.assertRegex(h, r'5,0 <span class="arrow"></span>')

    def test_checklist_marks(self):
        run(self.root)
        h = self.html("pathway")
        self.assertIn('<span class="mark">☑</span>xong', h)
        self.assertIn('<span class="mark">☐</span>chưa xong', h)

    def test_markdown_subset(self):
        out = pb.md_to_html("# Tiêu đề\n\nMột **đậm** và *nghiêng* <b>\n\n- a\n- b\n\n1. x\n2. y\n\n| H1 | H2 |\n|---|:-:|\n| 1 | **2** |")
        self.assertIn("<h3>Tiêu đề</h3>", out)
        self.assertIn("<strong>đậm</strong>", out)
        self.assertIn("<em>nghiêng</em>", out)
        self.assertIn("&lt;b&gt;", out)
        self.assertIn("<ul><li>a</li><li>b</li></ul>", out)
        self.assertIn("<ol><li>x</li><li>y</li></ol>", out)
        self.assertIn("<th>H1</th><th>H2</th>", out)
        self.assertIn("<td><strong>2</strong></td>", out)

    def test_svg_inlined_with_raster_and_prefixed_ids(self):
        root = make_project(Path(self.tmp.name) / "s", svg=True)
        run(root, layouts=["editorial"])
        h = (root / "07_present" / "poster" / "editorial.html").read_text(encoding="utf-8")
        self.assertIn('data-raster="../figures/F1.png"', h)
        self.assertIn('id="F1-p1"', h)
        self.assertIn("url(#F1-p1)", h)
        self.assertNotIn("<?xml", h)
        self.assertNotRegex(h, r'<svg[^>]* width="200pt"')

    def test_png_only_figure_uses_img(self):
        run(self.root, layouts=["editorial"])
        self.assertIn('<img src="../figures/F1.png" alt="Hình thử">', self.html("editorial"))

    def test_figure_led_needs_a_figure(self):
        spec = json.loads((self.poster / "poster.json").read_text(encoding="utf-8"))
        for s in spec["sections"]:
            s.pop("figure", None)
        (self.poster / "poster.json").write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
        rc, _, errs = run(self.root, layouts=["figure-led"])
        self.assertEqual(rc, 2)
        self.assertTrue(any("figure" in e for e in errs))

    def test_missing_figure_exits_2(self):
        (self.root / "07_present" / "figures" / "F1.png").unlink()
        rc, _, errs = run(self.root, layouts=["editorial"])
        self.assertEqual(rc, 2)
        self.assertTrue(any("F1" in e for e in errs))

    def test_hero_covers_45_percent(self):
        spec = pb.load_spec(self.root, self.poster / "poster.json")
        geo = pb.geometry("figure-led", spec)
        self.assertGreaterEqual(geo["hero_w"] * geo["hero_h"] / (geo["inner_w"] * geo["main_h"]), 0.45)

    def test_explicit_column_wins(self):
        spec = json.loads((self.poster / "poster.json").read_text(encoding="utf-8"))
        spec["sections"][0]["column"] = 3
        (self.poster / "poster.json").write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
        run(self.root, layouts=["editorial"])
        h = self.html("editorial")
        col3 = h.split('<div class="col box">')[3]
        self.assertIn("Đặt vấn đề", col3)

    def test_bad_size(self):
        spec = json.loads((self.poster / "poster.json").read_text(encoding="utf-8"))
        spec["size_cm"] = [200, 300]
        (self.poster / "poster.json").write_text(json.dumps(spec), encoding="utf-8")
        rc, _, errs = run(self.root)
        self.assertEqual(rc, 2)

    def test_find_browser_explicit_path(self):
        self.assertIsNone(pb.find_browser(str(Path(self.tmp.name) / "nope.exe")))
        f = Path(self.tmp.name) / "b.exe"
        f.write_text("x")
        self.assertEqual(pb.find_browser(str(f)), str(f))


@unittest.skipUnless(HAVE_PPTX, "python-pptx not installed")
class TestPptx(unittest.TestCase):
    def test_one_slide_at_poster_size(self):
        from pptx import Presentation
        with tempfile.TemporaryDirectory() as tmp:
            root = make_project(Path(tmp) / "p")
            for layout in pb.LAYOUTS:
                rc, msgs, errs = run(root, layouts=[layout], pptx=True)
                out = root / "07_present" / "poster" / f"{layout}.pptx"
                self.assertTrue(out.is_file(), errs)
                prs = Presentation(str(out))
                self.assertEqual(len(prs.slides), 1)
                self.assertAlmostEqual(prs.slide_width / 360000, 90, places=1)
                self.assertAlmostEqual(prs.slide_height / 360000, 120, places=1)
                shapes = prs.slides[0].shapes
                self.assertTrue(any(s.has_table for s in shapes if hasattr(s, "has_table")))
                self.assertTrue(any(s.shape_type == 13 for s in shapes))  # picture
                self.assertTrue((root / "07_present" / "poster" / f"{layout}.spec.json").is_file())
                self.assertTrue(any(m.endswith(f"{layout}.pptx") for m in msgs))


@unittest.skipUnless(BROWSER, "no Chrome or Edge found")
class TestBrowser(unittest.TestCase):
    def test_small_poster_builds_pdf_png_dom(self):
        with tempfile.TemporaryDirectory(prefix="poster có dấu ") as tmp:
            root = make_project(Path(tmp) / "dự án mẫu", size=(20, 30), svg=True)
            rc, msgs, errs = run(root, layouts=["editorial"], browser=BROWSER)
            self.assertEqual(rc, 0, errs)
            poster = root / "07_present" / "poster"
            for ext in (".pdf", ".png", ".dom.html"):
                self.assertTrue((poster / f"editorial{ext}").stat().st_size > 1000, ext)
            dom = (poster / "editorial.dom.html").read_text(encoding="utf-8")
            self.assertIn('data-preflight="done"', dom)
            self.assertRegex(dom, r'data-natural-w="\d+"')
            self.assertRegex(dom, r'data-placed-w-cm="[\d.]+"')
            png = (poster / "editorial.png").read_bytes()
            w, h = struct.unpack(">II", png[16:24])
            long_side = max(w, h)
            self.assertLess(abs(long_side - 2000) / 2000, 0.10, (w, h))


if __name__ == "__main__":
    unittest.main()
