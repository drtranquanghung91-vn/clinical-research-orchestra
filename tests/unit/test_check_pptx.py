import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
from _paths import ORCH_SCRIPTS

SCRIPT = ORCH_SCRIPTS / "check_pptx.py"
HAVE = importlib.util.find_spec("pptx") is not None
if HAVE:
    import check_pptx
    import pptx_from_spec
    from pptx import Presentation
    from pptx.util import Cm, Inches, Pt


def run(args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = check_pptx.main(args)
    return rc, buf.getvalue()


def deck(path, width=None, height=None, notes=True, boxes=()):
    """boxes: (x_in, y_in, w_in, h_in, text, pt, name)."""
    prs = Presentation()
    if width:
        prs.slide_width, prs.slide_height = width, height
    s = prs.slides.add_slide(prs.slide_layouts[6])
    for x, y, w, h, text, pt, name in boxes:
        tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tb.name = name
        tb.text_frame.word_wrap = True
        r = tb.text_frame.paragraphs[0].add_run()
        r.text = text
        r.font.size = Pt(pt)
    if notes:
        s.notes_slide.notes_text_frame.text = "note"
    prs.save(str(path))
    return s


@unittest.skipUnless(HAVE, "python-pptx not installed")
class TestCheck(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.tmp = Path(self._t.name)

    def tearDown(self):
        self._t.cleanup()

    def test_clean_deck(self):
        deck(self.tmp / "a.pptx", boxes=[(1, 1, 8, 1, "Hello", 24, "Body")])
        rc, out = run([str(self.tmp / "a.pptx")])
        self.assertEqual(rc, 0, out)
        self.assertIn("0 issue(s)", out)

    def test_leftover_markup_in_slide_text(self):
        for text in ("Nguy cơ cao hơn [@hu2026]", "@hu2026 thấy nguy cơ cao hơn",
                     "Xem `05_analysis/plan.md`", "Tỉ lệ {{R-A0-001}}"):
            with self.subTest(text=text):
                deck(self.tmp / "m.pptx", boxes=[(1, 1, 8, 1, text, 24, "Body")])
                rc, out = run([str(self.tmp / "m.pptx")])
                self.assertEqual(rc, 1, out)
                self.assertIn("leftover-markup", out)

    def test_email_and_plain_text_not_markup(self):
        deck(self.tmp / "e.pptx", boxes=[(1, 1, 8, 1, "Liên hệ [ab@example.org]; Hu và cs., 2026", 24, "Body")])
        rc, out = run([str(self.tmp / "e.pptx")])
        self.assertEqual(rc, 0, out)
        self.assertNotIn("leftover-markup", out)

    def test_leftover_markup_in_table_and_group(self):
        prs = Presentation()
        s = prs.slides.add_slide(prs.slide_layouts[6])
        tbl = s.shapes.add_table(2, 2, Inches(1), Inches(1), Inches(6), Inches(2)).table
        tbl.cell(1, 1).text = "OR 1,8 [@american2026]"
        grp = s.shapes.add_group_shape()
        tb = grp.shapes.add_textbox(Inches(1), Inches(4), Inches(6), Inches(1))
        tb.text_frame.text = "Nguồn: `ledger`"
        s.notes_slide.notes_text_frame.text = "note"
        prs.save(str(self.tmp / "t.pptx"))
        rc, out = run([str(self.tmp / "t.pptx")])
        self.assertEqual(rc, 1, out)
        self.assertEqual(out.count("leftover-markup"), 2, out)
        self.assertIn("[@american2026]", out)

    def test_markup_in_notes_ignored(self):
        deck(self.tmp / "n.pptx", boxes=[(1, 1, 8, 1, "Hello", 24, "Body")])
        prs = Presentation(str(self.tmp / "n.pptx"))
        prs.slides[0].notes_slide.notes_text_frame.text = "Đọc [@hu2026] và `plan.md` {{R-A0-001}}"
        prs.save(str(self.tmp / "n.pptx"))
        rc, out = run([str(self.tmp / "n.pptx")])
        self.assertEqual(rc, 0, out)
        self.assertNotIn("leftover-markup", out)

    def test_off_slide_flagged(self):
        deck(self.tmp / "a.pptx", boxes=[(12, 1, 4, 1, "Hello", 24, "Body")])
        rc, out = run([str(self.tmp / "a.pptx")])
        self.assertEqual(rc, 1)
        self.assertIn("off-slide", out)

    def test_missing_notes_flagged_but_not_serious(self):
        deck(self.tmp / "a.pptx", notes=False, boxes=[(1, 1, 8, 1, "Hello", 24, "Body")])
        rc, out = run([str(self.tmp / "a.pptx")])
        self.assertEqual(rc, 0)
        self.assertIn("no-notes", out)

    def test_overflow_and_tiny_text(self):
        deck(self.tmp / "a.pptx", boxes=[(1, 1, 2, 0.4, "word " * 80, 24, "Body"),
                                         (1, 5, 3, 0.5, "tiny", 8, "Note")])
        rc, out = run([str(self.tmp / "a.pptx")])
        self.assertEqual(rc, 1)
        self.assertIn("may-overflow", out)
        self.assertIn("tiny-text", out)

    def test_small_body_and_min_flags(self):
        deck(self.tmp / "a.pptx", boxes=[(1, 1, 8, 1, "Hello", 14, "Body")])
        rc, out = run([str(self.tmp / "a.pptx")])
        self.assertIn("small-body", out)
        rc, out = run([str(self.tmp / "a.pptx"), "--min-body", "12"])
        self.assertNotIn("small-body", out)
        rc, out = run([str(self.tmp / "a.pptx"), "--min-any", "20"])
        self.assertEqual(rc, 1)
        self.assertIn("tiny-text", out)

    def test_no_alt_text(self):
        from PIL import Image
        Image.new("RGB", (40, 30), "white").save(self.tmp / "p.png")
        prs = Presentation()
        s = prs.slides.add_slide(prs.slide_layouts[6])
        pic = s.shapes.add_picture(str(self.tmp / "p.png"), Inches(1), Inches(1), Inches(2), Inches(1.5))
        s.notes_slide.notes_text_frame.text = "n"
        pic._element.nvPicPr.cNvPr.set("descr", "")  # python-pptx defaults alt text to the file name
        prs.save(str(self.tmp / "a.pptx"))
        rc, out = run([str(self.tmp / "a.pptx")])
        self.assertIn("no-alt-text", out)
        pic._element.nvPicPr.cNvPr.set("descr", "a picture")
        prs.save(str(self.tmp / "b.pptx"))
        rc, out = run([str(self.tmp / "b.pptx")])
        self.assertNotIn("no-alt-text", out)

    def test_poster_skips_notes_and_scales_floor(self):
        w, h = Cm(90), Cm(120)
        # 20 pt body at 90 cm wide is below the 24 pt poster floor; a missing note is fine for a poster
        deck(self.tmp / "p.pptx", w, h, notes=False, boxes=[(1, 1, 20, 3, "Hello", 20, "Body")])
        rc, out = run([str(self.tmp / "p.pptx"), "--poster"])
        self.assertNotIn("no-notes", out)
        self.assertIn("small-body", out)
        rc, out = run([str(self.tmp / "p.pptx")])
        self.assertIn("no-notes", out)
        self.assertNotIn("small-body", out)
        deck(self.tmp / "q.pptx", w, h, notes=False, boxes=[(1, 1, 20, 3, "Hello", 30, "Body")])
        rc, out = run([str(self.tmp / "q.pptx"), "--poster"])
        self.assertEqual(rc, 0, out)
        self.assertNotIn("small-body", out)

    def test_poster_floor_scales_with_width(self):
        # 20 x 30 cm poster: floor is 24 * 20/90 pt, so 10 pt text is fine
        deck(self.tmp / "s.pptx", Cm(20), Cm(30), notes=False, boxes=[(0.5, 0.5, 6, 1, "Hello", 10, "Body")])
        rc, out = run([str(self.tmp / "s.pptx"), "--poster"])
        self.assertEqual(rc, 0, out)

    def test_built_deck_passes(self):
        # ported from grand-rounds test_tools.TestPptx: build with pptx_from_spec, then check
        from PIL import Image
        spec = {"cite": "Source A, 2026", "slides": [
            {"type": "title", "title": "Talk", "presenter": "Presenter", "notes": "n"},
            {"type": "bullets", "title": "Point", "bullets": ["one", {"text": "two", "level": 1}], "notes": "n"},
            {"type": "diagram", "title": "Schema", "notes": "n", "nodes": [
                {"id": "a", "x": 0, "y": 0.3, "w": 0.3, "h": 0.3, "text": "A"},
                {"id": "b", "x": 0.6, "y": 0.3, "w": 0.3, "h": 0.3, "text": "B", "style": "int"}],
             "edges": [{"from": "a", "to": "b"}]},
            {"type": "chart", "title": "AEs", "chart": "bar", "categories": ["x", "y"],
             "series": [{"name": "A", "values": [1.5, 2.5], "color": "intervention"}], "notes": "n"},
            {"type": "table", "title": "T", "columns": ["a", "b"], "rows": [["1", "2"]], "notes": "n"},
            {"type": "figure", "title": "Labelled", "image": "pic.png", "notes": "n",
             "labels": [{"text": "Left", "at": [0.2, 0.3], "side": "left"},
                        {"text": "Right", "at": [0.8, 0.6], "side": "right"}]}]}
        Image.new("RGB", (400, 300), "white").save(self.tmp / "pic.png")
        (self.tmp / "deck.json").write_text(json.dumps(spec), encoding="utf-8")
        self.assertEqual(pptx_from_spec.main([str(self.tmp / "deck.json"), str(self.tmp / "o.pptx")]), 0)
        rc, out = run([str(self.tmp / "o.pptx")])
        self.assertEqual(rc, 0, out)

    def test_poster_built_from_spec_passes(self):
        spec = {"size_cm": [90, 120], "slides": [
            {"type": "bullets", "title": "Poster", "bullets": ["one finding", "another finding"]}]}
        (self.tmp / "deck.json").write_text(json.dumps(spec), encoding="utf-8")
        self.assertEqual(pptx_from_spec.main([str(self.tmp / "deck.json"), str(self.tmp / "o.pptx")]), 0)
        rc, out = run([str(self.tmp / "o.pptx"), "--poster"])
        self.assertEqual(rc, 0, out)

    def test_bad_file_exit_2(self):
        (self.tmp / "x.pptx").write_text("not a pptx", encoding="utf-8")
        r = subprocess.run([sys.executable, str(SCRIPT), str(self.tmp / "x.pptx")],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 2)

    def test_missing_file_exit_2(self):
        r = subprocess.run([sys.executable, str(SCRIPT), str(self.tmp / "none.pptx")],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 2)


@unittest.skipUnless(HAVE, "python-pptx not installed")
class TestRenderAspect(unittest.TestCase):
    def test_png_export_uses_slide_aspect(self):
        from unittest import mock
        calls = []

        def fake_run(args, **kw):
            calls.append(" ".join(map(str, args)))
            return mock.Mock(returncode=1, stdout="", stderr="")
        with tempfile.TemporaryDirectory() as t, mock.patch.object(check_pptx.sys, "platform", "win32"), \
                mock.patch.object(check_pptx.subprocess, "run", fake_run), \
                mock.patch.object(check_pptx.shutil, "which", lambda *_: None):
            check_pptx.render(Path(t) / "a.pptx", Path(t) / "r", (Cm(90), Cm(120)))
        self.assertTrue(any("1920,2560" in c for c in calls), calls)


class TestMissingDependency(unittest.TestCase):
    def test_hint_and_exit_2(self):
        code = ("import sys, runpy; sys.modules['pptx'] = None; sys.argv = [%r, 'a.pptx']; "
                "runpy.run_path(%r, run_name='__main__')" % (str(SCRIPT), str(SCRIPT)))
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 2)
        self.assertIn("python -m pip install python-pptx", r.stderr)


if __name__ == "__main__":
    unittest.main()
