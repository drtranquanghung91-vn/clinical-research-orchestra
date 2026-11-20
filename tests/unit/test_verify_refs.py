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

    # I3: a wrong path or a broken ledger is an error (2), never "0 references, clean"
    def _run_err(self, argv, fetch=lambda p: FOUND):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = self._run(argv, fetch)
        return code, err.getvalue()

    def test_missing_project_exits_2(self):
        with tempfile.TemporaryDirectory() as t:
            code, err = self._run_err([str(Path(t) / "nonexistent_proj")])
            self.assertEqual(code, 2)
            self.assertIn("not found", err)

    def test_folder_without_ledgers_exits_2(self):
        with tempfile.TemporaryDirectory() as t:
            code, err = self._run_err([t])
            self.assertEqual(code, 2)
            self.assertIn("ledgers", err)

    def test_malformed_references_json_exits_2(self):
        with tempfile.TemporaryDirectory() as t:
            proj = self._proj(t, [])
            for body in ("{not json", "[]", '{"references": "x"}'):
                (proj / "ledgers" / "references.json").write_text(body, encoding="utf-8")
                code, err = self._run_err([str(proj)])
                self.assertEqual(code, 2, body)
                self.assertIn("references.json", err, body)

    def test_error_keeps_verified_by_and_warns_stale(self):
        def boom(p):
            raise OSError("offline")
        with tempfile.TemporaryDirectory() as t:
            old = "verify_refs.py 2026-01-01 VERIFIED"
            proj = self._proj(t, [dict(REC, verified_by=old)])
            out = io.StringIO()
            vr_fetch = vr.fetch_pubmed
            vr.fetch_pubmed = boom
            try:
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                    code = vr.main([str(proj), "--write"])
            finally:
                vr.fetch_pubmed = vr_fetch
            rec = ledgers.load_references(proj / "ledgers" / "references.json")[0]
            self.assertEqual(rec["verified_by"], old)
            self.assertIn("stale", out.getvalue())
            self.assertEqual(code, 2)

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
        errors = []

        def nf(url, *a, **k):
            errors.append(urllib.error.HTTPError(url, 404, "nf", {}, None))
            raise errors[-1]
        try:
            with mock.patch.object(vr, "_get", side_effect=nf):
                self.assertIsNone(vr.fetch_crossref("10.1/x"))
        finally:
            for e in errors:
                e.close()  # no ResourceWarning from the test's own HTTPError

    def test_pubmed_error_result_is_none(self):
        body = json.dumps({"result": {"123": {"error": "cannot get document summary"}}}).encode()
        with mock.patch.object(vr, "_get", return_value=body), mock.patch.object(vr.time, "sleep"):
            self.assertIsNone(vr.fetch_pubmed("123"))


if __name__ == "__main__":
    unittest.main()
