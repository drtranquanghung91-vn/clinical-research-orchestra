import contextlib
import io
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
import assemble
import audit
import case_facts
import gate
import gate_hook
import guideline_checklist as gc
import worklog
from crolib import drafts, reviews
from p5_helpers import case_project, review_project

REF = {"id": "lee2020", "title": "Fictional similar case", "authors": ["Lee A"], "journal": "J", "year": 2020,
       "pmid": "1", "verified_by": "verify_refs.py 2026-11-22 VERIFIED", "abstract": "A fictional similar case."}
FACTS = "id,label,value,unit,day,source\nC01,haemoglobin at admission,78,g/L,0,lab report\n"
SIMILAR = ("ref_id,age_range,sex,presentation,key_finding,treatment,outcome\n" +
           "lee2020,40-49,F,fever,rash,drug,recovered\n" * 3)
CASE = {
    "00-title.md": "# Fever and rash after a fictional exposure\n",
    "01-abstract.md": "# Abstract\n\nA fictional woman in her 40s had haemoglobin {{R-A0-001.value}} g/L on day 0.\n",
    "03-patient-information.md": "# Patient information\n\nA woman in her 40s with fever since day -2.\n",
    "04-clinical-findings.md": "# Clinical findings\n\nHaemoglobin was {{R-A0-001.value}} g/L on day 0; a rash appeared on day +14.\n",
    "05-timeline.md": "# Timeline\n\nTable 1. Timeline\n| Day | Event |\n|---|---|\n| 0 | admission |\n| 3 | rash |\n",
    "09-discussion.md": "# Discussion\n\nSimilar fictional cases were reported [@lee2020].\n",
    "11-consent.md": "# Informed consent\n\nWritten consent was obtained from the patient.\n",
}
CARE_IDS = ["1", "2", "3a", "3b", "3c", "3d", "4", "5a", "5b", "5c", "5d", "6", "7", "8a", "8b", "8c", "8d", "9a", "9b",
            "9c", "10a", "10b", "10c", "10d", "11a", "11b", "11c", "11d", "12", "13"]


def quiet(fn, *args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = fn(*args)
    return code, out.getvalue(), err.getvalue()


def write_reports(p: Path, d: str, guideline: str, ids: list[str]) -> None:
    dg = drafts.digest(p, d)
    for agent, (rel, crits) in reviews.REVIEWERS.items():
        (p / rel).write_text(f"STATUS: PASS\nFINDINGS\n| code | location | fix |\ndrafts-digest: {d} {dg}\n"
                             f"```scores\n{json.dumps({'deliverable': d, **dict.fromkeys(crits, 2)})}\n```\n", encoding="utf-8")
    (p / "reviews" / f"guideline-checklist-{d}.json").write_text(json.dumps(
        {"guideline": guideline, "deliverable": d, "items": {i: {"status": "na", "reason": "fixture"} for i in ids}}),
        encoding="utf-8")


def set_style(p: Path, style: str) -> None:
    y = (p / "project.yaml").read_text(encoding="utf-8")
    (p / "project.yaml").write_text(re.sub(r"(?m)^  journal_style:.*$", f"  journal_style: {style}", y), encoding="utf-8")


class TestDrafts(unittest.TestCase):
    def setUp(self):
        self.t = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.t, ignore_errors=True)

    def test_orders_required_and_roles(self):
        c = case_project(self.t)
        self.assertEqual(drafts.variant(c, "case-report"), "care")
        self.assertEqual(drafts.default_order(c, "case-report")[3], "03-patient-information.md")
        self.assertIn("11-consent.md", drafts.required(c, "case-report"))
        set_style(c, "bmj")
        self.assertEqual(drafts.variant(c, "case-report"), "bmj")
        self.assertEqual(set(drafts.required(c, "case-report")),
                         {"03-case-presentation.md", "08-discussion.md", "09-learning-points.md", "11-consent.md"})
        s = review_project(self.t / "s")
        self.assertEqual(drafts.review_kind(s), "systematic")
        self.assertIn("sof.md", drafts.default_order(s, "review"))
        sc = review_project(self.t / "sc", design="scoping-review")
        self.assertNotIn("sof.md", drafts.default_order(sc, "review"))
        nr = review_project(self.t / "n", design="narrative-review")
        self.assertIn("04-*.md", drafts.default_order(nr, "review"))
        self.assertEqual(set(drafts.required(nr, "review")), {"02-introduction.md", "03-methods.md", "06-conclusion.md"})
        self.assertEqual(drafts.default_order(c, "thesis"), drafts.DEFAULT_ORDER["thesis"])   # unchanged
        self.assertEqual(drafts.role_of("06_writing/case-report/04-clinical-findings.md"), "case-presentation")
        self.assertTrue(drafts.results_bearing("06_writing/case-report/01-abstract.md"))
        self.assertTrue(drafts.results_bearing("06_writing/review/sof.md"))
        self.assertTrue(drafts.is_literature("06_writing/review/04-themes.md"))
        self.assertFalse(drafts.is_literature("06_writing/review/04-results.md"))
        self.assertFalse(drafts.is_literature("06_writing/case-report/02-introduction.md"))
        self.assertTrue(drafts.results_bearing("06_writing/thesis/ch4-discussion.md"))
        self.assertTrue(reviews.DIGEST.search("drafts-digest: case-report " + "a" * 64))
        self.assertTrue(reviews.DIGEST.search("drafts-digest: review " + "b" * 64))
        self.assertEqual(gc.DELIVERABLES, drafts.DELIVERABLES)
        self.assertEqual(gate.DELIVERABLES, drafts.DELIVERABLES)
        self.assertEqual(worklog.TEXT["vi"]["case-report"], "báo cáo ca bệnh")


