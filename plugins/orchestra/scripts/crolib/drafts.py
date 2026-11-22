"""Draft files of a deliverable (thesis or manuscript): default section order, required sections, roles,
the digest reviewers quote, and the output language. Standard library only."""
from __future__ import annotations

import hashlib
from pathlib import Path

from . import projectcfg

DELIVERABLES = ("thesis", "manuscript")
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
ROLE = {"00-tom-tat.md": "abstract", "00-dat-van-de.md": "introduction", "ch2-methods.md": "methods",
        "ch3-results.md": "results", "ch4-discussion.md": "discussion", "05-ket-luan.md": "conclusion",
        "06-kien-nghi.md": "conclusion", "01-abstract.md": "abstract", "02-introduction.md": "introduction",
        "03-methods.md": "methods", "04-results.md": "results", "05-discussion.md": "discussion",
        "06-conclusion.md": "conclusion"}
RESULTS_ROLES = {"results", "discussion", "conclusion", "abstract"}
DERIVED = (".rendered.md", ".numbered.md", ".humanized.md", ".assembled.md")


def folder(project, deliverable: str) -> Path:
    if deliverable not in DELIVERABLES:
        raise ValueError(f"deliverable must be one of {DELIVERABLES}")
    return Path(project) / "06_writing" / deliverable


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
    return list(DEFAULT_ORDER[deliverable])


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
    return files, missing, [n for n in REQUIRED[deliverable] if n not in names]


def results_bearing(path) -> bool:
    return ROLE.get(Path(path).name) in RESULTS_ROLES


def is_literature(path) -> bool:
    name = Path(path).name
    return name.startswith("ch1-") or name == "02-introduction.md"


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
    if deliverable == "manuscript" and isinstance(target, dict) and target.get("language") in ("vi", "en"):
        return target["language"]
    return projectcfg.output_lang(project)
