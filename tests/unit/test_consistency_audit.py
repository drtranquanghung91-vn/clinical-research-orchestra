import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import _paths
import consistency_audit as ca

SCRIPT = _paths.ORCH_SCRIPTS / "consistency_audit.py"
LEDGER = {"results": [
    {"id": "R-A1-001", "kind": "percent", "value": 86.3, "count": 69, "n": 80, "status": "prespecified"},
    {"id": "R-A1-002", "kind": "or", "value": 1.8412, "ci": [1.214, 2.786], "p": 0.0041, "n": 80,
     "status": "prespecified"}]}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.p = Path(self.tmp.name)
        (self.p / "ledgers").mkdir()
        (self.p / "ledgers" / "results-ledger.json").write_text(json.dumps(LEDGER), encoding="utf-8")
        (self.p / "project.yaml").write_text("language:\n  output: vi\n", encoding="utf-8")
        (self.p / "06_writing" / "thesis").mkdir(parents=True)
        (self.p / "07_present").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def w(self, rel, text):
        f = self.p / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8")
        return f

    def run_audit(self, **kw):
        return ca.audit(self.p, **kw)

    def blocks(self, res=None, needle=""):
        res = self.run_audit() if res is None else res
        return [r for r in res if r[0] == "block" and needle in r[2]]

    def warns(self, res=None, needle=""):
        res = self.run_audit() if res is None else res
        return [r for r in res if r[0] == "warn" and needle in r[2]]


class TestSameQuantity(Base):
    def test_mzl_rate_conflict(self):
        self.w("07_present/abstract.md", "Tỷ lệ đáp ứng 85% ở nhóm điều trị.\n")
        self.w("06_writing/thesis/ch3.md", "Kết quả: tỷ lệ đáp ứng 86,3% sau 6 tháng.\n")
        b = self.blocks(needle="85%")
        self.assertEqual(len(b), 1, b)
        loc, msg = b[0][1], b[0][2]
        self.assertTrue(loc.endswith(":1"))
        self.assertIn("86,3%", msg)
        self.assertIn("abstract.md", loc + msg)
        self.assertIn("ch3.md", loc + msg)

    def test_equal_at_shorter_precision_is_fine(self):
        self.w("07_present/abstract.md", "Tỷ lệ đáp ứng 85%.\n")
        self.w("06_writing/thesis/ch3.md", "Tỷ lệ đáp ứng 85,0%.\n")
        self.assertEqual(self.blocks(), [])

    def test_different_keys_no_conflict(self):
        self.w("07_present/abstract.md", "Tỷ lệ đáp ứng 85%.\n")
        self.w("06_writing/thesis/ch3.md", "Tỷ lệ tử vong 12%.\n")
        self.assertEqual(self.blocks(), [])

    def test_different_units_no_conflict(self):
        self.w("06_writing/thesis/ch3.md", "Tỷ lệ đáp ứng 85%.\nTỷ lệ đáp ứng 85,4 lần.\n")
        self.assertEqual(self.blocks(), [])

    def test_cons_ok_escape(self):
        self.w("07_present/abstract.md", "Tỷ lệ đáp ứng 85%.\n")
        self.w("06_writing/thesis/ch3.md",
               "Tỷ lệ đáp ứng 86,3%. <!-- cons-ok: nhóm khác -->\n")
        self.assertEqual(self.blocks(), [])

    def test_years_headings_and_citations_ignored(self):
        self.w("06_writing/thesis/a.md", "# Mục tiêu 2\nNăm 2021 và [12] và nhóm 1.\n")
        self.w("06_writing/thesis/b.md", "# Mục tiêu 3\nNăm 2023 và [13] và nhóm 2.\n")
        self.assertEqual(self.blocks(), [])

    def test_english_and_integer_counts(self):
        self.w("06_writing/thesis/a.md", "The response rate is 85% overall. Total patients enrolled 120 patients.\n")
        self.w("06_writing/thesis/b.md", "The response rate is 86.3% overall. Total patients enrolled 130 patients.\n")
        self.assertEqual(len(self.blocks()), 2)

    def test_code_fence_skipped(self):
        self.w("06_writing/thesis/a.md", "Tỷ lệ đáp ứng 85%.\n```\nTỷ lệ đáp ứng 99%\n```\n")
        self.assertEqual(self.blocks(), [])


