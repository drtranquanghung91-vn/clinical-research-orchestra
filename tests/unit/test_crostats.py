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
