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
                    if p.is_file() and p.suffix != ".png":
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
        spec.loader.exec_module(mod)
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


if __name__ == "__main__":
    unittest.main()
