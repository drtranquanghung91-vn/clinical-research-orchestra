import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
from _paths import ORCH_SCRIPTS
import render_results

SCRIPT = ORCH_SCRIPTS / "render_results.py"
LEDGER = {"results": [
    {"id": "R-A1-001", "kind": "or", "value": 1.8412, "ci": [1.214, 2.786], "p": 0.0041, "n": 1070,
     "status": "prespecified"},
    {"id": "R-A0-001", "kind": "percent", "value": 12.54, "count": 134, "status": "prespecified"}]}


class TestRender(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.p = Path(self.tmp.name)
        (self.p / "ledgers").mkdir()
        (self.p / "ledgers" / "results-ledger.json").write_text(json.dumps(LEDGER), encoding="utf-8")
        (self.p / "project.yaml").write_text("language:\n  output: vi\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, f):
        return subprocess.run([sys.executable, str(SCRIPT), str(self.p), str(f)], capture_output=True, text=True)

    def test_render_text_en(self):
        by_id = {r["id"]: r for r in LEDGER["results"]}
        out, probs = render_results.render_text(
            "OR {{R-A1-001.full}}, p = {{R-A1-001.p}}; {{R-A0-001.full}}.", by_id, "en")
        self.assertEqual(probs, [])
        self.assertEqual(out, "OR 1.84 (95% CI 1.21–2.79), p = 0.004; 134 (12.5%).")

    def test_cli_uses_project_language(self):
        f = self.p / "ch3.md"
        f.write_text("Tỷ lệ {{R-A0-001}}.\n", encoding="utf-8")
        r = self.run_cli(f)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.p / "ch3.rendered.md").read_text(encoding="utf-8"), "Tỷ lệ 12,5%.\n")

    def test_unknown_id_and_missing_part(self):
        f = self.p / "ch3.md"
        f.write_text("A {{R-A9-001}}\nB {{R-A0-001.ci}}\n", encoding="utf-8")
        r = self.run_cli(f)
        self.assertEqual(r.returncode, 1)
        self.assertIn("E-NUM block", r.stdout)
        self.assertIn(":1:", r.stdout)
        self.assertIn(":2:", r.stdout)
        self.assertFalse((self.p / "ch3.rendered.md").exists())

    def test_bad_ledgers_exit_2_without_traceback(self):
        f = self.p / "ch3.md"
        f.write_text("A {{R-A0-001}}\n", encoding="utf-8")
        ledger = self.p / "ledgers" / "results-ledger.json"
        for content in ("[1, 2]", '{"results": 5}', '{"results": [1, "x"]}', "not json"):
            ledger.write_text(content, encoding="utf-8")
            r = self.run_cli(f)
            self.assertEqual(r.returncode, 2, content)
            self.assertNotIn("Traceback", r.stderr)
            self.assertTrue(r.stderr.strip())
        ledger.unlink()
        ledger.mkdir()
        r = self.run_cli(f)
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("Traceback", r.stderr)

    def test_missing_input_exit_2(self):
        r = self.run_cli(self.p / "nope.md")
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("Traceback", r.stderr)

    def test_crlf_preserved(self):
        f = self.p / "ch3.md"
        f.write_bytes("a {{R-A0-001}}\r\nb\r\n".encode("utf-8"))
        r = self.run_cli(f)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.p / "ch3.rendered.md").read_bytes(), "a 12,5%\r\nb\r\n".encode("utf-8"))


if __name__ == "__main__":
    unittest.main()
