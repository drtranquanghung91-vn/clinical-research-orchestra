import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
from _paths import ORCH_SCRIPTS

try:
    import matplotlib  # noqa: F401
    HAVE_MPL = True
except ImportError:  # pragma: no cover
    HAVE_MPL = False

SCRIPT = ORCH_SCRIPTS / "figures.py"
LEDGER = {"results": [
    {"id": "R-A1-003", "kind": "or", "value": 1.0975160894901683, "ci": [0.742276835802005, 1.6227659393254874],
     "p": 0.64, "n": 1043},
    {"id": "R-A1-004", "kind": "or", "value": 1.4216250761778106, "ci": [0.9386356164580091, 2.153144225278797],
     "p": 0.097, "n": 1043},
    {"id": "R-A0-062", "kind": "percent", "value": 19.574468085106382, "ci": [15.008147932635021, 25.119499626512305],
     "n": 235, "count": 46},
    {"id": "R-A0-063", "kind": "percent", "value": 21.011673151750973, "ci": [17.711308452772744, 24.74212108169325],
     "n": 514, "count": 108},
    {"id": "R-A0-001", "kind": "n", "value": 1100, "n": 1100},
    {"id": "R-A0-002", "kind": "n", "value": 1070, "n": 1070},
    {"id": "R-A0-003", "kind": "n", "value": 30, "n": 30},
]}

# group "<7": 15 subjects. events at 2, 3, 3, 5, 8; the rest censored (4, 6, 7, 9, 10, 10, 12 x4).
A = [(2, 1), (3, 1), (3, 1), (4, 0), (5, 1), (6, 0), (7, 0), (8, 1), (9, 0), (10, 0), (10, 0),
     (12, 0), (12, 0), (12, 0), (12, 0)]
# group "7-9": events at 1, 1, 4, 6, 6, 6, 9; censored 5, 7, 8, 10, 12 x4.
B = [(1, 1), (1, 1), (4, 1), (5, 0), (6, 1), (6, 1), (6, 1), (7, 0), (8, 0), (9, 1), (10, 0),
     (12, 0), (12, 0), (12, 0), (12, 0)]


def csv_text():
    lines = ["simulated,pid,t_days,ev,grp"]
    for i, (t, e) in enumerate(A):
        lines.append(f"SIMULATED,P{i:03d},{t},{e},<7")
    for i, (t, e) in enumerate(B):
        lines.append(f"SIMULATED,Q{i:03d},{t},{e},7-9")
    return "\n".join(lines) + "\n"


SPEC = {"style": {"colors": {"<7": "#1f4e79", "7-9": "#c0504d"}}, "figures": [
    {"id": "F1", "type": "forest", "title": "OR", "null": 1, "log_scale": True, "x_label": "OR (KTC 95%)",
     "source": "Bảng 3.3",
     "rows": [{"label": "7-9 vs <7", "result": "R-A1-003"}, {"label": ">9 vs <7", "result": "R-A1-004"}]},
    {"id": "F2", "type": "km", "data": "04_data/cohort.deid.csv", "time": "t_days", "event": "ev", "group": "grp",
     "order": ["<7", "7-9"], "at_risk": [0, 6, 12], "max_time": 12, "time_unit": "ngày"},
    {"id": "F3", "type": "rates", "unit": "%",
     "rows": [{"label": "<7%", "result": "R-A0-062"}, {"label": "7-9%", "result": "R-A0-063"}]},
    {"id": "F4", "type": "flow",
     "boxes": [{"text": "Hồ sơ đủ tiêu chuẩn", "n": "R-A0-001.n"}, {"text": "Đưa vào phân tích", "n": "R-A0-002.n"}],
     "exclusions": [{"text": "Loại trừ", "n": "R-A0-001.n - R-A0-002.n"}]},
]}


