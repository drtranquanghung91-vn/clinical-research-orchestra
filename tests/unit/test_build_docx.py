import subprocess
import sys
import tempfile
import unittest
import xml.dom.minidom
import zipfile
from pathlib import Path

import _paths  # noqa: F401
from _paths import ORCH_SCRIPTS
import build_docx

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
