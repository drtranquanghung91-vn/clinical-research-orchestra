"""Scenario files have the required lines; the P3 scenario fixtures produce the findings their scenarios rely on."""
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

import _paths  # noqa: F401
from _paths import ORCH_SCRIPTS, ROOT

SCEN = ROOT / "tests" / "scenarios"
FIX = SCEN / "fixtures"
REQUIRED = ("Fixtures:", "Allowed tools:", "Prompt:", "Expected (GREEN)", "Baseline (RED):")
P3 = ("mzl-consistency", "poster-87dpi", "humanizer-invariants", "vi-dense-prose")


def run(script: str, *args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(ORCH_SCRIPTS / script), *args], cwd=cwd, capture_output=True,
                          text=True, encoding="utf-8")


def idat_pixels(png: bytes) -> bytes:
    data, pos = b"", 8
    while pos < len(png):
        n = int.from_bytes(png[pos:pos + 4], "big")
        if png[pos + 4:pos + 8] == b"IDAT":
            data += png[pos + 8:pos + 8 + n]
        pos += 12 + n
    return zlib.decompress(data)


class ScenarioFormatTest(unittest.TestCase):
    def test_every_scenario_has_the_required_lines(self):
        files = sorted(p for p in SCEN.glob("*.md") if p.name not in {"README.md", "BASELINE.md"})
        self.assertGreaterEqual(len(files), 15)
        for f in files:
            text = f.read_text(encoding="utf-8")
            with self.subTest(scenario=f.name):
                self.assertRegex(text.splitlines()[0], r"^# " + re.escape(f.stem) + r": ")
                self.assertRegex(text, r"(?m)^Skill(?:/hook)? under test: ")
                for line in REQUIRED:
                    self.assertIn("\n" + line, text)

    def test_p3_scenarios_have_fixtures_and_lf_only(self):
        for sid in P3:
            with self.subTest(scenario=sid):
                self.assertTrue((SCEN / f"{sid}.md").is_file())
                fdir = FIX / sid
                self.assertTrue(fdir.is_dir())
                for p in fdir.rglob("*"):
                    if p.is_file() and p.suffix not in (".png", ".pyc") and "__pycache__" not in p.parts:
                        self.assertNotIn(b"\r\n", p.read_bytes(), str(p))


class P3FixtureTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def copy(self, sid: str) -> Path:
        dst = self.tmp / sid
        shutil.copytree(FIX / sid, dst)
        return dst

    def test_mzl_consistency_g3_locked_and_three_blocks(self):
        proj = self.copy("mzl-consistency")
        self.assertEqual(run("gate.py", "check", ".", "G3", cwd=proj).returncode, 0)
        r = run("consistency_audit.py", ".", cwd=proj)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        blocks = [ln for ln in (r.stdout + r.stderr).splitlines() if ln.startswith("E-CONS block")]
        self.assertEqual(len(blocks), 3, blocks)
        joined = "\n".join(blocks)
        self.assertIn("86,3%", joined)
        self.assertIn("≈26", joined)
        self.assertIn("06/2025", joined)

    def test_poster_87dpi_png_is_the_generator_output(self):
        fdir = FIX / "poster-87dpi"
        spec = importlib.util.spec_from_file_location("make_figure", fdir / "make_figure.py")
        mod = importlib.util.module_from_spec(spec)
        old, sys.dont_write_bytecode = sys.dont_write_bytecode, True  # no __pycache__ in the fixture
        try:
            spec.loader.exec_module(mod)
        finally:
            sys.dont_write_bytecode = old
        png = (fdir / "07_present" / "figures" / "F1.png").read_bytes()
        # Compare pixels, not compressed bytes: another zlib build may compress the same data differently.
        self.assertEqual(idat_pixels(png), idat_pixels(mod.png_bytes()))
        self.assertEqual(png[16:24], (600).to_bytes(4, "big") + (400).to_bytes(4, "big"))
        poster = json.loads((fdir / "07_present" / "poster" / "poster.json").read_text(encoding="utf-8"))
        pinned = [s for s in poster["sections"] if isinstance(s.get("figure"), dict) and s["figure"]["id"] == "F1"]
        self.assertEqual(pinned[0]["figure_width_cm"], 17.5)
        self.assertEqual(round(600 / (17.5 / 2.54)), 87)
        self.assertEqual(run("gate.py", "check", ".", "G3", cwd=self.copy("poster-87dpi")).returncode, 0)

    def test_vi_dense_prose_blocks_and_humanizer_paragraph_is_clean(self):
        dense = self.copy("vi-dense-prose")
        r = run("lint_prose.py", "06_writing/thesis/ch4-discussion.md", "--lang", "vi", cwd=dense)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        out = r.stdout + r.stderr
        for code in ("P01", "P02", "P03", "P06", "P00 block"):
            self.assertIn(code, out)
        text = (FIX / "humanizer-invariants" / "06_writing" / "thesis" / "ch4-discussion.md").read_text(encoding="utf-8")
        for s in ("OR 1,42 (KTC 95%: 1,05–1,91)", "có thể", "[@tran2022]", "{{R-A1-001.full}}"):
            self.assertIn(s, text)


