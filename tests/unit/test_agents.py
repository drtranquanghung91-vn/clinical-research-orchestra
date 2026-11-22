import unittest

import _paths  # noqa: F401
from _paths import ROOT
import lint_skills

AGENTS = ROOT / "plugins" / "orchestra" / "agents"
SCORED = {"citation-verifier": ("reviews/citation-verifier.md", ['"citations"']),
          "statistical-reviewer": ("reviews/statistical-reviewer.md", ['"statistics"']),
          "reporting-guideline-checker": ("reviews/reporting-guideline-checker.md", ['"guideline"']),
          "scientific-editor": ("reviews/scientific-editor.md", ['"structure"', '"claim_scope"', '"limitations"']),
          "consistency-auditor": ("reviews/consistency.md", ['"consistency"'])}


class TestAgents(unittest.TestCase):
    def load(self, name):
        return lint_skills.parse_frontmatter((AGENTS / f"{name}.md").read_text(encoding="utf-8"))

    def test_every_agent_is_read_only_with_the_report_shape(self):
        names = sorted(p.stem for p in AGENTS.glob("*.md"))
        self.assertEqual(names, sorted(list(SCORED) + ["committee-simulator"]))
        for name in names:
            fm, body = self.load(name)
            with self.subTest(agent=name):
                self.assertEqual(fm["tools"], "Read, Grep, Glob, Bash, Write")
                self.assertEqual(fm["disallowedTools"], "Edit, NotebookEdit")
                self.assertEqual(fm["model"], "sonnet")
                self.assertTrue(fm["description"].startswith("Use when"))
                for s in ("STATUS", "FINDINGS", "GAPS", "CONFLICTS", "reviews/"):
                    self.assertIn(s, body)
                self.assertLessEqual(len(body.split()), 500)

    def test_reviewers_write_digest_and_scores(self):
        for name, (report, keys) in SCORED.items():
            _, body = self.load(name)
            with self.subTest(agent=name):
                self.assertIn(report, body)
                self.assertIn('worklog.py" digest', body)
                self.assertIn("drafts-digest:", body)
                self.assertIn("```scores", body)
                self.assertIn('"deliverable"', body)
                for k in keys:
                    self.assertIn(k, body)
                self.assertIn("references/writing/rubric.md", body)

    def test_specific_duties(self):
        self.assertIn("guideline_checklist.py", self.load("reporting-guideline-checker")[1])
        self.assertIn("reviews/guideline-checklist-<d>.json", self.load("reporting-guideline-checker")[1])
        self.assertIn("never a summed score", self.load("reporting-guideline-checker")[1].lower())
        self.assertIn("analysis_plan.py", self.load("statistical-reviewer")[1])
        self.assertIn("NEW-ANALYSIS:", self.load("statistical-reviewer")[1])
        self.assertIn("abstract", self.load("citation-verifier")[1])
        self.assertIn("limitations", self.load("scientific-editor")[1].lower())


if __name__ == "__main__":
    unittest.main()
