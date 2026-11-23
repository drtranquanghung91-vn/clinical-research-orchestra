import shutil
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
from crolib import reviews


def report(*lines):
    return "STATUS: PASS\n" + "\n".join(lines) + "\n"


class TestRequests(unittest.TestCase):
    def test_none_with_a_trailing_comment_is_no_request(self):
        for line in ("NEW-ANALYSIS: none", "NEW-ANALYSIS: none — wording only",
                     "NEW-ANALYSIS: none; wording only", "NEW-ANALYSIS: None.",
                     "NEW-ANALYSIS: không có (chỉ sửa câu chữ)",
                     "NEW-ANALYSIS: none - all findings are wording fixes"):
            self.assertEqual(reviews.parse_report(report(line))["requests"], [], line)

    def test_real_request_is_kept(self):
        got = reviews.parse_report(report("NEW-ANALYSIS: sex subgroup of A1, asked by the committee"))["requests"]
        self.assertEqual(len(got), 1)
        self.assertIn("sex subgroup", got[0])

    def test_request_starting_with_a_none_like_word_is_kept(self):
        got = reviews.parse_report(report("NEW-ANALYSIS: nonelderly subgroup (age < 65)"))["requests"]
        self.assertEqual(len(got), 1)


FENCE = "`" * 3


class TestReportPaths(unittest.TestCase):
    def setUp(self):
        self.t = Path(tempfile.mkdtemp())
        self.p = self.t / "p"
        (self.p / "reviews").mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.t, ignore_errors=True)

    def test_names(self):
        self.assertEqual(reviews.report_rel("scientific-editor", "thesis"), "reviews/scientific-editor-thesis.md")
        self.assertEqual(reviews.report_rel("consistency-auditor", "manuscript"), "reviews/consistency-manuscript.md")
        self.assertEqual(reviews.report_candidates("citation-verifier", "review"),
                         ["reviews/citation-verifier-review.md", "reviews/citation-verifier.md"])

    def test_per_deliverable_first_then_legacy_only_for_its_deliverable(self):
        legacy = self.p / "reviews" / "scientific-editor.md"
        legacy.write_text(f'{FENCE}scores\n{{"deliverable": "thesis", "structure": 2}}\n{FENCE}\n', encoding="utf-8")
        self.assertEqual(reviews.report_path(self.p, "scientific-editor", "thesis"), legacy)
        self.assertEqual(reviews.report_path(self.p, "scientific-editor", "manuscript"),
                         self.p / "reviews" / "scientific-editor-manuscript.md")
        per = self.p / "reviews" / "scientific-editor-thesis.md"
        per.write_text("STATUS: PASS\n", encoding="utf-8")
        self.assertEqual(reviews.report_path(self.p, "scientific-editor", "thesis"), per)



if __name__ == "__main__":
    unittest.main()
