# Protocol template (Vietnamese structure) mapped to SPIRIT

Methods content by Amelia Le (co-author), adapted for clinical-research-orchestra. Source:
`protocol-design-vi` v3 (20 Nov 2026), `reference/protocol-template.md`, and the 18 Nov change notes.

Use this frame for a thesis protocol (đề cương luận văn) or an institutional project (đề tài cơ sở).
The SPIRIT column helps when converting to an English protocol or a trial registration.

**The item numbers in the SPIRIT column are SPIRIT 2013 numbers.** SPIRIT 2025 has 34 items and is
renumbered. The full item-by-item 2013 → 2025 map has **not been verified**; a wrong map would be worse
than a clearly flagged old one, so the column is left as 2013 on purpose. When submitting to a registry
or journal, check against the 2025 checklist itself and add the 2025 items: open science
(registration, public protocol and SAP, data sharing), patient and public involvement (PPI), harms
assessment, and description of the intervention and comparator (TIDieR). Trial reports use CONSORT 2025
(30 items) with the same additions.

| Vietnamese protocol section | Content | SPIRIT (2013 numbering) |
|---|---|---|
| Tên đề tài (title) | Follow the title rules of the `research-question` skill | 1 |
| ĐẶT VẤN ĐỀ (introduction) | Burden of the problem → what is known → gap → why here → objectives (listed) | 6a, 7 |
| CHƯƠNG 1. TỔNG QUAN (literature review) | From `literature-search` and `literature-review` | 6a |
| CHƯƠNG 2. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP (participants and methods) | | |
| 2.1. Đối tượng nghiên cứu (participants) | 2.1.1 Inclusion criteria; 2.1.2 Exclusion criteria; (2.1.3 Stopping or withdrawal criteria) | 10 |
| 2.2. Thời gian và địa điểm (time and place) | Data collection period, site | 9 |
| 2.3. Phương pháp nghiên cứu (methods) | 2.3.1 Design; 2.3.2 Sample size (from `sample-size-sap`); 2.3.3 Sampling method (+ randomisation, allocation concealment, blinding if interventional) | 8, 14, 16, 17 |
| 2.4. Can thiệp (intervention, if any) | Enough detail to replicate: drug, dose, duration, who delivers it; concomitant treatment allowed or not | 11 |
| 2.5. Biến số và chỉ số nghiên cứu (variables and indicators) | Variables table by objective; outcome definitions | 12 |
| 2.6. Công cụ và quy trình thu thập số liệu (tools and data collection) | Form or CRF, scales, devices, data collectors, training, study flow diagram, collection schedule | 13, 18 |
| 2.7. Sai số và biện pháp khống chế (bias and its control) | Bias and confounding table | — |
| 2.8. Xử lý và phân tích số liệu (data management and analysis) | Software, descriptive statistics, tests, multivariable models, missing data (detailed SAP from `sample-size-sap`) | 20 |
| 2.9. Đạo đức nghiên cứu (ethics) | Ethics committee, consent, confidentiality, risk–benefit, compensation (detail at the governance step, `ethics-and-crf`) | 24–27, 32 |
| CHƯƠNG 3. DỰ KIẾN KẾT QUẢ (expected results) | Dummy tables for each objective | — |
| CHƯƠNG 4. DỰ KIẾN BÀN LUẬN (expected discussion) | By objective | — |
| DỰ KIẾN KẾT LUẬN, KIẾN NGHỊ (expected conclusions, recommendations) | By objective | — |
| KẾ HOẠCH, KINH PHÍ (plan, budget) | Monthly Gantt chart; budget | — |
| TÀI LIỆU THAM KHẢO, PHỤ LỤC (references, appendices) | Vancouver; data collection form, consent form | 32 |

## Variables table (example)

The full table is written to `03_protocol/variables.md`; it is the input for the CRF and the data
dictionary later.

| Objective | Variable | Definition / how measured | Type | Values / unit | Collection method | Role |
|---|---|---|---|---|---|---|
| O1 | Age | Age in completed years on the admission date | Continuous | years | Medical record | Descriptive / confounder |
| O1 | Age group | 65–74; 75–84; ≥ 85 | Ordinal | 3 groups | Derived from age | Descriptive |
| O1 | Postoperative delirium | CAM-ICU positive at least once in the 5 days after surgery, assessed twice daily | Binary | Yes / No | Direct assessment | Primary outcome |
| O2 | Dexmedetomidine use | Infusion during surgery or ≤ 24 h after surgery | Binary | Yes / No | Anaesthesia record | Exposure |

Roles: primary outcome / secondary outcome / exposure–intervention / confounder / effect modifier /
mediator / descriptive. Types: continuous / binary / categorical / ordinal / time to event.

## Dummy tables (examples)

At least one table for each objective. Leave the numbers empty and name the statistic to be reported.

**Table 3.1. General characteristics of participants (n = …)**

| Characteristic | Group A (n = …) | Group B (n = …) | Total (n = …) |
|---|---|---|---|
| Age, mean ± SD | | | |
| Male, n (%) | | | |

(RCT: no p-values for the baseline table — CONSORT.)

**Table 3.x. Factors associated with {outcome} – multivariable logistic regression**

| Factor | Crude OR (95% CI) | Adjusted OR (95% CI) | p |
|---|---|---|---|

## Study flow diagram (text example)

```
Patients meeting inclusion criteria (expected n)
  └─ Excluded (reason, n)
      └─ Consented
          ├─ Group A ─ measure T0 ─ intervention ─ measure T1 ─ measure T2
          └─ Group B ─ measure T0 ─ control      ─ measure T1 ─ measure T2
              └─ Analysis (ITT / PP)
```

## References given in the source

These are the citations as Amelia Le recorded them; before either enters a project's reference list it
goes through `search_lit.py add` and `verify_refs.py`
(`${CLAUDE_PLUGIN_ROOT}/references/evidence-policy.md`).

1. Chan AW, Boutron I, Hopewell S, et al. SPIRIT 2025 statement. BMJ. 2025;389:e081477.
   doi:10.1136/bmj-2024-081477. PMID: 40294953.
2. Hopewell S, Chan AW, Collins GS, et al. CONSORT 2025 statement. BMJ. 2025;389:e081123.
   doi:10.1136/bmj-2024-081123. PMID: 40228833.
