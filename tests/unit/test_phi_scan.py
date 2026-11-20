import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
from _paths import PHI_SCRIPTS
import phi_scan

CASES = [
    ({"question": "Người bệnh: Nguyễn Văn Bình, 67 tuổi, rung nhĩ"}, "deny"),
    ({"question": "CCCD 079 123 456789, suy tim"}, "deny"),
    ({"q": "thẻ BHYT DN4797915123456"}, "deny"),
    ({"q": "ngày sinh: 12/03/1958, đái tháo đường"}, "deny"),
    ({"q": "mã bệnh án: 24-001234"}, "deny"),
    ({"q": "Patient name: John Smith, 54 years"}, "deny"),
    ({"q": "liên hệ 0903 123 456"}, "ask"),
    ({"question": "First-line therapy for CAP in adults, cite guidelines"}, None),
    ({"article_id": "0f8e2a10-1234-4abc-9def-012345678901"}, None),
    ({"pmids": ["26364623", "33264437"]}, None),
    ({"query": "dexmedetomidine delirium 10.1016/s0140-6736(16)30580-3"}, None),
    ({"question": "nam 72 tuổi, eGFR 28, rung nhĩ, chọn kháng đông nào"}, None),
    # multi-line, key/value, nested
    ({"q": "Tóm tắt\nBN: Trần Văn An, nam"}, "deny"),
    ({"q": "ghi chú\nDN4797915123456"}, "deny"),
    ({"q": "Họ tên:\nNguyễn Văn Bình"}, "deny"),
    ({"patient_name": "Nguyễn Văn Bình"}, "deny"),
    ({"BN": "Nguyễn Văn Bình"}, "deny"),
    ({"nested": {"items": [{"q": "CCCD 079 123 456789"}]}}, "deny"),
    # URLs keep their path and query
    ({"url": "https://example.org/search?cccd=079123456789&name=Nguyen+Van+Binh"}, "deny"),
    ({"url": "https://example.org/?q=0903123456"}, "ask"),
    ({"url": "https://pubmed.ncbi.nlm.nih.gov/26364623/"}, None),
    # name casing
    ({"q": "Họ tên: NGUYỄN VĂN BÌNH, 67 tuổi"}, "deny"),
    ({"q": "Bệnh nhân: đau đầu, sốt"}, None),
    ({"q": "Bệnh nhân: COPD Nặng"}, None),
    # URL parsing must not break detection
    ({"q": "BN: Trần Văn An [https://www.who.int]"}, "deny"),
    ({"q": "see guidelines [https://www.who.int]"}, None),
    # numeric scalars and dict keys
    ({"pid": 12345}, None),
    ({"CCCD 079 123 456789": None}, "deny"),
    # I5: common note forms without a colon (weak), English labels (strong)
    ({"q": "BN Nguyễn Văn An, 65 tuổi, THA"}, "ask"),
    ({"q": "Bệnh nhân Nguyễn Văn An 65 tuổi"}, "ask"),
    ({"q": "Ông Nguyễn Văn An sinh năm 1960"}, "ask"),
    ({"q": "anh Hưng hỏi về PICO"}, None),
    ({"q": "Name: Nguyen Van An"}, "deny"),
    ({"q": "patient: Nguyen Van An"}, "deny"),
    # I5: record numbers need a digit; all-caps after a label needs 3+ words or a diacritic
    ({"q": "PID treatment guidelines CDC 2021"}, None),
    ({"q": "PID: 24001234"}, "deny"),
    ({"q": "BN: COPD GOLD"}, None),
    ({"q": "BN: TRAN VAN AN"}, "deny"),
    ({"q": "BN: NGUYỄN AN"}, "deny"),
    # I5: URL fragments are scanned
    ({"url": "https://example.org/page#cccd=079123456789"}, "deny"),
    # R5: a name found only through a synthesised "key: value" is weak unless the key is patient-specific
    ({"name": "Weekly Lab Meeting"}, "ask"),
    ({"name": "Thesis Draft Folder"}, "ask"),
    ({"name": "Nguyễn Văn Bình"}, "ask"),
    ({"patient": "Nguyen Van An"}, "deny"),
    ({"ho_ten": "Nguyễn Văn Bình"}, "deny"),
    ({"Họ tên": "Nguyễn Văn Bình"}, "deny"),
    ({"ten_benh_nhan": "Nguyễn Văn Bình"}, "deny"),
    ({"benh_nhan": "Nguyễn Văn Bình"}, "deny"),
    ({"name": "x", "note": "Name: Nguyen Van An"}, "deny"),
]

