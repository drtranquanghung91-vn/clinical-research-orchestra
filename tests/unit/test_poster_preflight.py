import json
import re
import tempfile
import unittest
import zlib
from pathlib import Path

import _paths  # noqa: F401
from _paths import ORCH_SCRIPTS  # noqa: F401

import poster_build as pb
import poster_preflight as pp
import test_poster_build as tpb

BROWSER = pb.find_browser(None)
PT = 72 / 25.4  # points per mm


def pdf_bytes(w_mm, h_mm, fonts=(("Arial", True),), compress=False) -> bytes:
    """A tiny hand-written PDF: one page with a MediaBox and one FontDescriptor per (name, embedded)."""
    box = f"/MediaBox [0 0 {w_mm * PT:.3f} {h_mm * PT:.3f}]"
    descs = []
    for i, (name, emb) in enumerate(fonts):
        ff = "/FontFile2 9 0 R " if emb else ""
        descs.append(f"<</Type /FontDescriptor /FontName /AAAAAA+{name} /Flags 4 {ff}/ItalicAngle 0>>")
    if not compress:
        body = (f"%PDF-1.4\n1 0 obj\n<</Type /Page /Parent 2 0 R {box}>>\nendobj\n"
                + "".join(f"{10 + i} 0 obj\n{d}\nendobj\n" for i, d in enumerate(descs)) + "%%EOF\n")
        return body.encode("latin-1")
    inner = f"<</Type /Page /Parent 2 0 R {box}>>\n" + "\n".join(descs)
    z = zlib.compress(inner.encode("latin-1"))
    return (b"%PDF-1.5\n5 0 obj\n<</Type /ObjStm /N 2 /First 10 /Filter /FlateDecode /Length "
            + str(len(z)).encode() + b">>\nstream\n" + z + b"\nendstream\nendobj\n%%EOF\n")


def dom(images=(), boxes=(), done=True, alt=True) -> str:
    """DOM dump: images = (src, natural_w, placed_w_cm); boxes = (data_area, heading, overflow, font_pt)."""
    parts = ['<!DOCTYPE html><html><body' + (' data-preflight="done"' if done else "") + '><div class="sheet">']
    for area, head, over, fpt in boxes:
        a = f'data-area="{area}"' + (' data-overflow="1"' if over else "") + (f' data-font-pt="{fpt}"' if fpt else "")
        parts.append(f'<div class="col box" {a}><section class="sec"><h2>{head}</h2><p>x</p></section></div>')
    for src, nat, placed in images:
        altattr = ' alt="Forest plot"' if alt else ""
        parts.append(f'<img src="../figures/{src}"{altattr} data-natural-w="{nat}" data-natural-h="300" '
                     f'data-placed-w-cm="{placed}" data-placed-h-cm="9">')
    parts.append("</div></body></html>")
    return "\n".join(parts)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = tpb.make_project(Path(self.tmp.name) / "p")
        self.poster = self.root / "07_present" / "poster"

    def tearDown(self):
        self.tmp.cleanup()

    def spec(self, **kw):
        p = self.poster / "poster.json"
        d = json.loads(p.read_text(encoding="utf-8"))
        d.update(kw)
        p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")

    def put(self, pdf=None, domtext=None, layout="editorial"):
        if pdf is not None:
            (self.poster / f"{layout}.pdf").write_bytes(pdf)
        if domtext is not None:
            (self.poster / f"{layout}.dom.html").write_text(domtext, encoding="utf-8")

    def go(self, layouts=("editorial",)):
        out, err = [], []
        rc = pp.run(self.root, list(layouts), out=out.append, err=err.append)
        return rc, out, err

    GOOD_DOM = None


