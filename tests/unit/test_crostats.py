import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401

HAVE = all(importlib.util.find_spec(m) for m in ("pandas", "numpy", "scipy", "statsmodels"))


@unittest.skipUnless(HAVE, "pandas, numpy, scipy and statsmodels are required")
class TestCrostats(unittest.TestCase):
    def setUp(self):
        import crostats
        import numpy as np
        import pandas as pd
        self.cs, self.np, self.pd = crostats, np, pd
        self.tmp = tempfile.TemporaryDirectory()
        self.p = Path(self.tmp.name)
        (self.p / "ledgers").mkdir()
        (self.p / "04_data").mkdir()
        rng = np.random.default_rng(20261121)
        n = 400
        age = rng.normal(60, 10, n)
        hba1c = rng.normal(8, 1.5, n)
        lp = -6 + 0.05 * age + 0.3 * hba1c
        y = (rng.random(n) < 1 / (1 + np.exp(-lp))).astype(int)
        self.df = pd.DataFrame({"age": age, "hba1c": hba1c, "readmit": y,
                                "group": np.where(hba1c >= 8, "high", "low"),
                                "los": rng.exponential(5, n)})
        self.data = self.p / "04_data" / "c.deid.csv"
        self.df.to_csv(self.data, index=False)

    def tearDown(self):
        self.tmp.cleanup()

    def test_load_data_refuses_raw(self):
        with self.assertRaises(ValueError):
            self.cs.load_data(self.p / "04_data" / "c.csv")

    def test_crude_effect_known_values(self):
        r = self.cs.crude_effect(20, 80, 10, 90)
        self.assertAlmostEqual(r["or"][0], 2.25, places=4)
        self.assertAlmostEqual(r["or"][1], 0.9943, places=3)
        self.assertAlmostEqual(r["or"][2], 5.0916, places=3)
        self.assertAlmostEqual(r["rr"][0], 2.0, places=4)
        self.assertAlmostEqual(r["rr"][1], 0.9866, places=3)
        self.assertAlmostEqual(r["rr"][2], 4.0544, places=3)
        self.assertAlmostEqual(r["rd"][1], 0.002, places=3)
        self.assertAlmostEqual(r["rd"][2], 0.198, places=3)
        self.assertFalse(r["corrected"])
        self.assertTrue(self.cs.crude_effect(0, 10, 5, 5)["corrected"])

    def test_roc_auc(self):
        r = self.cs.roc_youden([0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8])
        self.assertAlmostEqual(r["auc"], 0.75)
        self.assertAlmostEqual(r["j"], 0.5)

    def test_describe_rules(self):
        d = self.cs.describe(self.df["age"])
        self.assertTrue(d["normal"])
        self.assertTrue(d["use_mean"])
        self.assertFalse(self.cs.describe(self.df["los"])["use_mean"])

    def test_compare_props_uses_fisher_for_small_expected(self):
        small = self.pd.DataFrame({"y": [1, 0, 0, 0, 1, 1, 1, 1, 0, 1], "g": ["a"] * 5 + ["b"] * 5})
        rec = self.cs.Recorder(self.p, self.data)
        self.assertEqual(self.cs.compare_props(small, "y", "g", rec, "A2")["test"], "Fisher exact")

    def test_logistic_and_recorder_output_is_a_valid_ledger_document(self):
        import results_ledger
        import statsmodels.formula.api as smf
        rec = self.cs.Recorder(self.p, self.data)
        out = self.cs.fit_logistic(self.df, "readmit", ["age", "hba1c"], rec, "A1", table="T3.2")
        ref = smf.logit("readmit ~ age + hba1c", self.df).fit(disp=0)
        self.assertAlmostEqual(out["or"]["hba1c"][0], float(self.np.exp(ref.params["hba1c"])), places=6)
        self.assertGreater(out["epv"], 10)
        self.assertEqual(out["ids"][0], "R-A1-001")
        self.cs.table1(self.df, ["age", "los", "readmit"], "group", rec, "T3.1", "Đặc điểm chung")
        path = rec.save()
        doc = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(results_ledger.validate_doc(doc, self.p, verify_raw=True), [])
        self.assertTrue((self.p / "05_analysis" / "output" / "tables" / "T3.1.csv").is_file())
        self.assertEqual(len(doc["data_sha256"]), 64)

    def test_small_epv_warns(self):
        rec = self.cs.Recorder(self.p, self.data)
        out = self.cs.fit_logistic(self.df.head(40), "readmit", ["age", "hba1c"], rec, "A3", status="posthoc")
        self.assertTrue(any("EPV" in w for w in out["warnings"]))

    def test_interaction_returns_p(self):
        p = self.cs.interaction(self.df, "readmit", "hba1c", "age", [], "logit")
        self.assertTrue(0 <= p <= 1)


