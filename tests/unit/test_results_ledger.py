import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

import _paths  # noqa: F401
from _paths import ORCH_SCRIPTS
import results_ledger

SCRIPT = ORCH_SCRIPTS / "results_ledger.py"


def result(**kw):
    rec = {"id": "R-A1-001", "analysis_id": "A1", "status": "prespecified", "label": "adjusted OR",
           "value": 1.84, "kind": "or", "ci": [1.21, 2.79], "p": 0.004, "n": 1070, "unit": "",
           "table": "T3.2", "source_file": "05_analysis/output/log.txt", "locator": "line 2",
           "raw": "OR 1.84 (95% CI 1.21-2.79), p=0.004"}
    rec.update(kw)
    return rec


class TestResultsLedger(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.p = Path(self.tmp.name)
        (self.p / "ledgers").mkdir()
        (self.p / "05_analysis" / "output").mkdir(parents=True)
        (self.p / "05_analysis" / "output" / "log.txt").write_text(
            "header\nOR 1.84 (95% CI 1.21-2.79), p=0.004\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def doc(self, *results):
        d = {"engine": "test", "data_file": "04_data/c.deid.csv", "data_sha256": "ab", "run_at": "x",
             "results": list(results), "tables": []}
        (self.p / "05_analysis" / "output" / "results.json").write_text(json.dumps(d), encoding="utf-8")
        return d

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)

    def test_valid_import_writes_ledger(self):
        self.doc(result())
        r = self.run_cli("import", str(self.p), "--verify-raw")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        led = json.loads((self.p / "ledgers" / "results-ledger.json").read_text(encoding="utf-8"))
        self.assertEqual(led["results"][0]["id"], "R-A1-001")
        self.assertEqual(led["results"][0]["data_sha256"], "ab")
        self.assertFalse(led["results"][0]["locked"])

    def test_bad_records_exit_1_and_write_nothing(self):
        self.doc(result(status="maybe"), result(id="R-A2-001"), result(id="R-A1-001", kind="weird"))
        r = self.run_cli("import", str(self.p))
        self.assertEqual(r.returncode, 1)
        self.assertIn("status", r.stdout)
        self.assertIn("R-A2-001", r.stdout)
        self.assertIn("duplicate", r.stdout)
        self.assertFalse((self.p / "ledgers" / "results-ledger.json").exists())

    def test_ci_and_p_ranges(self):
        probs = results_ledger.validate_doc(self.doc(result(ci=[3, 2], p=1.5)), self.p)
        self.assertTrue(any("ci" in x for x in probs))
        self.assertTrue(any("p" in x for x in probs))

    def test_source_outside_project_rejected(self):
        probs = results_ledger.validate_doc(self.doc(result(source_file="../x.txt")), self.p)
        self.assertTrue(any("source_file" in x for x in probs))

    def test_verify_raw_line_mismatch(self):
        self.doc(result(locator="line 1"))
        r = self.run_cli("import", str(self.p), "--verify-raw")
        self.assertEqual(r.returncode, 1)
        self.assertIn("raw", r.stdout)

    def test_verify_raw_value_not_in_raw(self):
        self.doc(result(value=1.95))
        r = self.run_cli("import", str(self.p), "--verify-raw")
        self.assertEqual(r.returncode, 1)
        self.assertIn("value", r.stdout)

    def test_xlsx_cell(self):
        x = self.p / "05_analysis" / "output" / "spss.xlsx"
        with zipfile.ZipFile(x, "w") as z:
            z.writestr("xl/workbook.xml", '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                       'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                       '<sheets><sheet name="Out" sheetId="1" r:id="rId1"/></sheets></workbook>')
            z.writestr("xl/_rels/workbook.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                       '<Relationship Id="rId1" Target="worksheets/sheet1.xml" Type="x"/></Relationships>')
            z.writestr("xl/sharedStrings.xml", '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                       '<si><t>Exp(B) 1.840</t></si></sst>')
            z.writestr("xl/worksheets/sheet1.xml", '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                       '<sheetData><row r="7"><c r="B7" t="s"><v>0</v></c></row></sheetData></worksheet>')
        self.assertEqual(results_ledger.read_xlsx_cell(x, "Out!B7"), "Exp(B) 1.840")
        self.doc(result(source_file="05_analysis/output/spss.xlsx", locator="Out!B7", raw="Exp(B) 1.840"))
        r = self.run_cli("import", str(self.p), "--verify-raw")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_missing_results_json_exit_2(self):
        r = self.run_cli("import", str(self.p))
        self.assertEqual(r.returncode, 2)

    def test_rooted_and_absolute_source_rejected(self):
        outside = self.p.parent / (self.p.name + "-abs.txt")
        outside.write_text("x", encoding="utf-8")
        try:
            for src in ("\\Users\\x.txt", "C:\\x.txt", "/etc/x", str(outside)):
                probs = results_ledger.validate_doc(self.doc(result(source_file=src)), self.p)
                self.assertTrue(any("source_file" in x for x in probs), src)
        finally:
            outside.unlink()

    def test_sibling_folder_with_same_prefix_rejected(self):
        sib = self.p.parent / (self.p.name + "2")
        sib.mkdir()
        (sib / "x.txt").write_text("x", encoding="utf-8")
        try:
            probs = results_ledger.validate_doc(
                self.doc(result(source_file=f"../{sib.name}/x.txt")), self.p)
            self.assertTrue(any("source_file" in x for x in probs))
        finally:
            (sib / "x.txt").unlink()
            sib.rmdir()

    def test_wrong_types_give_problems_not_crashes(self):
        d = self.doc(result())
        d["results"] = ["oops", result(analysis_id=1), result(id=5, status=["a"], kind={})]
        probs = results_ledger.validate_doc(d, self.p)
        self.assertGreaterEqual(len(probs), 3)
        self.assertEqual(results_ledger.validate_doc([1, 2], self.p)[0].split(":")[0], "document")
        self.assertTrue(results_ledger.validate_doc("x", self.p))

    def test_top_level_list_cli_exit_1(self):
        (self.p / "05_analysis" / "output" / "results.json").write_text("[1]", encoding="utf-8")
        r = self.run_cli("import", str(self.p))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_invalid_json_exit_2(self):
        (self.p / "05_analysis" / "output" / "results.json").write_text("{", encoding="utf-8")
        r = self.run_cli("import", str(self.p))
        self.assertEqual(r.returncode, 2)

    def test_missing_sheet_is_a_problem(self):
        x = self.p / "05_analysis" / "output" / "s.xlsx"
        with zipfile.ZipFile(x, "w") as z:
            z.writestr("xl/workbook.xml", '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                       'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                       '<sheets><sheet name="Out" sheetId="1" r:id="rId1"/></sheets></workbook>')
        d = self.doc(result(source_file="05_analysis/output/s.xlsx", locator="Nope!B7", raw="x"))
        probs = results_ledger.validate_doc(d, self.p, verify_raw=True)
        self.assertTrue(any("cannot be located" in x and "Nope" in x for x in probs), probs)

    def test_bad_xml_is_a_problem(self):
        x = self.p / "05_analysis" / "output" / "s.xlsx"
        with zipfile.ZipFile(x, "w") as z:
            z.writestr("xl/workbook.xml", "<not xml")
        d = self.doc(result(source_file="05_analysis/output/s.xlsx", locator="Out!B7", raw="x"))
        probs = results_ledger.validate_doc(d, self.p, verify_raw=True)
        self.assertTrue(any("cannot be located" in x for x in probs), probs)

    def test_data_file_must_be_under_04_data(self):
        d = self.doc(result())
        d["data_file"] = "00_inputs/raw.deid.csv"
        probs = results_ledger.validate_doc(d, self.p)
        self.assertTrue(any("data_file" in x for x in probs))