class TestCaseReportDeliverable(unittest.TestCase):
    def setUp(self):
        self.t = Path(tempfile.mkdtemp())
        p = self.p = case_project(self.t)
        (p / "01_case" / "facts.csv").write_text(FACTS, encoding="utf-8")
        (p / "01_case" / "similar-cases.csv").write_text(SIMILAR, encoding="utf-8")
        (p / "ledgers" / "references.json").write_text(json.dumps({"references": [REF]}), encoding="utf-8")
        self.assertEqual(quiet(case_facts.main, [str(p)])[0], 0)
        self.d = p / "06_writing" / "case-report"
        for name, text in CASE.items():
            (self.d / name).write_text(text, encoding="utf-8")
        (p / "decisions.md").write_text("# Decisions\n\nCONSENT: obtained written consent form, signed by the patient\n",
                                        encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.t, ignore_errors=True)

    def test_assemble_draft_and_required_sections(self):
        code, out, _ = quiet(assemble.main, [str(self.p), "case-report"])
        self.assertEqual(code, 0, out)
        text = (self.d / "case-report.assembled.md").read_text(encoding="utf-8")
        self.assertIn("haemoglobin 78 g/L", text)
        self.assertTrue((self.d / "case-report.draft.docx").is_file())
        (self.d / "11-consent.md").unlink()
        code, out, _ = quiet(assemble.main, [str(self.p), "case-report"])
        self.assertEqual(code, 1)
        self.assertIn("required section missing: Informed consent (11-consent.md)", out)

    def test_audit_case_report(self):
        write_reports(self.p, "case-report", "CARE", CARE_IDS)
        code, out, err = quiet(audit.main, [str(self.p), "case-report"])
        data = json.loads((self.p / "reviews" / "audit.json").read_text(encoding="utf-8"))
        codes = {f["code"] for f in data["findings"] if f["level"] == "block"}
        self.assertNotIn("E-STAT", {f["code"] for f in data["findings"]})       # no register in a case report
        self.assertNotIn("E-NUM", codes, data["findings"])                       # "day +14" is relative time (D20)
        self.assertEqual(data["deliverables"], ["case-report"])
        self.assertIn("01_case/facts.csv", data["files"])
        self.assertIn("E-CASE", (self.p / "reviews" / "audit.md").read_text(encoding="utf-8"))
        (self.d / "03-patient-information.md").write_text("# Patient information\n\nA 45-year-old woman.\n", encoding="utf-8")
        write_reports(self.p, "case-report", "CARE", CARE_IDS)
        quiet(audit.main, [str(self.p), "case-report"])
        data = json.loads((self.p / "reviews" / "audit.json").read_text(encoding="utf-8"))
        self.assertTrue(any(f["code"] == "E-CASE" and f["level"] == "block" for f in data["findings"]))

    def test_final_export_needs_recorded_consent(self):
        (self.p / "reviews" / "audit.json").write_text(json.dumps(
            {"deliverable": "case-report", "deliverables": ["case-report"], "at": "t", "blocks": 0, "warns": 0,
             "files": {rel: gate.sha256(self.p / rel) for rel in
                       [p.relative_to(self.p).as_posix() for p in drafts.tracked_files(self.p, "case-report")]}}),
            encoding="utf-8")
        gate.open_gate(self.p, "G4", by="A")
        self.assertEqual(gate.export_problems(self.p, "case-report"), [])
        (self.p / "decisions.md").write_text("# Decisions\n", encoding="utf-8")
        probs = gate.export_problems(self.p, "case-report")
        self.assertTrue(any("consent" in x for x in probs), probs)
        d = gate_hook.decide({"tool_name": "Bash", "tool_input": {"command": "python /x/assemble.py . case-report --final"},
                              "cwd": str(self.p)})
        self.assertEqual(d["permissionDecision"], "deny")
        self.assertIn("consent", d["permissionDecisionReason"])


