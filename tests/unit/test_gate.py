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


if __name__ == "__main__":
    unittest.main()