P4 = ("thesis-g3-closed", "discussion-overclaim", "g4-export-blocked", "revise-revert")


class P4FixtureTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def copy(self, sid: str) -> Path:
        dst = self.tmp / sid
        shutil.copytree(FIX / sid, dst)
        return dst

    def hook(self, payload: dict) -> dict | None:
        r = subprocess.run([sys.executable, str(ORCH_SCRIPTS / "gate_hook.py")], input=json.dumps(payload),
                           capture_output=True, text=True, encoding="utf-8")
        return json.loads(r.stdout)["hookSpecificOutput"] if r.stdout.strip() else None

    def test_p4_scenarios_have_fixtures_and_lf_only(self):
        for sid in P4:
            with self.subTest(scenario=sid):
                self.assertTrue((SCEN / f"{sid}.md").is_file())
                for p in (FIX / sid).rglob("*"):
                    if p.is_file():
                        self.assertNotIn(b"\r\n", p.read_bytes(), str(p))

    def test_thesis_g3_closed(self):
        proj = self.copy("thesis-g3-closed")
        self.assertEqual(run("gate.py", "check", ".", "G3", cwd=proj).returncode, 1)
        d = self.hook({"tool_name": "Agent", "tool_input": {"prompt": "orchestra-role: discussion\nDraft Chương 4."},
                       "cwd": str(proj)})
        self.assertEqual(d["permissionDecision"], "deny")
        self.assertIn("G3", d["permissionDecisionReason"])

    def test_discussion_overclaim_data(self):
        proj = self.copy("discussion-overclaim")
        self.assertEqual(run("gate.py", "check", ".", "G3", cwd=proj).returncode, 0)
        recs = json.loads((proj / "ledgers" / "results-ledger.json").read_text(encoding="utf-8"))["results"]
        ors = [r for r in recs if r.get("analysis_id") == "A1" and r.get("kind") == "or"
               and re.match(r"(crude OR, HbA1c|OR C\(hba1c_grp3)", str(r.get("label", "")))]  # exposure terms, not covariates
        self.assertTrue(ors)
        self.assertTrue(all(r["ci"][0] <= 1 <= r["ci"][1] for r in ors))
        self.assertFalse(any(re.search(r"trend|xu hướng", str(r.get("label", "")), re.I) for r in recs))
        self.assertFalse((proj / "06_writing" / "thesis" / "ch4-discussion.md").exists())

    def test_g4_export_blocked(self):
        proj = self.copy("g4-export-blocked")
        r = run("audit.py", ".", "thesis", cwd=proj)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        data = json.loads((proj / "reviews" / "audit.json").read_text(encoding="utf-8"))
        blocks = [f for f in data["findings"] if f["level"] == "block"]
        self.assertEqual({f["code"] for f in blocks}, {"E-REF"}, blocks)
        self.assertTrue(any("pham2019" in f["msg"] for f in blocks))
        self.assertEqual(run("gate.py", "open", ".", "G4", "--by", "A", cwd=proj).returncode, 1)
        d = self.hook({"tool_name": "Bash", "tool_input": {"command": "python x/assemble.py . thesis --final"},
                       "cwd": str(proj)})
        self.assertEqual(d["permissionDecision"], "deny")
        self.assertIn("G4", d["permissionDecisionReason"])

    def test_revise_revert(self):
        proj = self.copy("revise-revert")
        digest = run("worklog.py", "digest", ".", "thesis", cwd=proj).stdout.strip()
        for rel in ("reviews/citation-verifier.md", "reviews/statistical-reviewer.md", "reviews/consistency.md",
                    "reviews/reporting-guideline-checker.md", "reviews/scientific-editor.md"):
            self.assertIn(digest, (proj / rel).read_text(encoding="utf-8"), rel)
        log = json.loads((proj / "reviews" / "worklog.json").read_text(encoding="utf-8"))["rounds"][0]
        self.assertEqual((log["round"], log["total"], log["decision"]), (1, 15, "KEEP"))
        self.assertNotEqual((proj / "06_writing/thesis/ch4-discussion.md").read_bytes(),
                            (proj / "reviews/rounds/thesis/r1/ch4-discussion.md").read_bytes())
        r = run("worklog.py", "score", ".", "thesis", "--round", "2", cwd=proj)
        self.assertEqual(r.stdout.strip().splitlines()[-1], "REVERT", r.stdout + r.stderr)
        self.assertEqual(run("worklog.py", "revert", ".", "thesis", cwd=proj).returncode, 0)
        self.assertEqual((proj / "06_writing/thesis/ch4-discussion.md").read_bytes(),
                         (proj / "reviews/rounds/thesis/r1/ch4-discussion.md").read_bytes())
        self.assertEqual(run("worklog.py", "decisions", ".", cwd=proj).returncode, 0)
        self.assertIn("giới tính", (proj / "out" / "author-decisions.md").read_text(encoding="utf-8"))


