"""Reviewer reports: agent → report file → rubric criteria; parsing of ```scores blocks, drafts-digest lines and
NEW-ANALYSIS requests (references/writing/rubric.md). Reports live in reviews/<agent>-<deliverable>.md (written by the
orchestrating skill from the agent's reply); the older single reviews/<agent>.md is still read for the deliverable its
scores block names. Standard library only."""
from __future__ import annotations

import json
import re
from pathlib import Path

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


def report_rel(agent: str, deliverable: str) -> str:
    """Per-deliverable report path: reviews/<name>-<d>.md (the consistency auditor: reviews/consistency-<d>.md)."""
    return REVIEWERS[agent][0][:-len(".md")] + f"-{deliverable}.md"


def report_candidates(agent: str, deliverable: str) -> list[str]:
    """Where a report for <d> may be: the per-deliverable file, then the legacy single file."""
    return [report_rel(agent, deliverable), REVIEWERS[agent][0]]


def report_path(project, agent: str, deliverable: str) -> Path:
    """The deliverable's own report if it exists; else the legacy reviews/<agent>.md unless its scores blocks are all
    for other deliverables (as guideline_checklist.checklist_path does with the legacy checklist); else the
    per-deliverable path (absent, used in messages). A legacy file with a malformed block stays readable, so worklog
    can name the problem."""
    project = Path(project)
    per, legacy = project / report_rel(agent, deliverable), project / REVIEWERS[agent][0]
    if per.is_file():
        return per
    if legacy.is_file():
        try:
            parsed = parse_report(legacy.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeDecodeError):
            return legacy
        others = [b for b in parsed["scores"] if b.get("deliverable") not in (deliverable, None)]
        if scores_for(parsed, deliverable) is not None or not others:
            return legacy
    return per
