import json
import re
import struct
import subprocess
import sys
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
        self.assertEqual(ed.count('<div class="col box" data-area="col-'), 3)
        self.assertEqual(pw.count('<div class="col box" data-area="col-'), 2)
        self.assertEqual(fl.count('<div class="col box" data-area="col-'), 3)
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

    def test_hero_wide_figure_takes_full_width(self):
        spec = pb.load_spec(self.root, self.poster / "poster.json")
        make_png(self.root / "07_present" / "figures" / "F1.png", 600, 200)
        spec["sections"][1]["body"] = ""
        assets = pb.Assets(self.root, self.poster)
        geo = pb.geometry("figure-led", spec, assets)  # 600 x 200: very wide
        self.assertTrue(geo["hero_wide"])
        self.assertAlmostEqual(geo["hero_w"], geo["inner_w"])
        (self.poster / "poster.json").write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
        run(self.root, layouts=["figure-led"])
        self.assertIn('class="hero-row wide"', self.html("figure-led"))

    def test_hero_tall_figure_sits_beside_key_message(self):
        make_png(self.root / "07_present" / "figures" / "F1.png", 400, 400)
        run(self.root, layouts=["figure-led"])
        h = self.html("figure-led")
        self.assertIn('class="hero-row "', h)
        self.assertLess(h.index('data-area="hero"'), h.index('class="key-side box"'))

    def test_body_pt_per_layout(self):
        spec = pb.load_spec(self.root, self.poster / "poster.json")
        spec["body_pt"] = {"editorial": 50, "pathway": 40}
        self.assertEqual(pb.body_pt_of(spec, "editorial"), 50.0)
        self.assertEqual(pb.body_pt_of(spec, "figure-led"), float(pb.BODY_PT["figure-led"]))
        raw = json.loads((self.poster / "poster.json").read_text(encoding="utf-8"))
        raw["body_pt"] = {"poster": 40}
        (self.poster / "poster.json").write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
        rc, _, errs = run(self.root)
        self.assertEqual(rc, 2)

    def test_scale_uses_the_limiting_side(self):
        spec = pb.load_spec(self.root, self.poster / "poster.json")
        spec["size_cm"] = [120.0, 90.0]
        self.assertAlmostEqual(pb.geometry("editorial", spec)["k"], 0.75)
        spec["size_cm"] = [90.0, 120.0]
        self.assertAlmostEqual(pb.geometry("editorial", spec)["k"], 1.0)

    def test_distribute_balances_estimated_heights(self):
        secs = [{"heading": str(i)} for i in range(5)]
        cols = pb.distribute(secs, 3, [10, 10, 30, 10, 10])
        self.assertEqual(cols, [[0, 1], [2], [3, 4]])
        cols = pb.distribute(secs, 2, [10, 10, 10, 10, 10])
        self.assertEqual(sorted(len(c) for c in cols), [2, 3])
        self.assertEqual(sum(cols, []), [0, 1, 2, 3, 4])

    def test_poster_profile_figure_preferred(self):
        figs = self.root / "07_present" / "figures"
        make_png(figs / "F1.poster.png", 300, 600)
        info = pb.Assets(self.root, self.poster).figure("F1")
        self.assertTrue(str(info["png"]).endswith("F1.poster.png"))
        self.assertAlmostEqual(info["aspect"], 2.0)
        run(self.root, layouts=["editorial"])
        self.assertIn("F1.poster.png", self.html("editorial"))

    def test_template_tokens_in_user_text_stay_literal(self):
        spec = json.loads((self.poster / "poster.json").read_text(encoding="utf-8"))
        spec["title"] = "Tiêu đề %%KEY%% và %%COL1%%"
        (self.poster / "poster.json").write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
        run(self.root, layouts=["editorial"])
        h = self.html("editorial")
        self.assertIn("<h1>Tiêu đề %%KEY%% và %%COL1%%</h1>", h)

    def test_invalid_spec_values_exit_2_without_traceback(self):
        bad = [("body_pt", "abc"), ("body_pt", 8), ("colors", {"accent": "red"}), ("size_cm", [90, "x"]),
               ("bleed_mm", "3"), ("references", "not a list"), ("key_message", 5)]
        for key, val in bad:
            spec = json.loads((self.poster / "poster.json").read_text(encoding="utf-8"))
            spec[key] = val
            (self.poster / "poster.json").write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
            rc, _, errs = run(self.root)
            self.assertEqual(rc, 2, (key, val))
            self.assertTrue(errs and "poster_build:" in errs[0], (key, val))
            spec.pop(key)
            (self.poster / "poster.json").write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")

    def test_bad_lab_flag_exits_2(self):
        spec = json.loads((self.poster / "poster.json").read_text(encoding="utf-8"))
        spec["sections"][2]["lab_table"][0]["flag"] = "HIGH"
        (self.poster / "poster.json").write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
        rc, _, errs = run(self.root)
        self.assertEqual(rc, 2)
        self.assertTrue(any("flag" in e for e in errs))

    def test_year_at_line_start_is_not_a_list(self):
        out = pb.md_to_html("2023. Kết quả được công bố.")
        self.assertEqual(out, "<p>2023. Kết quả được công bố.</p>")
        self.assertIn("<ol>", pb.md_to_html("1. một\n2. hai"))
        self.assertIn("<ol>", pb.md_to_html("12) mười hai"))
        self.assertNotIn("<ol>", pb.md_to_html("Dòng một\n2. không phải danh sách"))

    def test_empty_key_message_prints_no_rules(self):
        spec = json.loads((self.poster / "poster.json").read_text(encoding="utf-8"))
        spec["key_message"] = ""
        (self.poster / "poster.json").write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
        run(self.root)
        for layout in pb.LAYOUTS:
            h = self.html(layout)
            self.assertNotIn('<div class="key">', h)
            self.assertNotIn('class="key-band', h)
            self.assertNotIn('class="key-side', h)

    def test_figure_led_skipped_when_no_figure_others_still_build(self):
        spec = json.loads((self.poster / "poster.json").read_text(encoding="utf-8"))
        for sec in spec["sections"]:
            sec.pop("figure", None)
        (self.poster / "poster.json").write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
        rc, _, errs = run(self.root)
        self.assertTrue(any("figure-led skipped" in e for e in errs))
        self.assertTrue((self.poster / "editorial.html").exists())
        self.assertTrue((self.poster / "pathway.html").exists())
        self.assertFalse((self.poster / "figure-led.html").exists())

    def test_browser_command_sandbox_flag_only_off_windows(self):
        old = pb.sys.platform
        try:
            pb.sys.platform = "linux"
            self.assertIn("--no-sandbox", pb._browser_cmd("chrome", "/tmp/x", []))
            pb.sys.platform = "win32"
            self.assertNotIn("--no-sandbox", pb._browser_cmd("chrome", "C:/x", []))
        finally:
            pb.sys.platform = old

    def test_timeout_kills_the_process(self):
        import subprocess
        import time
        t0 = time.time()
        with self.assertRaises(subprocess.TimeoutExpired):
            pb._run_cmd([sys.executable, "-c", "import time; time.sleep(60)"], 1.5)
        self.assertLess(time.time() - t0, 30)

    def test_explicit_column_wins(self):
        spec = json.loads((self.poster / "poster.json").read_text(encoding="utf-8"))
        spec["sections"][0]["column"] = 3
        (self.poster / "poster.json").write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
        run(self.root, layouts=["editorial"])
        h = self.html("editorial")
        col3 = h.split('<div class="col box" data-area="col-')[3]
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
            self.assertFalse([e for e in errs if "overflow" in e], errs)
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
            pdf = (poster / "editorial.pdf").read_bytes()
            box = re.search(rb"/MediaBox\s*\[\s*0\s+0\s+([\d.]+)\s+([\d.]+)\s*\]", pdf)
            self.assertTrue(box)
            self.assertAlmostEqual(float(box.group(1)), 20.6 / 2.54 * 72, delta=1.5)  # 20 cm + 2 x 3 mm bleed
            self.assertAlmostEqual(float(box.group(2)), 30.6 / 2.54 * 72, delta=1.5)
            self.assertEqual(len(re.findall(rb"/Type\s*/Page[^s]", pdf)), 1)
            self.assertRegex(dom, r'data-fill="[\d.]+"')

    def test_overflow_and_underfill_are_reported(self):
        with tempfile.TemporaryDirectory(prefix="poster qua ") as tmp:
            root = make_project(Path(tmp) / "p", size=(20, 30), svg=True)
            poster = root / "07_present" / "poster"
            spec = json.loads((poster / "poster.json").read_text(encoding="utf-8"))
            spec["sections"][0]["body"] = "Rất dài. " * 400
            spec["sections"][0]["column"] = 1
            spec["sections"][4]["column"] = 3
            (poster / "poster.json").write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
            rc, msgs, errs = run(root, layouts=["editorial"], browser=BROWSER)
            self.assertTrue([e for e in errs if "overflow" in e], errs)
            self.assertTrue([e for e in errs if "% full" in e], errs)

    def test_landscape_poster_no_overflow_in_any_layout(self):
        with tempfile.TemporaryDirectory(prefix="poster ngang ") as tmp:
            root = make_project(Path(tmp) / "p", size=(40, 30), svg=True,
                                extra={"title": "Tiêu đề dài hai dòng cho poster khổ ngang, kiểm tra thang chữ"})
            poster = root / "07_present" / "poster"
            spec = pb.load_spec(root, poster / "poster.json")
            assets = pb.Assets(root, poster)
            for layout in pb.LAYOUTS:
                html_path = poster / f"{layout}.html"
                html_path.write_text(pb.build_html(layout, spec, assets, poster), encoding="utf-8")
                pb.run_browser(BROWSER, html_path, poster / layout, pb.geometry(layout, spec, assets), outputs=("dom",))
                dom = (poster / f"{layout}.dom.html").read_text(encoding="utf-8")
                self.assertIn('data-preflight="done"', dom)
                over = re.findall(r'<(\w+) class="([^"]*)"[^>]*data-overflow="1"', dom)
                self.assertEqual(over, [], layout)

    def test_hero_figure_fills_its_box(self):
        for size, label in (((20, 30), "wide"), ((30, 30), "tall")):
            with tempfile.TemporaryDirectory(prefix="poster hero ") as tmp:
                root = make_project(Path(tmp) / "p", size=size, svg=(label == "wide"))
                if label == "tall":
                    make_png(root / "07_present" / "figures" / "F1.png", 400, 400)
                poster = root / "07_present" / "poster"
                spec = pb.load_spec(root, poster / "poster.json")
                assets = pb.Assets(root, poster)
                html_path = poster / "figure-led.html"
                html_path.write_text(pb.build_html("figure-led", spec, assets, poster), encoding="utf-8")
                pb.run_browser(BROWSER, html_path, poster / "figure-led", pb.geometry("figure-led", spec, assets),
                               outputs=("dom",))
                dom = (poster / "figure-led.dom.html").read_text(encoding="utf-8")
                box = re.search(r'class="hero-figure box"[^>]*data-box-w-cm="([\d.]+)"', dom)
                fig = re.search(r'<(?:svg|img)[^>]*data-placed-w-cm="([\d.]+)"', dom[dom.index("hero-figure"):])
                self.assertTrue(box and fig, label)
                self.assertGreaterEqual(float(fig.group(1)), 0.95 * float(box.group(1)), label)

    def test_preflight_reports_the_drawn_size_of_a_letterboxed_image(self):
        with tempfile.TemporaryDirectory(prefix="pre flight ") as tmp:
            tmp = Path(tmp)
            make_png(tmp / "wide.png", 600, 200)
            js = (pb.TEMPLATES / "preflight.js").read_text(encoding="utf-8")
            page = tmp / "t.html"
            page.write_text('<!DOCTYPE html><html><body style="margin:0">'
                            '<img src="wide.png" alt="x" style="display:block;width:10cm;height:20cm;object-fit:contain">'
                            f'<script>{js}</script></body></html>', encoding="utf-8")
            code, out, err = pb._run_cmd(pb._browser_cmd(BROWSER, str(tmp / "ud"), ["--dump-dom", page.as_uri()]), 120)
            dom = out.decode("utf-8")
            self.assertIn('data-preflight="done"', dom)
            w = float(re.search(r'data-placed-w-cm="([\d.]+)"', dom).group(1))
            h = float(re.search(r'data-placed-h-cm="([\d.]+)"', dom).group(1))
            self.assertAlmostEqual(w, 10.0, delta=0.05)
            self.assertAlmostEqual(h, 10.0 / 3, delta=0.05)  # 600 x 200 drawn inside 10 x 20 cm


if __name__ == "__main__":
    unittest.main()
