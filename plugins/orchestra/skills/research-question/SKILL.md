---
name: research-question
description: 'Use when a medical student, doctor or health worker has a clinical idea, observation or topic and needs a researchable question, PICO/PECO, objectives, hypotheses or a title, or asks whether a topic is feasible, or when stated objectives do not match the design. Triggers: "ý tưởng nghiên cứu", "câu hỏi nghiên cứu", "PICO", "PECO", "mục tiêu nghiên cứu", "giả thuyết nghiên cứu", "đặt tên đề tài", "chọn đề tài luận văn", "đề tài cơ sở", "đề tài này có làm được không", "FINER", "tôi muốn nghiên cứu về", "research question", "research idea", "is this topic feasible".'
---

Methods content by Amelia Le (co-author), adapted for clinical-research-orchestra.

# Research question

## 1. Core rule
The question decides design, sample size, variables and analysis. It must be
answerable with data the user can actually collect at their site, and must not already be answered
by a textbook, a current guideline or a recent systematic review: a "lookup question" is not a
research question. Not every good idea is a doable question. Cite only what a tool returned in this
session, as `[@id]` (`${CLAUDE_PLUGIN_ROOT}/references/evidence-policy.md` §Citing sources); never a
PMID or DOI from memory.

## 2. Inputs
`project.yaml` only. No project → use the Skill tool with `research-project-setup` first.

## 3. Steps
Details, tables and default thresholds for every step are in the workflow file (§7).

- **0** Intake: one combined question for the missing items of six (clinical idea, site, purpose,
  time, data sources, patient numbers); never re-ask what was given.
- **1** A broad topic counts as an idea: explore 3–5 angles in the scoping search.
- **2.0** Renamed-condition check before any query
  (`${CLAUDE_PLUGIN_ROOT}/references/literature/search-strategy.md` §Nomenclature check).
- **2** Regular vs research question test, then a mandatory scoping search ending in one of four
  situations. If a review already exists, reuse its search log and query only the new angle.
- **2b** Device, robot, surgical technique or AI idea: place it at an IDEAL stage (Pre-IDEAL to 4);
  if the device is not available at the site, Feasible = 1 for any effectiveness comparison.
- **3** Hypothesis first (analytic questions), then PICO/PECO or the matching framework, every
  component measurable.
- **4** FINER for 2–3 options, Novel judged with the data × idea novelty matrix; Ethical includes
  equipoise (no placebo RCT of a regimen already proven effective). Recommend one option.
- **5** "So what?": name the story, AND, BUT or HOW.
- **6** List the assumptions of the chosen option; the riskiest goes to the confirmation list.
- **7** Qualitative questions get their own rough size; reject the "n = 30 is enough" myth.
- **8** Objectives whose verbs match the design, hypothesis (or "no hypothesis tested"), one primary outcome.
- **9** Two or three title options with no word the design cannot answer.

## 4. "Just do it" rule
If the user says not to ask ("cứ làm luôn", "just do it"), do not ask. Proceed, open the answer
with an **Assumptions / Giả định** box listing every assumption, put the riskiest in the
confirmation list, and record the box in `decisions.md`. It never opens a gate: `gate.py open` runs
only after the author approves in chat.

## 5. Output
Write `01_question/question.md` in `project.yaml → language.output` (chat follows the user), with
the eight sections listed in the workflow file. Set `STATUS.md` row 1 to `doing`. Ask the author to
approve; after approval run
`python "${CLAUDE_PLUGIN_ROOT}/scripts/gate.py" open <project> G1 --by "<author>"` and set row 1 to `done`.

## 6. Hand-off
Next: use the Skill tool with `literature-search`.

## 7. Workflow
`${CLAUDE_PLUGIN_ROOT}/references/workflows/research-question.md`
