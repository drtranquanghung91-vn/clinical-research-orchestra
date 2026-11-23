import contextlib
import io
import json
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import xml.dom.minidom
import zipfile
import zlib
from pathlib import Path

import _paths  # noqa: F401
from _paths import ORCH_SCRIPTS
import build_docx
import gate
import init_project

SCRIPT = ORCH_SCRIPTS / "build_docx.py"
MD = """# Chương 3. Kết quả
## 3.1 Đặc điểm chung
Có **1070** bệnh nhân <!-- note -->và *đa số* là nữ.

Bảng 3.1. Đặc điểm chung
| Biến | Giá trị |
|---|---|
| Tuổi | 54,1 ± 7,3 |
Nguồn: dữ liệu mô phỏng.

- một ý
\\newpage
### 3.2 Mục tiêu 1
"""


class TestBuildDocx(unittest.TestCase):
    def doc_xml(self, data: bytes, name="word/document.xml") -> str:
        import io
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            return z.read(name).decode("utf-8")

    def test_structure(self):
        data = build_docx.build(MD, build_docx.settings_from_project(None))
        doc = self.doc_xml(data)
        xml.dom.minidom.parseString(doc)
        self.assertIn('w:val="Heading1"', doc)
        self.assertIn('w:val="Caption"', doc)
        self.assertIn('w:val="TableNote"', doc)
        self.assertIn("<w:tbl>", doc)
        self.assertIn("<w:b/>", doc)
        self.assertIn('w:type="page"', doc)
        self.assertIn("Bảng 3.1. Đặc điểm chung", doc)
        self.assertNotIn("note", doc)
        self.assertIn('w:w="11906"', doc)
        self.assertIn('w:left="1701"', doc)

    def test_project_settings(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "project.yaml").write_text(
                'docx:\n  font: "Arial"\n  size_pt: 12\n  line_spacing: 1.2\n  margins_cm: [2.5, 2.5, 3.5, 2]\n',
                encoding="utf-8")
            s = build_docx.settings_from_project(Path(d))
            self.assertEqual(s["font"], "Arial")
            self.assertEqual(s["margins_cm"], (2.5, 2.5, 3.5, 2.0))
            styles = self.doc_xml(build_docx.build("x", s), "word/styles.xml")
            self.assertIn('w:ascii="Arial"', styles)
            self.assertIn('w:val="24"', styles)

    def test_control_characters_stripped(self):
        md = "Dòng a\x0bb và \x01c\n\n| H | V |\n|---|---|\n| x | 1\x0b2\x01 |\n"
        doc = self.doc_xml(build_docx.build(md, build_docx.settings_from_project(None)))
        xml.dom.minidom.parseString(doc)
        self.assertIn("Dòng ab và c", doc)
        self.assertIn(">12<", doc)

    def test_statistical_asterisks_literal(self):
        s = build_docx.settings_from_project(None)
        for text in ("Mean* 5, SD* 3", "5*3 = 15 and 2*4", "*p<0,05; **p<0,01"):
            doc = self.doc_xml(build_docx.build(text, s))
            self.assertIn(text.replace("<", "&lt;"), doc)
            self.assertNotIn("<w:i/>", doc)
            self.assertNotIn("<w:b/>", doc)
        doc = self.doc_xml(build_docx.build("a **bold** and *italic* x", s))
        self.assertIn("<w:b/>", doc)
        self.assertIn("<w:i/>", doc)
        self.assertNotIn("*", doc.split("<w:body>")[1])
        doc = self.doc_xml(build_docx.build(r"p\* và *a*", s))
        self.assertIn("p* và ", doc)

    def test_escaped_pipe_in_cell(self):
        md = "| A | B |\n|---|---|\n| a\\|b | c |\n"
        doc = self.doc_xml(build_docx.build(md, build_docx.settings_from_project(None)))
        self.assertIn(">a|b<", doc)
        self.assertEqual(doc.count("<w:tc>"), 4)

    def test_block_quote_indented_and_marker_stripped(self):
        doc = self.doc_xml(build_docx.build("> trích dẫn *nghiêng*\n> dòng hai\n\nthường", build_docx.settings_from_project(None)))
        xml.dom.minidom.parseString(doc)
        self.assertIn('<w:ind w:left="567"/>', doc)
        self.assertNotIn("&gt;", doc)
        self.assertIn("trích dẫn ", doc)
        self.assertEqual(doc.count('<w:ind w:left="567"/>'), 2)

    def test_inline_backticks_stripped_code_kept(self):
        doc = self.doc_xml(build_docx.build("Dùng `crostats.table1(*x*)` và `p<0,05` ở đây", build_docx.settings_from_project(None)))
        xml.dom.minidom.parseString(doc)
        self.assertNotIn("`", doc)
        self.assertIn("crostats.table1(*x*)", doc)
        self.assertIn("p&lt;0,05", doc)
        self.assertIn("Consolas", doc)

    def test_cli_help_and_vietnamese_paths_on_cp1252_console(self):
        import os
        env = dict(os.environ, PYTHONIOENCODING="cp1252", PYTHONUTF8="0")
        r = subprocess.run([sys.executable, str(SCRIPT), "--help"], capture_output=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn(b"Traceback", r.stderr)
        with tempfile.TemporaryDirectory() as d:
            src, out = Path(d, "kết quả.md"), Path(d, "báo cáo.docx")
            src.write_text(MD, encoding="utf-8")
            r = subprocess.run([sys.executable, str(SCRIPT), str(src), str(out)], capture_output=True, env=env)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue(zipfile.is_zipfile(out))

    def test_cli(self):
        with tempfile.TemporaryDirectory() as d:
            src, out = Path(d, "a.md"), Path(d, "a.docx")
            src.write_text(MD, encoding="utf-8")
            r = subprocess.run([sys.executable, str(SCRIPT), str(src), str(out)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue(zipfile.is_zipfile(out))
            r2 = subprocess.run([sys.executable, str(SCRIPT), str(Path(d, "none.md")), str(out)],
                                capture_output=True, text=True)
            self.assertEqual(r2.returncode, 2)


def png(w: int, h: int) -> bytes:
    raw = b"".join(b"\x00" + b"\xff\x00\x00" * w for _ in range(h))

    def chunk(t: bytes, d: bytes) -> bytes:
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def make_template(path: Path) -> None:
    w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    r = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    styles = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles xmlns:w="{w}">'
              '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/>'
              '<w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/></w:rPr></w:style>'
              '<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/>'
              '<w:rPr><w:b/><w:color w:val="1F3864"/></w:rPr></w:style>'
              '<w:style w:type="paragraph" w:styleId="ThesisBody"><w:name w:val="Thesis body"/></w:style></w:styles>')
    doc = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="{w}" xmlns:r="{r}" '
           'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"><w:body><w:p/>'
           '<w:sectPr w:rsidR="00AB" w14:dummy="1"><w:headerReference w:type="default" r:id="rId9"/>'
           '<w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1440" w:right="1000" w:bottom="1440" w:left="2000" '
           'w:header="720" w:footer="720" w:gutter="0"/></w:sectPr></w:body></w:document>')
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("word/styles.xml", styles)
        z.writestr("word/document.xml", doc)


class TestBuildDocxP4(unittest.TestCase):
    def part(self, data: bytes, name: str) -> str:
        import io
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            return z.read(name).decode("utf-8")

    def names(self, data: bytes) -> list:
        import io
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            return z.namelist()

    def s(self):
        return build_docx.settings_from_project(None)

    def test_heading4_and_caption_styles(self):
        data = build_docx.build("#### Bốn\n", self.s())
        self.assertIn('w:val="Heading4"', self.part(data, "word/document.xml"))
        styles = self.part(data, "word/styles.xml")
        for sid in ("Heading4", "Caption", "FigureCaption", "Figure", "ListParagraph"):
            self.assertIn(f'w:styleId="{sid}"', styles)

    def test_real_list_numbering(self):
        md = "- a\n- b\n\n1. x\n2. y\n\nz\n\n3. p\n4. q\n"
        data = build_docx.build(md, self.s())
        doc, num = self.part(data, "word/document.xml"), self.part(data, "word/numbering.xml")
        for part in (doc, num):
            xml.dom.minidom.parseString(part)
        self.assertEqual(doc.count('<w:numId w:val="1"/>'), 2)
        self.assertEqual(doc.count('<w:numId w:val="2"/>'), 2)
        self.assertEqual(doc.count('<w:numId w:val="3"/>'), 2)
        self.assertIn('<w:startOverride w:val="3"/>', num)
        self.assertIn('w:val="bullet"', num)
        self.assertIn('w:val="decimal"', num)
        self.assertNotIn("1. x", doc)
        self.assertIn(">x</w:t>", doc)

    def test_png_image_fitted_caption_below(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "f.png").write_bytes(png(200, 100))
            data = build_docx.build("![Hình 3.1. Biểu đồ thử](f.png)\n", self.s(), base_dir=Path(d))
            doc = self.part(data, "word/document.xml")
            xml.dom.minidom.parseString(doc)
            self.assertIn('<wp:extent cx="5760085" cy="2880042"/>', doc)
            self.assertLess(doc.index("<w:drawing>"), doc.index('w:val="FigureCaption"'))
            self.assertIn("Hình 3.1. Biểu đồ thử", doc)
            self.assertIn("word/media/image1.png", self.names(data))
            self.assertIn('Extension="png"', self.part(data, "[Content_Types].xml"))
            self.assertIn('Target="media/image1.png"', self.part(data, "word/_rels/document.xml.rels"))
            self.assertEqual(build_docx.png_size(png(200, 100)), (200, 100))

    def test_image_errors(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                build_docx.build("![Hình 1. x](none.png)\n", self.s(), base_dir=Path(d))
            Path(d, "f.png").write_bytes(b"GIF89a....")
            with self.assertRaises(ValueError):
                build_docx.build("![Hình 1. x](f.png)\n", self.s(), base_dir=Path(d))

    def test_toc_field_and_update_on_open(self):
        data = build_docx.build("{TOC}\n\n# A\n", self.s())
        doc = self.part(data, "word/document.xml")
        self.assertIn('TOC \\o "1-3"', doc)
        self.assertNotIn("{TOC}", doc)
        self.assertIn('<w:updateFields w:val="true"/>', self.part(data, "word/settings.xml"))
        self.assertNotIn("updateFields", self.part(build_docx.build("# A\n", self.s()), "word/settings.xml"))

    def test_page_number_footer(self):
        data = build_docx.build("x\n", self.s())
        footer = self.part(data, "word/footer1.xml")
        xml.dom.minidom.parseString(footer)
        self.assertIn(" PAGE ", footer)
        self.assertIn('<w:footerReference w:type="default" r:id="rId3"/>', self.part(data, "word/document.xml"))
        self.assertIn("footer1.xml", self.part(data, "word/_rels/document.xml.rels"))
        self.assertIn("/word/footer1.xml", self.part(data, "[Content_Types].xml"))

    def test_template_styles_and_page_setup(self):
        with tempfile.TemporaryDirectory() as d:
            tpl = Path(d, "tpl.docx")
            make_template(tpl)
            Path(d, "f.png").write_bytes(png(100, 100))
            data = build_docx.build("# A\n\n![Hình 1.1. x](f.png)\n", self.s(), base_dir=Path(d), template=tpl)
            styles, doc = self.part(data, "word/styles.xml"), self.part(data, "word/document.xml")
            xml.dom.minidom.parseString(doc)
            self.assertIn('w:styleId="ThesisBody"', styles)
            self.assertEqual(styles.count('w:styleId="Heading1"'), 1)
            self.assertIn("1F3864", styles)
            self.assertIn('w:styleId="FigureCaption"', styles)
            self.assertIn('w:w="12240"', doc)
            self.assertNotIn("headerReference", doc)
            self.assertNotIn("w14:", doc)
            self.assertIn("footerReference", doc)
            self.assertIn(f'cx="{(12240 - 2000 - 1000) * 635}"', doc)

    def test_template_from_project_yaml_and_errors(self):
        with tempfile.TemporaryDirectory() as d:
            make_template(Path(d, "tpl.docx"))
            Path(d, "project.yaml").write_text('institution:\n  name: ""\n  template: "tpl.docx"\n', encoding="utf-8")
            self.assertEqual(build_docx.template_from_project(Path(d)), Path(d) / "tpl.docx")
            src, out = Path(d, "a.md"), Path(d, "a.docx")
            src.write_text("x\n", encoding="utf-8")
            r = subprocess.run([sys.executable, str(SCRIPT), str(src), str(out), "--project", d], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn('w:styleId="ThesisBody"', self.part(out.read_bytes(), "word/styles.xml"))
            r = subprocess.run([sys.executable, str(SCRIPT), str(src), str(out), "--template", str(Path(d, "none.docx"))],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 2)

    def test_multi_input_cli_with_relative_images(self):
        with tempfile.TemporaryDirectory() as d:
            sub = Path(d, "ch3")
            sub.mkdir()
            (sub / "f.png").write_bytes(png(50, 50))
            a, b, out = Path(d, "a.md"), sub / "b.md", Path(d, "o.docx")
            a.write_text("# Một\n", encoding="utf-8")
            b.write_text("# Hai\n\n![Hình 3.1. x](f.png)\n", encoding="utf-8")
            r = subprocess.run([sys.executable, str(SCRIPT), str(a), str(b), str(out)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            data = out.read_bytes()
            doc = self.part(data, "word/document.xml")
            self.assertIn("Một", doc)
            self.assertIn("Hai", doc)
            self.assertIn("word/media/image1.png", self.names(data))
            r = subprocess.run([sys.executable, str(SCRIPT), str(a), str(Path(d, "o.md"))], capture_output=True, text=True)
            self.assertEqual(r.returncode, 2)
            r = subprocess.run([sys.executable, str(SCRIPT), str(out)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 2)
            Path(d, "c.md").write_text("![Hình 1. x](missing.png)\n", encoding="utf-8")
            r = subprocess.run([sys.executable, str(SCRIPT), str(Path(d, "c.md")), str(out)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 2)
            self.assertIn("image not found", r.stderr)

    def test_all_parts_well_formed(self):
        data = build_docx.build("{TOC}\n# A\n- b\n1. c\n", self.s())
        for name in ("word/document.xml", "word/styles.xml", "word/numbering.xml", "word/footer1.xml",
                     "word/settings.xml", "[Content_Types].xml", "word/_rels/document.xml.rels"):
            xml.dom.minidom.parseString(self.part(data, name))


class TestBuildDocxReviewFixes(unittest.TestCase):
    def test_output_is_deterministic(self):
        import time
        s = build_docx.settings_from_project(None)
        a = build_docx.build("{TOC}\n# A\n- b\n", s)
        time.sleep(2)
        b = build_docx.build("{TOC}\n# A\n- b\n", s)
        self.assertEqual(a, b)

    def test_image_in_folder_with_parentheses(self):
        with tempfile.TemporaryDirectory() as d:
            sub = Path(d, "thư mục (1)")
            sub.mkdir()
            (sub / "f.png").write_bytes(png(40, 20))
            md = sub / "a.md"
            md.write_text("![Hình 1.1. x](f.png)\n", encoding="utf-8")
            out = Path(d, "o.docx")
            r = subprocess.run([sys.executable, str(SCRIPT), str(md), str(out)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            with zipfile.ZipFile(out) as z:
                self.assertIn("word/media/image1.png", z.namelist())
            data = build_docx.build("![x](" + (sub / "f.png").as_posix() + ")\n", build_docx.settings_from_project(None))
            with zipfile.ZipFile(__import__("io").BytesIO(data)) as z:
                self.assertIn("word/media/image1.png", z.namelist())

    def test_heading_outline_levels(self):
        data = build_docx.build("# A\n", build_docx.settings_from_project(None))
        with zipfile.ZipFile(__import__("io").BytesIO(data)) as z:
            styles = z.read("word/styles.xml").decode("utf-8")
        for lvl in range(4):
            self.assertIn(f'<w:outlineLvl w:val="{lvl}"/>', styles)


class TestFinalExportRefused(unittest.TestCase):
    """build_docx.py refuses out/<final name>.docx while gate.export_problems says no (important 2)."""

    def setUp(self):
        self.t = Path(tempfile.mkdtemp())
        self.p = init_project.create(self.t / "p", "T", "thesis-masters", "cohort", "vi", "vi")
        self.md = self.p / "06_writing" / "thesis" / "thesis.assembled.md"
        self.md.parent.mkdir(parents=True, exist_ok=True)
        self.md.write_text("# Chương 1\n\nVăn bản.\n", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.t, ignore_errors=True)

    def main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = build_docx.main([str(a) for a in argv])
        return code, out.getvalue(), err.getvalue()

    def test_refused_while_g4_closed(self):
        for name in ("thesis.docx", "manuscript.docx", "case-report.docx", "review.docx", "THESIS.DOCX"):
            with self.subTest(name=name):
                dest = self.p / "out" / name
                code, _, err = self.main(self.md, dest)
                self.assertEqual(code, 1, err)
                self.assertIn("G4", err)
                self.assertFalse(dest.exists())
        r = subprocess.run([sys.executable, str(SCRIPT), str(self.md), str(self.p / "out" / "thesis.docx")],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("final export", r.stderr)
        other = self.t / "elsewhere" / "out"                       # --project names the project
        other.mkdir(parents=True)
        self.assertEqual(self.main(self.md, other / "thesis.docx", "--project", self.p)[0], 1)
        self.assertFalse((other / "thesis.docx").exists())

    def test_other_names_and_non_projects_still_build(self):
        for dest in (self.p / "out" / "ch3-results.docx", self.p / "reviews" / "thesis.docx", self.t / "out" / "thesis.docx"):
            with self.subTest(dest=dest):
                dest.parent.mkdir(parents=True, exist_ok=True)
                code, _, err = self.main(self.md, dest)
                self.assertEqual(code, 0, err)
                self.assertTrue(dest.is_file())

    def test_allowed_once_export_problems_is_empty(self):
        (self.p / "decisions.md").write_text("# Decisions\n\nWAIVE G4: internal report, 2026-11-23\n", encoding="utf-8")
        (self.p / "reviews" / "audit.json").write_text(json.dumps(
            {"deliverable": "thesis", "at": "t", "blocks": 0, "warns": 0,
             "files": {"06_writing/thesis/thesis.assembled.md": gate.sha256(self.md)}}), encoding="utf-8")
        self.assertEqual(gate.export_problems(self.p, "thesis"), [])
        code, _, err = self.main(self.md, self.p / "out" / "thesis.docx", "--project", self.p)
        self.assertEqual(code, 0, err)
        self.assertTrue((self.p / "out" / "thesis.docx").is_file())

    def test_response_letter_is_a_final_name(self):
        with tempfile.TemporaryDirectory() as t:
            p = init_project.create(Path(t) / "p", "T", "manuscript", "cohort", "en", "en")
            self.assertTrue(build_docx.final_export_problems(p / "out" / "response-letter.docx"))
            self.assertEqual(build_docx.final_export_problems(p / "out" / "response-letter-draft.docx"), [])
