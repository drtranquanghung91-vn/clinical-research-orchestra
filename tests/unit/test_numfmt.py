import unittest
from decimal import Decimal

import _paths  # noqa: F401
from crolib import numfmt


class TestNumfmt(unittest.TestCase):
    def test_round_half_up(self):
        self.assertEqual(numfmt.fmt(2.345, 2), "2.35")
        self.assertEqual(numfmt.fmt(0.125, 2), "0.13")
        self.assertEqual(numfmt.fmt(92.0, 0), "92")

    def test_vietnamese_decimal_comma(self):
        self.assertEqual(numfmt.fmt(1.84, 2, "vi"), "1,84")

    def test_p_values(self):
        self.assertEqual(numfmt.fmt_p(0.0004), "< 0.001")
        self.assertEqual(numfmt.fmt_p(0.0004, "vi"), "< 0,001")
        self.assertEqual(numfmt.fmt_p(0.0381), "0.038")

    def test_render_parts(self):
        rec = {"kind": "or", "value": 1.8412, "ci": [1.214, 2.786], "p": 0.0041, "n": 1070}
        self.assertEqual(numfmt.render(rec, "value", "en"), "1.84")
        self.assertEqual(numfmt.render(rec, "ci", "en"), "1.21–2.79")
        self.assertEqual(numfmt.render(rec, "p", "en"), "0.004")
        self.assertEqual(numfmt.render(rec, "n", "en"), "1070")
        self.assertEqual(numfmt.render(rec, "full", "en"), "1.84 (95% CI 1.21–2.79)")
        self.assertEqual(numfmt.render(rec, "full", "vi"), "1,84 (KTC 95%: 1,21–2,79)")

    def test_render_full_by_kind(self):
        self.assertEqual(numfmt.render({"kind": "mean", "value": 54.06, "sd": 7.31}, "full", "en"), "54.1 ± 7.3")
        self.assertEqual(numfmt.render({"kind": "median", "value": 7.2, "iqr": [6.0, 8.45]}, "full", "en"), "7.2 (6.0–8.5)")
        self.assertEqual(numfmt.render({"kind": "percent", "value": 12.54, "count": 134}, "full", "en"), "134 (12.5%)")

    def test_render_missing_part_raises(self):
        with self.assertRaises(KeyError):
            numfmt.render({"kind": "or", "value": 1.0}, "ci", "en")

    def test_parse_tokens(self):
        toks = numfmt.parse_tokens("OR 1.84 (95% CI 1.21-2.79), p=0.004", "en")
        self.assertIn(("1.84", Decimal("1.84"), 2), toks)
        self.assertIn(("0.004", Decimal("0.004"), 3), toks)
        vi = numfmt.parse_tokens("tỷ lệ 12,5% ở nhóm", "vi")
        self.assertEqual(vi[0][:2], ("12,5%", Decimal("12.5")))

    def test_matches(self):
        self.assertTrue(numfmt.matches(Decimal("1.84"), 2, [1.8412]))
        self.assertFalse(numfmt.matches(Decimal("86.3"), 1, [85.0]))

    def test_candidates(self):
        rec = {"value": 1.0, "ci": [0.5, 2.0], "p": 0.2, "n": 10, "sd": None, "iqr": None, "count": None}
        self.assertEqual(sorted(numfmt.candidates(rec)), [0.2, 0.5, 1.0, 2.0, 10])
