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
NL = chr(10)
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

    def _present(self, **kw):
        self.write(**{"4": dict({"status": "present", "file": REL, "line": 5, "quote": "đoàn hệ"}, **kw)})
        return gc.check(self.p)

    def test_file_outside_project_blocks(self):
        outside = self.t / "outside.md"
        outside.write_text("đoàn hệ" + NL, encoding="utf-8")
        for bad in (str(outside), "../outside.md"):
            found = self._present(file=bad, line=1)
            self.assertTrue(any(l == "block" and "outside project" in m for l, _, m in found), (bad, found))

    def test_non_utf8_source_blocks_without_traceback(self):
        (self.p / REL).write_bytes(bytes([255, 254, 0, 98, 10]) * 5)
        found = self._present()
        self.assertTrue(any(l == "block" and "not UTF-8" in m for l, _, m in found), found)

    def test_empty_quote_blocks(self):
        for q in ("***", "_", "`"):
            found = self._present(quote=q)
            self.assertTrue(any(l == "block" and "empty quote" in m for l, _, m in found), (q, found))

    def test_deliverable_mismatch_warns(self):
        self.write()
        legacy = self.p / "reviews" / "guideline-checklist.json"
        self.assertEqual(gc.check(self.p, deliverable="thesis"), [])
        found = gc.check(self.p, checklist_path=legacy, deliverable="manuscript")
        self.assertTrue(any(l == "warn" and "deliverable" in m for l, _, m in found), found)
        # the legacy file holds the thesis checklist: it is not the manuscript's
        with self.assertRaises(gc.InputError):
            gc.check(self.p, deliverable="manuscript")
        code, _, err = self.cli("--deliverable", "manuscript")
        self.assertEqual(code, 2)
        self.assertIn("reviews/guideline-checklist-manuscript.json not found", err)
        (self.p / "reviews" / "guideline-checklist.json").write_text(
            json.dumps({"guideline": "STROBE", "items": {i: {"status": "na", "reason": "x"} for i in IDS}}),
            encoding="utf-8")
        self.assertTrue(any(l == "warn" for l, _, _ in gc.check(self.p, deliverable="thesis")))

    def write_for(self, deliverable, drop=()):
        items = {i: {"status": "na", "reason": "fixture"} for i in IDS if i not in drop}
        (self.p / "reviews" / f"guideline-checklist-{deliverable}.json").write_text(json.dumps(
            {"guideline": "STROBE", "deliverable": deliverable, "items": items}), encoding="utf-8")

    def test_one_checklist_per_deliverable(self):
        self.write_for("thesis")
        self.write_for("manuscript", drop=("1a",))
        self.assertEqual(gc.check(self.p, deliverable="thesis"), [])
        found = gc.check(self.p, deliverable="manuscript")
        self.assertEqual(found, [("block", "reviews/guideline-checklist-manuscript.json:1",
                                  "item 1a (Title and abstract) is missing from the checklist")])
        self.assertEqual(gc.checklist_path(self.p, "thesis"), self.p / "reviews" / "guideline-checklist-thesis.json")
        code, _, err = self.cli()
        self.assertEqual(code, 2)
        self.assertIn("pass --deliverable", err)
        code, out, _ = self.cli("--table", "--deliverable", "manuscript")
        self.assertEqual(code, 0)
        self.assertIn("| 1a |", out)
        self.assertIn("không có", out.splitlines()[2])

    def test_per_deliverable_file_wins_over_legacy(self):
        self.write(drop=("1a",))
        self.write_for("thesis")
        self.assertEqual(gc.check(self.p, deliverable="thesis"), [])

    def test_legacy_file_is_read_for_its_own_deliverable_or_without_one(self):
        self.write()
        legacy = self.p / "reviews" / "guideline-checklist.json"
        self.assertEqual(gc.checklist_path(self.p, "thesis"), legacy)
        self.assertEqual(gc.checklist_path(self.p, "manuscript"),
                         self.p / "reviews" / "guideline-checklist-manuscript.json")
        legacy.write_text(json.dumps({"guideline": "STROBE", "items": {}}), encoding="utf-8")
        self.assertEqual(gc.checklist_path(self.p, "manuscript"), legacy)

    def test_na_reason_must_be_a_string(self):
        self.write(**{"1a": {"status": "na", "reason": 5}})
        self.assertTrue(any(l == "block" and "item 1a" in m for l, _, m in gc.check(self.p)))

    def test_table_without_line_and_wrong_guideline(self):
        self.write(**{"4": {"status": "partial", "file": REL, "reason": "x"}})
        out = self.cli("--table")[1]
        self.assertNotIn("None", out)
        self.assertIn(f"| {REL} |", out)
        self.write(guideline="CONSORT-2025")
        code, _, err = self.cli("--table")
        self.assertEqual(code, 2)
        self.assertIn("CONSORT-2025", err)