BASH_CASES = [
    ({"command": 'python search_lit.py search "CCCD 079 123 456789 suy tim"'}, "deny"),
    ({"command": 'python3 "$R/search_lit.py" search "BN: Trần Văn An"'}, "deny"),
    ({"command": "curl 'https://example.org/?q=0903123456'"}, "ask"),
    ({"command": "wget https://example.org/cccd/079123456789"}, "deny"),
    ({"command": "Invoke-WebRequest -Uri 'https://example.org/?id=079123456789'"}, "deny"),
    ({"command": "python -c \"import urllib.request as u; u.urlopen('https://x.org/?c=079123456789')\""}, "deny"),
    ({"command": "python -c \"import requests; requests.get('https://x.org', params={'c': '079123456789'})\""},
     "deny"),
    # local commands are not outbound: allowed even when they mention an identifier
    ({"command": "grep -c 079123456789 00_inputs/data.csv"}, None),
    ({"command": "python -c \"print('079 123 456789')\""}, None),
    ({"command": 'python search_lit.py search "metformin PCOS"'}, None),
    # R4: more ways to send data out from a shell
    ({"command": "python - <<'EOF'\nimport urllib.request\nurllib.request.urlopen('https://x.org/?c=079123456789')\nEOF"},
     "deny"),
    ({"command": "python3 <<EOF\nimport requests\nrequests.get('https://x.org/', params={'c': '079123456789'})\nEOF"},
     "deny"),
    ({"command": "python -c \"import http.client as h; c = h.HTTPSConnection('x.org'); c.request('GET', '/?c=079123456789')\""},
     "deny"),
    ({"command": "py -c \"import urllib.request as u; u.urlopen('https://x.org/?c=079123456789')\""}, "deny"),
    ({"command": 'py search_lit.py search "CCCD 079 123 456789"'}, "deny"),
    ({"command": "node -e \"fetch('https://x.org/?c=079123456789')\""}, "deny"),
    ({"command": "node -e \"require('https').get('https://x.org/?c=079123456789')\""}, "deny"),
    ({"command": "node -e \"console.log('079123456789')\""}, None),
    ({"command": "python - <<'EOF'\nprint('079123456789')\nEOF"}, None),
]

POWERSHELL_CASES = [
    ({"command": "Invoke-RestMethod 'https://x.org/?c=079123456789'"}, "deny"),
    ({"command": "irm https://x.org/?c=079123456789"}, "deny"),
    ({"command": "iwr https://x.org/?c=079123456789"}, "deny"),
    ({"command": "Invoke-WebRequest -Uri https://x.org/?c=079123456789"}, "deny"),
    ({"command": "curl.exe 'https://x.org/?c=079123456789'"}, "deny"),
    ({"command": "Start-BitsTransfer -Source https://x.org/079123456789 -Destination out.txt"}, "deny"),
    ({"command": "py -c \"import requests; requests.get('https://x.org', params={'c': '079123456789'})\""}, "deny"),
    ({"command": 'py search_lit.py search "BN: Trần Văn An"'}, "deny"),
    ({"command": "Invoke-RestMethod 'https://x.org/?q=0903123456'"}, "ask"),
    # local commands are allowed even when they mention an identifier
    ({"command": "Get-Content 00_inputs\\data.csv | Select-String 079123456789"}, None),
    ({"command": "python -c \"print('079 123 456789')\""}, None),
]


def find_bash():
    """Git Bash on Windows (as Claude Code uses), bash elsewhere; None if unavailable."""
    if os.name == "nt":
        cands = [os.environ.get("CLAUDE_CODE_GIT_BASH_PATH", "")]
        git = shutil.which("git")
        if git:  # ...\Git\cmd\git.exe or ...\Git\mingw64\bin\git.exe
            for root in list(Path(git).resolve().parents)[:3]:
                cands += [str(root / "usr" / "bin" / "bash.exe"), str(root / "bin" / "bash.exe")]
        return next((c for c in cands if c and Path(c).is_file()), None)
    return shutil.which("bash")


