import json
import shutil
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
from _paths import ROOT
import autorater

FENCE = "`" * 3


def result_line(text, cost=0.5, turns=3):
    return json.dumps({"type": "result", "result": text, "total_cost_usd": cost, "num_turns": turns}) + "\n"


def fake_claude(args, cwd, out):
    cwd = Path(cwd)
    if "--plugin-dir" in args:                       # a side run: old or new plugins
        side = Path(args[args.index("--plugin-dir") + 1]).parent.name
        (cwd / "06_writing").mkdir(parents=True, exist_ok=True)
        (cwd / "06_writing" / "x.md").write_text(f"draft by {side}\n", encoding="utf-8")
        tool = {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash",
                                                              "input": {"command": "python meta.py . run"}}]}}
        Path(out).write_text(json.dumps(tool) + "\n" + result_line(f"answer {side}"), encoding="utf-8")
        return 0
    text = (cwd / "materials.md").read_text(encoding="utf-8")       # the judge: prefers the "new" attempt
    winner = "A" if text.index("answer new") < text.index("# Attempt B") else "B"
    answer = f'{FENCE}json\n{{"winner": "{winner}", "reasons": "fixture", "rubric": []}}\n{FENCE}'
    Path(out).write_text(result_line(answer, cost=0.25, turns=1), encoding="utf-8")
    return 0


class TestAutorater(unittest.TestCase):
    def setUp(self):
        self.t = Path(tempfile.mkdtemp())
        self.saved = (autorater.run_claude, autorater.extract_base, autorater.copy_head, autorater.git)
        autorater.run_claude = fake_claude
        autorater.extract_base = lambda ref, dest: dest
        autorater.copy_head = lambda dest: dest
        autorater.git = lambda *a: b"abc1234def\n" if a[0] == "rev-parse" else b""

    def tearDown(self):
        autorater.run_claude, autorater.extract_base, autorater.copy_head, autorater.git = self.saved
        shutil.rmtree(self.t, ignore_errors=True)

    def test_verdict_needs_both_orders_to_agree(self):
        v = autorater.verdict
        self.assertEqual(v("B", "A"), "new")
        self.assertEqual(v("A", "B"), "old")
        self.assertEqual(v("tie", "tie"), "tie")
        for w1, w2 in (("A", "A"), ("B", "B"), ("tie", "A"), ("B", None), (None, None)):
            self.assertEqual(v(w1, w2), "inconsistent", (w1, w2))

    def test_parse_judgement(self):
        good = f'Reasoning first.\n{FENCE}json\n{{"winner": "B", "reasons": "r", "rubric": []}}\n{FENCE}\n'
        self.assertEqual(autorater.parse_judgement(good)["winner"], "B")
        self.assertEqual(autorater.parse_judgement('{"winner": "tie", "reasons": ""}')["winner"], "tie")
        self.assertIsNone(autorater.parse_judgement('{"winner": "C"}'))
        self.assertIsNone(autorater.parse_judgement("no json here"))

    def test_starter_cases_are_complete(self):
        self.assertEqual(autorater.list_cases(), ["case-anonymisation", "sr-pooling", "thesis-discussion-overclaim"])
        for name in autorater.list_cases():
            c = autorater.load_case(name)
            self.assertTrue(c["prompt"] and c["rubric"] and c["skills"] and c["allowed_tools"], name)
            self.assertTrue((ROOT / c["fixture"]).is_dir(), name)
        self.assertEqual(autorater.list_cases("thesis-writing"), ["thesis-discussion-overclaim"])
        self.assertEqual(autorater.list_cases("systematic-review"), ["sr-pooling"])
        with self.assertRaises(autorater.Usage):
            autorater.load_case("no-such-case")

    def test_run_case_with_mocked_claude(self):
        res = autorater.run_case("sr-pooling", "main", results=self.t)
        self.assertEqual(res["verdict"], "new")
        self.assertEqual([j["winner"] for j in res["judgements"]], ["B", "A"])
        self.assertEqual(res["runs"]["old"]["changed"], ["06_writing/x.md"])
        self.assertEqual((res["head"], res["dirty"], res["base"]), ("abc1234def", False, "main"))
        self.assertAlmostEqual(res["cost_usd"], 1.5)
        saved = json.loads(Path(res["file"]).read_text(encoding="utf-8"))
        self.assertEqual(saved["verdict"], "new")
        self.assertIn("| sr-pooling |", autorater.report(self.t))

    def test_cli(self):
        self.assertEqual(autorater.main(["list", "--skill", "case-report"]), 0)
        self.assertEqual(autorater.main(["run", "nope", "--base", "main", "--results", str(self.t)]), 2)
        self.assertEqual(autorater.main(["report", "--results", str(self.t)]), 0)

    def test_results_ignored_and_agents_rule(self):
        self.assertIn("evals/results/", (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines())
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("tools/autorater.py list --skill", agents)
        self.assertIn("never runs in CI", agents)


if __name__ == "__main__":
    unittest.main()
