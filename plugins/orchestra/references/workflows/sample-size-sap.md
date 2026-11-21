# Sample size and SAP: full workflow

Methods content by Amelia Le (co-author), adapted for clinical-research-orchestra. Source: her
`sample-size-planning-vi` v3 (20 Nov 2026) and its two change notes (18 Nov, 20 Nov). Where the v3 text
and the 18 Nov notes differ, v3 is followed. Thresholds are **defaults** the author may override, not
standards (`${CLAUDE_PLUGIN_ROOT}/references/judgement-defaults.md`); record an override in
`decisions.md`.

Statistics library: `${CLAUDE_PLUGIN_ROOT}/references/statistics/sample-size-formulas.md`,
`${CLAUDE_PLUGIN_ROOT}/references/statistics/test-selection.md`,
`${CLAUDE_PLUGIN_ROOT}/references/statistics/sap-template.md`,
`${CLAUDE_PLUGIN_ROOT}/references/statistics/evidence-queries.md`. Tool procedures and reference
verification: `${CLAUDE_PLUGIN_ROOT}/references/evidence-policy.md`. Calculator:
`${CLAUDE_PLUGIN_ROOT}/scripts/samplesize.py`.

## Core rule

The sample size is the consequence of a chain of decisions, not a number looked up in a table. There is
no fixed number ("30 is enough" is a myth: 30 is the point where the t distribution approaches the normal
and the central limit theorem starts to help, not a study size; Nguyễn Văn Tuấn 2018): n depends on the
design, the outcome type, the effect size, the variability, α and power. A sample that is too small
(cannot answer the question) or too large (wasteful, exposes participants needlessly) is an ethical
problem. Every parameter that enters a formula must have a **source** (a prior study found through the
evidence sources, a pilot, or an assumption labelled as such). The test used to calculate the sample
size must be the test in the SAP.

The users are medical students, doctors and health workers: explain each parameter (power, α, effect
size) in plain words at its first use, so they can defend it before a committee themselves.

## Inputs

- Read if present: `03_protocol/protocol.md` (from the `protocol-design` skill: design, primary outcome,
  main comparison, expected number of confounders to adjust for, the sample-size hand-off block) and
  `02_evidence/*` (take parameters from the evidence table before searching again).
- Also used before the design exists, when the author has a research question and wants to know which
  prior-study parameters will be needed: run steps 1–4 and return the parameter table with its gaps.
