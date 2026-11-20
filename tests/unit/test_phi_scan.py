import contextlib
import io
import json
import os
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
]


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

    def test_scan_file_non_utf8(self):
        f = Path(self._tmp.name) / "latin.txt"
        f.write_bytes(b"B\xe9nh nh\xe2n\nCCCD 079 123 456789\n")
        found = phi_scan.scan_file(f)
        self.assertIn((2, "block"), {(x["line"], x["severity"]) for x in found})

    def test_hooks_json_targets_outbound_tools(self):
        hj = json.loads((PHI_SCRIPTS.parent / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        entry = hj["hooks"]["PreToolUse"][0]
        self.assertEqual(entry["matcher"], "mcp__.*|WebFetch|WebSearch")
        self.assertIn("phi_scan.py", entry["hooks"][0]["command"])


if __name__ == "__main__":
    unittest.main()
