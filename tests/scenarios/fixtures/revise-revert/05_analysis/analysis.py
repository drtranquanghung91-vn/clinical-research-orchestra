"""Analysis for this project: every analysis in the SAP register (03_protocol/sap.md §16), in ID order.
Reads only 04_data/cohort.deid.csv; writes 05_analysis/output/{results.json, log.txt, tables/}.
Run from the project folder: python 05_analysis/analysis.py
"""
import math
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):  # analysis output is UTF-8 (Windows consoles default to cp1252)
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # the vendored 05_analysis/crostats.py
try:
    import numpy as np
    import pandas as pd
    import statsmodels.formula.api as smf
    from patsy import dmatrix
    from scipy import stats
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    from statsmodels.stats.proportion import proportion_confint
    import crostats
except ImportError as e:
    sys.exit(f"{e}\nInstall: python -m pip install pandas scipy statsmodels openpyxl lifelines patsy")

PROJECT = HERE.parent
DATA = "04_data/cohort.deid.csv"
df = crostats.load_data(PROJECT / DATA)
rec = crostats.Recorder(PROJECT, DATA)

# In-memory derived columns only (04_data/cohort.deid.csv is never modified):
# - comorb_any: "Bệnh đồng mắc chính" (variables.md §3) = ≥1 of htn/ckd/cvd, not its own CSV column.
# - hba1c_grp3: same 3 groups as hba1c_group, relabelled "1. <7%"/"2. 7-9%"/"3. >9%" so crostats's
#   lexicographic level sort (table1, fit_logistic via Treatment reference) shows them in clinical
#   order <7% -> 7-9% -> >9% instead of the ASCII order "7-9" < "<7" < ">9" that the raw strings give.
df["comorb_any"] = ((df["htn"] == 1) | (df["ckd"] == 1) | (df["cvd"] == 1)).astype(int)
GROUP_LABELS = {"<7": "1. <7%", "7-9": "2. 7-9%", ">9": "3. >9%"}
df["hba1c_grp3"] = df["hba1c_group"].map(GROUP_LABELS)
# age_grp: POST-HOC A6 subgroup only (decisions.md), not used by any registered A0-A5 analysis.
df["age_grp"] = np.where(df["age"] < 65, "< 65", ">= 65")
REF = "1. <7%"
EXPOSURE_TERM = f"C(hba1c_grp3, Treatment(reference='{REF}'))"
COVARIATES = ["age", "C(sex)", "dm_duration_years", "comorb_any"]
A1_TERMS = [EXPOSURE_TERM] + COVARIATES
rec.log(f"derived columns (in-memory only): comorb_any = htn|ckd|cvd; hba1c_grp3 relabels hba1c_group "
        f"{sorted(GROUP_LABELS.items())} so table/model group order follows clinical severity, reference "
        f"group '{REF}'")


def records_table(table_id, title, analysis_ids):
    rows = [{"id": r["id"], "label": r["label"], "value": r["value"],
             "ci_low": (r.get("ci") or [None, None])[0], "ci_high": (r.get("ci") or [None, None])[1],
             "p": r.get("p"), "n": r.get("n")}
            for r in rec.results if r.get("table") == table_id]
    rec.add_table(table_id, title, pd.DataFrame(rows), analysis_ids)


def proportion_table(outcome, group, rec, analysis_id, table_id, title, label_prefix):
    """n, tỷ lệ % và KTC 95% Wilson (statsmodels proportion_confint), tổng thể và theo từng nhóm.
    Không có trong crostats; ghi lựa chọn và từng số bằng rec.log / rec.add (kind percent)."""
    rec.log(f"{analysis_id} {label_prefix}: tỷ lệ với KTC 95% Wilson (statsmodels proportion_confint, "
            "method='wilson'), không có sẵn trong crostats")
    rows = []
    for name, part in [("Chung", df)] + [(g, df[df[group] == g]) for g in sorted(df[group].dropna().unique())]:
        n = int(part[outcome].notna().sum())
        k = int(part[outcome].sum())
        pct = 100.0 * k / n
        lo, hi = proportion_confint(k, n, alpha=0.05, method="wilson")
        rec.add(analysis_id, "prespecified", f"{label_prefix} [{name}]", pct, "percent", ci=[100 * lo, 100 * hi],
                n=n, count=k, table=table_id)
        rows.append({"group": name, "n": n, "events": k, "percent": pct, "ci_low": 100 * lo, "ci_high": 100 * hi})
    rec.add_table(table_id, title, pd.DataFrame(rows), [analysis_id])