class TestSampleSize(Base):
    def test_approx_sample_size(self):
        self.w("06_writing/thesis/ch2.md", "Cỡ mẫu tối thiểu ≈26 bệnh nhân.\n")
        b = self.blocks(needle="sample size must be a whole number rounded up")
        self.assertEqual(len(b), 1)
        self.assertIn("≈26", b[0][2])

    def test_other_markers(self):
        self.w("06_writing/thesis/ch2.md",
               "Khoảng 40 người bệnh được chọn.\nWe enrolled approximately 52 participants.\n"
               "Cỡ mẫu: n ≈ 30.\n")
        self.assertEqual(len(self.blocks(needle="sample size")), 3)

    def test_decimal_count(self):
        self.w("06_writing/thesis/ch2.md", "Cần n = 26,65 bệnh nhân mỗi nhóm.\n")
        self.assertEqual(len(self.blocks(needle="sample size")), 1)

    def test_no_false_positives(self):
        self.w("06_writing/thesis/ch2.md",
               "Cỡ mẫu n = 27 bệnh nhân.\nKhoảng 60% bệnh nhân đáp ứng.\n"
               "Theo dõi khoảng 3 tháng ở 120 bệnh nhân.\nTuổi khoảng 50.\n")
        self.assertEqual(self.blocks(needle="sample size"), [])


class TestDates(Base):
    def test_end_date_mismatch(self):
        self.w("07_present/abstract.md", "Nghiên cứu từ 01/2021 đến 06/2023.\n")
        self.w("06_writing/thesis/ch2.md", "Thu thập từ tháng 1/2021 đến tháng 12/2023.\n")
        b = self.blocks(needle="date")
        self.assertEqual(len(b), 1, b)
        self.assertIn("abstract.md", b[0][1] + b[0][2])
        self.assertIn("ch2.md", b[0][1] + b[0][2])

    def test_same_range_in_other_formats_ok(self):
        self.w("07_present/abstract.md", "Từ 01/2021 đến 06/2023.\n")
        self.w("06_writing/thesis/ch2.md",
               "Từ tháng 1 năm 2021 đến tháng 6 năm 2023. Hay 2021-01 to 2023-06, "
               "January 2021 until June 2023, 01/01/2021 - 30/06/2023.\n")
        self.assertEqual(self.blocks(needle="date"), [])

    def test_same_end_different_start(self):
        self.w("06_writing/thesis/a.md", "From 03/2021 to 06/2023.\n")
        self.w("06_writing/thesis/b.md", "From 05/2021 to 06/2023.\n")
        self.assertEqual(len(self.blocks(needle="date")), 1)

    def test_dates_not_counted_as_quantities(self):
        self.w("06_writing/thesis/a.md", "Thu thập dữ liệu từ 01/2021 đến 06/2023.\n")
        self.w("06_writing/thesis/b.md", "Thu thập dữ liệu từ 01/2021 đến 06/2023.\n")
        self.assertEqual(self.blocks(), [])


class TestAbstract(Base):
    def test_abstract_number_missing_elsewhere(self):
        self.w("07_present/abstract.md", "Tỷ lệ đáp ứng 77,7%.\n")
        self.w("06_writing/thesis/ch3.md", "Tỷ lệ đáp ứng khác 12,5%.\n")
        self.assertEqual(len(self.warns(needle="77,7%")), 1)

    def test_abstract_number_in_ledger_or_other_file(self):
        self.w("07_present/abstract.md", "Tỷ lệ đáp ứng 86,3%, OR 1,84, KTC 1,21 đến 2,79, p = 0,004, 12,5%.\n")
        self.w("06_writing/thesis/ch3.md", "Tỷ lệ phụ 12,5%.\n")
        self.assertEqual(self.warns(needle="abstract"), [])


class TestPercentSum(Base):
    TABLE = ("| Đặc điểm | n (%) |\n|---|---|\n| Nam | 46 (46,2%) |\n| Nữ | 30 (30,1%) |\n"
             "| Khác | 22 (22,0%) |\n| Tổng | 98 (100%) |\n")

    def test_sum_warn(self):
        self.w("06_writing/thesis/ch3.md", self.TABLE)
        w = self.warns(needle="sum")
        self.assertEqual(len(w), 1)
        self.assertIn("98,3", w[0][2])
        self.assertTrue(w[0][1].endswith(":6"))

    def test_sum_ok(self):
        self.w("06_writing/thesis/ch3.md", self.TABLE.replace("22,0", "23,7"))
        self.assertEqual(self.warns(needle="sum"), [])

    def test_plain_percent_cells_and_total_english(self):
        self.w("06_writing/thesis/ch3.md", "| A | 60% |\n| B | 30% |\n| Total | 100% |\n")
        self.assertEqual(len(self.warns(needle="sum")), 1)