P5 = ("case-identifiers", "case-consent-missing", "sr-single-screener", "sr-pool-heterogeneous", "scoping-asks-pooling")


class P5FixtureTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def copy(self, sid: str) -> Path:
        dst = self.tmp / sid
        shutil.copytree(FIX / sid, dst)
        return dst

    def hook(self, payload: dict) -> dict | None:
        r = subprocess.run([sys.executable, str(ORCH_SCRIPTS / "gate_hook.py")], input=json.dumps(payload),
                           capture_output=True, text=True, encoding="utf-8")
        return json.loads(r.stdout)["hookSpecificOutput"] if r.stdout.strip() else None

    def test_p5_scenarios_have_fixtures_and_lf_only(self):
        for sid in P5:
            with self.subTest(scenario=sid):
                self.assertTrue((SCEN / f"{sid}.md").is_file())
                for p in (FIX / sid).rglob("*"):
                    if p.is_file():
                        self.assertNotIn(b"\r\n", p.read_bytes(), str(p))

    def test_case_identifiers_notes_hold_identifiers(self):
        proj = self.copy("case-identifiers")
        shutil.copy(proj / "00_inputs" / "case-notes.md", proj / "01_case" / "dossier.md")
        r = run("case_lint.py", ".", cwd=proj)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        for s in ("calendar date", "exact age", "names the institution or city"):
            self.assertIn(s, r.stdout)

    def test_case_consent_missing(self):
        proj = self.copy("case-consent-missing")
        self.assertEqual(run("gate.py", "check", ".", "G3", cwd=proj).returncode, 0)
        r = run("case_lint.py", ".", "--strict", cwd=proj)
        self.assertEqual(r.returncode, 1)
        self.assertIn("consent not recorded", r.stdout)
        d = self.hook({"tool_name": "Bash", "tool_input": {"command": "python /x/assemble.py . case-report --final"},
                       "cwd": str(proj)})
        self.assertEqual(d["permissionDecision"], "deny")
        self.assertIn("consent", d["permissionDecisionReason"])

    def test_sr_single_screener(self):
        proj = self.copy("sr-single-screener")
        self.assertEqual(run("gate.py", "check", ".", "G2", cwd=proj).returncode, 0)
        self.assertFalse((proj / "02_evidence" / "sr" / "screening.csv").exists())
        self.assertEqual(len((proj / "02_evidence" / "sr" / "records.csv").read_text(encoding="utf-8").splitlines()), 7)
        r = run("screening.py", ".", "decide", "--stage", "ta", "--reviewer", "Claude", "--rec", "rec-0001",
                "--decision", "include", cwd=proj)
        self.assertEqual(r.returncode, 1)
        self.assertIn("looks like an AI", r.stdout)

    def test_sr_pool_heterogeneous_is_heterogeneous(self):
        proj = self.copy("sr-pool-heterogeneous")
        r = run("meta.py", ".", "run", cwd=proj)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        led = {x["id"]: x for x in json.loads((proj / "ledgers" / "results-ledger.json").read_text(encoding="utf-8"))["results"]}
        self.assertGreater(led["R-A1-003"]["value"], 50)                      # I² high
        lo, hi = led["R-A1-005"]["ci"]
        self.assertTrue(lo < 1 < hi)                                          # prediction interval crosses 1

    def test_scoping_asks_pooling_is_refused_by_meta(self):
        proj = self.copy("scoping-asks-pooling")
        r = run("meta.py", ".", "run", cwd=proj)
        self.assertEqual(r.returncode, 1)
        self.assertIn("do not pool", r.stdout)
        self.assertFalse((proj / "04_data" / "sr" / "rob.csv").exists())
        self.assertEqual(run("extract_check.py", ".", cwd=proj).returncode, 0)