def quadratic_linearity_check(outcome, var, other_terms, d, rec, analysis_id):
    """Kiểm tra tuyến tính logit cho một biến liên tục (SAP §8): so sánh mô hình có var tuyến tính với
    mô hình thêm var^2 (likelihood-ratio test, df=1). Không dùng Box-Tidwell (var*ln(var)) vì
    dm_duration_years có giá trị 0 (ln(0) không xác định); phép kiểm bậc hai áp dụng được cho cả hai
    biến liên tục nên dùng thống nhất."""
    dd = d.copy()
    dd["_sq"] = dd[var] ** 2
    f_lin = f"{outcome} ~ {var} + " + " + ".join(other_terms)
    f_quad = f"{outcome} ~ {var} + _sq + " + " + ".join(other_terms)
    m_lin = smf.logit(f_lin, dd).fit(disp=0)
    m_quad = smf.logit(f_quad, dd).fit(disp=0)
    lr = max(0.0, 2 * (float(m_quad.llf) - float(m_lin.llf)))
    p = float(stats.chi2.sf(lr, 1))
    rec.log(f"{analysis_id} linearity check ({var}, quadratic-term LR test): LR={lr:.4f}, df=1, p={p:.4f} "
            f"({'không có bằng chứng phi tuyến tính' if p >= 0.05 else 'có bằng chứng phi tuyến tính, cần xem lại dạng hàm'})")
    return p


# ---------------------------------------------------------------------- A0
# A0 — mô tả: Bảng 1 theo 3 nhóm HbA1c (không kèm p, theo khuyến nghị sap.md §7), và tỷ lệ tái nhập
# viện 1 năm chung + theo nhóm (KTC 95% Wilson).
crostats.table1(df, ["age", "sex", "dm_duration_years", "htn", "ckd", "cvd", "comorb_any", "insulin",
                      "los_days"], "hba1c_grp3", rec, "T3.1", "Đặc điểm chung theo nhóm HbA1c lúc nhập viện",
                 analysis_id="A0", show_p=False)
proportion_table("readmit_1y", "hba1c_grp3", rec, "A0", "T3.2",
                  "Tỷ lệ tái nhập viện mọi nguyên nhân trong 1 năm, chung và theo nhóm HbA1c",
                  "tỷ lệ tái nhập viện 1 năm")

# ---------------------------------------------------------------------- A1
# A1 — chính: tái nhập viện 1 năm, nhóm HbA1c 3 mức (tham chiếu <7%).
d1 = df.dropna(subset=["readmit_1y", "hba1c_grp3"])
events_by_group = d1.groupby("hba1c_grp3")["readmit_1y"].sum()
rec.log(f"A1 số sự kiện tái nhập viện mỗi nhóm HbA1c: {events_by_group.to_dict()}; quy tắc đổi sang "
        "kiểm định thay thế (sap.md §8) áp dụng nếu một nhóm có < 5 sự kiện")
if (events_by_group < 5).any():
    rec.log("A1 CẢNH BÁO: ít nhất một nhóm có < 5 sự kiện — xem DEVIATION A1 nếu chuyển kiểm định")
else:
    rec.log("A1 mọi nhóm có >= 5 sự kiện — hồi quy logistic đa biến tiến hành như đăng ký, không cần đổi "
            "kiểm định")

