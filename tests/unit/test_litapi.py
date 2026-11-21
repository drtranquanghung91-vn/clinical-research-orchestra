import json
import unittest

import _paths  # noqa: F401
from crolib import litapi

ESUMMARY = {"result": {"uids": ["111"], "111": {
    "uid": "111", "title": "Metformin in PMOS.", "sortfirstauthor": "Nguyen A",
    "authors": [{"name": "Nguyen A", "authtype": "Author"}], "source": "PLoS Med",
    "pubdate": "2026 Mar", "articleids": [{"idtype": "doi", "value": "10.1371/x"}],
    "pubtype": ["Journal Article"]}}}


class TestLitapi(unittest.TestCase):
    def setUp(self):
        self._orig = litapi.http_get

    def tearDown(self):
        litapi.http_get = self._orig

    def test_ua_is_project_ua(self):
        self.assertIn("clinical-research-orchestra", litapi.UA)

    def test_summaries_to_records(self):
        litapi.http_get = lambda url, timeout=30: json.dumps(ESUMMARY).encode()
        recs = litapi.summaries(["111"])
        self.assertEqual(recs[0]["pmid"], "111")
        self.assertEqual(recs[0]["doi"], "10.1371/x")
        self.assertEqual(recs[0]["year"], 2026)
        self.assertEqual(recs[0]["title"], "Metformin in PMOS")
        self.assertEqual(recs[0]["id"], "nguyen2026")

    def test_make_id(self):
        self.assertEqual(litapi.make_id("Le Thi B", "2025"), "le2025")
        self.assertEqual(litapi.make_id("", ""), "ref")

    def test_make_id_folds_diacritics(self):
        self.assertEqual(litapi.make_id("Nguyễn Văn A", "2024"), "nguyen2024")
        self.assertEqual(litapi.make_id("Đặng T", "2020"), "dang2020")
        self.assertEqual(litapi.make_id("Müller K", "2019"), "muller2019")

    def test_summaries_skip_error_entries(self):
        body = {"result": {"uids": ["111", "99999999"], "111": ESUMMARY["result"]["111"],
                           "99999999": {"uid": "99999999", "error": "cannot get document summary"}}}
        litapi.http_get = lambda url, timeout=30: json.dumps(body).encode()
        recs = litapi.summaries(["111", "99999999"])
        self.assertEqual([r["pmid"] for r in recs], ["111"])

    def test_epmc_by_pmid(self):
        body = {"resultList": {"result": [{
            "pmid": "111", "title": "Metformin in PMOS.", "authorString": "Nguyen A, Le B.", "pubYear": "2026",
            "doi": "10.1371/x", "authorList": {"author": [{"fullName": "Nguyen A"}, {"fullName": "Le B"}]},
            "journalInfo": {"journal": {"medlineAbbreviation": "PLoS Med"}, "volume": "9", "issue": "2"},
            "pageInfo": "1-9", "abstractText": "<h4>Aim</h4> text",
            "pubTypeList": {"pubType": ["Journal Article", "Retracted Publication"]}}]}}
        urls = []

        def fake(url, timeout=30):
            urls.append(url)
            return json.dumps(body).encode()
        litapi.http_get = fake
        recs = litapi.epmc_by_pmid(["111", "222"])
        self.assertEqual([r["pmid"] for r in recs], ["111"])  # 222 not returned for its own query
        self.assertIn("EXT_ID%3A111+AND+SRC%3AMED", urls[0])
        self.assertIn("resultType=core", urls[0])
        self.assertEqual(recs[0]["pubtypes"], ["Journal Article", "Retracted Publication"])
        self.assertEqual(recs[0]["id"], "nguyen2026")
        self.assertEqual(recs[0]["abstract"], "Aim text")
        self.assertEqual(recs[0]["pages"], "1-9")

    def test_epmc_by_pmid_empty(self):
        litapi.http_get = lambda url, timeout=30: json.dumps({"resultList": {"result": []}}).encode()
        self.assertEqual(litapi.epmc_by_pmid(["5"]), [])


    # --- group (collective) authors, one test per lookup path (final review #1)

    def test_esummary_keeps_collective_name(self):
        body = {"result": {"uids": ["222"], "222": {
            "uid": "222", "title": "Diabetes care in the hospital.",
            "sortfirstauthor": "American Diabetes Association Professional Practice Committee for Diabetes*",
            "authors": [{"name": "American Diabetes Association Professional Practice Committee for Diabetes*",
                         "authtype": "CollectiveName"},
                        {"name": "", "authtype": "Author"}],
            "source": "Diabetes Care", "pubdate": "2026 Jan", "articleids": []}}}
        litapi.http_get = lambda url, timeout=30: json.dumps(body).encode()
        rec = litapi.summaries(["222"])[0]
        self.assertEqual(rec["authors"],
                         ["American Diabetes Association Professional Practice Committee for Diabetes"])
        self.assertEqual(rec["id"], "american2026")

    def test_epmc_collective_name_and_null_author_list(self):
        body = {"resultList": {"result": [
            {"pmid": "333", "title": "Guideline.", "authorString": "WHO Guideline Group, Le B.", "pubYear": "2025",
             "authorList": {"author": [{"collectiveName": "WHO Guideline Group"}, {"fullName": "Le B"}, {}]}},
            {"pmid": "444", "title": "No authors.", "authorString": "", "pubYear": "2024", "authorList": None},
        ]}}
        litapi.http_get = lambda url, timeout=30: json.dumps(body).encode()
        recs = {r["pmid"]: r for r in (litapi.epmc_search("x"))}
        self.assertEqual(recs["333"]["authors"], ["WHO Guideline Group", "Le B"])
        self.assertNotIn(None, recs["333"]["authors"])
        self.assertEqual(recs["444"]["authors"], [])

    def test_crossref_organisation_author(self):
        body = {"message": {"DOI": "10.9/org", "title": ["Consensus statement"],
                            "issued": {"date-parts": [[2023]]},
                            "author": [{"name": "Vietnam Society of Cardiology"},
                                       {"family": "Tran", "given": "Van An"}, {"given": "Orphan"}]}}
        litapi.http_get = lambda url, timeout=30: json.dumps(body).encode()
        rec = litapi.crossref("10.9/org")
        self.assertEqual(rec["authors"], ["Vietnam Society of Cardiology", "Tran VA"])
        self.assertEqual(rec["id"], "vietnam2023")


if __name__ == "__main__":
    unittest.main()
