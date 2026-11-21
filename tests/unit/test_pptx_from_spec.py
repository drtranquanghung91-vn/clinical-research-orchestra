import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
from _paths import ORCH_SCRIPTS

SCRIPT = ORCH_SCRIPTS / "pptx_from_spec.py"
HAVE = importlib.util.find_spec("pptx") is not None
if HAVE:
    import pptx_from_spec as pfs
    from pptx import Presentation
    from pptx.enum.chart import XL_CHART_TYPE
    from pptx.util import Cm

LEDGER = {"results": [
    {"id": "R-A1-001", "kind": "or", "value": 1.8412, "ci": [1.214, 2.786], "p": 0.0041, "n": 1070,
     "status": "prespecified"}]}

KM = {"id": "F2", "type": "km", "source": "Redrawn from 04_data/x.deid.csv",
      "chart": {"kind": "km", "time_unit": "days", "x_label": "Days", "y_label": "Survival",
                "series": [{"name": "Low", "points": [[0, 1.0], [12, 1.0], [12, 0.98], [30, 0.98], [30, 0.9], [60, 0.9]]},
                           {"name": "High", "points": [[0, 1.0], [10, 1.0], [10, 0.95], [60, 0.7]]}],
                "at_risk": {"times": [0, 30, 60], "rows": [{"name": "Low", "n": [50, 45, 40]},
                                                           {"name": "High", "n": [48, 31, 22]}]}}}
FOREST = {"id": "F1", "type": "forest", "source": "Ledger",
          "chart": {"kind": "forest", "log": True, "null": 1, "x_label": "Odds ratio",
                    "rows": [{"label": "Age 65+", "est": 1.10, "lo": 0.74, "hi": 1.62},
                             {"label": "Female", "est": 1.84, "lo": 1.21, "hi": 2.79},
                             {"label": "Diabetes", "est": 0.55, "lo": 0.30, "hi": 1.01}]}}
BAR = {"id": "F3", "type": "rates", "chart": {"kind": "bar", "categories": ["Ward A", "Ward B"],
                                               "series": [{"name": "Rate", "values": [21.1, 14.0]}],
                                               "labels": ["21,1% (16,1–27,1)", "14,0% (9,0–19,0)"]}}
FLOW = {"id": "F4", "type": "flow", "chart": {"kind": "diagram", "nodes": [
    {"id": "n1", "text": "Screened\nn = 1070", "x": 0.3, "y": 0.0, "w": 0.4, "h": 0.2},
    {"id": "n2", "text": "Analysed\nn = 900", "x": 0.3, "y": 0.6, "w": 0.4, "h": 0.2}],
    "edges": [{"from": "n1", "to": "n2"}]}}


def write(tmp, name, obj):
    (tmp / name).write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")


def charts(slide):
    return [s.chart for s in slide.shapes if getattr(s, "has_chart", False) and s.has_chart]


def tables(slide):
    return [s.table for s in slide.shapes if getattr(s, "has_table", False) and s.has_table]


def texts(slide):
    return [s.text_frame.text for s in slide.shapes if s.has_text_frame]


