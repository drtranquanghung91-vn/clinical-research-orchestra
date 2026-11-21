import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
from _paths import ORCH_SCRIPTS
import invariants

SCRIPT = ORCH_SCRIPTS / "invariants.py"
P1 = "Tỷ lệ OR 1,42 (KTC 95%: 1,05–1,91) [@smith2020; @lee2019] {{R-A1-001.ci}}."
P2 = "Kết quả có thể do nhiễu. Hiệu số 0,83 <!-- derived: R-A1-001.hi - 1 --> thấp."
P3 = "Đoạn thứ ba không đổi, n = 120."
BEFORE = "\n\n".join([P1, P2, P3]) + "\n"


def run(before, after, *extra, raw=False):
    with tempfile.TemporaryDirectory() as d:
        b, a, o = Path(d, "b.md"), Path(d, "a.md"), Path(d, "o.md")
        b.write_bytes(before if isinstance(before, bytes) else before.encode("utf-8"))
        a.write_bytes(after if isinstance(after, bytes) else after.encode("utf-8"))
        p = subprocess.run([sys.executable, str(SCRIPT), str(b), str(a), "--merge", str(o), *extra],
                           capture_output=True)
        p.stdout = p.stdout.decode("utf-8", "replace")
        p.stderr = p.stderr.decode("utf-8", "replace")
        if not o.exists():
            return p, None
        return p, (o.read_bytes() if raw else o.read_bytes().decode("utf-8"))