@unittest.skipUnless(HAVE, "pandas, numpy, scipy and statsmodels are required")
class TestCrostatsFixRound1(unittest.TestCase):
    """Review fix round 1: separation, exact tests, k groups, Table 1 consistency, difference order."""

    def setUp(self):
        import crostats
        import numpy as np
        import pandas as pd
        import scipy.stats as st
        self.cs, self.np, self.pd, self.st = crostats, np, pd, st
        self.tmp = tempfile.TemporaryDirectory()
        self.p = Path(self.tmp.name)
        (self.p / "04_data").mkdir()
        self.data = self.p / "04_data" / "c.deid.csv"
        self.data.write_text("x\n1\n", encoding="utf-8")
        self.rec = crostats.Recorder(self.p, self.data)

    def tearDown(self):
        self.tmp.cleanup()

    def _lines(self, start):
        return [ln for ln in self.rec.lines if ln.startswith(start)]

    def test_complete_separation_is_logged_not_recorded(self):
        import results_ledger
        x = self.np.arange(1, 13)
        d = self.pd.DataFrame({"x": x, "y": (x > 6).astype(int)})
        out = self.cs.fit_logistic(d, "y", ["x"], self.rec, "A5")
        self.assertTrue(out["failed"])
        self.assertEqual(self.rec.results, [])
        failed = [i for i, ln in enumerate(self.rec.lines) if ln.startswith("MODEL FAILED A5: ")]
        self.assertEqual(len(failed), 1)
        self.assertTrue(self.rec.lines[failed[0]].endswith(
            "; consider Firth or exact logistic as a declared deviation"))
        epv = [i for i, ln in enumerate(self.rec.lines) if ln.startswith("A5 WARNING: EPV 6.0 < 10")]
        self.assertEqual(len(epv), 1)
        self.assertLess(epv[0], failed[0])
        self.assertTrue(any("EPV" in w for w in out["warnings"]))
        doc = json.loads(self.rec.save().read_text(encoding="utf-8"))
        self.assertEqual(results_ledger.validate_doc(doc, self.p, verify_raw=True), [])

    def test_quasi_separation_is_logged_not_recorded(self):
        rng = self.np.random.default_rng(3)
        b = rng.integers(0, 2, 100)
        z = rng.normal(0, 1, 100)
        y = self.np.where(b == 1, 1, (rng.random(100) < 0.4).astype(int))
        out = self.cs.fit_logistic(self.pd.DataFrame({"y": y, "b": b, "z": z}), "y", ["b", "z"], self.rec, "A6")
        self.assertTrue(out["failed"])
        self.assertIn("coefficient for b ", out["reason"])
        self.assertEqual(self.rec.results, [])
        self.assertEqual(len(self._lines("MODEL FAILED A6: ")), 1)

    def test_fisher_when_a_group_is_under_20(self):
        d = self.pd.DataFrame({"y": [1] * 5 + [0] * 10 + [1] * 10 + [0] * 5, "g": ["a"] * 15 + ["b"] * 15})
        r = self.cs.compare_props(d, "y", "g", self.rec, "A2")
        self.assertEqual(r["test"], "Fisher exact")
        self.assertAlmostEqual(r["p"], 0.1431109780507063, places=10)
        self.assertAlmostEqual(r["p"], self.st.fisher_exact([[10, 5], [5, 10]])[1], places=12)

    def test_chi_square_for_large_2x2(self):
        d = self.pd.DataFrame({"y": [1] * 30 + [0] * 70 + [1] * 20 + [0] * 80, "g": ["a"] * 100 + ["b"] * 100})
        r = self.cs.compare_props(d, "y", "g", self.rec, "A2")
        self.assertEqual(r["test"], "Chi-square")
        self.assertAlmostEqual(r["p"], self.st.chi2_contingency([[70, 30], [80, 20]], correction=False)[1], places=12)

    def test_monte_carlo_exact_for_small_rxc(self):
        d = self.pd.DataFrame({"y": [1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0],
                               "g": ["a"] * 5 + ["b"] * 5 + ["c"] * 5})
        r = self.cs.compare_props(d, "y", "g", self.rec, "A2")
        self.assertEqual(r["test"], "Monte Carlo exact (chi-square, 10000 permutations)")
        self.assertLessEqual(abs(r["p"] - 0.298), 0.02)  # exact enumeration 0.3007; asymptotic 0.153
        self.assertTrue(any("10000 permutations" in ln and "seed 20261121" in ln for ln in self.rec.lines))

    def _k_groups(self, seed, make):
        rng = self.np.random.default_rng(seed)
        xs = [make(rng, i) for i in range(3)]
        d = self.pd.DataFrame({"y": self.np.concatenate(xs), "g": self.np.repeat(["a", "b", "c"], 60)})
        return d, xs

    def test_compare_k_one_way_anova(self):
        d, xs = self._k_groups(11, lambda rng, i: rng.normal(10 + i, 2, 60))
        r = self.cs.compare_k(d, "y", "g", self.rec, "A7")
        self.assertEqual(r["test"], "One-way ANOVA")
        self.assertAlmostEqual(r["p"], float(self.st.f_oneway(*xs).pvalue), places=12)
        self.assertEqual(self.rec.results[-1]["kind"], "p")

    def test_compare_k_welch_anova(self):
        from statsmodels.stats.oneway import anova_oneway
        d, xs = self._k_groups(12, lambda rng, i: rng.normal(10 + i, (1, 1, 6)[i], 60))
        r = self.cs.compare_k(d, "y", "g", self.rec, "A7")
        self.assertEqual(r["test"], "Welch ANOVA")
        self.assertAlmostEqual(r["p"], float(anova_oneway(xs, use_var="unequal").pvalue), places=12)

    def test_compare_k_kruskal_wallis(self):
        d, xs = self._k_groups(13, lambda rng, i: rng.exponential(1 + 0.5 * i, 60))
        r = self.cs.compare_k(d, "y", "g", self.rec, "A7")
        self.assertEqual(r["test"], "Kruskal–Wallis")
        self.assertAlmostEqual(r["p"], float(self.st.kruskal(*xs).pvalue), places=12)

    def test_compare_two_difference_order(self):
        rng = self.np.random.default_rng(5)
        y0, y1 = rng.normal(10, 2, 50), rng.normal(12, 2, 50)
        d = self.pd.DataFrame({"y": self.np.r_[y0, y1], "g": [0] * 50 + [1] * 50})
        r = self.cs.compare_two(d, "y", "g", self.rec, "A1")
        self.assertEqual(r["test"], "Welch t-test")
        self.assertAlmostEqual(r["md"], float(y0.mean() - y1.mean()), places=12)
        self.assertAlmostEqual(r["p"], float(self.st.ttest_ind(y0, y1, equal_var=False).pvalue), places=12)
        self.assertIn("0 − 1", self.rec.results[-1]["label"])
        r2 = self.cs.compare_two(d, "y", "g", self.rec, "A1", order=(1, 0))
        self.assertAlmostEqual(r2["md"], -r["md"], places=12)
        self.assertAlmostEqual(r2["ci"][0], -r["ci"][1], places=12)
        self.assertIn("1 − 0", self.rec.results[-1]["label"])
        d9 = d.assign(g=["9"] * 50 + ["10"] * 50)
        r3 = self.cs.compare_two(d9, "y", "g", self.rec, "A1")
        self.assertAlmostEqual(r3["md"], r["md"], places=12)
        self.assertIn("9 − 10", self.rec.results[-1]["label"])

    def test_group_order_logged_for_text_groups_and_order_sets_reference(self):
        rng = self.np.random.default_rng(31)
        lv = ["<7", "7-9", ">9"]
        d = self.pd.DataFrame({"y": rng.normal(10, 2, 150), "g": [lv[i % 3] for i in range(150)]})
        self.cs.compare_k(d, "y", "g", self.rec, "A1")
        self.assertTrue(any(l.startswith("GROUP ORDER g:") and "text sort" in l for l in self.rec.lines),
                        self.rec.lines)
        n0 = len(self.rec.lines)
        r = self.cs.compare_k(d, "y", "g", self.rec, "A1", order=["<7", "7-9", ">9"])
        self.assertFalse(any(l.startswith("GROUP ORDER") for l in self.rec.lines[n0:]))
        self.assertIn("(<7, 7-9, >9)", self.rec.results[-1]["label"])
        with self.assertRaises(ValueError):
            self.cs.compare_k(d, "y", "g", self.rec, "A1", order=["<7", "7-9"])

    def test_table1_order_sets_column_order_and_numeric_groups_do_not_log(self):
        rng = self.np.random.default_rng(32)
        d = self.pd.DataFrame({"x": rng.normal(0, 1, 120), "g": ["b", "a"] * 60})
        t = self.cs.table1(d, ["x"], "g", self.rec, "T3.1", "T", order=["b", "a"])
        self.assertTrue(t.columns[2].startswith("b ("), list(t.columns))
        d2 = d.assign(g=[1, 2] * 60)
        n0 = len(self.rec.lines)
        self.cs.table1(d2, ["x"], "g", self.rec, "T3.2", "T")
        self.assertFalse(any(l.startswith("GROUP ORDER") for l in self.rec.lines[n0:]))

    def test_table1_negative_iqr_uses_to(self):
        rng = self.np.random.default_rng(33)
        x = self.np.r_[rng.exponential(1, 100) - 3, rng.exponential(1, 100) - 3]
        d = self.pd.DataFrame({"x": x, "g": ["a"] * 100 + ["b"] * 100})
        t = self.cs.table1(d, ["x"], "g", self.rec, "T3.1", "T")
        cell = t[t["Characteristic"].str.startswith("x,")].iloc[0, 1]
        self.assertIn(" to ", cell)
        self.assertNotIn("–", cell)
        self.assertEqual(self.cs._range_text(-0.001, 1.2), "0.0–1.2")
        self.assertEqual(self.cs._range_text(0.5, 1.2), "0.5–1.2")

    def test_table1_test_follows_displayed_summary(self):
        from crolib import numfmt
        rng = self.np.random.default_rng(21)
        xa, xb = rng.normal(0, 1, 300), rng.normal(10, 1, 50)
        d = self.pd.DataFrame({"x": self.np.r_[xa, xb], "g": ["a"] * 300 + ["b"] * 50})
        self.assertFalse(self.cs.describe(d["x"])["use_mean"])  # the overall column alone would say median
        t = self.cs.table1(d, ["x"], "g", self.rec, "T3.1", "T")
        row = t[t["Characteristic"].str.startswith("x,")].iloc[0]
        self.assertEqual(row["Characteristic"], "x, mean ± SD")
        self.assertEqual(row["Test"], "Welch t-test")
        self.assertEqual(row["p"], numfmt.fmt_p(float(self.st.ttest_ind(xa, xb, equal_var=False).pvalue)))

    def test_table1_three_groups(self):
        from crolib import numfmt
        d, xs = self._k_groups(11, lambda rng, i: rng.normal(10 + i, 2, 60))
        rng = self.np.random.default_rng(14)
        d["sex"] = rng.choice(["F", "M"], len(d))
        t = self.cs.table1(d, ["y", "sex"], "g", self.rec, "T3.1", "T")
        num = t[t["Characteristic"] == "y, mean ± SD"].iloc[0]
        self.assertEqual(num["Test"], "One-way ANOVA")
        self.assertEqual(num["p"], numfmt.fmt_p(float(self.st.f_oneway(*xs).pvalue)))
        cat = t[t["Characteristic"] == "sex, n (%)"].iloc[0]
        self.assertEqual(cat["Test"], "Chi-square")
        ref = self.st.chi2_contingency(self.pd.crosstab(d["g"], d["sex"]).to_numpy(), correction=False)[1]
        self.assertEqual(cat["p"], numfmt.fmt_p(float(ref)))


