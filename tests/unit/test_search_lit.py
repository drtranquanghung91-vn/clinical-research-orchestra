import contextlib
import io
import json
import tempfile
import unittest
import urllib.error
import urllib.parse
from pathlib import Path
from unittest import mock

import _paths  # noqa: F401
import search_lit
from crolib import ledgers, litapi

REC = {"id": "nguyen2026", "title": "Metformin in PMOS", "authors": ["Nguyen A"], "journal": "PLoS Med",
       "year": 2026, "doi": "10.1371/x", "pmid": "111", "pmcid": "", "pubtypes": ["Retracted Publication"],
       "retrieved_with": "litapi esummary", "access": "metadata"}


class TestSearchLit(unittest.TestCase):
    def test_to_ledger_record_adds_required_fields(self):
        r = search_lit.to_ledger_record(REC, "Background: ...")
        self.assertEqual(r["abstract"], "Background: ...")
        self.assertTrue(r["retracted"])
        self.assertIsNone(r["verified_by"])
        self.assertEqual(r["used_in"], [])
        self.assertEqual(ledgers.validate_reference(r), [])

    def test_add_to_ledger_dedupes_and_makes_unique_ids(self):
        orig_s, orig_a = search_lit.litapi.summaries, search_lit.litapi.abstracts
        try:
            search_lit.litapi.summaries = lambda pmids: [dict(REC, pmid=p) for p in pmids]
            search_lit.litapi.abstracts = lambda pmids: {p: "abs" for p in pmids}
            with tempfile.TemporaryDirectory() as t:
                proj = Path(t)
                (proj / "ledgers").mkdir()
                added = search_lit.add_to_ledger(proj, ["111", "222"])
                self.assertEqual(added, ["nguyen2026", "nguyen2026a"])
                again = search_lit.add_to_ledger(proj, ["111"])
                self.assertEqual(again, [])
                refs = ledgers.load_references(proj / "ledgers" / "references.json")
                self.assertEqual(len(refs), 2)
        finally:
            search_lit.litapi.summaries, search_lit.litapi.abstracts = orig_s, orig_a

    def test_search_falls_back_to_europepmc_when_pubmed_raises(self):
        orig_s, orig_e = search_lit.litapi.search, search_lit.litapi.epmc_search

        def boom(query, retmax=10):
            raise OSError("blocked")

        try:
            search_lit.litapi.search = boom
            search_lit.litapi.epmc_search = lambda q, retmax=10: [{"title": "From EPMC"}]
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                rc = search_lit.main(["search", "x"])
            self.assertEqual(rc, 0)
            self.assertIn("From EPMC", out.getvalue())
            self.assertIn("PubMed unavailable", err.getvalue())
        finally:
            search_lit.litapi.search, search_lit.litapi.epmc_search = orig_s, orig_e


ESUM = {"uid": "111", "title": "Metformin in PMOS.", "sortfirstauthor": "Nguyen A",
        "authors": [{"name": "Nguyen A", "authtype": "Author"}], "source": "PLoS Med", "pubdate": "2026 Mar",
        "articleids": [{"idtype": "doi", "value": "10.1371/x"}], "pubtype": ["Journal Article"]}


def fake_ncbi(url, timeout=30):
    """Offline NCBI: PMID 111 exists, every other PMID returns NCBI's per-id error entry."""
    q = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
    ids = q.get("id", [""])[0].split(",")
    if "esummary" in url:
        res = {"uids": ids}
        for i in ids:
            res[i] = dict(ESUM) if i == "111" else {"uid": i, "error": "cannot get document summary"}
        return json.dumps({"result": res}).encode()
    if "efetch" in url:
        arts = "".join(f"<PubmedArticle><MedlineCitation><PMID>{i}</PMID><Article><Abstract><AbstractText>abs"
                       f"</AbstractText></Abstract></Article></MedlineCitation></PubmedArticle>"
                       for i in ids if i == "111")
        return f"<PubmedArticleSet>{arts}</PubmedArticleSet>".encode()
    raise AssertionError(f"unexpected URL {url}")


