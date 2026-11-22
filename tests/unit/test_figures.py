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
        for name in ("F1.svg", "F1.data.json"):  # text outputs are LF only, every OS
            self.assertNotIn(b"\r\n", (self.p / "07_present" / "figures" / name).read_bytes(), name)

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

    def test_unmatched_colour_key_warns(self):
        self.write_spec(SPEC)
        r = self.run_cli("--dpi", "100", "--only", "F3")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("F3: style.colors", r.stderr)
        self.assertIn("'<7'", r.stderr)
        self.assertIn("'<7%'", r.stderr)
        r = self.run_cli("--dpi", "100", "--only", "F1,F2")  # km labels match; forest has no group labels
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("style.colors", r.stderr)

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


LONG_SPEC = {"style": {"colors": {"<7": "#1f4e79", "7-9": "#c0504d"}}, "figures": [
    {"id": "F1", "type": "forest", "title": "Nguy cơ tái nhập viện theo nhóm HbA1c, hiệu chỉnh theo tuổi và giới",
     "null": 1, "log_scale": True, "x_label": "OR (KTC 95%), thang logarit", "source": "Bảng 3.3",
     "rows": [{"label": "HbA1c 7-9% so với <7%", "result": "R-A1-003"},
              {"label": "HbA1c >9% so với <7%", "result": "R-A1-004"}]},
    {"id": "F2", "type": "km", "title": "Tái nhập viện trong 1 năm", "data": "04_data/cohort.deid.csv",
     "time": "t_days", "event": "ev", "group": "grp", "order": ["<7", "7-9"], "at_risk": [0, 6, 12],
     "max_time": 12, "time_unit": "ngày"},
    {"id": "F3", "type": "rates", "unit": "%", "title": "Tỷ lệ tái nhập viện",
     "rows": [{"label": "HbA1c <7%", "result": "R-A0-062"}, {"label": "HbA1c 7-9%", "result": "R-A0-063"}]},
    {"id": "F4", "type": "flow", "title": "Sơ đồ chọn mẫu", "source": "Hồ sơ bệnh án",
     "boxes": [{"text": "Hồ sơ đủ tiêu chuẩn chọn vào nghiên cứu", "n": "R-A0-001.n"},
               {"text": "Đưa vào phân tích", "n": "R-A0-002.n"}],
     "exclusions": [{"text": "Loại trừ do thiếu dữ liệu HbA1c", "n": "R-A0-001.n - R-A0-002.n"}]},
]}


