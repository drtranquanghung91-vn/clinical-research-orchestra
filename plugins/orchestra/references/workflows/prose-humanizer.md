# Prose humanizer: full workflow

Catalog and exceptions: `${CLAUDE_PLUGIN_ROOT}/references/writing/prose-patterns.md`. Thresholds:
`${CLAUDE_PLUGIN_ROOT}/references/judgement-defaults.md` ("Prose pattern density"). Scripts are in
`${CLAUDE_PLUGIN_ROOT}/scripts/`; run them from the project folder.

## 1. When
After the last content revision, before the format pass. Not on `claims.json`, ledgers, references or
tables of numbers.

## 2. Before
`python "${CLAUDE_PLUGIN_ROOT}/scripts/lint_prose.py" <file> --json` and note hits per paragraph (a
paragraph is flagged above 3 per 100 words; a document blocks above 2 per 100 words). Work on the flagged
paragraphs first, but read the whole file for tone.

## 3. Rewrite rules
- Paragraph by paragraph, same order, same paragraph count; do not merge or split paragraphs.
- Keep: passive voice in Methods; hedges required by observational or exploratory work (the hedge count
  may not fall); guideline wording quoted as written; standard headings; abbreviations; Vietnamese
  academic register in a Vietnamese file.
- Cut: stock openers and closers, intensifiers, contrasts that argue with nobody, forced triads, bold
  labels in prose, chatbot residue. State the fact. Vary sentence length. Add no claim and no source.
- Never change: numbers, `{{R-…}}` placeholders, `[@key]` citations, `<!-- derived: -->` and
  `<!-- not-a-result: -->` comments, `ledgers/claims.json`.
- Write the whole text to `reviews/tmp/<stem>.humanized.md`. Do not overwrite the original.

## 4. Verify
`python "${CLAUDE_PLUGIN_ROOT}/scripts/invariants.py" <file> reviews/tmp/<stem>.humanized.md --merge <file>`
Exit 0: the rewrite is safe. Exit 1: INV blocks name paragraphs whose numbers, citations, placeholders,
derived comments or hedge count changed; with `--merge` each such paragraph is replaced by its original.
Exit 2: usage or I/O error. A changed paragraph count is one "paragraph structure changed" block and the
merge result is the original.
Report every reverted paragraph with its reason, and offer a second attempt on those paragraphs.
The merge result replaces the file only after the author agrees, or directly under the "just do it" rule.

## 5. After
`lint_prose.py` on the merged file; report hits before and after. Hits the author keeps are fine. Then
re-run the checks that apply to the document: `render_results.py` and `check_numbers.py` for results
text, `consistency_audit.py` for the project.

## 6. Disclosure
Humanizing changes style, not authorship. It does not replace the disclosure of AI use that the journal,
institution or ethics body requires. Say so in the hand-off.

## 7. Hand-off
File, hits before and after, reverted paragraphs, checks run. The author reads the merged text.
