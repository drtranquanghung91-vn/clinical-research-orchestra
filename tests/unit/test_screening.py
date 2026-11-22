import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
import screening
from crolib import projectcfg
from p5_helpers import review_project, set_reviewers

RIS = """TY  - JOUR
TI  - Fictional trial of drug X in adults
AU  - Alpha, A
AU  - Beta, B
PY  - 2020
JO  - Fictional Journal
DO  - 10.0000/fictional.1
AB  - Fictional abstract.
ER  - 
TY  - JOUR
TI  - Fictional cohort of drug X
AU  - Gamma, C
PY  - 2021
JO  - Fictional Journal
AB  - Another fictional abstract.
ER  - 
"""
NBIB = """PMID- 99999901
TI  - Fictional trial of drug X in adults.
AU  - Alpha A
DP  - 2020 Mar
JT  - Fictional Journal
LID - 10.0000/fictional.1 [doi]
AB  - Fictional abstract that wraps
      onto a second line.

PMID- 99999902
TI  - Fictional registry study of drug X.
AU  - Delta D
DP  - 2019
JT  - Fictional Journal
"""
CSVX = ("Title,Authors,Year,Journal,DOI\nFictional cohort of drug X,Gamma C,2021,Fictional Journal,\n"
        "Fictional unrelated report,Epsilon E,2022,Fictional Journal,\n")
SEARCH_LOG = ("database,platform,date_run,string_id,hits,export_file\n"
              "Embase,Ovid,2026-11-01,S2,2,embase.ris\nPubMed,PubMed,2026-11-01,S1,2,pubmed.nbib\n")


def cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = screening.main([str(a) for a in argv])
    return code, out.getvalue(), err.getvalue()


class TestProjectcfgLists(unittest.TestCase):
    def test_parse_list_and_get(self):
        self.assertEqual(projectcfg.parse_list("[Reviewer A, 'Reviewer B']"), ["Reviewer A", "Reviewer B"])
        for empty in ("", "[]", "null", "~"):
            self.assertEqual(projectcfg.parse_list(empty), [])
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / "project.yaml").write_text("tools:\n  rscript: null\ntarget:\n  journal_style: bmj\n",
                                                  encoding="utf-8")
            self.assertIsNone(projectcfg.get(Path(t), "tools.rscript"))
            self.assertEqual(projectcfg.get(Path(t), "target.journal_style"), "bmj")
            self.assertEqual(projectcfg.get(Path(t), "missing.key", "x"), "x")