class TestPdf(Base):
    def setUp(self):
        super().setUp()
        self.spec(size_cm=[90, 120])
        self.good_dom = dom(images=[("F1.png", 1200, 17.5)], boxes=[("col-1", "Kết quả", False, "30.00")])

    def test_clean(self):
        self.put(pdf_bytes(906, 1206), self.good_dom)
        rc, out, err = self.go()
        self.assertEqual(rc, 0, err)
        self.assertEqual(err, [])
        self.assertEqual(out, ["poster_preflight: editorial: 0 block, 0 warn"])

    def test_unembedded_font_blocks_by_name(self):
        self.put(pdf_bytes(906, 1206, fonts=(("Arial", True), ("Calibri", False))), self.good_dom)
        rc, out, err = self.go()
        self.assertEqual(rc, 1)
        self.assertEqual(len(err), 1, err)
        self.assertRegex(err[0], r"^E-PRINT block editorial\.pdf:1: font not embedded: .*Calibri")
        self.assertEqual(out, ["poster_preflight: editorial: 1 block, 0 warn"])

    def test_no_descriptor_is_not_checked_not_passed(self):
        data = f"%PDF-1.4\n1 0 obj\n<</Type /Page /MediaBox [0 0 {906 * PT:.3f} {1206 * PT:.3f}]>>\nendobj\n".encode()
        self.put(data, self.good_dom)
        rc, out, err = self.go()
        self.assertEqual(rc, 0)
        self.assertEqual(len(err), 1)
        self.assertIn("E-PRINT warn editorial.pdf:1: not checked by script", err[0])
        self.assertEqual(out, ["poster_preflight: editorial: 0 block, 1 warn"])

    def test_base_font_without_descriptor_blocks(self):
        data = pdf_bytes(906, 1206) + b"20 0 obj\n<</Type /Font /Subtype /Type1 /BaseFont /Helvetica>>\nendobj\n"
        self.put(data, self.good_dom)
        rc, out, err = self.go()
        self.assertEqual(rc, 1)
        self.assertIn("font not embedded: Helvetica", err[0])

    def test_page_one_cm_off_blocks(self):
        self.put(pdf_bytes(916, 1206), self.good_dom)
        rc, out, err = self.go()
        self.assertEqual(rc, 1)
        self.assertRegex(err[0], r"page size 916\.0 x 1206\.0 mm, expected 906\.0 x 1206\.0 mm")

    def test_half_millimetre_is_within_tolerance(self):
        self.put(pdf_bytes(906.5, 1205.6), self.good_dom)
        self.assertEqual(self.go()[0], 0)

    def test_bleed_requested_but_page_is_trim_size(self):
        self.put(pdf_bytes(900, 1200), self.good_dom)
        rc, out, err = self.go()
        self.assertEqual(rc, 1)
        self.assertIn("bleed requested (3 mm) but the page is the trim size", err[0])

    def test_zero_bleed_trim_page_is_clean(self):
        self.spec(bleed_mm=0)
        self.put(pdf_bytes(900, 1200), self.good_dom)
        self.assertEqual(self.go()[0], 0)

    def test_flate_compressed_object_stream_is_parsed(self):
        self.put(pdf_bytes(906, 1206, compress=True), self.good_dom)
        self.assertEqual(self.go()[0], 0)
        self.put(pdf_bytes(916, 1206, compress=True), self.good_dom)
        self.assertEqual(self.go()[0], 1)
        self.put(pdf_bytes(906, 1206, fonts=(("Calibri", False),), compress=True), self.good_dom)
        rc, out, err = self.go()
        self.assertEqual(rc, 1)
        self.assertIn("Calibri", err[0])

    def test_unreadable_pdf_is_not_checked(self):
        self.put(b"not a pdf", self.good_dom)
        rc, out, err = self.go()
        self.assertEqual(rc, 0)
        self.assertTrue(any("not checked by script" in e and "MediaBox" in e for e in err), err)

    def test_media_box_with_integers_and_offset(self):
        self.assertEqual(pp.media_box(b"/MediaBox [0 0 595 842]"), (595.0, 842.0))
        self.assertEqual(pp.media_box(b"/MediaBox[ 10 10 605.5 852 ]"), (595.5, 842.0))


