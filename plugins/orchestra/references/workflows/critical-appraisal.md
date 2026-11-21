# Critical appraisal: full workflow

Methods content by Amelia Le (co-author), adapted for clinical-research-orchestra. Source: her
`critical-appraisal-vi` v3 (20 Nov 2026) and its two change notes (18 Nov, 20 Nov). Where the v3 text
and the 18 Nov notes differ, v3 is followed. Thresholds are **defaults** the author may override, not
standards (`${CLAUDE_PLUGIN_ROOT}/references/judgement-defaults.md`).

Tool procedures, the reference-verification table and the retraction check:
`${CLAUDE_PLUGIN_ROOT}/references/evidence-policy.md`. Appraisal library:
`${CLAUDE_PLUGIN_ROOT}/references/appraisal-tools/design-tree.md`,
`${CLAUDE_PLUGIN_ROOT}/references/appraisal-tools/tools-by-design.md`,
`${CLAUDE_PLUGIN_ROOT}/references/appraisal-tools/tool-domains.md`,
`${CLAUDE_PLUGIN_ROOT}/references/appraisal-tools/tool-references.md`,
`${CLAUDE_PLUGIN_ROOT}/references/appraisal-tools/source-credibility.md`.

## Why a separate skill
Appraisal has enough detail (a design tree, many tools) to swamp the literature skill, and it must
also work alone (journal club, "is this paper trustworthy?"). `literature-search` calls it at its
step 4c; the `/orchestra:appraise` command calls it for one paper.

## What appraisal is
A systematic judgement of one study on **three questions before a decision**:
1. **Trustworthy (validity)?** Are the design and conduct tight enough that bias, confounding and
   chance do not explain the result?
2. **Valuable (results)?** How large is the effect, how precise (95% CI), and does it matter
   clinically, not only p < 0.05?
3. **Relevant (applicability)?** Does it apply to the user's patients, setting and health system
   (often Vietnam)?

Appraise the **real design**, not the name the authors gave it, and use the right tool for that design:
a tool for the wrong design gives the wrong verdict. No study is perfect: separate **critical flaws**
(which remove the value of the result) from **minor flaws** (worth noting), and do not conclude from a
single paper when a systematic review exists.

**A reporting standard is not an appraisal tool.** CONSORT, STROBE, PRISMA, SRQR check whether the
paper *reported enough*; RoB 2, ROBINS-I, NOS, CASP check whether the study was *done correctly*.
Complete reporting does not mean low bias. Where the paper does not report, write "Unclear
(Không rõ)", never infer that it was done.

The reader is a medical student, doctor or health worker: explain a term at first use and keep the
English term in brackets.

## Inputs
- One paper: a reference id from `ledgers/references.json` (the interface `literature-search` uses),
  a PMID, a DOI, a PDF or an abstract the user gives; or a list of papers from the evidence table.
- The user's question or PICO, to judge relevance. If missing, ask once: "What decision will this
  paper inform, and for which patients?" If the user said not to ask (cứ làm luôn), do not ask: open
  with an **Assumptions / Giả định** box. This never opens a gate:
  `gate.py open` runs only after the author approves in chat (a gate is the author's act).
- Getting the content: PubMed metadata for the abstract; full text when a PMC copy exists; the PDF the
  user supplies. **Abstract only → state "preliminary appraisal from abstract (thẩm định sơ bộ từ
  abstract)" at the top**, score only the domains an abstract allows, and write "Unclear, needs full
  text" for the rest. Set `fulltext_read` in the ledger record accordingly.
- A trial: look up its registration (NCT) on ClinicalTrials.gov (`search_lit.py trial`, or
  `get_trial_details`) to compare the registered outcome with the reported one.

## The 7 steps (WHO EMRO / CASP / CEBM; course slides Module 7)
**Step 1, ask the question.** PICO/PECO for quantitative work; aims or SPIDER for qualitative work.
Write the *user's* question next to the *paper's* question.

**Step 2, relevance screen.** Does the paper answer the question for patients like the user's? Are the
aims clear? Does the method fit the aims? Continue only with two "yes"; with "no" stop and record why.

**Step 3, real design.** Walk the design tree, then pick the tool from the table. A paper can contain
results from different designs (an RCT with an observational secondary analysis): appraise each result
the decision relies on.

