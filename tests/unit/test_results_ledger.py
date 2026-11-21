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
