---
name: protocol-design
description: 'Use when a study must be designed or a protocol drafted or reviewed: design choice, population, inclusion and exclusion criteria, sampling, outcomes, variables, bias and confounding, "đề cương nghiên cứu" or "chương 2 đối tượng và phương pháp". Triggers: "thiết kế nghiên cứu", "chọn thiết kế", "đề cương", "protocol", "tiêu chuẩn lựa chọn", "tiêu chuẩn loại trừ", "biến số nghiên cứu", "bảng biến số", "sai số", "yếu tố nhiễu", "confounder", "bias", "cohort hay case-control", "hồi cứu hay tiến cứu", "SPIRIT", "bảng dự kiến kết quả", "study design", "review my protocol".'
---

Methods content by Amelia Le (co-author), adapted for clinical-research-orchestra.

# Protocol design

## 1. Core rule
Design follows the question, not habit. Every choice (design, eligibility, variables, confounder
control) states **why, and what it costs**; write both into the protocol. Thresholds are defaults the
author may override (`${CLAUDE_PLUGIN_ROOT}/references/judgement-defaults.md`). Never write a PMID, DOI
or guideline year from memory (`${CLAUDE_PLUGIN_ROOT}/references/evidence-policy.md`).

## 2. Scope
No sample size (use `sample-size-sap`); no ethics file or CRF (`ethics-and-crf`, phase P4).

## 3. Inputs
`01_question/question.md` and `02_evidence/*`. First run
`python "${CLAUDE_PLUGIN_ROOT}/scripts/gate.py" check <project> G1`: if closed, say so and stop unless
the author waives G1. No clear question → `research-question` first. Ask once for site, period,
patients per month, randomisation, records, budget; if told not to ask, open with an **Assumptions /
Giả định** box (this never opens or waives a gate; only the author's approval in chat does).

## 4. Steps
Detail for every step is in the workflow file (§7).
1. Design on two axes, time direction × design type ("prospective" ≠ "cohort"), one alternative,
   main limitation: `${CLAUDE_PLUGIN_ROOT}/references/design/design-selection.md`.
2. Diagnostic criteria with citations (ADA, KDIGO, DSM-5), current version via `guideline-check`.
3. Population, eligibility (exclusion is not negated inclusion), sampling named truthfully;
   representativeness matters only for prevalence aims.
4. Outcomes and the variables table, each variable serving an objective → `03_protocol/variables.md`.
5. Measurement and questionnaire rules; Vietnamese-validated tools.
6. Bias, confounding, reverse causation, time zero, DAG:
   `${CLAUDE_PLUGIN_ROOT}/references/design/bias-confounding.md`; Bradford Hill for causal language.
   - 6b. Drug or device: regulatory status and off-label use, drug source and blinding, women of
     reproductive age, washout at enrolment, standardised hormone assays, dose escalation, safety, DSMB.
   - 6c. Phase I–IV only for drugs, otherwise "Phase: Not Applicable"; add-on trials need one
     background-dose protocol for all arms and rescue criteria; estimand per ICH E9(R1).
7. Intervention reporting (TIDieR, CERT), STROBE-Equity where relevant; main analysis per objective.
8. Qualitative arm: the 8 protocol essentials.
9. SPIRIT 2025 (34 items) and CONSORT 2025 for trials; the full SPIRIT 2013→2025 numbering map is
   unverified, so say so.
10. Dummy tables, at least one per objective:
   `${CLAUDE_PLUGIN_ROOT}/references/design/protocol-template.md`.

## 5. Output
Part A design decision, Part B draft Chapter 2 by the Vietnamese frame (each table once; sample size
left empty), Part C sample-size hand-off, at most 3 items to confirm, references cited as `[@id]`
(`${CLAUDE_PLUGIN_ROOT}/references/evidence-policy.md` §Citing sources). Write
`03_protocol/protocol.md` and `03_protocol/variables.md` in `project.yaml → language.output`; set
`STATUS.md` row 3 to `doing`. No project: answer in chat and offer to save. Word: the `docx` skill if
installed.

## 6. Hand-off
Next: use the Skill tool with `sample-size-sap`. Gate G2 opens after the author approves protocol and
SAP: `python "${CLAUDE_PLUGIN_ROOT}/scripts/gate.py" open <project> G2 --by "<author>"`.

## 7. Workflow
`${CLAUDE_PLUGIN_ROOT}/references/workflows/protocol-design.md`
