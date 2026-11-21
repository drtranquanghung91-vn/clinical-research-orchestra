# Poster rules

Used by `research-poster`. Format of the spec: `${CLAUDE_PLUGIN_ROOT}/references/presenting/poster-spec.md`.

## IVLBCL rules (from the poster session)
- Label semantics are the same on every figure: filled marker or bar = positive or event, outlined =
  negative; one colour per group.
- Lab values are tables with arrows (high, low). Criteria are check lists.
- No decorative cards, gradients, shadows or rounded boxes.
- Every number comes from the results ledger by placeholder; spell-check the terminology.
- Look at the PNG of every layout before sending: nothing cut off, text readable from 1.5 m, layouts
  visibly different.

## Key-message test
Write one sentence. Read it to a colleague who walks past; a day later they should be able to say it
back. It states the finding with its estimate and CI, names the population, and uses no causal verb for an
observational design. Two sentences, or a sentence that needs a table to make sense, fails the test.

## Preflight findings (E-PRINT)
`poster_preflight.py` blocks on: wrong page size (poster plus bleed, 1 mm tolerance), an image under
100 dpi at placed size, a font not embedded, a requested bleed missing, a box that overflows. Under 150 dpi
is a warning. Fixes: supply a larger source image, place the image smaller, enlarge the box; never
upscale a raster to raise its dpi.

## Print note (give to the author)
- Print at 100 % (no "fit to page"), from the PDF, which embeds the fonts.
- Request the bleed stated in `poster.json` (default 3 mm) and crop marks if the printer offers them.
- If the printer rebuilds from the PPTX instead, the printer needs the font installed.
- Confirm paper (matt or satin, about 150-200 g) and the exact size with the printer before sending.
- Print an A4 proof, and check the real print from 1.5 m before the session.
