import unittest

import _paths  # noqa: F401
from _paths import ROOT
import lint_skills

AGENTS = ROOT / "plugins" / "orchestra" / "agents"
SCORED = {"citation-verifier": ("reviews/citation-verifier-<d>.md", ['"citations"']),
          "statistical-reviewer": ("reviews/statistical-reviewer-<d>.md", ['"statistics"']),
          "reporting-guideline-checker": ("reviews/reporting-guideline-checker-<d>.md", ['"guideline"']),
          "scientific-editor": ("reviews/scientific-editor-<d>.md", ['"structure"', '"claim_scope"', '"limitations"']),
          "consistency-auditor": ("reviews/consistency-<d>.md", ['"consistency"'])}


class TestAgents(unittest.TestCase):
    def load(self, name):
        return lint_skills.parse_frontmatter((AGENTS / f"{name}.md").read_text(encoding="utf-8"))

    def test_every_agent_is_read_only_with_the_report_shape(self):
        names = sorted(p.stem for p in AGENTS.glob("*.md"))
        self.assertEqual(names, sorted(list(SCORED) + ["committee-simulator"]))
        for name in names:
            fm, body = self.load(name)
            with self.subTest(agent=name):
                self.assertEqual(fm["tools"], "Read, Grep, Glob, Bash")
                self.assertEqual(fm["disallowedTools"], "Write, Edit, NotebookEdit")
                self.assertIn("in your reply", body)
                self.assertIn("never write or edit a file", body.lower())
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

    def test_p5_duties(self):
        stat = self.load("statistical-reviewer")[1]
        for s in ("meta.py", "prediction interval", "I²", "τ²", "Egger", "k ≥ 10", "S-HET", "S-META", "S-SMALL",
                  "DEVIATION", "sr-protocol.md"):
            self.assertIn(s, stat)
        rg = self.load("reporting-guideline-checker")
        for s in ("CARE", "PRISMA-2020", "PRISMA-ScR", "SANRA"):
            self.assertIn(s, rg[1])
        for name in ("citation-verifier", "statistical-reviewer", "reporting-guideline-checker", "scientific-editor"):
            self.assertIn("`case-report` or `review`", self.load(name)[1])


SKILLS = ROOT / "plugins" / "orchestra" / "skills"
ROUND = ROOT / "plugins" / "orchestra" / "references" / "writing" / "review-round.md"


class TestReviewRound(unittest.TestCase):
    def skill(self, name):
        return lint_skills.parse_frontmatter((SKILLS / name / "SKILL.md").read_text(encoding="utf-8"))[1]

    def test_reference_holds_the_procedure(self):
        text = ROUND.read_text(encoding="utf-8")
        for s in ("reviews/<agent>-<d>.md", "reviews/consistency-<d>.md", "reviews/guideline-checklist-<d>.json",
                  "Exactly one", "At most 3 rounds", "--stdin", "never edit it", "NEW-ANALYSIS:",
                  "never rerun all five"):
            self.assertIn(s, text)

    def test_writing_skills_point_to_it(self):
        for name, d in (("thesis-writing", "thesis"), ("manuscript-writing", "manuscript"),
                        ("case-report", "case-report"), ("systematic-review", "review")):
            body = self.skill(name)
            with self.subTest(skill=name):
                self.assertIn("references/writing/review-round.md", body)
                self.assertIn(f"reviews/<agent>-{d}.md", body)
                self.assertIn(f"worklog.py\" score . {d} --round N", body)
                self.assertLessEqual(len(body.split()), 500)
        self.assertIn("never edited", self.skill("thesis-writing"))
        self.assertIn("each followed by its result id", self.skill("systematic-review"))

    def test_poster_and_defense_rules(self):
        poster, defense = self.skill("research-poster"), self.skill("defense-prep")
        for s in ("Required:", "reviews/committee-poster.md", "whether `committee-simulator` ran", "Read tool"):
            self.assertIn(s, poster)
        for s in ("without the author's yes to that exact change", "save its reply to `reviews/committee-defense.md`"):
            self.assertIn(s, defense)


if __name__ == "__main__":
    unittest.main()
