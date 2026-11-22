import contextlib
import io
import json
import math
import shutil
import tempfile
import unittest
from pathlib import Path
from statistics import NormalDist
from unittest import mock

import _paths  # noqa: F401
import gate
import meta
from p5_helpers import review_project

GOLD = Path(__file__).parent / "fixtures" / "meta" / "metafor-goldens.json"
Y3, V3 = [0.1, 0.5, 0.9], [0.04, 0.09, 0.01]
YH, VH = [-0.5, 0.2, 0.9, 0.1, 1.2], [0.02, 0.03, 0.025, 0.04, 0.05]
REGISTER = ("# Review protocol (fictional)\n\n## Full-text exclusion reasons\n- wrong population\n\n"
            "## Analysis register\n\n| ID | Type | Outcome | Timepoint | Measure | Model | HKSJ | Experimental | Comparator | Factor |\n"
            "|---|---|---|---|---|---|---|---|---|---|\n| A0 | counts | PRISMA flow | | | | | | | |\n"
            "| A1 | pool | mortality | 30 days | RR | RE-REML | no | drug | placebo | |\n"
            "| A2 | subgroup | mortality | 30 days | RR | RE-REML | no | drug | placebo | design |\n"
            "| A3 | leave-one-out | mortality | 30 days | RR | RE-REML | no | drug | placebo | |\n"
            "| A4 | pool | pain | 6 weeks | MD | RE-DL | yes | drug | placebo | |\n")
EXTRACTION = ("study_id,outcome,timepoint,group,n,events,mean,sd,es,se,design\n"
              "S01,mortality,30 days,drug,50,5,,,,,rct\nS01,mortality,30 days,placebo,50,9,,,,,rct\n"
              "S02,mortality,30 days,drug,40,4,,,,,rct\nS02,mortality,30 days,placebo,41,8,,,,,rct\n"
              "S03,mortality,30 days,drug,60,10,,,,,nrsi\nS03,mortality,30 days,placebo,58,12,,,,,nrsi\n"
              "S01,pain,6 weeks,drug,50,,3.1,1.2,,,rct\nS01,pain,6 weeks,placebo,50,,3.9,1.4,,,rct\n")


def close(a, b, rel=1e-4):
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= rel * max(abs(a), abs(b)) or abs(a - b) <= 1e-8


def cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = meta.main([str(a) for a in argv])
    return code, out.getvalue(), err.getvalue()


class TestDistributions(unittest.TestCase):
    def test_closed_forms(self):
        self.assertAlmostEqual(meta.t_ppf(0.975, 1), math.tan(math.pi * 0.475), places=6)      # Cauchy
        for q in (0.9, 0.975, 0.995):
            self.assertAlmostEqual(meta.t_ppf(q, 2), (2 * q - 1) / math.sqrt(2 * q * (1 - q)), places=6)
        for x in (0.5, 3.0, 10.0):
            self.assertAlmostEqual(meta.chi2_sf(x, 2), math.exp(-x / 2), places=10)
        for df in (3, 7, 30):
            self.assertAlmostEqual(meta.t_p2(meta.t_ppf(0.975, df), df), 0.05, places=8)
        self.assertAlmostEqual(meta.t_ppf(0.975, 100000), NormalDist().inv_cdf(0.975), places=3)
        self.assertAlmostEqual(meta.betai(2.5, 4.0, 0.3) + meta.betai(4.0, 2.5, 0.7), 1.0, places=12)


