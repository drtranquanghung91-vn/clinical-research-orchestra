import unittest

import _paths  # noqa: F401
import review_lint as rl

LISTING_EN = ("Smith et al. (2019) studied 120 women and found lower weight. "
              "Nguyen and Tran (2021) reported improved ovulation. "
              "Le et al. (2022) showed no change in insulin.")
LISTING_VI = ("Tác giả Nguyễn Văn A (2019) nghiên cứu 120 phụ nữ và thấy cân nặng giảm. "
              "Năm 2021, Trần Thị B báo cáo tỉ lệ rụng trứng tăng. "
              "Nghiên cứu của Lê C (2022) không thấy thay đổi insulin.")
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


if __name__ == "__main__":
    unittest.main()