@unittest.skipUnless(HAVE_MPL, "matplotlib is not installed")
class TestFigures(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.p = Path(self.tmp.name)
        (self.p / "ledgers").mkdir()
        (self.p / "ledgers" / "results-ledger.json").write_text(json.dumps(LEDGER), encoding="utf-8")
        (self.p / "project.yaml").write_text("language:\n  output: vi\n", encoding="utf-8")
        (self.p / "04_data").mkdir()
        (self.p / "04_data" / "cohort.deid.csv").write_text(csv_text(), encoding="utf-8")
        (self.p / "07_present" / "figures").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def write_spec(self, spec):
        (self.p / "07_present" / "figures" / "figures.json").write_text(json.dumps(spec), encoding="utf-8")

    def run_cli(self, *extra):
        return subprocess.run([sys.executable, str(SCRIPT), str(self.p), *extra], capture_output=True,
                              text=True, encoding="utf-8")

    def data(self, fid):
        return json.loads((self.p / "07_present" / "figures" / f"{fid}.data.json").read_text(encoding="utf-8"))

    def test_all_types_write_files(self):
        self.write_spec(SPEC)
        r = self.run_cli("--dpi", "100")
        self.assertEqual(r.returncode, 0, r.stderr)
        for fid in ("F1", "F2", "F3", "F4"):
            for ext in ("svg", "pdf", "png", "data.json"):
                f = self.p / "07_present" / "figures" / f"{fid}.{ext}"
                self.assertTrue(f.is_file() and f.stat().st_size > 0, f"{fid}.{ext}")
        self.assertIn("F1 forest", r.stdout)
        self.assertIn("07_present/figures/F1.{svg,pdf,png}", r.stdout)
        self.assertTrue((self.p / "07_present" / "figures" / "F1.png").read_bytes().startswith(b"\x89PNG"))
        self.assertIn("<text", (self.p / "07_present" / "figures" / "F1.svg").read_text(encoding="utf-8"))

    def test_forest_values_from_ledger(self):
        self.write_spec(SPEC)
        self.assertEqual(self.run_cli("--only", "F1").returncode, 0)
        d = self.data("F1")
        self.assertEqual(d["type"], "forest")
        v = d["values"][0]
        self.assertEqual((v["ref"], v["est"], v["lo"], v["hi"]),
                         ("R-A1-003", LEDGER["results"][0]["value"], LEDGER["results"][0]["ci"][0],
                          LEDGER["results"][0]["ci"][1]))
        self.assertEqual(v["text"], "1,10 (0,74–1,62)")
        self.assertEqual(d["chart"]["kind"], "forest")
        self.assertTrue(d["chart"]["log"])
        self.assertEqual(d["chart"]["null"], 1)
        self.assertEqual(d["chart"]["rows"][1]["est"], LEDGER["results"][1]["value"])
        self.assertEqual(d["source"], "Bảng 3.3")
        self.assertFalse((self.p / "07_present" / "figures" / "F2.png").exists())

    def test_english_formatting(self):
        (self.p / "project.yaml").write_text("language:\n  output: en\n", encoding="utf-8")
        self.write_spec({"figures": [SPEC["figures"][0]]})
        self.assertEqual(self.run_cli().returncode, 0)
        self.assertEqual(self.data("F1")["values"][0]["text"], "1.10 (0.74–1.62)")

    def test_rates(self):
        self.write_spec(SPEC)
        self.assertEqual(self.run_cli("--only", "F3").returncode, 0)
        d = self.data("F3")
        self.assertEqual(d["chart"]["kind"], "bar")
        self.assertEqual(d["chart"]["categories"], ["<7%", "7-9%"])
        self.assertEqual(d["chart"]["series"][0]["values"], [LEDGER["results"][2]["value"], LEDGER["results"][3]["value"]])
        self.assertEqual(d["chart"]["labels"][0], "19,6% (15,0–25,1)")

    def test_km_matches_hand_computation(self):
        self.write_spec(SPEC)
        self.assertEqual(self.run_cli("--only", "F2").returncode, 0)
        d = self.data("F2")
        ch = d["chart"]
        self.assertEqual(ch["kind"], "km")
        self.assertEqual(ch["time_unit"], "ngày")
        names = [s["name"] for s in ch["series"]]
        self.assertEqual(names, ["<7", "7-9"])

        def surv(points, t):
            s = 1.0
            for x, y in points:
                if x <= t:
                    s = y
            return s
        a, b = ch["series"][0]["points"], ch["series"][1]["points"]
        self.assertEqual(a[0], [0, 1.0])
        # <7: 14/15 at t=2; 12/15 at t=3; 8/11 at t=5; 7/11 at t=8 (carried to t=12)
        self.assertAlmostEqual(surv(a, 2), 14 / 15, places=6)
        self.assertAlmostEqual(surv(a, 3), 0.8, places=6)
        self.assertAlmostEqual(surv(a, 4), 0.8, places=6)
        self.assertAlmostEqual(surv(a, 5), 8 / 11, places=6)
        self.assertAlmostEqual(surv(a, 8), 7 / 11, places=6)
        self.assertAlmostEqual(surv(a, 12), 7 / 11, places=6)
        self.assertEqual(a[-1][0], 12)
        # step: the drop at t=2 is a vertical segment [2, 1.0] -> [2, 14/15]
        self.assertIn([2, 1.0], a)
        # 7-9: 13/15 at t=1; x12/13 at t=4 (0.8); x8/11 at t=6 (96/165); x5/6 at t=9 (6 still at risk)
        self.assertAlmostEqual(surv(b, 1), 13 / 15, places=6)
        self.assertAlmostEqual(surv(b, 4), 0.8, places=6)
        self.assertAlmostEqual(surv(b, 6), 96 / 165, places=6)
        self.assertAlmostEqual(surv(b, 9), 96 / 165 * 5 / 6, places=6)
        self.assertEqual(ch["at_risk"]["times"], [0, 6, 12])
        self.assertEqual(ch["at_risk"]["rows"], [{"name": "<7", "n": [15, 10, 4]}, {"name": "7-9", "n": [15, 11, 4]}])
        sha = hashlib.sha256((self.p / "04_data" / "cohort.deid.csv").read_bytes()).hexdigest()
        self.assertEqual(d["data_sha256"], sha)
        self.assertEqual(d["data_file"], "04_data/cohort.deid.csv")
        self.assertEqual(d["source"], "Vẽ lại từ 04_data/cohort.deid.csv")

    def test_km_default_order_warns(self):
        spec = {"figures": [dict(SPEC["figures"][1])]}
        del spec["figures"][0]["order"]
        self.write_spec(spec)
        r = self.run_cli()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("order", r.stderr)
        self.assertEqual([s["name"] for s in self.data("F2")["chart"]["series"]], ["7-9", "<7"])

    def test_flow(self):
        self.write_spec(SPEC)
        self.assertEqual(self.run_cli("--only", "F4").returncode, 0)
        ch = self.data("F4")["chart"]
        self.assertEqual(ch["kind"], "diagram")
        texts = [n["text"] for n in ch["nodes"]]
        self.assertIn("Hồ sơ đủ tiêu chuẩn\nn = 1100", texts)
        self.assertIn("Loại trừ\nn = 30", texts)
        for n in ch["nodes"]:
            for k in ("id", "x", "y", "w", "h"):
                self.assertIn(k, n)
            self.assertTrue(0 <= n["x"] and n["x"] + n["w"] <= 1.0001 and 0 <= n["y"] and n["y"] + n["h"] <= 1.0001)
        ids = {n["id"] for n in ch["nodes"]}
        for e in ch["edges"]:
            self.assertIn(e["from"], ids)
            self.assertIn(e["to"], ids)

    def test_unknown_id_exit_2(self):
        spec = {"figures": [{"id": "F1", "type": "forest", "rows": [{"label": "x", "result": "R-A9-999"}]}]}
        self.write_spec(spec)
        r = self.run_cli()
        self.assertEqual(r.returncode, 2)
        self.assertIn("F1", r.stderr)
        self.assertIn("R-A9-999", r.stderr)

    def test_unlisted_part_exit_2(self):
        spec = {"figures": [{"id": "F3", "type": "rates", "rows": [{"label": "x", "result": "R-A0-062.ci"}]}]}
        self.write_spec(spec)
        r = self.run_cli()
        self.assertEqual(r.returncode, 2)
        self.assertIn("F3", r.stderr)

    def test_unknown_type_exit_2(self):
        self.write_spec({"figures": [{"id": "F9", "type": "pie", "rows": []}]})
        r = self.run_cli()
        self.assertEqual(r.returncode, 2)
        self.assertIn("F9", r.stderr)

    def test_csv_outside_data_dir_exit_2(self):
        (self.p / "other.deid.csv").write_text(csv_text(), encoding="utf-8")
        for bad in ("other.deid.csv", "04_data/raw.csv", "../x.deid.csv"):
            fig = dict(SPEC["figures"][1], data=bad)
            self.write_spec({"figures": [fig]})
            r = self.run_cli()
            self.assertEqual(r.returncode, 2, bad)
            self.assertIn("F2", r.stderr)

    def test_flow_unknown_formula_exit_2(self):
        spec = {"figures": [{"id": "F4", "type": "flow", "boxes": [{"text": "x", "n": "__import__('os')"}]}]}
        self.write_spec(spec)
        r = self.run_cli()
        self.assertEqual(r.returncode, 2)
        self.assertIn("F4", r.stderr)

    def test_missing_spec_and_usage(self):
        self.assertEqual(self.run_cli().returncode, 2)
        self.assertEqual(subprocess.run([sys.executable, str(SCRIPT), "--help"], capture_output=True).returncode, 0)
        self.write_spec(SPEC)
        self.assertEqual(self.run_cli("--only", "F77").returncode, 2)


if __name__ == "__main__":
    unittest.main()