class TestEstimators(unittest.TestCase):
    def test_dl_tau2_recomputed_independently(self):
        w = [1 / v for v in V3]
        mu = sum(a * b for a, b in zip(w, Y3)) / sum(w)
        q = sum(wi * (yi - mu) ** 2 for wi, yi in zip(w, Y3))
        c = sum(w) - sum(x * x for x in w) / sum(w)
        expected = max(0.0, (q - 2) / c)
        f = meta.pool(Y3, V3, "RE-DL")
        self.assertAlmostEqual(f["tau2"], expected, places=12)
        self.assertAlmostEqual(f["q"], q, places=12)
        self.assertAlmostEqual(f["i2"], max(0.0, (q - 2) / q) * 100, places=9)   # DL: I² = (Q - df)/Q
        self.assertAlmostEqual(meta.tau2_dl(Y3, V3), expected, places=12)

    def test_reml_fixed_point_solves_the_score_equation(self):
        f = meta.pool(YH, VH, "RE-REML")
        t = f["tau2"]
        self.assertGreater(t, 0)
        w = [1 / (v + t) for v in VH]
        mu = sum(a * b for a, b in zip(w, YH)) / sum(w)
        score = sum(wi * wi * (yi - mu) ** 2 for wi, yi in zip(w, YH)) - sum(w) + sum(x * x for x in w) / sum(w)
        self.assertLess(abs(score), 1e-8)
        self.assertAlmostEqual(f["estimate"], mu, places=10)
        self.assertAlmostEqual(f["se"], math.sqrt(1 / sum(w)), places=10)

    def test_hksj_at_least_as_wide_as_wald_when_scale_factor_ge_1(self):
        wald, hk = meta.pool(YH, VH, "RE-REML"), meta.pool(YH, VH, "RE-REML", hksj=True)
        t = wald["tau2"]
        w = [1 / (v + t) for v in VH]
        qh = sum(wi * (yi - wald["estimate"]) ** 2 for wi, yi in zip(w, YH)) / (len(YH) - 1)
        # REML makes the scale factor hover around 1 (it can sit just below), so the premise is the closed form:
        # HKSJ se = sqrt(qh) * Wald se, and the interval is wider whenever sqrt(qh) * t(0.975, k-1) >= 1.959964.
        self.assertAlmostEqual(hk["se"], math.sqrt(qh) * wald["se"], places=12)
        self.assertGreaterEqual(math.sqrt(qh) * meta.t_ppf(0.975, len(YH) - 1), 1.959964)
        self.assertGreaterEqual(hk["ci"][1] - hk["ci"][0], wald["ci"][1] - wald["ci"][0])
        self.assertAlmostEqual(hk["estimate"], wald["estimate"], places=12)

    def test_identical_studies_mh_iv_agree_and_no_heterogeneity(self):
        s = {"a": 10, "n1": 50, "c": 20, "n2": 50}
        studies = [dict(s, study=f"S{i}") for i in range(3)]
        y, v = meta.study_effect("OR", s)
        self.assertAlmostEqual(y, math.log(10 * 30 / (40 * 20)), places=12)
        self.assertAlmostEqual(v, 1 / 10 + 1 / 40 + 1 / 20 + 1 / 30, places=12)
        iv = meta.pool([y] * 3, [v] * 3, "CE-IV")
        mh = meta.pool_mh(studies, "OR")
        reml = meta.pool([y] * 3, [v] * 3, "RE-REML")
        for f in (iv, mh, reml):
            self.assertAlmostEqual(f["estimate"], y, places=10)
            self.assertAlmostEqual(f["i2"], 0.0, places=10)
            self.assertAlmostEqual(f["q"], 0.0, places=10)
        self.assertAlmostEqual(reml["tau2"], 0.0, places=10)
        self.assertAlmostEqual(meta.pool_mh(studies, "RR")["estimate"], math.log((10 / 50) / (20 / 50)), places=10)

    def test_invariances(self):
        s2 = {"a": 7, "n1": 40, "c": 12, "n2": 44}
        swapped = {"a": 12, "n1": 44, "c": 7, "n2": 40}
        for m in ("OR", "RR", "RD"):
            self.assertAlmostEqual(meta.study_effect(m, s2)[0], -meta.study_effect(m, swapped)[0], places=12)
            self.assertAlmostEqual(meta.study_effect(m, s2)[1], meta.study_effect(m, swapped)[1], places=12)
        c = {"m1": 3.1, "sd1": 1.2, "n1": 50, "m2": 3.9, "sd2": 1.4, "n2": 52}
        cs = {"m1": 3.9, "sd1": 1.4, "n1": 52, "m2": 3.1, "sd2": 1.2, "n2": 50}
        for m in ("MD", "SMD"):
            self.assertAlmostEqual(meta.study_effect(m, c)[0], -meta.study_effect(m, cs)[0], places=12)
        a = meta.pool(YH, VH, "RE-REML")
        b = meta.pool(YH[::-1], VH[::-1], "RE-REML")
        for k in ("estimate", "tau2", "i2", "q"):
            self.assertAlmostEqual(a[k], b[k], places=9)

    def test_zero_cells_and_double_zero(self):
        self.assertIsNone(meta.study_effect("OR", {"a": 0, "n1": 20, "c": 0, "n2": 20}))
        self.assertIsNone(meta.study_effect("RR", {"a": 20, "n1": 20, "c": 15, "n2": 15}))
        y, v = meta.study_effect("OR", {"a": 0, "n1": 20, "c": 3, "n2": 20})
        a, b, c, d = 0.5, 20.5, 3.5, 17.5
        self.assertAlmostEqual(y, math.log(a * d / (b * c)), places=12)
        self.assertAlmostEqual(v, 1 / a + 1 / b + 1 / c + 1 / d, places=12)

    def test_smd_exact_correction(self):
        c = {"m1": 3.1, "sd1": 1.2, "n1": 11, "m2": 3.9, "sd2": 1.4, "n2": 11}
        m = 20
        sp = math.sqrt((10 * 1.2 ** 2 + 10 * 1.4 ** 2) / m)
        g, v = meta.study_effect("SMD", c)
        j = g / ((3.1 - 3.9) / sp)
        self.assertAlmostEqual(j, 1 - 3 / (4 * m - 1), places=3)          # the usual approximation
        self.assertAlmostEqual(v, 1 / 11 + 1 / 11 + g * g / (2 * 22), places=12)

    def test_prediction_interval_rules(self):
        self.assertIsNone(meta.pool(Y3[:2], V3[:2], "RE-REML")["pi"])
        self.assertIsNone(meta.pool(Y3, V3, "CE-IV")["pi"])
        f = meta.pool(YH, VH, "RE-REML")
        h = meta.t_ppf(0.975, 3) * math.sqrt(f["tau2"] + f["se"] ** 2)
        self.assertAlmostEqual(f["pi"][0], f["estimate"] - h, places=12)
        self.assertLess(f["pi"][0], f["ci"][0])
        with self.assertRaises(ValueError):
            meta.pool([0.1], [0.04], "RE-REML")

    def test_egger_equals_classic_regression_of_y_over_se_on_precision(self):
        y = [0.10, 0.35, -0.20, 0.55, 0.05, 0.40, 0.25, -0.05, 0.60, 0.15]
        v = [0.010, 0.040, 0.020, 0.090, 0.015, 0.060, 0.030, 0.012, 0.080, 0.025]
        z = [yi / math.sqrt(vi) for yi, vi in zip(y, v)]
        x = [1 / math.sqrt(vi) for vi in v]
        mx, mz = sum(x) / len(x), sum(z) / len(z)
        slope = sum((a - mx) * (b - mz) for a, b in zip(x, z)) / sum((a - mx) ** 2 for a in x)
        self.assertAlmostEqual(meta.egger(y, v)["intercept"], mz - slope * mx, places=10)

    def test_subgroup_test_matches_definition(self):
        fits = [{"estimate": 0.2, "se": 0.1}, {"estimate": 0.6, "se": 0.2}]
        w = [100.0, 25.0]
        mu = (100 * 0.2 + 25 * 0.6) / 125
        qb = 100 * (0.2 - mu) ** 2 + 25 * (0.6 - mu) ** 2
        t = meta.subgroup_test(fits)
        self.assertAlmostEqual(t["q"], qb, places=12)
        self.assertEqual(t["df"], 1)
        self.assertAlmostEqual(t["p"], meta.chi2_sf(qb, 1), places=12)
        self.assertTrue(all(isinstance(x, float) for x in w))


