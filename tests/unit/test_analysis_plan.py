import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
from _paths import ORCH_SCRIPTS
import analysis_plan

SCRIPT = ORCH_SCRIPTS / "analysis_plan.py"
SAP = """# SAP
## 15. Changes from the protocol
none
## Analysis register (Bảng đăng ký phân tích)
| ID | Objective | Outcome | Population | Method | Covariates | Multiplicity |
|---|---|---|---|---|---|---|
| A0 | descriptive | baseline | all | Table 1 | none | n/a |
| A1 | primary | readmission | all | logistic | age, sex | none |
| A2 | secondary | LOS | all | linear | age | Holm |
"""


def res(rid, aid, status="prespecified"):
    return {"id": rid, "analysis_id": aid, "status": status}


class TestAnalysisPlan(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.p = Path(self.tmp.name)
        (self.p / "03_protocol").mkdir()
        (self.p / "03_protocol" / "sap.md").write_text(SAP, encoding="utf-8")
        (self.p / "05_analysis" / "output").mkdir(parents=True)
        (self.p / "decisions.md").write_text("# Decisions\n", encoding="utf-8")
        (self.p / "project.yaml").write_text("design: cohort\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def results(self, *rs):
        (self.p / "05_analysis" / "output" / "results.json").write_text(
            json.dumps({"results": list(rs), "tables": []}), encoding="utf-8")

    def test_parse_register(self):
        reg = analysis_plan.parse_register(SAP)
        self.assertEqual([r["id"] for r in reg], ["A0", "A1", "A2"])
        self.assertEqual(reg[1]["covariates"], "age, sex")

    def test_parse_register_errors(self):
        with self.assertRaises(ValueError):
            analysis_plan.parse_register("# SAP\nno table")
        with self.assertRaises(ValueError):
            analysis_plan.parse_register(SAP.replace("| A2 |", "| A1 |"))

    def test_clean(self):
        self.results(res("R-A0-001", "A0"), res("R-A1-001", "A1"), res("R-A2-001", "A2"))
        self.assertEqual(analysis_plan.check(self.p, []), [])

    def test_undeclared_posthoc_and_unknown_prespecified_and_missing(self):
        self.results(res("R-A1-001", "A1"), res("R-A7-001", "A7", "posthoc"), res("R-A9-001", "A9"))
        msgs = " | ".join(m for _, _, m in analysis_plan.check(self.p, []))
        self.assertIn("A7", msgs)
        self.assertIn("POST-HOC A7:", msgs)
        self.assertIn("A9", msgs)
        self.assertIn("A2 is in the register", msgs)

    def test_declared_posthoc_and_deviation_ok(self):
        (self.p / "decisions.md").write_text(
            "- POST-HOC A7: subgroup by sex, requested by Example author, 2026-11-21\n"
            "DEVIATION A2: not done, outcome not collected, 2026-11-21\n", encoding="utf-8")
        self.results(res("R-A0-001", "A0"), res("R-A1-001", "A1"), res("R-A7-001", "A7", "posthoc"))
        self.assertEqual(analysis_plan.check(self.p, []), [])

    def test_text_posthoc_label_and_causal_warning(self):
        (self.p / "decisions.md").write_text("POST-HOC A7: x, requested by Y, 2026-11-21\n", encoding="utf-8")
        self.results(res("R-A0-001", "A0"), res("R-A1-001", "A1"), res("R-A2-001", "A2"),
                     res("R-A7-001", "A7", "posthoc"))
        t = self.p / "ch3.md"
        t.write_text("Nam giới có OR {{R-A7-001}}.\n\nPhân tích thăm dò: {{R-A7-001.full}}.\n\n"
                     "HbA1c cao gây ra tái nhập viện {{R-A1-001}}.\n", encoding="utf-8")
        found = analysis_plan.check(self.p, [t])
        blocks = [loc for sev, loc, _ in found if sev == "block"]
        warns = [loc for sev, loc, _ in found if sev == "warn"]
        self.assertEqual(blocks, [f"{t}:1"])
        self.assertEqual(warns, [f"{t}:5"])

    def _msgs(self, texts=()):
        return " | ".join(f"{sev} {loc} {m}" for sev, loc, m in analysis_plan.check(self.p, list(texts)))

    def base(self):
        self.results(res("R-A0-001", "A0"), res("R-A1-001", "A1"), res("R-A2-001", "A2"))

    def test_malformed_posthoc_and_deviation_lines_block(self):
        (self.p / "decisions.md").write_text(
            "POST-HOC A7: subgroup, requested by X\nDEVIATION A2: not done, no date here\n", encoding="utf-8")
        self.results(res("R-A0-001", "A0"), res("R-A1-001", "A1"))
        out = self._msgs()
        self.assertIn("malformed POST-HOC line", out)
        self.assertIn("malformed DEVIATION line", out)
        self.assertIn("decisions.md:1", out)

    def test_posthoc_on_register_id_blocks(self):
        (self.p / "decisions.md").write_text("POST-HOC A2: late, requested by X, 2026-11-21\n", encoding="utf-8")
        self.base()
        self.assertIn("A2 is prespecified in the register; use DEVIATION", self._msgs())

    def test_deviation_result_needs_label_in_text(self):
        (self.p / "decisions.md").write_text("DEVIATION A2: changed model, 2026-11-21\n", encoding="utf-8")
        self.results(res("R-A0-001", "A0"), res("R-A1-001", "A1"), res("R-A2-001", "A2", "deviation"))
        t = self.p / "d.md"
        t.write_text("LOS {{R-A2-001}}.\n\nThis is a deviation from the SAP: {{R-A2-001}}.\n\nSai lệch: {{R-A2-001}}\n", encoding="utf-8")
        found = analysis_plan.check(self.p, [t])
        self.assertEqual([loc for s, loc, _ in found if s == "block"], [f"{t}:1"])

    def test_derived_comment_ids_count_as_used(self):
        (self.p / "decisions.md").write_text("POST-HOC A7: x, requested by Y, 2026-11-21\n", encoding="utf-8")
        self.results(res("R-A0-001", "A0"), res("R-A1-001", "A1"), res("R-A2-001", "A2"), res("R-A7-001", "A7", "posthoc"))
        t = self.p / "d.md"
        t.write_text("Diff 3.2 <!-- derived: R-A7-001.value - 1, note -->.\n", encoding="utf-8")
        found = analysis_plan.check(self.p, [t])
        self.assertEqual([loc for s, loc, _ in found if s == "block"], [f"{t}:1"])

    def test_all_cause_is_not_causal(self):
        self.base()
        t = self.p / "d.md"
        t.write_text("All-cause mortality was 5%. all-cause deaths.\n\nSmoking causes death.\n", encoding="utf-8")
        warns = [loc for s, loc, _ in analysis_plan.check(self.p, [t]) if s == "warn"]
        self.assertEqual(warns, [f"{t}:3"])

    def test_cli_exit_codes(self):
        self.results(res("R-A1-001", "A1"))
        r = subprocess.run([sys.executable, str(SCRIPT), "check", str(self.p)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("E-STAT block", r.stdout)
        r2 = subprocess.run([sys.executable, str(SCRIPT), "register", str(self.p)], capture_output=True, text=True)
        self.assertEqual(r2.returncode, 0)
        self.assertEqual(json.loads(r2.stdout)[0]["id"], "A0")
        (self.p / "05_analysis" / "output" / "results.json").unlink()
        r3 = subprocess.run([sys.executable, str(SCRIPT), "check", str(self.p)], capture_output=True, text=True)
        self.assertEqual(r3.returncode, 2)


    def test_non_object_results_json_exits_2(self):
        (self.p / "05_analysis" / "output" / "results.json").write_text("[1, 2]", encoding="utf-8")
        r = subprocess.run([sys.executable, str(SCRIPT), "check", str(self.p)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("Traceback", r.stderr)
        (self.p / "05_analysis" / "output" / "results.json").write_text('{"results": 5}', encoding="utf-8")
        r = subprocess.run([sys.executable, str(SCRIPT), "check", str(self.p)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("Traceback", r.stderr)
        (self.p / "05_analysis" / "output" / "results.json").write_text("{not json", encoding="utf-8")
        r = subprocess.run([sys.executable, str(SCRIPT), "check", str(self.p)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("Traceback", r.stderr)

    def test_non_object_record_is_a_block_finding(self):
        self.results(res("R-A0-001", "A0"), res("R-A1-001", "A1"), res("R-A2-001", "A2"), "oops",
                     {"id": "R-A3-001", "analysis_id": ["A3"], "status": "prespecified"})
        found = analysis_plan.check(self.p, [])
        self.assertEqual([s for s, _, _ in found], ["block", "block"])

    def test_utf8_bom_files(self):
        (self.p / "03_protocol" / "sap.md").write_text(SAP, encoding="utf-8-sig")
        self.results(res("R-A0-001", "A0"), res("R-A1-001", "A1"), res("R-A2-001", "A2"))
        self.assertEqual(analysis_plan.check(self.p, []), [])

    def test_numbered_heading(self):
        sap = SAP.replace("## Analysis register (Bảng đăng ký phân tích)", "## 16. Analysis register")
        self.assertEqual(len(analysis_plan.parse_register(sap)), 3)