# OR thô từng nhóm so với nhóm tham chiếu (crude_effect không tự ghi kết quả)
ref_mask = d1["hba1c_grp3"] == REF
a_ref, b_ref = int((ref_mask & (d1.readmit_1y == 1)).sum()), int((ref_mask & (d1.readmit_1y == 0)).sum())
for g in sorted(GROUP_LABELS.values()):
    if g == REF:
        continue
    gm = d1["hba1c_grp3"] == g
    a, b = int((gm & (d1.readmit_1y == 1)).sum()), int((gm & (d1.readmit_1y == 0)).sum())
    ce = crostats.crude_effect(a, b, a_ref, b_ref)
    rec.log(f"A1 crude OR {g} vs {REF}: Woolf CI; Haldane correction "
            f"{'applied' if ce['corrected'] else 'not needed'}")
    est, lo, hi = ce["or"]
    rec.add("A1", "prespecified", f"crude OR, HbA1c {g} vs {REF}", est, "or", ci=[lo, hi],
            n=a + b + a_ref + b_ref, table="T3.3")

# OR hiệu chỉnh (mô hình đa biến), covariates như sap.md §8
m1 = crostats.fit_logistic(df, "readmit_1y", A1_TERMS, rec, "A1", table="T3.3")
if m1["failed"]:
    print(f"A1 model failed: {m1['reason']} (reported as failed; a replacement needs a DEVIATION A1 line)")
else:
    rec.add("A1", "prespecified", "EPV, mô hình hiệu chỉnh A1", m1["epv"], "other", n=m1["n"], table="T3.3")
    # VIF (collinearity) trên cùng tập ca đầy đủ của mô hình hiệu chỉnh — sap.md §8 yêu cầu, không có
    # sẵn trong crostats.
    dX = df.dropna(subset=["readmit_1y", "hba1c_grp3", "age", "sex", "dm_duration_years", "comorb_any"])
    X = dmatrix(" + ".join(A1_TERMS), dX, return_type="dataframe")
    rec.log(f"A1 VIF (statsmodels variance_inflation_factor, ngưỡng quy ước VIF > 5 gợi ý đa cộng tuyến; "
            f"không có sẵn trong crostats), n={len(dX)}")
    for j, term in enumerate(X.columns):
        if term == "Intercept":
            continue
        vif = float(variance_inflation_factor(X.values, j))
        rec.log(f"A1 VIF {term} = {vif:.3f}")
        rec.add("A1", "prespecified", f"VIF {term}", vif, "other", n=len(dX), table="T3.3")
    # Kiểm tra tuyến tính logit cho 2 biến liên tục (tuổi, thời gian mắc ĐTĐ) — sap.md §8
    quadratic_linearity_check("readmit_1y", "age",
                               [EXPOSURE_TERM, "C(sex)", "dm_duration_years", "comorb_any"], dX, rec, "A1")
    quadratic_linearity_check("readmit_1y", "dm_duration_years",
                               [EXPOSURE_TERM, "age", "C(sex)", "comorb_any"], dX, rec, "A1")
records_table("T3.3", "Tái nhập viện 1 năm theo nhóm HbA1c: OR thô và OR hiệu chỉnh", ["A1"])

# ---------------------------------------------------------------------- A2
# A2 — phụ: HbA1c liên tục (mỗi 1%) thay cho 3 nhóm, cùng biến hiệu chỉnh.
m2 = crostats.fit_logistic(df, "readmit_1y", ["hba1c"] + COVARIATES, rec, "A2", table="T3.4")
if m2["failed"]:
    print(f"A2 model failed: {m2['reason']} (reported as failed; a replacement needs a DEVIATION A2 line)")
else:
    rec.add("A2", "prespecified", "EPV, mô hình A2", m2["epv"], "other", n=m2["n"], table="T3.4")
records_table("T3.4", "Tái nhập viện 1 năm theo HbA1c liên tục (mỗi 1%), OR hiệu chỉnh", ["A2"])

# ---------------------------------------------------------------------- A3
# A3 — phụ: tái nhập viện liên quan ĐTĐ, nhóm HbA1c 3 mức, cùng biến hiệu chỉnh như A1.
m3 = crostats.fit_logistic(df, "readmit_dm_1y", A1_TERMS, rec, "A3", table="T3.5")
if m3["failed"]:
    print(f"A3 model failed: {m3['reason']} (reported as failed; a replacement needs a DEVIATION A3 line)")
else:
    rec.add("A3", "prespecified", "EPV, mô hình A3", m3["epv"], "other", n=m3["n"], table="T3.5")
