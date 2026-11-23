import contextlib
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
import init_project
from crolib import ledgers


class TestInitProject(unittest.TestCase):
    def test_creates_full_skeleton(self):
        with tempfile.TemporaryDirectory() as t:
            dest = Path(t) / "pmos-study"
            init_project.create(dest, "Lifestyle in PMOS", "thesis-masters", "rct", "vi", "vi")
            for d in ["00_inputs", "01_question", "02_evidence", "03_protocol", "04_data",
                      "05_analysis", "06_writing", "07_present", "ledgers", "gates", "reviews", "out"]:
                self.assertTrue((dest / d).is_dir(), d)
            y = (dest / "project.yaml").read_text(encoding="utf-8")
            self.assertIn('title: "Lifestyle in PMOS"', y)
            self.assertIn("reporting_guideline: CONSORT-2025", y)
            self.assertIn("output: vi", y)
            self.assertIn("| 1 Question |", (dest / "STATUS.md").read_text(encoding="utf-8"))
            self.assertEqual(ledgers.check_project(dest), [])
            self.assertEqual(json.loads((dest / "gates" / "state.json").read_text(encoding="utf-8")), {})

    # I8: a new project keeps raw inputs, key files and non-de-identified data out of git
    def test_new_project_has_gitignore(self):
        with tempfile.TemporaryDirectory() as t:
            dest = init_project.create(Path(t) / "p", "A", "manuscript", "cohort", "en", "vi")
            lines = (dest / ".gitignore").read_text(encoding="utf-8").splitlines()
            for rule in ("00_inputs/", "*.key.csv", "04_data/*", "!04_data/*.deid.csv", "!04_data/.gitkeep"):
                self.assertIn(rule, lines)

    def test_new_project_gitignore_works_in_git(self):
        if not shutil.which("git"):
            self.skipTest("git not installed")
        with tempfile.TemporaryDirectory() as t:
            dest = init_project.create(Path(t) / "p", "A", "manuscript", "cohort", "en", "vi")
            subprocess.run(["git", "init", "-q", str(dest)], check=True, capture_output=True)

            def ignored(rel):
                return subprocess.run(["git", "-C", str(dest), "check-ignore", "-q", "--no-index", rel],
                                      capture_output=True).returncode == 0
            for rel in ("00_inputs/data.xlsx", "04_data/data.csv", "04_data/data.key.csv", "x/y.key.csv"):
                self.assertTrue(ignored(rel), rel)
            for rel in ("04_data/data.deid.csv", "04_data/.gitkeep", "project.yaml", "ledgers/references.json"):
                self.assertFalse(ignored(rel), rel)

    def test_repo_does_not_ignore_template_gitignore(self):
        if not shutil.which("git") or not (_paths.ROOT / ".git").exists():
            self.skipTest("not a git checkout")
        rel = "plugins/orchestra/templates/project/.gitignore"
        r = subprocess.run(["git", "-C", str(_paths.ROOT), "check-ignore", "-q", "--no-index", rel],
                           capture_output=True)
        self.assertEqual(r.returncode, 1, "repo .gitignore hides the template .gitignore")

    def test_refuses_existing_project(self):
        with tempfile.TemporaryDirectory() as t:
            dest = Path(t) / "p"
            init_project.create(dest, "A", "manuscript", "cohort", "en", "vi")
            with self.assertRaises(FileExistsError):
                init_project.create(dest, "A", "manuscript", "cohort", "en", "vi")

    def test_rejects_unknown_design(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):
                init_project.create(Path(t) / "p", "A", "manuscript", "astrology", "en", "en")

    # I10: input errors -> stderr + exit 2
    def _main(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = init_project.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_main_existing_project_exits_2(self):
        with tempfile.TemporaryDirectory() as t:
            dest = str(Path(t) / "p")
            args = [dest, "--title", "A", "--type", "manuscript", "--design", "cohort"]
            self.assertEqual(self._main(args)[0], 0)
            code, out, err = self._main(args)
            self.assertEqual(code, 2)
            self.assertIn("already has project.yaml", err)
            self.assertNotIn("created", out)

    def test_main_destination_is_a_file_exits_2(self):
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / "afile"
            f.write_text("x", encoding="utf-8")
            code, out, err = self._main([str(f), "--title", "A", "--type", "manuscript", "--design", "cohort"])
            self.assertEqual(code, 2)
            self.assertIn("init_project:", err)

    def test_main_bad_choice_exits_2(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(SystemExit) as cm, contextlib.redirect_stderr(io.StringIO()):
                init_project.main([str(Path(t) / "p"), "--title", "A", "--type", "x", "--design", "cohort"])
            self.assertEqual(cm.exception.code, 2)

    def test_guideline_map_covers_all_designs(self):
        for d in init_project.DESIGNS:
            self.assertIn(d, init_project.GUIDELINE_BY_DESIGN)

    def test_gitignore_versions_codebook_and_cleaning_log(self):
        with tempfile.TemporaryDirectory() as t:
            dest = init_project.create(Path(t) / "p", "A", "manuscript", "cohort", "en", "vi")
            gi = (dest / ".gitignore").read_text(encoding="utf-8")
            self.assertIn("!04_data/codebook.md", gi)
            self.assertIn("!04_data/cleaning-log.md", gi)
            self.assertIn("04_data/*", gi)

    def test_creates_thesis_and_manuscript_folders(self):
        with tempfile.TemporaryDirectory() as t:
            dest = init_project.create(Path(t) / "p", "A", "manuscript", "cohort", "en", "vi")
            self.assertTrue((dest / "06_writing" / "thesis").is_dir())
            self.assertTrue((dest / "06_writing" / "manuscript").is_dir())

    def test_project_yaml_has_docx_block(self):
        with tempfile.TemporaryDirectory() as t:
            dest = init_project.create(Path(t) / "p", "A", "manuscript", "cohort", "en", "vi")
            y = (dest / "project.yaml").read_text(encoding="utf-8")
            self.assertIn("\ndocx:\n", y)
            for key in ("font:", "size_pt:", "line_spacing:", "margins_cm:"):
                self.assertIn(key, y)


class TestInitP5(unittest.TestCase):
    def test_type_design_pairs_folders_and_keys(self):
        from crolib import projectcfg
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            with self.assertRaises(ValueError):
                init_project.create(t / "a", "A", "review", "systematic-review", "en", "vi")
            with self.assertRaises(ValueError):
                init_project.create(t / "b", "A", "case-report", "cohort", "en", "vi")
            c = init_project.create(t / "c", "A", "case-report", "case-report", "en", "vi")
            self.assertTrue((c / "01_case").is_dir() and (c / "06_writing" / "case-report").is_dir())
            self.assertFalse((c / "04_data" / "sr").exists())
            s = init_project.create(t / "s", "A", "systematic-review", "systematic-review", "en", "vi")
            for d in ("02_evidence/sr", "04_data/sr", "05_analysis/meta", "06_writing/review"):
                self.assertTrue((s / d).is_dir(), d)
            n = init_project.create(t / "n", "A", "review", "narrative-review", "en", "vi")
            self.assertTrue((n / "06_writing" / "review").is_dir())
            self.assertFalse((n / "02_evidence" / "sr").exists())
            self.assertIn("reporting_guideline: SANRA", (n / "project.yaml").read_text(encoding="utf-8"))
            self.assertEqual(projectcfg.parse_list(projectcfg.get(s, "review.reviewers", "")), [])
            for key in ("review.registration", "target.journal_style", "tools.rscript", "institution.city"):
                self.assertIsNone(projectcfg.get(s, key), key)
            m = init_project.create(t / "m", "A", "thesis-masters", "cohort", "vi", "vi")   # P1-P4 types unchanged
            self.assertFalse((m / "01_case").exists())

    def test_review_and_case_designs_need_their_type(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            for i, (ptype, design) in enumerate((("thesis-masters", "case-report"), ("manuscript", "systematic-review"),
                                                 ("thesis-phd", "scoping-review"), ("poster-only", "narrative-review"),
                                                 ("systematic-review", "scoping-review"), ("review", "case-report"))):
                with self.subTest(ptype=ptype, design=design):
                    with self.assertRaises(ValueError):
                        init_project.create(t / f"x{i}", "A", ptype, design, "en", "vi")
                    self.assertFalse((t / f"x{i}" / "project.yaml").exists())
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                code = init_project.main([str(t / "cli"), "--title", "A", "--type", "thesis-masters", "--design", "case-report"])
            self.assertEqual(code, 2)
            self.assertIn("case-report", err.getvalue())
            primary = [d for d in init_project.DESIGNS
                       if d not in ("case-report", "systematic-review", "scoping-review", "narrative-review")]
            n = 0
            for ptype in ("thesis-ckii", "thesis-masters", "thesis-phd", "de-tai-co-so", "manuscript", "poster-only"):
                for design in primary:                                    # every P1-P4 combination still accepted
                    n += 1
                    init_project.create(t / f"ok{n}", "A", ptype, design, "vi", "vi")

    def test_review_data_folder_is_versioned(self):
        if not shutil.which("git"):
            self.skipTest("git not installed")
        with tempfile.TemporaryDirectory() as t:
            dest = init_project.create(Path(t) / "p", "A", "systematic-review", "systematic-review", "en", "vi")
            subprocess.run(["git", "init", "-q", str(dest)], check=True, capture_output=True)
            ignored = lambda rel: subprocess.run(["git", "-C", str(dest), "check-ignore", "-q", "--no-index", rel],  # noqa: E731
                                                 capture_output=True).returncode == 0
            self.assertFalse(ignored("04_data/sr/extraction.csv"))
            self.assertTrue(ignored("04_data/raw.csv"))


class TestInitP6(unittest.TestCase):
    def test_ethics_for_every_type_submission_and_revision_for_publishing_types(self):
        for ptype, design, publishing in (("thesis-masters", "cohort", False), ("de-tai-co-so", "cohort", False),
                                          ("poster-only", "cohort", False), ("manuscript", "cohort", True),
                                          ("case-report", "case-report", True),
                                          ("systematic-review", "systematic-review", True),
                                          ("review", "scoping-review", True)):
            with tempfile.TemporaryDirectory() as t:
                p = init_project.create(Path(t) / "p", "T", ptype, design, "vi", "vi")
                with self.subTest(type=ptype):
                    self.assertTrue((p / "03_protocol" / "ethics").is_dir())
                    for rel in ("08_submission", "09_revision"):
                        self.assertEqual((p / rel).is_dir(), publishing, rel)


if __name__ == "__main__":
    unittest.main()
