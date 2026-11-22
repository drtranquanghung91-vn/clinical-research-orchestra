import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
from crolib import projectcfg
from p5_helpers import case_project, review_project


class TestProjectcfgLists(unittest.TestCase):
    def test_parse_list_and_get(self):
        self.assertEqual(projectcfg.parse_list("[Reviewer A, 'Reviewer B']"), ["Reviewer A", "Reviewer B"])
        for empty in ("", "[]", "null", "~"):
            self.assertEqual(projectcfg.parse_list(empty), [])
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / "project.yaml").write_text("tools:\n  rscript: null\ntarget:\n  journal_style: bmj\n",
                                                  encoding="utf-8")
            self.assertIsNone(projectcfg.get(Path(t), "tools.rscript"))
            self.assertEqual(projectcfg.get(Path(t), "target.journal_style"), "bmj")
            self.assertEqual(projectcfg.get(Path(t), "missing.key", "x"), "x")


class TestP5Helpers(unittest.TestCase):
    def test_review_and_case_projects(self):
        with tempfile.TemporaryDirectory() as t:
            p = review_project(Path(t))
            self.assertTrue((p / "03_protocol" / "sr-protocol.md").exists())
            rev = projectcfg.read_project_yaml(p).get("review", {})
            self.assertEqual(projectcfg.parse_list(rev.get("reviewers", "")), ["Reviewer A", "Reviewer B"])
            c = case_project(Path(t))
            self.assertTrue((c / "01_case").is_dir())


if __name__ == "__main__":
    unittest.main()
