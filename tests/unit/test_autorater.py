import contextlib
import io
import json
import re
import shutil
import tempfile
import types
import unittest
from pathlib import Path

import _paths  # noqa: F401
from _paths import ROOT
import autorater

FENCE = "`" * 3


def result_line(text, cost=0.5, turns=3):
    return json.dumps({"type": "result", "result": text, "total_cost_usd": cost, "num_turns": turns}) + "\n"


JUDGE_CALLS = []


SEEN = []


def fake_claude(args, cwd, out, timeout=None):
    cwd = Path(cwd)
    SEEN.append((list(args), timeout))
    if "--plugin-dir" in args:                       # a side run: old or new plugins
        side = Path(args[args.index("--plugin-dir") + 1]).parent.name
        (cwd / "06_writing").mkdir(parents=True, exist_ok=True)
        (cwd / "06_writing" / "x.md").write_text(f"draft by {side}\n", encoding="utf-8")
        tool = {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash",
                                                              "input": {"command": f"python {args[args.index('--plugin-dir') + 1]}/meta.py {cwd} run"}}]}}
        Path(out).write_text(json.dumps(tool) + "\n" + result_line(f"answer {side}"), encoding="utf-8")
        return 0
    text = (cwd / "materials.md").read_text(encoding="utf-8")       # the judge: prefers the "new" attempt
    JUDGE_CALLS.append((cwd, args[1], text))
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

    def test_judge_is_blind_to_old_and_new_paths(self):
        JUDGE_CALLS.clear()
        autorater.run_case("sr-pooling", "main", results=self.t)
        self.assertEqual(len(JUDGE_CALLS), 2)
        tmp = Path(tempfile.gettempdir())
        for cwd, prompt, mats in JUDGE_CALLS:
            rel = cwd.relative_to(tmp)
            self.assertFalse({p.lower() for p in rel.parts} & {"old", "new"}, cwd)
            self.assertNotIn("judge-old", str(cwd))
            self.assertNotRegex(prompt, r"[/\\](old|new)[/\\]")
            self.assertNotRegex(mats, r"[/\\](old|new)[/\\]")
            self.assertNotIn("autorater-sr-pooling", mats)
            self.assertIn("<RUN_A>", mats)
            self.assertIn("<RUN_B>", mats)
            self.assertFalse(cwd.exists(), "judge folder is removed afterwards")

    def test_budget_stops_further_runs(self):
        calls = []
        inner = autorater.run_claude

        def counting(args, cwd, out, timeout=None):
            calls.append(1)
            return inner(args, cwd, out, timeout)

        autorater.run_claude = counting
        res = autorater.run_case("sr-pooling", "main", results=self.t, budget=autorater.Budget(0.4))
        self.assertEqual(len(calls), 1)                       # the old run cost 0.5 >= 0.4, so nothing else starts
        self.assertEqual((res["verdict"], res["stopped"]), ("stopped: budget", "budget"))
        self.assertEqual(res["judgements"], [])
        self.assertIn("stopped: budget", autorater.report(self.t))
        calls.clear()
        res = autorater.run_case("sr-pooling", "main", results=self.t, budget=autorater.Budget(1.2))
        self.assertEqual(len(calls), 3)                       # 0.5 + 0.5 + 0.25 = 1.25 >= 1.2: second judge not started
        self.assertEqual(res["stopped"], "budget")
        calls.clear()
        res = autorater.run_case("sr-pooling", "main", results=self.t, budget=autorater.Budget(20))
        self.assertEqual((len(calls), res["stopped"], res["unknown_cost_calls"]), (4, None, 0))

    def test_unknown_cost_is_counted(self):
        b = autorater.Budget(1.0)
        b.add(None)
        self.assertEqual((b.unknown, b.spent, b.over()), (1, 0.0, False))
        inner = autorater.run_claude

        def no_cost(args, cwd, out, timeout=None):
            code = inner(args, cwd, out, timeout)
            data = [json.loads(ln) for ln in Path(out).read_text(encoding="utf-8").splitlines()]
            for d in data:
                d.pop("total_cost_usd", None)
            Path(out).write_text("\n".join(json.dumps(d) for d in data) + "\n", encoding="utf-8")
            return code

        autorater.run_claude = no_cost
        res = autorater.run_case("sr-pooling", "main", results=self.t)
        self.assertEqual((res["unknown_cost_calls"], res["cost_usd"]), (4, 0.0))

    def test_cli_prints_estimate(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            autorater.main(["run", "sr-pooling", "--base", "main", "--results", str(self.t), "--max-usd", "5"])
        self.assertIn("estimate 1 case(s)", err.getvalue())
        self.assertIn("USD 5", err.getvalue())

    def test_cli(self):
        self.assertEqual(autorater.main(["list", "--skill", "case-report"]), 0)
        self.assertEqual(autorater.main(["run", "nope", "--base", "main", "--results", str(self.t)]), 2)
        self.assertEqual(autorater.main(["report", "--results", str(self.t)]), 0)

    def test_claude_is_resolved_with_which(self):
        real = self.saved[0]
        saved = (autorater.shutil.which, autorater.subprocess.run)
        try:
            autorater.shutil.which = lambda name: None
            with self.assertRaises(autorater.Usage) as cm:
                real([], self.t, self.t / "o.jsonl")
            self.assertIn("claude", str(cm.exception))
            seen = []

            def fake_run(cmd, **kw):
                seen.append((cmd, kw))
                return types.SimpleNamespace(returncode=0)

            autorater.shutil.which = lambda name: r"C:\bin\claude.cmd"
            autorater.subprocess.run = fake_run
            self.assertEqual(real(["-p", "x"], self.t, self.t / "o.jsonl", timeout=7), 0)
            self.assertEqual(seen[0][0], [r"C:\bin\claude.cmd", "-p", "x"])
            self.assertEqual(seen[0][1]["timeout"], 7)
        finally:
            autorater.shutil.which, autorater.subprocess.run = saved

    def test_missing_claude_exits_2(self):
        saved = autorater.shutil.which
        autorater.run_claude = self.saved[0]
        autorater.shutil.which = lambda name: None
        try:
            with contextlib.redirect_stderr(io.StringIO()) as err, contextlib.redirect_stdout(io.StringIO()):
                code = autorater.main(["run", "sr-pooling", "--base", "main", "--results", str(self.t)])
        finally:
            autorater.shutil.which = saved
        self.assertEqual(code, 2)
        self.assertIn("claude", err.getvalue())

    def test_timeout_is_recorded_as_failed_with_unknown_cost(self):
        real = self.saved[0]
        saved = (autorater.shutil.which, autorater.subprocess.run)

        def boom(cmd, **kw):
            raise autorater.subprocess.TimeoutExpired(cmd, kw["timeout"])

        try:
            autorater.shutil.which = lambda name: "claude"
            autorater.subprocess.run = boom
            self.assertEqual(real([], self.t, self.t / "o.jsonl", timeout=1), "timeout")
        finally:
            autorater.shutil.which, autorater.subprocess.run = saved

        inner = autorater.run_claude

        def slow(args, cwd, out, timeout=None):
            if "--plugin-dir" in args and Path(args[args.index("--plugin-dir") + 1]).parent.name == "new":
                Path(out).write_text("", encoding="utf-8")
                return "timeout"
            if "--plugin-dir" not in args:               # the judge sees no "answer new" text: fixed verdict
                Path(out).write_text(result_line(f'{FENCE}json\n{{"winner": "tie"}}\n{FENCE}'), encoding="utf-8")
                return 0
            return inner(args, cwd, out, timeout)

        autorater.run_claude = slow
        res = autorater.run_case("sr-pooling", "main", results=self.t, timeout_min=3)
        self.assertEqual(res["runs"]["new"]["exit"], "timeout")
        self.assertIsNone(res["runs"]["new"]["cost_usd"])
        self.assertGreaterEqual(res["unknown_cost_calls"], 1)

    def test_per_call_cap_and_timeout_are_passed(self):
        SEEN.clear()
        autorater.run_case("sr-pooling", "main", results=self.t, budget=autorater.Budget(20), timeout_min=12)
        self.assertEqual(len(SEEN), 4)
        for args, timeout in SEEN:
            self.assertEqual(timeout, 12 * 60)
            cap = float(args[args.index("--max-budget-usd") + 1])
            self.assertLessEqual(cap, 20 / 4 + 1e-9)
            self.assertGreater(cap, 0)
        self.assertIn("--max-turns", SEEN[0][0])
        SEEN.clear()
        autorater.run_case("sr-pooling", "main", results=self.t, budget=autorater.Budget(1.2))
        caps = [float(a[a.index("--max-budget-usd") + 1]) for a, _ in SEEN]
        self.assertLessEqual(caps[-1], 1.2 - 1.0 + 1e-9)        # never more than what is left

    def test_cli_has_timeout_option(self):
        SEEN.clear()
        with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            autorater.main(["run", "sr-pooling", "--base", "main", "--results", str(self.t), "--timeout-min", "2"])
        self.assertEqual({t for _, t in SEEN}, {120})
        SEEN.clear()
        with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            autorater.main(["run", "sr-pooling", "--base", "main", "--results", str(self.t)])
        self.assertEqual({t for _, t in SEEN}, {1800})

    def test_report_reads_utf8_and_source_is_explicit(self):
        (self.t / "x-20260101T000000Z.json").write_text(
            json.dumps({"case": "ca-ế", "verdict": "new", "cost_usd": 1}, ensure_ascii=False), encoding="utf-8")
        self.assertIn("ca-ế", autorater.report(self.t))
        src = (ROOT / "tools" / "autorater.py").read_text(encoding="utf-8")
        for m in re.finditer(r"(read_text|write_text|open)\(([^\n]*)", src):
            line = m.group(0)
            if "\"wb\"" in line or "fileobj" in line:
                continue
            self.assertIn("encoding=", line, line)

    def test_progress_lines_go_to_stderr(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            autorater.run_case("sr-pooling", "main", results=self.t)
        lines = [ln for ln in err.getvalue().splitlines() if "sr-pooling" in ln]
        self.assertGreaterEqual(len(lines), 8)                    # start + finish for 4 calls
        for token in ("old", "new", "old-new", "new-old", "USD"):
            self.assertTrue(any(token in ln for ln in lines), token)

    def test_results_ignored_and_agents_rule(self):
        self.assertIn("evals/results/", (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines())
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("tools/autorater.py list --skill", agents)
        self.assertIn("never runs in CI", agents)


if __name__ == "__main__":
    unittest.main()
