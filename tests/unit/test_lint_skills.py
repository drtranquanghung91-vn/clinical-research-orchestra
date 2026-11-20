import tempfile
import unittest
from pathlib import Path

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
description: Use when a user asks for X. Triggers: "x", "câu hỏi x".
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


if __name__ == "__main__":
    unittest.main()
