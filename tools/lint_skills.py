#!/usr/bin/env python3
"""Lint skill and agent frontmatter.

Rules: frontmatter exists; `name` equals the skill folder (or agent file stem); `description`
exists; model-invoked skills' descriptions start with "Use when"; skill bodies are at most
500 words. Usage: python tools/lint_skills.py [repo_root]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

MAX_WORDS = 500


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        raise ValueError("no frontmatter")
    parts = text.split("\n---", 1)
    if len(parts) < 2:
        raise ValueError("unterminated frontmatter")
    head = parts[0].splitlines()[1:]
    body = parts[1].split("\n", 1)[1] if "\n" in parts[1] else ""
    fm: dict[str, str] = {}
    key = None
    block: list[str] = []
    for line in head:
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m and not line.startswith(" "):
            if key is not None and block:
                fm[key] = " ".join(block).strip()
            key, val = m.group(1), m.group(2).strip()
            block = []
            if val in ("|", ">", "|-", ">-", ""):
                fm[key] = ""  # block scalar: continuation lines follow
            else:
                fm[key] = val.strip('"').strip("'")
                key = None
        elif key is not None:
            block.append(line.strip())
    if key is not None and block:
        fm[key] = " ".join(block).strip()
    return fm, body


def lint_skill(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        fm, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    except ValueError as e:
        return [f"{path}: {e}"]
    expected = path.parent.name if path.name == "SKILL.md" else path.stem
    if fm.get("name") != expected:
        errors.append(f"{path}: name '{fm.get('name')}' must equal '{expected}'")
    desc = fm.get("description", "")
    if not desc:
        errors.append(f"{path}: missing description")
    user_invoked = fm.get("disable-model-invocation", "").lower() == "true"
    if path.name == "SKILL.md" and not user_invoked and not desc.startswith("Use when"):
        errors.append(f"{path}: model-invoked description must start with 'Use when'")
    if path.name == "SKILL.md":
        words = len(body.split())
        if words > MAX_WORDS:
            errors.append(f"{path}: body has {words} words (max {MAX_WORDS})")
    return errors


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    root = Path(argv[0]) if argv else Path(__file__).resolve().parents[1]
    files = sorted(root.glob("plugins/*/skills/*/SKILL.md")) + sorted(root.glob("plugins/*/agents/*.md"))
    errors = [e for f in files for e in lint_skill(f)]
    for e in errors:
        print(e)
    print(f"lint_skills: {len(files)} files, {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