class TestReviewDeliverable(unittest.TestCase):
    def setUp(self):
        self.t = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.t, ignore_errors=True)

    def test_hook_prep_marker_needs_g2_and_final_review_needs_g4(self):
        p = review_project(self.t, g2=False)
        payload = {"tool_name": "Agent", "tool_input": {"prompt": "orchestra-prep: screen-suggest\nSuggest decisions."},
                   "cwd": str(p)}
        d = gate_hook.decide(payload)
        self.assertEqual(d["permissionDecision"], "deny")
        self.assertIn("G2", d["permissionDecisionReason"])
        gate.open_gate(p, "G2", by="A", files=["03_protocol/sr-protocol.md"])
        self.assertIsNone(gate_hook.decide(payload))
        d = gate_hook.decide({"tool_name": "Agent", "tool_input": {"prompt": "orchestra-role: review-systematic\nDraft."},
                              "cwd": str(p)})
        self.assertEqual(d["permissionDecision"], "deny")                     # writing still needs G3
        d = gate_hook.decide({"tool_name": "Bash", "cwd": str(p), "tool_input": {
            "command": "python /x/build_docx.py 06_writing/review/review.assembled.md out/review.docx --project ."}})
        self.assertEqual(d["permissionDecision"], "deny")

    def test_audit_review_rows(self):
        p = review_project(self.t)
        d = p / "06_writing" / "review"
        for name in ("02-introduction.md", "03-methods.md", "04-results.md", "05-discussion.md"):
            (d / name).write_text(f"# {name[3:-3].title()}\n\nFictional text.\n", encoding="utf-8")
        (d / "04-results.md").write_text("# Results\n\nDrug X reduces mortality ({{R-A1-001.full}}).\n", encoding="utf-8")
        (p / "ledgers" / "results-ledger.json").write_text(json.dumps({"results": [
            {"id": "R-A1-001", "analysis_id": "A1", "status": "prespecified", "label": "pooled RR", "value": 0.7,
             "ci": [0.5, 0.98], "count": 3, "n": 300, "kind": "rr", "source_file": "x", "locator": "line 1", "raw": "x"}]}),
            encoding="utf-8")
        (p / "05_analysis" / "meta").mkdir(parents=True, exist_ok=True)
        (p / "05_analysis" / "meta" / "grade.json").write_text(json.dumps({"outcomes": [{
            "outcome": "Mortality", "result": "R-A1-001", "design": "rct", "rob_tool": "RoB 2",
            "downgrades": {"risk_of_bias": [-1, "fictional"], "inconsistency": [-1, "fictional"]}}]}), encoding="utf-8")
        write_reports(p, "review", "PRISMA-2020", [])
        quiet(audit.main, [str(p), "review"])
        data = json.loads((p / "reviews" / "audit.json").read_text(encoding="utf-8"))
        codes = {(f["code"], f["level"]) for f in data["findings"]}
        self.assertIn(("E-SCR", "block"), codes)            # no screening log
        self.assertIn(("E-GRADE", "warn"), codes)           # low certainty, unhedged
        self.assertTrue(any(f["code"] == "E-STAT" for f in data["findings"]))   # register read from sr-protocol.md
        n = review_project(self.t / "n", design="narrative-review")
        (n / "06_writing" / "review" / "02-introduction.md").write_text("# Introduction\n\nText.\n", encoding="utf-8")
        write_reports(n, "review", "SANRA", [])
        quiet(audit.main, [str(n), "review"])
        data = json.loads((n / "reviews" / "audit.json").read_text(encoding="utf-8"))
        self.assertFalse({"E-SCR", "E-STAT"} & {f["code"] for f in data["findings"]})

    def test_worklog_digest_and_gate_check_accept_new_deliverables(self):
        p = review_project(self.t)
        (p / "06_writing" / "review" / "02-introduction.md").write_text("# Introduction\n", encoding="utf-8")
        code, out, _ = quiet(worklog.main, ["digest", str(p), "review"])
        self.assertEqual(code, 0)
        self.assertRegex(out, r"drafts-digest: review [0-9a-f]{64}")
        self.assertEqual(quiet(gate.main, ["check", str(p), "G4", "--deliverable", "review"])[0], 1)
