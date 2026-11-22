#!/usr/bin/env python3
"""orchestra gate hook (PreToolUse on Bash|PowerShell|Agent|Task); reads the hook JSON on stdin.

- A shell command running `assemble.py <project> <deliverable> … --final`, or `build_docx.py … <dir>/out/thesis.docx`
  (manuscript.docx, case-report.docx or review.docx), is denied unless `gate.py check <project> G4` passes for that deliverable. The project is
  the <project> argument (build_docx: --project, else the folder holding out/), else the working directory.
- An Agent/Task prompt containing `orchestra-role:` is denied unless G3 is open for the project in the working
  directory (the nearest folder upward with project.yaml).
- An Agent/Task prompt containing `orchestra-prep:` (P5 review-work briefs) is denied unless G2 is open.
- Anything else, or no project.yaml: allowed silently (no output). The hook never blocks on its own errors: it
  answers "ask" with the error text. Exit code always 0. Standard library only.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gate  # noqa: E402

SHELL = ("Bash", "PowerShell")
AGENT = ("Agent", "Task")
ROLE = re.compile(r"orchestra-role:\s*([\w-]+)")
SEP = re.compile(r"&&|\|\||[;|\n]")
CD = {"cd", "set-location", "sl", "pushd", "push-location", "chdir"}
OPTS_WITH_VALUE = {"assemble.py": {"--lang"}, "build_docx.py": {"--project", "--template"}}
FINAL_NAMES = ("thesis.docx", "manuscript.docx", "case-report.docx", "review.docx")
PREP = re.compile(r"orchestra-prep:\s*([\w-]+)")


TOKEN = re.compile(r"""(?:[^\s"']|"[^"]*"|'[^']*')+""")


def _tokens(segment: str) -> list[str]:
    """Whitespace tokens; a quoted part (also inside a word: --project="a b") stays in one token, quotes removed."""
    toks = TOKEN.findall(segment) or segment.split()
    return [t.replace('"', "").replace("'", "") for t in toks]


def map_path(s: str, nt: bool | None = None) -> str:
    """Git Bash paths on Windows: `/c/x` -> `C:/x`; `~` -> the home folder."""
    if s.startswith("~"):
        s = os.path.expanduser(s)
    if (os.name == "nt" if nt is None else nt) and re.match(r"^/[A-Za-z](/|$)", s):
        s = s[1].upper() + ":" + (s[2:] or "/")
    return s


def _name(tok: str) -> str:
    return tok.replace("\\", "/").rsplit("/", 1)[-1].lower()


def _args(toks: list[str], i: int, script: str) -> tuple[list[str], dict]:
    pos, opts, k = [], {}, i + 1
    while k < len(toks):
        t = toks[k]
        if t.startswith("-"):
            key, eq, val = t.partition("=")
            if key in OPTS_WITH_VALUE[script] and not eq:
                opts[key] = toks[k + 1] if k + 1 < len(toks) else ""
                k += 2
                continue
            opts[key] = val if eq else True
        else:
            pos.append(t)
        k += 1
    return pos, opts


def exports(command: str, cwd: Path) -> list[tuple[Path, str, str]]:
    """(project, deliverable, what) for every final export the command would run."""
    found = []
    for seg in SEP.split(command):
        toks = _tokens(seg.strip())
        if not toks:
            continue
        if toks[0].lower() in CD:
            target = next((t for t in toks[1:] if not t.startswith("-")), None)
            if target:
                cwd = cwd / map_path(target)
            continue
        for i, tok in enumerate(toks):
            name = _name(tok)
            if name == "assemble.py":
                pos, opts = _args(toks, i, name)
                if "--final" in opts:
                    found.append((cwd / map_path(pos[0]) if pos else cwd, pos[1] if len(pos) > 1 else "", "assemble.py --final"))
            elif name == "build_docx.py":
                pos, opts = _args(toks, i, name)
                if len(pos) >= 2:
                    out = Path(os.path.normpath(cwd / map_path(pos[-1])))
                    if out.name.lower() in FINAL_NAMES and out.parent.name.lower() == "out":
                        proj = opts.get("--project")
                        project = cwd / map_path(proj) if isinstance(proj, str) and proj else out.parent.parent
                        found.append((project, out.stem.lower(), f"build_docx.py → out/{out.name}"))
    return found


def _find_project(start: Path) -> Path | None:
    start = start.resolve()
    for p in (start, *start.parents):
        if (p / "project.yaml").is_file():
            return p
    return None


def _deny(reason: str) -> dict:
    return {"permissionDecision": "deny", "permissionDecisionReason": reason}


def decide(data: dict) -> dict | None:
    tool = str(data.get("tool_name", ""))
    tin = data.get("tool_input") or {}
    cwd = Path(str(data.get("cwd") or ".")).expanduser()
    if tool in SHELL:
        cmd = str(tin.get("command", "")) if isinstance(tin, dict) else str(tin)
        low = cmd.lower()
        if "assemble.py" not in low and "build_docx.py" not in low:
            return None
        for project, deliverable, what in exports(cmd, cwd):
            if not (project / "project.yaml").is_file():
                continue
            why = gate.export_problems(project, deliverable or None)
            if why:
                scope = f" for the {deliverable}" if deliverable else ""
                return _deny(f"[orchestra] {what} is a final export and cannot run{scope}: {'; '.join(why)}. "
                             "Run /orchestra:audit, fix every block, then the author opens G4 "
                             "(gate.py open . G4 --by NAME) and the export runs again. / "
                             "Xuất bản cuối cần cổng G4 mở: chạy /orchestra:audit, sửa hết lỗi chặn, rồi tác giả mở G4.")
        return None
    if tool in AGENT:
        text = " ".join(str(tin.get(k, "")) for k in ("prompt", "description")) if isinstance(tin, dict) else str(tin)
        m, prep = ROLE.search(text), PREP.search(text)
        if not m and not prep:
            return None
        project = _find_project(cwd)
        if project is None:
            return None
        if prep:
            ok, why = gate.check_gate(project, "G2")
            if not ok:
                return _deny(f"[orchestra] review-work brief '{prep.group(1)}' (screening suggestions, draft extraction "
                             f"or risk of bias) needs the locked protocol and G2 is not open: {'; '.join(why)}. The author "
                             "locks the protocol first (gate.py open . G2 --by NAME --files 03_protocol/sr-protocol.md …). / "
                             "Sàng lọc, trích xuất và đánh giá nguy cơ sai lệch chỉ làm sau khi tác giả khoá đề cương (G2).")
        if m:
            ok, why = gate.check_gate(project, "G3")
            if not ok:
                return _deny(f"[orchestra] writer role '{m.group(1)}' needs locked results and G3 is not open: "
                             f"{'; '.join(why)}. The author reviews the results and locks them first "
                             "(gate.py lock . G3 --by NAME --files …). / "
                             "Vai trò viết cần kết quả đã được tác giả khoá (G3); hãy khoá kết quả trước.")
    return None


def main() -> int:
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8-sig", errors="replace") or "{}")
        if not isinstance(data, dict):
            raise ValueError("input is not a JSON object")
        d = decide(data)
    except Exception as e:  # noqa: BLE001 - never block on our own errors
        d = {"permissionDecision": "ask", "permissionDecisionReason": (
            f"[orchestra] gate hook error ({type(e).__name__}: {e}); review this call before allowing. / "
            "Lỗi hook kiểm tra cổng; hãy xem lại trước khi cho phép.")}
    if d:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", **d}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
