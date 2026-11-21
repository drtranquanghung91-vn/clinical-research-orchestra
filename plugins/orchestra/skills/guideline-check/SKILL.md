---
name: guideline-check
description: 'Use when the user asks which clinical or reporting guidelines apply to a study, whether a cited guideline is still current, or needs the reporting checklist for their design; also before a protocol or manuscript is finalised. Triggers: "guideline mới nhất", "cập nhật guideline", "hướng dẫn điều trị mới nhất", "khuyến cáo hiện hành", "checklist báo cáo", "dùng checklist nào", "CONSORT", "STROBE", "PRISMA", "STARD", "TRIPOD", "CARE", "SPIRIT", "reporting guideline", "is this guideline current", "which checklist".'
---

# Guideline check

Requested by Amelia Le: keep the guidelines a study relies on current.

## Two kinds of guideline
- **Clinical guidelines** used for definitions, diagnostic criteria and comparators (for example ADA,
  KDIGO, ESC, Bộ Y tế). Find the newest version through the evidence sources in
  `${CLAUDE_PLUGIN_ROOT}/references/evidence-policy.md`; record issuing body, year, version, DOI or
  official URL, and the date you checked.
- **Reporting guidelines** chosen from `project.yaml → design` using
  `${CLAUDE_PLUGIN_ROOT}/references/reporting-guidelines/index.md`; citations come from
  `guidelines.json` (already verified).

## Steps
1. Read `project.yaml`, `01_question/question.md`, `03_protocol/protocol.md` if present.
2. List every guideline the project cites or should cite. For each clinical guideline, search for a
   newer version or a published update; never state "latest" without a lookup made today.
3. Flag outdated guidelines anywhere in the project (`grep` the project for the guideline name and year).
4. Write `02_evidence/guidelines.md` in `language.output`: table `Guideline | Kind | Version used |
   Current version | Checked on | Action`.
5. Add clinical-guideline papers to the ledger with `search_lit.py add` and verify them.
6. If a reporting-guideline item mapping is uncertain (for example SPIRIT 2013 → 2025 numbering),
   say so in the table instead of guessing.
