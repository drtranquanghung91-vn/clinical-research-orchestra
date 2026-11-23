#!/usr/bin/env python3
"""Create a research project folder from the orchestra template.

  python init_project.py <dest> --title "..." --type thesis-masters --design cohort --output-lang vi --chat-lang vi

Types case-report, systematic-review and review (with --design scoping-review or narrative-review) also create
their folders (01_case/ or 02_evidence/sr/, 04_data/sr/, 05_analysis/meta/, and 06_writing/case-report/ or
06_writing/review/). The pairing holds both ways: design case-report needs type case-report, systematic-review needs
type systematic-review, scoping-review and narrative-review need type review.

Every project gets 03_protocol/ethics/; types that publish (manuscript, case-report, systematic-review, review) also
get 08_submission/ and 09_revision/.

Exit codes: 0 = created; 2 = bad arguments, destination already has project.yaml, or cannot write.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "project"
TYPES = ("thesis-ckii", "thesis-masters", "thesis-phd", "de-tai-co-so", "manuscript", "review",
         "systematic-review", "case-report", "poster-only")
GUIDELINE_BY_DESIGN = {
    "rct": "CONSORT-2025", "cohort": "STROBE", "case-control": "STROBE", "cross-sectional": "STROBE",
    "diagnostic-accuracy": "STARD-2015", "prediction-model": "TRIPOD+AI", "qualitative": "SRQR",
    "mixed": "GRAMMS", "case-report": "CARE", "systematic-review": "PRISMA-2020",
    "scoping-review": "PRISMA-ScR", "narrative-review": "SANRA",
}
DESIGNS = tuple(GUIDELINE_BY_DESIGN)
TYPE_DESIGNS = {"case-report": ("case-report",), "systematic-review": ("systematic-review",),
                "review": ("scoping-review", "narrative-review")}
FOLDERS = {"case-report": ("01_case", "06_writing/case-report"),
           "systematic-review": ("02_evidence/sr", "04_data/sr", "05_analysis/meta", "06_writing/review"),
           "scoping-review": ("02_evidence/sr", "04_data/sr", "05_analysis/meta", "06_writing/review"),
           "narrative-review": ("06_writing/review",)}
LANGS = ("vi", "en")
PUBLISHING = ("manuscript", "case-report", "systematic-review", "review")

YAML = """title: "{title}"
type: {ptype}
design: {design}
reporting_guideline: {guideline}
language:
  chat: {chat}
  output: {output}
institution:
  name: ""
  city: ""
  template: ""
citation_style: {style}
target:
  journal: ""
  journal_style: null
  conference: ""
  word_limit: null
  text_words: null
  poster_size_cm: [90, 120]
evidence_sources: [openevidence, pubmed, europepmc, crossref]
docx:
  font: "Times New Roman"
  size_pt: 13
  line_spacing: 1.5
  margins_cm: [2, 2, 3, 2]
review:
  reviewers: []
  registration: null
tools:
  rscript: null
"""


def create(dest: Path, title: str, ptype: str, design: str, output_lang: str, chat_lang: str) -> Path:
    if ptype not in TYPES:
        raise ValueError(f"type must be one of {TYPES}")
    if design not in DESIGNS:
        raise ValueError(f"design must be one of {DESIGNS}")
    if ptype in TYPE_DESIGNS and design not in TYPE_DESIGNS[ptype]:
        raise ValueError(f"type {ptype} needs --design {' or '.join(TYPE_DESIGNS[ptype])}")
    owner = next((t for t, ds in TYPE_DESIGNS.items() if design in ds), None)
    if owner is not None and ptype != owner:     # the other direction: these designs belong to one type
        raise ValueError(f"design {design} needs --type {owner}")
    if output_lang not in LANGS or chat_lang not in LANGS:
        raise ValueError("languages must be 'vi' or 'en'")
    dest = Path(dest)
    if (dest / "project.yaml").exists():
        raise FileExistsError(f"{dest} already has project.yaml")
    shutil.copytree(TEMPLATE, dest, dirs_exist_ok=True)
    style = "vn-thesis" if ptype.startswith("thesis") or ptype == "de-tai-co-so" else "vancouver"
    safe_title = title.replace("\n", " ").replace("\\", "\\\\").replace('"', '\\"').strip()
    (dest / "project.yaml").write_text(YAML.format(
        title=safe_title, ptype=ptype, design=design, guideline=GUIDELINE_BY_DESIGN[design],
        chat=chat_lang, output=output_lang, style=style), encoding="utf-8")
    for rel in (FOLDERS.get(design, ()) if ptype in TYPE_DESIGNS else ()):
        (dest / rel).mkdir(parents=True, exist_ok=True)
    (dest / "03_protocol" / "ethics").mkdir(parents=True, exist_ok=True)
    if ptype in PUBLISHING:
        for rel in ("08_submission", "09_revision"):
            (dest / rel).mkdir(parents=True, exist_ok=True)
    return dest


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dest")
    ap.add_argument("--title", required=True)
    ap.add_argument("--type", dest="ptype", required=True, choices=TYPES)
    ap.add_argument("--design", required=True, choices=DESIGNS)
    ap.add_argument("--output-lang", default="vi", choices=LANGS)
    ap.add_argument("--chat-lang", default="vi", choices=LANGS)
    a = ap.parse_args(argv)
    try:
        d = create(Path(a.dest), a.title, a.ptype, a.design, a.output_lang, a.chat_lang)
    except (OSError, ValueError) as e:  # existing project, destination is a file, no permission, ...
        print(f"init_project: {e}", file=sys.stderr)
        return 2
    print(f"created {d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
