import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
import guideline_checklist as gc
import init_project

IDS = ["1a", "1b", "2", "3", "4", "5", "6a", "6b", "7", "8", "9", "10", "11", "12a", "12b", "12c", "12d", "12e",
       "13a", "13b", "13c", "14a", "14b", "14c", "15", "16a", "16b", "16c", "17", "18", "19", "20", "21", "22"]
SECTIONS = {"Title and abstract", "Introduction", "Methods", "Results", "Discussion", "Other information"}
METHODS = ("# Chương 2\n\nDòng hai.\nDòng ba.\nNghiên cứu đoàn hệ hồi cứu tại một bệnh viện tỉnh.\nDòng năm.\n"
           "Dòng sáu.\nDòng bảy.\nDòng tám.\nDòng chín.\nDòng mười.\nCỡ mẫu gồm {{R-A0-001.n}} người bệnh.\n")
REL = "06_writing/thesis/ch2-methods.md"   # design sentence on line 5, sample size on line 12


class TestGuidelineChecklist(unittest.TestCase):
    def setUp(self):
        self.t = Path(tempfile.mkdtemp())
        self.p = init_project.create(self.t / "p", "T", "thesis-masters", "cohort", "vi", "vi")
        (self.p / "06_writing" / "thesis").mkdir(parents=True, exist_ok=True)
        (self.p / REL).write_text(METHODS, encoding="utf-8")
        (self.p / "ledgers" / "results-ledger.json").write_text(json.dumps({"results": [
            {"id": "R-A0-001", "label": "n", "value": 1070, "n": 1070, "kind": "n",
             "source_file": "x", "locator": "1", "raw": "x"}]}), encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.t, ignore_errors=True)

    def write(self, drop=(), guideline="STROBE", **over):
        items = {i: {"status": "na", "reason": "fixture"} for i in IDS if i not in drop}
        items.update(over)
        (self.p / "reviews" / "guideline-checklist.json").write_text(json.dumps(
            {"guideline": guideline, "deliverable": "thesis", "items": items}, ensure_ascii=False, indent=2), encoding="utf-8")

    def cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = gc.main([str(self.p), *argv])
        return code, out.getvalue(), err.getvalue()

    def test_item_list_is_complete_and_paraphrased_briefly(self):
        data = gc.load_items("STROBE")
        self.assertEqual((data["code"], data["version"]), ("STROBE", "2007"))
        self.assertEqual([i["id"] for i in data["items"]], IDS)
        for it in data["items"]:
            self.assertIn(it["section"], SECTIONS)
            self.assertTrue(0 < len(it["text"].split()) <= 12, it)

    def test_all_na_with_reasons_is_clean(self):
        self.write()
        self.assertEqual(gc.check(self.p), [])
        self.assertEqual(self.cli()[0], 0)

    def test_present_quote_found_in_source_or_rendered_window(self):
        self.write(**{"4": {"status": "present", "file": REL, "line": 8, "quote": "đoàn hệ  hồi cứu"},
                      "10": {"status": "present", "file": REL, "line": 12, "quote": "Cỡ mẫu gồm 1070 người bệnh"}})
        self.assertEqual(gc.check(self.p), [])
        self.write(**{"4": {"status": "present", "file": REL, "line": 9, "quote": "đoàn hệ hồi cứu"}})
        found = gc.check(self.p)
        self.assertEqual([(lvl, loc) for lvl, loc, _ in found], [("block", f"{REL}:9")])
        self.assertIn("±3", found[0][2])

    def test_blocks_and_warns(self):
        self.write(drop=("22",), **{"1a": {"status": "absent"}, "6b": {"status": "na", "reason": " "},
                                    "13a": {"status": "partial", "file": REL, "line": 12, "reason": "no stage counts"},
                                    "12c": {"status": "maybe"}, "99": {"status": "na", "reason": "x"},
                                    "5": {"status": "present", "file": REL, "line": 5}})
        found = gc.check(self.p)
        blocks = [m for lvl, _, m in found if lvl == "block"]
        warns = [m for lvl, _, m in found if lvl == "warn"]
        for frag in ("item 1a", "item 6b", "item 12c", "item 22", "item 5"):
            self.assertTrue(any(frag in m for m in blocks), (frag, blocks))
        self.assertTrue(any("item 13a" in m for m in warns))
        self.assertTrue(any("item 99" in m for m in warns))
        code, out, _ = self.cli()
        self.assertEqual(code, 1)
        self.assertRegex(out, r"(?m)^E-RG block reviews/guideline-checklist\.json:\d+: item 1a")
        self.assertEqual(gc.absent_count(self.p), 2)

    def test_wrong_guideline_blocks(self):
        self.write(guideline="CONSORT-2025")
        self.assertTrue(any(lvl == "block" and "CONSORT-2025" in m for lvl, _, m in gc.check(self.p)))

    def test_errors_exit_2(self):
        self.assertEqual(self.cli()[0], 2)                       # no checklist yet
        self.write()
        y = self.p / "project.yaml"
        y.write_text(y.read_text(encoding="utf-8").replace("reporting_guideline: STROBE", "reporting_guideline: CONSORT-2025"),
                     encoding="utf-8")
        code, _, err = self.cli()
        self.assertEqual(code, 2)
        self.assertIn("no item list for CONSORT-2025", err)
        with self.assertRaises(gc.NoItemList):
            gc.check(self.p)
        self.assertEqual(self.cli("--guideline", "STROBE")[0], 0)

    def test_table_and_checklist_path(self):
        self.write()
        code, out, _ = self.cli("--table")
        self.assertEqual(code, 0)
        rows = [ln for ln in out.splitlines() if ln.startswith("| ") and not ln.startswith("| Mục")]
        self.assertEqual(len(rows), 34)
        self.assertTrue(out.splitlines()[0].startswith("| Mục |"))
        other = self.p / "reviews" / "rounds" / "thesis" / "r1" / "reviews"
        other.mkdir(parents=True)
        (other / "guideline-checklist.json").write_text(json.dumps({"guideline": "STROBE", "items": {}}), encoding="utf-8")
        self.assertEqual(len(gc.check(self.p, checklist_path=other / "guideline-checklist.json")), 34)
