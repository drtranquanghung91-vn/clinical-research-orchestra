import contextlib
import io
import json
import re
import shutil
import tempfile
import unittest
import urllib.error
from pathlib import Path

import _paths  # noqa: F401
import init_project
import journal_check
from crolib import projectcfg

# Fictional journal and ISSNs (valid check digits, no real journal); shapes as the three APIs answer (plan D8).
NLM_SEARCH = json.dumps({"esearchresult": {"idlist": ["900000001"]}}).encode()
NLM_EMPTY = json.dumps({"esearchresult": {"idlist": []}}).encode()
NLM_XML = ('<NLMCatalogRecordSet><NLMCatalogRecord><NlmUniqueID>900000001</NlmUniqueID>'
           '<TitleMain><Title Sort="N">Journal of Fictional Medicine.</Title></TitleMain>'
           '<PublicationInfo><Publisher>Fictional Press Ltd</Publisher></PublicationInfo>'
           '<ISSN IssnType="Print">0000-0000</ISSN><ISSN IssnType="Electronic">0000-0019</ISSN>'
           '<IndexingSourceList><IndexingSourceName IndexingStatus="Currently-indexed">MEDLINE</IndexingSourceName>'
           '</IndexingSourceList></NLMCatalogRecord></NLMCatalogRecordSet>').encode()
DOAJ_HIT = json.dumps({"total": 1, "results": [{"bibjson": {
    "title": "Journal of Fictional Medicine", "pissn": "0000-0000", "eissn": "0000-0019",
    "publisher": {"name": "Fictional Press"}, "apc": {"has_apc": True, "max": [{"price": 1000, "currency": "USD"}]}},
    "admin": {"seal": False}}]}).encode()
DOAJ_NONE = json.dumps({"total": 0, "results": []}).encode()
CR_MSG = {"title": "Journal of Fictional Medicine", "publisher": "Fictional Press", "ISSN": ["0000-0000", "0000-0019"],
          "issn-type": [{"value": "0000-0000", "type": "print"}, {"value": "0000-0019", "type": "electronic"}]}
FOUND = [("esearch.fcgi", NLM_SEARCH), ("efetch.fcgi", NLM_XML), ("doaj.org", DOAJ_HIT),
         ("api.crossref.org/journals/0000-0000", json.dumps({"message": CR_MSG}).encode())]


def router(routes):
    calls = []

    def get(url):
        calls.append(url)
        for key, val in routes:
            if key in url:
                if isinstance(val, BaseException):
                    raise val
                return val
        raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
    get.calls = calls
    return get


