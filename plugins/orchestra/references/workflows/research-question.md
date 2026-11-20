# Research question: full workflow

Methods content by Amelia Le (co-author), adapted for clinical-research-orchestra from her skill
`research-question-refinement-vi` (v3, 20 Nov 2026) and its change notes. Step numbers match the
`research-question` skill.

Numbers marked **default** are judgement defaults, not standards: the author may override any of
them and the override is recorded in `decisions.md`. Shared defaults (for example qualitative
interview counts) live in `${CLAUDE_PLUGIN_ROOT}/references/judgement-defaults.md`.

## Who the users are
Medical students, doctors, nurses and pharmacists; many are doing research for the first time.
Explain each term the first time it is used and keep the English term in brackets. A good research
question decides everything after it: design, sample size, variables, analysis. It must be
answerable with data the user can actually collect where they work and must not already be fully
answered in the literature. Not every good idea is a doable question.

## Step 0 – Intake (one question only)
Needed, six items:
1. the clinical idea or observation;
2. the site (hospital level, department, community);
3. the purpose (graduation thesis for BS/CK1/CK2/ThS/NCS, institutional project "đề tài cơ sở",
   paper, quality improvement);
4. the time available;
5. data sources available (medical records, clinic registers, the hospital information system
   (HIS), which laboratory tests can be done);
6. estimated patients per month or year.

- Whatever is missing goes into **one combined question**; then stop and wait for the answer.
  Never ask item by item, and never re-ask what the user already gave.
- If the user gave items 1–3, assume the rest (label each one "assumption" / "giả định") and continue.
- If the user said not to ask ("không cần hỏi", "cứ làm luôn", "just do it"): do not ask. Open the
  answer with an **Assumptions / Giả định** box listing every assumption, put the riskiest one in
  the "needs your confirmation" list, and record the box in `decisions.md`.

## Step 1 – Broad topic: explore angles
- An idea that is only a broad topic ("đái tháo đường ở người cao tuổi", diabetes in older people)
  still counts as item 1: do not make the user narrow it themselves.
- Run step 2 in **angle-exploration mode**: scan the literature for 3–5 angles (epidemiology,
  associated factors, over- or under-treatment, adherence, complications, screening tools…), then
  fit each angle into a framework (step 3).
- As soon as a direction is chosen, think of the four approach elements together: study design,
  subjects, what is measured, how it is analysed. Feasibility depends on all four; spotting a
  measurement or analysis problem early avoids an unanswerable question (Tuấn 2018).

## Step 2.0 – Renamed-condition check (before any query)
Follow `${CLAUDE_PLUGIN_ROOT}/references/evidence-policy.md` §Nomenclature check; the full search
strategy is handled by `literature-search`. For the scoping search:
1. Search Consensus and PubMed for the last 2 years (**default**):
   `{condition} AND (renamed OR "new name" OR nomenclature OR "formerly known as")`, and read the
   latest guideline or consensus statement.
2. New name or new diagnostic criteria → the P block holds the MeSH term + old name `[tiab]` + new
   name `[tiab]` + new abbreviation. MeSH is often updated late; papers using the new name may carry
   a different MeSH term. Use old and new names in every query below and record the change in the
   search log.
3. Check: run `<PMID of a paper that uses the new name>[pmid] AND (P block)`; 0 results → the P block
   is still incomplete.
4. Verified example: PCOS → PMOS (*polyendocrine metabolic ovarian syndrome*, 2026): add
   `"polyendocrine metabolic ovarian syndrome"[tiab] OR PMOS[tiab]`. The 2026 PLoS Med
   meta-analysis (PMID 42776991) is indexed under
   MeSH "Metabolic Syndrome" and did not match the standard PCOS query; without this check the
   scoping search could wrongly conclude that no research exists. Measure what is missed with
   `(new name) AND (I block) NOT (old P block)`: the GLP-1 RA in PMOS test case (Nov 2026) returned
   4 papers that the standard PCOS query missed. Record that number in the search log.
5. Other frequent renamings (check the same way; the list is never complete): NAFLD → MASLD; changed
   diagnostic criteria (new DSM, KDIGO or ADA versions). The aim is the checking habit, not a list.
