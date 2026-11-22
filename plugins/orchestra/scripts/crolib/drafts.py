"""Draft files of a deliverable (thesis, manuscript, case-report, review): default section order, required sections,
roles, the digest reviewers quote, and the output language. Standard library only."""
from __future__ import annotations

import hashlib
from pathlib import Path

from . import projectcfg

DELIVERABLES = ("thesis", "manuscript", "case-report", "review")
DEFAULT_ORDER = {
    "thesis": ["00-tom-tat.md", "00-dat-van-de.md", "ch1-*.md", "ch2-methods.md", "ch3-results.md",
               "ch4-discussion.md", "05-ket-luan.md", "06-kien-nghi.md", "90-phu-luc.md"],
    "manuscript": ["00-title.md", "01-abstract.md", "02-introduction.md", "03-methods.md", "04-results.md",
                   "05-discussion.md", "06-conclusion.md"],
}
REQUIRED = {
    "thesis": {"ch2-methods.md": "Chương 2", "ch3-results.md": "Chương 3", "ch4-discussion.md": "Chương 4",
               "05-ket-luan.md": "Kết luận"},
    "manuscript": {"02-introduction.md": "Introduction", "03-methods.md": "Methods", "04-results.md": "Results",
                   "05-discussion.md": "Discussion"},
}
_REVIEW = ["00-title.md", "01-abstract.md", "02-introduction.md", "03-methods.md", "04-results.md", "sof.md",
           "05-discussion.md", "06-conclusion.md", "07-other-information.md"]
ORDERS = dict(DEFAULT_ORDER, **{
    "care": ["00-title.md", "01-abstract.md", "02-introduction.md", "03-patient-information.md",
             "04-clinical-findings.md", "05-timeline.md", "06-diagnostic-assessment.md",
             "07-therapeutic-intervention.md", "08-follow-up.md", "09-discussion.md", "10-patient-perspective.md",
             "11-consent.md"],
    "bmj": ["00-title.md", "01-summary.md", "02-background.md", "03-case-presentation.md", "04-investigations.md",
            "05-differential-diagnosis.md", "06-treatment.md", "07-outcome.md", "08-discussion.md",
            "09-learning-points.md", "10-patient-perspective.md", "11-consent.md"],
    "systematic": _REVIEW,
    "scoping": [x for x in _REVIEW if x != "sof.md"],
    "narrative": ["00-title.md", "01-abstract.md", "02-introduction.md", "03-methods.md", "04-*.md",
                  "05-discussion.md", "06-conclusion.md"],
})
_IMRAD = {"02-introduction.md": "Introduction", "03-methods.md": "Methods", "04-results.md": "Results",
          "05-discussion.md": "Discussion"}
REQUIRED_BY = dict(REQUIRED, **{
    "care": {"03-patient-information.md": "Patient information", "04-clinical-findings.md": "Clinical findings",
             "05-timeline.md": "Timeline", "09-discussion.md": "Discussion", "11-consent.md": "Informed consent"},
    "bmj": {"03-case-presentation.md": "Case presentation", "08-discussion.md": "Discussion",
            "09-learning-points.md": "Learning points", "11-consent.md": "Patient consent"},
    "systematic": _IMRAD,
    "scoping": _IMRAD,
    "narrative": {"02-introduction.md": "Introduction", "03-methods.md": "Methods (scope and search)",
                  "06-conclusion.md": "Conclusion"},
})
ROLE = {"00-tom-tat.md": "abstract", "00-dat-van-de.md": "introduction", "ch2-methods.md": "methods",
        "ch3-results.md": "results", "ch4-discussion.md": "discussion", "05-ket-luan.md": "conclusion",
        "06-kien-nghi.md": "conclusion", "01-abstract.md": "abstract", "02-introduction.md": "introduction",
        "03-methods.md": "methods", "04-results.md": "results", "05-discussion.md": "discussion",
        "06-conclusion.md": "conclusion"}
CASE_ROLE = dict.fromkeys(["00-title.md", "01-abstract.md", "01-summary.md", "02-introduction.md", "02-background.md"],
                          "case-front")
CASE_ROLE.update(dict.fromkeys(["03-patient-information.md", "04-clinical-findings.md", "05-timeline.md",
                                "06-diagnostic-assessment.md", "07-therapeutic-intervention.md", "08-follow-up.md",
                                "03-case-presentation.md", "04-investigations.md", "05-differential-diagnosis.md",
                                "06-treatment.md", "07-outcome.md"], "case-presentation"))