@unittest.skipUnless(HAVE, "pandas, numpy, scipy and statsmodels are required")
class TestCrostatsVendored(unittest.TestCase):
    """Projects copy crostats.py alone into 05_analysis/; it must not import sibling modules."""

    def test_single_file_copy_runs_alone(self):
        import shutil
        import subprocess
        import sys
        import numpy as np
        import pandas as pd
        import crostats
        import results_ledger
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            shutil.copy(Path(crostats.__file__), tmp / "crostats.py")
            (tmp / "04_data").mkdir()
            rng = np.random.default_rng(7)
            pd.DataFrame({"y": np.r_[rng.normal(10, 2, 40), rng.normal(12, 2, 40)],
                          "g": [0] * 40 + [1] * 40}).to_csv(tmp / "04_data" / "x.deid.csv", index=False)
            code = (
                "import sys\n"
                f"sys.path.insert(0, {str(tmp)!r})\n"
                "import crostats\n"
                "assert not any(m == 'crolib' or m.startswith('crolib.') for m in sys.modules), 'crolib imported'\n"
                "df = crostats.load_data('04_data/x.deid.csv')\n"
                "rec = crostats.Recorder('.', '04_data/x.deid.csv')\n"
                "rec.add('A1', 'prespecified', 'participants analysed', len(df), 'n')\n"
                "r = crostats.compare_two(df, 'y', 'g', rec, 'A1')\n"
                "rec.save()\n"
                "print(r['test'])\n")
            run = subprocess.run([sys.executable, "-I", "-c", code], cwd=tmp, capture_output=True, text=True,
                                 timeout=300)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(run.stdout.strip(), "Welch t-test")
            doc = json.loads((tmp / "05_analysis" / "output" / "results.json").read_text(encoding="utf-8"))
            self.assertEqual([r["id"] for r in doc["results"]], ["R-A1-001", "R-A1-002"])
            self.assertEqual(doc["results"][0]["value"], 80)
            self.assertEqual(results_ledger.validate_doc(doc, tmp, verify_raw=True), [])

    def test_inlined_formatting_matches_numfmt(self):
        import crostats
        from crolib import numfmt
        self.assertEqual(crostats.KINDS, numfmt.KINDS)
        self.assertEqual(crostats.EN_DASH, numfmt.EN_DASH)
        for x in (0.05, 0.25, 0.35, 1.45, 2.675, -0.04, -0.05, 12.345, 99.95, 1e-7, 123456.789):
            for d in (0, 1, 2, 3):
                self.assertEqual(crostats._fmt(x, d), numfmt.fmt(x, d), (x, d))
        for p in (0.0, 0.0004, 0.000999, 0.001, 0.0015, 0.0495, 0.05, 0.9999, 1.0):
            self.assertEqual(crostats._fmt_p(p), numfmt.fmt_p(p), p)