class TestJournalCheck(unittest.TestCase):
    def setUp(self):
        self.t = Path(tempfile.mkdtemp())
        self.p = init_project.create(self.t / "p", "Fictional study", "manuscript", "cohort", "en", "en")
        self._get, self._gap = journal_check.http_get, journal_check.MIN_GAP
        journal_check.MIN_GAP = 0

    def tearDown(self):
        journal_check.http_get, journal_check.MIN_GAP = self._get, self._gap
        shutil.rmtree(self.t, ignore_errors=True)

    def use(self, routes):
        journal_check.http_get = router(routes)
        return journal_check.http_get

    def cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = journal_check.main([str(self.p), *argv])
        return code, out.getvalue(), err.getvalue()

    def data(self):
        return json.loads((self.p / journal_check.JSON_REL).read_text(encoding="utf-8"))

    def test_issn_helpers(self):
        self.assertTrue(journal_check.issn_check_ok("0000-0000"))
        self.assertTrue(journal_check.issn_check_ok("0000-0019"))
        self.assertFalse(journal_check.issn_check_ok("0000-0011"))
        self.assertEqual(journal_check.norm_issn("00000019"), "0000-0019")
        self.assertIsNone(journal_check.norm_issn("Journal of Fictional Medicine"))

    def test_lookup_by_issn_records_sources_and_dates(self):
        self.use(FOUND)
        code, out, err = self.cli("lookup", "0000-0000")
        self.assertEqual(code, 0, out + err)
        rec = self.data()["journals"][0]
        self.assertEqual(rec["key"], "0000-0000")
        self.assertRegex(rec["looked_up"], r"^\d{4}-\d{2}-\d{2}$")
        self.assertEqual({t["source"] for t in rec["title"]}, {"NLM Catalog", "DOAJ", "Crossref"})
        self.assertEqual(rec["title"][0]["value"], "Journal of Fictional Medicine")
        self.assertIs(rec["medline"]["value"], True)
        self.assertIn("Currently", rec["medline"]["detail"])
        self.assertTrue(rec["doaj"]["listed"])
        self.assertEqual(rec["doaj"]["apc"], ["1000 USD"])
        self.assertEqual(rec["signals"], [])
        md = (self.p / journal_check.MD_REL).read_bytes()
        self.assertNotIn(b"\r\n", md)
        self.assertIn("| Journal of Fictional Medicine |", md.decode("utf-8"))

    def test_signals_are_listed_never_a_verdict(self):
        self.use([("esearch.fcgi", NLM_EMPTY), ("doaj.org", DOAJ_NONE)])
        code, out, _ = self.cli("lookup", "0000-0019", "--claim", "medline", "--claim", "scopus", "--open-access",
                                "--concern", "promises publication in two weeks")
        self.assertEqual(code, 0)
        rec = self.data()["journals"][0]
        text = " | ".join(s["signal"] for s in rec["signals"])
        for s in ("not found in the NLM Catalog, DOAJ or Crossref", "claims MEDLINE indexing", "not checkable",
                  "not listed in DOAJ", "two weeks"):
            self.assertIn(s, text)
        self.assertTrue(all(s["source"] for s in rec["signals"]))
        for blob in (out, (self.p / journal_check.JSON_REL).read_text(encoding="utf-8"),
                     (self.p / journal_check.MD_REL).read_text(encoding="utf-8")):
            self.assertNotIn("predatory", blob.lower())

    def test_publisher_mismatch_and_check_digit(self):
        other = json.dumps({"message": dict(CR_MSG, publisher="Another House")}).encode()
        self.use(FOUND[:3] + [("api.crossref.org/journals/0000-0000", other)])
        self.cli("lookup", "0000-0000")
        self.assertIn("publisher differs", " ".join(s["signal"] for s in self.data()["journals"][0]["signals"]))
        self.use([("esearch.fcgi", NLM_EMPTY), ("doaj.org", DOAJ_NONE)])
        self.cli("lookup", "0000-0011")
        rec = [r for r in self.data()["journals"] if r["key"] == "0000-0011"][0]
        self.assertIn("invalid check digit", " ".join(s["signal"] for s in rec["signals"]))

    def test_title_lookup_resolves_issn_for_doaj(self):
        get = self.use([("esearch.fcgi", NLM_SEARCH), ("efetch.fcgi", NLM_XML), ("doaj.org", DOAJ_HIT),
                        ("journals?query=", json.dumps({"message": {"items": [CR_MSG]}}).encode())])
        self.assertEqual(self.cli("lookup", "Journal of Fictional Medicine")[0], 0)
        self.assertTrue(any("doaj.org" in u and "0000-0000" in u for u in get.calls), get.calls)
        self.assertEqual(self.data()["journals"][0]["key"], "0000-0000")

    def test_network_error_exits_2_and_writes_nothing(self):
        self.use([("esearch.fcgi", urllib.error.URLError("offline"))])
        code, _, err = self.cli("lookup", "0000-0000")
        self.assertEqual(code, 2)
        self.assertIn("offline", err)
        self.assertFalse((self.p / journal_check.JSON_REL).exists())

    def test_note_and_pick_write_only_target_keys(self):
        self.use(FOUND)
        self.cli("lookup", "0000-0000")
        before = (self.p / "project.yaml").read_text(encoding="utf-8").replace("\r\n", "\n").splitlines()
        self.assertEqual(self.cli("note", "0000-0000", "--words", "3000", "--abstract", "250", "--ref-style", "Vancouver",
                                  "--scope", "Clinical epidemiology", "--scope-url", "https://example.org/scope",
                                  "--source-url", "https://example.org/authors")[0], 0)
        self.assertIsNone(projectcfg.get(self.p, "target.journal"))
        self.assertEqual(self.cli("pick", "0000-0000", "--by", "Example author")[0], 0)
        self.assertEqual(projectcfg.get(self.p, "target.journal"), "Journal of Fictional Medicine")
        self.assertEqual(projectcfg.get(self.p, "target.word_limit"), "250")
        self.assertEqual(projectcfg.get(self.p, "target.text_words"), "3000")
        after = (self.p / "project.yaml").read_text(encoding="utf-8").splitlines()
        changed = [a for a, b in zip(after, before) if a != b]
        self.assertEqual(len(after), len(before))
        self.assertTrue(all(re.match(r"^  (journal|word_limit|text_words): ", c) for c in changed), changed)
        rec = self.data()["journals"][0]
        self.assertEqual(rec["picked"]["by"], "Example author")
        self.assertEqual(rec["notes"]["word_limit"]["source"], "https://example.org/authors")
        self.assertIn("picked by Example author", (self.p / journal_check.MD_REL).read_text(encoding="utf-8"))

    def test_pick_unknown_key_is_refused(self):
        code, out, _ = self.cli("pick", "0000-0019", "--by", "Example author")
        self.assertEqual(code, 1)
        self.assertIsNone(projectcfg.get(self.p, "target.journal"))

    def test_set_target_keeps_colons_and_quotes_readable(self):
        journal_check.set_target(self.p, {"journal": 'Journal: "Fictional" Medicine', "word_limit": 200})
        self.assertEqual(projectcfg.get(self.p, "target.journal"), "Journal: 'Fictional' Medicine")
        self.assertEqual(projectcfg.get(self.p, "target.word_limit"), "200")

    def _yaml_without_target(self):
        out, skip = [], False
        for ln in (self.p / "project.yaml").read_text(encoding="utf-8").splitlines():
            if ln.startswith("target:"):
                skip = True
                continue
            if skip and ln.startswith(" "):
                continue
            skip = False
            out.append(ln)
        return "\n".join(out) + "\n"

    def test_set_target_matches_target_line_variants(self):
        base = self._yaml_without_target()
        for variant in ("target: ", "target:  # comment", "target: {}", "target: null", "target:"):
            (self.p / "project.yaml").write_text(base + variant + "\n", encoding="utf-8", newline="\n")
            journal_check.set_target(self.p, {"journal": "Fictional Medicine", "word_limit": 200})
            text = (self.p / "project.yaml").read_text(encoding="utf-8")
            self.assertEqual(len(re.findall(r"(?m)^target:", text)), 1, variant)
            self.assertEqual(projectcfg.get(self.p, "target.journal"), "Fictional Medicine", variant)
            self.assertEqual(projectcfg.get(self.p, "target.word_limit"), "200", variant)

    def test_set_target_refuses_other_inline_value(self):
        base = self._yaml_without_target()
        (self.p / "project.yaml").write_text(base + "target: something\n", encoding="utf-8", newline="\n")
        with self.assertRaises(ValueError) as cm:
            journal_check.set_target(self.p, {"journal": "X"})
        self.assertIn("target", str(cm.exception))

    def test_get_maps_http_exception_to_network_error(self):
        import http.client

        def boom(url):
            raise http.client.IncompleteRead(b"x")
        journal_check.http_get = boom
        with self.assertRaises(journal_check.NetworkError):
            journal_check._get("https://example.org/x?y=1")


if __name__ == "__main__":
    unittest.main()
