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
        self.doc(result(source_file="05_analysis/output/spss.xlsx", locator="Out!B7", raw="Exp(B) 1.840",
                        ci=None, p=None))
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

    def _log(self, text):
        (self.p / "05_analysis" / "output" / "log.txt").write_text("header\n" + text + "\n", encoding="utf-8")

    def test_verify_raw_invented_ci_fails(self):
        d = self.doc(result(ci=[1.5, 2.79]))
        probs = results_ledger.validate_doc(d, self.p, verify_raw=True)
        self.assertTrue(any("ci lo 1.5" in x for x in probs), probs)
        self.assertFalse(any("ci hi" in x for x in probs), probs)

    def test_verify_raw_invented_p_fails(self):
        probs = results_ledger.validate_doc(self.doc(result(p=0.04)), self.p, verify_raw=True)
        self.assertTrue(any("p 0.04" in x for x in probs), probs)

    def test_verify_raw_spss_leading_dot_p(self):
        self._log("Exp(B) 1.840 95% CI 1.210 2.790 Sig. .032")
        rec = result(p=0.032, raw="Exp(B) 1.840 95% CI 1.210 2.790 Sig. .032")
        self.assertEqual(results_ledger.validate_doc(self.doc(rec), self.p, verify_raw=True), [])
        rec = result(p=0.023, raw="Exp(B) 1.840 95% CI 1.210 2.790 Sig. .032")
        self.assertTrue(any("p 0.023" in x for x in results_ledger.validate_doc(self.doc(rec), self.p, verify_raw=True)))

    def test_verify_raw_kind_p_value_needs_decimals(self):
        raw = "Pearson Chi-Square 4.612 1 .032"
        self._log(raw)
        bad = result(kind="p", value=0.77, ci=None, p=None, raw=raw)
        self.assertTrue(any("value 0.77" in x for x in results_ledger.validate_doc(self.doc(bad), self.p, verify_raw=True)))
        ok = result(kind="p", value=0.032, ci=None, p=None, raw=raw)
        self.assertEqual(results_ledger.validate_doc(self.doc(ok), self.p, verify_raw=True), [])

    def test_verify_raw_spss_tiny_p(self):
        self._log("OR 1.84 (95% CI 1.21-2.79) Sig. <.001")
        rec = result(p=0.0004, raw="OR 1.84 (95% CI 1.21-2.79) Sig. <.001")
        self.assertEqual(results_ledger.validate_doc(self.doc(rec), self.p, verify_raw=True), [])

    def test_verify_raw_comma_joined_ci(self):
        self._log("R-A1-001 OR: value=1.84 ci=1.2134,2.7861 p=0.004")
        rec = result(ci=[1.2134, 2.7861], raw="R-A1-001 OR: value=1.84 ci=1.2134,2.7861 p=0.004")
        self.assertEqual(results_ledger.validate_doc(self.doc(rec), self.p, verify_raw=True), [])
        self._log("R-A1-001 OR: value=1.84 ci=-2.5,-2.1018 p=0.004")
        rec = result(kind="beta", value=1.84, ci=[-2.5, -2.1018], raw="R-A1-001 OR: value=1.84 ci=-2.5,-2.1018 p=0.004")
        self.assertEqual(results_ledger.validate_doc(self.doc(rec), self.p, verify_raw=True), [])

    def test_verify_raw_negative_ci(self):
        self._log("MD -0.30 (95% CI -0.55 to -0.05)")
        rec = result(kind="md", value=-0.3, ci=[-0.55, -0.05], p=None,
                     raw="MD -0.30 (95% CI -0.55 to -0.05)")
        self.assertEqual(results_ledger.validate_doc(self.doc(rec), self.p, verify_raw=True), [])

    def test_count_must_be_non_negative_int(self):
        for bad in (-1, 2.5, True, "3"):
            probs = results_ledger.validate_doc(self.doc(result(count=bad)), self.p)
            self.assertTrue(any("count" in x for x in probs), bad)
        self.assertEqual(results_ledger.validate_doc(self.doc(result(count=0)), self.p), [])
        self.assertEqual(results_ledger.validate_doc(self.doc(result(count=134)), self.p), [])

    def test_relabel_blocked_unless_accepted(self):
        self.doc(result())
        self.assertEqual(self.run_cli("import", str(self.p)).returncode, 0)
        led = self.p / "ledgers" / "results-ledger.json"
        before = led.read_text(encoding="utf-8")
        self.doc(result(label="crude OR", kind="rr"), result(id="R-A1-002"))
        r = self.run_cli("import", str(self.p))
        self.assertEqual(r.returncode, 1)
        self.assertIn("R-A1-001", r.stderr)
        self.assertIn("label", r.stderr)
        self.assertIn("kind", r.stderr)
        self.assertEqual(led.read_text(encoding="utf-8"), before)
        r = self.run_cli("import", str(self.p), "--accept-relabel")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len(json.loads(led.read_text(encoding="utf-8"))["results"]), 2)

    def test_removed_id_blocked_new_id_fine(self):
        self.doc(result())
        self.run_cli("import", str(self.p))
        self.doc(result(id="R-A1-002"))
        r = self.run_cli("import", str(self.p))
        self.assertEqual(r.returncode, 1)
        self.assertIn("R-A1-001: removed", r.stderr)
        self.doc(result(), result(id="R-A1-002"))
        self.assertEqual(self.run_cli("import", str(self.p)).returncode, 0)

    def test_writes_lf_only(self):
        self.doc(result())
        self.assertEqual(self.run_cli("import", str(self.p)).returncode, 0)
        raw = (self.p / "ledgers" / "results-ledger.json").read_bytes()
        self.assertNotIn(b"\r", raw)

    def lock_g3(self):
        import gate
        gate.open_gate(self.p, "G3", by="A", files=["ledgers/results-ledger.json"])

    def test_g3_locked_refuses_changed_ledger(self):
        self.doc(result())
        self.run_cli("import", str(self.p))
        self.lock_g3()
        led = self.p / "ledgers" / "results-ledger.json"
        before = led.read_bytes()
        self.doc(result(value=1.9), result(id="R-A1-002"))
        r = self.run_cli("import", str(self.p), "--accept-relabel")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("G3 is locked; the ledger is unchanged", r.stderr)
        self.assertEqual(led.read_bytes(), before)

    def test_g3_locked_identical_reimport_is_noop(self):
        self.doc(result())
        self.run_cli("import", str(self.p))
        self.lock_g3()
        led = self.p / "ledgers" / "results-ledger.json"
        before = led.read_bytes()
        r = self.run_cli("import", str(self.p))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("ledger unchanged", r.stdout)
        self.assertEqual(led.read_bytes(), before)

    def test_crlf_ledger_with_same_content_left_alone(self):
        self.doc(result())
        self.run_cli("import", str(self.p))
        led = self.p / "ledgers" / "results-ledger.json"
        crlf = led.read_bytes().replace(b"\n", b"\r\n")
        led.write_bytes(crlf)
        r = self.run_cli("import", str(self.p))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(led.read_bytes(), crlf)
