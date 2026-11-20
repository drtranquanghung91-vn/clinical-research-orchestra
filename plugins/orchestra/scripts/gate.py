#!/usr/bin/env python3
"""Author approval gates for a research project.

G1 question · G2 protocol and SAP · G3 results locked · G4 release.
State lives in <project>/gates/state.json. A gate may be waived by a line in decisions.md
starting with "WAIVE G<n>:".

  python gate.py open  <project> G1 --by "Author name"
  python gate.py lock  <project> G3 --by "Author name" --files ledgers/results-ledger.json 05_analysis/output/km.txt
  python gate.py check <project> G3
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
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _waived(project: Path, gate: str) -> bool:
    d = Path(project) / "decisions.md"
    if not d.exists():
        return False
    return re.search(rf"^WAIVE {gate}:", d.read_text(encoding="utf-8"), re.M) is not None


def open_gate(project: Path, gate: str, by: str, files: list[str] | None = None) -> dict:
    if gate not in GATES:
        raise ValueError(f"gate must be one of {GATES}")
    project = Path(project)
    entry = {"status": "open", "at": dt.datetime.now().isoformat(timespec="seconds"), "by": by,
             "files": {f: sha256(project / f) for f in (files or [])}}
    state = _load(project)
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
    entry = _load(project).get(gate)
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
    if a.cmd in ("open", "lock"):
        if not a.by:
            print("gate: --by is required (who approved)")
            return 2
        if a.cmd == "lock" and not a.files:
            print("gate: lock needs --files")
            return 2
        open_gate(Path(a.project), a.gate, a.by, a.files)
        print(f"{a.gate} open by {a.by}")
        return 0
    ok, why = check_gate(Path(a.project), a.gate)
    print(f"{a.gate}: {'open' if ok else 'closed'}" + "".join(f"\n  - {w}" for w in why))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