class TestTerms(Base):
    def test_builtin_variant(self):
        self.w("06_writing/thesis/ch1.md", "Mức HbA1C và hba1c; HbA1c đúng. Bệnh tiểu đường týp 2.\n")
        w = self.warns(needle="should be")
        self.assertEqual(len(w), 2, w)

    def test_project_terms(self):
        (self.p / "project.yaml").write_text(
            "language:\n  output: vi\nterms:\n  tái nhập viện: [nhập viện lại, \"tái nhập\"]\n"
            "  BN:\n    - bệnh nhân\n", encoding="utf-8")
        self.w("06_writing/thesis/ch1.md", "Nguy cơ nhập viện lại cao. Mỗi bệnh nhân.\n")
        self.assertEqual(len(self.warns(needle="should be")), 2)

    def test_cons_ok_term(self):
        self.w("06_writing/thesis/ch1.md", "HbA1C <!-- cons-ok: trích nguyên văn -->\n")
        self.assertEqual(self.warns(needle="should be"), [])


class TestFilesAndJson(Base):
    def test_json_strings_with_path(self):
        self.w("07_present/defense/deck.json",
               json.dumps({"slides": [{"title": "Tỷ lệ đáp ứng 90%"}]}, ensure_ascii=False))
        self.w("06_writing/thesis/ch3.md", "Tỷ lệ đáp ứng 86,3%.\n")
        b = self.blocks(needle="90%")
        self.assertEqual(len(b), 1, b)
        self.assertIn("deck.json:slides[0].title", b[0][1] + b[0][2])

    def test_rendered_preferred_over_source(self):
        self.w("07_present/abstract.md", "Tỷ lệ đáp ứng 85%.\n")
        self.w("06_writing/thesis/ch3.md", "Tỷ lệ đáp ứng {{R-A1-001}}.\n")
        self.w("06_writing/thesis/ch3.rendered.md", "Tỷ lệ đáp ứng 85%.\n")
        self.assertEqual(self.blocks(), [])
        res = self.run_audit()
        self.assertFalse(any("ch3.md" in r[1] + r[2] for r in res))

    def test_placeholder_rendered_in_memory(self):
        self.w("07_present/abstract.md", "Tỷ lệ đáp ứng 85%.\n")
        self.w("06_writing/thesis/ch3.md", "Tỷ lệ đáp ứng {{R-A1-001}}.\n")
        b = self.blocks()
        self.assertEqual(len(b), 1)
        self.assertIn("86,3%", b[0][2])

    def test_explicit_files(self):
        a = self.w("x/a.md", "Tỷ lệ đáp ứng 85%.\n")
        b = self.w("x/b.md", "Tỷ lệ đáp ứng 91%.\n")
        self.w("06_writing/thesis/ch3.md", "Tỷ lệ đáp ứng 70%.\n")
        self.assertEqual(len(self.blocks(self.run_audit(files=[a, b]))), 1)
        self.assertEqual(self.blocks(self.run_audit(files=[a])), [])


class TestResultIdMasking(Base):
    def test_result_ids_not_read_as_numbers(self):
        self.w("07_present/defense/deck.json", json.dumps(
            {"slides": [{"title": "Tỷ lệ đáp ứng R-A12-062 và R-A12-063.part"}]}, ensure_ascii=False))
        self.w("06_writing/thesis/ch3.md", "Tỷ lệ đáp ứng R-A12-064 và R-A0-061.\n")
        self.assertEqual(self.blocks(), [])


