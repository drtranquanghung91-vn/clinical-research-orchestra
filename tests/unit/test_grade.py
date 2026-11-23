import contextlib
import io
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
import gate
import grade
from p5_helpers import review_project

LOG = "05_analysis/output/meta-log.txt"


def rec(rid, kind, value, ci, status="prespecified"):
    return {"id": rid, "analysis_id": rid.split("-")[1], "status": status, "label": f"pooled {kind}", "value": value,
            "ci": ci, "count": 3, "n": 300, "kind": kind, "source_file": LOG, "locator": "line 1", "raw": "x"}


def outcome(result="R-A1-001", design="rct", rob="RoB 2", down=(0, -1, 0, -1, 0), up=(0, 0, 0), cr=0.2):
    keys = ("risk_of_bias", "inconsistency", "indirectness", "imprecision", "publication_bias")
    o = {"outcome": "Mortality at 30 days", "result": result, "design": design, "rob_tool": rob,
         "downgrades": {k: [v, "fictional reason" if v else ""] for k, v in zip(keys, down)},
         "upgrades": {k: [v, "fictional reason" if v else ""] for k, v in zip(("large_effect", "dose_response",
                                                                             "plausible_confounding"), up)},
         "comparator_source": "median control-group risk of the included studies (fictional)"}
    if cr is not None:
        o["comparator_risk"] = cr
    return o


def cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = grade.main([str(a) for a in argv])
    return code, out.getvalue(), err.getvalue()


