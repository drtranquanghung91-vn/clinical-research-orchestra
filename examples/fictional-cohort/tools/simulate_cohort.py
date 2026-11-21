"""Simulate the fictional cohort's de-identified extract (no real data; stdlib only, seeded).

Usage: python simulate_cohort.py [--out FILE]
Default output: ../04_data/cohort.deid.csv next to this script. Every row's first column is SIMULATED.

n = 1,070 (03_protocol/sample-size.md). Variables follow 03_protocol/variables.md (index admission only;
dates are replaced by day counts). 1-year readmission is drawn from a logistic model with a moderate
HbA1c effect (OR 1.3 for 7-9 % and 1.6 for > 9 % against < 7 %), adjusted for age, sex, diabetes
duration and comorbidity. These parameters are inventions for the demonstration, not estimates.
"""
import argparse
import csv
import math
import random
from pathlib import Path

SEED = 20261121
N = 1070
HEADER = ["simulated", "pid", "age", "sex", "dm_duration_years", "htn", "ckd", "cvd", "hba1c",
          "hba1c_group", "insulin", "los_days", "readmit_1y", "readmit_dm_1y", "time_to_readmit_days",
          "death_inhosp_1y"]


def _logistic(x):
    return 1.0 / (1.0 + math.exp(-x))


def _group(hba1c):
    if hba1c < 7.0:
        return "<7"
    if hba1c <= 9.0:
        return "7-9"
    return ">9"


def simulate(n=N, seed=SEED):
    rng = random.Random(seed)
    rows = []
    for i in range(n):
        age = min(95, max(30, round(rng.gauss(64, 11))))
        male = rng.random() < 0.48
        duration = min(40.0, max(0.0, rng.gauss(9, 5.5)))
        htn = int(rng.random() < _logistic(-0.6 + 0.04 * (age - 64)))
        ckd = int(rng.random() < _logistic(-1.9 + 0.04 * (age - 64) + 0.05 * (duration - 9)))
        cvd = int(rng.random() < _logistic(-1.5 + 0.05 * (age - 64)))
        hba1c = round(min(14.5, max(5.0, rng.gauss(8.2, 1.7))), 1)
        group = _group(hba1c)
        insulin = int(rng.random() < _logistic(-1.2 + 0.55 * (hba1c - 8)))
        los = min(60, max(1, round(math.exp(rng.gauss(math.log(7), 0.45)))))
        comorb = int(htn or ckd or cvd)
        lp = (-1.75 + {"<7": 0.0, "7-9": math.log(1.3), ">9": math.log(1.6)}[group]
              + 0.02 * (age - 64) + 0.10 * male + 0.02 * (duration - 9) + 0.30 * comorb)
        readmit = int(rng.random() < _logistic(lp))
        readmit_dm = int(readmit and rng.random() < _logistic(-0.4 + 0.35 * (hba1c - 8)))
        days = min(365, max(1, round(rng.expovariate(1 / 120)))) if readmit else 365
        death = int(readmit and rng.random() < 0.07)
        if rng.random() < 0.02:  # about 2 % of diabetes durations not recorded (missing at random)
            duration_txt = ""
        else:
            duration_txt = f"{duration:.1f}"
        rows.append(["SIMULATED", f"P{i + 1:04d}", age, "Nam" if male else "Nữ", duration_txt, htn, ckd, cvd,
                     f"{hba1c:.1f}", group, insulin, los, readmit, readmit_dm, days, death])
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parents[1] / "04_data" / "cohort.deid.csv"))
    a = ap.parse_args(argv)
    rows = simulate()
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(HEADER)
        w.writerows(rows)
    print(f"simulate_cohort: {len(rows)} rows written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
