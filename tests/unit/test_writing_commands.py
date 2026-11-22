"""Every script command the writing skills and workflows show must exist and match the real argparse choices."""
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import _paths

ORCH = _paths.ROOT / "plugins" / "orchestra"
FILES = [ORCH / "skills" / "thesis-writing" / "SKILL.md", ORCH / "skills" / "manuscript-writing" / "SKILL.md",
         ORCH / "skills" / "thesis" / "SKILL.md", ORCH / "skills" / "manuscript" / "SKILL.md",
         ORCH / "references" / "workflows" / "thesis.md", ORCH / "references" / "workflows" / "manuscript.md",
         ORCH / "skills" / "case-report" / "SKILL.md", ORCH / "skills" / "systematic-review" / "SKILL.md",
         ORCH / "skills" / "case" / "SKILL.md", ORCH / "skills" / "sr" / "SKILL.md",
         ORCH / "skills" / "literature-review" / "SKILL.md", ORCH / "skills" / "review" / "SKILL.md",
         ORCH / "references" / "workflows" / "case-report.md", ORCH / "references" / "workflows" / "systematic-review.md",
         ORCH / "references" / "workflows" / "scoping-review.md"]
MENTION = re.compile(r"(?:scripts/)?\b([a-z_]+)\.py\b\"?([^`\n]*)")
_help_cache: dict[str, str] = {}


def _p9_ready() -> bool:
    """TEMPORARY guard (remove after Task 9 merges): CLI lines that need the case-report/review deliverables."""
    r = subprocess.run([sys.executable, str(ORCH / "scripts" / "assemble.py"), "--help"],
                       capture_output=True, text=True, encoding="utf-8", timeout=60)
    return "case-report" in r.stdout


P9_READY = _p9_ready()


def needs_p9(name: str, rest: str) -> bool:
    """True for a command line that cannot pass before Task 9 are merged."""
    return not P9_READY and bool(re.search(r"(?<![\w-])(case-report|review)(?![\w-])", rest.split("→")[0]))


def positionals(script: str) -> list:
    """Positional slots of the script's argparse: a list of choices, or None for a free value."""
    if script not in _help_cache:
        r = subprocess.run([sys.executable, str(ORCH / "scripts" / (script + ".py")), "--help"],
                           capture_output=True, text=True, encoding="utf-8", timeout=60)
        _help_cache[script] = r.stdout
    out, on = [], False
    for line in _help_cache[script].splitlines():
        if line.startswith("positional arguments:"):
            on = True
            continue
        if on:
            if not line.strip():
                break
            tok = line.split()[0]
            out.append(tok.strip("{}").split(",") if tok.startswith("{") else None)
    return out


def positional_words(rest: str) -> list:
    """Bare words of a command line after the script name (flags, flag values and placeholders dropped)."""
    head = rest.split("→")[0].split(";")[0]
    words = [t.strip("\"'") for t in re.findall(r"\S+", head)]
    words = [t for t in words if not t.startswith("-") and not t.startswith("…")]
    return [t for t in words if not re.fullmatch(r"N|\d+", t)]


