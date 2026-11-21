# Defence deck rules

Used by `defense-prep`. The deck is the last place a number can go wrong; the thesis is the first.

## Lessons from a real thesis defence (MZL)

Three defects reached the final session because slides were planned before the text was audited.
1. **Unrounded sample size.** The thesis said "≈26" where the formula gave 26.65. A sample size is always
   rounded up: 27. `consistency_audit.py` blocks an approximate or decimal sample size.
2. **Study end date.** The abstract and the methods gave different end dates. Date ranges must match in
   every file; a follow-up window that deliberately shares a start needs `<!-- cons-ok: reason -->`.
3. **85% vs 86,3%.** One rate, two roundings. Take the value from the ledger placeholder everywhere.

Fix these in the thesis, with the author, before any slide exists; then slides inherit correct numbers.

## Slide rules

- **Action title.** A sentence that states the finding ("Biến chứng gặp ở {{R-A0-001}} bệnh nhân"), not a
  topic ("Kết quả"). `lint_prose.py --slides` flags topic titles (S17).
- **One message per slide.** If a slide needs "and" twice, split it.
- **Time budget.** 18-20 minutes unless the committee says otherwise; about one slide per minute, so 16-20
  slides plus backup. Write the minutes in each slide's notes. Never read the slide; the notes hold the
  spoken line and the number to say.
- **Numbers as placeholders.** `{{R-…}}` in titles, bullets, tables and notes. A typed number is a defect.
- **Native charts.** Bar, column, line, Kaplan-Meier and forest are native PowerPoint charts from
  `F<n>.data.json`, editable by the candidate on the day. A picture only when no native kind fits (PNG, 300 dpi).
- **Kaplan-Meier.** Redrawn from the de-identified CSV by `figures.py`, never traced from a picture. The
  at-risk table sits under the curve as a native table, and the source note "Vẽ lại từ <file>" stays.
- **Do not narrate the picture.** "Biểu đồ này cho thấy" is S20; say what to see.
- **Hedging.** No "chứng minh", "proves", "significantly better" without the interval; no causal verbs for
  observational designs; post-hoc results labelled exploratory on the slide.
- **Closing.** The conclusion slide answers each objective in order; the recommendations follow from the
  conclusions only.
- **Backup slides.** After the closing slide: sample size derivation, definitions and cut-offs with their
  source, sensitivity analyses, missing data, deviations. The weak points in `reviews/committee-defense.md`
  decide which ones.

## Institution template

The faculty template is matched, not imitated: set `template` (and `layouts`) in the deck spec, so masters,
logo, fonts and colours stay the institution's. Put the file in `07_present/theme/`. Do not restyle it with
`styles` unless its sample slides were formatted by hand. If the faculty requires a title-slide wording
(school, supervisor, academic year), copy it exactly from the template or the faculty's instructions.