**Step 4, trustworthy?** Run the source-credibility checks first, then score each domain of the tool
(`tool-domains.md`). Each domain gets an answer on the scale **Yes / Probably yes / Probably no / No /
No information (Có / Có lẽ có / Có lẽ không / Không / Không rõ)**, with a **quoted sentence from the
paper as the basis** (or "not reported"). Domain judgement: Low / Some concerns / High (RoB 2); Low /
Moderate / Serious / Critical (ROBINS-I V2, ROBINS-E). The overall level is the worst domain (RoB 2,
ROBINS); several "some concerns" can raise it to "high": state why. NOS, AXIS, JBI, CASP: never sum
the items into one score to rank quality; report each item and the critical flaws.

**Step 5, valuable?**
- Quantitative: effect size (RR, OR, HR, ARR, MD, NNT/NNH) with 95% CI; is the limit of the CI nearest
  1 (or 0) still worth caring about? Compare with the MCID. p < 0.05 does not mean important; p ≥ 0.05
  does not mean no effect (look at the CI width).
- **Read the 95% CI by clinical zones** (Nguyễn Văn Tuấn 2018, interpretation chapter): set beforehand
  a threshold for benefit and harm (illustration only: RR ≤ 0.90 beneficial, RR ≥ 1.10 harmful; the
  clinician sets it per outcome), then place the CI. Whole CI in the beneficial zone: effective. CI in
  the negligible zone (even with p < 0.05): the effect is not worth attention. CI spanning beneficial
  and harmful: no conclusion possible (usually small n). Never write "no difference" because p > 0.05:
  for example RR 0.70, CI 0.47–1.02 suggests benefit but is not conclusive; it is not "negative".
- Do not compare P values to say which effect is larger: P reflects both effect size and sample size.
- Prefer absolute effects (ARR, NNT) for decisions. With only RR or OR, compute ARR from the baseline
  risk in the user's population and state that assumption.
- **Multiple comparisons and subgroups**: the chance of at least one "significant" result among k
  tests is 1 − (1 − α)^k (k = 10 gives about 40%). A single positive result among many tests, or in a
  very narrow subgroup not declared beforehand, is a hypothesis to retest, not a finding.
- **Spin**: does the abstract conclusion go beyond the primary outcome? Does it stress secondary or
  subgroup results when the primary is negative?
- Qualitative: are findings clear, tied to data (quotations), and are alternative explanations considered?

**Step 6, relevant?** For analytic or causal studies, **do not downgrade only because the sample is
not "representative"**: internal validity comes first; generalisation rests on biological knowledge
and replication in other populations (Tuấn 2018, representativeness chapter). Representativeness is a
critical criterion only when the aim is to estimate a proportion for a defined population. Check:
population (age, sex, severity, BMI, Asian ethnicity), setting (hospital level, resources), whether the
intervention can be done in Vietnam (cost, staff, drug on the market), whether the outcome matters to
patients or is a surrogate, and whether benefit outweighs harm and cost.

**Step 7, overall verdict.** Answer three questions after reading (Tuấn 2018, how-to-read chapter):
(1) Do I believe this result? (2) If so, must I change practice, given this effect size? (3) What did
I learn, and how would I design it if I did it again? Then write one paragraph: confidence + size and
precision + relevance → **usable / use with caution / should not be used** for the user's decision,
and which critical flaw decides it. If the user is reading a single study, suggest looking for a
systematic review.