class TestGrade(unittest.TestCase):
    def setUp(self):
        self.t = Path(tempfile.mkdtemp())
        self.p = review_project(self.t)
        (self.p / LOG).parent.mkdir(parents=True, exist_ok=True)
        (self.p / LOG).write_text("x\n", encoding="utf-8")
        self.led = [rec("R-A1-001", "rr", 0.75, [0.5, 1.1]), rec("R-A2-001", "or", 2.0, [1.5, 3.0]),
                    rec("R-A3-001", "md", -0.8, [-1.2, -0.4])]
        self.write_ledger()

    def tearDown(self):
        shutil.rmtree(self.t, ignore_errors=True)

    def write_ledger(self):
        (self.p / "ledgers" / "results-ledger.json").write_text(json.dumps({"results": self.led}), encoding="utf-8")

    def write_grade(self, *outcomes):
        path = self.p / grade.GRADE_JSON
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"outcomes": list(outcomes)}), encoding="utf-8")

    def ledger(self):
        return {r["id"]: r for r in json.loads((self.p / "ledgers" / "results-ledger.json").read_text(encoding="utf-8"))["results"]}

    def test_certainty_levels(self):
        self.assertEqual(grade.certainty(outcome(down=(0, 0, 0, 0, 0))), "high")
        self.assertEqual(grade.certainty(outcome(down=(0, -1, 0, 0, 0))), "moderate")
        self.assertEqual(grade.certainty(outcome()), "low")
        self.assertEqual(grade.certainty(outcome(down=(-2, -1, 0, -1, 0))), "very low")
        self.assertEqual(grade.certainty(outcome(design="nrsi", rob="NOS", down=(0, 0, 0, 0, 0))), "low")
        self.assertEqual(grade.certainty(outcome(design="nrsi", rob="ROBINS-I", down=(0, 0, 0, 0, 0))), "high")
        self.assertEqual(grade.certainty(outcome(design="nrsi", rob="NOS", down=(0, 0, 0, 0, 0), up=(1, 0, 0))), "moderate")

    def test_absolute_conversions(self):
        self.assertAlmostEqual(grade.absolute("rr", 0.75, 0.2), 0.15, places=12)
        self.assertAlmostEqual(grade.absolute("or", 2.0, 0.2), 2.0 * 0.2 / (1 - 0.2 + 2.0 * 0.2), places=12)
        self.assertAlmostEqual(grade.absolute("hr", 0.5, 0.2), 1 - 0.8 ** 0.5, places=12)
        self.assertAlmostEqual(grade.absolute("rd", -0.05, 0.2), 0.15, places=12)

    def test_run_writes_absolute_records_and_sof(self):
        (self.p / "06_writing" / "review" / "04-results.md").write_text("# Results\n\nTable 1. Included studies\n| a |\n|---|\n| b |\n", encoding="utf-8")
        self.write_grade(outcome(), outcome(result="R-A2-001", down=(0, 0, 0, 0, 0)), outcome(result="R-A3-001", cr=None))
        code, out, err = cli(self.p, "run")
        self.assertEqual(code, 0, out + err)
        led = self.ledger()
        self.assertAlmostEqual(led["R-A1-901"]["value"], 200, places=9)
        self.assertAlmostEqual(led["R-A1-902"]["value"], 0.75 * 0.2 * 1000, places=9)
        self.assertAlmostEqual(led["R-A1-902"]["ci"][0], 0.5 * 0.2 * 1000, places=9)
        self.assertAlmostEqual(led["R-A1-903"]["value"], (0.75 - 1) * 0.2 * 1000, places=9)
        self.assertAlmostEqual(led["R-A1-903"]["ci"][1], (1.1 - 1) * 0.2 * 1000, places=9)
        self.assertEqual({led[i]["kind"] for i in ("R-A1-901", "R-A1-902", "R-A1-903")}, {"absolute"})
        self.assertEqual(led["R-A1-902"]["status"], "prespecified")
        self.assertAlmostEqual(led["R-A2-902"]["value"], 1000 * 2.0 * 0.2 / (1 - 0.2 + 2.0 * 0.2), places=9)
        self.assertNotIn("R-A3-901", led)
        sof = (self.p / grade.SOF).read_text(encoding="utf-8")
        self.assertIn("Table 2. Summary of findings", sof)
        self.assertIn("{{R-A1-001.full}}", sof)
        self.assertIn("{{R-A1-903.full}}", sof)
        self.assertIn("⊕⊕◯◯ Low", sof)
        self.assertIn("⊕⊕⊕⊕ High", sof)
        self.assertIn("median control-group risk", sof)
        self.assertIn("inconsistency: down one level (fictional reason)", sof)
        self.assertFalse([ln for ln in sof.splitlines() if ln.startswith("- ") and re.search(r"\d", ln)])  # footnotes: words, not digits (E-NUM)
        self.assertIn("not-a-result", sof)
        self.assertIn("low certainty", out.lower())

    def test_vietnamese_sof(self):
        y = (self.p / "project.yaml").read_text(encoding="utf-8").replace("output: en", "output: vi")
        (self.p / "project.yaml").write_text(y, encoding="utf-8")
        self.write_grade(outcome())
        self.assertEqual(cli(self.p, "run")[0], 0)
        sof = (self.p / grade.SOF).read_text(encoding="utf-8")
        self.assertIn("Bảng 1. Tóm tắt kết quả", sof)
        self.assertIn("⊕⊕◯◯ Thấp", sof)

    def test_invalid_grade_json_exit_2(self):
        bad = outcome()
        bad["downgrades"]["inconsistency"] = [-1, ""]
        self.write_grade(bad)
        code, out, err = cli(self.p, "run")
        self.assertEqual(code, 2)
        self.assertIn("inconsistency: a downgrade needs a reason", err)
        self.write_grade(outcome(up=(1, 0, 0)))
        self.assertIn("upgrades are for non-randomised", cli(self.p, "run")[2])
        self.write_grade(outcome(result="R-A9-001"))
        self.assertIn("R-A9-001 is not in the results ledger", cli(self.p, "run")[2])
        self.write_grade(outcome(cr=1.5))
        self.assertIn("comparator_risk", cli(self.p, "run")[2])

    def test_g3_lock_refuses(self):
        self.write_grade(outcome())
        gate.open_gate(self.p, "G3", by="A", files=["ledgers/results-ledger.json"])
        code, out, err = cli(self.p, "run")
        self.assertEqual(code, 1)
        self.assertIn("G3 is locked", err)

    def test_wording_check(self):
        self.write_grade(outcome(), outcome(result="R-A2-001", down=(-2, -1, 0, -1, 0)))
        self.assertEqual(grade.certainty_by_result(self.p)["R-A1-001"], "low")
        self.assertEqual(grade.certainty_by_result(self.p)["R-A1-903"], "low")
        d = self.p / "06_writing" / "review"
        (d / "04-results.md").write_text(
            "# Results\n\nDrug X reduces mortality ({{R-A1-001.full}}).\n\n"
            "Drug X may reduce mortality ({{R-A1-001.full}}).\n\n"
            "Drug Y may increase harm ({{R-A2-001.full}}).\n\n"
            "We are very uncertain whether drug Y increases harm ({{R-A2-001.full}}).\n\n"
            "| Outcome | Effect |\n|---|---|\n| Mortality | {{R-A1-001.full}} |\n", encoding="utf-8")
        found = grade.check_wording(self.p, [d / "04-results.md"])
        locs = sorted(loc for _, loc, _ in found)
        self.assertEqual(locs, ["06_writing/review/04-results.md:3", "06_writing/review/04-results.md:7"])
        self.assertTrue(all(s == "warn" for s, _, _ in found))
        code, out, _ = cli(self.p, "check", "--text", d / "04-results.md")
        self.assertEqual(code, 0)
        self.assertIn("E-GRADE warn 06_writing/review/04-results.md:3", out)

    def test_month_may_is_not_a_hedge(self):
        self.write_grade(outcome())
        d = self.p / "06_writing" / "review"
        (d / "04-results.md").write_text(
            "# Results\n\nIn the trial published in May 2024 drug X reduces mortality ({{R-A1-001.full}}).\n\n"
            "May reduce mortality, the trial suggests ({{R-A1-001.full}}).\n", encoding="utf-8")
        locs = [loc for _, loc, _ in grade.check_wording(self.p, [d / "04-results.md"])]
        self.assertEqual(locs, ["06_writing/review/04-results.md:3"])

    def test_hedge_words_match_across_unicode_forms(self):
        import unicodedata
        word = "có thể"
        for form in ("NFC", "NFD"):
            self.assertTrue(grade._hedged(unicodedata.normalize(form, "thuốc có thể giảm tử vong"),
                                          [unicodedata.normalize("NFD" if form == "NFC" else "NFC", word)], "vi"))

    def test_wording_lists(self):
        for lang in ("vi", "en"):
            w = grade.load_wording(lang)
            self.assertTrue(w["low"] and w["very low"])
        self.assertIn("có thể", grade.load_wording("vi")["low"])
        self.assertIn("chưa chắc chắn", grade.load_wording("vi")["very low"])
        self.assertIn("may", grade.load_wording("en")["low"])
        self.assertIn("very uncertain", grade.load_wording("en")["very low"])

    def test_outcome_names_with_digits_carry_the_marker(self):
        import check_numbers
        self.assertEqual(grade.outcome_cell("Mortality at 30 days"),
                         "Mortality at 30 <!-- not-a-result: outcome name --> days")
        self.assertEqual(grade.outcome_cell("Pain"), "Pain")
        (self.p / "06_writing" / "review" / "04-results.md").write_text(
            "# Results\n\nTable 1. Included studies\n| a |\n|---|\n| b |\n", encoding="utf-8")
        self.write_grade(outcome())
        self.assertEqual(cli(self.p, "run")[0], 0)
        sof = (self.p / grade.SOF).read_text(encoding="utf-8")
        self.assertIn("Mortality at 30 <!-- not-a-result: outcome name --> days", sof)
        found = [tok for _, tok in check_numbers.find_unmatched(sof, list(self.ledger().values()), "en")]
        self.assertNotIn("30", found)


if __name__ == "__main__":
    unittest.main()