6. **Check intervention and exposure terms too, not only the condition.** Ambiguous or changing
   terms → list all variants and exclude stray meanings with `NOT`. Verified example (Nov 2026):
   "robotic" + cardiology also returns robotic percutaneous coronary intervention (CorPath, R-One)
   and rehabilitation robots; 10 of the first 30 ClinicalTrials.gov trials were off topic. Add
   `NOT (percutaneous coronary[tiab] OR PCI[tiab] OR rehabilitation[tiab])` and read titles before
   counting. "Totally endoscopic" may or may not use a robot: separate the two when synthesising.
   AI: `"artificial intelligence" OR "machine learning" OR "deep learning" OR "computer vision" OR "neural network"`.
7. **AI, engineering or device topics**: much of the work is published only in IEEE Xplore, arXiv or
   engineering conferences (MICCAI) and not in PubMed. Search them if a tool is available; otherwise
   record the gap as a limitation.

## Step 2 – Regular vs research question; scoping search

### Regular vs research question test
(*Critical Thinking in Academic Research*; *Choosing & Using Sources*, ch. 1; change notes cite
Gruwell & Ewing 2023.) If a textbook, a current guideline or a recent systematic review (SR)
already answers the question directly, it is a lookup question, not a research question → move to
an angle that is not yet answered (the Vietnamese population, real-world application, a different
outcome). Without this test the skill could polish a question that is already answered.

### Scoping search (mandatory before the question is fixed)
Follow `${CLAUDE_PLUGIN_ROOT}/references/evidence-policy.md` (§Source order, §PubMed procedure,
§Consensus procedure, §OpenEvidence procedure).

**A review already exists** (`02_evidence/` holds a search log or evidence map, or
`literature-search` already ran in this session): do not search again from scratch. Reuse the
search log, evidence map and gap list. Run extra queries only for a **new question option** the
review did not cover (usually 1–3 queries: SR/MA of the last 5 years + Vietnam + ClinicalTrials.gov
for that angle), and write in section 3 of the output "reused the review results of <date>".

