import json
import subprocess
import sys
import unittest

import _paths  # noqa: F401
from _paths import ORCH_SCRIPTS

SCRIPT = ORCH_SCRIPTS / "samplesize.py"


def run(*args):
    r = subprocess.run([sys.executable, str(SCRIPT), *args, "--json"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


class TestSampleSize(unittest.TestCase):
    def test_two_means(self):
        out = run("two-means", "--delta", "5", "--sd", "12")
        self.assertEqual((out["n1_final"], out["n_total_final"]), (92, 184))

    def test_dropout_inflates_raw_n_before_rounding(self):
        out = run("two-means", "--delta", "5", "--sd", "12", "--dropout", "0.15")
        self.assertEqual(out["n1_final"], 108)

    def test_two_props(self):
        self.assertEqual(run("two-props", "--p1", "0.30", "--p2", "0.45")["n1_final"], 163)

    def test_prevalence(self):
        self.assertEqual(run("prevalence", "--p", "0.15", "--width", "0.05")["n_total_final"], 196)

    def test_v3_checked_values(self):
        # values Amelia Le re-checked in v3 (change notes, 20 Nov 2026)
        out = run("two-means", "--delta", "3", "--sd", "5.5")
        self.assertEqual((out["n1_raw"], out["n1_final"]), (53.72, 54))
        self.assertEqual(run("two-props", "--p1", "0.30", "--p2", "0.15")["n1_final"], 121)
        self.assertEqual(run("prevalence", "--p", "0.5", "--width", "0.05")["n_total_final"], 385)
        surv = run("survival", "--hr", "0.70", "--p-event-ctrl", "0.40", "--p-event-trt", "0.30")
        self.assertEqual(surv["events_required"], 247)

    def test_runs_without_scipy(self):
        code = ("import sys; sys.modules['scipy'] = None; "
                "sys.argv = ['samplesize.py', 'two-means', '--delta', '5', '--sd', '12', '--json']; "
                f"exec(compile(open(r'{SCRIPT}', encoding='utf-8').read(), 'samplesize.py', 'exec'), {{'__name__': '__main__'}})")
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["n1_final"], 92)

    def test_every_documented_example_runs(self):
        doc = SCRIPT.read_text(encoding="utf-8").split('"""')[1]
        for line in doc.splitlines():
            line = line.strip()
            if line.startswith("python samplesize.py "):
                args = line.split()[2:]
                r = subprocess.run([sys.executable, str(SCRIPT), *args, "--json"], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, f"{line}\n{r.stderr}")


if __name__ == "__main__":
    unittest.main()