@unittest.skipUnless(GOLD.is_file(), "metafor goldens not generated yet (Task 5 step 4)")
class TestMetaforGoldens(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = json.loads(GOLD.read_text(encoding="utf-8"))
        cls.engine, cls.cases = data["engine"], data["cases"]

    def fit(self, c, studies=None, model=None):
        studies = c["studies"] if studies is None else studies
        model = model or c["model"]
        if model == "CE-MH":
            return meta.pool_mh(studies, c["measure"])
        eff = [e for e in (meta.study_effect(c["measure"], s) for s in studies) if e is not None]
        return meta.pool([e[0] for e in eff], [e[1] for e in eff], model, c["hksj"])

    def same(self, got, want, keys=("estimate", "se", "p", "tau2", "i2", "q", "q_p")):
        for k in keys:
            if k in want:
                self.assertTrue(close(got[k], want[k]), f"{k}: python {got[k]!r}, metafor {want[k]!r}")
        for k in ("ci", "pi"):
            if k in want:
                if want[k] is None:
                    self.assertIsNone(got[k], k)
                else:
                    for a, b in zip(got[k], want[k]):
                        self.assertTrue(close(a, b), f"{k}: python {got[k]!r}, metafor {want[k]!r}")

    def test_engine_recorded_without_paths(self):
        self.assertIn("metafor", self.engine)
        self.assertNotRegex(self.engine, r"[\\/]")

    def test_pooled_cases(self):
        n = 0
        for name, c in self.cases.items():
            if any(k in c for k in ("egger", "levels", "loo")):
                continue
            with self.subTest(case=name):
                self.same(self.fit(c), c)
                n += 1
        self.assertGreaterEqual(n, 9)

    def test_egger(self):
        c = self.cases["bcg_rr_egger"]
        eff = [meta.study_effect("RR", s) for s in c["studies"]]
        got = meta.egger([e[0] for e in eff], [e[1] for e in eff])
        for k in ("intercept", "se", "t", "p"):
            self.assertTrue(close(got[k], c["egger"][k]), k)

    def test_subgroups(self):
        c = self.cases["bcg_rr_subgroup_alloc"]
        fits = []
        for lev, want in c["levels"].items():
            sub = [s for s in c["studies"] if c["factor"][s["study"]] == lev]
            got = self.fit(c, sub)
            with self.subTest(level=lev):
                self.same(got, want)
            fits.append(got)
        t = meta.subgroup_test(fits)
        self.assertTrue(close(t["q"], c["qb"]))
        self.assertEqual(t["df"], c["qb_df"])
        self.assertTrue(close(t["p"], c["qb_p"]))

    def test_leave_one_out(self):
        c = self.cases["bcg_rr_loo"]
        for row in c["loo"]:
            rest = [s for s in c["studies"] if s["study"] != row["omit"]]
            got = self.fit(c, rest)
            with self.subTest(omit=row["omit"]):
                self.same(got, {"estimate": row["estimate"], "ci": row["ci"]}, keys=("estimate",))


class TestMetaCli(unittest.TestCase):
    def setUp(self):
        self.t = Path(tempfile.mkdtemp())
        self.p = review_project(self.t)
        (self.p / "03_protocol" / "sr-protocol.md").write_text(REGISTER, encoding="utf-8")
        (self.p / "04_data" / "sr" / "extraction.csv").write_text(EXTRACTION, encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.t, ignore_errors=True)

    def ledger(self):
        recs = json.loads((self.p / "ledgers" / "results-ledger.json").read_text(encoding="utf-8"))["results"]
        return {r["id"]: r for r in recs}

    def test_run_writes_ledger_records_and_files(self):
        code, out, err = cli(self.p, "run")
        self.assertEqual(code, 0, out + err)
        led = self.ledger()
        for rid in ("R-A1-001", "R-A1-002", "R-A1-003", "R-A1-004", "R-A1-005", "R-A1-011", "R-A1-012", "R-A1-013",
                    "R-A2-001", "R-A2-021", "R-A3-001", "R-A3-002", "R-A3-003"):
            self.assertIn(rid, led)
        self.assertNotIn("R-A1-006", led)                        # Egger only when k >= 10
        self.assertNotIn("R-A2-011", led)                        # level "nrsi" has one study: not pooled
        self.assertNotIn("R-A4-001", led)                        # one study: narrative line, no pooled id
        self.assertIn("R-A4-011", led)
        self.assertIn("A4 pain: 1 study; not pooled", (self.p / meta.LOG_REL).read_text(encoding="utf-8"))
        studies = [{"a": 5, "n1": 50, "c": 9, "n2": 50}, {"a": 4, "n1": 40, "c": 8, "n2": 41},
                   {"a": 10, "n1": 60, "c": 12, "n2": 58}]
        eff = [meta.study_effect("RR", s) for s in studies]
        f = meta.pool([e[0] for e in eff], [e[1] for e in eff], "RE-REML")
        self.assertAlmostEqual(led["R-A1-001"]["value"], math.exp(f["estimate"]), places=9)
        self.assertEqual((led["R-A1-001"]["kind"], led["R-A1-001"]["status"], led["R-A1-001"]["count"]), ("rr", "prespecified", 3))
        self.assertEqual(led["R-A1-002"]["kind"], "tau2")
        self.assertEqual(led["R-A1-003"]["kind"], "percent")
        self.assertAlmostEqual(led["R-A1-005"]["ci"][0], math.exp(f["pi"][0]), places=9)
        self.assertEqual(led["R-A1-011"]["label"], "S01 RR")
        self.assertEqual(led["R-A3-001"]["label"], "pooled RR without S01")
        py = json.loads((self.p / meta.PY_REL).read_text(encoding="utf-8"))
        self.assertIn("A1", py)
        self.assertIn("A2|rct", py)
        self.assertIn("A3|-S01", py)
        self.assertNotIn(b"\r\n", (self.p / meta.LOG_REL).read_bytes())

    def test_deviation_status_and_g3_lock(self):
        (self.p / "decisions.md").write_text("# Decisions\n\n- DEVIATION A1: model changed to REML before data, 2026-11-20\n",
                                             encoding="utf-8")
        self.assertEqual(cli(self.p, "run")[0], 0)
        self.assertEqual(self.ledger()["R-A1-001"]["status"], "deviation")
        gate.open_gate(self.p, "G3", by="A", files=["ledgers/results-ledger.json"])
        (self.p / "04_data" / "sr" / "extraction.csv").write_text(EXTRACTION.replace("drug,50,5", "drug,50,6"), encoding="utf-8")
        code, out, err = cli(self.p, "run")
        self.assertEqual(code, 1)
        self.assertIn("G3 is locked", err)

    def test_scoping_review_is_refused(self):
        shutil.rmtree(self.t / "p")
        self.p = review_project(self.t, design="scoping-review")
        code, out, err = cli(self.p, "run")
        self.assertEqual(code, 1)
        self.assertIn("do not pool", out)

    def test_forest_spec_and_r_script(self):
        self.assertEqual(cli(self.p, "run")[0], 0)
        self.assertEqual(cli(self.p, "forest-spec")[0], 0)
        spec = json.loads((self.p / "07_present" / "figures" / "figures.json").read_text(encoding="utf-8"))
        fig = next(f for f in spec["figures"] if f["id"] == "F-A1")
        self.assertEqual((fig["type"], fig["pooled"], fig["prediction"], fig["log_scale"], fig["null"]),
                         ("forest", "R-A1-001", "R-A1-005", True, 1))
        self.assertEqual([r["result"] for r in fig["rows"]], ["R-A1-011", "R-A1-012", "R-A1-013"])
        self.assertEqual(cli(self.p, "forest-spec")[0], 0)            # idempotent: one entry per id
        spec = json.loads((self.p / "07_present" / "figures" / "figures.json").read_text(encoding="utf-8"))
        self.assertEqual(sum(f["id"] == "F-A1" for f in spec["figures"]), 1)
        self.assertEqual(cli(self.p, "r-script")[0], 0)
        script = (self.p / meta.R_SCRIPT).read_text(encoding="utf-8")
        self.assertIn("library(metafor)", script)
        self.assertIn('"05_analysis/meta/meta-input.csv"', script)
        self.assertNotIn(str(self.p), script)
        self.assertNotIn(str(self.t), script)
        plan = (self.p / meta.PLAN_REL).read_text(encoding="utf-8").splitlines()
        self.assertEqual(plan[0], "key,measure,model,hksj")
        self.assertIn("A1,RR,RE-REML,no", plan)

    def test_usage_errors(self):
        (self.p / "04_data" / "sr" / "extraction.csv").unlink()
        self.assertEqual(cli(self.p, "run")[0], 2)
        (self.p / "03_protocol" / "sr-protocol.md").write_text(REGISTER.replace("| RR | RE-REML | no | drug | placebo | |\n| A2",
                                                                                "| XX | RE-REML | no | drug | placebo | |\n| A2"),
                                                                encoding="utf-8")
        self.assertEqual(cli(self.p, "run")[0], 2)
        self.assertEqual(cli(self.t / "none", "run")[0], 2)


class TestRDiscovery(unittest.TestCase):
    def setUp(self):
        self.t = Path(tempfile.mkdtemp())
        self.p = review_project(self.t)

    def tearDown(self):
        shutil.rmtree(self.t, ignore_errors=True)

    def fake(self, *parts) -> Path:
        f = self.t.joinpath(*parts)
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("", encoding="utf-8")
        return f

    def test_windows_newest_version_first(self):
        for v in ("R-4.5.0", "R-4.10.1", "R-4.6.1"):
            self.fake("lad", "Programs", "R", v, "bin", "Rscript.exe")
        got = meta.find_rscript(self.p, env={"LOCALAPPDATA": str(self.t / "lad")}, system="Windows", which=lambda n: None)
        self.assertEqual(got.parent.parent.name, "R-4.10.1")
        pf = self.fake("pf", "R", "R-4.4.0", "bin", "Rscript.exe")
        got = meta.find_rscript(self.p, env={"ProgramFiles": str(self.t / "pf")}, system="Windows", which=lambda n: None)
        self.assertEqual(got, pf)

    def test_order_config_path_r_home(self):
        cfg = self.fake("cfg", "Rscript")
        rhome = self.fake("rhome", "bin", "Rscript")
        with open(self.p / "project.yaml", "a", encoding="utf-8") as fh:
            fh.write(f'tools:\n  rscript: "{cfg.as_posix()}"\n')
        on_path = self.fake("path", "Rscript")
        got = meta.find_rscript(self.p, env={"R_HOME": str(self.t / "rhome")}, system="Linux", which=lambda n: str(on_path))
        self.assertEqual(got, cfg)
        cands = meta.rscript_candidates(self.p, env={"R_HOME": str(self.t / "rhome")}, system="Linux",
                                        which=lambda n: str(on_path))
        self.assertEqual(cands[:3], [cfg, on_path, rhome])

    def test_macos_and_linux_standard_locations(self):
        got = meta.find_rscript(self.p, env={}, system="Darwin", which=lambda n: None,
                                is_file=lambda p: p.as_posix() == "/opt/homebrew/bin/Rscript")
        self.assertEqual(got.as_posix(), "/opt/homebrew/bin/Rscript")
        cands = [c.as_posix() for c in meta.rscript_candidates(self.p, env={}, system="Darwin", which=lambda n: None)]
        self.assertEqual(cands[0], "/Library/Frameworks/R.framework/Resources/bin/Rscript")
        got = meta.find_rscript(self.p, env={}, system="Linux", which=lambda n: None,
                                is_file=lambda p: p.as_posix() == "/usr/bin/Rscript")
        self.assertEqual(got.as_posix(), "/usr/bin/Rscript")
        self.assertIsNone(meta.find_rscript(self.p, env={}, system="Linux", which=lambda n: None, is_file=lambda p: False))

    def test_status_and_check_without_r_exit_2_with_hint(self):
        for system in ("Windows", "Darwin", "Linux"):
            self.assertIn('install.packages("metafor")', meta.install_hint(system))
            self.assertIn("cran.r-project.org", meta.install_hint(system))
        with mock.patch.object(meta, "find_rscript", return_value=None):
            code, out, err = cli(self.p, "r-status")
            self.assertEqual(code, 2)
            self.assertIn("R not found", err)
            self.assertIn("tools.rscript", err)
            self.assertEqual(cli(self.p, "r-check")[0], 2)
        with mock.patch.object(meta, "find_rscript", return_value=Path("Rscript")), \
                mock.patch.object(meta, "r_versions", return_value=("4.6.1", None)):
            code, out, err = cli(self.p, "r-status")
            self.assertEqual(code, 2)
            self.assertIn("metafor not installed", err)
        with mock.patch.object(meta, "find_rscript", return_value=Path("Rscript")), \
                mock.patch.object(meta, "r_versions", return_value=("4.6.1", "5.2.1")):
            code, out, err = cli(self.p, "r-status")
            self.assertEqual(code, 0)
            self.assertIn("metafor 5.2.1", out)

    def test_compare_flags_mismatch_as_warn(self):
        py = {"A1": {"estimate": 0.5, "ci": [0.1, 0.9], "tau2": 0.02, "i2": 40.0, "q": 3.0, "pi": None, "k": 3}}
        rr = {"A1": {"estimate": 0.5000001, "ci": [0.1, 0.9], "tau2": 0.03, "i2": 40.0, "q": 3.0, "pi": None, "k": 3}}
        found = meta.compare(py, rr)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0][0], "warn")
        self.assertIn("A1 tau2", found[0][2])
        self.assertIn("missing", meta.compare(py, {})[0][2])
