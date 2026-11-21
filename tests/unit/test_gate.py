import contextlib
import io
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
import gate
import init_project


def project(t):
    return init_project.create(Path(t) / "p", "T", "manuscript", "cohort", "en", "vi")


class TestGate(unittest.TestCase):
    def test_closed_by_default(self):
        with tempfile.TemporaryDirectory() as t:
            ok, why = gate.check_gate(project(t), "G1")
            self.assertFalse(ok)
            self.assertTrue(why)

    def test_open_then_check(self):
        with tempfile.TemporaryDirectory() as t:
            p = project(t)
            gate.open_gate(p, "G1", by="Author")
            self.assertEqual(gate.check_gate(p, "G1"), (True, []))

    def test_lock_detects_changed_file(self):
        with tempfile.TemporaryDirectory() as t:
            p = project(t)
            f = p / "ledgers" / "results-ledger.json"
            gate.open_gate(p, "G3", by="Author", files=["ledgers/results-ledger.json"])
            self.assertTrue(gate.check_gate(p, "G3")[0])
            f.write_text('{"results": [{"id": "R-1"}]}', encoding="utf-8")
            ok, why = gate.check_gate(p, "G3")
            self.assertFalse(ok)
            self.assertTrue(any("changed" in w for w in why))

    def test_waiver_in_decisions(self):
        with tempfile.TemporaryDirectory() as t:
            p = project(t)
            with (p / "decisions.md").open("a", encoding="utf-8") as fh:
                fh.write("\nWAIVE G1: poster from a published paper\n")
            self.assertEqual(gate.check_gate(p, "G1"), (True, []))

    def test_unknown_gate(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):
                gate.open_gate(project(t), "G9", by="A")

    def test_cli_check_exit_codes(self):
        with tempfile.TemporaryDirectory() as t:
            p = project(t)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(gate.main(["check", str(p), "G2"]), 1)
                self.assertEqual(gate.main(["open", str(p), "G2", "--by", "A"]), 0)
                self.assertEqual(gate.main(["check", str(p), "G2"]), 0)

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = gate.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    # I10: usage errors go to stderr with exit 2; a missing project folder is an error, not "closed"
    def test_cli_usage_errors_on_stderr(self):
        with tempfile.TemporaryDirectory() as t:
            p = project(t)
            code, out, err = self.run_cli("open", str(p), "G1")
            self.assertEqual(code, 2)
            self.assertIn("--by is required", err)
            self.assertEqual(out, "")
            code, out, err = self.run_cli("lock", str(p), "G3", "--by", "A")
            self.assertEqual(code, 2)
            self.assertIn("lock needs --files", err)
            self.assertEqual(out, "")

    def test_cli_missing_project_exits_2(self):
        with tempfile.TemporaryDirectory() as t:
            for argv in (("check", str(Path(t) / "nope"), "G1"), ("open", str(Path(t) / "nope"), "G1", "--by", "A")):
                code, out, err = self.run_cli(*argv)
                self.assertEqual(code, 2, argv)
                self.assertIn("not found", err, argv)
            self.assertFalse((Path(t) / "nope").exists())

    def test_cli_lock_missing_file(self):
        with tempfile.TemporaryDirectory() as t:
            p = project(t)
            code, _, err = self.run_cli("lock", str(p), "G3", "--by", "A", "--files", "nope.txt")
            self.assertEqual(code, 2)
            self.assertIn("cannot read", err)
            self.assertIn("nope.txt", err)
            self.assertNotIn("G3", (p / "gates" / "state.json").read_text(encoding="utf-8"))

    def test_files_outside_project_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p = project(t)
            (Path(t) / "x.txt").write_text("x", encoding="utf-8")
            with self.assertRaises(ValueError):
                gate.open_gate(p, "G3", by="A", files=["../x.txt"])
            with self.assertRaises(ValueError):
                gate.open_gate(p, "G3", by="A", files=[str(Path(t) / "x.txt")])
            code, _, err = self.run_cli("lock", str(p), "G3", "--by", "A", "--files", "../x.txt")
            self.assertEqual(code, 2)
            self.assertIn("file outside project", err)
            self.assertNotIn("G3", (p / "gates" / "state.json").read_text(encoding="utf-8"))

    def test_corrupt_state_fails_closed(self):
        with tempfile.TemporaryDirectory() as t:
            p = project(t)
            sp = p / "gates" / "state.json"
            sp.write_text("{not json", encoding="utf-8")
            ok, why = gate.check_gate(p, "G1")
            self.assertFalse(ok)
            self.assertTrue(why[0].startswith("gates/state.json is unreadable:"))
            code, out, _ = self.run_cli("check", str(p), "G1")
            self.assertEqual(code, 1)
            self.assertIn("unreadable", out)
            code, _, err = self.run_cli("open", str(p), "G1", "--by", "A")
            self.assertEqual(code, 2)
            self.assertIn("unreadable", err)
            self.assertEqual(sp.read_text(encoding="utf-8"), "{not json")


if __name__ == "__main__":
    unittest.main()


class TestGateCheckLines(unittest.TestCase):
    def run_cli(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = gate.main(list(argv))
        return code, out.getvalue()

    def test_never_opened_line(self):
        with tempfile.TemporaryDirectory() as t:
            code, out = self.run_cli("check", str(project(t)), "G3")
            self.assertEqual(code, 1)
            self.assertTrue(out.startswith("G3: not open"), out)
            self.assertIn("not locked yet", out)

    def test_open_locked_line_is_explicit(self):
        with tempfile.TemporaryDirectory() as t:
            p = project(t)
            gate.open_gate(p, "G3", by="Dr A", files=["ledgers/results-ledger.json"])
            code, out = self.run_cli("check", str(p), "G3")
            self.assertEqual(code, 0)
            self.assertTrue(out.startswith("G3: open"), out)
            self.assertIn("results locked by Dr A on ", out)
            self.assertIn("1 locked files unchanged", out)

    def test_changed_file_keeps_closed_lines(self):
        with tempfile.TemporaryDirectory() as t:
            p = project(t)
            gate.open_gate(p, "G3", by="A", files=["ledgers/results-ledger.json"])
            (p / "ledgers" / "results-ledger.json").write_text("{}", encoding="utf-8")
            code, out = self.run_cli("check", str(p), "G3")
            self.assertEqual(code, 1)
            self.assertTrue(out.startswith("G3: closed"), out)
            self.assertIn("changed after G3 was locked", out)