P6 = ("crf-missing-variable", "journal-predatory-signals", "reviewer-asks-new-analysis", "response-claims-unmade-change")


class P6FixtureTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def copy(self, sid: str) -> Path:
        dst = self.tmp / sid
        shutil.copytree(FIX / sid, dst)
        return dst

    def test_p6_scenarios_have_fixtures_and_lf_only(self):
        for sid in P6:
            with self.subTest(scenario=sid):
                self.assertTrue((SCEN / f"{sid}.md").is_file())
                for p in (FIX / sid).rglob("*"):
                    if p.is_file():
                        self.assertNotIn(b"\r\n", p.read_bytes(), str(p))

    def test_crf_missing_variable_blocks_on_bmi_and_keeps_g2(self):
        p = self.copy("crf-missing-variable")
        self.assertEqual(run("crf.py", ".", "build", cwd=p).returncode, 0)
        r = run("crf.py", ".", "check", cwd=p)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("uses 'BMI', which matches no CRF variable", r.stdout)
        self.assertEqual(run("gate.py", "check", ".", "G2", cwd=p).returncode, 0)

    def test_journal_fixture_has_no_target_journal(self):
        sys.path.insert(0, str(ORCH_SCRIPTS))
        from crolib import projectcfg
        p = FIX / "journal-predatory-signals"
        self.assertIsNone(projectcfg.get(p, "target.journal"))
        text = (p / "08_submission" / "invitation.md").read_text(encoding="utf-8")
        for s in ("0000-0019", "MEDLINE", "Fictional"):
            self.assertIn(s, text)

    def test_reviewer_fixture_g4_open_and_init_splits_the_comments(self):
        p = self.copy("reviewer-asks-new-analysis")
        self.assertEqual(run("gate.py", "check", ".", "G4", "--deliverable", "manuscript", cwd=p).returncode, 0)
        self.assertEqual(run("response.py", ".", "init", "09_revision/comments-received.md", cwd=p).returncode, 0)
        items = json.loads((p / "09_revision" / "comments.json").read_text(encoding="utf-8"))["items"]
        self.assertEqual([i["id"] for i in items], ["E1", "R1.1", "R1.2", "R2.1"])
        self.assertIn("subgroup analysis by sex", items[1]["text"])

    def test_response_fixture_blocks_on_the_unmade_change(self):
        p = self.copy("response-claims-unmade-change")
        r = run("response.py", ".", "check", cwd=p)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("R1.2: the response says the manuscript was changed but gives no", r.stdout)
        self.assertNotIn("R1.1:", " ".join(ln for ln in r.stdout.splitlines() if " block " in ln))


if __name__ == "__main__":
    unittest.main()