records_table("T3.5", "Tái nhập viện liên quan ĐTĐ trong 1 năm theo nhóm HbA1c, OR hiệu chỉnh", ["A3"])

# ---------------------------------------------------------------------- A4
# A4 — phụ: thời gian đến lần tái nhập viện đầu tiên (kiểm duyệt 365 ngày), Cox, HR thô và hiệu chỉnh.
mc_crude = crostats.fit_cox(df, "time_to_readmit_days", "readmit_1y", [EXPOSURE_TERM], rec, "A4", table="T3.6")
if mc_crude["failed"]:
    print(f"A4 crude Cox model failed: {mc_crude['reason']} (reported as failed)")
else:
    rec.add("A4", "prespecified", "concordance, mô hình Cox thô A4", mc_crude["concordance"], "other",
            n=mc_crude["n"], table="T3.6")
    rec.add("A4", "prespecified", "PH test min p, mô hình Cox thô A4", mc_crude["ph_min_p"], "p",
            n=mc_crude["n"], table="T3.6")
mc_adj = crostats.fit_cox(df, "time_to_readmit_days", "readmit_1y", A1_TERMS, rec, "A4", table="T3.6")
if mc_adj["failed"]:
    print(f"A4 adjusted Cox model failed: {mc_adj['reason']} (reported as failed; a replacement needs a "
          "DEVIATION A4 line)")
else:
    rec.add("A4", "prespecified", "EPV, mô hình Cox hiệu chỉnh A4", mc_adj["epv"], "other", n=mc_adj["n"],
            table="T3.6")
    rec.add("A4", "prespecified", "concordance, mô hình Cox hiệu chỉnh A4", mc_adj["concordance"], "other",
            n=mc_adj["n"], table="T3.6")
    rec.add("A4", "prespecified", "PH test min p, mô hình Cox hiệu chỉnh A4", mc_adj["ph_min_p"], "p",
            n=mc_adj["n"], table="T3.6")
records_table("T3.6", "Thời gian đến lần tái nhập viện đầu tiên theo nhóm HbA1c: HR thô và HR hiệu chỉnh",
               ["A4"])

# ---------------------------------------------------------------------- A5
# A5 — phụ, chỉ mô tả: tử vong trong viện trong 1 năm, không phân tích đa biến (sap.md §9).
proportion_table("death_inhosp_1y", "hba1c_grp3", rec, "A5", "T3.7",
                  "Tỷ lệ tử vong trong viện trong 1 năm, chung và theo nhóm HbA1c", "tỷ lệ tử vong trong viện")

# ---------------------------------------------------------------------- A6 (POST-HOC, decisions.md)
# A6 — hậu kiểm, theo yêu cầu tác giả 2026-11-21: hiệu ứng nhóm HbA1c lên tái nhập viện 1 năm theo
# nhóm tuổi (<65 / >=65), cùng biến hiệu chỉnh như A1, kèm kiểm định tương tác. Không có trong sap.md.
for level in sorted(df["age_grp"].dropna().unique()):
    rec.log(f"A6 subgroup age_grp = {level}: the next model is fitted in this age subgroup only "
            "(POST-HOC, decisions.md)")
    ms = crostats.fit_logistic(df[df["age_grp"] == level], "readmit_1y", A1_TERMS, rec, "A6",
                                status="posthoc", table="T3.8", label=f"tuổi {level}")
    if ms["failed"]:
        print(f"A6 model in age_grp = {level} failed: {ms['reason']} (reported as failed)")
p_int_age = crostats.interaction(df, "readmit_1y", EXPOSURE_TERM, "age_grp", COVARIATES, family="logit",
                                  rec=rec, analysis_id="A6", status="posthoc",
                                  label="p-interaction, nhóm HbA1c × nhóm tuổi")
if math.isnan(p_int_age):
    print("A6 interaction model failed: see MODEL FAILED in log.txt; reported as failed, never as a p-value")
records_table("T3.8", "Tái nhập viện 1 năm theo nhóm HbA1c, trong từng nhóm tuổi (hậu kiểm)", ["A6"])

print(rec.save())