- Ask **once**, in one question, for everything still missing; never one question at a time.
- If the user says not to ask ("cứ làm luôn", "just do it"): do not ask. Open the answer with an
  **Assumptions / Giả định** box listing every assumption made, and put the riskiest one in the list of
  items for the user to confirm; record the box in `decisions.md`. This never opens a gate:
  `gate.py open` runs only after the author approves in chat (a gate is the author's act).

## The seven steps (in order, none skipped)

```
Research question → Primary outcome → Effect measure → Expected effect size (evidence sources)
→ α / power / dropout → Sample size (+ sensitivity) → Test selection + SAP
```

### Step 1 – Research question

Force it into PICO/PECO: population, intervention or exposure, comparator, outcome, design (RCT /
pilot–feasibility / cohort / case-control / cross-sectional / diagnostic / non-inferiority / qualitative).
If the design or comparator is not given, ask **one** question that gathers everything missing, then
continue. No research question at all → use the Skill tool with `research-question` first.

### Step 2 – Primary outcome

Exactly one primary outcome, with its measurement definition and time point. Several primary outcomes →
choose one or split α (record it in the SAP). Classify it: continuous / binary / time to event / ordinal /
count / diagnostic accuracy / prevalence.

### Step 3 – Effect measure

From outcome type + design → choose the estimand: mean difference, ARR/RR/OR, HR, sensitivity/
specificity, prevalence. Map it to a script subcommand (table in `statistics/sample-size-formulas.md`).

### Step 4 – Expected effect size from the literature

Required before any calculation. Tool calls and verification: `evidence-policy.md`. Template question for
each parameter: `statistics/evidence-queries.md`.
1. Search the first available evidence source for **each missing parameter**: control-group proportion or
   mean, SD, expected effect or MCID, dropout, ICC (if clustered), margin (if non-inferiority), prevalence
   (if descriptive). Check each number against the abstract.
2. **Always** search PubMed (or Europe PMC) and Consensus alongside it, and read numbers from the
   abstract. Prefer Vietnamese or Asian studies for baseline parameters (proportions, SD).
3. OpenEvidence geo-blocked, not signed in, or failing for a technical reason → tell the user in one
   sentence, **do not stop**, continue with PubMed and Consensus.
4. Build the **parameter table**: Parameter | Value chosen | Source (author, year, design, n, PMID/DOI) |
   Range in the literature. The number must be readable in the abstract or full text the tool returned.
   Key numbers are re-read from the raw tool output when a summarising layer sits between the tool and the
   agent (evidence-policy §Intermediate summary layer).
5. Main value = the study closest to the author's population and setting. The target difference (Δ, p₂)
   follows **DELTA2** (Sones/Cook 2018, Trials, PMID 30305155): it must be both **important** (worth
   detecting) and **realistic** (achievable). Source order: (a) a published MCID for the same scale and
   population; (b) the opinion of clinicians and patients on what change matters; (c) a pilot; (d) the
   effect in the literature, as a cautious estimate from the RCT with the closest population, never the
   optimistic point estimate.
   - Do **not** use the lower CI bound as the main value when the CI is wide, I² > 50% or there are
     < 5 studies: the lower bound of an imprecise pooled estimate is not "the smallest important effect".
     Put the lower bound and the prediction interval into the sensitivity table. (Checked example from
     the source test run: OR 4.03 [1.16–14.05], I² = 73%, 5 studies → using the lower bound 1.16 gave
     n = 8,230, infeasible and not clinically meaningful. This figure is the source's; it cannot be
     re-run here because the control-group exposure proportion is not given.)
   - n above about 3 × the realistic recruitment (a **default**, `judgement-defaults.md`) → do not accept
     the number; propose changing the primary outcome (a continuous or more sensitive variable), the
     design (pilot, multicentre) or the follow-up time, and put it in the list for the user to confirm.
   - State in the justification how the target difference was chosen (the DELTA2 reporting requirement
     and the sample-size items of SPIRIT/CONSORT 2025).
   - Δ and SD are taken at **the same time point** as the primary outcome; for behavioural or lifestyle
     interventions, and for interventions added on top of background therapy, see "Matching the time
     point" and "Add-on effects" in `sample-size-formulas.md`. When the source trial has more than two
     arms, convert its SD as in that file (SUSTAIN 5 example). A behavioural RCT at risk of contamination
     between arms is sized as a cluster trial (`--cluster-size --icc`).

No source returns usable numbers → the fallback in `statistics/evidence-queries.md`; label every
parameter without a source **ASSUMPTION / GIẢ ĐỊNH**.

### Step 5 – α, power, dropout

α = 0.05 two-sided; non-inferiority or equivalence → one-sided α 0.025. Power = 0.90 when **any** of these
holds: a phase III or confirmatory trial meant to change practice; the primary outcome is death or a
serious irreversible event; the study is hard to repeat (rare, costly). Otherwise power = 0.80, and report
the n at 0.90 in the sensitivity table. Dropout comes from the literature (step 4); without it, 10–20% as a
stated assumption. Clusters: add `--cluster-size` and `--icc`. These are defaults the author may override.

**Descriptive proportions** (`prevalence`) and the **EPV rule** (`regression-epv`) have no power: drop the
power rule above and choose precision and EPV instead (defaults):
- Absolute precision d: p ≥ 30% → d = 0.05; 10% ≤ p < 30% → d ≈ p/4 (rounded, for example p = 12% →
  d = 0.03); p < 10% → relative precision ε = 0.1–0.2.
- EPV = 10 minimum; report EPV = 20 in the sensitivity table. Count **parameters**, not variables: a
  categorical variable with k levels = k − 1 parameters.
- Cluster sampling with a **fixed number of clusters** (for example 10 communes already chosen): use
  `prevalence --n-clusters k --icc ρ`, not `--cluster-size`. The script reports INFEASIBLE when k/ICC is
  below the required size → advise more clusters (for example more hamlets in each commune) or a looser
  precision.
- A prevalence that needs a screening step (for example masked hypertension = normal clinic BP but high
  home BP): state the **denominator** of p (whole population or only those screened) and take p from a
  study with the same denominator; if the denominator is the screened group, also estimate how many people
  must be screened.

**Qualitative studies** (in-depth interviews, focus groups): there is no formula; **do not run the
script**. Argue the sample size from:
- **Information power** (Malterud 2016, Qual Health Res, PMID 26613970): fewer participants are needed
  when the aim is narrow, the sample highly specific, the study guided by theory, the dialogue strong and
  the analysis case-by-case; more when the opposite holds. Score these 5 dimensions in a table.
- **Empirical evidence on saturation** (Hennink & Kaiser 2022, Soc Sci Med, PMID 34785096): a homogeneous
  population with a narrow aim usually reaches code saturation at 9–17 interviews or 4–8 focus groups; a
  diverse or stratified sample, or the need for meaning saturation, needs more.
- Plan **per stratum** (for example BMI, wish to conceive), give an expected range (default 12–20
  interviews, `judgement-defaults.md`) rather than one number, and declare a **stopping rule** in advance
  (for example 2–3 consecutive interviews with no new code, judged per stratum).
- Report against SRQR/COREQ.

**Pilot / feasibility trials**: no efficacy test, no power. Size by the precision of the feasibility
estimates (recruitment, retention, adherence rates: `prevalence` with the chosen p and d) and/or the
estimate of SD for the main trial; a rule of thumb for pilots may be cited once its citation is verified
through PubMed. Never conclude efficacy from a pilot.

### Step 6 – Calculate the sample size

Run the script; never calculate by hand:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/samplesize.py" <design> [options] --json
python "${CLAUDE_PLUGIN_ROOT}/scripts/samplesize.py" sensitivity --design <design> --vary <param> --values a,b,c
```

The script needs no scipy (it falls back to Python's `statistics.NormalDist`, Python ≥ 3.8) and no
`pip install`. `python "${CLAUDE_PLUGIN_ROOT}/scripts/samplesize.py" --help` lists every design and option;
`<design> --help` lists the options of one design.

- Report n **exactly as the script returns it**: the script divides the unrounded n by (1 − dropout) and
  then rounds up. Never round first and divide again (worked example in `sample-size-formulas.md`).
- `sensitivity --design` supports two-means, two-props, survival, prevalence and regression-epv (for
  prevalence you can vary `p`, `width`, `icc`, `n_clusters`, `deff`; for EPV vary `epv`, `p_outcome`,
  `predictors`).
- A study with both a descriptive and an analytic aim: compute both, take the larger n, and present both
  in the justification.
- Always run `sensitivity` on the most uncertain parameter (usually the effect size or SD), with at least
  4 values; when the user already has a fixed n, run `power` to report the power achieved.
- A **key secondary outcome under hierarchical testing** (for example a hormone outcome tested after
  weight): run `power` for it at the primary's analysable n and report the result; power < 0.80 → say so
  plainly, or propose a larger n. Example (`power --design two-means --n 92 --delta 4 --sd 12 --json`):
  power 0.6182.
- When varying the control proportion `p1`, add `--link rr` (keep RR) or `--link arr` (keep ARR) so p₂
  is recomputed; without a link p₂ stays fixed and the script stops with a message if p1 = p2.
  (`--link d` keeps Cohen d when varying `sd`; the table is then constant by construction, so never
  present it as an SD sensitivity analysis.)
- ANCOVA as the main analysis: n × (1 − r²) with a sourced r, otherwise keep the t-test n (conservative).
  Matched case-control: `two-props` is only an approximation; state it.
- AI/ML studies: the validation set counts patients (`prevalence --n-clusters --icc`), prediction models
  follow Riley 2020 (`pmsampsize`), training sets use learning curves (`sample-size-formulas.md` §AI /
  machine-learning models).

### Step 7 – Test selection and SAP

Choose the test with `statistics/test-selection.md` (outcome × number of groups × pairing × assumptions).
Fill `statistics/sap-template.md` into `03_protocol/sap.md`; its section 5 copies the justification
paragraph below.

## Output (in this order)

1. **PICO + design summary** (3–5 lines).
2. **Parameter table with sources** (step 4). Every row has a citation or the word **ASSUMPTION /
   GIẢ ĐỊNH**.
3. **Sample-size result**: n per group, total n, n to recruit after dropout; for survival add the number of
   events; for clusters add the number of clusters.
4. **Sensitivity table** (at least 4 values of the most uncertain parameter).
5. **"Sample size justification" paragraph**, ready to paste into the protocol (template at the end of
   `sample-size-formulas.md`), with the formula and references.
6. **"How to explain this to the committee"** (Giải thích cho hội đồng): one plain-language sentence per
   parameter (why this value, which source) + 3–5 questions committees often ask, with suggested answers.
   In a project file it is always written; in a chat-only answer, add it when the user mentions a
   committee or defence, or the n is for a thesis or institutional project (CK1, CK2, ThS, NCS, đề tài
   cơ sở).
7. **Main statistical test** + alternative test + reason.
8. **SAP** (when asked for, or when the user is writing a protocol) per `sap-template.md`.
9. **References**: cite as `[@id]` (`evidence-policy.md` §Citing sources); bibliographic details (year,
   volume, pages) come from the ledger records that `search_lit.py add` built from PubMed metadata, for
   papers from every source, OpenEvidence and Consensus included; check with
   `verify_refs.py <project> --cite <file>`; numbers come only from `cite_render.py`.

**Where it goes**: in a project, write items 1–7 and 9 to `03_protocol/sample-size.md` and item 8 to
`03_protocol/sap.md`, in `project.yaml → language.output` (chat follows the user; when the output is
Vietnamese, keep the English statistical term in brackets at its first use). Fill section 2.3.2 of
`03_protocol/protocol.md` from the justification paragraph. Without a project folder, answer in chat and
ask in one line at the end whether to save it (saving needs a project: `research-project-setup`). No
remarks about "the limitations of AI". End in the order of evidence-policy §Citing sources (the
single confirmation question → the sources line → any Consensus notice, in chat
only).

## Gate G2 and hand-off

The SAP must end with the analysis register (section 16 of the template) before G2 is approved.
Ask the author to approve `03_protocol/protocol.md`, `03_protocol/sample-size.md` and `03_protocol/sap.md`.
After approval: `python "${CLAUDE_PLUGIN_ROOT}/scripts/gate.py" open <project> G2 --by "<author>" --files 03_protocol/sap.md`, then
set `STATUS.md` row 3 to `done`. Never open the gate on the author's behalf without that approval. Next in
the chain: the CRF and data dictionary from the variables table in `03_protocol/variables.md`
(`ethics-and-crf`, phase P4).

## Common errors

| Error | Fix |
|---|---|
| Using the "hoped-for" effect from an abstract instead of an MCID | Choose the target difference by DELTA2 (MCID → opinion → pilot → cautious literature) |
| Using the lower CI bound of a heterogeneous meta-analysis (high I², wide CI) as Δ → n in the thousands | Put the lower bound and the prediction interval into the sensitivity table; the main value must be realistic; infeasible n → change outcome or design |
| A qualitative study that says "interviews until saturation" with no planned range | Argue from information power + the empirical saturation range, per stratum, with a stopping rule |
| A pilot powered for efficacy | Size a pilot by the precision of feasibility estimates; no efficacy conclusions |
| Sizing an AI model by images or frames as if they were independent | The unit is the patient or case; `prevalence --n-clusters --icc` (`sample-size-formulas.md` §AI / machine-learning models) |
| "A sample of 30 is enough" | There is no fixed number; calculate from design, outcome, effect size, SD, α, power |
| Taking the SD from a study with another scale or time point | State the scale and time point in the evidence question; convert SD from SE/CI/IQR per `sample-size-formulas.md` |
| Non-inferiority with a two-sided α 0.05 | One-sided α 0.025; the margin must be argued |
| Survival sized by n instead of events | Report events and n; explain that follow-up is long enough to reach the events |
| Ignoring clustering (multicentre, clusters) | Multiply by the design effect; the SAP uses a mixed model or GEE |
| Sizing with one test and analysing with another | Align with `test-selection.md`; if the main analysis is ANCOVA, state that the t-test sample size is conservative |
| A result without a sensitivity table | Always run `sensitivity` |
| A parameter without a source and without the label ASSUMPTION | The parameter table must have a Source column |
| Asking the user many separate questions | Gather everything missing into one question |
| An "associated factors" study sized only by the proportion formula (n = Z²p(1−p)/d²) | Compute `prevalence` for the descriptive aim and `regression-epv` (or `two-props`) for the analytic aim; take the larger n |
| Cluster sampling (communes, schools, wards) without a design effect | `prevalence --deff`, `--cluster-size --icc`, or `--n-clusters --icc` when the number of clusters is fixed |
| Only 10 clusters, but the DE is computed from an assumed cluster size, giving an n that looks feasible | Use `--n-clusters`; a high ICC makes n grow very fast or become infeasible – run sensitivity on ICC |
| Small p (< 10%) with absolute precision d = 0.05 | Use `--relative-precision` (ε = 0.1–0.2) or d ≤ p/4 |
| OpenEvidence blocked, so going straight to assumptions | Search PubMed + Consensus first; assume only when none of the sources has numbers |

## Why these rules (change history)

18 Nov 2026 (10 edits to the skill, `formulas.md` and `test-selection.md`):
- The lower-CI rule was replaced by DELTA2 (target difference important and realistic; source order MCID →
  stakeholder opinion → pilot → cautious prior evidence; lower CI and prediction interval only in
  sensitivity; infeasible n → change outcome or design). The most serious test-run failure: the old rule
  turned a wide pooled interval (lower limit 1.16; OR 4.03, 95% CI 1.16–14.05, I² = 73%, menstrual
  regularity) into 8,230 participants; the lower limit of an imprecise interval is noise (Sones/Cook 2018,
  DELTA2).
- The justification states how the target difference was chosen: DELTA2 and the SPIRIT/CONSORT 2025
  sample-size items require it.
- Qualitative sample size (information power, saturation ranges, per-stratum plan, stopping rule; no
  script): the skill had no method, so the qualitative arm of the test case had no justified n
  (Malterud 2016; Hennink & Kaiser 2022).
- Pilot and feasibility trials sized by precision, no power, no efficacy claims: a Vietnamese lifestyle
  trial would realistically start as a pilot.
- ANCOVA n × (1 − r²): lifestyle trials are usually analysed with baseline adjustment; ignoring the
  correlation overstates n (the Borm et al. approach).
- Matched case-control row: conditional analysis, `two-props` only an approximation (Dupont method in PS,
  `epiR`).
- The "30 is enough" myth; samples too small or too large are an ethics issue (Tuấn 2018, sample-size
  chapter).
- Estimation over testing, predefined clinical thresholds for reading CIs, multiplicity, R/Stata scripts
  rather than Excel (Tuấn 2018, P-value and data-analysis chapters).
- The design list gained pilot and qualitative; five new error rows record these failure modes (by
  content: the hoped-for effect, lower-CI, qualitative, pilot and "30 is enough" rows of the table).
- `samplesize.py` itself was unchanged by these edits; after them the skill still passed its validator
  and the script gave the same results (124 for the test-case RCT; the notes do not give that run's
  inputs, so it is not re-run here).

20 Nov 2026 (v3):
- `samplesize.py` no longer needs scipy (falls back to `statistics.NormalDist`); reference values
  re-checked: two-means Δ 3 / SD 5.5 → n raw 53.72; 30% vs 15% → 121 per group; p = 0.5, d = 0.05 → 385;
  survival HR 0.7 → 247 events. (Re-run here: same values; `sample-size-formulas.md` §Worked examples.)
- Commands use the skill's own folder instead of a home-directory path; in this plugin that is
  `${CLAUDE_PLUGIN_ROOT}/scripts/samplesize.py`.
- Step 6: power for the key secondary outcome under hierarchical testing.
- `formulas.md`: pooled SD and absolute → % conversion with a checked example; a new section "AI /
  machine-learning models" (validation set counted in patients with `--n-clusters --icc`, Riley/pmsampsize,
  learning curves) and one error row (the AI-frames row) after a test case on an AI-integrated cardiac
  surgical robot; SD conversion for trials with more than two arms (SUSTAIN 5), Δ and SD at the primary
  outcome's time point (lifestyle effects fade, PMID 28178985), add-on effects usually smaller, after a test
  case on metformin + insulin + GLP-1 RA ± lifestyle in type 2 diabetes.
- SKILL.md: matching reminders, and cluster sizing when the intervention may contaminate the control arm.
- `sap-template.md`: SPIRIT 2025 referenced.

## Sources named

As given in the source skill and its change notes (identifiers copied from the source, not from memory;
each still enters a project only through `search_lit.py add` and `verify_refs.py`):
- Sones W, Julious SA, Rothwell JC, et al. Development of the DELTA2 guidance. Trials. 2018;19:542.
  doi:10.1186/s13063-018-2887-x. PMID 30305155.
- Malterud K, Siersma VD, Guassora AD. Sample size in qualitative interview studies: information power.
  Qual Health Res. 2016;26:1753-60. doi:10.1177/1049732315617444. PMID 26613970.
- Hennink M, Kaiser BN. Sample sizes for saturation in qualitative research. Soc Sci Med.
  2022;292:114523. doi:10.1016/j.socscimed.2021.114523. PMID 34785096.
- Cradock 2017 (lifestyle effect on HbA1c over time), PMID 28178985.
- Named without identifiers (verify before citing): Nguyễn Văn Tuấn (2018); Guenther; Fleiss; Schoenfeld;
  Buderer 1996; Peduzzi 1996; Riley 2020; Dupont; Borm et al.; SUSTAIN 5; ICH E9 and E9(R1); Gamble 2017;
  SPIRIT 2025 and CONSORT 2025 (cited in `design/protocol-template.md`); SRQR; COREQ; TRIPOD+AI;
  STARD-AI; CLAIM.
