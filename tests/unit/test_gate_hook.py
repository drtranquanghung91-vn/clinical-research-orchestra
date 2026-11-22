import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
from _paths import ORCH_SCRIPTS
import gate
import gate_hook
import init_project

HOOK = ORCH_SCRIPTS / "gate_hook.py"
HOOKS_JSON = ORCH_SCRIPTS.parent / "hooks" / "hooks.json"


def find_bash():
    """Git Bash on Windows (as Claude Code uses), bash elsewhere; None if unavailable (copy of test_phi_scan)."""
    if os.name == "nt":
        cands = [os.environ.get("CLAUDE_CODE_GIT_BASH_PATH", "")]
        git = shutil.which("git")
        if git:
            for root in list(Path(git).resolve().parents)[:3]:
                cands += [str(root / "usr" / "bin" / "bash.exe"), str(root / "bin" / "bash.exe")]
        return next((c for c in cands if c and Path(c).is_file()), None)
    return shutil.which("bash")


def run(payload, raw: bytes | None = None):
    r = subprocess.run([sys.executable, str(HOOK)], input=raw if raw is not None else json.dumps(payload).encode("utf-8"),
                       capture_output=True, timeout=60)
    assert r.returncode == 0, r.stderr
    out = r.stdout.decode("utf-8").strip()
    return json.loads(out)["hookSpecificOutput"] if out else None


def shell(cmd: str, cwd: Path, tool: str = "Bash") -> dict:
    return {"tool_name": tool, "tool_input": {"command": cmd}, "cwd": str(cwd)}


def open_g4(p: Path, deliverable: str = "thesis") -> None:
    f = p / "06_writing" / deliverable / "x.md"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("x\n", encoding="utf-8")
    (p / "reviews" / "audit.json").write_text(json.dumps({"deliverable": deliverable, "at": "t", "blocks": 0, "warns": 0,
                                                          "files": {f.relative_to(p).as_posix(): gate.sha256(f)}}),
                                              encoding="utf-8")
    gate.open_gate(p, "G4", by="A")


class TestGateHook(unittest.TestCase):
    def setUp(self):
        self.t = Path(tempfile.mkdtemp())
        self.p = init_project.create(self.t / "p", "T", "thesis-masters", "cohort", "vi", "vi")

    def tearDown(self):
        shutil.rmtree(self.t, ignore_errors=True)

    def test_final_assemble_denied_while_g4_closed(self):
        d = run(shell('python "/plug/scripts/assemble.py" . thesis --final', self.p))
        self.assertEqual(d["permissionDecision"], "deny")
        self.assertIn("G4", d["permissionDecisionReason"])
        self.assertIn("/orchestra:audit", d["permissionDecisionReason"])

    def test_final_assemble_allowed_after_g4_and_draft_always(self):
        self.assertIsNone(run(shell("python /plug/scripts/assemble.py . thesis", self.p)))
        open_g4(self.p)
        self.assertIsNone(run(shell("python /plug/scripts/assemble.py . thesis --final", self.p)))

    def test_per_deliverable(self):
        open_g4(self.p, "thesis")
        self.assertIsNone(run(shell("python /plug/scripts/assemble.py . thesis --final", self.p)))
        d = run(shell("python /plug/scripts/assemble.py . manuscript --final", self.p))
        self.assertEqual(d["permissionDecision"], "deny")

    def test_build_docx_to_out_final_names_only(self):
        d = run(shell("python /plug/scripts/build_docx.py 06_writing/thesis/thesis.assembled.md out/thesis.docx --project .", self.p))
        self.assertEqual(d["permissionDecision"], "deny")
        for out in ("out/ch3-results.docx", "reviews/tmp/thesis.docx"):
            self.assertIsNone(run(shell(f"python /plug/scripts/build_docx.py a.md {out}", self.p)), out)

    def test_cd_and_powershell_paths(self):
        d = run(shell("cd p && python /plug/scripts/assemble.py . manuscript --final", self.t))
        self.assertEqual(d["permissionDecision"], "deny")
        d = run(shell('python "C:\\plug\\scripts\\assemble.py" . thesis --final', self.p, tool="PowerShell"))
        self.assertEqual(d["permissionDecision"], "deny")

    def test_waiver_and_no_project(self):
        self.assertIsNone(run(shell("python /plug/scripts/assemble.py . thesis --final", self.t)))
        with (self.p / "decisions.md").open("a", encoding="utf-8") as fh:
            fh.write("\nWAIVE G4: internal report, 2026-11-22\n")
        self.assertIsNone(run(shell("python /plug/scripts/assemble.py . thesis --final", self.p)))

    def test_writer_role_needs_g3(self):
        payload = {"tool_name": "Agent", "tool_input": {"description": "draft Chương 4",
                   "prompt": "orchestra-role: discussion\n\nDraft 06_writing/thesis/ch4-discussion.md."},
                   "cwd": str(self.p / "06_writing")}
        d = run(payload)
        self.assertEqual(d["permissionDecision"], "deny")
        self.assertIn("discussion", d["permissionDecisionReason"])
        self.assertIn("G3", d["permissionDecisionReason"])
        gate.open_gate(self.p, "G3", by="A", files=["ledgers/results-ledger.json"])
        self.assertIsNone(run(payload))
        self.assertIsNone(run({"tool_name": "Task", "tool_input": {"prompt": "review the thesis"}, "cwd": str(self.p)}))

    def test_errors_ask_never_block(self):
        d = run(None, raw=b"not json")
        self.assertEqual(d["permissionDecision"], "ask")
        self.assertIn("gate hook error", d["permissionDecisionReason"])

    def test_exports_parser(self):
        found = gate_hook.exports("cd p; python x/assemble.py . thesis --lang vi --final && echo ok", self.t)
        self.assertEqual([(f[0].resolve(), f[1]) for f in found], [((self.t / "p").resolve(), "thesis")])

    def _cmd(self):
        return json.loads(HOOKS_JSON.read_text(encoding="utf-8"))["hooks"]["PreToolUse"][0]["hooks"][0]["command"]

    def test_hooks_json_command_end_to_end(self):
        bash = find_bash()
        if not bash:
            self.skipTest("bash not available")
        env = dict(os.environ, CLAUDE_PLUGIN_ROOT=ORCH_SCRIPTS.parent.as_posix())
        payload = shell("python /plug/scripts/assemble.py . thesis --final", self.p)
        r = subprocess.run([bash, "-c", self._cmd()], input=json.dumps(payload).encode("utf-8"), capture_output=True,
                           env=env, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout.decode("utf-8"))["hookSpecificOutput"]["permissionDecision"], "deny")
        with tempfile.TemporaryDirectory() as empty:
            r = subprocess.run([bash, "-c", self._cmd()], input=json.dumps(payload).encode("utf-8"), capture_output=True,
                               env=dict(env, PATH=empty), timeout=60)
        out = json.loads(r.stdout.decode("utf-8"))["hookSpecificOutput"]
        self.assertEqual(out["permissionDecision"], "ask")
        self.assertIn("Python not found", out["permissionDecisionReason"])