Otherwise, run:
1. **Consensus** `search`: the PICO/PECO question in English (exploration mode: "What are the main
   research areas and unanswered questions about {topic} in {population}?").
2. **PubMed** (`search_articles` or `search_lit.py search`), **for each question option**:
   (a) topic + `AND (systematic review[pt] OR meta-analysis[pt])`, limited to the last 5 years
   (**default**); (b) topic + `AND (Vietnam[Affiliation] OR Vietnam[Title/Abstract])`. Record
   `total_count`. Comparing several options usually takes 4–10 queries; that is normal.
3. **OpenEvidence** (if `oe_auth_status` is OK): `oe_ask` with model `sackett` (fallback `osler`),
   `wait_for_completion=false`, then `oe_article_wait`: "What is currently known about {topic} in
   {population}? What are the main unanswered questions and ongoing controversies?"

### Building the queries
- Each component P, I/E, C, O is one block. Usually **P + I/E (+ O)** is enough: C and O blocks
  often lose relevant papers; add them when there are more than 500 results (**default**).
- Each block: main MeSH term + free text (synonyms, abbreviations, brand names, British and American
  spellings). OR inside a block, AND between blocks, full brackets.
- Common PubMed tags:

| Tag | Meaning | Example |
|---|---|---|
| `[MeSH Terms]` | MeSH term (includes narrower terms) | `"Diabetes Mellitus, Type 2"[MeSH Terms]` |
| `[Majr]` | MeSH as major topic | `"Delirium"[Majr]` |
| `[tiab]` | Title and abstract | `delirium[tiab]` |
| `[ti]` + `[au]` + `[dp]` | Verify one paper (title words + first author + year) | `frailty[ti] AND overtreatment[ti] AND Smith[au] AND 2023[dp]` |
| `[pt]` | Publication type | `randomized controlled trial[pt]`, `meta-analysis[pt]`, `systematic review[pt]`, `practice guideline[pt]` |
| `[Affiliation]` | Author affiliation | `Vietnam[Affiliation]` |
| `[doi]` | Search by DOI | `10.1001/jama.2019.0234[doi]` |

- Do not use the `*` wildcard (the tool refuses it); list variants instead
  (`child OR children OR pediatric OR paediatric`).
- Worked example, postoperative delirium after cardiac surgery in older adults, dexmedetomidine:

```
("Delirium"[MeSH Terms] OR delirium[tiab] OR "acute confusion"[tiab])
AND ("Cardiac Surgical Procedures"[MeSH Terms] OR "cardiac surgery"[tiab] OR CABG[tiab] OR "coronary artery bypass"[tiab] OR "valve surgery"[tiab])
AND ("Dexmedetomidine"[MeSH Terms] OR dexmedetomidine[tiab] OR Precedex[tiab])
AND ("Aged"[MeSH Terms] OR elderly[tiab] OR "older adults"[tiab] OR geriatric[tiab])
```

  Variants to run: `... AND (systematic review[pt] OR meta-analysis[pt])`;
  `... AND randomized controlled trial[pt]`; drop the intervention block and add
  `AND (incidence[tiab] OR prevalence[tiab] OR "risk factors"[MeSH Terms])` for epidemiology and
  risk factors; `... AND (Vietnam[Affiliation] OR Vietnam[tiab] OR Vietnamese[tiab])`; Asia:
  `AND (Asia[MeSH Terms] OR China[Affiliation] OR Japan[Affiliation] OR Korea[Affiliation] OR Thailand[Affiliation])`.
- Consensus / OpenEvidence questions (English, specific):
  epidemiology "What is the incidence of postoperative delirium after cardiac surgery in patients
  aged 65 and older?"; effectiveness "Does perioperative dexmedetomidine reduce postoperative
  delirium after cardiac surgery compared with propofol or placebo?"; associated factors "What are
  the independent risk factors for delirium after cardiac surgery in older adults?"; measurement
  "Which delirium assessment tools are validated after cardiac surgery (CAM-ICU, 3D-CAM)?";
  guideline "What do current guidelines recommend for prevention of postoperative delirium in older
  surgical patients?"; gap "What are the main unanswered research questions about {topic}?"
- Search log, one row per query: # · date · source · query or question · filters · results · kept.
- When results look wrong (thresholds are **defaults**):

| Situation | What to do |
|---|---|
| More than 500 papers | Add the O or C block; use `[Majr]`; limit publication type or years |
| Fewer than 10 papers | Drop a less important block; add synonyms; check `query_translation` to see whether PubMed understood the query |
| Off-topic results | Read `query_translation`: PubMed may map to the wrong MeSH ("cardiac surgery" → also "thoracic surgery"); add `[tiab]` to force the exact words |

### Four situations
Conclude with one of four situations, with the evidence:

| Situation | Signs | What to do |
|---|---|---|
| Answered with confidence | Recent SR/MA, consistent results, guideline already recommends | Change angle: the Vietnamese population, real-world application (adherence, barriers), a different outcome, a subgroup |
| Evidence exists but conflicts or is low quality | SR concludes "more research needed", high I² | Keep the question, stress a tighter design |
| Exists abroad, not in Vietnam | Many international papers, few or no Vietnamese papers in PubMed | Reasonable for a thesis or institutional project; state why Vietnamese data are needed (epidemiology, health system, genetics, cost) |
| Almost nothing | Very few results | Re-check keywords (synonyms, MeSH) before concluding that the question is new |

- Most Vietnamese journals (Tạp chí Y học Việt Nam, Y học TP.HCM…) are not in PubMed: remind the
  user to search Google Scholar or the university library too, and never state "no one has done
  this in Vietnam". Write "not found in PubMed/Consensus".
- Cite only papers a tool returned in this session; papers from Consensus are verified through
  PubMed (`evidence-policy.md` §Verifying references) before entering the reference list. Every
  reference enters the project through `search_lit.py add` and is checked by `verify_refs.py`.
- Numbers (rates, thresholds, doses) come only from an abstract or full text that was actually read;
  never quote a number from a guideline whose content was not read.

## Step 2b – Surgical technique, device, robot, software or AI ideas: IDEAL stage
"Build or adopt X" is a **project**, not yet a research question. Place the idea at its stage of the
IDEAL framework (McCulloch 2009, Lancet, PMID 19782876; updated by Hirst 2019, Ann Surg, PMID
29697448, which adds Pre-IDEAL and the IDEAL-D variant for devices), then ask only the question that
fits the stage:

| Stage | Situation at the user's site | Fitting question / design |
|---|---|---|
| Pre-IDEAL (preclinical) | Device not yet used in humans; data (video, images, records) or animal or simulation models exist | Develop and validate a component (for example an AI model on existing data), simulation study, needs or readiness survey |
| 1 Idea | First few cases | Registered case report or case series, describe safety |
| 2a Development | Technique still being refined | Small prospective cohort, learning curve |
| 2b Exploration | Technique stable, several surgeons | Prospective cohort or registry, RCT preparation (define the intervention, outcome, sample size) |
| 3 Assessment | Ready for comparison | RCT (or an alternative design if randomisation is impossible) |
| 4 Long-term | In wide use | Registry, rare events, long-term outcomes |

Device or technique **not available at the site** → Feasible = 1 for every effectiveness
comparison; move to a Pre-IDEAL or component question that can be done now. Put "does the site
have, or will it soon have, the device?" in the confirmation list.

## Step 3 – Hypothesis first, then the framework
- An analytic research question must start from a **grounded hypothesis** (Nguyễn Văn Tuấn 2018).
  A descriptive survey without a hypothesis is still valuable for policy, but must say that this is
  its purpose. This prevents decorative, after-the-fact hypotheses and makes clear what the study
  can and cannot conclude.
- Then name the question type and its framework:

| Question type | Example | Framework | Usual design |
|---|---|---|---|
| Descriptive / prevalence | What is the prevalence of depression in dialysis patients? | **CoCoPop** (Condition, Context, Population) | Descriptive cross-sectional |
| Associated factors / cause / risk | Is smoking associated with …? | **PECO** (Population, Exposure, Comparator, Outcome) | Analytic cross-sectional, case-control, cohort |
| Intervention / treatment effect | Does drug A reduce … compared with B? | **PICO(T)** (+ Time) | RCT, before–after, non-randomised intervention, retrospective cohort |
| Diagnosis | How accurately does test X diagnose Y? | **PIRD** (Population, Index test, Reference standard, Diagnosis) | Diagnostic accuracy study (cross-sectional) |
| Prognosis | Which factors predict 30-day mortality? | **PFO** (Population, Prognostic Factor, Outcome) | Cohort |
| Experience / views | How do patients experience …? | **SPIDER** | Qualitative |

- Write each framework component in a table. Every component must be **measurable**: "older people"
  → "patients ≥ 60 years admitted to the cardiology ward"; "good outcome" → "proportion with
  HbA1c < 7% after 3 months".

## Step 4 – FINER and choosing an option
Propose **2–3 question options** (usually one ambitious, one manageable, one safe for a short
time frame). Score each:

| Criterion | Check | Score 1–5 |
|---|---|---|
| **F**easible | Enough patients in the time available? Outcome measurable with available means? Enough funds and staff? For retrospective data: are the needed variables recorded in the medical records? | |
| **I**nteresting | Do the user and the committee care? | |
| **N**ovel | Conclusion of step 2. Novelty by the data × idea matrix (Nguyễn Văn Tuấn 2018): new data + new idea; new data + old idea (for example replication in a Vietnamese population); old data + new idea or new interpretation are all novel; only "old data + old idea" is not. Novelty can lie in the measurement tool, the approach, an unstudied population, or the interpretation | |
| **E**thical | Risky intervention, vulnerable group, consent needed? **Equipoise**: if the literature or a guideline has shown that an intervention works, an RCT against placebo or no treatment in people who need treatment is unethical → compare with standard care, or move the question to an unanswered component (for example adding lifestyle change to a proven drug regimen) | |
| **R**elevant | Would the result change practice or policy, or open further research? Answer step 5 ("So what?"). Is the study still worth doing for every possible result, positive or negative? | |

- Score bands (**default**): 5 = clearly met, with evidence or figures; 3 = met if one assumption
  holds (write the assumption); 1 = hard to meet or a serious problem. Always write a one-sentence
  reason next to each score.
- Feasibility in numbers: patients per month × months of data collection, compared with a **rough**
  sample size (screening only; the formal calculation is done with `sample-size-sap`). Rough
  screening figures (**defaults**):
  - one proportion: ~385 (p unknown, d = 0.05); ~150–250 if p ≈ 10–20% and d = 0.05;
  - associated factors by logistic regression: ≈ 10 × number of variables in the model / outcome
    rate (for example 8 variables, outcome 25% → ~320);
  - two groups, outcome rates 15 percentage points apart (30% vs 15%): ~120 per group;
  - qualitative designs: step 7.
  - Quick calculator: `python "${CLAUDE_PLUGIN_ROOT}/scripts/samplesize.py" --help` (no scipy needed).
- If the user does not know patients per month: assume conservatively, say so, and put "confirm
  patients per month with the planning department (phòng Kế hoạch tổng hợp)" in the confirmation list.
- Feasible ≤ 2 (**default**) → do not recommend that option.
- Recommend **one** option, with a short reason.

## Step 5 – Relevant: "So what?"
"Has practical significance" is not an answer. Answer **"So what?" ("Thì sao?")** and name the
story (Ogden 2019, ch. 9): **AND** (replication in a new population or setting), **BUT** (challenges
the literature) or **HOW** (explains a mechanism or process). The story type forces the user to
state the contribution.

## Step 6 – Assumptions
List the assumptions behind the chosen option (RED model: recognise assumptions → evaluate
arguments → draw conclusions): patient numbers, ability to measure the outcome, available data,
expected effect size, acceptance by participants. Thesis projects usually fail on an untested
assumption (recruitment, measurability). Mark the riskiest assumption and put it in the
confirmation list. Remind the user to discuss the idea with their supervisor or an experienced
person in the specialty before fixing it (Tuấn 2018).

## Step 7 – Qualitative questions and the "n = 30" myth
- Qualitative (in-depth interviews, focus groups): usually 12–20 interviews (shared **default**, see
  `judgement-defaults.md`) or 4–8 groups (**default**) for a fairly homogeneous population, more when
  there are several strata; the formal argument uses information power (Hennink & Kaiser 2022), done
  with `sample-size-sap`.
- There is no universal minimum sample size: "30 is enough" is a myth (Tuấn 2018). n depends on the
  design, outcome type, effect size, variability, α and power.

## Step 8 – Question, objectives, hypothesis, outcomes
**Research question**: one sentence containing every framework component, the time and the place.

**Objectives**: 1 general objective + 2–3 specific objectives (**default**), each starting with a
measurable verb that matches the design:

| Design | Fitting verbs | Do not use |
|---|---|---|
| Descriptive | Describe, Determine the proportion, Estimate ("Mô tả", "Xác định tỷ lệ", "Ước tính") | Evaluate effectiveness, Prove ("Đánh giá hiệu quả", "Chứng minh") |
| Analytic cross-sectional / case-control | Determine the association, Analyse associated factors ("Xác định mối liên quan", "Phân tích một số yếu tố liên quan") | Determine causes, risk factors (cross-sectional) ("Xác định nguyên nhân", "yếu tố nguy cơ") |
| Cohort | Determine risk, Compare incidence, Determine prognostic factors ("Xác định nguy cơ", "So sánh tỷ lệ mới mắc", "Xác định yếu tố tiên lượng") | |
| Intervention | Evaluate effectiveness, Compare effectiveness, Evaluate safety ("Đánh giá hiệu quả", "So sánh hiệu quả", "Đánh giá tính an toàn") | |
| Diagnosis | Determine sensitivity, specificity, diagnostic value ("Xác định độ nhạy, độ đặc hiệu, giá trị chẩn đoán") | |

Each specific objective must be answerable by **one table or one analysis** in the results.
Objective 1 is usually descriptive, objective 2 usually analytic.

**Hypothesis**: only for analytic, intervention or diagnostic questions with a comparison. A purely
descriptive study writes "Descriptive study; no hypothesis tested" ("Nghiên cứu mô tả, không kiểm
định giả thuyết"). Each hypothesis has:
- a verbal form: "patients on A have a lower rate of … than patients on B";
- H₀ / H₁ in symbols (p₁ = p₂ / p₁ ≠ p₂; or μ, HR, OR);
- for intervention questions: superiority / non-inferiority / equivalence (omit this line for
  observational questions: association, prognosis, diagnosis); in every case one- or two-sided
  (two-sided by default);
- the expected direction and size if the step 2 literature gives figures (with citation): this is an
  input for the sample size.
A hypothesis must be grounded in the literature and testable with the data that will be collected.

**Outcome**: exactly one primary outcome (definition, measurement tool, time point) + secondary outcomes.

## Step 9 – Title
Vietnamese convention: `{Verb/content} {outcome/characteristic} ở {population} tại {site} {year}`,
for example "Tỷ lệ và một số yếu tố liên quan đến sảng sau mổ ở người bệnh ≥ 65 tuổi phẫu thuật tim
mở tại Bệnh viện X năm 2026–2027". The title contains no word the design cannot answer ("hiệu quả"
/ effectiveness in a descriptive study, "nguyên nhân" / cause in a cross-sectional study). Offer
2–3 options.

## Output: `01_question/question.md`
Written in `project.yaml → language.output`. Sections, in this order:
1. **Brief context** (2–3 lines, with the assumptions if any).
2. **Question type + framework table** (PICO/PECO/…).
3. **Scoping results**: 3–6 bullets with citations + which of the four situations applies + a short
   search log (source, query, number of results).
4. **FINER table** for the 2–3 options + recommendation.
5. **Final version**: title, research question, general and specific objectives, hypothesis (or the
   no-hypothesis note), primary/secondary outcomes, suggested design.
6. **Needs your confirmation** (at most 3 items, **default**).
7. **References**: cite as `[@id]` from `ledgers/references.json`; the numbered Vancouver list is
   rendered by `cite_render.py`, and every entry has a PMID or DOI.
8. **Next steps**: full literature review with appraisal of each paper (`literature-search`, which
   uses `critical-appraisal`) → protocol (`protocol-design`) → sample size (`sample-size-sap`).

Later skills read this file again. If no project exists (the user declined setup), give the
answer in chat and ask in one line whether to save it. If the author wants a Word file, use a docx
skill if one is installed (the plugin's own Word export is planned).

## Common errors

| Error | Fix |
|---|---|
| Topic too broad ("nghiên cứu về đái tháo đường") | Force it through the framework: specific population + one measurable outcome + place + time |
| Objective "evaluate effectiveness" in a descriptive cross-sectional design | Change the verb, or change the design if the user really wants to know effectiveness |
| Causal conclusion ("risk factor") from a cross-sectional study | Use "associated factor" ("yếu tố liên quan") |
| Intervention question without a comparison group | Add a comparator (standard care, pre-intervention, historical controls) and state the limitation |
| 4–5 objectives, each with its own main outcome | Keep one primary outcome; the rest are secondary |
| Hypothesis for a descriptive study | Write "no hypothesis tested" |
| Retrospective topic chosen but the key variable is not in the records | Check sample records first; if absent, go prospective or change the variable |
| "No research in Vietnam" concluded from PubMed alone | Write "not found in PubMed/Consensus"; remind the user to search Vietnamese journals |
| Citing a paper from memory | Cite only papers with a PMID/DOI returned by a tool in this session |
| Asking the user one question at a time | Put every missing item into one question |
| Searching only the old name of a condition, missing papers that use the new name | Step 2.0: check renaming and redefinition; use old and new names |
| "Phase III RCT" for a non-drug intervention (lifestyle, education, surgery) | Phase labels are for drugs only; write "confirmatory RCT" and register as "Phase: Not Applicable" (details in `protocol-design`) |
| Placebo RCT for a regimen already proven effective | Check equipoise (FINER-E); change the comparison or the question |
| RCT comparing a device or robot the site does not have | Step 2b: place the IDEAL stage, ask the stage's question |
| Question already answered by a guideline or textbook | Run the regular vs research question test; move to an unanswered angle |
| "Relevant" written only as "has practical significance" | Answer "So what?" and name the story: AND / BUT / HOW |
| Decorative hypothesis written for form's sake | The hypothesis must be grounded in the literature and testable with the data that will be collected |

## Basis
- Nguyễn Văn Tuấn 2018: chapters on the research question, on ideas and on novelty (hypothesis
  first, four approach elements, data × idea matrix, assumptions and mentor discussion, "n = 30" myth).
- *Critical Thinking in Academic Research*; *Choosing & Using Sources*, ch. 1 (change notes: Gruwell
  & Ewing 2023): regular vs research question.
- Ogden 2019, ch. 9 (course slide 65): "So what?" and the AND / BUT / HOW story.
- RED model (course slide 12): assumptions.
- Hennink & Kaiser 2022: qualitative sample size, information power.
- IDEAL: McCulloch 2009, Lancet, PMID 19782876; Hirst 2019, Ann Surg, PMID 29697448.
- Renamed-condition regression case: PLoS Med 2026 meta-analysis, PMID 42776991 (skill text and
  change notes). Change-note reference: Olalere O, Koh MD, Crabb K, et al. Lifestyle interventions in
  polyendocrine metabolic ovarian syndrome: SR and MA. PLoS Med. 2026;23:e1004887.
  doi:10.1371/journal.pmed.1004887.
