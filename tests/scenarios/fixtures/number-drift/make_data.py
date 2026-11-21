"""Synthetic cohort for scenario fixtures: 300 rows, seeded, no real data.
Usage: python make_data.py <out.csv>"""
import csv
import random
import sys

random.seed(7)
N = 300
readmit = set(random.sample(range(N), 45))  # 15.0 % readmitted, independent of the covariates
rows = []
for i in range(N):
    age = min(90, max(30, round(random.gauss(62, 11))))
    sex = random.choice(["M", "F"])
    hba1c = round(min(13.0, max(5.0, random.gauss(7.4, 1.2))), 1)
    rows.append([f"P{i + 1:03d}", age, sex, hba1c, 1 if i in readmit else 0])
with open(sys.argv[1], "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "age", "sex", "hba1c", "readmit"])
    w.writerows(rows)
