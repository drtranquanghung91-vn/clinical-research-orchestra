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

    def test_sap_template_has_analysis_register(self):
        t = (REF / "statistics" / "sap-template.md").read_text(encoding="utf-8")
        self.assertIn("## Analysis register", t)
        self.assertIn("| ID | Objective | Outcome | Population | Method | Covariates | Multiplicity |", t)
        self.assertIn("A0", t)

    def test_judgement_defaults_cover_p2(self):
        t = (REF / "judgement-defaults.md").read_text(encoding="utf-8")
        for needle in ("Shapiro", "IQR × 1.5", "EPV", "Times New Roman", "integers 0–10"):
            self.assertIn(needle, t, needle)

    def test_p4_role_briefs_start_with_the_marker(self):
        roles = REF / "writing" / "roles"
        for name in ("introduction", "methods", "results", "discussion", "conclusion", "abstract"):
            text = (roles / f"{name}.md").read_text(encoding="utf-8")
            self.assertEqual(text.splitlines()[0], f"orchestra-role: {name}")
            if name != "introduction":
                self.assertIn("{{R-", text)
            self.assertIn("[@id]", text)
        disc = (roles / "discussion.md").read_text(encoding="utf-8").lower()
        for s in ("principal finding", "mechanism", "strengths", "limitations", "implications", "causal", "trend",
                  "evidence table", "studied population"):
            self.assertIn(s, disc)
        self.assertIn("<!-- results: R-A1-004 -->", (roles / "conclusion.md").read_text(encoding="utf-8"))
        methods = (roles / "methods.md").read_text(encoding="utf-8")
        for s in ("Part B", "Part A", "Part C", "past tense", "DEVIATION", "POST-HOC"):
            self.assertIn(s, methods)

    def test_p4_writing_references(self):
        w = REF / "writing"
        thesis = (w / "vn-thesis.md").read_text(encoding="utf-8")
        for s in ("Đặt vấn đề", "Chương 1", "Chương 2", "Chương 3", "Chương 4", "Kết luận", "Kiến nghị",
                  "Tài liệu tham khảo", "Phụ lục", "Lời cam đoan", "Mục lục", "Bảng 3.1.", "Hình 3.1.", "Biểu đồ 3.1.",
                  "{TOC}", "institution.template"):
            self.assertIn(s, thesis)
        man = (w / "manuscript.md").read_text(encoding="utf-8")
        for s in ("IMRaD", "structured abstract", "target.word_limit", "--count-words", "Vancouver", "[[AUTHOR:"):
            self.assertIn(s, man)
        dis = (w / "ai-disclosure.md").read_text(encoding="utf-8")
        for s in ("ICMJE", "not an author", "không phải là tác giả", "STATUS.md", "decisions.md", "never marked final"):
            self.assertIn(s, dis)



if __name__ == "__main__":
    unittest.main()