## Reading order and warning signs
Reading order: title → abstract (note the numbers and compare with the conclusion) → **tables and
figures** (data are harder to bend than prose) → methods (measurement decides internal validity; how
participants were chosen; analysis and confounder adjustment) → discussion (the authors' view). Trust
the data, not the authors' wording.

Common warning signs (Tuấn 2018, current-issues chapter; reproducibility crisis):
- Chasing statistical significance: many tests, only p < 0.05 reported, p just under 0.05, post-hoc subgroups.
- Love of novelty: "first-ever" results, a very large effect from a small study, no replication.
- Ornate theory: hypothesis written after seeing the data, untested mechanisms.
- Algorithms without a causal basis: prediction or machine-learning models presented as causal evidence; confusing prediction with cause.
- Quantity over quality: repeating known work with nothing new, in a doubtful journal.
- Analysis that cannot be reproduced: software and model not described.

Causation across a body of observational evidence: use the **nine Bradford Hill criteria** (strength,
consistency, specificity, temporality, dose–response, biological plausibility, coherence, experimental
evidence, analogy). Temporality is mandatory; the others support.

## From one paper to a body of evidence
When several papers address one outcome (from `literature-search`):
- **GRADE** (quantitative): start high (RCT) or low (observational; with ROBINS-I the start can be
  high and then be downgraded for risk of bias). Downgrade for risk of bias, inconsistency (I²,
  prediction interval), indirectness (different population, intervention or outcome), imprecision
  (wide CI, few events, crossing a decision threshold) and publication bias. Upgrade (observational)
  for a very large effect, dose–response, and residual confounding that would reduce the effect.
  Result: High / Moderate / Low / Very low.
- **GRADE-CERQual** (qualitative synthesis): methodological limitations, coherence, adequacy of data,
  relevance, giving High / Moderate / Low / Very low per finding.
- A GRADE rating made by one person from abstracts is a **preliminary** rating; say so.

## Output
**One paper → appraisal sheet** `02_evidence/appraisal/<ref-id>.md` (in `project.yaml →
language.output`), in this order:
1. Paper details (Vancouver, PMID/DOI) and the content actually read (abstract / full text / PDF).
2. The paper's question versus the user's question (PICO side by side).
3. Real design and why (from the design tree), the tool chosen and the matching reporting standard.
4. Source credibility (`source-credibility.md`): retraction, journal, funding/COI, registration, registered versus reported outcome.
5. Domain table: Domain | Key question | Answer | Basis (quote / location) | Domain judgement.
6. Results: effect with 95% CI, absolute effect, comparison with the MCID, spin.
7. Applicability to the user's setting.
8. **Conclusion**: Trustworthy (RoB level) – Valuable (size, precision) – Relevant (high/medium/low) → recommendation to use; critical flaws; minor flaws.
9. What the user should still check (at most 3, usually the "Unclear, needs full text" domains).
Then update the reference record in `ledgers/references.json`: `design` and `rob`.

**Several papers → appraisal summary table** (to paste into the evidence table of `literature-search`):

| # | Paper [ref] | Real design | Tool | Main domain of concern | Overall RoB | Effect (95% CI) | Relevant to Vietnam | Note (preliminary from abstract?) |
|---|---|---|---|---|---|---|---|---|

plus a GRADE / CERQual table per main outcome when there are two or more papers.

Citation and verification rules are in `${CLAUDE_PLUGIN_ROOT}/references/evidence-policy.md`: every
reference carries a PMID or DOI that a tool returned in this session; never one from memory.

**Journal-club mode** (no project folder): write `appraisal-<first-author><year>.md` beside the PDF; if
the user asks for a Word file, use the `docx` skill.

## Common errors
| Error | Fix |
|---|---|
| Choosing the tool by the design name the authors give ("prospective study" → appraised as a cohort) | Find the design with the tree; "prospective" is not a synonym of cohort |
| Using CONSORT/STROBE to "score quality" | They are reporting standards; use the matching appraisal tool |
| NOS for an RCT, RoB 2 for a cohort, AMSTAR 2 for a primary study | Right tool for the right design |
| Summing NOS/JBI points into "good quality if ≥ 7" | Report each item; one critical flaw (uncontrolled confounding) can decide |
| Writing "Yes" when the paper does not report | Write "Unclear"; for an abstract write "needs full text" |
| Trusting a paper for its famous journal or author | Source is not content; appraise the methods |
| p < 0.05 = useful; p ≥ 0.05 = no effect | Read effect size, 95% CI, MCID |
| Reading only the abstract's conclusion | Compare with the primary and registered outcomes; check for spin |
| Causal conclusion from a cross-sectional or case-control study | Use "associated with"; consider reverse causation and confounding |
| Appraising qualitative work with quantitative criteria (small n, not randomised) | Use CASP/JBI qualitative: fit of method, reflexivity, rigour of analysis |
| Skipping relevance | Always do step 6; a good paper may still not apply in Vietnam |
| Stopping at one paper when an SR exists | Look for SR/MA and guidelines; appraise the SR with AMSTAR 2 |
| Downgrading an analytic study for a "non-representative" sample | Judge internal validity first; generalise from biology and replication |
| "No difference" when p > 0.05 but the CI is wide | Read the CI by zones (beneficial / negligible / harmful); write "not yet conclusive" |
| Believing a subgroup result with p < 0.05 among dozens of tests | Compute 1 − (1 − α)^k; treat it as a hypothesis to replicate |
| Counting two papers from one trial as two studies | Compare registration, n, dose, duration, authors (`source-credibility.md`); merge into one row |
| Raising a red flag because a PROSPERO/NCT code "looks odd" | Look it up in the registry; PROSPERO has a longer format from 2025 |
| Taking a comment by a summarising layer as paper content | Re-read the raw abstract or JSON before recording a data-integrity concern |

## Basis
Nguyễn Văn Tuấn. Cẩm nang nghiên cứu khoa học: Từ ý tưởng đến công bố. 2018; Ogden J. Thinking
Critically About Research. Routledge; 2019; course slides Critical Thinking in Medical Research
(Module 7).
