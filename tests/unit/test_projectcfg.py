import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
from crolib import projectcfg

YAML = '''title: "Demo"
design: cohort
language:
  chat: vi
  output: vi
docx:
  font: "Arial"
  size_pt: 12
'''


class TestProjectcfg(unittest.TestCase):
    def test_read(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "project.yaml").write_text(YAML, encoding="utf-8")
            cfg = projectcfg.read_project_yaml(Path(d))
            self.assertEqual(cfg["design"], "cohort")
            self.assertEqual(cfg["docx"]["font"], "Arial")
            self.assertEqual(projectcfg.output_lang(Path(d)), "vi")

    def test_missing_file_defaults(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(projectcfg.output_lang(Path(d)), "en")

    def test_inline_comment_stripped_but_quoted_hash_kept(self):
        text = 'title: "Study #2"\nlanguage:\n  output: vi  # chosen by author\n'
        with tempfile.TemporaryDirectory() as d:
            Path(d, "project.yaml").write_text(text, encoding="utf-8")
            cfg = projectcfg.read_project_yaml(Path(d))
            self.assertEqual(cfg["title"], "Study #2")
            self.assertEqual(projectcfg.output_lang(Path(d)), "vi")

    def test_bom_is_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "project.yaml").write_text("﻿" + YAML, encoding="utf-8")
            cfg = projectcfg.read_project_yaml(Path(d))
            self.assertEqual(cfg["title"], "Demo")
            self.assertEqual(projectcfg.output_lang(Path(d)), "vi")