@unittest.skipUnless(HAVE_MPL, "matplotlib is not installed")
class TestFigureLayout(unittest.TestCase):
    """Layout is relative to the font size: no clipping, no overlapping text at any (width, font) pair."""

    SIZES = [(16, 9), (30, 24), (60, 36)]

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

    def check(self, fig_spec, width, pt):
        import figures
        import matplotlib.pyplot as plt
        f, _src, _data = figures.render_figure(self.p, fig_spec, width_cm=width, font_pt=pt, lang="vi")
        try:
            f.canvas.draw()
            r = f.canvas.get_renderer()
            W, H = f.bbox.width, f.bbox.height
            items = [(t, t.get_window_extent(r)) for t in figures.text_artists(f)]
            self.assertGreaterEqual(len(items), 3)
            tag = f"{fig_spec['type']} {width}cm {pt}pt"
            for t, bb in items:
                self.assertGreaterEqual(bb.x0, -0.5, f"{tag}: {t.get_text()!r} left of canvas")
                self.assertGreaterEqual(bb.y0, -0.5, f"{tag}: {t.get_text()!r} below canvas")
                self.assertLessEqual(bb.x1, W + 0.5, f"{tag}: {t.get_text()!r} right of canvas")
                self.assertLessEqual(bb.y1, H + 0.5, f"{tag}: {t.get_text()!r} above canvas")
            for i in range(len(items)):
                for j in range(i + 1, len(items)):
                    a, b = items[i][1], items[j][1]
                    ox = min(a.x1, b.x1) - max(a.x0, b.x0)
                    oy = min(a.y1, b.y1) - max(a.y0, b.y0)
                    self.assertFalse(ox > 1 and oy > 1, f"{tag}: {items[i][0].get_text()!r} overlaps "
                                                         f"{items[j][0].get_text()!r}")
            # the figure is at least as wide as asked (it only grows when the text needs it)
            self.assertGreaterEqual(f.get_figwidth() * 2.54, width - 0.01)
        finally:
            plt.close(f)

    def test_each_type_each_size(self):
        for spec in (LONG_SPEC, SPEC):
            for fig in spec["figures"]:
                for w, pt in self.SIZES:
                    with self.subTest(type=fig["type"], w=w, pt=pt, spec=len(spec["figures"][0].get("title", ""))):
                        self.check(fig, w, pt)

    def test_text_scales_with_font_not_width(self):
        import figures
        import matplotlib.pyplot as plt
        f, _s, _d = figures.render_figure(self.p, LONG_SPEC["figures"][0], width_cm=30, font_pt=24, lang="vi")
        try:
            sizes = {round(t.get_fontsize()) for t in figures.text_artists(f)}
            self.assertGreaterEqual(min(sizes), 24 - 1)
        finally:
            plt.close(f)

    def test_poster_profile_files_and_defaults(self):
        spec = json.loads(json.dumps(SPEC))
        spec["figures"][0]["poster_width_cm"] = 40
        (self.p / "07_present" / "figures" / "figures.json").write_text(json.dumps(spec), encoding="utf-8")
        r = subprocess.run([sys.executable, str(SCRIPT), str(self.p), "--profile", "poster", "--dpi", "50"],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = self.p / "07_present" / "figures"
        for n in (1, 2, 3, 4):
            for ext in ("svg", "pdf", "png"):
                self.assertTrue((out / f"F{n}.poster.{ext}").exists(), f"F{n}.poster.{ext}")
        self.assertFalse((out / "F1.svg").exists())
        self.assertFalse((out / "F1.poster.data.json").exists())
        svg1 = (out / "F1.poster.svg").read_text(encoding="utf-8")
        svg3 = (out / "F3.poster.svg").read_text(encoding="utf-8")
        import re
        m1 = re.search(r'width="([\d.]+)pt"', svg1)
        m3 = re.search(r'width="([\d.]+)pt"', svg3)
        self.assertAlmostEqual(float(m1.group(1)) / 72 * 2.54, 40, delta=0.5)
        self.assertAlmostEqual(float(m3.group(1)) / 72 * 2.54, 30, delta=0.5)
        # SVG keeps text (svg.fonttype none); the poster font size appears in the style attribute
        self.assertRegex(svg3, r"font:[^\"]*24px|font-size:\s*24")

    def test_document_profile_default_unchanged_names(self):
        (self.p / "07_present" / "figures" / "figures.json").write_text(json.dumps(SPEC), encoding="utf-8")
        r = subprocess.run([sys.executable, str(SCRIPT), str(self.p), "--profile", "document", "--dpi", "50"],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.p / "07_present" / "figures" / "F1.svg").exists())
        self.assertTrue((self.p / "07_present" / "figures" / "F1.data.json").exists())

    def write_spec(self, spec):
        (self.p / "07_present" / "figures" / "figures.json").write_text(json.dumps(spec), encoding="utf-8")

    def run_cli(self, *extra):
        return subprocess.run([sys.executable, str(SCRIPT), str(self.p), *extra], capture_output=True,
                              text=True, encoding="utf-8")

    def data(self, fid):
        return json.loads((self.p / "07_present" / "figures" / f"{fid}.data.json").read_text(encoding="utf-8"))

    def test_render_profiles_recorded_in_data_json(self):
        self.write_spec(SPEC)
        self.assertEqual(self.run_cli("--dpi", "50").returncode, 0)
        before = self.data("F3")
        doc = before["render"]["document"]
        self.assertEqual(doc["font_pt"], 9)
        self.assertGreaterEqual(doc["width_cm"], 16)
        self.assertNotIn("poster", before["render"])
        r = self.run_cli("--profile", "poster", "--dpi", "50")
        self.assertEqual(r.returncode, 0, r.stderr)
        after = self.data("F3")
        self.assertEqual(after["render"]["poster"]["font_pt"], 24)
        self.assertGreaterEqual(after["render"]["poster"]["width_cm"], 30)
        self.assertEqual(after["render"]["document"], doc)
        for k in ("values", "chart", "source"):
            self.assertEqual(after[k], before[k])
        fig = self.p / "07_present" / "figures"
        self.assertGreaterEqual((fig / "F3.poster.svg").stat().st_mtime, (fig / "F3.data.json").stat().st_mtime)

    def test_km_at_risk_time_out_of_range_exit_2(self):
        for bad in ([0, 6, 18], [-1, 6, 12]):
            spec = json.loads(json.dumps(SPEC))
            spec["figures"][1]["at_risk"] = bad
            self.write_spec(spec)
            r = self.run_cli("--only", "F2", "--dpi", "50")
            self.assertEqual(r.returncode, 2, bad)
            self.assertIn("F2", r.stderr)
            self.assertIn("at_risk", r.stderr)

    def test_slide_profile_refused(self):
        (self.p / "07_present" / "figures" / "figures.json").write_text(json.dumps(SPEC), encoding="utf-8")
        r = subprocess.run([sys.executable, str(SCRIPT), str(self.p), "--profile", "slide"],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 2)




