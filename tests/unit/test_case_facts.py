import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
import analysis_plan
import case_facts
import gate
import init_project
import results_ledger
from crolib import numfmt, resultlog

FACTS = ("id,label,value,unit,day,source\n"
         "C01,haemoglobin at admission,78,g/L,0,lab report\n"
         "C02,C-reactive protein,12.5,mg/L,0,lab report\n"
         "C03,oxygen saturation,91,%,0,nursing chart\n"
         "C04,days in hospital,9,,+9,discharge summary\n"
         "C05,creatinine,1.07,mg/dL,-14,outpatient record\n")
REGISTER = ("# Protocol (fictional)\n\n## Analysis register\n\n| ID | Type | Outcome |\n|---|---|---|\n"
            "| A0 | counts | PRISMA flow |\n| A1 | pool | mortality |\n")


def quiet(fn, *args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = fn(*args)
    return code, out.getvalue(), err.getvalue()


def rec(rid, aid, status, src, label="x", kind="n"):
    return {"id": rid, "analysis_id": aid, "status": status, "label": label, "value": 1, "kind": kind,
            "source_file": src, "locator": "line 1", "raw": f"{rid} {label}: value=1"}


class TestCaseFacts(unittest.TestCase):
    def setUp(self):
        self.t = Path(tempfile.mkdtemp())
        self.p = init_project.create(self.t / "p", "T", "case-report", "case-report", "en", "vi")
        (self.p / "01_case").mkdir(exist_ok=True)
        (self.p / "01_case" / "facts.csv").write_text(FACTS, encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.t, ignore_errors=True)

    def ledger(self):
        return json.loads((self.p / "ledgers" / "results-ledger.json").read_text(encoding="utf-8"))["results"]

    def test_kind_for(self):
        self.assertEqual(case_facts.kind_for("%", "91"), ("percent", 0))
        self.assertEqual(case_facts.kind_for("", "9"), ("n", None))
        self.assertEqual(case_facts.kind_for("lần", "2"), ("n", None))
        self.assertEqual(case_facts.kind_for("", "2.5"), ("measure", 1))
        self.assertEqual(case_facts.kind_for("g/L", "78"), ("measure", 0))
        self.assertEqual(case_facts.kind_for("mg/dL", "1,07"), ("measure", 2))

    def test_facts_become_observed_a0_records(self):
        code, out, err = quiet(case_facts.main, [str(self.p)])
        self.assertEqual(code, 0, out + err)
        recs = self.ledger()
        self.assertEqual([r["id"] for r in recs], [f"R-A0-00{i}" for i in range(1, 6)])
        self.assertTrue(all(r["analysis_id"] == "A0" and r["status"] == "observed" for r in recs))
        by = {r["id"]: r for r in recs}
        self.assertEqual((by["R-A0-001"]["kind"], by["R-A0-001"]["decimals"], by["R-A0-001"]["unit"]), ("measure", 0, "g/L"))
        self.assertEqual((by["R-A0-002"]["kind"], by["R-A0-002"]["decimals"]), ("measure", 1))
        self.assertEqual(by["R-A0-003"]["kind"], "percent")
        self.assertEqual(by["R-A0-004"]["kind"], "n")
        self.assertEqual((by["R-A0-004"]["day"], by["R-A0-005"]["day"]), (9, -14))
        self.assertIn("[C01]", by["R-A0-001"]["label"])
        self.assertEqual(numfmt.render(by["R-A0-001"], "value", "en"), "78")
        self.assertEqual(numfmt.render(by["R-A0-002"], "value", "vi"), "12,5")
        self.assertEqual(numfmt.render(by["R-A0-005"], "value", "en"), "1.07")
        self.assertEqual(numfmt.render(by["R-A0-003"], "value", "en"), "91%")
        self.assertIn("C01 → R-A0-001", out)
        doc = json.loads((self.p / case_facts.DOC_REL).read_text(encoding="utf-8"))
        self.assertEqual(doc["data_file"], "01_case/facts.csv")
        self.assertEqual(results_ledger.validate_doc(doc, self.p, verify_raw=True), [])
        self.assertNotIn(b"\r\n", (self.p / case_facts.LOG_REL).read_bytes())

    def test_rerun_is_byte_stable_and_g3_lock_refuses_changes(self):
        self.assertEqual(quiet(case_facts.main, [str(self.p)])[0], 0)
        led = self.p / "ledgers" / "results-ledger.json"
        before = led.read_bytes()
        self.assertEqual(quiet(case_facts.main, [str(self.p)])[0], 0)
        self.assertEqual(led.read_bytes(), before)
        gate.open_gate(self.p, "G3", by="A", files=["ledgers/results-ledger.json", "01_case/facts.csv"])
        (self.p / "01_case" / "facts.csv").write_text(FACTS.replace(",78,", ",79,"), encoding="utf-8")
        code, out, err = quiet(case_facts.main, [str(self.p)])
        self.assertEqual(code, 1)
        self.assertIn("G3 is locked", err)
        self.assertEqual(led.read_bytes(), before)

    def test_relabel_needs_flag(self):
        self.assertEqual(quiet(case_facts.main, [str(self.p)])[0], 0)
        (self.p / "01_case" / "facts.csv").write_text(FACTS.replace("haemoglobin at admission", "Hb"), encoding="utf-8")
        self.assertEqual(quiet(case_facts.main, [str(self.p)])[0], 1)
        self.assertEqual(quiet(case_facts.main, [str(self.p), "--accept-relabel"])[0], 0)
        self.assertIn("Hb [C01]", self.ledger()[0]["label"])

    def test_invalid_rows_are_listed_and_nothing_written(self):
        bad = FACTS + "C01,duplicate id,1,,0,x\nC07,calendar day,5,,12/03/2025,x\nC08,,3,,0,x\nC09,text value,high,,0,x\n"
        (self.p / "01_case" / "facts.csv").write_text(bad, encoding="utf-8")
        code, out, err = quiet(case_facts.main, [str(self.p)])
        self.assertEqual(code, 1)
        for s in ("C01: duplicate id", "C07: day", "C08: label", "C09: value"):
            self.assertIn(s, out)
        self.assertNotIn("R-A0", (self.p / "ledgers" / "results-ledger.json").read_text(encoding="utf-8"))

    def test_usage_errors_exit_2(self):
        (self.p / "01_case" / "facts.csv").write_text("id,label\nC01,x\n", encoding="utf-8")
        self.assertEqual(quiet(case_facts.main, [str(self.p)])[0], 2)
        (self.p / "01_case" / "facts.csv").unlink()
        self.assertEqual(quiet(case_facts.main, [str(self.p)])[0], 2)
        self.assertEqual(quiet(case_facts.main, [str(self.t / "nope")])[0], 2)


class TestLedgerP5(unittest.TestCase):
    def setUp(self):
        self.t = Path(tempfile.mkdtemp())
        self.p = init_project.create(self.t / "p", "T", "systematic-review", "systematic-review", "en", "vi")
        out = self.p / "05_analysis" / "output"
        out.mkdir(parents=True, exist_ok=True)
        for name in ("a-log.txt", "b-log.txt"):
            (out / name).write_text("x\n", encoding="utf-8")
        (self.p / "01_case").mkdir(exist_ok=True)
        (self.p / "01_case" / "facts.csv").write_text(FACTS, encoding="utf-8")
        self.A, self.B = "05_analysis/output/a-log.txt", "05_analysis/output/b-log.txt"

    def tearDown(self):
        shutil.rmtree(self.t, ignore_errors=True)

    def doc(self, results, data_file="01_case/facts.csv"):
        return {"engine": "t", "data_file": data_file, "data_sha256": "", "run_at": "t", "results": results, "tables": []}

    def put(self, name, results):
        path = self.p / "05_analysis" / "output" / name
        path.write_text(json.dumps(self.doc(results)), encoding="utf-8")
        return path

    def ids(self):
        return [r["id"] for r in json.loads((self.p / "ledgers" / "results-ledger.json").read_text(encoding="utf-8"))["results"]]

    def test_observed_only_for_a0(self):
        probs = results_ledger.validate_doc(self.doc([rec("R-A1-001", "A1", "observed", self.A)]), self.p)
        self.assertTrue(any("only for A0" in x for x in probs), probs)
        self.assertEqual(results_ledger.validate_doc(self.doc([rec("R-A0-001", "A0", "observed", self.A)]), self.p), [])

    def test_new_kinds_and_decimals(self):
        for kind in ("absolute", "smd", "tau2", "measure"):
            self.assertIn(kind, numfmt.KINDS)
            self.assertEqual(results_ledger.validate_doc(self.doc([rec("R-A1-001", "A1", "prespecified", self.A, kind=kind)]), self.p), [])
        bad = dict(rec("R-A0-001", "A0", "observed", self.A), decimals=7)
        self.assertTrue(any("decimals" in x for x in results_ledger.validate_doc(self.doc([bad]), self.p)))
        self.assertEqual(numfmt.render({"value": 12.0, "kind": "absolute"}, "value", "en"), "12")
        self.assertEqual(numfmt.render({"value": 0.04321, "kind": "tau2"}, "value", "en"), "0.043")

    def test_p5_data_files_allowed(self):
        for f in results_ledger.DATA_FILES:
            probs = results_ledger.validate_doc(self.doc([], data_file=f), self.p)
            self.assertFalse([x for x in probs if "data_file" in x], f)
        probs = results_ledger.validate_doc(self.doc([], data_file="01_case/other.csv"), self.p)
        self.assertTrue(any("data_file" in x for x in probs))

    def test_merge_keeps_other_sources_and_refuses_clashes(self):
        a = self.put("a.json", [rec("R-A0-001", "A0", "observed", self.A)])
        b = self.put("b.json", [rec("R-A1-001", "A1", "prespecified", self.B)])
        self.assertEqual(results_ledger.import_results(self.p, b, merge=True), (1, []))
        self.assertEqual(results_ledger.import_results(self.p, a, merge=True), (1, []))
        self.assertEqual(self.ids(), ["R-A0-001", "R-A1-001"])
        a2 = self.put("a.json", [rec("R-A0-001", "A0", "observed", self.A), rec("R-A0-002", "A0", "observed", self.A)])
        self.assertEqual(results_ledger.import_results(self.p, a2, merge=True), (2, []))
        self.assertEqual(self.ids(), ["R-A0-001", "R-A0-002", "R-A1-001"])
        clash = self.put("c.json", [rec("R-A1-001", "A1", "prespecified", self.A)])
        n, probs = results_ledger.import_results(self.p, clash, merge=True)
        self.assertEqual(n, 0)
        self.assertTrue(any("R-A1-001" in x and "another source" in x for x in probs))
        self.assertEqual(results_ledger.import_results(self.p, b, accept_relabel=True), (1, []))  # P2 mode replaces all
        self.assertEqual(self.ids(), ["R-A1-001"])

    def test_merge_cli_flag(self):
        b = self.put("b.json", [rec("R-A1-001", "A1", "prespecified", self.B)])
        code, out, err = quiet(results_ledger.main, ["import", str(self.p), "--from", str(b), "--merge"])
        self.assertEqual(code, 0, err)

    def test_resultlog_writes_p2_lines(self):
        log = resultlog.ResultLog(self.p, "01_case/facts.csv", "05_analysis/output/t-log.txt", "test")
        rid = log.add("A1", "prespecified", "pooled RR", 0.7512345678912, "rr", ci=[0.5, 1.1], p=0.04, n=120, count=3)
        self.assertEqual(rid, "R-A1-001")
        self.assertEqual(log.add("A1", "prespecified", "absolute", 12, "absolute", number=901), "R-A1-901")
        with self.assertRaises(ValueError):
            log.add("A1", "prespecified", "again", 1, "absolute", number=901)
        with self.assertRaises(ValueError):
            log.add("A1", "observed", "x", 1, "n")
        path = log.save("05_analysis/output/t.json")
        lines = (self.p / "05_analysis" / "output" / "t-log.txt").read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[0], "R-A1-001 pooled RR: value=0.7512345679 ci=0.5,1.1 p=0.04 n=120 count=3")
        doc = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(results_ledger.validate_doc(doc, self.p, verify_raw=True), [])
        self.assertEqual(resultlog.num_str(3), "3")
        self.assertEqual(resultlog.num_str(-0.0), "0")