CASE_ROLE.update(dict.fromkeys(["09-discussion.md", "08-discussion.md", "09-learning-points.md",
                                "10-patient-perspective.md", "11-consent.md"], "case-discussion"))
RESULTS_ROLES = {"results", "discussion", "conclusion", "abstract", "case-front", "case-presentation", "case-discussion"}
DERIVED = (".rendered.md", ".numbered.md", ".humanized.md", ".assembled.md")
REVIEW_KIND = {"systematic-review": "systematic", "scoping-review": "scoping", "narrative-review": "narrative"}


def folder(project, deliverable: str) -> Path:
    if deliverable not in DELIVERABLES:
        raise ValueError(f"deliverable must be one of {DELIVERABLES}")
    return Path(project) / "06_writing" / deliverable


def review_kind(project) -> str:
    return REVIEW_KIND.get(str(projectcfg.read_project_yaml(project).get("design", "")), "narrative")


def variant(project, deliverable: str) -> str:
    if deliverable == "case-report":
        return "bmj" if str(projectcfg.get(project, "target.journal_style", "") or "").casefold() == "bmj" else "care"
    if deliverable == "review":
        return review_kind(project)
    folder(project, deliverable)  # validates the name
    return deliverable


def default_order(project, deliverable: str) -> list[str]:
    return list(ORDERS[variant(project, deliverable)])


def required(project, deliverable: str) -> dict[str, str]:
    return dict(REQUIRED_BY[variant(project, deliverable)])


def is_draft(name: str) -> bool:
    return name.endswith(".md") and not name.endswith(DERIVED)


def draft_files(project, deliverable: str) -> list[Path]:
    base = folder(project, deliverable)
    if not base.is_dir():
        return []
    return sorted((p for p in base.glob("*.md") if p.is_file() and is_draft(p.name)), key=lambda p: p.name)


def tracked_files(project, deliverable: str) -> list[Path]:
    """Drafts plus order.txt: what the digest covers and what a revert restores."""
    order = folder(project, deliverable) / "order.txt"
    return draft_files(project, deliverable) + ([order] if order.is_file() else [])


def order_entries(project, deliverable: str) -> list[str]:
    order = folder(project, deliverable) / "order.txt"
    if order.is_file():
        return [ln.strip() for ln in order.read_text(encoding="utf-8-sig").splitlines()
                if ln.strip() and not ln.lstrip().startswith("#")]
    return default_order(project, deliverable)


def ordered(project, deliverable: str) -> tuple[list[Path], list[str], list[str]]:
    """(section files in order, order entries not found, required sections missing)."""
    base = folder(project, deliverable)
    files: list[Path] = []
    missing: list[str] = []
    for entry in order_entries(project, deliverable):
        if "/" in entry or "\\" in entry or ".." in entry:
            missing.append(entry)
            continue
        if any(c in entry for c in "*?["):
            hits = sorted((p for p in base.glob(entry) if p.is_file() and is_draft(p.name)), key=lambda p: p.name)
        else:
            hits = [base / entry] if (base / entry).is_file() and is_draft(entry) else []
        if not hits:
            missing.append(entry)
        files += [h for h in hits if h not in files]
    names = {p.name for p in files}
    return files, missing, [n for n in required(project, deliverable) if n not in names]


def role_of(path) -> str | None:
    p = Path(path)
    if p.parent.name == "case-report":
        return CASE_ROLE.get(p.name)
    if p.parent.name == "review":
        if p.name == "sof.md":
            return "results"
        if p.name.startswith("04-") and p.name != "04-results.md":
            return "synthesis"
    return ROLE.get(p.name)


def results_bearing(path) -> bool:
    return role_of(path) in RESULTS_ROLES


def is_literature(path) -> bool:
    p = Path(path)
    if p.parent.name == "case-report":
        return False
    return p.name.startswith("ch1-") or p.name == "02-introduction.md" or role_of(p) == "synthesis"


def digest(project, deliverable: str) -> str:
    paths = tracked_files(project, deliverable)
    if not draft_files(project, deliverable):
        raise FileNotFoundError(f"no drafts in 06_writing/{deliverable}/")
    h = hashlib.sha256()
    for p in sorted(paths, key=lambda x: x.name):
        h.update(p.name.encode("utf-8") + b"\0" + hashlib.sha256(p.read_bytes()).hexdigest().encode("ascii") + b"\n")
    return h.hexdigest()


def lang_of(project, deliverable: str) -> str:
    target = projectcfg.read_project_yaml(project).get("target", {})
    if deliverable != "thesis" and isinstance(target, dict) and target.get("language") in ("vi", "en"):
        return target["language"]
    return projectcfg.output_lang(project)
