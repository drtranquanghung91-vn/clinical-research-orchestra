import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
import search_lit
from crolib import ledgers

REC = {"id": "nguyen2026", "title": "Metformin in PMOS", "authors": ["Nguyen A"], "journal": "PLoS Med",
       "year": 2026, "doi": "10.1371/x", "pmid": "111", "pmcid": "", "pubtypes": ["Retracted Publication"],
       "retrieved_with": "pubmed.py esummary", "access": "metadata"}


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


if __name__ == "__main__":
    unittest.main()