P5_LISTS = {
    "CARE": ("2013",
             ["1", "2", "3a", "3b", "3c", "3d", "4", "5a", "5b", "5c", "5d", "6", "7", "8a", "8b", "8c", "8d",
              "9a", "9b", "9c", "10a", "10b", "10c", "10d", "11a", "11b", "11c", "11d", "12", "13"],
             {"Title", "Key words", "Abstract", "Introduction", "Patient information", "Clinical findings", "Timeline",
              "Diagnostic assessment", "Therapeutic intervention", "Follow-up and outcomes", "Discussion",
              "Patient perspective", "Informed consent"}),
    "PRISMA-2020": ("2020",
                    ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10a", "10b", "11", "12", "13a", "13b", "13c", "13d",
                     "13e", "13f", "14", "15", "16a", "16b", "17", "18", "19", "20a", "20b", "20c", "20d", "21", "22",
                     "23a", "23b", "23c", "23d", "24a", "24b", "24c", "25", "26", "27"],
                    {"Title", "Abstract", "Introduction", "Methods", "Results", "Discussion", "Other information"}),
    "PRISMA-ScR": ("2018", [str(i) for i in range(1, 23)],
                   {"Title", "Abstract", "Introduction", "Methods", "Results", "Discussion", "Funding"}),
    "SANRA": ("2019", [str(i) for i in range(1, 7)], {"Quality item"}),
}
P5_RECORDS = {"CARE": "gagnier2013", "PRISMA-2020": "page2021", "PRISMA-ScR": "tricco2018", "SANRA": "baethge2019"}


class TestP5ItemLists(unittest.TestCase):
    def setUp(self):
        self.t = Path(tempfile.mkdtemp())
        self.p = init_project.create(self.t / "p", "T", "systematic-review", "systematic-review", "en", "en")

    def tearDown(self):
        shutil.rmtree(self.t, ignore_errors=True)

    def test_item_lists_load_with_official_ids(self):
        for code, (version, ids, sections) in P5_LISTS.items():
            with self.subTest(guideline=code):
                data = gc.load_items(code)
                self.assertEqual((data["code"], data["version"]), (code, version))
                self.assertEqual([i["id"] for i in data["items"]], ids)
                for it in data["items"]:
                    self.assertIn(it["section"], sections)
                    self.assertTrue(0 < len(it["text"].split()) <= 12, it)
                    self.assertTrue(it["text"].endswith("."), it)

    def test_guideline_records_are_verified(self):
        lib = json.loads((gc.ITEMS_DIR.parent / "guidelines.json").read_text(encoding="utf-8"))
        by = {r["id"]: r for r in lib["references"]}
        index = (gc.ITEMS_DIR.parent / "index.md").read_text(encoding="utf-8")
        for code, rid in P5_RECORDS.items():
            with self.subTest(guideline=code):
                self.assertTrue(str(by[rid].get("verified_by", "")).endswith("VERIFIED"))
                self.assertIn(f"| {code} |", index)
                self.assertIn(f"items/{code}.json", index)

    def test_checklist_runs_for_each_p5_guideline(self):
        for code, (_, ids, _) in P5_LISTS.items():
            with self.subTest(guideline=code):
                path = self.p / "reviews" / f"cl-{code}.json"
                items = {i: {"status": "na", "reason": "fixture"} for i in ids}
                path.write_text(json.dumps({"guideline": code, "items": items}), encoding="utf-8")
                self.assertEqual(gc.check(self.p, guideline=code, checklist_path=path), [])
                del items[ids[-1]]
                path.write_text(json.dumps({"guideline": code, "items": items}), encoding="utf-8")
                found = gc.check(self.p, guideline=code, checklist_path=path)
                self.assertTrue(any(s == "block" and f"item {ids[-1]}" in m for s, _, m in found), found)

    def test_notice_rows(self):
        notice = (_paths.ROOT / "NOTICE.md").read_text(encoding="utf-8")
        for code in P5_LISTS:
            self.assertIn(f"`references/reporting-guidelines/items/{code}.json`", notice)