@unittest.skipUnless(HAVE, "pandas, numpy, scipy and statsmodels are required")
class TestCrostatsFollowUp2(unittest.TestCase):
    """interaction and roc_youden record through the Recorder and report model failure."""

    def setUp(self):
        import crostats
        import numpy as np
        import pandas as pd
        self.cs, self.np, self.pd = crostats, np, pd
        self.tmp = tempfile.TemporaryDirectory()
        self.p = Path(self.tmp.name)
        (self.p / "04_data").mkdir()
        self.data = self.p / "04_data" / "c.deid.csv"
        self.data.write_text("x\n1\n", encoding="utf-8")
        self.rec = crostats.Recorder(self.p, self.data)

    def tearDown(self):
        self.tmp.cleanup()

    def _saved_log(self):
        self.rec.save()
        return (self.p / "05_analysis" / "output" / "log.txt").read_text(encoding="utf-8").splitlines()

    def test_interaction_quasi_separation_in_a_subgroup_fails(self):
        import math
        rng = self.np.random.default_rng(31)
        n = 400
        e = rng.integers(0, 2, n)
        m = rng.integers(0, 2, n)
        y = (rng.random(n) < 0.35).astype(int)
        y[(e == 1) & (m == 1)] = 1  # outcome constant in one exposure x modifier cell
        d = self.pd.DataFrame({"y": y, "e": e, "m": m})
        p = self.cs.interaction(d, "y", "e", "m", [], "logit", rec=self.rec, analysis_id="A4")
        self.assertTrue(math.isnan(p))
        self.assertEqual(self.rec.results, [])
        failed = [ln for ln in self._saved_log() if ln.startswith("MODEL FAILED A4: interaction e×m: ")]
        self.assertEqual(len(failed), 1)
        self.assertIn("coefficient for e:m", failed[0])
        self.assertTrue(failed[0].endswith("; consider Firth or exact logistic as a declared deviation"))
        self.assertTrue(math.isnan(self.cs.interaction(d, "y", "e", "m", [], "logit")))

    def test_interaction_records_one_p(self):
        import scipy.stats as st
        import statsmodels.formula.api as smf
        rng = self.np.random.default_rng(32)
        n = 300
        d = self.pd.DataFrame({"x": rng.normal(0, 1, n), "z": rng.normal(0, 1, n), "c": rng.normal(0, 1, n)})
        d["y"] = (rng.random(n) < 1 / (1 + self.np.exp(-(0.5 * d.x + 0.3 * d.z + 0.4 * d.x * d.z)))).astype(int)
        d.loc[[0, 1], "c"] = self.np.nan
        cc = d.dropna()
        red = smf.logit("y ~ x + z + c", cc).fit(disp=0)
        full = smf.logit("y ~ x + z + c + x:z", cc).fit(disp=0)
        ref = float(st.chi2.sf(2 * (full.llf - red.llf), 1))
        p = self.cs.interaction(d, "y", "x", "z", ["c"], "logit", rec=self.rec, analysis_id="A5", status="posthoc")
        self.assertAlmostEqual(p, ref, places=12)
        self.assertEqual(p, self.cs.interaction(d, "y", "x", "z", ["c"], "logit"))
        self.assertEqual(len(self.rec.results), 1)
        r = self.rec.results[0]
        self.assertEqual((r["id"], r["kind"], r["status"], r["n"], r["label"]),
                         ("R-A5-001", "p", "posthoc", 298, "p-interaction x×z"))
        self.assertAlmostEqual(r["value"], ref, places=12)
        log = self._saved_log()
        self.assertTrue(any(ln.startswith("A5 interaction x×z") and "df=1" in ln for ln in log))

    def test_roc_records_auc(self):
        r = self.cs.roc_youden([0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8], rec=self.rec, analysis_id="A6")
        self.assertAlmostEqual(r["auc"], 0.75)
        self.assertEqual(len(self.rec.results), 1)
        rr = self.rec.results[0]
        self.assertEqual((rr["kind"], rr["value"], rr["n"]), ("auc", 0.75, 4))
        log = self._saved_log()
        self.assertTrue(any("cutoff=0.35" in ln and "sens=1" in ln and "spec=0.5" in ln and "J=0.5" in ln
                            for ln in log))
        self.assertFalse(any("score direction inverted" in ln for ln in log))

    def test_roc_inverted_marker_logs_direction(self):
        r = self.cs.roc_youden([0, 0, 1, 1], [0.9, 0.6, 0.65, 0.2], rec=self.rec, analysis_id="A6")  # 1 - score
        self.assertAlmostEqual(r["auc"], 0.25)
        self.assertEqual(self.rec.results[0]["value"], 0.25)
        log = self._saved_log()
        self.assertEqual(sum("score direction inverted: AUC < 0.5; consider 1 − score" in ln for ln in log), 1)


