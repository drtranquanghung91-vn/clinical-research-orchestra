import contextlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
import extract_check
from p5_helpers import review_project

HEAD = "study_id,outcome,timepoint,group,n,events,mean,sd,es,se\n"
A = HEAD + "S01,mortality,30 days,drug,50,5,,,,\nS01,mortality,30 days,placebo,50,9,,,,\nS02,mortality,30 days,drug,40,4,,,,\n"
B = HEAD + "S01,mortality,30 days,drug,50,6,,,,\nS01,mortality,30 days,placebo,50,9.0,,,,\nS02,mortality,30 days,drug,40,4,,,,\n"
ROB_HEAD = "study_id,outcome,tool,domain,judgement,support,reviewer\n"


def rob_rows(overall="some concerns", reviewer="Reviewer A; Reviewer B", d3="some concerns"):
    doms = {"D1": "low", "D2": "low", "D3": d3, "D4": "low", "D5": "low", "overall": overall}
    return ROB_HEAD + "".join(f'S01,mortality,RoB 2,{d},{j},"quote p. 4",{reviewer}\n' for d, j in doms.items())


def cli(p):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        code = extract_check.main([str(p)])
    return code, out.getvalue()


class TestExtractCheck(unittest.TestCase):
    def setUp(self):
        self.t = Path(tempfile.mkdtemp())
        self.p = review_project(self.t)
        self.d = self.p / "04_data" / "sr"

    def tearDown(self):
        shutil.rmtree(self.t, ignore_errors=True)

    def w(self, name, text):
        (self.d / name).write_text(text, encoding="utf-8")

    def msgs(self, level=None):
        return [m for s, _, m in extract_check.check(self.p) if level in (None, s)]

    def test_differences_listed_and_consensus_needed(self):
        self.w("extraction-reviewer-a.csv", A)
        self.w("extraction-reviewer-b.csv", B)
        warns = self.msgs("warn")
        self.assertTrue(any("S01 / mortality / 30 days / drug: events Reviewer A=5, Reviewer B=6" in m for m in warns), warns)
        self.assertFalse(any("placebo" in m for m in warns))          # 9 and 9.0 are the same number
        self.assertTrue(any("no consensus file" in m for m in self.msgs("block")))
        self.assertEqual(cli(self.p)[0], 1)

    def test_consensus_rule(self):
        self.w("extraction-reviewer-a.csv", A)
        self.w("extraction-reviewer-b.csv", B)
        cons = HEAD.rstrip("\n") + ",consensus_note\n"
        self.w("extraction.csv", cons + "S01,mortality,30 days,drug,50,6,,,,,\nS01,mortality,30 days,placebo,50,9,,,,,\n"
                                         "S02,mortality,30 days,drug,40,4,,,,,\n")
        self.assertEqual(self.msgs("block"), [])
        self.w("extraction.csv", cons + "S01,mortality,30 days,drug,50,7,,,,,\nS01,mortality,30 days,placebo,50,9,,,,,\n"
                                         "S02,mortality,30 days,drug,40,4,,,,,\n")
        self.assertTrue(any("events = 7 matches neither extractor" in m for m in self.msgs("block")))
        self.w("extraction.csv", cons + "S01,mortality,30 days,drug,50,7,,,,,re-read table 2 with both reviewers\n"
                                         "S01,mortality,30 days,placebo,50,9,,,,,\nS02,mortality,30 days,drug,40,4,,,,,\n")
        self.assertEqual(self.msgs("block"), [])
        self.assertEqual(cli(self.p)[0], 0)

    def test_extractor_files_must_be_the_two_reviewers(self):
        self.w("extraction-reviewer-a.csv", A)
        self.assertTrue(any("two extraction files" in m for m in self.msgs("block")))
        self.w("extraction-claude.csv", B)
        self.assertTrue(any("extraction-claude.csv" in m and "not a reviewer" in m for m in self.msgs("block")))

    def test_rob_rules(self):
        self.w("rob.csv", rob_rows())
        self.assertEqual(self.msgs("block"), [])
        self.w("rob.csv", rob_rows(overall="low"))
        self.assertTrue(any("overall 'low' is better than the worst domain 'some concerns'" in m for m in self.msgs("block")))
        self.w("rob.csv", rob_rows(reviewer="AI draft"))
        self.assertTrue(any("both reviewers" in m for m in self.msgs("block")))
        self.w("rob.csv", rob_rows(d3="3"))
        self.assertTrue(any("never a summed score" in m for m in self.msgs("block")))
        self.w("rob.csv", rob_rows().replace("S01,mortality,RoB 2,D5,low", "S01,mortality,RoB 2,D9,low"))
        blocks = self.msgs("block")
        self.assertTrue(any("D5 missing" in m for m in blocks), blocks)
        self.assertTrue(any("D9" in m for m in blocks), blocks)
        self.w("rob.csv", rob_rows().replace('"quote p. 4"', '""'))
        self.assertTrue(any("no supporting quote" in m for m in self.msgs("warn")))

    def test_robins_i_overall_is_worst_domain(self):
        rows = ROB_HEAD + "".join(f'S02,mortality,ROBINS-I,D{i},{j},"q",Reviewer A; Reviewer B\n'
                                  for i, j in enumerate(["low", "serious", "low", "moderate", "no information", "low", "low"], 1))
        self.w("rob.csv", rows + 'S02,mortality,ROBINS-I,overall,moderate,"q",Reviewer A; Reviewer B\n')
        self.assertTrue(any("better than the worst domain 'serious'" in m for m in self.msgs("block")))
        self.w("rob.csv", rows + 'S02,mortality,ROBINS-I,overall,serious,"q",Reviewer A; Reviewer B\n')
        self.assertEqual(self.msgs("block"), [])

    def test_extraction_csv_without_two_extractor_files_blocks(self):
        self.w("extraction.csv", HEAD.rstrip("\n") + ",consensus_note\nS01,mortality,30 days,drug,50,6,,,,,\n")
        self.assertTrue(any("two extraction-<reviewer>.csv" in m for m in self.msgs("block")), self.msgs())
        self.w("extraction-reviewer-a.csv", A)
        self.assertTrue(any("two extraction files" in m for m in self.msgs("block")))

    def test_study_missing_from_consensus_blocks(self):
        self.w("extraction-reviewer-a.csv", A)
        self.w("extraction-reviewer-b.csv", A)
        cons = HEAD.rstrip("\n") + ",consensus_note\n"
        self.w("extraction.csv", cons + "S01,mortality,30 days,drug,50,5,,,,,\nS01,mortality,30 days,placebo,50,9,,,,,\n")
        blocks = self.msgs("block")
        self.assertTrue(any("S02 / mortality / 30 days / drug" in m and "missing from extraction.csv" in m for m in blocks), blocks)

    def test_robins_i_overall_no_information_allowed(self):
        rows = ROB_HEAD + "".join(f'S02,mortality,ROBINS-I,D{i},{j},"q",Reviewer A; Reviewer B\n'
                                  for i, j in enumerate(["low", "serious", "low", "moderate", "no information", "low", "low"], 1))
        self.w("rob.csv", rows + 'S02,mortality,ROBINS-I,overall,no information,"q",Reviewer A; Reviewer B\n')
        self.assertEqual(self.msgs("block"), [])

    def test_scoping_charting(self):
        shutil.rmtree(self.t / "p")
        self.p = review_project(self.t, design="scoping-review")
        self.d = self.p / "04_data" / "sr"
        self.w("charting.csv", "source_id,concept,extracted_by,verified_by\nS01,x,Reviewer A,Reviewer B\nS02,y,Reviewer A,\n"
                               "S03,z,Reviewer A,Reviewer A\n")
        blocks = self.msgs("block")
        self.assertTrue(any("line 3" in m and "verified_by" in m for m in blocks), blocks)
        self.assertTrue(any("line 4" in m and "the same person" in m for m in blocks), blocks)
        self.w("rob.csv", rob_rows())
        self.assertTrue(any("scoping reviews do not assess risk of bias" in m for m in self.msgs("warn")))

    def test_nothing_to_check_and_usage(self):
        self.assertEqual(extract_check.check(self.p), [])
        self.assertEqual(cli(self.t / "none")[0], 2)


if __name__ == "__main__":
    unittest.main()