class TestDom(Base):
    def setUp(self):
        super().setUp()
        self.spec(size_cm=[90, 120])
        self.pdf = pdf_bytes(906, 1206)

    def run_dom(self, **kw):
        self.put(self.pdf, dom(**kw))
        return self.go()

    def test_87_dpi_blocks_and_names_the_pixels_needed(self):
        rc, out, err = self.run_dom(images=[("F1.png", 600, 17.5)])
        self.assertEqual(rc, 1)
        self.assertEqual(len(err), 1)
        self.assertRegex(err[0], r"^E-PRINT block editorial\.dom\.html:\d+: image F1\.png: 600 px over 17\.5 cm = 87 dpi")
        self.assertIn("1034 px wide are needed for 150 dpi", err[0])

    def test_174_dpi_is_clean(self):
        rc, out, err = self.run_dom(images=[("F1.png", 1200, 17.5)])
        self.assertEqual((rc, err), (0, []))

    def test_130_dpi_warns(self):
        rc, out, err = self.run_dom(images=[("F1.png", 900, 17.5)])
        self.assertEqual(rc, 0)
        self.assertEqual(len(err), 1)
        self.assertRegex(err[0], r"E-PRINT warn .*image F1\.png: 900 px over 17\.5 cm = 131 dpi")
        self.assertEqual(out, ["poster_preflight: editorial: 0 block, 1 warn"])

    def test_dpi_boundaries(self):
        self.assertEqual(self.run_dom(images=[("F1.png", 680, 17.5)])[0], 1)   # 98.7 dpi
        self.assertEqual(self.run_dom(images=[("F1.png", 700, 17.5)])[0], 0)   # 101.6 dpi: warn only

    def test_overflow_blocks_and_names_the_section(self):
        rc, out, err = self.run_dom(boxes=[("col-2", "Kết quả", True, None)])
        self.assertEqual(rc, 1)
        self.assertIn("col-2 (sections: Kết quả) overflows", err[0])

    def test_missing_alt_warns(self):
        rc, out, err = self.run_dom(images=[("F1.png", 1200, 17.5)], alt=False)
        self.assertEqual(rc, 0)
        self.assertRegex(err[0], r"E-PRINT warn .*image F1\.png has no alt text")

    def test_small_text_scales_with_poster_width(self):
        b = [("col-1", "A", False, "20.00")]
        rc, out, err = self.run_dom(boxes=b)  # 90 cm: threshold 24 pt
        self.assertEqual(rc, 0)
        self.assertRegex(err[0], r"E-PRINT warn .*20\.0 pt, below 24\.0 pt")
        self.spec(size_cm=[45, 60])  # threshold 12 pt
        self.pdf = pdf_bytes(456, 606)
        self.assertEqual(self.run_dom(boxes=b)[2], [])
        self.spec(size_cm=[120, 90])  # threshold 32 pt
        self.pdf = pdf_bytes(1206, 906)
        self.assertRegex(self.run_dom(boxes=[("col-1", "A", False, "30.00")])[2][0], r"below 32\.0 pt")

    def test_exactly_at_threshold_is_clean(self):
        self.assertEqual(self.run_dom(boxes=[("col-1", "A", False, "24.00")])[2], [])

    def test_missing_dom_is_not_checked_and_not_a_block(self):
        self.put(self.pdf)
        rc, out, err = self.go()
        self.assertEqual(rc, 0)
        self.assertEqual(len(err), 1)
        self.assertRegex(err[0], r"^E-PRINT warn editorial\.dom\.html:1: not checked by script \(no DOM dump")

    def test_missing_dom_still_reports_pdf_blocks(self):
        self.put(pdf_bytes(916, 1206))
        rc, out, err = self.go()
        self.assertEqual(rc, 1)
        self.assertEqual(out, ["poster_preflight: editorial: 1 block, 1 warn"])

    def test_missing_pdf_is_not_checked(self):
        self.put(None, dom(images=[("F1.png", 1200, 17.5)]))
        rc, out, err = self.go()
        self.assertEqual(rc, 0)
        self.assertRegex(err[0], r"^E-PRINT warn editorial\.pdf:1: not checked by script")

    def test_dom_without_preflight_markers_is_not_checked(self):
        rc, out, err = self.run_dom(images=[("F1.png", 600, 17.5)], done=False)
        self.assertEqual(rc, 0)
        self.assertIn("no preflight markers", err[0])

    def test_image_with_unknown_natural_size_is_not_checked(self):
        self.put(self.pdf, dom(images=[("F1.png", 0, 17.5)]))
        rc, out, err = self.go()
        self.assertEqual(rc, 0)
        self.assertIn("not checked by script", err[0])

    def test_inline_svg_with_raster_is_checked(self):
        d = ('<html><body data-preflight="done"><svg data-raster="../figures/F1.png" data-natural-w="600" '
             'data-natural-h="300" data-placed-w-cm="17.5" data-placed-h-cm="8.75"><g><path d="M0"></path></g></svg>'
             '<div class="box" data-area="col-1" data-overflow="1"><h2>Tail</h2></div></body></html>')
        self.put(self.pdf, d)
        rc, out, err = self.go()
        self.assertEqual(rc, 1)
        self.assertEqual(len(err), 2, err)
        self.assertTrue(any("F1.png: 600 px" in e for e in err))
        self.assertTrue(any("Tail" in e for e in err))