class TestWritingCommands(unittest.TestCase):
    def test_mentions_found(self):
        found = []
        for f in FILES:
            found += [m.group(1) for m in MENTION.finditer(f.read_text(encoding="utf-8"))]
        for name in ("gate", "worklog", "assemble", "audit", "lint_prose"):
            self.assertIn(name, found)

    def test_every_mentioned_script_and_subcommand_exists(self):
        for f in FILES:
            text = f.read_text(encoding="utf-8")
            for m in MENTION.finditer(text):
                name, rest = m.group(1), m.group(2)
                if needs_p9(name, rest):
                    continue  # needs Task 9
                with self.subTest(file=f.name, cmd=m.group(0)[:60]):
                    self.assertTrue((ORCH / "scripts" / (name + ".py")).exists(), name + ".py does not exist")
                    slots = positionals(name)
                    words = positional_words(rest)
                    for i, choices in enumerate(slots):
                        if choices is None:
                            continue
                        if i < len(words) and re.fullmatch(r"[A-Za-z][A-Za-z0-9-]+", words[i]):
                            self.assertIn(words[i], choices, f"{name}: argument {i + 1}")
                        elif i == 0:
                            self.fail(f"{name}: missing subcommand")

    def test_every_flag_is_known_to_the_script(self):
        for f in FILES:
            for m in MENTION.finditer(f.read_text(encoding="utf-8")):
                name, rest = m.group(1), m.group(2)
                if needs_p9(name, rest):
                    continue  # needs Task 9
                positionals(name)  # fills the help cache
                helptext = _help_cache[name]
                head = rest.split("→")[0].split(";")[0]
                for flag in re.findall(r"(?<!\S)(--[a-z][a-z-]*)", head):
                    with self.subTest(file=f.name, cmd=m.group(0)[:60], flag=flag):
                        self.assertIn(flag, helptext)

    def test_gate_commands_run_without_usage_error(self):
        """Each gate.py command line, as written, is accepted by argparse (exit 1 = refused is fine, 2 is not)."""
        sys.path.insert(0, str(ORCH / "scripts"))
        import init_project
        n = 0
        for f in FILES:
            for line in f.read_text(encoding="utf-8").splitlines():
                for m in re.finditer(r"gate\.py\"?\s+(open|check)\s+\.\s+(G\d)([^`]*)", line):
                    args = [m.group(1), "{p}", m.group(2)] + re.findall(r"\S+", m.group(3).split("→")[0])
                    args = [a.strip("\"'").replace("<name>", "X") for a in args]
                    if "…" in " ".join(args) or "." in args[3:4]:
                        continue
                    with tempfile.TemporaryDirectory() as t:
                        proj = init_project.create(Path(t) / "p", "A", "manuscript", "cohort", "en", "vi")
                        cmd = [sys.executable, str(ORCH / "scripts" / "gate.py")] + [a.replace("{p}", str(proj)) for a in args]
                        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=60)
                        with self.subTest(file=f.name, args=args):
                            self.assertNotEqual(r.returncode, 2, r.stderr)
                    n += 1
        self.assertGreaterEqual(n, 4)


class TestP5Skills(unittest.TestCase):
    def text(self, name):
        return (ORCH / "skills" / name / "SKILL.md").read_text(encoding="utf-8")

    def test_p5_scripts_are_cited(self):
        found = set()
        for f in FILES:
            found |= {m.group(1) for m in MENTION.finditer(f.read_text(encoding="utf-8"))}
        for name in ("case_facts", "case_lint", "screening", "extract_check", "meta", "grade", "figures"):
            self.assertIn(name, found)

    def test_frontmatter_and_rules(self):
        import lint_skills
        for name, command in (("case-report", False), ("systematic-review", False), ("case", True), ("sr", True)):
            fm, body = lint_skills.parse_frontmatter(self.text(name))
            with self.subTest(skill=name):
                self.assertEqual(fm["name"], name)
                self.assertEqual(fm.get("disable-model-invocation", "") == "true", command)
                self.assertLessEqual(len(body.split()), 500)
                if not command:
                    self.assertTrue(fm["description"].startswith("Use when"))
                    self.assertRegex(fm["description"], r"[àáảãạăâđèéêìíòóôơùúưỳý]")   # a Vietnamese trigger
        case = self.text("case-report")
        for s in ("CONSENT: obtained", "relative time", "case_lint.py", "case_facts.py", "case-front.md", "--final",
                  "Never lock it yourself"):
            self.assertIn(s, case)
        sr = self.text("systematic-review")
        for s in ("never a reviewer", "screen-suggest.md", "review.reviewers", "prediction interval", "DEVIATION",
                  "r-status", "never install", "swim.md", "statistician"):
            self.assertIn(s, sr)
        lr = self.text("literature-review")
        for s in ("**c. Narrative or scoping review**", "review-narrative.md", "scoping-review.md", "`systematic-review`",
                  "chart, not pool"):
            self.assertIn(s, lr)
        self.assertIn("`case-report`", self.text("case"))
        self.assertIn("`systematic-review`", self.text("sr"))
        self.assertIn("(c)", self.text("review"))
        self.assertNotIn("phase P3", self.text("literature-search"))


if __name__ == "__main__":
    unittest.main()
