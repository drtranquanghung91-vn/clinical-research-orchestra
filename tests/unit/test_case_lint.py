import contextlib
import io
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import _paths  # noqa: F401
import audit
import case_lint
from p5_helpers import case_project

OK_REF = {"id": "lee2020", "title": "Fictional similar case", "authors": ["Lee A"], "journal": "J", "year": 2020,
          "pmid": "1", "verified_by": "verify_refs.py 2026-11-22 VERIFIED"}
SIMILAR = ("ref_id,age_range,sex,presentation,key_finding,treatment,outcome\n"
           "lee2020,40-49,F,fever,finding,drug,recovered\nlee2020,50-59,M,rash,finding,drug,recovered\n"
           "lee2020,30-39,F,fever,finding,surgery,recovered\n")


def set_institution(p: Path, name: str, city: str) -> None:
    y = (p / "project.yaml").read_text(encoding="utf-8")
    y = re.sub(r"(?m)^institution:\n(?:  .*\n)*", f'institution:\n  name: "{name}"\n  city: "{city}"\n  template: ""\n', y)
    (p / "project.yaml").write_text(y, encoding="utf-8")


class TestCaseLint(unittest.TestCase):
    def setUp(self):
        self.t = Path(tempfile.mkdtemp())
        self.p = case_project(self.t)
        set_institution(self.p, "Bệnh viện Mô phỏng", "Thành phố Giả định")
        (self.p / "ledgers" / "references.json").write_text(json.dumps({"references": [OK_REF]}), encoding="utf-8")
        (self.p / case_lint.SIMILAR).write_text(SIMILAR, encoding="utf-8")
        self.d = self.p / case_lint.DRAFTS
        (self.d / "00-title.md").write_text("# Fever and rash after a fictional exposure\n", encoding="utf-8")
        (self.d / "05-timeline.md").write_text("## Timeline\n\n| Day | Event |\n|---|---|\n| 0 | admission |\n", encoding="utf-8")
        (self.p / "decisions.md").write_text("# Decisions\n\nCONSENT: obtained written consent form, signed by the patient\n",
                                             encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.t, ignore_errors=True)

    def found(self, strict=False, level=None, code="E-CASE"):
        return [(loc, msg) for c, lv, loc, msg in case_lint.lint(self.p, strict=strict, phi=False)
                if c == code and level in (None, lv)]

    def dossier(self, text):
        (self.p / case_lint.DOSSIER).write_text(text, encoding="utf-8")

    def test_clean_case_has_no_finding(self):
        self.dossier("Bệnh nhân nữ ở độ tuổi 40–49 tuổi, nhập viện ngày 0 vì sốt; ngày +3 nổi ban. "
                     "A woman in her 40s; on day +3 a rash appeared, 3 days later it faded.\n")
        self.assertEqual(self.found(strict=True), [])

    def test_dates_block(self):
        for s in ("Nhập viện 12/03/2025.", "Admitted 2025-03-12.", "Vào tháng 3 năm 2025.", "Vào tháng 03/2025.",
                  "Seen in March 2025.", "Seen on 12 March 2025.", "Seen on March 12, 2025."):
            with self.subTest(text=s):
                self.dossier(s + "\n")
                blocks = self.found(level="block")
                self.assertTrue(any("calendar date" in m for _, m in blocks), blocks)
                self.assertEqual(blocks[0][0], "01_case/dossier.md:1")

    def test_exact_ages_block_ranges_pass(self):
        for s in ("Bệnh nhân 45 tuổi.", "Trẻ 5 tháng tuổi.", "A 45-year-old woman.", "A woman aged 45.",
                  "45 years of age."):
            with self.subTest(text=s):
                self.dossier(s + "\n")
                self.assertTrue(any("exact age" in m for _, m in self.found(level="block")))
        for s in ("Bệnh nhân 40–49 tuổi.", "A woman in her 40s.", "A man in his fifth decade."):
            with self.subTest(text=s):
                self.dossier(s + "\n")
                self.assertEqual(self.found(level="block"), [])

    def test_institution_and_city_block(self):
        (self.d / "03-patient-information.md").write_text("Admitted to Bệnh viện Mô phỏng.\nLives in thành phố giả định.\n",
                                                          encoding="utf-8")
        blocks = self.found(level="block")
        self.assertIn("06_writing/case-report/03-patient-information.md:1", [loc for loc, _ in blocks])
        self.assertIn("06_writing/case-report/03-patient-information.md:2", [loc for loc, _ in blocks])

    def test_consent(self):
        (self.p / "decisions.md").write_text("# Decisions\n\nCONSENT: obtained\n", encoding="utf-8")
        self.assertFalse(case_lint.consent_recorded(self.p))
        self.assertTrue(any("consent" in m for _, m in self.found(level="warn")))
        self.assertTrue(any("consent" in m for _, m in self.found(strict=True, level="block")))
        (self.p / "decisions.md").write_text("- CONSENT: obtained written form, signed by the patient's mother\n",
                                             encoding="utf-8")
        self.assertTrue(case_lint.consent_recorded(self.p))
        self.assertEqual(self.found(strict=True, level="block"), [])

    def test_structure_warnings(self):
        y = (self.p / "project.yaml").read_text(encoding="utf-8")
        y = y.replace("word_limit: null", "word_limit: 20") + "\n" if "word_limit: null" in y else y
        y = re.sub(r"(?m)^  journal_style:.*$", "  journal_style: bmj", y) if "journal_style" in y else \
            y.replace("target:\n", "target:\n  journal_style: bmj\n")
        (self.p / "project.yaml").write_text(y, encoding="utf-8")
        (self.d / "00-title.md").write_text("# A rare first case report of fictional fever\n", encoding="utf-8")
        (self.d / "01-summary.md").write_text("# Summary\n\n" + "word " * 30 + "\n", encoding="utf-8")
        (self.d / "09-learning-points.md").write_text("# Learning points\n\n- one\n- two\n", encoding="utf-8")
        (self.d / "05-timeline.md").unlink()
        (self.p / case_lint.SIMILAR).write_text(SIMILAR.split("\n", 2)[0] + "\n" + SIMILAR.split("\n")[1] + "\n",
                                                encoding="utf-8")
        warns = " | ".join(m for _, m in self.found(level="warn"))
        for s in ("'rare'", "'first'", "'case report'", "over the 20-word limit", "2 learning points",
                  "fewer than 3 rows", "no timeline table"):
            self.assertIn(s, warns)

    def test_similar_cases_references_must_be_verified(self):
        (self.p / case_lint.SIMILAR).write_text(SIMILAR + "ghost2021,20-29,M,x,y,z,w\n", encoding="utf-8")
        refs = self.found(level="block", code="E-REF")
        self.assertTrue(any("ghost2021" in m for _, m in refs), refs)

    def test_phi_guard_identifiers(self):
        self.dossier("Họ tên: Nguyễn Văn An\n")
        found = [f for f in case_lint.lint(self.p, phi=True) if f[0] == "E-CASE" and f[1] == "block"]
        self.assertTrue(any("identifier" in f[3] for f in found), found)
        with mock.patch.object(audit, "find_phi_scan", return_value=None):
            found = case_lint.lint(self.p, phi=True)
            self.assertTrue(any(f[1] == "warn" and "phi-guard not found" in f[3] for f in found))

    def test_mask_relative_time(self):
        text = "Day +3 rash; ngày 14 sốt; tuần 6 khỏi; 3 days later; sau 3 ngày; week 6; Hb 78 g/L"
        masked = case_lint.mask_relative_time(text)
        for tok in ("+3", "14", "tuần 6", "3 days", "sau 3", "week 6"):
            self.assertNotIn(tok, masked)
        self.assertIn("78 g/L", masked)
        self.assertEqual(len(masked), len(text))

    def test_age_ranges_and_bounds_pass(self):
        for s in ("Patients aged 40–49.", "Bệnh nhân 40 - 49 tuổi.", "từ 40 đến 49 tuổi", "trên 65 tuổi",
                  "patients aged 65 years and older", "children under 5 years of age", "in her 40s",
                  "dưới 5 tuổi", "over 65 years old", "aged 40 to 49", "65 tuổi trở lên", "≥ 65 years old",
                  "Hb 45 mmol/L, published (2019), day +3."):
            with self.subTest(text=s):
                self.dossier(s + "\n")
                self.assertEqual(self.found(level="block"), [])

    def test_more_exact_ages_and_dates_block(self):
        for s in ("a 45 years old man", "age 45", "age: 45", "45 yo", "45 y/o", "a 45-yr-old", "March 5th, 2025",
                  "2025/03/05", "03/2025"):
            with self.subTest(text=s):
                self.dossier(s + "\n")
                self.assertTrue(self.found(level="block"), s)
        for s in ("on 5 March", "March 5", "ngày 5 tháng 3", "ngày 05/03"):
            with self.subTest(text=s):
                self.dossier(s + "\n")
                self.assertTrue(self.found(level="warn"), s)

    def test_mask_keeps_real_numbers(self):
        for text, keep in (("BE −8 mmol/L", "8"), ("increased by +12%", "12"), ("z-score −2.5", "2.5"),
                           ("within 24 hours 3 doses", "3 doses"), ("mỗi ngày 2 lần", "2 lần")):
            with self.subTest(text=text):
                self.assertIn(keep, case_lint.mask_relative_time(text))
        for text in ("day +3", "ngày 14", "week 6", "tuần 6", "3 days later", "sau 3 ngày", "within 24 hours"):
            with self.subTest(text=text):
                self.assertEqual(case_lint.mask_relative_time(text).strip(), "")

    def test_consent_placeholders_rejected(self):
        for tail in ("obtained <form, who signed>", "obtained — pending", "obtained, not yet", "obtained chưa", "obtained TBD"):
            with self.subTest(tail=tail):
                (self.p / "decisions.md").write_text(f"CONSENT: {tail}\n", encoding="utf-8")
                self.assertFalse(case_lint.consent_recorded(self.p))

    def test_consent_inside_code_fence_ignored(self):
        line = "CONSENT: obtained written form, signed by the patient"
        for fence in ("```", "~~~", "```text"):
            with self.subTest(fence=fence):
                close = fence[:3]
                (self.p / "decisions.md").write_text(f"# Decisions\n\nExample of the format:\n\n{fence}\n{line}\n{close}\n",
                                                     encoding="utf-8")
                self.assertFalse(case_lint.consent_recorded(self.p))
        (self.p / "decisions.md").write_text(f"# Decisions\n\n```\nexample\n```\n\n{line}\n", encoding="utf-8")
        self.assertTrue(case_lint.consent_recorded(self.p))

    def test_institution_word_boundary_and_diacritics(self):
        set_institution(self.p, "Bệnh viện Mô phỏng", "Huế")
        self.dossier("Nộp thuế đúng hạn.\n")
        self.assertEqual(self.found(level="block"), [])
        self.dossier("Sống ở Hue.\n")
        self.assertTrue(self.found(level="block"))
        set_institution(self.p, "Bệnh viện Mô phỏng", "Hà Nội")
        self.dossier("Lives in Ha Noi.\n")
        self.assertTrue(self.found(level="block"))

    def test_cli_exit_codes(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(case_lint.main([str(self.p), "--strict"]), 0)
            self.dossier("Bệnh nhân 45 tuổi.\n")
            self.assertEqual(case_lint.main([str(self.p)]), 1)
            self.assertEqual(case_lint.main([str(self.t / "none")]), 2)
        self.assertIn("E-CASE block 01_case/dossier.md:1:", out.getvalue())


if __name__ == "__main__":
    unittest.main()
