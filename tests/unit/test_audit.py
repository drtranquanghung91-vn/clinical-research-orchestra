import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import _paths  # noqa: F401
import assemble
import audit
import gate
import init_project
from crolib import drafts, reviews

OK = {"id": "a2020", "title": "Glycaemic control and readmission", "authors": ["Nguyen A"], "journal": "J Test",
      "year": 2020, "pmid": "123", "verified_by": "verify_refs.py 2026-11-21 VERIFIED",
      "abstract": "Higher HbA1c was associated with readmission."}
BAD = dict(OK, id="b2021", pmid="456", verified_by="verify_refs.py 2026-11-21 NOT_FOUND")
RES = {"id": "R-A1-001", "analysis_id": "A1", "status": "prespecified", "label": "adjusted OR", "value": 1.42,
       "ci": [1.05, 1.91], "n": 749, "kind": "or", "source_file": "05_analysis/output/log.txt", "locator": "line 1",
       "raw": "R-A1-001 value=1.42"}
SAP = "# SAP\n\n## Analysis register\n\n| ID | Objective | Method |\n|---|---|---|\n| A1 | Mục tiêu 2 | hồi quy logistic |\n"
SECTIONS = {
    "ch1-literature-review.md": "# Chương 1. Tổng quan tài liệu\n\nHbA1c cao đi kèm tái nhập viện trong nhiều quần thể [@a2020].\n",
    "ch2-methods.md": "# Chương 2. Đối tượng và phương pháp nghiên cứu\n\nNghiên cứu đoàn hệ hồi cứu tại bệnh viện mô phỏng.\n",
    "ch3-results.md": "# Chương 3. Kết quả nghiên cứu\n\nOR hiệu chỉnh là {{R-A1-001.full}}.\n",
    "ch4-discussion.md": ("# Chương 4. Bàn luận\n\nKết quả tương đồng với nghiên cứu trước [@a2020].\n\n"
                          "## Hạn chế\n\nThiết kế hồi cứu có thể có sai lệch chọn.\n"),
    "05-ket-luan.md": "# Kết luận\n\nHbA1c cao có liên quan với tái nhập viện. <!-- results: R-A1-001 -->\n",
}
IDS = ["1a", "1b", "2", "3", "4", "5", "6a", "6b", "7", "8", "9", "10", "11", "12a", "12b", "12c", "12d", "12e",
       "13a", "13b", "13c", "14a", "14b", "14c", "15", "16a", "16b", "16c", "17", "18", "19", "20", "21", "22"]
PNG = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x02\x00\x00\x00\x02\x08\x02\x00\x00\x00"
       b"\xfd\xd4\x9a\x73\x00\x00\x00\x0cIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xa7\x35\x81\x84\x00\x00\x00\x00IEND\xaeB`\x82")


def write_reports(p: Path, deliverable: str = "thesis") -> None:
    dg = drafts.digest(p, deliverable)
    for agent, (rel, crits) in reviews.REVIEWERS.items():
        (p / rel).write_text(f"STATUS: PASS\nFINDINGS\n| code | location | fix |\ndrafts-digest: {deliverable} {dg}\n"
                             f"```scores\n{json.dumps({'deliverable': deliverable, **dict.fromkeys(crits, 2)})}\n```\n",
                             encoding="utf-8")
    (p / "reviews" / "guideline-checklist.json").write_text(json.dumps(
        {"guideline": "STROBE", "deliverable": deliverable, "items": {i: {"status": "na", "reason": "fixture"} for i in IDS}}),
        encoding="utf-8")


