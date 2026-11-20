import json
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
import init_project
from crolib import ledgers


class TestInitProject(unittest.TestCase):
    def test_creates_full_skeleton(self):
        with tempfile.TemporaryDirectory() as t:
            dest = Path(t) / "pmos-study"
            init_project.create(dest, "Lifestyle in PMOS", "thesis-masters", "rct", "vi", "vi")
            for d in ["00_inputs", "01_question", "02_evidence", "03_protocol", "04_data",
                      "05_analysis", "06_writing", "07_present", "ledgers", "gates", "reviews", "out"]:
                self.assertTrue((dest / d).is_dir(), d)
            y = (dest / "project.yaml").read_text(encoding="utf-8")
            self.assertIn('title: "Lifestyle in PMOS"', y)
            self.assertIn("reporting_guideline: CONSORT-2025", y)
            self.assertIn("output: vi", y)
            self.assertIn("| 1 Question |", (dest / "STATUS.md").read_text(encoding="utf-8"))
            self.assertEqual(ledgers.check_project(dest), [])
            self.assertEqual(json.loads((dest / "gates" / "state.json").read_text(encoding="utf-8")), {})

    def test_refuses_existing_project(self):
        with tempfile.TemporaryDirectory() as t:
            dest = Path(t) / "p"
            init_project.create(dest, "A", "manuscript", "cohort", "en", "vi")
            with self.assertRaises(FileExistsError):
                init_project.create(dest, "A", "manuscript", "cohort", "en", "vi")

    def test_rejects_unknown_design(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):
                init_project.create(Path(t) / "p", "A", "manuscript", "astrology", "en", "en")

    def test_guideline_map_covers_all_designs(self):
        for d in init_project.DESIGNS:
            self.assertIn(d, init_project.GUIDELINE_BY_DESIGN)


if __name__ == "__main__":
    unittest.main()
