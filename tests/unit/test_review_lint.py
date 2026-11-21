import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import _paths
import review_lint as rl

SCRIPT = _paths.ORCH_SCRIPTS / "review_lint.py"

LISTING_EN = ("Smith et al. (2019) studied 120 women and found lower weight. "
              "Nguyen and Tran (2021) reported improved ovulation. "
              "Le et al. (2022) showed no change in insulin.")
LISTING_VI = ("Tác giả Nguyễn Văn A (2019) nghiên cứu 120 phụ nữ và thấy cân nặng giảm. "
              "Năm 2021, Trần Thị B báo cáo tỉ lệ rụng trứng tăng. "
              "Nghiên cứu của Lê C (2022) không thấy thay đổi insulin.")
LISTING_KEYS = ("Smith [@smith2019] studied 120 women and found lower weight. "
                "Jones [@jones2020] found improved ovulation. "
                "Brown [@brown2021] reported no change in insulin.")
LISTING_MIXED = ("Nguyen et al, 2020 showed lower weight. "
                 "Tran et al. [3] reported improved ovulation. "
                 "Study by Le (2022) found no change in insulin.")
THEMATIC = ("Lifestyle programmes reduce weight by 3 to 5 kg across trials [@smith2019; @le2022]. "
            "Effects on ovulation are less consistent and depend on baseline BMI [@nguyen2021]. "
            "No trial was powered for live birth, which leaves the key outcome untested.")


class TestReviewLint(unittest.TestCase):
    def test_author_led(self):
        self.assertTrue(rl.author_led("Smith et al. (2019) studied 120 women."))
        self.assertTrue(rl.author_led("Tác giả Nguyễn Văn A (2019) nghiên cứu 120 phụ nữ."))
        self.assertTrue(rl.author_led("Năm 2021, Trần Thị B báo cáo tỉ lệ tăng."))
        self.assertTrue(rl.author_led("Nghiên cứu của Lê C (2022) không thấy thay đổi."))
        self.assertFalse(rl.author_led("Lifestyle programmes reduce weight by 3 to 5 kg [@a]."))

    def test_sentences_do_not_split_et_al(self):
        self.assertEqual(len(rl.sentences(LISTING_EN)), 3)

    def test_paragraphs_skip_headings_tables_lists(self):
        text = "# Heading\n\n" + THEMATIC + "\n\n| a | b |\n|---|---|\n\n- item\n\n" + LISTING_EN
        self.assertEqual(len(rl.paragraphs(text)), 2)

    def test_listing_chapter_blocks(self):
        rep = rl.lint("\n\n".join([LISTING_EN, LISTING_VI, THEMATIC]))
        self.assertEqual(len(rep["flagged"]), 2)
        self.assertTrue(rep["blocking"])

    def test_thematic_chapter_passes(self):
        rep = rl.lint("\n\n".join([THEMATIC, THEMATIC, LISTING_EN, THEMATIC, THEMATIC, THEMATIC, THEMATIC]))
        self.assertEqual(len(rep["flagged"]), 1)
        self.assertFalse(rep["blocking"])

    def test_author_led_single_letter_initials(self):
        self.assertTrue(rl.author_led("Trần Thị B (2021) báo cáo tỉ lệ tăng."))
        self.assertTrue(rl.author_led("Smith J. (2019) studied 120 women."))
        self.assertTrue(rl.author_led("Nguyễn Văn A và cộng sự (2020) ghi nhận kết quả."))

    def test_author_led_negative_common_word_with_year(self):
        self.assertFalse(rl.author_led("Weight reduction was sustained in later trials (2019) [@a]."))
        self.assertFalse(rl.author_led("Lifestyle change (2019) remains the first-line advice [@a]."))

    def test_fence_with_blank_line_does_not_hide_following_prose(self):
        text = "```\ncode\n\nmore code\n```\n\n" + "\n\n".join([LISTING_EN, LISTING_VI])
        self.assertEqual(len(rl.paragraphs(text)), 2)
        rep = rl.lint(text)
        self.assertEqual(len(rep["flagged"]), 2)
        self.assertTrue(rep["blocking"])

    # ---- author-led openers in the project's own citation syntax (final review #3)
    def test_author_led_citation_key_and_number(self):
        self.assertTrue(rl.author_led("Smith [@smith2019] found lower weight."))
        self.assertTrue(rl.author_led("Smith and Jones [@smith2019; @jones2020] found lower weight."))
        self.assertTrue(rl.author_led("Smith et al. [@smith2019] found lower weight."))
        self.assertTrue(rl.author_led("Tran et al. [3] reported improved ovulation."))
        self.assertTrue(rl.author_led("Tran [3,5] reported improved ovulation."))
        self.assertTrue(rl.author_led("Nguyễn và cộng sự [@nguyen2020] ghi nhận kết quả."))

    def test_author_led_comma_year(self):
        self.assertTrue(rl.author_led("Nguyen et al, 2020 showed lower weight."))
        self.assertTrue(rl.author_led("Nguyen, 2020 showed lower weight."))

    def test_author_led_study_by_without_article(self):
        self.assertTrue(rl.author_led("Study by Smith (2019) found lower weight."))
        self.assertFalse(rl.author_led("Review of the evidence shows lower weight [@a]."))

    def test_thematic_with_keys_at_end_not_flagged(self):
        self.assertFalse(rl.author_led("Weight fell by 3 kg in three trials [@smith2019; @jones2020]."))
        self.assertFalse(rl.author_led("In 2020, two cohorts reported lower weight [@nguyen2020]."))

    def test_listing_in_citation_syntax_blocks(self):
        rep = rl.lint("\n\n".join([LISTING_KEYS, LISTING_MIXED, THEMATIC]))
        self.assertEqual(len(rep["flagged"]), 2)
        self.assertTrue(rep["blocking"])


class TestReviewLintCli(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.dir = Path(self._td.name)

    def run_rl(self, path):
        return subprocess.run([sys.executable, str(SCRIPT), str(path)],
                              capture_output=True, text=True, encoding="utf-8")

    def test_exit_0_clean(self):
        f = self.dir / "ok.md"
        f.write_text("\n\n".join([THEMATIC] * 3), encoding="utf-8")
        p = self.run_rl(f)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertNotIn("E-LIT", p.stdout)

    def test_exit_1_block(self):
        f = self.dir / "bad.md"
        f.write_text("\n\n".join([LISTING_KEYS, LISTING_MIXED, THEMATIC]), encoding="utf-8")
        p = self.run_rl(f)
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        self.assertIn("E-LIT (block)", p.stdout)

    def test_exit_2_missing_file(self):
        p = self.run_rl(self.dir / "nope.md")
        self.assertEqual(p.returncode, 2)
        self.assertIn("cannot read", p.stderr)

    def test_exit_2_not_utf8(self):
        f = self.dir / "latin1.md"
        f.write_bytes("Nghi\xean c\xe9u".encode("latin-1") + b"\xff\xfe")
        p = self.run_rl(f)
        self.assertEqual(p.returncode, 2)
        self.assertIn("cannot read", p.stderr)


if __name__ == "__main__":
    unittest.main()