class TestAudit(unittest.TestCase):
    def setUp(self):
        self.t = Path(tempfile.mkdtemp())
        p = self.p = init_project.create(self.t / "p", "T", "thesis-masters", "cohort", "vi", "vi")
        (p / "ledgers" / "references.json").write_text(json.dumps({"references": [OK, BAD]}), encoding="utf-8")
        (p / "ledgers" / "results-ledger.json").write_text(json.dumps({"results": [RES]}), encoding="utf-8")
        (p / "05_analysis" / "output").mkdir(parents=True, exist_ok=True)
        (p / "05_analysis" / "output" / "results.json").write_text(json.dumps(
            {"results": [{"id": "R-A1-001", "analysis_id": "A1", "status": "prespecified"}]}), encoding="utf-8")
        (p / "03_protocol" / "sap.md").write_text(SAP, encoding="utf-8")
        self.d = p / "06_writing" / "thesis"
        self.d.mkdir(parents=True, exist_ok=True)
        for name, text in SECTIONS.items():
            (self.d / name).write_text(text, encoding="utf-8")
        write_reports(p)

    def tearDown(self):
        shutil.rmtree(self.t, ignore_errors=True)

    def cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = audit.main([str(self.p), *argv])
        return code, out.getvalue(), err.getvalue()

    def blocks(self):
        data = json.loads((self.p / "reviews" / "audit.json").read_text(encoding="utf-8"))
        return [f for f in data["findings"] if f["level"] == "block"]

    def test_clean_project_passes_and_g4_can_open(self):
        code, out, err = self.cli("thesis")
        self.assertEqual(code, 0, out + err)
        data = json.loads((self.p / "reviews" / "audit.json").read_text(encoding="utf-8"))
        self.assertEqual((data["deliverable"], data["deliverables"], data["blocks"]), ("thesis", ["thesis"], 0))
        self.assertIn("06_writing/thesis/ch4-discussion.md", data["files"])
        self.assertIn("ledgers/references.json", data["files"])
        md = (self.p / "reviews" / "audit.md").read_text(encoding="utf-8")
        self.assertIn("| Check | Code | Block | Warn |", md)
        self.assertIn("## Findings", md)
        gate.open_gate(self.p, "G4", by="A")
        self.assertTrue(gate.check_gate(self.p, "G4", "thesis")[0])

    def test_end_to_end_audit_gate_and_final_export_with_image(self):
        (self.d / "fig1.png").write_bytes(PNG)
        (self.d / "ch3-results.md").write_text(
            SECTIONS["ch3-results.md"] + "\n![Hình 3.1. Minh hoạ](fig1.png)\n", encoding="utf-8")
        write_reports(self.p)
        code, out, err = self.cli("thesis")
        self.assertEqual(code, 0, out + err)
        data = json.loads((self.p / "reviews" / "audit.json").read_text(encoding="utf-8"))
        self.assertIn("06_writing/thesis/fig1.png", data["files"])
        self.assertTrue(gate.export_problems(self.p, "thesis"))      # G4 not opened yet
        gate.open_gate(self.p, "G4", by="A")
        self.assertEqual(gate.export_problems(self.p, "thesis"), [])
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(assemble.assemble(self.p, "thesis", final=True), 0)
        self.assertTrue((self.p / "out" / "thesis.docx").is_file())

    def test_unverified_citation_blocks(self):
        (self.d / "ch4-discussion.md").write_text(SECTIONS["ch4-discussion.md"].replace("[@a2020]", "[@b2021]"),
                                                  encoding="utf-8")
        write_reports(self.p)
        code, out, _ = self.cli("thesis")
        self.assertEqual(code, 1)
        self.assertIn("E-REF block 06_writing/thesis/ch4-discussion.md:3: [@b2021] is not verified", out)
        with self.assertRaises(gate.Refused):
            gate.open_gate(self.p, "G4", by="A")

    def test_typed_number_blocks(self):
        (self.d / "ch3-results.md").write_text("# Chương 3\n\nOR hiệu chỉnh là 1,52.\n", encoding="utf-8")
        write_reports(self.p)
        self.assertEqual(self.cli("thesis")[0], 1)
        self.assertTrue(any(f["code"] == "E-NUM" and f["file"] == "06_writing/thesis/ch3-results.md" for f in self.blocks()))

    def test_reviews_missing_or_stale(self):
        (self.p / "reviews" / "scientific-editor.md").unlink()
        self.assertEqual(self.cli("thesis")[0], 1)
        self.assertTrue(any(f["code"] == "E-REV" and "scientific-editor" in f["msg"] for f in self.blocks()))
        write_reports(self.p)
        (self.d / "ch2-methods.md").write_text(SECTIONS["ch2-methods.md"] + "\nThêm một câu.\n", encoding="utf-8")
        code, out, _ = self.cli("thesis")
        self.assertEqual(code, 0, out)
        self.assertIn("E-REV warn reviews/citation-verifier.md:1", out)

    def test_review_falls_back_to_round_snapshot(self):
        snap = self.p / "reviews" / "rounds" / "thesis" / "r2" / "reviews"
        snap.mkdir(parents=True)
        shutil.copyfile(self.p / "reviews" / "citation-verifier.md", snap / "citation-verifier.md")
        (self.p / "reviews" / "citation-verifier.md").write_text(
            "STATUS: PASS\ndrafts-digest: manuscript " + "0" * 64 + "\n```scores\n{\"deliverable\": \"manuscript\", \"citations\": 2}\n```\n",
            encoding="utf-8")
        self.assertEqual(self.cli("thesis")[0], 0)

    def test_checklist_rules(self):
        (self.p / "reviews" / "guideline-checklist.json").unlink()
        self.cli("thesis")
        self.assertTrue(any(f["code"] == "E-RG" for f in self.blocks()))
        y = self.p / "project.yaml"
        y.write_text(y.read_text(encoding="utf-8").replace("reporting_guideline: STROBE", "reporting_guideline: CONSORT-2025"),
                     encoding="utf-8")
        write_reports(self.p)
        code, out, _ = self.cli("thesis")
        self.assertEqual(code, 0, out)
        self.assertIn("E-RG warn", out)

    def test_identifier_and_phi_guard_missing(self):
        (self.d / "ch2-methods.md").write_text(SECTIONS["ch2-methods.md"] + "\nCCCD 079123456789\n", encoding="utf-8")
        write_reports(self.p)
        self.cli("thesis")
        self.assertTrue(any(f["code"] == "E-PHI" for f in self.blocks()))
        with mock.patch.object(audit, "find_phi_scan", return_value=None):
            code, out, _ = self.cli("thesis")
        self.assertIn("E-PHI warn", out)
        self.assertIn("phi-guard not found", out)

    def test_paper_by_paper_chapter1_blocks(self):
        par = " ".join(f"Tác giả {n} năm 2020 ghi nhận kết quả [@a2020]." for n in "ABCD")
        (self.d / "ch1-literature-review.md").write_text(f"# Chương 1\n\n{par}\n\n{par}\n", encoding="utf-8")
        write_reports(self.p)
        self.cli("thesis")
        self.assertTrue(any(f["code"] == "E-LIT" for f in self.blocks()))

    def test_all_mode_and_errors(self):
        code, out, _ = self.cli()
        data = json.loads((self.p / "reviews" / "audit.json").read_text(encoding="utf-8"))
        self.assertEqual((data["deliverable"], data["deliverables"]), ("all", ["thesis"]))
        self.assertEqual(self.cli("manuscript")[0], 2)
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(audit.main([str(self.t / "none")]), 2)

    def test_online_network_error_exits_2(self):
        with mock.patch.object(audit, "verify_online", side_effect=audit.NetworkError("offline")):
            code, _, err = self.cli("thesis", "--online")
        self.assertEqual(code, 2)
        self.assertIn("offline", err)

    def test_json_flag_prints_the_audit(self):
        code, out, _ = self.cli("thesis", "--json")
        self.assertEqual(json.loads(out)["deliverable"], "thesis")

    def test_checklist_for_another_deliverable_does_not_count(self):
        c = self.p / "reviews" / "guideline-checklist.json"
        data = json.loads(c.read_text(encoding="utf-8"))
        data["deliverable"] = "manuscript"
        c.write_text(json.dumps(data), encoding="utf-8")
        self.cli("thesis")
        self.assertTrue(any(f["code"] == "E-RG" for f in self.blocks()))   # none matches thesis

    def append(self, name, text):
        (self.d / name).write_text((self.d / name).read_text(encoding="utf-8") + text, encoding="utf-8")
        write_reports(self.p)

    def codes(self):
        return {f["code"] for f in self.blocks()}

    def test_stat_block_for_undeclared_posthoc(self):
        (self.p / "05_analysis" / "output" / "results.json").write_text(json.dumps(
            {"results": [{"id": "R-A1-001", "analysis_id": "A1", "status": "posthoc"}]}), encoding="utf-8")
        self.assertEqual(self.cli("thesis")[0], 1)
        self.assertIn("E-STAT", self.codes())

    def test_consistency_block(self):
        self.append("ch2-methods.md", "\nCỡ mẫu gồm 120 bệnh nhân.\nCỡ mẫu gồm 125 bệnh nhân.\n")
        code, out, _ = self.cli("thesis")
        self.assertEqual(code, 1, out)
        self.assertIn("E-CONS", self.codes())

    def test_prose_density_block(self):
        self.append("ch2-methods.md", "\nMô hình này không chỉ giảm tải cho bác sĩ mà còn cải thiện kết quả điều trị.\n"
                    "Nó không chỉ nhanh mà còn chính xác. Quy trình đóng vai trò quan trọng trong thực hành.\n")
        self.assertEqual(self.cli("thesis")[0], 1)
        self.assertIn("P00", self.codes())

    def test_author_placeholder_blocks(self):
        self.append("ch2-methods.md", "\n[[TÁC GIẢ: bổ sung cỡ mẫu]]\n")
        self.assertEqual(self.cli("thesis")[0], 1)
        self.assertTrue(any(f["code"] == "E-FMT" and "placeholder" in f["msg"] for f in self.blocks()))

    def test_crash_in_a_check_is_a_block_not_a_clean_pass(self):
        (self.p / "ledgers" / "results-ledger.json").write_text("[]", encoding="utf-8")
        code, out, err = self.cli("thesis")
        self.assertEqual(code, 1, out + err)
        self.assertTrue(any("could not run: " in f["msg"] for f in self.blocks()), self.blocks())

    def test_unexpected_exception_exits_2_and_removes_old_reports(self):
        self.assertEqual(self.cli("thesis")[0], 0)
        self.assertTrue((self.p / "reviews" / "audit.json").is_file())
        with mock.patch.object(audit, "run", side_effect=RuntimeError("boom")):
            code, _, err = self.cli("thesis")
        self.assertEqual(code, 2)
        self.assertIn("boom", err)
        self.assertFalse((self.p / "reviews" / "audit.json").exists())
        self.assertFalse((self.p / "reviews" / "audit.md").exists())

    def stub_phi(self, body):
        s = self.t / "phi_stub.py"
        s.write_text(body, encoding="utf-8")
        return mock.patch.object(audit, "find_phi_scan", return_value=s)

    def test_phi_scan_strong_exit_without_parsable_line_blocks(self):
        with self.stub_phi("import sys\nprint('garbled')\nsys.exit(1)\n"):
            code, out, _ = self.cli("thesis")
        self.assertEqual(code, 1)
        self.assertIn("phi_scan reported a strong finding that could not be read", out)

    def test_phi_scan_other_exit_codes_warn(self):
        with self.stub_phi("import sys\nsys.exit(3)\n"):
            code, out, _ = self.cli("thesis")
        self.assertEqual(code, 0, out)
        self.assertIn("E-PHI warn", out)
        self.assertIn("phi_scan could not run (exit 3)", out)

    def test_audit_md_explains_each_code_in_output_language(self):
        self.append("ch2-methods.md", "\n[[TÁC GIẢ: bổ sung]]\n")
        self.cli("thesis")
        md = (self.p / "reviews" / "audit.md").read_text(encoding="utf-8")
        self.assertIn("## Cách sửa / How to fix", md)
        self.assertIn("- `E-FMT`: thêm phần còn thiếu", md)
        self.assertLess(md.index("How to fix"), md.index("## Findings"))

    def test_gate_export_files_cover_drafts_order_and_images(self):
        (self.d / "fig1.png").write_bytes(PNG)
        self.append("ch3-results.md", "\n![Hình 3.1. x](fig1.png)\n")
        (self.d / "order.txt").write_text("ch1-*.md\nch2-methods.md\nch3-results.md\nch4-discussion.md\n05-ket-luan.md\n",
                                          encoding="utf-8")
        names = {f.name for f in gate.export_files(self.p, "thesis")}
        self.assertTrue({"fig1.png", "order.txt", "ch3-results.md"} <= names)