P5_LEDGER = {"results": [
    {"id": "R-A1-011", "kind": "rr", "value": 0.6, "ci": [0.3, 1.2]},
    {"id": "R-A1-012", "kind": "rr", "value": 0.9, "ci": [0.5, 1.6]},
    {"id": "R-A1-001", "kind": "rr", "value": 0.78, "ci": [0.55, 1.1], "count": 2},
    {"id": "R-A1-005", "kind": "rr", "value": 0.78, "ci": [0.3, 2.0]},
] + [{"id": f"R-A0-{i:03d}", "kind": "n", "value": v}
     for i, v in ((1, 6), (2, 0), (3, 2), (4, 4), (5, 2), (6, 2), (7, 0), (8, 2), (9, 1), (10, 1), (11, 1), (51, 1))]}
ROB_CSV = ("study_id,outcome,tool,domain,judgement,support,reviewer\n"
           + "".join(f"S0{s},mortality,RoB 2,{d},{j},q,A; B\n" for s, row in ((1, ("low", "low", "some concerns", "low", "low", "some concerns")),
                                                                            (2, ("high", "low", "low", "low", "low", "high")))
                     for d, j in zip(("D1", "D2", "D3", "D4", "D5", "overall"), row)))
P5_SPEC = {"figures": [
    {"id": "F5", "type": "forest", "log_scale": True, "x_label": "RR (KTC 95%)",
     "rows": [{"label": "S01", "result": "R-A1-011"}, {"label": "S02", "result": "R-A1-012"}],
     "pooled": "R-A1-001", "prediction": "R-A1-005"},
    {"id": "F6", "type": "prisma", "identified": "R-A0-001", "registers": "R-A0-002", "duplicates": "R-A0-003",
     "screened": "R-A0-004", "excluded": "R-A0-005", "sought": "R-A0-006", "not_retrieved": "R-A0-007",
     "assessed": "R-A0-008", "reports_excluded": "R-A0-009", "studies": "R-A0-010", "reports": "R-A0-011",
     "reasons": [{"text": "wrong population", "n": "R-A0-051"}]},
    {"id": "F7", "type": "rob", "outcome": "mortality", "tool": "RoB 2", "source": "04_data/sr/rob.csv"},
]}


