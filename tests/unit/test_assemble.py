import contextlib
import io
import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

import _paths  # noqa: F401
import assemble
import gate
import init_project

REFS = [{"id": "a2020", "title": "A", "authors": ["Nguyen A"], "journal": "J", "year": 2020, "pmid": "1",
         "verified_by": "verify_refs.py 2026-11-21 VERIFIED"},
        {"id": "b2021", "title": "B", "authors": ["Tran B"], "journal": "K", "year": 2021, "pmid": "2",
         "verified_by": "verify_refs.py 2026-11-21 VERIFIED"}]
RES = [{"id": "R-A1-001", "label": "OR", "value": 1.0929, "ci": [0.7431, 1.6076], "n": 749, "kind": "or",
        "source_file": "x", "locator": "1", "raw": "x"}]
THESIS = {
    "00-dat-van-de.md": "# ĐẶT VẤN ĐỀ\n\nNghiên cứu trước [@b2021].\n",
    "ch2-methods.md": ("# CHƯƠNG 2. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP\n\nBảng 2.1. Biến số\n| A | B |\n|---|---|\n| x | y |\n\n"
                       "Xem Bảng 2.1.\n\n## Tài liệu tham khảo\n\n{REFERENCES}\n"),
    "ch3-results.md": "# CHƯƠNG 3. KẾT QUẢ\n\nOR là {{R-A1-001.full}} [@a2020].\n\nBảng 3.1. Kết quả\n| A |\n|---|\n| 1 |\n",
    "ch4-discussion.md": "# CHƯƠNG 4. BÀN LUẬN\n\nPhù hợp [@a2020; @b2021] (Bảng 3.1).\n",
    "05-ket-luan.md": "# KẾT LUẬN\n\nCó liên quan. <!-- results: R-A1-001 -->\n",
}


