"""Live cross-check with R metafor; skipped when R or metafor is absent (CI never installs R)."""
import contextlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
import meta
from p5_helpers import review_project
from test_meta import EXTRACTION, REGISTER


class TestMetaR(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rs = meta.find_rscript(Path("."))
        if cls.rs is None:
            raise unittest.SkipTest("R not found (optional)")
        try:
            _, mf = meta.r_versions(cls.rs)
        except Exception as e:  # noqa: BLE001
            raise unittest.SkipTest(f"R not usable: {e}")
        if mf is None:
            raise unittest.SkipTest("metafor not installed (optional)")

    def test_r_check_agrees_with_python(self):
        t = Path(tempfile.mkdtemp())
        try:
            p = review_project(t)
            (p / "03_protocol" / "sr-protocol.md").write_text(REGISTER, encoding="utf-8")
            (p / "04_data" / "sr" / "extraction.csv").write_text(EXTRACTION, encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(meta.main([str(p), "run"]), 0)
                self.assertEqual(meta.main([str(p), "r-check"]), 0)
            self.assertNotIn("E-META", out.getvalue())
            self.assertIn("r-check: 0 mismatches", out.getvalue())
        finally:
            shutil.rmtree(t, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
