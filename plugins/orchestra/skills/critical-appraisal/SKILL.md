---
name: critical-appraisal
description: 'Use when a research paper or a body of evidence must be appraised for trustworthiness, value and relevance before it is used, with the tool matched to the real study design, including journal club. Triggers: "thẩm định y văn", "đánh giá chất lượng bài báo", "bài này có tin được không", "đánh giá phê bình", "critical appraisal", "risk of bias", "nguy cơ sai lệch", "RoB 2", "ROBINS-I", "ROBINS-E", "Newcastle-Ottawa", "NOS", "AXIS", "CASP", "JBI", "AMSTAR 2", "QUADAS", "PROBAST", "GRADE", "CERQual", "journal club"; or when literature-search reaches its appraisal step.'
---

Methods content by Amelia Le (co-author), adapted for clinical-research-orchestra.

# Critical appraisal

## 1. Three questions
Answer them in this order, for the user's own decision:
1. **Trustworthy?** Are design and conduct sound enough that bias, confounding and chance do not explain the result?
2. **Valuable?** Effect size with 95% CI and its clinical meaning, not p < 0.05.
3. **Relevant?** Does it fit the user's patients, setting and health system?

## 2. Rules
- Appraise the **real design**, not the label. Walk `${CLAUDE_PLUGIN_ROOT}/references/appraisal-tools/design-tree.md`.
- Pick the tool by design: `${CLAUDE_PLUGIN_ROOT}/references/appraisal-tools/tools-by-design.md`; domains in `${CLAUDE_PLUGIN_ROOT}/references/appraisal-tools/tool-domains.md`.
- A reporting checklist (CONSORT, STROBE, PRISMA, SRQR) is not an appraisal tool.
- Never sum items into a score ("NOS ≥ 7 is good"). Report items and name the critical flaw.
- Missing reporting is "unclear / Không rõ", never "yes". Each domain answer quotes its basis.
- Check source credibility first (retraction, journal, registration, duplicate publication): `${CLAUDE_PLUGIN_ROOT}/references/appraisal-tools/source-credibility.md`.

## 3. Input
One reference id from `ledgers/references.json` (the call from `literature-search` step 4c), or a PDF, PMID or DOI the user gives. Use full text when available. With an abstract only, write "preliminary appraisal from abstract" at the top and mark unassessable domains "Unclear, needs full text". Trials: compare the registered outcome with the reported one. Ask once what decision the paper informs; if the user says not to ask, open with an **Assumptions / Giả định** box (this never opens a gate).

## 4. Steps
1. Question: PICO/PECO (SPIDER if qualitative), the paper's beside the user's.
2. Relevance screen: two "yes" to continue.
3. Real design and tool.
4. Trustworthy: credibility checks, then each domain (Yes / Probably yes / Probably no / No / No information); overall = worst domain.
5. Valuable: CI read by clinical zones, absolute effect (ARR, NNT), multiplicity, spin.
6. Relevant: do not downgrade analytic studies for an unrepresentative sample.
7. Verdict: usable / use with caution / should not be used, with the deciding flaw. One study alone: suggest looking for a systematic review.

For several papers on one outcome add GRADE (or GRADE-CERQual), marked preliminary when made from abstracts.

## 5. Output
`02_evidence/appraisal/<ref-id>.md` in `project.yaml → language.output`, three-question verdict first. Then set the reference record's `design` and `rob` fields in `ledgers/references.json`. Every cited reference carries a PMID or DOI a tool returned in this session (`${CLAUDE_PLUGIN_ROOT}/references/evidence-policy.md`); never one from memory.

**Journal-club mode** (no project folder): write `appraisal-<first-author><year>.md` beside the PDF; add a .docx with the `docx` skill only if the user asks.

## 6. Workflow
`${CLAUDE_PLUGIN_ROOT}/references/workflows/critical-appraisal.md`
