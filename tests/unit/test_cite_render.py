import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import _paths

SCRIPT = _paths.ORCH_SCRIPTS / "cite_render.py"

EIGHT = ["A1 X", "A2 X", "A3 X", "A4 X", "A5 X", "A6 X", "A7 X", "A8 X"]
REFS = [
    {"id": "a", "title": "Alpha trial", "authors": ["Smith J", "Lee K"], "journal": "BMJ", "year": 2024,
     "volume": "12", "issue": "3", "pages": "100-9", "doi": "10.1/a", "pmid": "111"},
    {"id": "b", "title": "Beta cohort", "authors": ["Tran H"], "journal": "Lancet", "year": 2023,
     "volume": "5", "issue": "", "pages": "1-2"},
    {"id": "c", "title": "Gamma review", "authors": EIGHT, "journal": "JAMA", "year": 2022,
     "volume": "9", "issue": "1", "pages": "5-6"},
    {"id": "d", "title": "Delta note", "authors": ["Nguyen P"], "journal": "Cureus", "year": 2021},
    {"id": "e", "title": "Epsilon", "authors": ["Pham Q"], "year": 2020},
    {"id": "f", "title": "Zeta unused", "authors": ["Le Z"], "year": 2019},
    {"id": "r", "title": "Retracted one", "authors": ["Bad B"], "year": 2018, "retracted": True},
]


class TestCiteRender(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.root = Path(self._td.name)
        (self.root / "ledgers").mkdir()
        self.write_refs(REFS)
        self.out = self.root / "out.md"

    def write_refs(self, refs):
        (self.root / "ledgers" / "references.json").write_text(
            json.dumps({"references": refs}), encoding="utf-8")

    def run_cr(self, draft_text, *extra, draft_name="draft.md"):
        if draft_text is not None:
            (self.root / "draft.md").write_bytes(draft_text.encode("utf-8"))
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(self.root), str(self.root / draft_name), str(self.out), *extra],
            capture_output=True, text=True, encoding="utf-8")

    def output(self):
        return self.out.read_bytes().decode("utf-8")

    def test_order_of_first_appearance(self):
        p = self.run_cr("One [@b]. Two [@a]. Again [@b].\n")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(self.output(), "One [1]. Two [2]. Again [1].\n")

    def test_group_compression(self):
        p = self.run_cr("X [@a; @b; @c] Y [@a; @b] Z [@c; @a; @b; @d; @e] W [@d; @a]\n")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(self.output(), "X [1–3] Y [1,2] Z [1–5] W [1,4]\n")

    def test_compress_with_gap(self):
        self.run_cr("[@a] [@b] [@c] [@d] [@e] then [@a; @b; @c; @e]\n")
        self.assertEqual(self.output().splitlines()[0], "[1] [2] [3] [4] [5] then [1–3,5]")

    def test_start_marker(self):
        draft = "Table [@a; @b]\n## 1.6 Review\nText [@c] [@a]\n"
        p = self.run_cr(draft, "--start-marker", "## 1.6")
        self.assertEqual(p.returncode, 0, p.stderr)
        # review ids first (c=1, a=2); the id seen only before the marker (b) comes last
        self.assertEqual(self.output(), "Table [2,3]\n## 1.6 Review\nText [1] [2]\n")

    def test_start_marker_missing_exit_2(self):
        p = self.run_cr("Text [@a]\n", "--start-marker", "## nowhere")
        self.assertEqual(p.returncode, 2)
        self.assertFalse(self.out.exists())

    def test_reference_list(self):
        p = self.run_cr("A [@a] B [@c] C [@d] D [@e] E [@b]\n\n{REFERENCES}\n")
        self.assertEqual(p.returncode, 0, p.stderr)
        lines = self.output().splitlines()
        self.assertEqual(lines[2], "1. Smith J, Lee K. Alpha trial. BMJ. 2024;12(3):100-9. doi:10.1/a. PMID: 111.")
        self.assertEqual(lines[3], "2. A1 X, A2 X, A3 X, A4 X, A5 X, A6 X, et al. Gamma review. JAMA. 2022;9(1):5-6.")
        self.assertNotIn("A7 X", self.output())
        self.assertEqual(lines[4], "3. Nguyen P. Delta note. Cureus. 2021.")
        self.assertEqual(lines[5], "4. Pham Q. Epsilon. 2020.")
        self.assertEqual(lines[6], "5. Tran H. Beta cohort. Lancet. 2023;5:1-2.")

    def test_exactly_six_authors_no_et_al(self):
        self.write_refs([dict(REFS[2], authors=EIGHT[:6])])
        self.run_cr("[@c]\n{REFERENCES}\n")
        self.assertNotIn("et al.", self.output())

    def test_no_stray_punctuation(self):
        self.run_cr("[@d]\n{REFERENCES}\n")
        entry = self.output().splitlines()[1]
        self.assertEqual(entry, "1. Nguyen P. Delta note. Cureus. 2021.")
        for bad in (";", ":", "()", " ."):
            self.assertNotIn(bad, entry)

    def test_missing_id(self):
        p = self.run_cr("Cited [@a] and [@ghost].\n")
        self.assertEqual(p.returncode, 1)
        self.assertIn("E-REF ghost: not in references.json", p.stdout)
        self.assertFalse(self.out.exists())

    def test_retracted_id(self):
        p = self.run_cr("Cited [@r].\n")
        self.assertEqual(p.returncode, 1)
        self.assertIn("E-REF r: retracted", p.stdout)
        self.assertFalse(self.out.exists())

    def test_unused_reported(self):
        p = self.run_cr("Only [@a].\n")
        self.assertEqual(p.returncode, 0)
        self.assertIn("1 references numbered; unused: b, c, d, e, f, r", p.stdout)

    def test_no_unused(self):
        self.write_refs([REFS[0]])
        p = self.run_cr("[@a]\n")
        self.assertIn("unused: none", p.stdout)

    def test_missing_draft_exit_2(self):
        p = self.run_cr(None, draft_name="nope.md")
        self.assertEqual(p.returncode, 2)
        self.assertTrue(p.stderr)
        self.assertFalse(self.out.exists())

    def test_bad_ledger_json_exit_2(self):
        (self.root / "ledgers" / "references.json").write_text("{not json", encoding="utf-8")
        p = self.run_cr("[@a]\n")
        self.assertEqual(p.returncode, 2)

    def test_non_citation_brackets_untouched_and_crlf_kept(self):
        self.run_cr("See [link](http://x) and [@a].\r\n")
        self.assertEqual(self.output(), "See [link](http://x) and [1].\r\n")


if __name__ == "__main__":
    unittest.main()
