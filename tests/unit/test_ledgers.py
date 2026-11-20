import json
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
from crolib import ledgers

REF = {"id": "smith2024", "title": "A trial", "authors": ["Smith J"], "year": 2024,
       "pmid": "12345678", "doi": "", "abstract": "", "retracted": False,
       "verified_by": None, "used_in": []}
RES = {"id": "R-001", "label": "median PFS", "value": "11.2", "unit": "months",
       "source_file": "05_analysis/output/km.txt", "locator": "line 41",
       "raw": "median survival 11.2", "locked": False}
CLAIM = {"id": "C-001", "file": "06_writing/thesis/ch1.md", "location": "p4", "text": "X reduces Y.",
         "kind": "background", "refs": ["smith2024"], "results": [], "status": "verified-abstract"}


class TestLedgers(unittest.TestCase):
    def test_valid_records_pass(self):
        self.assertEqual(ledgers.validate_reference(REF), [])
        self.assertEqual(ledgers.validate_result(RES), [])
        self.assertEqual(ledgers.validate_claim(CLAIM), [])

    def test_reference_needs_identifier(self):
        bad = dict(REF, pmid="", doi="")
        self.assertTrue(any("PMID or DOI" in e for e in ledgers.validate_reference(bad)))

    def test_reference_pmid_must_be_digits(self):
        self.assertTrue(ledgers.validate_reference(dict(REF, pmid="PMID123")))

    def test_result_needs_source_and_raw(self):
        self.assertTrue(ledgers.validate_result(dict(RES, source_file="")))
        self.assertTrue(ledgers.validate_result(dict(RES, raw="")))

    def test_claim_kind_and_status_enums(self):
        self.assertTrue(ledgers.validate_claim(dict(CLAIM, kind="opinion")))
        self.assertTrue(ledgers.validate_claim(dict(CLAIM, status="maybe")))

    def test_unique_id(self):
        self.assertEqual(ledgers.unique_id("smith2024", set()), "smith2024")
        self.assertEqual(ledgers.unique_id("smith2024", {"smith2024"}), "smith2024a")
        self.assertEqual(ledgers.unique_id("smith2024", {"smith2024", "smith2024a"}), "smith2024b")

    def test_save_and_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "references.json"
            self.assertEqual(ledgers.load_references(p), [])
            ledgers.save_references(p, [REF])
            self.assertEqual(ledgers.load_references(p), [REF])
            self.assertIn('"references"', p.read_text(encoding="utf-8"))

    def test_check_project_reports_bad_records_and_duplicates(self):
        with tempfile.TemporaryDirectory() as t:
            led = Path(t) / "ledgers"
            led.mkdir()
            (led / "references.json").write_text(json.dumps({"references": [REF, REF]}), encoding="utf-8")
            (led / "results-ledger.json").write_text(json.dumps({"results": [dict(RES, raw="")]}), encoding="utf-8")
            (led / "claims.json").write_text(json.dumps({"claims": [CLAIM]}), encoding="utf-8")
            errs = ledgers.check_project(Path(t))
            self.assertTrue(any("duplicate id" in e for e in errs))
            self.assertTrue(any("R-001" in e for e in errs))


if __name__ == "__main__":
    unittest.main()
