"""Minimal reader for a project's project.yaml (top-level keys and one nested level). Standard library only."""
from __future__ import annotations

from pathlib import Path


def _clean(val: str) -> str:
    quote = None
    for i, ch in enumerate(val):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'" and (i == 0 or val[i - 1].isspace()):
            quote = ch
        elif ch == "#" and i > 0 and val[i - 1].isspace():
            val = val[:i]
            break
    val = val.strip()
    if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
        return val[1:-1]
    return val


def read_project_yaml(project: Path) -> dict:
    path = Path(project) / "project.yaml"
    data: dict = {}
    if not path.is_file():
        return data
    current = None
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        key, _, val = raw.strip().partition(":")
        val = _clean(val.strip())
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


NULLS = ("", "null", "~", "Null", "NULL")


def parse_list(val) -> list[str]:
    """A one-line YAML flow list ("[a, 'b c']") as strings; "", null, ~ and [] give []. Items cannot contain commas."""
    if not isinstance(val, str):
        return []
    v = val.strip()
    if v in NULLS or v == "[]":
        return []
    if not (v.startswith("[") and v.endswith("]")):
        return [_clean(v)]
    return [_clean(x.strip()) for x in v[1:-1].split(",") if x.strip()]


def get(project: Path, dotted: str, default=None):
    """Value of a top-level or one-level nested key ("tools.rscript"); "", null and ~ give `default`."""
    cur = read_project_yaml(project)
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    if isinstance(cur, str) and cur.strip() in NULLS:
        return default
    return cur