@unittest.skipUnless(HAVE, "pandas, numpy, scipy and statsmodels are required")
class TestCrostatsLabelPrefix(unittest.TestCase):
    """label= prefixes every recorded label of one call ("<label>: ..."); the default is unchanged."""

    def setUp(self):
        import crostats
        import numpy as np
        import pandas as pd
        self.cs = crostats
        self.tmp = tempfile.TemporaryDirectory()
        self.p = Path(self.tmp.name)
        (self.p / "04_data").mkdir()
        self.data = self.p / "04_data" / "c.deid.csv"
        self.data.write_text("x\n1\n", encoding="utf-8")
        rng = np.random.default_rng(41)
        n = 400
        d = pd.DataFrame({"age": rng.normal(60, 10, n), "hba1c": rng.normal(8, 1.5, n),
                          "sex": rng.choice(["nam", "nữ"], n), "g3": rng.choice(["a", "b", "c"], n),
                          "t": rng.exponential(10, n)})
        d["readmit"] = (rng.random(n) < 1 / (1 + np.exp(-(-6 + 0.05 * d.age + 0.3 * d.hba1c)))).astype(int)
        d["cnt"] = rng.poisson(np.exp(0.1 * (d.hba1c - 8)))
        d["los"] = rng.exponential(5, n)
        d["ev"] = (rng.random(n) < 0.6).astype(int)
        self.df = d

    def tearDown(self):
        self.tmp.cleanup()

    def _pair(self, call):
        plain = self.cs.Recorder(self.p, self.data)
        tagged = self.cs.Recorder(self.p, self.data)
        call(plain, {})
        call(tagged, {"label": "nữ"})
        self.assertGreater(len(plain.results), 0)
        self.assertEqual([r["label"] for r in tagged.results], ["nữ: " + r["label"] for r in plain.results])
        self.assertEqual([r["value"] for r in tagged.results], [r["value"] for r in plain.results])
        return plain, tagged

    def test_subgroup_logistic_labels(self):
        sub = self.df[self.df["sex"] == "nữ"]
        plain, tagged = self._pair(lambda rec, kw: self.cs.fit_logistic(
            sub, "readmit", ["age", "hba1c"], rec, "A8", status="posthoc", **kw))
        self.assertEqual(plain.results[1]["label"], "OR hba1c, readmit ~ age + hba1c")
        self.assertEqual(tagged.results[1]["label"], "nữ: OR hba1c, readmit ~ age + hba1c")
        self.assertTrue(all(r["label"].startswith("nữ: ") for r in tagged.results))

    def test_other_fits_and_comparisons(self):
        df = self.df
        self._pair(lambda rec, kw: self.cs.fit_linear(df, "los", ["age"], rec, "A1", **kw))
        self._pair(lambda rec, kw: self.cs.fit_poisson(df, "cnt", ["hba1c"], rec, "A1", **kw))
        self._pair(lambda rec, kw: self.cs.compare_two(df, "age", "sex", rec, "A1", **kw))
        self._pair(lambda rec, kw: self.cs.compare_two(df, "los", "sex", rec, "A1", **kw))
        self._pair(lambda rec, kw: self.cs.compare_k(df, "age", "g3", rec, "A1", **kw))
        self._pair(lambda rec, kw: self.cs.compare_props(df, "readmit", "sex", rec, "A1", **kw))

    @unittest.skipUnless(importlib.util.find_spec("lifelines"), "lifelines not installed")
    def test_cox_labels(self):
        self._pair(lambda rec, kw: self.cs.fit_cox(self.df, "t", "ev", ["age"], rec, "A1", **kw))
