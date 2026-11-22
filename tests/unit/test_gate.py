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


import json


def audited(p: Path, deliverable: str = "thesis", blocks: int = 0, text: str = "x\n") -> Path:
    f = p / "06_writing" / deliverable / "ch4.md"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text, encoding="utf-8")
    files = {f.relative_to(p).as_posix(): gate.sha256(f),
             "ledgers/references.json": gate.sha256(p / "ledgers" / "references.json")}
    (p / "reviews" / "audit.json").write_text(json.dumps(
        {"deliverable": deliverable, "at": "2026-11-22T10:00:00", "blocks": blocks, "warns": 0, "files": files}),
        encoding="utf-8")
    return f


class TestGateG4(unittest.TestCase):
    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = gate.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_open_refused_without_clean_fresh_audit(self):
        with tempfile.TemporaryDirectory() as t:
            p = project(t)
            code, out, _ = self.run_cli("open", str(p), "G4", "--by", "A")
            self.assertEqual(code, 1)
            self.assertTrue(out.startswith("G4: refused"), out)
            self.assertIn("audit.json not found", out)
            audited(p, blocks=2)
            code, out, _ = self.run_cli("open", str(p), "G4", "--by", "A")
            self.assertEqual(code, 1)
            self.assertIn("blocking finding", out)
            f = audited(p)
            f.write_text("edited\n", encoding="utf-8")
            code, out, _ = self.run_cli("open", str(p), "G4", "--by", "A")
            self.assertEqual(code, 1)
            self.assertIn("06_writing/thesis/ch4.md changed since the audit", out)
            self.assertNotIn("G4", json.loads((p / "gates" / "state.json").read_text(encoding="utf-8")))

    def test_open_locks_audit_hashes_then_edit_closes(self):
        with tempfile.TemporaryDirectory() as t:
            p = project(t)
            f = audited(p)
            code, out, _ = self.run_cli("open", str(p), "G4", "--by", "Dr A")
            self.assertEqual((code, out.strip()), (0, "G4 open by Dr A"))
            state = json.loads((p / "gates" / "state.json").read_text(encoding="utf-8"))
            audit = json.loads((p / "reviews" / "audit.json").read_text(encoding="utf-8"))
            self.assertEqual(state["G4"]["files"], audit["files"])
            self.assertEqual(state["G4"]["deliverables"]["thesis"]["files"], audit["files"])
            code, out, _ = self.run_cli("check", str(p), "G4")
            self.assertEqual(code, 0)
            self.assertTrue(out.startswith("G4: open — approved after a clean audit by Dr A"), out)
            f.write_text("edited\n", encoding="utf-8")
            code, out, _ = self.run_cli("check", str(p), "G4")
            self.assertEqual(code, 1)
            self.assertEqual(out.strip(), "G4: closed — 06_writing/thesis/ch4.md changed since the audit")

    def test_per_deliverable_locks(self):
        with tempfile.TemporaryDirectory() as t:
            p = project(t)
            audited(p, "thesis")
            gate.open_gate(p, "G4", by="A")
            m = audited(p, "manuscript")
            gate.open_gate(p, "G4", by="A")
            self.assertEqual(gate.check_gate(p, "G4", "thesis"), (True, []))
            self.assertEqual(gate.check_gate(p, "G4", "manuscript"), (True, []))
            m.write_text("edited\n", encoding="utf-8")
            self.assertTrue(gate.check_gate(p, "G4", "thesis")[0])
            self.assertFalse(gate.check_gate(p, "G4", "manuscript")[0])
            self.assertFalse(gate.check_gate(p, "G4")[0])
            code, out, _ = self.run_cli("check", str(p), "G4", "--deliverable", "thesis")
            self.assertEqual(code, 0, out)

    def test_not_open_for_a_deliverable(self):
        with tempfile.TemporaryDirectory() as t:
            p = project(t)
            audited(p, "thesis")
            gate.open_gate(p, "G4", by="A")
            ok, why = gate.check_gate(p, "G4", "manuscript")
            self.assertFalse(ok)
            self.assertIn("not open for the manuscript", why[0])
            code, out, _ = self.run_cli("check", str(p), "G4", "--deliverable", "manuscript")
            self.assertEqual(code, 1)
            self.assertTrue(out.startswith("G4: not open"), out)

    def test_waiver_counts_as_open(self):
        with tempfile.TemporaryDirectory() as t:
            p = project(t)
            with (p / "decisions.md").open("a", encoding="utf-8") as fh:
                fh.write("\nWAIVE G4: internal report only, 2026-11-22\n")
            self.assertEqual(gate.check_gate(p, "G4", "thesis"), (True, []))
            self.assertTrue(gate.waived(p, "G4"))

    def test_g4_usage_errors(self):
        with tempfile.TemporaryDirectory() as t:
            p = project(t)
            audited(p)
            self.assertEqual(self.run_cli("open", str(p), "G4", "--by", "A", "--files", "x")[0], 2)
            self.assertEqual(self.run_cli("lock", str(p), "G4", "--by", "A", "--files", "x")[0], 2)
            self.assertEqual(self.run_cli("check", str(p), "G3", "--deliverable", "thesis")[0], 2)

    def test_audit_file_outside_project_refused(self):
        with tempfile.TemporaryDirectory() as t:
            p = project(t)
            (Path(t) / "x.txt").write_text("x", encoding="utf-8")
            (p / "reviews" / "audit.json").write_text(json.dumps(
                {"deliverable": "thesis", "at": "x", "blocks": 0, "warns": 0, "files": {"../x.txt": "0" * 64}}),
                encoding="utf-8")
            with self.assertRaises(gate.Refused):
                gate.open_gate(p, "G4", by="A")