class TestPhiScan(unittest.TestCase):
    def setUp(self):
        self._old = os.environ.get("PHI_GUARD_ALLOW_FILE")
        self._tmp = tempfile.TemporaryDirectory()
        self.allow = Path(self._tmp.name) / "allow.txt"  # absent unless a test writes it
        os.environ["PHI_GUARD_ALLOW_FILE"] = str(self.allow)

    def tearDown(self):
        if self._old is None:
            os.environ.pop("PHI_GUARD_ALLOW_FILE", None)
        else:
            os.environ["PHI_GUARD_ALLOW_FILE"] = self._old
        self._tmp.cleanup()

    def run_hook(self, stdin: bytes):
        return subprocess.run([sys.executable, str(PHI_SCRIPTS / "phi_scan.py")], input=stdin,
                              capture_output=True, env=dict(os.environ))

    def test_decisions(self):
        for tool_input, want in CASES:
            with self.subTest(tool_input=tool_input):
                d = phi_scan.decide("mcp__oe__oe_ask", tool_input)
                got = d["permissionDecision"] if d else None
                self.assertEqual(got, want, tool_input)

    def test_internal_app_tools_are_allowed(self):
        self.assertIsNone(phi_scan.decide("mcp__ccd_session__x", {"q": "CCCD 079 123 456789"}))

    def test_invalid_allow_regex_is_skipped(self):
        self.allow.write_text("([unclosed\n^foo$\n", encoding="utf-8")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            d = phi_scan.decide("mcp__oe__x", {"q": "CCCD 079 123 456789"})
            self.assertIsNone(phi_scan.decide("foo", {"q": "CCCD 079 123 456789"}))
        self.assertEqual(d["permissionDecision"], "deny")
        self.assertIn("phi-guard", err.getvalue())

    def test_reason_is_bilingual(self):
        d = phi_scan.decide("WebSearch", {"query": "CCCD 079 123 456789"})
        self.assertIn("phi-guard", d["permissionDecisionReason"])
        self.assertIn("identifier", d["permissionDecisionReason"])
        self.assertIn("định danh", d["permissionDecisionReason"])

    def test_hook_mode_prints_hook_output(self):
        payload = json.dumps({"tool_name": "WebSearch", "tool_input": {"query": "CCCD 079 123 456789"}})
        r = self.run_hook(payload.encode("utf-8"))
        self.assertEqual(r.returncode, 0)
        out = json.loads(r.stdout.decode("utf-8"))
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "PreToolUse")

    def test_hook_allow_is_silent(self):
        self.allow.write_text("^WebSearch$\n", encoding="utf-8")
        payload = json.dumps({"tool_name": "WebSearch", "tool_input": {"query": "CCCD 079 123 456789"}})
        r = self.run_hook(payload.encode("utf-8"))
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, b"")

    def test_hook_ask(self):
        payload = json.dumps({"tool_name": "WebSearch", "tool_input": {"query": "liên hệ 0903 123 456"}})
        r = self.run_hook(payload.encode("utf-8"))
        self.assertEqual(r.returncode, 0)
        self.assertEqual(json.loads(r.stdout.decode("utf-8"))["hookSpecificOutput"]["permissionDecision"], "ask")

    def test_hook_unreadable_stdin_asks(self):
        for raw in (b"[1,2]", b"not json", b""):
            r = self.run_hook(raw)
            self.assertEqual(r.returncode, 0, raw)
            out = json.loads(r.stdout.decode("utf-8"))["hookSpecificOutput"]
            self.assertEqual(out["permissionDecision"], "ask", raw)
            self.assertIn("could not check", out["permissionDecisionReason"])
            self.assertIn("Không kiểm tra được", out["permissionDecisionReason"])

    def test_scan_file(self):
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / "draft.md"
            f.write_text("Line one\nBN: Trần Văn An, nam\nliên hệ 0903 123 456\n", encoding="utf-8")
            found = phi_scan.scan_file(f)
            self.assertEqual({(x["line"], x["severity"]) for x in found}, {(2, "block"), (3, "warn")})
            self.assertTrue(all(x["code"] == "E-PHI" for x in found))

    def test_scan_file_with_bracketed_url(self):
        f = Path(self._tmp.name) / "url.md"
        f.write_text("BN: Trần Văn An [https://www.who.int]\n", encoding="utf-8")
        found = phi_scan.scan_file(f)
        self.assertEqual([(x["line"], x["severity"]) for x in found], [(1, "block")])

    def test_scan_file_non_utf8(self):
        f = Path(self._tmp.name) / "latin.txt"
        f.write_bytes(b"B\xe9nh nh\xe2n\nCCCD 079 123 456789\n")
        found = phi_scan.scan_file(f)
        self.assertIn((2, "block"), {(x["line"], x["severity"]) for x in found})

    def test_hooks_json_targets_outbound_tools(self):
        hj = json.loads((PHI_SCRIPTS.parent / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        entry = hj["hooks"]["PreToolUse"][0]
        self.assertEqual(entry["matcher"], "mcp__.*|WebFetch|WebSearch|Bash|PowerShell")
        self.assertIn("phi_scan.py", entry["hooks"][0]["command"])

    # I6: Bash commands that send queries out are scanned; local commands are not
    def test_bash_outbound_commands(self):
        for tool_input, want in BASH_CASES:
            with self.subTest(tool_input=tool_input):
                d = phi_scan.decide("Bash", tool_input)
                got = d["permissionDecision"] if d else None
                self.assertEqual(got, want, tool_input)

    # R4: PowerShell uses the same outbound-only branch as Bash
    def test_powershell_outbound_commands(self):
        for tool_input, want in POWERSHELL_CASES:
            with self.subTest(tool_input=tool_input):
                d = phi_scan.decide("PowerShell", tool_input)
                got = d["permissionDecision"] if d else None
                self.assertEqual(got, want, tool_input)

    # I5: file mode joins neighbouring lines
    def test_scan_file_label_and_name_on_two_lines(self):
        f = Path(self._tmp.name) / "two.md"
        f.write_text("Ghi chú\nHọ tên:\nNguyễn Văn An\nkết thúc\n", encoding="utf-8")
        found = phi_scan.scan_file(f)
        self.assertEqual([(x["line"], x["severity"]) for x in found], [(2, "block")])

    # I10: missing file is an IO error -> stderr + 2
    def test_file_mode_missing_file_exits_2(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = phi_scan.main(["--file", str(Path(self._tmp.name) / "missing.md")])
        self.assertEqual(code, 2)
        self.assertIn("cannot read", err.getvalue())
        self.assertEqual(out.getvalue(), "")

    def test_file_mode_without_files_exits_2(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(phi_scan.main(["--file"]), 2)

    # I4: the real hooks.json command, end to end through bash
    def _hook_command(self):
        hj = json.loads((PHI_SCRIPTS.parent / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        return hj["hooks"]["PreToolUse"][0]["hooks"][0]["command"]

    def _run_hook_command(self, payload: dict, path=None):
        bash = find_bash()
        if not bash:
            self.skipTest("bash not available (Git Bash on Windows); hook command cannot be run")
        env = dict(os.environ, CLAUDE_PLUGIN_ROOT=PHI_SCRIPTS.parent.as_posix())
        if path is not None:
            env["PATH"] = path
        return subprocess.run([bash, "-c", self._hook_command()], input=json.dumps(payload).encode("utf-8"),
                              capture_output=True, env=env, timeout=60)

    def test_hooks_json_command_denies_cccd_end_to_end(self):
        r = self._run_hook_command({"tool_name": "WebSearch", "tool_input": {"query": "CCCD 079 123 456789"}})
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout.decode("utf-8"))["hookSpecificOutput"]
        self.assertEqual(out["permissionDecision"], "deny")

    def test_hooks_json_command_asks_when_python_missing(self):
        with tempfile.TemporaryDirectory() as empty:
            r = self._run_hook_command({"tool_name": "WebSearch", "tool_input": {"query": "x"}}, path=empty)
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout.decode("utf-8"))["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "PreToolUse")
        self.assertEqual(out["permissionDecision"], "ask")
        self.assertIn("Python not found", out["permissionDecisionReason"])
        self.assertIn("Không tìm thấy Python", out["permissionDecisionReason"])


if __name__ == "__main__":
    unittest.main()
