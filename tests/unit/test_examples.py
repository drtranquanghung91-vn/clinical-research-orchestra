import csv
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

import _paths  # noqa: F401
from _paths import ROOT

EXAMPLE = ROOT / "examples" / "fictional-cohort"
SIMULATOR = EXAMPLE / "tools" / "simulate_cohort.py"
DATA = EXAMPLE / "04_data" / "cohort.deid.csv"
GATE = ROOT / "plugins" / "orchestra" / "scripts" / "gate.py"


def required_n() -> int:
    text = (EXAMPLE / "03_protocol" / "sample-size.md").read_text(encoding="utf-8")
    m = re.search(r"\*\*n yêu cầu = ([\d.]+)\*\*", text)
    assert m, "sample-size.md has no '**n yêu cầu = …**' line"
    return int(m.group(1).replace(".", ""))


class TestFictionalCohortData(unittest.TestCase):
    def test_simulated_data_is_marked(self):
        with open(DATA, encoding="utf-8", newline="") as fh:
            rows = list(csv.reader(fh))
        self.assertEqual(rows[0][0], "simulated")
        body = rows[1:]
        self.assertTrue(body)
        self.assertTrue(all(r[0] == "SIMULATED" for r in body))
        self.assertEqual(len(body), required_n())

    def test_simulator_is_reproducible_and_lf_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "cohort.deid.csv"
            r = subprocess.run([sys.executable, str(SIMULATOR), "--out", str(out)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn(f"{required_n()} rows", r.stdout)
            self.assertEqual(out.read_bytes(), DATA.read_bytes())
        self.assertNotIn(b"\r", DATA.read_bytes())


class TestFictionalCohortWrite(unittest.TestCase):
    """P4: thesis and manuscript exported through G4 after a clean audit."""

    def gate(self, *args):
        return subprocess.run([sys.executable, str(GATE), "check", str(EXAMPLE), *args],
                              capture_output=True, text=True, encoding="utf-8")

    def test_g3_still_open(self):
        r = self.gate("G3")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_g4_open_for_both_deliverables(self):
        for args in ((), ("--deliverable", "thesis"), ("--deliverable", "manuscript")):
            r = self.gate("G4", *args)
            self.assertEqual(r.returncode, 0, f"{args}: {r.stdout}{r.stderr}")

    def test_final_docx_are_zips(self):
        for name in ("thesis.docx", "manuscript.docx"):
            path = EXAMPLE / "out" / name
            self.assertTrue(zipfile.is_zipfile(path), name)
            with zipfile.ZipFile(path) as z:
                self.assertIn("word/document.xml", z.namelist())

    def test_disclosure_and_decisions_exist(self):
        for name in ("ai-use-disclosure.md", "author-decisions.md"):
            path = EXAMPLE / "out" / name
            self.assertTrue(path.is_file(), name)
            self.assertTrue(path.read_text(encoding="utf-8").strip(), name)

    def test_audit_has_no_block_and_covers_both(self):
        data = json.loads((EXAMPLE / "reviews" / "audit.json").read_text(encoding="utf-8"))
        self.assertEqual(data["blocks"], 0)
        self.assertEqual(sorted(data["deliverables"]), ["manuscript", "thesis"])
        self.assertFalse([f for f in data["findings"] if f.get("level") == "block"])


CASE = ROOT / "examples" / "fictional-case"


class TestFictionalCase(unittest.TestCase):
    """P5: a fictional case report exported through G4 after a clean audit."""

    def script(self, name, *args):
        return subprocess.run([sys.executable, str(GATE.parent / name), *args], capture_output=True, text=True,
                              encoding="utf-8")

    def test_gates(self):
        for args in (("G3",), ("G4", "--deliverable", "case-report")):
            r = self.script("gate.py", "check", str(CASE), *args)
            self.assertEqual(r.returncode, 0, f"{args}: {r.stdout}{r.stderr}")

    def test_strict_case_lint_and_consent(self):
        r = self.script("case_lint.py", str(CASE), "--strict")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertRegex((CASE / "decisions.md").read_text(encoding="utf-8"), r"(?m)^\s*(?:- )?CONSENT: obtained \S")

    def test_outputs_and_audit(self):
        with zipfile.ZipFile(CASE / "out" / "case-report.docx") as z:
            self.assertIn("word/document.xml", z.namelist())
        for name in ("ai-use-disclosure.md", "author-decisions.md"):
            self.assertTrue((CASE / "out" / name).read_text(encoding="utf-8").strip(), name)
        data = json.loads((CASE / "reviews" / "audit.json").read_text(encoding="utf-8"))
        self.assertEqual((data["blocks"], data["deliverables"]), (0, ["case-report"]))

    def test_facts_and_references(self):
        recs = json.loads((CASE / "ledgers" / "results-ledger.json").read_text(encoding="utf-8"))["results"]
        self.assertTrue(recs)
        self.assertTrue(all(r["analysis_id"] == "A0" and r["status"] == "observed" for r in recs))
        refs = json.loads((CASE / "ledgers" / "references.json").read_text(encoding="utf-8"))["references"]
        self.assertTrue(all(str(r.get("verified_by", "")).endswith("VERIFIED") for r in refs))
        with open(CASE / "01_case" / "similar-cases.csv", encoding="utf-8", newline="") as fh:
            self.assertGreaterEqual(len(list(csv.DictReader(fh))), 3)
        self.assertIn("fictional", (CASE / "README.md").read_text(encoding="utf-8").lower())


SR = ROOT / "examples" / "fictional-sr"
sys.path.insert(0, str(GATE.parent))


class TestFictionalSystematicReview(unittest.TestCase):
    """P5: a fictional systematic review exported through G4; every number from the ledger."""

    @classmethod
    def setUpClass(cls):
        cls.led = {r["id"]: r for r in json.loads((SR / "ledgers" / "results-ledger.json").read_text(encoding="utf-8"))["results"]}

    def test_gates_and_outputs(self):
        for args in (("G2",), ("G3",), ("G4", "--deliverable", "review")):
            r = subprocess.run([sys.executable, str(GATE), "check", str(SR), *args], capture_output=True, text=True,
                               encoding="utf-8")
            self.assertEqual(r.returncode, 0, f"{args}: {r.stdout}{r.stderr}")
        with zipfile.ZipFile(SR / "out" / "review.docx") as z:
            self.assertIn("word/document.xml", z.namelist())
        data = json.loads((SR / "reviews" / "audit.json").read_text(encoding="utf-8"))
        self.assertEqual((data["blocks"], data["deliverables"]), (0, ["review"]))
        for name in ("ai-use-disclosure.md", "author-decisions.md"):
            self.assertTrue((SR / "out" / name).read_text(encoding="utf-8").strip(), name)

    def test_ledger_holds_counts_pooled_heterogeneity_and_absolute_effects(self):
        for i in range(1, 12):
            rec = self.led[f"R-A0-{i:03d}"]
            self.assertEqual((rec["status"], rec["kind"]), ("observed", "n"))
        pooled = self.led["R-A1-001"]
        self.assertEqual((pooled["kind"], pooled["count"]), ("rr", 5))
        self.assertEqual(len(pooled["ci"]), 2)
        self.assertEqual(self.led["R-A1-002"]["kind"], "tau2")
        self.assertEqual(self.led["R-A1-003"]["kind"], "percent")
        self.assertEqual(len(self.led["R-A1-005"]["ci"]), 2)
        self.assertNotIn("R-A1-006", self.led)                      # k < 10: no Egger
        for i in (901, 902, 903):
            self.assertEqual(self.led[f"R-A1-{i}"]["kind"], "absolute")

    def test_logs_clean_and_text_uses_placeholders(self):
        import extract_check
        import screening
        self.assertEqual([f for f in screening.check(SR) if f[0] == "block"], [])
        self.assertEqual([f for f in extract_check.check(SR) if f[0] == "block"], [])
        results = (SR / "06_writing" / "review" / "04-results.md").read_text(encoding="utf-8")
        for s in ("{{R-A0-", "{{R-A1-001", "{{R-A1-003", "{{R-A1-005"):
            self.assertIn(s, results)
        figs = json.loads((SR / "07_present" / "figures" / "figures.json").read_text(encoding="utf-8"))["figures"]
        self.assertEqual({f["type"] for f in figs} >= {"prisma", "forest", "rob"}, True)

    def test_included_studies_are_fictional_manual_records(self):
        refs = json.loads((SR / "ledgers" / "references.json").read_text(encoding="utf-8"))["references"]
        studies = [r for r in refs if r.get("source") == "manual"]
        self.assertEqual(len(studies), 5)
        self.assertTrue(all(r["title"].startswith("Fictional") and r.get("seen_in") for r in studies))
        self.assertTrue(all(str(r.get("verified_by", "")).endswith("VERIFIED") for r in refs if r.get("source") != "manual"))
        self.assertIn("fictional", (SR / "README.md").read_text(encoding="utf-8").lower())


class TestFictionalCohortP6(unittest.TestCase):
    """P6: ethics dossier and CRF, journal shortlist from live lookups, one revision round to the response letter."""

    def script(self, name, *args):
        return subprocess.run([sys.executable, str(GATE.parent / name), *args], capture_output=True, text=True,
                              encoding="utf-8")

    def test_crf_and_ethics_documents(self):
        r = self.script("crf.py", str(EXAMPLE), "check")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for name in ("crf.md", "data-dictionary.csv", "consent-form.md", "dossier.md"):
            self.assertTrue((EXAMPLE / "03_protocol" / "ethics" / name).is_file(), name)
        for name in ("crf.docx", "consent-form.docx", "dossier.docx"):
            self.assertTrue(zipfile.is_zipfile(EXAMPLE / "out" / "ethics" / name), name)

    def test_journal_shortlist_from_lookups_and_the_authors_pick(self):
        from crolib import projectcfg
        data = json.loads((EXAMPLE / "08_submission" / "journals.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(data["journals"]), 2)
        for rec in data["journals"]:
            self.assertRegex(rec["looked_up"], r"^\d{4}-\d{2}-\d{2}$")
            self.assertTrue(rec["title"] and all(t["source"] for t in rec["title"]), rec["key"])
        picked = [r for r in data["journals"] if r.get("picked")]
        self.assertEqual(len(picked), 1)
        self.assertEqual(picked[0]["picked"]["by"], "Example author")
        self.assertEqual(projectcfg.get(EXAMPLE, "target.journal"), picked[0]["title"][0]["value"].replace('"', "'"))
        self.assertNotIn("predatory", (EXAMPLE / "08_submission" / "journals.md").read_text(encoding="utf-8").lower())

    def test_revision_round_and_letter(self):
        r = self.script("response.py", str(EXAMPLE), "check")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        data = json.loads((EXAMPLE / "09_revision" / "comments.json").read_text(encoding="utf-8"))
        self.assertTrue(data["approved"])
        for rel, sha in data["submitted"].items():
            self.assertEqual(hashlib.sha256((EXAMPLE / "09_revision" / "submitted" / rel).read_bytes()).hexdigest(), sha)
        text = (EXAMPLE / "09_revision" / "response.md").read_text(encoding="utf-8")
        for item in data["items"]:
            self.assertIn(f"## {item['id']}", text)
        self.assertIn("[[CHANGE:", text)
        self.assertIn("fictional", (EXAMPLE / "09_revision" / "comments-received.md").read_text(encoding="utf-8").lower())
        with zipfile.ZipFile(EXAMPLE / "out" / "response-letter.docx") as z:
            self.assertIn("word/document.xml", z.namelist())
        r = subprocess.run([sys.executable, str(GATE), "check", str(EXAMPLE), "G4", "--deliverable", "manuscript"],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertFalse((EXAMPLE / "out" / "ch3-results.docx").exists())


if __name__ == "__main__":
    unittest.main()