class TestGateG4Review(unittest.TestCase):
    def test_check_without_deliverable_checks_each_entry(self):
        with tempfile.TemporaryDirectory() as t:
            p = project(t)
            audited(p, "thesis")
            gate.open_gate(p, "G4", by="A")
            m = audited(p, "manuscript")
            gate.open_gate(p, "G4", by="A")
            # a file listed only in the thesis entry changes: the union would still hide nothing, but each entry counts
            state_p = p / "gates" / "state.json"
            state = json.loads(state_p.read_text(encoding="utf-8"))
            state["G4"]["files"] = {}
            state_p.write_text(json.dumps(state), encoding="utf-8")
            self.assertTrue(gate.check_gate(p, "G4")[0])
            (p / "06_writing" / "thesis" / "ch4.md").write_text("edited\n", encoding="utf-8")
            ok, why = gate.check_gate(p, "G4")
            self.assertFalse(ok)
            self.assertIn("06_writing/thesis/ch4.md changed since the audit", why)
            self.assertTrue(m.is_file())

    def test_open_refused_when_no_deliverable_resolves(self):
        with tempfile.TemporaryDirectory() as t:
            p = project(t)
            audited(p)
            audit = json.loads((p / "reviews" / "audit.json").read_text(encoding="utf-8"))
            audit["deliverables"] = ["all"]
            (p / "reviews" / "audit.json").write_text(json.dumps(audit), encoding="utf-8")
            self.assertEqual(gate.audited_deliverables(audit), [])
            with self.assertRaises(gate.Refused):
                gate.open_gate(p, "G4", by="A")

    def test_export_problems(self):
        with tempfile.TemporaryDirectory() as t:
            p = project(t)
            self.assertTrue(any("not open" in w for w in gate.export_problems(p, "thesis")))
            f = audited(p)
            gate.open_gate(p, "G4", by="A")
            self.assertEqual(gate.export_problems(p, "thesis"), [])
            self.assertTrue(gate.export_problems(p, "manuscript"))
            f.write_text("edited\n", encoding="utf-8")
            why = gate.export_problems(p, "thesis")
            self.assertEqual(why, ["06_writing/thesis/ch4.md changed since the audit"])

    def test_export_problems_new_draft_order_or_image_since_audit(self):
        with tempfile.TemporaryDirectory() as t:
            p = project(t)
            audited(p, text="![f](f.png)\n")
            (p / "06_writing" / "thesis" / "f.png").write_bytes(b"\x89PNG")
            gate.open_gate(p, "G4", by="A")
            why = gate.export_problems(p, "thesis")
            self.assertEqual(why, ["06_writing/thesis/f.png is not covered by the audit (added since)"])
            (p / "06_writing" / "thesis" / "f.png").unlink()
            self.assertEqual(gate.export_problems(p, "thesis"), [])
            (p / "06_writing" / "thesis" / "ch5.md").write_text("new\n", encoding="utf-8")
            self.assertEqual(gate.export_problems(p, "thesis"),
                             ["06_writing/thesis/ch5.md is not covered by the audit (added since)"])
            (p / "06_writing" / "thesis" / "ch5.md").unlink()
            (p / "06_writing" / "thesis" / "order.txt").write_text("ch4.md\n", encoding="utf-8")
            self.assertEqual(gate.export_problems(p, "thesis"),
                             ["06_writing/thesis/order.txt is not covered by the audit (added since)"])

    def test_export_problems_waiver_needs_a_matching_audit_but_tolerates_blocks(self):
        with tempfile.TemporaryDirectory() as t:
            p = project(t)
            with (p / "decisions.md").open("a", encoding="utf-8") as fh:
                fh.write("\nWAIVE G4: internal report, 2026-11-22\n")
            self.assertTrue(any("audit.json not found" in w for w in gate.export_problems(p, "thesis")))
            f = audited(p, blocks=3)
            self.assertEqual(gate.export_problems(p, "thesis"), [])
            f.write_text("edited\n", encoding="utf-8")
            self.assertTrue(any("changed since the audit" in w for w in gate.export_problems(p, "thesis")))