class TestAnalysisPlanP5(unittest.TestCase):
    def setUp(self):
        self.t = Path(tempfile.mkdtemp())
        self.p = self.t / "p"
        (self.p / "03_protocol").mkdir(parents=True)
        (self.p / "ledgers").mkdir()
        (self.p / "03_protocol" / "sr-protocol.md").write_text(REGISTER, encoding="utf-8")
        (self.p / "project.yaml").write_text("design: systematic-review\n", encoding="utf-8")
        self.recs = [rec("R-A0-001", "A0", "observed", "x"), rec("R-A1-001", "A1", "prespecified", "y")]

    def tearDown(self):
        shutil.rmtree(self.t, ignore_errors=True)

    def write(self):
        (self.p / "ledgers" / "results-ledger.json").write_text(json.dumps({"results": self.recs}), encoding="utf-8")

    def test_register_falls_back_to_sr_protocol(self):
        self.assertEqual(analysis_plan.register_path(self.p).name, "sr-protocol.md")
        code, out, _ = quiet(analysis_plan.main, ["register", str(self.p)])
        self.assertEqual(code, 0)
        self.assertEqual([r["id"] for r in json.loads(out)], ["A0", "A1"])

    def test_observed_records_are_skipped_and_ledger_is_read(self):
        self.write()
        self.assertEqual(analysis_plan.check(self.p, []), [])

    def test_observed_outside_a0_blocks(self):
        self.recs.append(rec("R-A1-002", "A1", "observed", "y"))
        self.write()
        found = analysis_plan.check(self.p, [])
        self.assertTrue(any(s == "block" and "observed" in m for s, _, m in found), found)

    def test_missing_result_blocks_at_the_register_file(self):
        self.recs = self.recs[:1]
        self.write()
        found = analysis_plan.check(self.p, [])
        self.assertIn(("block", "03_protocol/sr-protocol.md"), [(s, loc) for s, loc, _ in found])


if __name__ == "__main__":
    unittest.main()
