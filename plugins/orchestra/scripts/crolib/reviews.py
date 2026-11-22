"""Reviewer reports: agent → report file → rubric criteria; parsing of ```scores blocks, drafts-digest lines and
NEW-ANALYSIS requests (references/writing/rubric.md). Standard library only."""
from __future__ import annotations

import json
import re

REVIEWERS = {
    "citation-verifier": ("reviews/citation-verifier.md", ("citations",)),
    "statistical-reviewer": ("reviews/statistical-reviewer.md", ("statistics",)),
    "reporting-guideline-checker": ("reviews/reporting-guideline-checker.md", ("guideline",)),
    "scientific-editor": ("reviews/scientific-editor.md", ("structure", "claim_scope", "limitations")),
    "consistency-auditor": ("reviews/consistency.md", ("consistency",)),
}
CRITERIA = ("citations", "statistics", "guideline", "structure", "claim_scope", "limitations", "consistency", "prose")
SCORES = re.compile(r"^```scores[ \t]*\r?\n(.*?)\r?\n```[ \t]*$", re.M | re.S)
DIGEST = re.compile(r"^drafts-digest:[ \t]*(thesis|manuscript|case-report|review)[ \t]+([0-9a-f]{64})[ \t]*$", re.M)
REQUEST = re.compile(r"^[ \t]*(?:[-*][ \t]*)?NEW-ANALYSIS:[ \t]*(\S.*?)[ \t]*$", re.M)
NONE = {"none", "không có", "không", "n/a", "-"}
NONE_SPLIT = re.compile(r"\s*[—–;:,(]|\s+-\s+")


def parse_report(text: str) -> dict:
    blocks, bad = [], 0
    for m in SCORES.finditer(text):
        try:
            obj = json.loads(m.group(1))
        except ValueError:
            bad += 1
            continue
        if isinstance(obj, dict):
            blocks.append(obj)
        else:
            bad += 1
    return {"scores": blocks, "bad_scores": bad, "digests": dict(DIGEST.findall(text)),
            "requests": [r for r in REQUEST.findall(text) if not is_none(r)]}


def is_none(request: str) -> bool:
    """`none`, also with a trailing comment ("none — wording only", "không có (…)")."""
    head = NONE_SPLIT.split(request.strip(), 1)[0]
    return head.strip("() .").lower() in NONE or request.strip("() .").lower() in NONE


def scores_for(parsed: dict, deliverable: str) -> dict | None:
    return next((s for s in parsed["scores"] if s.get("deliverable") == deliverable), None)
