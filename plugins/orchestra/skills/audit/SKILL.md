---
name: audit
description: 'Audit the thesis or manuscript before export: citations, numbers, statistics, literature, consistency, prose, guideline, captions, identifiers and reviews in one check (kiểm tra trước khi xuất bản).'
disable-model-invocation: true
---

# /orchestra:audit

1. From the project folder run `python "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" . [thesis|manuscript]` with the
   deliverable the user named (none = every deliverable with drafts). Add `--online` only when the user asks to
   re-check references against PubMed/Crossref. Exit 2 → show the stderr text and stop.
2. Read `reviews/audit.md`. In the user's language, explain each block: what it means, where (file:line), and the
   fix, grouped by code; then the warns in one short list.
   - `E-REF`: a citation missing, retracted or unverified → `verify_refs.py --write`, a verified replacement, or
     the author's own document (`search_lit.py add-manual`); never edit a status by hand.
   - `E-NUM`: a typed number → its `{{R-…}}` placeholder, or `<!-- not-a-result: … -->` for a non-result.
   - `E-STAT`: an undeclared post-hoc or deviation, or an unlabelled one → `decisions.md` line or label.
   - `E-LIT`: Chương 1 / Introduction written paper by paper → rewrite by theme (`literature-review`).
   - `E-CONS`: two places disagree → which source is right (ledger first).
   - `P00`: prose density → `prose-humanizer`.
   - `E-RG`: guideline item absent or misquoted → add it, or record why it does not apply.
   - `E-FMT`: section missing, caption numbering, image, or an unfilled `[[AUTHOR: …]]`.
   - `E-PHI`: a possible identifier → remove it; never print it back.
   - `E-REV`: a reviewer report missing → rerun that agent on the current drafts.
3. Never fix silently: do not edit drafts, ledgers, `reviews/audit.json` or `gates/state.json`; never change a
   reference status; never open G4. Propose the fixes and ask which to apply.
4. 0 blocks: tell the author that they may open G4 themselves —
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/gate.py" open . G4 --by "<name>"` — and that
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/assemble.py" . <deliverable> --final` then writes `out/<deliverable>.docx`.
   Any edit to a draft or ledger after the audit closes G4 again.
