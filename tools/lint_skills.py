#!/usr/bin/env python3
"""Lint skill and agent frontmatter.

Rules: frontmatter exists and is valid YAML (unquoted values must be plain YAML scalars: no ": "
or " #", no leading indicator character; checked with PyYAML too when it is installed); `name`
equals the skill folder (or agent file stem); `description` exists; model-invoked skills'
descriptions start with "Use when"; skill bodies are at most 500 words.
Usage: python tools/lint_skills.py [repo_root]   (exit 0 clean, 1 errors, 2 nothing to lint)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    import yaml  # optional: a second, exact opinion on the frontmatter
except ImportError:  # pragma: no cover
    yaml = None

MAX_WORDS = 500
BLOCK = ("|", ">", "|-", ">-", "|+", ">+")
INDICATORS = tuple("[{&*!|>%@`") + ("- ", "? ", ",", "]", "}", "#")


def _scalar(key: str, val: str) -> str:
    """Return the value of a one-line YAML scalar, or raise ValueError if YAML would reject it."""
    if val.startswith("'"):
        inner = val[1:-1]
        if len(val) < 2 or not val.endswith("'") or "'" in inner.replace("''", ""):
            raise ValueError(f"frontmatter value for '{key}' is not a valid single-quoted YAML string "
                             "(escape ' inside as '')")
        return inner.replace("''", "'")
    if val.startswith('"'):
        try:
            out = json.loads(val)
        except ValueError:
            raise ValueError(f"frontmatter value for '{key}' is not a valid double-quoted YAML string") from None
        if not isinstance(out, str):
            raise ValueError(f"frontmatter value for '{key}' is not a valid double-quoted YAML string")
        return out
    if ": " in val or " #" in val or val.endswith(":") or val.startswith(INDICATORS):
        raise ValueError(f"frontmatter value for '{key}' is not valid plain YAML; wrap it in single quotes")
    return val


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        raise ValueError("no frontmatter")
    parts = text.split("\n---", 1)
    if len(parts) < 2:
        raise ValueError("unterminated frontmatter")
    head = parts[0].splitlines()[1:]
    if yaml is not None:
        try:
            loaded = yaml.safe_load("\n".join(head))
        except yaml.YAMLError as e:
            raise ValueError("frontmatter is not valid YAML: " + " ".join(str(e).split())) from None
        if not isinstance(loaded, dict):
            raise ValueError("frontmatter is not valid YAML: expected 'key: value' lines")
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
            if val in BLOCK or val == "":
                fm[key] = ""  # block scalar: continuation lines follow
            else:
                fm[key] = _scalar(key, val)
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
    if not files and not (root / "plugins").is_dir():
        print(f"lint_skills: no plugins/ folder under {root}; nothing was linted", file=sys.stderr)
        return 2
    errors = [e for f in files for e in lint_skill(f)]
    for e in errors:
        print(e)
    print(f"lint_skills: {len(files)} files, {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