@unittest.skipUnless(HAVE_MPL, "matplotlib is not installed")
class TestP5Figures(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.p = Path(self.tmp.name)
        (self.p / "ledgers").mkdir()
        (self.p / "ledgers" / "results-ledger.json").write_text(json.dumps(P5_LEDGER), encoding="utf-8")
        (self.p / "project.yaml").write_text("language:\n  output: vi\n", encoding="utf-8")
        (self.p / "04_data" / "sr").mkdir(parents=True)
        (self.p / "04_data" / "sr" / "rob.csv").write_text(ROB_CSV, encoding="utf-8")
        (self.p / "07_present" / "figures").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def run_spec(self, spec, *extra):
        (self.p / "07_present" / "figures" / "figures.json").write_text(json.dumps(spec), encoding="utf-8")
        return subprocess.run([sys.executable, str(SCRIPT), str(self.p), "--dpi", "80", *extra], capture_output=True,
                              text=True, encoding="utf-8")

    def data(self, fid):
        return json.loads((self.p / "07_present" / "figures" / f"{fid}.data.json").read_text(encoding="utf-8"))

    def test_all_p5_types_render(self):
        r = self.run_spec(P5_SPEC)
        self.assertEqual(r.returncode, 0, r.stderr)
        for fid in ("F5", "F6", "F7"):
            self.assertTrue((self.p / "07_present" / "figures" / f"{fid}.png").read_bytes().startswith(b"\x89PNG"))

    def test_forest_pooled_diamond_and_prediction(self):
        self.assertEqual(self.run_spec(P5_SPEC, "--only", "F5").returncode, 0)
        d = self.data("F5")
        self.assertEqual(d["chart"]["pooled"], {"label": "Ước lượng gộp", "est": 0.78, "lo": 0.55, "hi": 1.1})
        self.assertEqual(d["chart"]["prediction"], [0.3, 2.0])
        last = d["values"][-1]
        self.assertEqual(last["ref"], "R-A1-001")
        self.assertEqual(last["text"], "0,78 (0,55–1,10); KDB 95% 0,30–2,00")
        bad = {"figures": [dict(P5_SPEC["figures"][0], pooled=None)]}
        r = self.run_spec(bad)
        self.assertEqual(r.returncode, 2)
        self.assertIn("'prediction' needs 'pooled'", r.stderr)

    def test_prisma_boxes_from_ledger(self):
        self.assertEqual(self.run_spec(P5_SPEC, "--only", "F6").returncode, 0)
        ch = self.data("F6")["chart"]
        texts = [n["text"] for n in ch["nodes"]]
        self.assertIn("Bản ghi từ cơ sở dữ liệu\nvà sổ đăng ký (n = 0)\nn = 6", texts)
        self.assertIn("Bản ghi được sàng lọc\nn = 4", texts)
        self.assertIn("Báo cáo bị loại\nwrong population (n = 1)\nn = 1", texts)
        self.assertIn("Nghiên cứu được đưa vào\nBáo cáo của các nghiên cứu (n = 1)\nn = 1", texts)
        self.assertEqual([s["label"] for s in ch["stages"]], ["Nhận diện", "Sàng lọc", "Đưa vào"])
        refs = {v["ref"] for v in self.data("F6")["values"]}
        self.assertTrue({"R-A0-001.value", "R-A0-051.value", "R-A0-002.value"} <= refs)
        bad = {"figures": [{k: v for k, v in P5_SPEC["figures"][1].items() if k != "assessed"}]}
        r = self.run_spec(bad)
        self.assertEqual(r.returncode, 2)
        self.assertIn("assessed", r.stderr)

    def test_rob_traffic_light(self):
        self.assertEqual(self.run_spec(P5_SPEC, "--only", "F7").returncode, 0)
        d = self.data("F7")
        self.assertEqual(d["data_file"], "04_data/sr/rob.csv")
        self.assertEqual(len(d["data_sha256"]), 64)
        ch = d["chart"]
        self.assertEqual((ch["kind"], ch["tool"]), ("rob", "RoB 2"))
        self.assertEqual(ch["studies"], ["S01", "S02"])
        self.assertEqual(ch["domains"], ["D1", "D2", "D3", "D4", "D5", "overall"])
        self.assertEqual(ch["cells"][1][0], "high")
        svg = (self.p / "07_present" / "figures" / "F7.svg").read_text(encoding="utf-8")
        for sym in ("+", "−", "×"):
            self.assertIn(sym, svg)                       # symbols for greyscale printing
        (self.p / "04_data" / "sr" / "rob.csv").write_text(ROB_CSV.replace(",high,", ",awful,"), encoding="utf-8")
        r = self.run_spec(P5_SPEC, "--only", "F7")
        self.assertEqual(r.returncode, 2)
        self.assertIn("awful", r.stderr)
        r = self.run_spec({"figures": [dict(P5_SPEC["figures"][2], outcome="pain")]})
        self.assertEqual(r.returncode, 2)
        self.assertIn("no rows for outcome 'pain'", r.stderr)


if __name__ == "__main__":
    unittest.main()