class TestAssemble(unittest.TestCase):
    def setUp(self):
        self.t = Path(tempfile.mkdtemp())
        self.p = init_project.create(self.t / "p", "T", "thesis-masters", "cohort", "vi", "vi")
        (self.p / "ledgers" / "references.json").write_text(json.dumps({"references": REFS}), encoding="utf-8")
        (self.p / "ledgers" / "results-ledger.json").write_text(json.dumps({"results": RES}), encoding="utf-8")
        self.d = self.p / "06_writing" / "thesis"
        self.d.mkdir(parents=True, exist_ok=True)
        for name, text in THESIS.items():
            (self.d / name).write_text(text, encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.t, ignore_errors=True)

    def cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = assemble.main([str(self.p), *argv])
        return code, out.getvalue(), err.getvalue()

    def doc(self, path: Path) -> str:
        with zipfile.ZipFile(path) as z:
            return z.read("word/document.xml").decode("utf-8")

    def test_thesis_assembles_with_one_numbering(self):
        code, out, err = self.cli("thesis")
        self.assertEqual(code, 0, out + err)
        text = (self.d / "thesis.assembled.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("**MỤC LỤC**\n\n{TOC}"))
        self.assertIn("1,09 (KTC 95%: 0,74–1,61) [2]", text)
        self.assertIn("Nghiên cứu trước [1].", text)
        self.assertIn("Phù hợp [1,2]", text)
        self.assertEqual(text.count("# TÀI LIỆU THAM KHẢO"), 1)
        self.assertNotIn("## Tài liệu tham khảo", text)
        self.assertNotIn("{REFERENCES}", text)
        self.assertIn("1. Tran B.", text)
        self.assertEqual(text.count("\\newpage"), 6)
        self.assertNotIn(b"\r\n", (self.d / "thesis.assembled.md").read_bytes())
        self.assertIn("BẢN NHÁP", self.doc(self.d / "thesis.draft.docx"))
        self.assertFalse((self.p / "out" / "thesis.docx").exists())
        self.assertIn("E-FMT warn 06_writing/thesis/90-phu-luc.md:1", out)

    def test_reference_list_before_appendix(self):
        (self.d / "90-phu-luc.md").write_text("# PHỤ LỤC\n\nBảng PL. x\n", encoding="utf-8")
        self.assertEqual(self.cli("thesis")[0], 0)
        text = (self.d / "thesis.assembled.md").read_text(encoding="utf-8")
        self.assertLess(text.index("# TÀI LIỆU THAM KHẢO"), text.index("# PHỤ LỤC"))

    def test_missing_required_blocks_and_writes_nothing(self):
        (self.d / "ch4-discussion.md").unlink()
        code, out, _ = self.cli("thesis")
        self.assertEqual(code, 1)
        self.assertIn("E-FMT block 06_writing/thesis/ch4-discussion.md:1: required section missing: Chương 4", out)
        self.assertFalse((self.d / "thesis.assembled.md").exists())
        self.assertFalse((self.d / "thesis.draft.docx").exists())

    def test_caption_rules(self):
        sec = [("06_writing/thesis/ch3-results.md",
                "# CHƯƠNG 3\n\nBảng 3.2. a\n| x |\n\nBảng 3.2. b\n| x |\n\nBảng 2.1. c\n| x |\n\n"
                "Xem Bảng 3.9 và Biểu đồ 3.1.\n\n![Biểu đồ 3.1. d](f.png)\n\nNhư Hình 2 của Robbins <!-- fmt-ok: other paper -->\n")]
        msgs = [m for _, lvl, _, m in assemble.caption_findings(sec, "thesis") if lvl == "block"]
        self.assertTrue(any("Bảng 3.2 out of sequence: expected Bảng 3.1" in m for m in msgs), msgs)
        self.assertTrue(any("Bảng 3.2 is used twice" in m for m in msgs), msgs)
        self.assertTrue(any("Bảng 2.1 in chapter 3 must be numbered Bảng 3.n" in m for m in msgs), msgs)
        self.assertTrue(any("Bảng 3.9 is mentioned but no caption" in m for m in msgs), msgs)
        self.assertFalse(any("Biểu đồ 3.1" in m for m in msgs), msgs)
        self.assertFalse(any("Hình 2" in m for m in msgs), msgs)
        man = [("06_writing/manuscript/04-results.md", "Table 1. a\n| x |\n\nTable 1.1. b\n| x |\n\nFigure 2. c\n")]
        msgs = [m for _, _, _, m in assemble.caption_findings(man, "manuscript")]
        self.assertTrue(any("across the paper" in m for m in msgs), msgs)
        self.assertTrue(any("Figure 2 out of sequence: expected Figure 1" in m for m in msgs), msgs)

    def test_pending_figure_slot_is_a_warning(self):
        sec = [("06_writing/thesis/ch3-results.md",
                "# CHƯƠNG 3\n\n[Biểu đồ 3.1: Sơ đồ — chờ research-figures]\n\nXem Biểu đồ 3.1.\n")]
        found = assemble.caption_findings(sec, "thesis")
        self.assertEqual([lvl for _, lvl, _, _ in found], ["warn"], found)

    def test_pending_figure_slot_blocks_in_strict_mode(self):
        (self.d / "ch3-results.md").write_text(
            "# CHƯƠNG 3\n\n[Biểu đồ 3.1: Sơ đồ — chờ research-figures]\n\nBảng 3.1. T\n| A |\n|---|\n| 1 |\n", encoding="utf-8")
        self.assertEqual(self.cli("thesis")[0], 0)
        strict = assemble.format_findings(self.p, "thesis", strict=True)
        self.assertTrue(any(lvl == "block" and "pending figure slot" in m for _, lvl, _, m in strict), strict)

    def test_caption_forms(self):
        sec = [("06_writing/thesis/ch3-results.md",
                "# CHƯƠNG 3\n\n**Bảng 3.1.** a\n| x |\n\n*Hình 3.1. b*\n\n![Biểu đồ 3.1](f.png)\n\n"
                "Xem Bảng 3.1, Hình 3.1 và Biểu đồ 3.1.\n")]
        found = assemble.caption_findings(sec, "thesis")
        self.assertEqual(found, [], found)

    def test_citation_inside_comment_is_ignored(self):
        (self.d / "ch3-results.md").write_text(
            "# CHƯƠNG 3\n\nOK [@a2020] <!-- note [@zzz2000] -->\n\nBảng 3.1. T\n| A |\n|---|\n| 1 |\n", encoding="utf-8")
        code, out, err = self.cli("thesis")
        self.assertEqual(code, 0, out + err)
        text = (self.d / "thesis.assembled.md").read_text(encoding="utf-8")
        self.assertNotIn("zzz2000", text)
        self.assertEqual(text.count("Nguyen A."), 1)

    def test_citation_split_across_lines_is_checked(self):
        (self.d / "ch3-results.md").write_text("# CHƯƠNG 3\n\nx [@a2020;\n@zzz9999]\n", encoding="utf-8")
        code, out, err = self.cli("thesis")
        self.assertEqual(code, 1, out + err)
        self.assertIn("E-REF block 06_writing/thesis/ch3-results.md:4: [@zzz9999] is not in ledgers/references.json", out)
        self.assertNotIn("KeyError", err)

    def test_unknown_language_is_a_usage_error(self):
        err = io.StringIO()
        with mock.patch.object(assemble.drafts, "lang_of", return_value="fr"), contextlib.redirect_stderr(err), \
                contextlib.redirect_stdout(io.StringIO()):
            code = assemble.main([str(self.p), "thesis"])
        self.assertEqual(code, 2)
        self.assertIn("language", err.getvalue())

    def test_docx_build_failure_writes_nothing(self):
        with mock.patch.object(assemble.build_docx, "build", side_effect=ValueError("boom")), \
                contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            code = assemble.main([str(self.p), "thesis"])
        self.assertEqual(code, 2)
        self.assertFalse((self.d / "thesis.assembled.md").exists())

    def test_unknown_placeholder_and_citation_block(self):
        (self.d / "ch3-results.md").write_text("# CHƯƠNG 3\n\n{{R-A9-001}} [@zzz2000]\n", encoding="utf-8")
        code, out, _ = self.cli("thesis")
        self.assertEqual(code, 1)
        self.assertIn("E-NUM block 06_writing/thesis/ch3-results.md:3:", out)
        self.assertIn("E-REF block 06_writing/thesis/ch3-results.md:3: [@zzz2000] is not in ledgers/references.json", out)

    def test_order_txt_and_author_placeholder(self):
        (self.d / "order.txt").write_text("ch2-methods.md\nch3-results.md\nch4-discussion.md\n05-ket-luan.md\nnone.md\n",
                                          encoding="utf-8")
        (self.d / "ch2-methods.md").write_text("# CHƯƠNG 2\n\nSố quyết định [[TÁC GIẢ: số quyết định]].\n", encoding="utf-8")
        code, out, _ = self.cli("thesis")
        self.assertEqual(code, 0, out)
        self.assertIn("E-FMT warn 06_writing/thesis/none.md:1", out)
        self.assertIn("E-FMT warn 06_writing/thesis/00-dat-van-de.md:1: draft not in the section order", out)
        self.assertIn("E-FMT warn 06_writing/thesis/ch2-methods.md:3:", out)
        strict = assemble.format_findings(self.p, "thesis", strict=True)
        self.assertTrue(any(lvl == "block" and "[[" in m for _, lvl, _, m in strict))

    def test_author_placeholder_wrapped_over_lines(self):
        (self.d / "ch2-methods.md").write_text("# CHƯƠNG 2\n\nTài trợ: [[TÁC\nGIẢ: nguồn tài trợ,\nnếu có]].\n",
                                               encoding="utf-8")
        found = [f for f in assemble.format_findings(self.p, "thesis") if "placeholder" in f[3]]
        self.assertEqual(len(found), 1, found)
        code, lvl, loc, msg = found[0]
        self.assertEqual((code, lvl, loc), ("E-FMT", "warn", "06_writing/thesis/ch2-methods.md:3"))
        self.assertIn("[[TÁC GIẢ: nguồn tài trợ, nếu có]]", msg)
        strict = [f for f in assemble.format_findings(self.p, "thesis", strict=True) if "placeholder" in f[3]]
        self.assertEqual([f[1] for f in strict], ["block"])

    def audit_json(self):
        files = {p.relative_to(self.p).as_posix(): gate.sha256(p) for p in sorted(self.d.glob("*.md"))
                 if not p.name.endswith(".assembled.md")}
        for rel in ("ledgers/references.json", "ledgers/results-ledger.json"):
            files[rel] = gate.sha256(self.p / rel)
        (self.p / "reviews" / "audit.json").write_text(json.dumps(
            {"deliverable": "thesis", "deliverables": ["thesis"], "at": "t", "blocks": 0, "warns": 0, "files": files}),
            encoding="utf-8")

    def test_final_needs_g4_then_writes_out(self):
        code, out, _ = self.cli("thesis", "--final")
        self.assertEqual(code, 1)
        self.assertIn("G4: closed for the thesis", out)
        self.assertFalse((self.p / "out" / "thesis.docx").exists())
        self.audit_json()
        gate.open_gate(self.p, "G4", by="A")
        code, out, err = self.cli("thesis", "--final")
        self.assertEqual(code, 0, out + err)
        self.assertNotIn("BẢN NHÁP", self.doc(self.p / "out" / "thesis.docx"))
        (self.d / "ch4-discussion.md").write_text(THESIS["ch4-discussion.md"] + "\nThêm.\n", encoding="utf-8")
        self.assertEqual(self.cli("thesis", "--final")[0], 1)

    def test_manuscript_breaks_and_numbering(self):
        m = self.p / "06_writing" / "manuscript"
        m.mkdir(parents=True, exist_ok=True)
        for name, text in {"00-title.md": "# Tiêu đề\n", "01-abstract.md": "## Tóm tắt\n\nx\n",
                           "02-introduction.md": "## Đặt vấn đề\n\nx [@a2020]\n", "03-methods.md": "## Phương pháp\n\nx\n",
                           "04-results.md": "## Kết quả\n\nBảng 1. a\n| x |\n|---|\n| 1 |\n\nXem Bảng 1.\n",
                           "05-discussion.md": "## Bàn luận\n\nx\n", "06-conclusion.md": "## Kết luận\n\nx\n"}.items():
            (m / name).write_text(text, encoding="utf-8")
        code, out, _ = self.cli("manuscript")
        self.assertEqual(code, 0, out)
        text = (m / "manuscript.assembled.md").read_text(encoding="utf-8")
        self.assertEqual(text.count("\\newpage"), 3)
        self.assertNotIn("{TOC}", text)
        self.assertTrue(text.rstrip().endswith("1. Nguyen A. A. J. 2020. PMID: 1."))

    def test_usage_errors(self):
        shutil.rmtree(self.p / "06_writing" / "manuscript", ignore_errors=True)   # Task 9 scaffolds it
        self.assertEqual(self.cli("manuscript")[0], 2)          # no 06_writing/manuscript/
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(assemble.main([str(self.t / "none"), "thesis"]), 2)
            with self.assertRaises(SystemExit):
                assemble.main([str(self.p), "poster"])
