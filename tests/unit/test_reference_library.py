import json
import re
import unittest

import _paths  # noqa: F401
from _paths import ROOT

REF = ROOT / "plugins" / "orchestra" / "references"


class TestReferenceLibrary(unittest.TestCase):
    def test_evidence_policy_has_required_rules(self):
        t = (REF / "evidence-policy.md").read_text(encoding="utf-8")
        for needle in ["search_lit.py", "verify_refs.py", "Nomenclature check", "retract",
                       "abstract only", "OpenEvidence", "Europe PMC", "Crossref"]:
            self.assertIn(needle, t, needle)

    def test_evidence_policy_has_tool_rules(self):
        t = (REF / "evidence-policy.md").read_text(encoding="utf-8")
        for needle in ["3 papers per call", "geo", "authenticated=false", "20 Boolean operators",
                       "at most 10 PMIDs", "python -I -X utf8", "one at a time", "Self-appraisal gate"]:
            self.assertIn(needle, t, needle)

    def test_judgement_defaults_are_labelled_defaults(self):
        t = (REF / "judgement-defaults.md").read_text(encoding="utf-8")
        self.assertIn("default", t.lower())
        self.assertIn("override", t.lower())
        for needle in ["5 studies", "300 participants", "12–20", "10–20"]:
            self.assertIn(needle, t, needle)

    def test_every_skill_link_to_references_resolves(self):
        for skill in (ROOT / "plugins" / "orchestra" / "skills").glob("*/SKILL.md"):
            for rel in re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/(references/[\w/\-.]+\.(?:md|json))", skill.read_text(encoding="utf-8")):
                self.assertTrue((ROOT / "plugins" / "orchestra" / rel).is_file(), f"{skill}: {rel}")

    def test_guideline_library_covers_every_project_guideline(self):
        import init_project
        lib = json.loads((REF / "reporting-guidelines" / "guidelines.json").read_text(encoding="utf-8"))
        codes = {r["guideline"] for r in lib["references"]}
        for code in set(init_project.GUIDELINE_BY_DESIGN.values()):
            self.assertIn(code, codes, code)
        from crolib import ledgers
        for r in lib["references"]:
            self.assertEqual(ledgers.validate_reference(r), [], r["id"])
            self.assertTrue(r["verified_by"] and "VERIFIED" in r["verified_by"], r["id"])


if __name__ == "__main__":
    unittest.main()
