---
name: appraise
description: 'Appraise one research paper (PDF, PMID or DOI) for journal club or for the project''s evidence table (thẩm định một bài báo).'
disable-model-invocation: true
---

Use the Skill tool with `critical-appraisal` on the paper the user gives. If a project folder exists,
first add the paper (a PMID or DOI via `search_lit.py add <project> <id>`; a PDF with neither via
`add-manual` with the PDF path as `--seen-in`) and verify it; otherwise run in standalone journal-club mode.
Reply in the user's language with the three-question verdict first.
