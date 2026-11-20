import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import _paths  # noqa: F401
import lint_skills


def write_skill(root: Path, folder: str, text: str) -> Path:
    d = root / folder
    d.mkdir(parents=True)
    p = d / "SKILL.md"
    p.write_text(text, encoding="utf-8")
    return p


GOOD = """---
name: good-skill
description: 'Use when a user asks for X. Triggers: "x", "câu hỏi x".'
---

# Good skill

Body text.
"""


class TestLintSkills(unittest.TestCase):
    def test_parse_frontmatter_block_scalar(self):
        fm, body = lint_skills.parse_frontmatter(
            "---\nname: a\ndescription: |\n  Use when one.\n  Two.\n---\nBody\n")
        self.assertEqual(fm["name"], "a")
        self.assertTrue(fm["description"].startswith("Use when one."))
        self.assertIn("Two.", fm["description"])
        self.assertEqual(body.strip(), "Body")

    def test_good_skill_has_no_errors(self):
        with tempfile.TemporaryDirectory() as t:
            p = write_skill(Path(t), "good-skill", GOOD)
            self.assertEqual(lint_skills.lint_skill(p), [])

    def test_name_must_equal_folder(self):
        with tempfile.TemporaryDirectory() as t:
            p = write_skill(Path(t), "other-folder", GOOD)
            self.assertTrue(any("name" in e for e in lint_skills.lint_skill(p)))

    def test_model_invoked_description_must_start_use_when(self):
        with tempfile.TemporaryDirectory() as t:
            p = write_skill(Path(t), "s", "---\nname: s\ndescription: Helps with things.\n---\nBody\n")
            self.assertTrue(any("Use when" in e for e in lint_skills.lint_skill(p)))

    def test_user_invoked_skill_may_use_any_description(self):
        with tempfile.TemporaryDirectory() as t:
            p = write_skill(Path(t), "s", "---\nname: s\ndescription: Start a project.\n"
                                          "disable-model-invocation: true\n---\nBody\n")
            self.assertEqual(lint_skills.lint_skill(p), [])

    def test_body_over_500_words_fails(self):
        with tempfile.TemporaryDirectory() as t:
            p = write_skill(Path(t), "good-skill", GOOD + ("word " * 501))
            self.assertTrue(any("500" in e for e in lint_skills.lint_skill(p)))

    def test_missing_frontmatter_fails(self):
        with tempfile.TemporaryDirectory() as t:
            p = write_skill(Path(t), "s", "# No frontmatter\n")
            self.assertTrue(lint_skills.lint_skill(p))

    # I1: values Claude Code's YAML parser rejects must fail the lint (own check, PyYAML not needed)
    def _lint_desc(self, desc_line: str) -> list:
        with tempfile.TemporaryDirectory() as t, mock.patch.object(lint_skills, "yaml", None):
            p = write_skill(Path(t), "s", f"---\nname: s\n{desc_line}\n---\nBody\n")
            return lint_skills.lint_skill(p)

    def test_unquoted_colon_space_is_invalid_yaml(self):
        errs = self._lint_desc('description: Use when a user asks. Triggers: "PICO", "PECO".')
        self.assertTrue(any("frontmatter value for 'description' is not valid plain YAML; wrap it in single quotes"
                            in e for e in errs), errs)

    def test_unquoted_space_hash_is_invalid_yaml(self):
        errs = self._lint_desc("description: Use when step #2 fails")
        self.assertTrue(any("not valid plain YAML" in e for e in errs), errs)

    def test_unquoted_indicator_start_is_invalid_yaml(self):
        for first in ["[", "{", "&", "*", "!", "|", ">", "%", "@", "`"]:
            errs = self._lint_desc(f"description: {first}Use when x")
            self.assertTrue(any("not valid plain YAML" in e for e in errs), (first, errs))

    def test_more_invalid_plain_starts(self):  # R6: rejected without PyYAML too
        for value in ["- Use when x", "? Use when x", ",Use when x", "]Use when x", "}Use when x", "#Use when x"]:
            errs = self._lint_desc(f"description: {value}")
            self.assertTrue(any("not valid plain YAML" in e for e in errs), (value, errs))

    def test_plain_value_starting_with_dash_word_is_fine(self):
        with mock.patch.object(lint_skills, "yaml", None):
            fm, _ = lint_skills.parse_frontmatter("---\nname: s\ndescription: -1 dose, ?maybe\n---\nB\n")
        self.assertEqual(fm["description"], "-1 dose, ?maybe")

    def test_plain_value_without_indicators_is_fine(self):
        self.assertEqual(self._lint_desc("description: Use when x, y or z (ratio 1:2, item#3, 50%)"), [])

    def test_single_quoted_value_is_unquoted(self):
        fm, _ = lint_skills.parse_frontmatter("---\nname: s\ndescription: 'Use when it''s x: \"y\"'\n---\nB\n")
        self.assertEqual(fm["description"], 'Use when it\'s x: "y"')

    def test_double_quoted_value_is_unquoted(self):
        fm, _ = lint_skills.parse_frontmatter('---\nname: s\ndescription: "Use when \\"x\\": y"\n---\nB\n')
        self.assertEqual(fm["description"], 'Use when "x": y')

    def test_lone_quote_inside_single_quotes_is_invalid(self):
        errs = self._lint_desc("description: 'Use when it's x'")
        self.assertTrue(errs, errs)

    def test_pyyaml_error_is_reported(self):
        if lint_skills.yaml is None:
            self.skipTest("PyYAML not installed")
        with tempfile.TemporaryDirectory() as t:
            p = write_skill(Path(t), "s", "---\nname: s\ndescription: 'Use when x'\n  extra\n---\nBody\n")
            errs = lint_skills.lint_skill(p)
        self.assertTrue(any("not valid YAML" in e for e in errs), errs)

    def test_main_no_files_and_no_plugins_folder_returns_2(self):
        with tempfile.TemporaryDirectory() as t:
            err = io.StringIO()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
                self.assertEqual(lint_skills.main([t]), 2)
            self.assertIn("plugins", err.getvalue())

    def test_main_plugins_folder_without_skills_returns_0(self):
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / "plugins").mkdir()
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(lint_skills.main([t]), 0)


if __name__ == "__main__":
    unittest.main()
