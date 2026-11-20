# Sample-size formulas and how to explain them

Methods content by Amelia Le (co-author), adapted for clinical-research-orchestra. Source: her
`sample-size-planning-vi` v3 (20 Nov 2026), `reference/formulas.md`. Used by the `sample-size-sap` skill.
Every n is computed by `${CLAUDE_PLUGIN_ROOT}/scripts/samplesize.py`, never by hand; the formulas below
are for explaining the number, not for replacing the script. Run
`python "${CLAUDE_PLUGIN_ROOT}/scripts/samplesize.py" <design> --help` for the options of each design.

Notation: z_α = normal quantile 1−α/2 (two-sided) or 1−α (one-sided); z_β = quantile 1−β (power = 1−β);
k = allocation ratio n₂/n₁. Common values: z_0.975 = 1.960, z_0.95 = 1.645, z_0.80 = 0.842,
z_0.90 = 1.282.

All n below are **analysable n**. Recruited n = n / (1 − dropout); the script divides the unrounded n
and then rounds up, so report its output as it stands. Cluster: multiply by the design effect
DE = 1 + (m − 1)·ICC (`--cluster-size m --icc ρ`).

## Designs, script subcommands and formulas

| Design | Subcommand | Formula for n₁ | Parameters needed from the literature | Explanatory note |
|---|---|---|---|---|
| Two independent means | `two-means` | (1+1/k)·[σ(z_α+z_β)/Δ]² + z_α²/4 | σ (pooled SD), Δ (MCID or expected difference) | +z_α²/4 is Guenther's correction to match the t-test. Cohen d = Δ/σ (0.2 small, 0.5 medium, 0.8 large). |
| Two proportions | `two-props` | [z_α√((1+1/k)·p̄q̄) + z_β√(p₁q₁+p₂q₂/k)]² / (p₁−p₂)² | p₁ (control), p₂ (expected) | `--continuity` (Fleiss) if Fisher or a corrected χ² is planned; adds about 10% to n. |
| One proportion against a standard | `one-prop` | [z_α√(p₀q₀) + z_β√(p₁q₁)]² / (p₁−p₀)² | p₀ (standard or historical), p₁ (expected) | Single-arm design (single-arm phase II). |
| One mean against a standard | `one-mean` | [σ(z_α+z_β)/Δ]² + z_α²/2 | σ, Δ | |
| Before–after / paired | `paired` | [σ_d(z_α+z_β)/Δ]² + z_α²/2 | σ_d = SD of the within-pair differences (`--sd-diff`) | With only the outcome SD σ and correlation r: σ_d = σ√(2(1−r)). No r → assume r = 0.5, so σ_d = σ. n = number of pairs. |
| Correlation | `correlation` | [(z_α+z_β)/C]² + 3, C = ½ln((1+r)/(1−r)) | expected r | Fisher z. |
| Survival (log-rank / Cox) | `survival` | Events E = (z_α+z_β)² / [π₁π₂(ln HR)²]; n_total = E / p̄_event | HR, control event proportion over follow-up | Schoenfeld. Treatment-arm event proportion defaults to 1−(1−p_c)^HR. Power depends on the number of **events**, not on n. |
| Non-inferiority, proportions | `noninf-props` | (z_α+z_β)²·(p_c q_c + p_t q_t/k) / (δ + (p_t−p_c))² | p_c, p_t (usually = p_c), margin δ | α **one-sided** (usually 0.025). The margin must be argued (usually ≤ 50% of the active control's effect against placebo). |
| Non-inferiority, means | `noninf-means` | (1+1/k)·[σ(z_α+z_β)/(δ−\|Δ_true\|)]² | σ, δ, Δ_true | One-sided α. |
| Equivalence, means (TOST) | `equiv-means` | (1+1/k)·[σ(z_α+z_{1−β/2})/(δ−\|Δ_true\|)]² | σ, δ | Two one-sided tests; β is split in half. |
| Sensitivity / specificity | `diag` | n_diseased = z_α²·Se(1−Se)/w²; n_total = n_diseased / prev (for Sp divide by 1−prev) | expected Se or Sp, prevalence, CI half-width w | Buderer 1996. Take the larger of the n for Se and the n for Sp. |
| Prevalence / descriptive proportion | `prevalence` | z_α²·p(1−p)/d² (absolute, `--width d`) or z_α²·(1−p)/(ε²·p) (relative, `--relative-precision ε`) | p, d or ε | The "estimate one proportion" formula familiar from Vietnamese theses. Finite population correction `--finite-pop N`; cluster sampling `--deff` (usually 1.5–2) or `--cluster-size m --icc ρ`, or `--n-clusters k --icc ρ` when the number of clusters is fixed. p = 0.5 gives the largest n when p is unknown. p < 10% → use relative precision ε. |
| Case-control | `two-props` | as for two proportions, with p₁ = exposure proportion among controls, p₂ = OR·p₁/(1−p₁+OR·p₁) | p₁ (exposure among controls), expected OR | `--ratio` = controls per case (1–4; above 4 adds almost no power). |
| **Matched** case-control | `two-props` (approximation) | Needs the within-pair correlation of exposure; analysis is conditional logistic regression | p₁, OR, correlation of exposure between matched case and control | The script only approximates (conservative when the correlation is positive). State the limitation; when precision matters use software with Dupont's method (for example PS, `epiR`). |
| Multivariable regression (associated factors) | `regression-epv` | n = (number of parameters × EPV) / p_outcome | number of candidate parameters (each dummy variable counts), proportion with the less frequent outcome | EPV ≥ 10 (Peduzzi 1996), 20 is safer. Clinical prediction models: use Riley 2020 (`pmsampsize` in R/Stata); EPV is only a rough estimate. |

## Converting effect measures

- OR → p₂ when p₁ is known: p₂ = OR·p₁ / (1 − p₁ + OR·p₁).
- RR → p₂: p₂ = RR·p₁.
- HR → treatment-arm event proportion: p_t = 1 − (1−p_c)^HR.
- Median survival → event proportion at time t (exponential assumption): p = 1 − exp(−ln2 · t / median).
- **ANCOVA** with baseline adjustment (baseline–follow-up correlation r): n_ANCOVA ≈ n_t-test × (1 − r²).
  Run `two-means`, then multiply by this factor and state where r came from. No source for r → keep the
  t-test n (conservative).
- Cohen d → Δ: Δ = d·σ. Only d and no σ: run `two-means --delta <d> --sd 1`.
- SD from SE: SD = SE·√n. SD from the 95% CI of a mean: SD = √n·(upper − lower)/3.92.
- **Pooled SD from the 95% CI of a difference between two means** (common in RCT abstracts):
  SE = (upper − lower)/3.92; SD = SE / √(1/n₁ + 1/n₂). Use the analysed n of each arm; if the abstract
  gives only the randomised n, use it and record the assumption. Small n (< 30 per arm): replace 3.92 by
  2·t₀.₉₇₅,df. SD from IQR ≈ IQR/1.35. SD from range ≈ range/4 (n ≈ 30) or range/6 (large n).
- **Trials with more than two arms** that report only the total n: n per arm ≈ total n / number of arms
  (record the assumption when the allocation ratio is unclear). Checked example (SUSTAIN 5, n = 397,
  3 arms): ETD −1.35 (−1.61 to −1.10) → SE = 0.51/3.92 = 0.130; n ≈ 132 per arm →
  SD ≈ 0.130/√(2/132) ≈ 1.06%. (Arithmetic re-checked: 0.1301 / 0.1231 = 1.057.)
- **Pooled SD from two group SDs**: SD_pooled = √[((n₁−1)SD₁² + (n₂−1)SD₂²)/(n₁+n₂−2)]; with two
  groups of about equal size, √((SD₁² + SD₂²)/2).
- **Absolute → relative units** (the outcome is a % change but the source reports kg, mmHg …):
  SD_% ≈ SD_absolute / baseline × 100 and Δ_% ≈ Δ_absolute / baseline × 100. Take the baseline from
  **the author's population** (for example the mean weight of the target group in Vietnam), not from the
  source study when the two populations differ; with no data, label it **ASSUMPTION / GIẢ ĐỊNH** and run
  a sensitivity analysis on SD. A smaller baseline gives a larger SD_%, hence a larger n (the cautious
  direction). Checked example: weight-loss SDs 3.34 and 4.27 kg → pooled SD 3.83 kg; assumed baseline
  weight 64 kg → SD ≈ 6.0%. (Arithmetic re-checked: √((3.34² + 4.27²)/2) = 3.833; 3.833/64 × 100 = 5.99.)

## AI / machine-learning models

There is no single formula; split the study into three parts and argue each separately.

1. **Test (validation) set of a classification or detection model.** The aim is the *precision of the
   estimate* (accuracy, Se, Sp, F1), not power. Use `prevalence --p <expected performance> --width d`
   (or `diag` when Se/Sp by disease prevalence are needed). **The independent unit is the patient or
   case**, not the image or frame: when several measurements sit inside one case (frames in a video,
   slices in a scan, several lesions in one person), use `--n-clusters <number of test cases> --icc ρ`.
   ICC is rarely reported → label it **ASSUMPTION / GIẢ ĐỊNH**, run sensitivity on ICC **and** on the
   number of cases, and propose estimating ICC in a pilot. When the script reports INFEASIBLE, add cases;
   adding measurements per case does not fix it. Checked example (Nov 2026): accuracy 0.85, d 0.05,
   40 videos, ICC 0.10 → 346 frames; ICC 0.25 → INFEASIBLE (re-run below).
2. **Clinical prediction model** (clinical variables → risk): use the Riley 2020 criteria (`pmsampsize`
   in R/Stata) for model development; external validation needs enough events to estimate the
   calibration slope and AUROC precisely (verify the recommended minimum number of events through PubMed
   before writing a number). EPV is only a rough estimate.
3. **Training set of a deep-learning model**: there is no standard formula. Argue from a learning curve
   (train on 25/50/75/100% of the data and see whether performance plateaus), from similar studies (with
   citations) and from practical limits (cases per year, labelling effort).

Always state how the data are split **by patient, centre or time before training**; the test set stays
locked until the single final evaluation. Reporting standards: TRIPOD+AI (prediction), STARD-AI or CLAIM
(imaging or diagnosis); check the current version on EQUATOR.

## Rules for choosing parameters

- **Δ / p₂ is the target difference under DELTA2: both important and realistic**, not the "hoped-for"
  effect. Source order: MCID → stakeholder opinion → pilot → literature (cautious estimate). The lower CI
  bound and the prediction interval are used only in the sensitivity analysis, especially when the
  pooled estimate is imprecise (wide CI, high I², few studies).
- σ, p₁, ICC and dropout come from the study whose population and setting are closest; prefer the
  control arm of an RCT, then a cohort, then a pilot.
- **Matching the time point**: Δ and SD must be taken at **the same measurement time** as the study's
  primary outcome. Behavioural or lifestyle effects usually fade (checked example: HbA1c −1.11% at
  month 3 but −0.28% at month 12; Cradock 2017, PMID 28178985), so use the value at the matching time,
  not the early peak.
- **Add-on effects**: an intervention added to an already strong background therapy usually has a
  smaller effect than the one reported against usual care in the general literature; prefer data from a
  population already on similar background therapy, and put the smaller value into the sensitivity
  analysis.
- Defaults (the author may override): α = 0.05 two-sided; power = 0.80 (0.90 for a confirmatory trial,
  phase III or a safety outcome); dropout from the literature (10–20% when none is available).
- Multiplicity: with ≥ 2 primary outcomes or ≥ 3 groups, split α (Bonferroni) or state the strategy
  (hierarchical testing) in the SAP.
- Interim analysis (O'Brien–Fleming, one interim): multiply n by about 1.01–1.03; Pocock: about
  1.10–1.15.

## Standard "Sample size justification" paragraph (for the protocol)

Write it in `project.yaml → language.output`. Template:

> The sample size was calculated for the primary outcome {outcome} in a {design}. Based on {source study,
> year}, the proportion/mean in the control group is {p₁/μ₁ ± σ}. We assume the intervention will
> {reduce/increase} it to {p₂/μ₂}, corresponding to {ARR/RR/HR/Δ}, the minimal clinically important
> difference {per the MCID source}. With α = {0.05} (two-sided) and power = {80%}, {n₁} patients per
> group ({n_total} in total) are needed. Allowing for {dropout}% loss to follow-up, the recruitment
> target is {n_recruit} ({n₁_recruit} per group). The target difference was chosen from {MCID /
> expert–patient opinion / pilot / literature} because {reason}. Calculated with {formula/software}.
> Sensitivity analysis shows that if {parameter} varies within {a–b}, the sample size ranges from {x–y}.

Vietnamese version (when `language.output` is `vi`):

> Cỡ mẫu được tính cho outcome chính là {outcome} với thiết kế {design}. Dựa trên {nghiên cứu nguồn, năm}
> tỷ lệ/mean ở nhóm chứng là {p₁/μ₁ ± σ}. Chúng tôi giả định can thiệp làm {giảm/tăng} đến {p₂/μ₂},
> tương ứng {ARR/RR/HR/Δ}, là mức chênh lệch có ý nghĩa lâm sàng tối thiểu {theo MCID nguồn}. Với
> α = {0.05} (hai phía) và power = {80%}, cần {n₁} bệnh nhân mỗi nhóm ({n_total} tổng). Dự phòng
> {dropout}% mất theo dõi, cỡ mẫu tuyển là {n_recruit} ({n₁_recruit} mỗi nhóm). Hiệu quả mục tiêu được
> chọn dựa trên {MCID / ý kiến chuyên gia–người bệnh / pilot / y văn}, vì {lý do}. Tính bằng {công
> thức/phần mềm}. Phân tích độ nhạy cho thấy nếu {tham số} thay đổi trong khoảng {a–b}, cỡ mẫu dao động
> {x–y}.

When any parameter is an assumption, the paragraph must contain the sentence: "The values of
{parameters} are assumptions and must be replaced by cited data before the protocol is locked." /
"Các giá trị {tham số} là giả định, cần thay bằng số liệu có trích dẫn trước khi khoá protocol."

## Worked examples (re-run with `samplesize.py --json`, 20 Nov 2026)

Numbers are quoted exactly as the script returned them.

| Command (all with `--json`) | Script output |
|---|---|
| `two-means --delta 5 --sd 12` | n1_raw 91.38, n1_final 92, n_total_final 184, cohen_d 0.417 |
| `two-means --delta 5 --sd 12 --dropout 0.15` | n1_raw 91.38, n1_final 108, n_total_final 216 |
| `two-means --delta 3 --sd 5.5` | n1_raw 53.72, n1_final 54, n_total_final 108 |
| `two-props --p1 0.30 --p2 0.15` | n1_raw 120.47, n1_final 121, n_total_final 242 (RR 0.5, OR 0.412) |
| `two-props --p1 0.30 --p2 0.45` | n1_raw 162.33, n1_final 163, n_total_final 326 |
| `prevalence --p 0.15 --width 0.05` | n_srs 195.91, n_total_final 196 |
| `prevalence --p 0.5 --width 0.05` | n_srs 384.15, n_total_final 385 |
| `survival --hr 0.70 --p-event-ctrl 0.40 --p-event-trt 0.30` | events_required 247, n1_final 353, n_total_final 706 |
| `prevalence --p 0.12 --width 0.03 --n-clusters 10 --icc 0.01 --dropout 0.1` | n_srs 450.73, cluster_size_m 81.2, design_effect 1.802, n_after_deff 813, n_total_final 903, per_cluster_final 91 |
| `regression-epv --predictors 8 --epv 10 --p-outcome 0.25` | events_required 80, n_total_final 320 |
| `prevalence --p 0.85 --width 0.05 --n-clusters 40 --icc 0.10` (AI video example) | n_srs 195.91, cluster_size_m 8.6, design_effect 1.764, n_total_final 346, per_cluster_final 9 |
| `prevalence --p 0.85 --width 0.05 --n-clusters 40 --icc 0.25` | exit code 1: "INFEASIBLE: with 40 clusters and ICC=0.25, the effective sample size can never exceed k/ICC = 160 < required 196. Increase the number of clusters (need > 49.0), relax the precision, or justify a smaller ICC." |

**Why "never round first"**: with dropout 0.15 the script computes 91.38 / 0.85 = 107.5 → 108 per group.
Rounding first (92 / 0.85 = 108.2 → 109) gives a different number from the one the script reports.

**Sensitivity on ICC for the AI example**
(`sensitivity --design prevalence --p 0.85 --width 0.05 --n-clusters 40 --icc 0.10 --vary icc --values 0.05,0.10,0.15,0.20,0.25`):

| ICC | n_total | design_effect |
|---|---|---|
| 0.05 | 247 | 1.258 |
| 0.10 | 346 | 1.764 |
| 0.15 | 628 | 3.204 |
| 0.20 | 7673 | 39.162 |
| 0.25 | INFEASIBLE | — |

Varying the number of cases instead (`--vary n_clusters --values 30,40,60,80`) gives 509, 346, 262 and
234: more cases, not more frames per case, is what lowers n.