class TestRealTextFalsePositives(Base):
    def test_ci_bounds_never_compared(self):
        self.w("06_writing/thesis/a.md", "OR thô 1,09 (KTC 95%: 0,74–1,61) ở nhóm A.\n")
        self.w("06_writing/thesis/b.md",
               "Tỷ lệ chung 22,1% (KTC 95%: 19,7–24,6) và khoảng tin cậy 95% 0,94 đến 2,12.\n")
        self.assertEqual(self.blocks(), [])

    def test_group_labels_and_ranges(self):
        self.w("06_writing/thesis/a.md",
               "So với nhóm HbA1c <7% (tham chiếu), tỷ lệ tái nhập viện ở nhóm 7–9% là 20% "
               "và ở nhóm >9% là 25%.\n")
        self.w("06_writing/thesis/b.md", "Tỷ lệ tái nhập viện ở nhóm <7% là 19% và nhóm 7–9% là 21%.\n")
        self.assertEqual(self.blocks(), [])

    def test_section_and_figure_references(self):
        self.w("06_writing/thesis/a.md", "Xem mục 1.7, bảng 3.2, biểu đồ 2.1 và figure 4.1, chương 12.\n")
        self.w("06_writing/thesis/b.md", "Xem mục 1.5, bảng 3.3, biểu đồ 2.2 và figure 4.2, chương 13.\n")
        self.assertEqual(self.blocks(), [])

    def test_time_points_keyed_with_unit_and_following_words(self):
        self.w("06_writing/thesis/a.md", "Tuổi chiếm ưu thế ở mốc 30 ngày, các chỉ số viêm nổi lên.\n")
        self.w("06_writing/thesis/b.md", "Biến chứng chiếm ưu thế ở mốc 365 ngày (phân tích SHAP).\n")
        self.assertEqual(self.blocks(), [])
        self.w("06_writing/thesis/c.md", "Thời điểm theo dõi 30 ngày sau xuất viện.\n")
        self.w("06_writing/thesis/d.md", "Thời điểm theo dõi 90 ngày sau xuất viện.\n")
        self.assertEqual(len(self.blocks()), 1)

    def test_vietnamese_thousands_separator(self):
        self.w("06_writing/thesis/a.md",
               "Một nghiên cứu khác trên 1.627 người bệnh và 12.041 người bệnh (cùng 2.007 người bệnh dùng).\n")
        self.assertEqual(self.blocks(), [])
        self.w("06_writing/thesis/b.md", "Cỡ mẫu n = 1.627 người bệnh; n = 26,65 người bệnh.\n")
        self.assertEqual(len(self.blocks(needle="sample size")), 1)

    def test_numbered_copy_not_audited_twice(self):
        self.w("06_writing/thesis/ch1.md", "Cỡ mẫu ≈26 bệnh nhân.\n")
        self.w("06_writing/thesis/ch1.numbered.md", "1 Cỡ mẫu ≈26 bệnh nhân.\n")
        self.assertEqual(len(self.blocks(needle="sample size")), 1)

    def test_overall_row_is_not_a_sum_row(self):
        self.w("06_writing/thesis/ch3.md",
               "| Nhóm | Tái nhập, n (%) |\n|---|---|\n| Chung | 22,1% |\n| A | 19,6% |\n| B | 25,5% |\n")
        self.assertEqual(self.warns(needle="sum"), [])

    def test_total_row_must_be_100(self):
        self.w("06_writing/thesis/ch3.md", "| A | 10% |\n| B | 10% |\n| Tổng | 50% |\n")
        self.assertEqual(self.warns(needle="sum"), [])
        self.w("06_writing/thesis/ch4.md", "| A | 60% |\n| B | 30% |\n| Tổng cộng | 100% |\n")
        self.assertEqual(len(self.warns(needle="sum")), 1)

    def test_fictional_cohort_has_no_blocks(self):
        ex = _paths.ROOT / "examples" / "fictional-cohort"
        if not ex.is_dir():
            self.skipTest("examples/fictional-cohort not present")
        self.assertEqual(self.blocks(ca.audit(ex)), [])


class TestCli(Base):
    def run_cli(self, *args):
        r = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True,
                           text=True, encoding="utf-8")
        return r.returncode, r.stdout, r.stderr

    def test_clean_exit_0(self):
        self.w("06_writing/thesis/ch3.md", "Tỷ lệ đáp ứng 86,3%.\n")
        code, out, _ = self.run_cli(self.p)
        self.assertEqual(code, 0, out)
        self.assertIn("consistency_audit: 0 block, 0 warn", out)

    def test_block_exit_1(self):
        self.w("07_present/abstract.md", "Tỷ lệ đáp ứng 85%.\n")
        self.w("06_writing/thesis/ch3.md", "Tỷ lệ đáp ứng 86,3%.\n")
        code, out, _ = self.run_cli(self.p)
        self.assertEqual(code, 1)
        self.assertIn("E-CONS block", out)
        self.assertIn("consistency_audit: 1 block, 1 warn", out)

    def test_warn_only_exit_0(self):
        self.w("06_writing/thesis/ch1.md", "Mức HbA1C.\n")
        code, out, _ = self.run_cli(self.p)
        self.assertEqual(code, 0)
        self.assertIn("E-CONS warn", out)

    def test_missing_project_exit_2(self):
        code, _, err = self.run_cli(self.p / "nope")
        self.assertEqual(code, 2)
        self.assertIn("consistency_audit", err)

    def test_missing_file_exit_2(self):
        code, _, _ = self.run_cli(self.p, self.p / "nope.md")
        self.assertEqual(code, 2)

    def test_lang_flag(self):
        self.w("06_writing/thesis/ch3.md", "Tỷ lệ đáp ứng 86,3%.\n")
        code, _, _ = self.run_cli(self.p, "--lang", "en")
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
