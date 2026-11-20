import contextlib
import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

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

    def test_cite_keys_ignores_email_in_brackets(self):
        self.assertEqual(vr.cite_keys("[contact foo@bar.com]"), [])
        self.assertEqual(vr.cite_keys("[@a; @b]"), ["a", "b"])

    def _run(self, argv, fetch):
        out = io.StringIO()
        orig = vr.fetch_pubmed
        vr.fetch_pubmed = fetch
        try:
            with contextlib.redirect_stdout(out):
                return vr.main(argv)
        finally:
            vr.fetch_pubmed = orig

    def _proj(self, t, recs):
        proj = Path(t)
        (proj / "ledgers").mkdir()
        ledgers.save_references(proj / "ledgers" / "references.json", recs)
        return proj

    def test_main_write_updates_ledger(self):
        with tempfile.TemporaryDirectory() as t:
            proj = self._proj(t, [dict(REC)])
            code = self._run([str(proj), "--write"], lambda p: FOUND)
            self.assertEqual(code, 0)
            rec = ledgers.load_references(proj / "ledgers" / "references.json")[0]
            self.assertTrue(rec["verified_by"].startswith("verify_refs.py"))
            self.assertIn("VERIFIED", rec["verified_by"])
            self.assertFalse(rec["retracted"])

    def test_main_returns_1_on_not_found(self):
        with tempfile.TemporaryDirectory() as t:
            proj = self._proj(t, [dict(REC)])
            self.assertEqual(self._run([str(proj)], lambda p: None), 1)

    def test_main_returns_1_on_unknown_cite(self):
        with tempfile.TemporaryDirectory() as t:
            proj = self._proj(t, [dict(REC)])
            f = Path(t) / "c.md"
            f.write_text("Ghost [@ghost2020].", encoding="utf-8")
            self.assertEqual(self._run([str(proj), "--cite", str(f)], lambda p: FOUND), 1)

    def test_main_missing_cite_file_returns_2(self):
        with tempfile.TemporaryDirectory() as t:
            proj = self._proj(t, [dict(REC)])
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                code = self._run([str(proj), "--cite", str(Path(t) / "nope.md")], lambda p: FOUND)
            self.assertEqual(code, 2)
            self.assertIn("cannot read", err.getvalue())

    def test_write_not_found_keeps_retracted_true(self):
        with tempfile.TemporaryDirectory() as t:
            proj = self._proj(t, [dict(REC, retracted=True)])
            self._run([str(proj), "--write"], lambda p: None)
            rec = ledgers.load_references(proj / "ledgers" / "references.json")[0]
            self.assertTrue(rec["retracted"])
            self.assertTrue(rec["verified_by"].endswith("NOT_FOUND"))


class TestFetchers(unittest.TestCase):
    def test_crossref_retraction(self):
        msg = {"message": {"title": ["T"], "issued": {"date-parts": [[2020]]}, "author": [{"family": "Roe"}],
                           "DOI": "10.1/x", "updated-by": [{"type": "retraction"}]}}
        with mock.patch.object(vr, "_get", return_value=json.dumps(msg).encode()):
            found = vr.fetch_crossref("10.1/x")
        self.assertEqual(found["pubtypes"], ["Retracted Publication"])

    def test_crossref_404_is_none(self):
        def nf(url, *a, **k):
            raise urllib.error.HTTPError(url, 404, "nf", {}, None)
        with mock.patch.object(vr, "_get", side_effect=nf):
            self.assertIsNone(vr.fetch_crossref("10.1/x"))

    def test_pubmed_error_result_is_none(self):
        body = json.dumps({"result": {"123": {"error": "cannot get document summary"}}}).encode()
        with mock.patch.object(vr, "_get", return_value=body), mock.patch.object(vr.time, "sleep"):
            self.assertIsNone(vr.fetch_pubmed("123"))


if __name__ == "__main__":
    unittest.main()
