---
name: prose-humanizer
description: 'Use when academic prose sounds machine-written and must be rewritten naturally without changing what it asserts. Triggers: "văn máy", "giọng AI", "viết lại cho tự nhiên", "humanize", "sounds like AI", "AI-sounding", "chỉnh văn", "bớt sáo rỗng", "rewrite naturally".'
---

# Prose humanizer

## 1. Order
Run after the last content revision and before the format pass (`build_docx.py`). A later content edit
means running this again.

## 2. Measure first
`python "${CLAUDE_PLUGIN_ROOT}/scripts/lint_prose.py" <file>` (add `--lang vi|en` if auto-detect is wrong).
Catalog: `${CLAUDE_PLUGIN_ROOT}/references/writing/prose-patterns.md`. A hit is a pattern, not a verdict.

## 3. Rewrite
Go paragraph by paragraph and keep what the catalog excludes: passive voice in Methods, hedges that
observational designs require, guideline wording, standard headings, abbreviations. Say the point
plainly; add no claim. Write the whole rewrite to `reviews/tmp/<stem>.humanized.md`, same paragraph
count and order. Never touch numbers, `{{R-…}}` placeholders, citation keys, derived or not-a-result
comments, or `ledgers/claims.json`.

## 4. Verify
`python "${CLAUDE_PLUGIN_ROOT}/scripts/invariants.py" <file> reviews/tmp/<stem>.humanized.md --merge <file>`
A paragraph that changes numbers, citations or placeholders, or loses a hedge, is reverted in the merge
result. Exit 1 lists them: report each reverted paragraph and why. The merge result replaces the file
only after the author agrees, or directly under the "just do it" rule. Keep the original until then.

## 5. Measure after
Run `lint_prose.py` again and report hits before and after. Hits the author wants to keep stay.

## 6. Disclosure
Humanizing does not replace disclosure of AI use. Remind the author to follow the venue's or
institution's policy.

## 7. Hand-off
Report: file, hits before and after, reverted paragraphs. The author reads the merged text before it is
final.

## 8. "Just do it" rule
Apply the merge directly, open the report with an **Assumptions / Giả định** line, record it in
`decisions.md`.

## 9. Workflow
`${CLAUDE_PLUGIN_ROOT}/references/workflows/prose-humanizer.md`