class TestCli(Base):
    def test_default_layouts_skip_unbuilt_ones(self):
        self.spec(size_cm=[90, 120], layouts=["editorial", "figure-led"])
        self.put(pdf_bytes(906, 1206), dom(), "editorial")
        out, err = [], []
        rc = pp.run(self.root, out=out.append, err=err.append)
        self.assertEqual(rc, 0)
        self.assertEqual(out, ["poster_preflight: editorial: 0 block, 0 warn"])

    def test_nothing_built_reports_not_checked(self):
        self.spec(size_cm=[90, 120], layouts=["editorial"])
        out, err = [], []
        rc = pp.run(self.root, out=out.append, err=err.append)
        self.assertEqual(rc, 0)
        self.assertEqual(len(err), 2)

    def test_bad_spec_exits_2(self):
        (self.poster / "poster.json").write_text("{", encoding="utf-8")
        out, err = [], []
        self.assertEqual(pp.run(self.root, out=out.append, err=err.append), 2)
        self.assertEqual(out, [])

    def test_main_exit_codes(self):
        self.spec(size_cm=[90, 120])
        self.put(pdf_bytes(916, 1206), dom())
        self.assertEqual(pp.main([str(self.root), "--layout", "editorial"]), 1)
        self.assertEqual(pp.main([str(self.root / "nope")]), 2)

    def test_explicit_spec_path_relative_to_project(self):
        self.spec(size_cm=[90, 120])
        self.put(pdf_bytes(906, 1206), dom())
        out, err = [], []
        rc = pp.run(self.root, ["editorial"], "07_present/poster/poster.json", out=out.append, err=err.append)
        self.assertEqual(rc, 0)


@unittest.skipUnless(BROWSER, "no Chrome or Edge found")
class TestRealBuild(unittest.TestCase):
    """Browser output (Skia PDF + preflight.js DOM dump), end to end."""

    def build(self, root, size, png_w=None):
        if png_w:
            tpb.make_png(root / "07_present" / "figures" / "F1.png", png_w, png_w // 2)
        msgs, errs = [], []
        rc = pb.build(root, layouts=["editorial"], browser=BROWSER, pptx=False, out=msgs.append, err=errs.append)
        self.assertEqual(rc, 0, errs)

    def check(self, root):
        out, err = [], []
        rc = pp.run(root, ["editorial"], out=out.append, err=err.append)
        return rc, out, err

    def test_real_pdf_and_dom_are_clean_for_a_good_image(self):
        with tempfile.TemporaryDirectory(prefix="pre flight ") as tmp:
            root = tpb.make_project(Path(tmp) / "p", size=(90, 120))
            self.build(root, (90, 120), png_w=2400)
            rc, out, err = self.check(root)
            self.assertEqual(rc, 0, err)
            self.assertEqual(err, [])
            data = (root / "07_present" / "poster" / "editorial.pdf").read_bytes()
            self.assertIsNotNone(pp.media_box(data))
            emb, missing, found = pp.fonts(data)
            self.assertTrue(found and emb and not missing, (emb, missing))
            html = (root / "07_present" / "poster" / "editorial.dom.html").read_text(encoding="utf-8")
            self.assertRegex(html, r'data-font-pt="[\d.]+"')

    def test_87_dpi_block_end_to_end(self):
        with tempfile.TemporaryDirectory(prefix="pre flight ") as tmp:
            root = tpb.make_project(Path(tmp) / "p", size=(69, 92))  # the figure column is about 17.5 cm wide
            self.build(root, (69, 92), png_w=600)
            rc, out, err = self.check(root)
            self.assertEqual(rc, 1, err)
            blocks = [e for e in err if "E-PRINT block" in e]
            self.assertEqual(len(blocks), 1, err)
            m = re.search(r"600 px over ([\d.]+) cm = (\d+) dpi", blocks[0])
            self.assertTrue(m, blocks)
            self.assertTrue(80 <= int(m.group(2)) <= 95, blocks)
            self.assertIn("F1.png", blocks[0])

    def test_tampered_media_box_blocks(self):
        with tempfile.TemporaryDirectory(prefix="pre flight ") as tmp:
            root = tpb.make_project(Path(tmp) / "p", size=(20, 30))
            self.build(root, (20, 30), png_w=2400)
            pdf = root / "07_present" / "poster" / "editorial.pdf"
            data = pdf.read_bytes()
            w = pp.media_box(data)[0]
            data = re.sub(rb"/MediaBox \[0 0 [\d.]+", b"/MediaBox [0 0 %.2f" % (w + 28.35), data, count=1)  # +1 cm
            pdf.write_bytes(data)
            rc, out, err = self.check(root)
            self.assertEqual(rc, 1)
            self.assertIn("page size", err[0])


if __name__ == "__main__":
    unittest.main()