def offline():
    raise urllib.error.URLError("offline")


class TestSearchLitCli(unittest.TestCase):
    def setUp(self):
        self._p = [mock.patch.object(litapi.time, "sleep"), mock.patch.object(litapi, "http_get", fake_ncbi)]
        for p in self._p:
            p.start()
        self._tmp = tempfile.TemporaryDirectory()
        self.proj = Path(self._tmp.name)
        (self.proj / "ledgers").mkdir()

    def tearDown(self):
        for p in self._p:
            p.stop()
        self._tmp.cleanup()

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = search_lit.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def refs(self):
        return ledgers.load_references(self.proj / "ledgers" / "references.json")

    def test_add_nonexistent_pmid_is_reported_not_recorded(self):
        code, out, err = self.run_cli("add", str(self.proj), "111", "99999999")
        self.assertEqual(code, 1)
        self.assertIn("99999999", err)
        self.assertIn("not found", err)
        self.assertEqual([r["pmid"] for r in self.refs()], ["111"])
        self.assertEqual(json.loads(out)["not_found"], ["99999999"])

    def test_add_all_found_exits_0(self):
        code, out, err = self.run_cli("add", str(self.proj), "111")
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["added"], ["nguyen2026"])

    def test_fetch_nonexistent_pmid(self):
        code, out, err = self.run_cli("fetch", "111", "99999999")
        self.assertEqual(code, 1)
        self.assertEqual([r["pmid"] for r in json.loads(out)], ["111"])
        self.assertIn("99999999", err)

    def test_non_digit_pmid_exits_2_without_network(self):
        with mock.patch.object(litapi, "http_get", side_effect=AssertionError("network used")):
            for argv in (("fetch", "12a"), ("add", str(self.proj), "111", "PMID:5")):
                code, out, err = self.run_cli(*argv)
                self.assertEqual(code, 2, argv)
                self.assertIn("not a PMID", err)
                self.assertEqual(out, "")
        self.assertEqual(self.refs(), [])

    def test_add_without_ledgers_folder_exits_2(self):
        code, _, err = self.run_cli("add", str(self.proj / "nope"), "111")
        self.assertEqual(code, 2)
        self.assertIn("ledgers", err)

    def test_add_with_malformed_ledger_exits_2(self):
        (self.proj / "ledgers" / "references.json").write_text("{oops", encoding="utf-8")
        code, _, err = self.run_cli("add", str(self.proj), "111")
        self.assertEqual(code, 2)
        self.assertIn("references.json", err)

    def test_add_tolerates_existing_record_without_id(self):
        ledgers.save_references(self.proj / "ledgers" / "references.json", [{"title": "hand-made", "pmid": "5"}])
        added = search_lit.add_to_ledger(self.proj, ["111"])
        self.assertEqual(added, ["nguyen2026"])
        self.assertEqual(len(self.refs()), 2)

    def test_network_errors_exit_2(self):
        with mock.patch.object(litapi, "http_get", side_effect=lambda *a, **k: offline()):
            for argv in (("fetch", "111"), ("add", str(self.proj), "111"), ("doi", "10.1/x"),
                         ("trial", "NCT01234567"), ("search", "x")):
                code, out, err = self.run_cli(*argv)
                self.assertEqual(code, 2, argv)
                self.assertIn("search_lit:", err, argv)
                self.assertEqual(out, "", argv)

    def test_doi_not_found_exits_1(self):
        def nf(url, timeout=30):
            raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
        with mock.patch.object(litapi, "http_get", side_effect=nf):
            code, out, err = self.run_cli("doi", "10.1/missing")
        self.assertEqual(code, 1)
        self.assertIn("not found", err)


if __name__ == "__main__":
    unittest.main()
