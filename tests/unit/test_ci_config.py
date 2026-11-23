"""C11: CI installs pinned versions of its direct dependencies."""
import re
import unittest

import _paths  # noqa: F401
from _paths import ROOT

DIRECT = ["matplotlib", "openpyxl", "pandas", "python-pptx", "scipy", "statsmodels"]


class TestCiConfig(unittest.TestCase):
    def test_requirements_are_pinned(self):
        lines = [ln.strip() for ln in (ROOT / "tests" / "requirements-ci.txt").read_text(encoding="utf-8").splitlines()
                 if ln.strip() and not ln.lstrip().startswith("#")]
        self.assertEqual(sorted(ln.split("==")[0].lower() for ln in lines), DIRECT)
        for ln in lines:
            self.assertRegex(ln, r"^[A-Za-z0-9_.-]+==\d+(\.\d+)+$")

    def test_ci_uses_the_requirements_file(self):
        ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("pip install -r tests/requirements-ci.txt", ci)
        self.assertNotRegex(ci, r"pip install (?!-r )")


if __name__ == "__main__":
    unittest.main()
