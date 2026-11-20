---
name: sample-size-sap
description: 'Use when a sample size must be calculated, explained or justified, power computed, a Statistical Analysis Plan (SAP) written, or a statistical test chosen for a clinical or epidemiological study. Triggers: "tính cỡ mẫu", "cỡ mẫu bao nhiêu", "n bao nhiêu là đủ", "công thức cỡ mẫu", "giải thích cỡ mẫu cho hội đồng", "kế hoạch phân tích thống kê", "chọn test thống kê", "dùng test gì", "sample size", "power", "SAP", "effect size", "MCID", "non-inferiority margin", "cluster ICC"; or when a protocol lacks a sample-size section.'
---

Methods content by Amelia Le (co-author), adapted for clinical-research-orchestra.

# Sample size and SAP

## 1. Core rule
n follows design, outcome type, effect size, variability, α and power; "30 is enough" is a myth. Every
parameter has a source or the label **ASSUMPTION / GIẢ ĐỊNH**; the test used for n is the test in the
SAP. Thresholds are defaults (`${CLAUDE_PLUGIN_ROOT}/references/judgement-defaults.md`); never a PMID or
DOI from memory (`${CLAUDE_PLUGIN_ROOT}/references/evidence-policy.md`). Explain power, α and effect size
in plain words.

## 2. Inputs
`03_protocol/protocol.md` (from `protocol-design`) and `02_evidence/*`. No question yet → use the Skill
tool with `research-question`. Ask once for everything missing; if told not to ask, open with an
**Assumptions / Giả định** box.

## 3. Seven steps, in order
1. Question as PICO/PECO and design.
2. One primary outcome, its measure and time point.
3. Effect measure → script design:
   `${CLAUDE_PLUGIN_ROOT}/references/statistics/sample-size-formulas.md`.
4. Sourced parameters (`${CLAUDE_PLUGIN_ROOT}/references/statistics/evidence-queries.md`). Target
   difference by DELTA2 source order: MCID > stakeholder opinion > pilot > cautious prior evidence; lower
   CI bound only in sensitivity. Δ and SD at the primary outcome's time point; convert the SD when the
   source trial has more than two arms; assume add-on effects are smaller; size by cluster when
   contamination is likely.
5. α, power, dropout (defaults in the workflow).
6. n with sensitivity (§4).
7. Test (`${CLAUDE_PLUGIN_ROOT}/references/statistics/test-selection.md`) and SAP
   (`${CLAUDE_PLUGIN_ROOT}/references/statistics/sap-template.md`).

## 4. The script
```
python "${CLAUDE_PLUGIN_ROOT}/scripts/samplesize.py" <design> [options] --json
python "${CLAUDE_PLUGIN_ROOT}/scripts/samplesize.py" sensitivity --design <design> --vary <param> --values a,b,c
```
Report n exactly as the script returns it; the script divides the unrounded n by (1 − dropout) and then
rounds up; never round first. Always run a sensitivity table on the most uncertain parameter, and `power`
when n is fixed. Step 6 also runs `power` for the key secondary outcome under hierarchical testing.

## 5. Special cases
- Descriptive and analytic aims: compute both, take the larger.
- Qualitative: information power and saturation (Malterud 2016; Hennink & Kaiser 2022); no formula.
- Pilot or feasibility trial: sized by precision; no efficacy power.
- ANCOVA: n × (1 − r²). Matched case-control: `two-props` only approximates; say so.
- AI/ML: the validation set counts patients, `--n-clusters --icc` for clustering; prediction models
  follow Riley 2020 (pmsampsize); training sets use learning curves.
- Infeasible: n above about 3 × feasible recruitment (a default) → change outcome, design or follow-up;
  ask the author.

## 6. Output
`03_protocol/sample-size.md` (summary, parameter table, n, sensitivity table, justification, a "how to
explain this to the committee" paragraph, main test) and `03_protocol/sap.md`, in
`project.yaml → language.output`. No project: answer in chat and offer to save. Then ask the author to
approve; after approval run
`python "${CLAUDE_PLUGIN_ROOT}/scripts/gate.py" open <project> G2 --by "<author>"` and set `STATUS.md`
row 3 to `done`.

## 7. Workflow
`${CLAUDE_PLUGIN_ROOT}/references/workflows/sample-size-sap.md`
