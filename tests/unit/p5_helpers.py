"""Shared fixtures for the P5 unit tests. Everything here is fictional."""
from __future__ import annotations

import re
from pathlib import Path

import _paths  # noqa: F401
import gate
import init_project

PROTOCOL = """# Review protocol (fictional, for unit tests)

## Full-text exclusion reasons
- wrong population
- wrong intervention
- wrong outcome
- wrong study design

## Analysis register

| ID | Type | Outcome | Timepoint | Measure | Model | HKSJ | Experimental | Comparator | Factor |
|---|---|---|---|---|---|---|---|---|---|
| A0 | counts | PRISMA flow | | | | | | | |
| A1 | pool | mortality | 30 days | RR | RE-REML | no | drug | placebo | |
"""


def set_reviewers(p: Path, names: list[str]) -> None:
    y = (p / "project.yaml").read_text(encoding="utf-8")
    line = "  reviewers: [" + ", ".join(names) + "]"
    if re.search(r"(?m)^  reviewers:.*$", y):
        y = re.sub(r"(?m)^  reviewers:.*$", lambda m: line, y)
    else:
        y = y.rstrip("\n") + "\nreview:\n" + line + "\n"
    (p / "project.yaml").write_text(y, encoding="utf-8", newline="\n")


def review_project(root: Path, design: str = "systematic-review", reviewers=("Reviewer A", "Reviewer B"),
                   g2: bool = True) -> Path:
    ptype = "systematic-review" if design == "systematic-review" else "review"
    p = init_project.create(Path(root) / "p", "Fictional review", ptype, design, "en", "en")
    for d in ("02_evidence/sr", "04_data/sr", "05_analysis/meta", "06_writing/review"):
        (p / d).mkdir(parents=True, exist_ok=True)
    (p / "03_protocol" / "sr-protocol.md").write_text(PROTOCOL, encoding="utf-8", newline="\n")
    set_reviewers(p, list(reviewers))
    if g2:
        gate.open_gate(p, "G2", by="Example author", files=["03_protocol/sr-protocol.md"])
    return p


def case_project(root: Path) -> Path:
    p = init_project.create(Path(root) / "c", "Fictional case", "case-report", "case-report", "en", "en")
    for d in ("01_case", "06_writing/case-report"):
        (p / d).mkdir(parents=True, exist_ok=True)
    return p
