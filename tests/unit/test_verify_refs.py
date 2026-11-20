import json
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
import verify_refs as vr
from crolib import ledgers

REC = {"id": "smith2024", "title": "Lifestyle intervention in polycystic ovary syndrome",
       "authors": ["Smith J"], "year": 2024, "pmid": "123", "doi": "10.1/abc"}
FOUND = {"title": "Lifestyle intervention in polycystic ovary syndrome.", "year": 2024,
         "first_author": "Smith J", "doi": "10.1/abc", "journal": "BMJ", "pubtypes": ["Journal Article"]}


class TestVerify(unittest.TestCase):
    def test_verified(self):
        self.assertEqual(vr.verify(REC, pubmed=lambda p: FOUND)[0], "VERIFIED")

    def test_not_found(self):
        self.assertEqual(vr.verify(REC, pubmed=lambda p: None)[0], "NOT_FOUND")

    def test_title_mismatch(self):
        st, notes = vr.verify(REC, pubmed=lambda p: dict(FOUND, title="Something unrelated entirely"))
        self.assertEqual(st, "MISMATCH")
        self.assertTrue(any("title" in n for n in notes))

    def test_retracted_beats_verified(self):
        st, _ = vr.verify(REC, pubmed=lambda p: dict(FOUND, pubtypes=["Retracted Publication"]))
        self.assertEqual(st, "RETRACTED")

    def test_doi_only_uses_crossref(self):
        st, _ = vr.verify(dict(REC, pmid=""), pubmed=lambda p: None, crossref=lambda d: FOUND)
        self.assertEqual(st, "VERIFIED")

    def test_no_identifier(self):
        self.assertEqual(vr.verify(dict(REC, pmid="", doi=""))[0], "NO_IDENTIFIER")

    def test_network_error_is_never_verified(self):
        def boom(p):
            raise OSError("offline")
        self.assertEqual(vr.verify(REC, pubmed=boom)[0], "ERROR")


class TestCitations(unittest.TestCase):
    def test_cite_keys(self):
        text = "A [@smith2024]. B [@le2025; @tran2023, p. 4]. Email a@b.com is not a cite."
        self.assertEqual(vr.cite_keys(text), ["smith2024", "le2025", "tran2023"])

    def test_check_citations_flags_unknown_and_retracted(self):
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / "ch1.md"
            f.write_text("Known [@smith2024]. Unknown [@ghost2020]. Bad [@ret2019].", encoding="utf-8")
            refs = [dict(REC), dict(REC, id="ret2019", retracted=True)]
            found = vr.check_citations([f], refs)
            keys = {(x["key"], x["code"]) for x in found}
            self.assertIn(("ghost2020", "E-REF"), keys)
            self.assertIn(("ret2019", "E-REF"), keys)
            self.assertNotIn("smith2024", {x["key"] for x in found})

    def test_main_write_updates_ledger(self):
        with tempfile.TemporaryDirectory() as t:
            proj = Path(t)
            (proj / "ledgers").mkdir()
            ledgers.save_references(proj / "ledgers" / "references.json", [dict(REC)])
            orig = vr.fetch_pubmed
            vr.fetch_pubmed = lambda p: FOUND
            try:
                code = vr.main([str(proj), "--write"])
            finally:
                vr.fetch_pubmed = orig
            self.assertEqual(code, 0)
            rec = ledgers.load_references(proj / "ledgers" / "references.json")[0]
            self.assertTrue(rec["verified_by"].startswith("verify_refs.py"))
            self.assertIn("VERIFIED", rec["verified_by"])
            self.assertFalse(rec["retracted"])


if __name__ == "__main__":
    unittest.main()
