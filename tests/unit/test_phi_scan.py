import json
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
]


class TestPhiScan(unittest.TestCase):
    def test_decisions(self):
        for tool_input, want in CASES:
            d = phi_scan.decide("mcp__oe__oe_ask", tool_input)
            got = d["permissionDecision"] if d else None
            self.assertEqual(got, want, tool_input)

    def test_internal_app_tools_are_allowed(self):
        self.assertIsNone(phi_scan.decide("mcp__ccd_session__x", {"q": "CCCD 079 123 456789"}))

    def test_reason_is_bilingual(self):
        d = phi_scan.decide("WebSearch", {"query": "CCCD 079 123 456789"})
        self.assertIn("phi-guard", d["permissionDecisionReason"])
        self.assertIn("identifier", d["permissionDecisionReason"])
        self.assertIn("định danh", d["permissionDecisionReason"])

    def test_hook_mode_prints_hook_output(self):
        payload = json.dumps({"tool_name": "WebSearch", "tool_input": {"query": "CCCD 079 123 456789"}})
        r = subprocess.run([sys.executable, str(PHI_SCRIPTS / "phi_scan.py")], input=payload.encode("utf-8"),
                           capture_output=True)
        self.assertEqual(r.returncode, 0)
        out = json.loads(r.stdout.decode("utf-8"))
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "PreToolUse")

    def test_scan_file(self):
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / "draft.md"
            f.write_text("Line one\nBN: Trần Văn An, nam\nliên hệ 0903 123 456\n", encoding="utf-8")
            found = phi_scan.scan_file(f)
            self.assertEqual({(x["line"], x["severity"]) for x in found}, {(2, "block"), (3, "warn")})
            self.assertTrue(all(x["code"] == "E-PHI" for x in found))

    def test_hooks_json_targets_outbound_tools(self):
        hj = json.loads((PHI_SCRIPTS.parent / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        entry = hj["hooks"]["PreToolUse"][0]
        self.assertEqual(entry["matcher"], "mcp__.*|WebFetch|WebSearch")
        self.assertIn("phi_scan.py", entry["hooks"][0]["command"])


if __name__ == "__main__":
    unittest.main()