class TestScreening(unittest.TestCase):
    def setUp(self):
        self.t = Path(tempfile.mkdtemp())
        self.p = review_project(self.t)
        ex = self.t / "exports"
        ex.mkdir()
        for name, text in (("embase.ris", RIS), ("pubmed.nbib", NBIB), ("other.csv", CSVX)):
            (ex / name).write_text(text, encoding="utf-8")
        (self.p / screening.SEARCH_LOG).write_text(SEARCH_LOG, encoding="utf-8")
        self.ex = ex

    def tearDown(self):
        shutil.rmtree(self.t, ignore_errors=True)

    def load(self):
        for name, db in (("embase.ris", "Embase"), ("pubmed.nbib", "PubMed"), ("other.csv", "Other")):
            code, out, err = cli(self.p, "import", self.ex / name, "--database", db)
            self.assertEqual(code, 0, out + err)
        self.assertEqual(cli(self.p, "dedupe")[0], 0)

    def decide(self, stage, reviewer, rec, decision, *extra):
        return cli(self.p, "decide", "--stage", stage, "--reviewer", reviewer, "--rec", rec, "--decision", decision, *extra)

    def rows(self):
        return screening.read_csv(self.p / screening.RECORDS)

    def test_import_parses_and_dedupe_marks(self):
        code, out, _ = cli(self.p, "import", self.ex / "embase.ris", "--database", "Embase")
        self.assertEqual(code, 0)
        self.assertIn("2 records imported", out)
        cli(self.p, "import", self.ex / "pubmed.nbib", "--database", "PubMed")
        code, out, _ = cli(self.p, "import", self.ex / "other.csv", "--database", "Other")
        self.assertIn("E-SCR warn 02_evidence/sr/search-log.csv", out)
        self.assertIn("other: 0 hits logged, 2 records imported", out)
        rows = {r["rec_id"]: r for r in self.rows()}
        self.assertEqual(list(rows), [f"rec-000{i}" for i in range(1, 7)])
        self.assertEqual(rows["rec-0003"]["pmid"], "99999901")
        self.assertEqual(rows["rec-0003"]["doi"], "10.0000/fictional.1")
        self.assertEqual(rows["rec-0003"]["abstract"], "Fictional abstract that wraps onto a second line.")
        self.assertEqual(rows["rec-0001"]["authors"], "Alpha, A; Beta, B")
        self.assertEqual(cli(self.p, "dedupe")[0], 0)
        dup = {r["rec_id"]: r["duplicate_of"] for r in self.rows()}
        self.assertEqual(dup, {"rec-0001": "", "rec-0002": "", "rec-0003": "rec-0001", "rec-0004": "",
                               "rec-0005": "rec-0002", "rec-0006": ""})

    def test_decide_refused_while_g2_closed(self):
        shutil.rmtree(self.t / "p")
        self.p = review_project(self.t, g2=False)
        self.load()
        code, out, _ = self.decide("ta", "Reviewer A", "rec-0001", "include")
        self.assertEqual(code, 1)
        self.assertIn("G2: not open", out)
        self.assertFalse((self.p / screening.SCREENING).exists())

    def test_reviewer_rules(self):
        self.load()
        code, out, _ = self.decide("ta", "Someone Else", "rec-0001", "include")
        self.assertEqual(code, 1)
        self.assertIn("not in project.yaml review.reviewers", out)
        set_reviewers(self.p, ["Reviewer A", "Claude"])
        code, out, _ = self.decide("ta", "Claude", "rec-0001", "include")
        self.assertEqual(code, 1)
        self.assertIn("looks like an AI", out)
        msgs = [m for _, _, m in screening.check(self.p)]
        self.assertTrue(any("looks like an AI" in m for m in msgs))
        self.assertTrue(any("1 human reviewer" in m for m in msgs))
        code, out, _ = self.decide("ta", "Reviewer A", "rec-0003", "include")
        self.assertEqual(code, 1)
        self.assertIn("duplicate of rec-0001", out)

    def test_full_flow_conflicts_kappa_counts_and_check(self):
        self.load()
        for rec, a, b in (("rec-0001", "include", "include"), ("rec-0002", "include", "exclude"),
                          ("rec-0004", "exclude", "exclude"), ("rec-0006", "exclude", "exclude")):
            self.assertEqual(self.decide("ta", "Reviewer A", rec, a)[0], 0)
            self.assertEqual(self.decide("ta", "Reviewer B", rec, b)[0], 0)
        code, out, _ = cli(self.p, "conflicts", "--stage", "ta")
        self.assertEqual(code, 1)
        self.assertIn("rec-0002: conflict: Reviewer A include, Reviewer B exclude", out)
        code, out, _ = cli(self.p, "kappa", "--stage", "ta")
        self.assertEqual(code, 0)
        self.assertIn("kappa ta: 0.50 (n = 4; agreement 75.0%)", out)   # po 3/4, pe 0.5x0.25 + 0.5x0.75
        self.assertEqual(self.decide("ta", "consensus", "rec-0002", "include")[0], 0)
        self.assertEqual(cli(self.p, "conflicts", "--stage", "ta")[0], 0)
        code, out, _ = cli(self.p, "counts")
        self.assertEqual(code, 1)
        self.assertIn("not decided by Reviewer A, Reviewer B", out)
        code, out, _ = self.decide("ft", "Reviewer A", "rec-0004", "include")
        self.assertEqual(code, 1)
        self.assertIn("did not pass title/abstract screening", out)
        self.assertEqual(self.decide("ft", "Reviewer A", "rec-0002", "exclude")[0], 1)
        code, out, _ = self.decide("ft", "Reviewer A", "rec-0002", "exclude", "--reason", "wrong colour")
        self.assertEqual(code, 1)
        self.assertIn("not in the protocol's full-text exclusion reasons", out)
        for rv in ("Reviewer A", "Reviewer B"):
            self.assertEqual(self.decide("ft", rv, "rec-0001", "include", "--study", "S01")[0], 0)
            self.assertEqual(self.decide("ft", rv, "rec-0002", "exclude", "--reason", "wrong population")[0], 0)
        code, out, err = cli(self.p, "counts")
        self.assertEqual(code, 0, out + err)
        led = json.loads((self.p / "ledgers" / "results-ledger.json").read_text(encoding="utf-8"))["results"]
        got = {r["id"]: r["value"] for r in led}
        self.assertTrue(all(r["status"] == "observed" and r["kind"] == "n" for r in led))
        expected = {"R-A0-001": 6, "R-A0-002": 0, "R-A0-003": 2, "R-A0-004": 4, "R-A0-005": 2, "R-A0-006": 2,
                    "R-A0-007": 0, "R-A0-008": 2, "R-A0-009": 1, "R-A0-010": 1, "R-A0-011": 1,
                    "R-A0-021": 2, "R-A0-022": 2, "R-A0-023": 2, "R-A0-051": 1}
        self.assertEqual(got, expected)
        labels = {r["id"]: r["label"] for r in led}
        self.assertEqual((labels["R-A0-021"], labels["R-A0-051"]),
                         ("records identified: Embase", "reports excluded: wrong population"))
        found = screening.check(self.p)
        self.assertEqual([f for f in found if f[0] == "block"], [])
        self.assertEqual(self.decide("ft", "consensus", "rec-0002", "include", "--study", "S02")[0], 0)
        found = screening.check(self.p)
        self.assertTrue(any(s == "block" and "differ from a fresh counts run" in m for s, _, m in found), found)

    def test_check_blocks_missing_decisions_and_reasons(self):
        self.load()
        self.decide("ta", "Reviewer A", "rec-0001", "include")
        found = screening.check(self.p)
        self.assertTrue(any(s == "block" and "rec-0001 (ta): not decided by Reviewer B" in m for s, _, m in found), found)
        with open(self.p / screening.SCREENING, "a", encoding="utf-8", newline="") as fh:
            fh.write("ta,rec-0001,Reviewer B,include,,,2026-11-22\n"
                     "ft,rec-0001,consensus,exclude,,,2026-11-22\n")
        found = screening.check(self.p)
        self.assertTrue(any("full-text exclusion without a reason" in m for _, _, m in found), found)

    def test_suggestions_never_become_decisions(self):
        self.load()
        src = self.t / "raw.csv"
        src.write_text("rec_id,suggestion,reason\nrec-0001,include,matches PICO\nrec-0004,exclude,registry only\n",
                       encoding="utf-8")
        code, out, _ = cli(self.p, "suggest", "--stage", "ta", "--from", src)
        self.assertEqual(code, 0)
        self.assertIn("not decisions", out)
        sug = screening.read_csv(self.p / screening.SUGGESTIONS)
        self.assertEqual([(r["rec_id"], r["suggestion"]) for r in sug], [("rec-0001", "include"), ("rec-0004", "exclude")])
        self.assertTrue(all(r["source"].startswith("AI") for r in sug))
        self.assertFalse((self.p / screening.SCREENING).exists())
        code, out, _ = cli(self.p, "sheet", "--stage", "ta", "--reviewer", "Reviewer A")
        self.assertEqual(code, 0)
        sheet = self.p / "reviews" / "tmp" / "screening-ta-reviewer-a.csv"
        rows = screening.read_csv(sheet)
        self.assertEqual(rows[0]["ai_suggestion"], "include")
        self.assertEqual(rows[0]["decision"], "")
        self.assertEqual(cli(self.p, "decide", "--stage", "ta", "--reviewer", "Reviewer A", "--file", sheet)[0], 0)
        self.assertEqual(screening.read_csv(self.p / screening.SCREENING), [])   # blank decisions: nothing recorded
        src.write_text("rec_id,suggestion,reason\nrec-9999,include,x\n", encoding="utf-8")
        self.assertEqual(cli(self.p, "suggest", "--stage", "ta", "--from", src)[0], 1)

    def test_bulk_decide_is_all_or_nothing(self):
        self.load()
        sheet = self.t / "sheet.csv"
        sheet.write_text("rec_id,decision,reason,study\nrec-0001,include,,\nrec-0002,perhaps,,\n", encoding="utf-8")
        self.assertEqual(cli(self.p, "decide", "--stage", "ta", "--reviewer", "Reviewer A", "--file", sheet)[0], 2)
        sheet.write_text("rec_id,decision,reason,study\nrec-0001,include,,\nrec-0099,include,,\n", encoding="utf-8")
        self.assertEqual(cli(self.p, "decide", "--stage", "ta", "--reviewer", "Reviewer A", "--file", sheet)[0], 1)
        self.assertEqual(screening.read_csv(self.p / screening.SCREENING), [])

    def test_usage_errors_exit_2(self):
        bad = self.t / "x.pdf"
        bad.write_text("x", encoding="utf-8")
        self.assertEqual(cli(self.p, "import", bad, "--database", "X")[0], 2)
        self.assertEqual(cli(self.t / "none", "dedupe")[0], 2)
        self.assertEqual(cli(self.p, "dedupe")[0], 2)            # nothing imported yet
        self.load()
        self.assertEqual(cli(self.p, "decide", "--stage", "ta", "--reviewer", "Reviewer A")[0], 2)
        with self.assertRaises(SystemExit):
            cli(self.p, "frobnicate")


if __name__ == "__main__":
    unittest.main()
