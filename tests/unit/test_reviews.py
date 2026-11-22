import unittest

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


if __name__ == "__main__":
    unittest.main()
