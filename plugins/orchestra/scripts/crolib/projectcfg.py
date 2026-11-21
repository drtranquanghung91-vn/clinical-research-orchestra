"""Minimal reader for a project's project.yaml (top-level keys and one nested level). Standard library only."""
from __future__ import annotations

from pathlib import Path


def read_project_yaml(project: Path) -> dict:
    path = Path(project) / "project.yaml"
    data: dict = {}
    if not path.is_file():
        return data
    current = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        key, _, val = raw.strip().partition(":")
        val = val.strip().strip('"').strip("'")
        if indent == 0:
            if val == "":
                data[key] = {}
                current = key
            else:
                data[key] = val
                current = None
        elif current is not None:
            data[current][key] = val
    return data


def output_lang(project: Path) -> str:
    lang = read_project_yaml(project).get("language", {})
    return lang.get("output", "en") if isinstance(lang, dict) else "en"
