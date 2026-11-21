#!/usr/bin/env python3
"""Author approval gates for a research project.

G1 question · G2 protocol and SAP · G3 results locked · G4 release.
State lives in <project>/gates/state.json. A gate may be waived by a line in decisions.md
starting with "WAIVE G<n>:".

  python gate.py open  <project> G1 --by "Author name"
  python gate.py lock  <project> G3 --by "Author name" --files ledgers/results-ledger.json 05_analysis/output/km.txt
  python gate.py check <project> G3

check prints (first token kept): "G3: open — results locked by <by> on <date>; <n> locked files unchanged"
(open = the author approved; it does NOT mean the files are free to change), "G3: not open — not locked yet",
or "G3: closed" plus the reasons (a locked file changed or is missing).

Exit codes: open/lock 0 = recorded; check 0 = open (or waived), 1 = closed (reasons listed);
2 = usage error, missing project folder or file, unreadable state (open/lock). Errors go to stderr.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

GATES = ("G1", "G2", "G3", "G4")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _state_path(project: Path) -> Path:
    return Path(project) / "gates" / "state.json"


def _load(project: Path) -> dict:
    p = _state_path(project)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"gates/state.json is unreadable: {e}") from e


def _waived(project: Path, gate: str) -> bool:
    d = Path(project) / "decisions.md"
    if not d.exists():
        return False
    return re.search(rf"^WAIVE {gate}:", d.read_text(encoding="utf-8"), re.M) is not None


def open_gate(project: Path, gate: str, by: str, files: list[str] | None = None) -> dict:
    if gate not in GATES:
        raise ValueError(f"gate must be one of {GATES}")
    project = Path(project)
    root = project.resolve()
    for f in files or []:
        target = (project / f).resolve()
        if Path(f).is_absolute() or not target.is_relative_to(root):
            raise ValueError(f"file outside project: {f}")
    state = _load(project)
    entry = {"status": "open", "at": dt.datetime.now().isoformat(timespec="seconds"), "by": by,
             "files": {f: sha256(project / f) for f in (files or [])}}
    state[gate] = entry
    _state_path(project).parent.mkdir(parents=True, exist_ok=True)
    _state_path(project).write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return entry


def check_gate(project: Path, gate: str) -> tuple[bool, list[str]]:
    if gate not in GATES:
        raise ValueError(f"gate must be one of {GATES}")
    project = Path(project)
    if _waived(project, gate):
        return True, []
    try:
        entry = _load(project).get(gate)
    except ValueError as e:
        return False, [str(e)]
    if not entry or entry.get("status") != "open":
        return False, [f"{gate} is not open: the author has not approved it"]
    why = []
    for rel, digest in entry.get("files", {}).items():
        f = project / rel
        if not f.exists():
            why.append(f"{rel} is missing since {gate} was locked")
        elif sha256(f) != digest:
            why.append(f"{rel} changed after {gate} was locked")
    return (not why), why


def check_line(project: Path, gate: str, ok: bool, why: list[str]) -> str:
    """Text printed by `check`. "G3: open" means the author approved; it never means "unlocked"."""
    try:
        entry = _load(project).get(gate)
    except ValueError:
        return f"{gate}: closed" + "".join(f"\n  - {w}" for w in why)
    is_open = bool(entry) and entry.get("status") == "open"
    if not ok:
        if not is_open and not _waived(project, gate):
            return f"{gate}: not open — " + ("not locked yet" if gate == "G3" else "not approved yet")
        return f"{gate}: closed" + "".join(f"\n  - {w}" for w in why)
    if not is_open:
        return f"{gate}: open — waived in decisions.md"
    n = len(entry.get("files", {}))
    when = str(entry.get("at", ""))[:10]
    what = "results locked" if gate == "G3" else "approved"
    tail = f"; {n} locked files unchanged" if n else ""
    return f"{gate}: open — {what} by {entry.get('by', '?')} on {when}{tail}"


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["open", "lock", "check"])
    ap.add_argument("project")
    ap.add_argument("gate", choices=GATES)
    ap.add_argument("--by", default="")
    ap.add_argument("--files", nargs="*", default=[])
    a = ap.parse_args(argv)
    if not Path(a.project).is_dir():
        print(f"gate: project folder {a.project} not found", file=sys.stderr)
        return 2
    if a.cmd in ("open", "lock"):
        if not a.by:
            print("gate: --by is required (who approved)", file=sys.stderr)
            return 2
        if a.cmd == "lock" and not a.files:
            print("gate: lock needs --files", file=sys.stderr)
            return 2
        try:
            open_gate(Path(a.project), a.gate, a.by, a.files)
        except OSError as e:
            print(f"gate: cannot read {e.filename or e}", file=sys.stderr)
            return 2
        except ValueError as e:
            print(f"gate: {e}", file=sys.stderr)
            return 2
        print(f"{a.gate} open by {a.by}")
        return 0
    ok, why = check_gate(Path(a.project), a.gate)
    print(check_line(Path(a.project), a.gate, ok, why))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
