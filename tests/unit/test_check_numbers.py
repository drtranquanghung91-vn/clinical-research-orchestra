import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
from _paths import ORCH_SCRIPTS
import check_numbers

SCRIPT = ORCH_SCRIPTS / "check_numbers.py"
RESULTS = [{"id": "R-A0-001", "kind": "percent", "value": 85.04, "count": 910},
           {"id": "R-A1-001", "kind": "or", "value": 1.8412, "ci": [1.214, 2.786], "p": 0.0004, "n": 1070}]


class TestCheckNumbers(unittest.TestCase):
    def test_matching_numbers_pass(self):
        text = "Of 1070 patients, 910 (85.0%) were followed. OR 1.84 (95% CI 1.21–2.79), p < 0.001."
        self.assertEqual(check_numbers.find_unmatched(text, RESULTS, "en"), [])

    def test_drift_is_found(self):
        self.assertEqual(check_numbers.find_unmatched("Follow-up was 86.3%.", RESULTS, "en"), [(1, "86.3%")])

    def test_exclusions(self):
        text = ("# 3.2 Kết quả 2026\n"
                "Bảng 3.2 cho thấy {{R-A1-001.full}} [@smith2019] [1–3,5] vào 12/03/2025, 3 nhóm.\n"
                "Hiệu số 0,83 <!-- derived: R-A1-001.ci -->.")
        self.assertEqual(check_numbers.find_unmatched(text, RESULTS, "vi"), [])

    def test_vietnamese_comma(self):
        self.assertEqual(check_numbers.find_unmatched("tỷ lệ 85,0%", RESULTS, "vi"), [])
        self.assertEqual(check_numbers.find_unmatched("tỷ lệ 85,1%", RESULTS, "vi"), [(1, "85,1%")])

    def test_p_threshold_only_when_ledger_has_small_p(self):
        self.assertEqual(check_numbers.find_unmatched("p < 0.001", [{"value": 1.0, "p": 0.2}], "en"), [(1, "0.001")])

    def test_thousands_separator_is_a_finding(self):
        # Expected: this project writes no thousands separators; the fix is a placeholder.
        self.assertNotEqual(check_numbers.find_unmatched("n = 1,070", RESULTS, "en"), [])
        self.assertNotEqual(check_numbers.find_unmatched("n = 1.070", RESULTS, "vi"), [])

    def test_unicode_minus(self):
        md = [{"id": "R-A2-001", "kind": "md", "value": -0.30, "ci": [-0.55, -0.05]}]
        self.assertEqual(check_numbers.find_unmatched("−0.30 (95% CI −0.55 to −0.05)", md, "en"), [])
        self.assertEqual(check_numbers.find_unmatched("−0,30 (KTC 95%: −0,55 đến −0,05)", md, "vi"), [])
        self.assertEqual(check_numbers.find_unmatched("−0.31", md, "en"), [(1, "-0.31")])

    def test_ci_label_variants(self):
        for t in ("khoảng tin cậy 95% 1.21–2.79", "95% confidence interval 1.21–2.79", "95% CrI 1.21–2.79",
                  "KTC95% 1.21–2.79", "95% ci 1.21–2.79", "95% khoảng tin cậy 1.21–2.79"):
            self.assertEqual(check_numbers.find_unmatched(t, RESULTS, "en"), [], t)
        self.assertEqual(check_numbers.find_unmatched("coverage 95%", RESULTS, "en"), [(1, "95%")])

    def test_significance_thresholds(self):
        for t, lang in (("p < 0,05", "vi"), ("α = 0.05", "en"), ("alpha = 0.05", "en"), ("p ≤ 0.01", "en"),
                        ("p > 0,1", "vi"), ("P = 0.05", "en")):
            self.assertEqual(check_numbers.find_unmatched(t, RESULTS, lang), [], t)
        self.assertEqual(check_numbers.find_unmatched("p = 0.03", RESULTS, "en"), [(1, "0.03")])

    def test_hyphenated_names(self):
        self.assertEqual(check_numbers.find_unmatched("COVID-19, SARS-CoV-2 and IL-6 in 910 patients", RESULTS, "en"), [])

    def test_not_a_result_marker(self):
        t = "Tuổi 18–65 <!-- not-a-result: eligibility --> và 77 <!-- not-a-result: ward code -->."
        self.assertEqual(check_numbers.find_unmatched(t, RESULTS, "vi"), [])
        self.assertEqual(check_numbers.find_unmatched("Tuổi 18–65 và 77", RESULTS, "vi"), [(1, "18"), (1, "65"), (1, "77")])

    def test_cli(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "ledgers").mkdir()
            (p / "ledgers" / "results-ledger.json").write_text(json.dumps({"results": RESULTS}), encoding="utf-8")
            f = p / "r.md"
            f.write_text("ok 85.0%\nbad 86.3%\n", encoding="utf-8")
            r = subprocess.run([sys.executable, str(SCRIPT), str(p), str(f), "--lang", "en"],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)
            self.assertIn("E-NUM block", r.stdout)
            self.assertIn("r.md:2: 86.3%", r.stdout)
            r2 = subprocess.run([sys.executable, str(SCRIPT), str(p), str(p / "missing.md")],
                                capture_output=True, text=True)
            self.assertEqual(r2.returncode, 2)

    def _run_with_ledger(self, raw: bytes):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "ledgers").mkdir()
            (p / "ledgers" / "results-ledger.json").write_bytes(raw)
            f = p / "r.md"
            f.write_text("ok 85.0%\n", encoding="utf-8")
            return subprocess.run([sys.executable, str(SCRIPT), str(p), str(f), "--lang", "en"],
                                  capture_output=True, text=True)

    def test_bad_ledgers_exit_2_without_traceback(self):
        for raw in (b"{not json", b"[1, 2]", b'{"results": {"a": 1}}', b'{"results": [1, 2]}',
                    b"\xff\xfe\x00bad", b'"text"'):
            r = self._run_with_ledger(raw)
            self.assertEqual(r.returncode, 2, raw)
            self.assertIn("check_numbers", r.stderr)
            self.assertNotIn("Traceback", r.stderr, raw)

    def test_bom_ledger_is_read(self):
        raw = b"\xef\xbb\xbf" + json.dumps({"results": RESULTS}).encode("utf-8")
        r = self._run_with_ledger(raw)
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
