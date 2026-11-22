# Institution thesis template

An institution template is your institution's sample thesis as a Word file (`.docx`). Save it in the project,
for example as `<project>/06_writing/template.docx`, and point to it in `project.yaml`:

```yaml
institution:
  template: "06_writing/template.docx"
```

You can also pass it once with `build_docx.py ... --template FILE.docx`.

## What is taken

- All of `word/styles.xml`, verbatim.
- Page size and margins, from the last section's `w:sectPr` in the template.

## What is not taken

Headers, the cover page, existing content, numbering definitions and images stay behind. The content always
comes from the Markdown files. Our centred page-number footer is added to every document.

## Style ids the Markdown uses

`Heading1` to `Heading4`, `Caption` (table captions), `FigureCaption` and `Figure` (images), `TableNote`,
`ListParagraph`. A template style with the same id wins; an id the template lacks is added from the defaults.
Word style ids stay English (`Heading1`) whatever the display language of the template.

## Lists of tables and figures

In Word: References > Insert Table of Figures > Options, then pick the style `caption` (tables) or
`figure caption` (figures). A `{TOC}` line in the Markdown gives the table of contents; Word fills it when
the file opens: Word asks whether to update the fields because of the table of contents; answer Yes.

## Without a template

Defaults are Times New Roman 13 pt, 1.5 line spacing, margins 2/2/3/2 cm (top, bottom, left, right), A4.
Change them under `docx:` in `project.yaml`.

## Limitation

Institution-specific reference ordering is not supported (spec section 2).