@unittest.skipUnless(HAVE, "python-pptx not installed")
class TestBuild(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.tmp = Path(self._t.name)
        (self.tmp / "figs").mkdir()
        write(self.tmp / "figs", "F1.data.json", FOREST)
        write(self.tmp / "figs", "F2.data.json", KM)
        write(self.tmp / "figs", "F3.data.json", BAR)
        write(self.tmp / "figs", "F4.data.json", FLOW)

    def tearDown(self):
        self._t.cleanup()

    def build(self, spec, extra=()):
        write(self.tmp, "deck.json", spec)
        out = self.tmp / "o.pptx"
        rc = pfs.main([str(self.tmp / "deck.json"), str(out), *extra])
        return rc, out

    def test_every_slide_type(self):
        from PIL import Image
        Image.new("RGB", (400, 300), "white").save(self.tmp / "pic.png")
        spec = {"slides": [
            {"type": "title", "title": "Defence", "presenter": "P", "notes": "n"},
            {"type": "bullets", "title": "Outline", "bullets": ["a", {"text": "b", "level": 1}], "notes": "n"},
            {"type": "chart", "chart": "km", "title": "KM", "data": "figs/F2.data.json", "notes": "n"},
            {"type": "chart", "chart": "forest", "title": "Forest", "data": "figs/F1.data.json", "notes": "n"},
            {"type": "chart", "chart": "bar", "title": "Bar", "data": "figs/F3.data.json", "notes": "n"},
            {"type": "diagram", "title": "Flow", "data": "figs/F4.data.json", "notes": "n"},
            {"type": "table", "title": "T", "columns": ["a", "b"], "rows": [["1", "2"]], "notes": "n"},
            {"type": "big_number", "title": "Big", "numbers": [{"value": "1,84", "label": "OR"}], "notes": "n"},
            {"type": "figure", "title": "Pic", "image": "pic.png", "notes": "n"},
            {"type": "references", "title": "Refs", "items": ["One", "Two"], "notes": "n"},
            {"type": "closing", "title": "Thanks", "notes": "n"}]}
        rc, out = self.build(spec)
        self.assertEqual(rc, 0)
        prs = Presentation(str(out))
        self.assertEqual(len(prs.slides), 11)

    def test_km_chart_and_at_risk_table(self):
        rc, out = self.build({"lang": "en", "slides": [
            {"type": "chart", "chart": "km", "title": "KM", "data": "figs/F2.data.json"}]})
        self.assertEqual(rc, 0)
        slide = Presentation(str(out)).slides[0]
        ch = charts(slide)[0]
        self.assertEqual(ch.chart_type, XL_CHART_TYPE.XY_SCATTER_LINES_NO_MARKERS)
        self.assertEqual([s.name for s in ch.plots[0].series], ["Low", "High"])
        self.assertEqual(ch.value_axis.maximum_scale, 1)
        self.assertEqual(ch.value_axis.minimum_scale, 0)
        self.assertEqual(ch.category_axis.maximum_scale, 60)
        ys = list(ch.plots[0].series[0].values)
        self.assertEqual(ys, [1.0, 1.0, 0.98, 0.98, 0.9, 0.9])
        tbl = tables(slide)[0]
        grid = [[c.text for c in r.cells] for r in tbl.rows]
        self.assertEqual(grid[0][0], "Number at risk")
        self.assertEqual(grid[0][1:], ["0", "30", "60"])
        self.assertEqual(grid[1], ["Low", "50", "45", "40"])
        self.assertEqual(grid[2], ["High", "48", "31", "22"])

    def test_km_vi_header_and_percent(self):
        rc, out = self.build({"lang": "vi", "slides": [
            {"type": "chart", "chart": "km", "title": "KM", "data": "figs/F2.data.json", "percent": True}]})
        self.assertEqual(rc, 0)
        slide = Presentation(str(out)).slides[0]
        ch = charts(slide)[0]
        self.assertEqual(ch.value_axis.maximum_scale, 100)
        self.assertEqual(list(ch.plots[0].series[0].values)[2], 98.0)
        self.assertEqual(tables(slide)[0].cell(0, 0).text, "Số người còn nguy cơ")

    def test_km_without_at_risk_has_no_table(self):
        d = json.loads(json.dumps(KM))
        del d["chart"]["at_risk"]
        write(self.tmp / "figs", "F2.data.json", d)
        rc, out = self.build({"slides": [{"type": "chart", "chart": "km", "title": "KM",
                                          "data": "figs/F2.data.json"}]})
        self.assertEqual(rc, 0)
        self.assertEqual(tables(Presentation(str(out)).slides[0]), [])

    def test_forest_log_scale_and_structure(self):
        rc, out = self.build({"lang": "vi", "slides": [{"type": "chart", "chart": "forest", "title": "F",
                                                         "data": "figs/F1.data.json"}]})
        self.assertEqual(rc, 0)
        slide = Presentation(str(out)).slides[0]
        ch = charts(slide)[0]
        xml = ch._chartSpace.xml
        self.assertIn('<c:logBase val="10"/>', xml)
        self.assertIn(ch.chart_type, (XL_CHART_TYPE.XY_SCATTER, XL_CHART_TYPE.XY_SCATTER_LINES_NO_MARKERS))
        names =[s.name for s in ch.plots[0].series]
        self.assertEqual(len(names), 1 + 3 + 1)  # estimates, one CI per row, null line
        est = ch.plots[0].series[0]
        self.assertEqual(list(est.values), [3, 2, 1])  # first row at the top
        self.assertIn("Age 65+", texts(slide))
        self.assertTrue(any("1,10 (0,74–1,62)" in t for t in texts(slide)))

    def test_forest_linear_has_no_log(self):
        d = json.loads(json.dumps(FOREST))
        d["chart"]["log"] = False
        write(self.tmp / "figs", "F1.data.json", d)
        rc, out = self.build({"slides": [{"type": "chart", "chart": "forest", "title": "F",
                                          "data": "figs/F1.data.json"}]})
        self.assertEqual(rc, 0)
        self.assertNotIn("c:logBase", charts(Presentation(str(out)).slides[0])[0]._chartSpace.xml)

    def test_bar_from_data_with_labels(self):
        rc, out = self.build({"slides": [{"type": "chart", "chart": "bar", "title": "B",
                                          "data": "figs/F3.data.json"}]})
        self.assertEqual(rc, 0)
        ch = charts(Presentation(str(out)).slides[0])[0]
        self.assertEqual(list(ch.plots[0].categories), ["Ward A", "Ward B"])
        self.assertEqual(list(ch.plots[0].series[0].values), [21.1, 14.0])
        self.assertIn("21,1% (16,1–27,1)", ch._chartSpace.xml)

    def test_diagram_from_data(self):
        rc, out = self.build({"slides": [{"type": "diagram", "title": "Flow", "data": "figs/F4.data.json"}]})
        self.assertEqual(rc, 0)
        slide = Presentation(str(out)).slides[0]
        names = [s.name for s in slide.shapes]
        self.assertIn("Node n1", names)
        node = next(s for s in slide.shapes if s.name == "Node n2")
        self.assertEqual([p.text for p in node.text_frame.paragraphs], ["Analysed", "n = 900"])

    def test_relative_paths_from_spec_folder(self):
        write(self.tmp, "deck.json", {"slides": [{"type": "chart", "chart": "forest", "title": "F",
                                                   "data": "figs/F1.data.json"}]})
        other = tempfile.mkdtemp()
        r = subprocess.run([sys.executable, str(SCRIPT), str(self.tmp / "deck.json"), str(self.tmp / "o.pptx")],
                           cwd=other, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_size_cm(self):
        rc, out = self.build({"size_cm": [90, 120], "slides": [
            {"type": "bullets", "title": "Poster", "bullets": ["x"]}]})
        self.assertEqual(rc, 0)
        prs = Presentation(str(out))
        self.assertEqual(prs.slide_width, Cm(90))
        self.assertEqual(prs.slide_height, Cm(120))

    def test_default_is_16x9(self):
        rc, out = self.build({"slides": [{"type": "title", "title": "T"}]})
        prs = Presentation(str(out))
        self.assertAlmostEqual(prs.slide_width / prs.slide_height, 16 / 9, places=2)

    def test_poster_scales_fonts(self):
        def body_pt(spec):
            _, out = self.build(spec)
            return next(r.font.size.pt for sh in Presentation(str(out)).slides[0].shapes
                        if sh.name == "Body" for p in sh.text_frame.paragraphs for r in p.runs)
        small = body_pt({"slides": [{"type": "bullets", "title": "T", "bullets": ["x"]}]})
        big = body_pt({"size_cm": [90, 120], "slides": [{"type": "bullets", "title": "T", "bullets": ["x"]}]})
        self.assertGreater(big, 2 * small)

    def test_unknown_type_exit_2(self):
        rc, _ = self.build({"slides": [{"type": "nope"}]})
        self.assertEqual(rc, 2)

    def test_missing_data_file_exit_2(self):
        rc, _ = self.build({"slides": [{"type": "chart", "chart": "km", "title": "K", "data": "figs/none.json"}]})
        self.assertEqual(rc, 2)

    def test_km_without_data_exit_2(self):
        rc, _ = self.build({"slides": [{"type": "chart", "chart": "km", "title": "K"}]})
        self.assertEqual(rc, 2)

    def test_bad_args_exit_2(self):
        r = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 2)

    def test_credit_defaults_to_data_source(self):
        rc, out = self.build({"slides": [{"type": "chart", "chart": "km", "title": "KM",
                                          "data": "figs/F2.data.json"}]})
        self.assertIn("Redrawn from 04_data/x.deid.csv", texts(Presentation(str(out)).slides[0]))


@unittest.skipUnless(HAVE, "python-pptx not installed")
class TestPlaceholders(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.p = Path(self._t.name)
        (self.p / "ledgers").mkdir()
        write(self.p / "ledgers", "results-ledger.json", LEDGER)
        (self.p / "project.yaml").write_text("language:\n  output: vi\n", encoding="utf-8")
        (self.p / "07_present").mkdir()

    def tearDown(self):
        self._t.cleanup()

    def run_cli(self, spec, *extra):
        write(self.p / "07_present", "deck.json", spec)
        return subprocess.run([sys.executable, str(SCRIPT), str(self.p / "07_present" / "deck.json"),
                               str(self.p / "07_present" / "o.pptx"), *extra],
                              capture_output=True, text=True, encoding="utf-8")

    def test_renders_in_project_language(self):
        r = self.run_cli({"slides": [
            {"type": "bullets", "title": "OR {{R-A1-001}}", "bullets": ["CI {{R-A1-001.ci}}"], "notes": "p {{R-A1-001.p}}"},
            {"type": "big_number", "title": "T", "numbers": [{"value": "{{R-A1-001}}", "label": "OR"}]}]},
            "--project", str(self.p))
        self.assertEqual(r.returncode, 0, r.stderr)
        prs = Presentation(str(self.p / "07_present" / "o.pptx"))
        t = "\n".join(texts(prs.slides[0]) + texts(prs.slides[1]))
        self.assertIn("OR 1,84", t)
        self.assertIn("1,21–2,79", t)
        self.assertNotIn("{{", t)
        self.assertIn("0,004", prs.slides[0].notes_slide.notes_text_frame.text)

    def test_spec_lang_overrides_project(self):
        r = self.run_cli({"lang": "en", "slides": [{"type": "bullets", "title": "OR {{R-A1-001}}"}]},
                         "--project", str(self.p))
        self.assertEqual(r.returncode, 0, r.stderr)
        t = "\n".join(texts(Presentation(str(self.p / "07_present" / "o.pptx")).slides[0]))
        self.assertIn("OR 1.84", t)

    def test_unknown_id_exit_2_lists_ids(self):
        r = self.run_cli({"slides": [{"type": "bullets", "title": "OR {{R-A9-999}}"}]}, "--project", str(self.p))
        self.assertEqual(r.returncode, 2)
        self.assertIn("R-A9-999", r.stderr)
        self.assertIn("R-A1-001", r.stderr)  # known ids listed
        self.assertFalse((self.p / "07_present" / "o.pptx").exists())

    def test_missing_part_exit_2(self):
        r = self.run_cli({"slides": [{"type": "bullets", "title": "{{R-A1-001.count}}"}]}, "--project", str(self.p))
        self.assertEqual(r.returncode, 2)

    def test_without_project_left_alone(self):
        r = self.run_cli({"slides": [{"type": "bullets", "title": "OR {{R-A1-001}}"}]})
        self.assertEqual(r.returncode, 0, r.stderr)
        t = "\n".join(texts(Presentation(str(self.p / "07_present" / "o.pptx")).slides[0]))
        self.assertIn("{{R-A1-001}}", t)

    def test_bad_project_exit_2(self):
        r = self.run_cli({"slides": [{"type": "bullets", "title": "x"}]}, "--project", str(self.p / "nope"))
        self.assertEqual(r.returncode, 2)


class TestMissingDependency(unittest.TestCase):
    def test_hint_and_exit_2(self):
        code = ("import sys, runpy; sys.modules['pptx'] = None; sys.argv = [%r, 'a.json', 'b.pptx']; "
                "runpy.run_path(%r, run_name='__main__')" % (str(SCRIPT), str(SCRIPT)))
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 2)
        self.assertIn("python -m pip install python-pptx", r.stderr)


if __name__ == "__main__":
    unittest.main()
