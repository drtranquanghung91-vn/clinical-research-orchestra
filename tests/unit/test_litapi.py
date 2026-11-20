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


if __name__ == "__main__":
    unittest.main()
