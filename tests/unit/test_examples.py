import csv
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
from _paths import ROOT

EXAMPLE = ROOT / "examples" / "fictional-cohort"
SIMULATOR = EXAMPLE / "tools" / "simulate_cohort.py"
DATA = EXAMPLE / "04_data" / "cohort.deid.csv"


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


if __name__ == "__main__":
    unittest.main()