class TestInvariants(unittest.TestCase):
    def test_identical(self):
        self.assertEqual(invariants.compare(BEFORE, BEFORE), [])
        p, out = run(BEFORE, BEFORE)
        self.assertEqual(p.returncode, 0)
        self.assertEqual(out, BEFORE)

    def test_number_change_only_that_paragraph(self):
        after = BEFORE.replace("OR 1,42 (KTC 95%: 1,05–1,91)", "OR 1,4")
        f = invariants.compare(BEFORE, after)
        self.assertEqual([x["index"] for x in f], [1])
        self.assertIn("number 1,42 → 1,4", f[0]["problems"])
        p, _ = run(BEFORE, after)
        self.assertEqual(p.returncode, 1)
        self.assertIn(":1: paragraph 1: number 1,42 → 1,4", p.stdout)
        self.assertNotIn("paragraph 2", p.stdout)

    def test_hedge_dropped(self):
        f = invariants.compare(BEFORE, BEFORE.replace("có thể do", "do"))
        self.assertEqual([x["index"] for x in f], [2])
        self.assertIn("hedges 1 → 0", f[0]["problems"])

    def test_english_hedges(self):
        f = invariants.compare("It may help.\n", "It helps.\n")
        self.assertIn("hedges 1 → 0", f[0]["problems"])

    def test_reordered_citations_clean(self):
        after = BEFORE.replace("[@smith2020; @lee2019]", "[@lee2019; @smith2020]")
        self.assertEqual(invariants.compare(BEFORE, after), [])

    def test_dropped_citation(self):
        f = invariants.compare(BEFORE, BEFORE.replace("[@smith2020; @lee2019]", "[@lee2019]"))
        self.assertIn("citation [@smith2020] dropped", f[0]["problems"])

    def test_placeholder_changed(self):
        f = invariants.compare(BEFORE, BEFORE.replace("{{R-A1-001.ci}}", "{{R-A1-001.p}}"))
        self.assertIn("placeholder {{R-A1-001.ci}} dropped", f[0]["problems"])
        self.assertIn("placeholder {{R-A1-001.p}} added", f[0]["problems"])

    def test_derived_comment_changed(self):
        f = invariants.compare(BEFORE, BEFORE.replace("R-A1-001.hi - 1", "R-A1-001.hi - 2"))
        self.assertEqual([x["index"] for x in f], [2])

    def test_merge_restores_only_failing(self):
        after = BEFORE.replace("OR 1,42 (KTC 95%: 1,05–1,91)", "OR 1,4").replace("không đổi", "giữ nguyên")
        p, out = run(BEFORE, after)
        self.assertEqual(p.returncode, 1)
        self.assertIn("invariants: 1 of 3 paragraphs reverted", p.stdout)
        self.assertIn("OR 1,42 (KTC 95%: 1,05–1,91)", out)
        self.assertIn("giữ nguyên", out)

    def test_structure_change(self):
        p, out = run(BEFORE, BEFORE + "\nĐoạn mới.\n")
        self.assertEqual(p.returncode, 1)
        self.assertIn("paragraph structure changed (3 → 4); compare by hand", p.stdout)
        self.assertIn(":1: paragraph structure changed", p.stdout)
        self.assertEqual(out, BEFORE)

    def test_unicode_minus(self):
        self.assertEqual(invariants.compare("Chênh −0,18 điểm.\n", "Chênh -0,18 điểm.\n"), [])
        self.assertNotEqual(invariants.compare("Chênh −0,18 điểm.\n", "Chênh 0,18 điểm.\n"), [])

    def test_decimal_separator_normalised(self):
        self.assertEqual(invariants.compare("OR 1,42 ok.\n", "OR 1.42 ok.\n"), [])

    def test_names_and_keys_not_numbers(self):
        self.assertEqual(invariants.compare("COVID-19 [@a2020x].\n", "Đại dịch COVID-19 [@a2020x].\n"), [])

    def test_crlf_merge_keeps_untouched_bytes(self):
        before = BEFORE.replace("\n", "\r\n")
        after = before.replace("OR 1,42 (KTC 95%: 1,05–1,91)", "OR 1,4").replace("không đổi", "giữ nguyên")
        p, out = run(before, after, raw=True)
        self.assertEqual(p.returncode, 1)
        self.assertEqual(out, before.replace("không đổi", "giữ nguyên").encode("utf-8"))

    def test_crlf_structure_change_copies_before(self):
        before = BEFORE.replace("\n", "\r\n")
        p, out = run(before, before + "\r\nĐoạn mới.\r\n", raw=True)
        self.assertEqual(out, before.encode("utf-8"))

    def test_non_utf8_exit_2(self):
        p, _ = run(BEFORE, b"T\xe1 l\xff 1,4\n")
        self.assertEqual(p.returncode, 2)
        self.assertNotIn("Traceback", p.stderr)

    def test_import_reconfigures_stdout_replace(self):
        code = ("import sys, io; sys.stdout = io.TextIOWrapper(io.BytesIO(), encoding='ascii');"
                "sys.path.insert(0, %r); import invariants; print('\\u2192')" % str(ORCH_SCRIPTS))
        p = subprocess.run([sys.executable, "-c", code], capture_output=True)
        self.assertEqual(p.returncode, 0, p.stderr)

    def test_hedge_reflowed_lines_and_spaces(self):
        self.assertEqual(invariants.compare("Kết quả có thể do nhiễu.\n", "Kết quả có\nthể do nhiễu.\n"), [])
        self.assertEqual(invariants.compare("Chưa đủ bằng chứng.\n", "Chưa đủ  bằng\nchứng.\n"), [])

    def test_hedge_nfc(self):
        import unicodedata
        nfd = unicodedata.normalize("NFD", "Kết quả có thể do nhiễu.\n")
        self.assertEqual(invariants.compare("Kết quả có thể do nhiễu.\n", nfd), [])

    def test_may_month_not_hedge(self):
        self.assertEqual(invariants.compare("In May 2020 we enrolled.\n", "We enrolled in 2020.\n"), [])
        self.assertTrue(invariants.compare("Effects may vary.\n", "Effects vary.\n"))

    def test_lang_selects_hedge_list(self):
        self.assertEqual(invariants.compare("Effects may vary.\n", "Effects vary.\n", "vi"), [])
        self.assertEqual(invariants.compare("Có thể đúng.\n", "Đúng.\n", "en"), [])
        self.assertTrue(invariants.compare("Có thể đúng.\n", "Đúng.\n", "vi"))
        self.assertTrue(invariants.compare("Có thể đúng.\n", "Đúng.\n"))

    def test_narrative_citation(self):
        f = invariants.compare("@smith2020 found it.\n", "Smith found it.\n")
        self.assertIn("citation [@smith2020] dropped", f[0]["problems"])
        self.assertEqual(invariants.compare("@a2020 and [@b2019].\n", "[@b2019] and @a2020.\n"), [])
        self.assertEqual(invariants.compare("Mail me@example.com.\n", "Mail me@example.com now.\n"), [])

    def test_usage_error(self):
        p = subprocess.run([sys.executable, str(SCRIPT), "nope1.md", "nope2.md"], capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)


if __name__ == "__main__":
    unittest.main()
