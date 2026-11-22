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

G4 opens only from a clean, fresh audit: `open <project> G4 --by NAME` locks the files listed in
reviews/audit.json (refused with the reasons while the audit is missing, has blocks, or a file changed since);
`lock ... G4` and `--files` are usage errors. `check <project> G4 --deliverable thesis|manuscript|case-report|review` checks only
that deliverable's locked files. Line: "G4: open — approved after a clean audit by <by> on <date>; <n> locked files
unchanged", "G4: not open — not approved yet[ for the <d>]", or "G4: closed — <reason>; <reason>".
`check <project> G4` without --deliverable checks every per-deliverable entry and fails if any fails.

A case report's final export also needs a `CONSENT: obtained …` line in decisions.md (P5).

export_problems(project, deliverable) -> list[str] is the one rule for a FINAL export (assemble.py --final,
build_docx.py out/<d>.docx, the orchestra gate hook): [] = allowed. It returns the reasons G4 is not open for the
deliverable (a "WAIVE G4:" line counts as open), plus the reasons reviews/audit.json is missing, unreadable, or
no longer matches the files on disk. The audit file must exist and match even when G4 is waived; blocking
findings in it are tolerated only when G4 is waived.

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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crolib import drafts  # noqa: E402

GATES = ("G1", "G2", "G3", "G4")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _state_path(project: Path) -> Path:
    return Path(project) / "gates" / "state.json"


def _save_state(project: Path, state: dict) -> None:
    """Write gates/state.json with LF line endings on every platform."""
    path = _state_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


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


DELIVERABLES = drafts.DELIVERABLES
AUDIT = Path("reviews") / "audit.json"


class Refused(Exception):
    """A gate that cannot be opened yet (CLI: exit 1, reason on stdout)."""


def waived(project: Path, gate: str) -> bool:
    return _waived(project, gate)


def audit_status(project: Path) -> tuple[dict | None, list[str]]:
    p = Path(project) / AUDIT
    if not p.is_file():
        return None, ["reviews/audit.json not found: run /orchestra:audit (audit.py) first"]
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError) as e:
        return None, [f"reviews/audit.json is unreadable: {e}"]
    if not isinstance(data, dict) or not isinstance(data.get("files"), dict) \
            or not isinstance(data.get("blocks"), int) or isinstance(data.get("blocks"), bool):
        return None, ["reviews/audit.json lacks 'blocks' or 'files'"]
    why = []
    if data["blocks"]:
        why.append(f"the audit has {data['blocks']} blocking finding(s); see reviews/audit.md")
    if not data["files"]:
        why.append("reviews/audit.json lists no files")
    root = Path(project).resolve()
    for rel, digest in sorted(data["files"].items()):
        f = Path(project) / rel
        if Path(rel).is_absolute() or not f.resolve().is_relative_to(root):
            why.append(f"{rel} is outside the project")
        elif digest is None:            # an input absent at audit time
            if f.exists():
                why.append(f"{rel} changed since the audit (created after it)")
        elif not f.is_file():
            why.append(f"{rel} is missing since the audit")
        elif sha256(f) != digest:
            why.append(f"{rel} changed since the audit")
    return data, why


def audited_deliverables(data: dict) -> list[str]:
    ds = data.get("deliverables")
    if isinstance(ds, list) and ds:
        return [d for d in ds if d in DELIVERABLES]
    d = data.get("deliverable")
    return [d] if d in DELIVERABLES else list(DELIVERABLES)


def _open_g4(project: Path, by: str) -> dict:
    data, why = audit_status(project)
    if why:
        raise Refused("; ".join(why))
    if not audited_deliverables(data):
        raise Refused("reviews/audit.json names no thesis, manuscript, case-report or review deliverable")
    state = _load(project)
    old = state.get("G4") if isinstance(state.get("G4"), dict) and state["G4"].get("status") == "open" else {}
    now = dt.datetime.now().isoformat(timespec="seconds")
    per = dict(old.get("deliverables", {}))
    for d in audited_deliverables(data):
        per[d] = {"at": now, "by": by, "audit_at": str(data.get("at", "")), "files": dict(data["files"])}
    union: dict = {}
    for entry in per.values():
        union.update(entry["files"])
    state["G4"] = {"status": "open", "at": now, "by": by, "files": union, "deliverables": per}
    _save_state(project, state)
    return state["G4"]


def open_gate(project: Path, gate: str, by: str, files: list[str] | None = None) -> dict:
    if gate not in GATES:
        raise ValueError(f"gate must be one of {GATES}")
    if gate == "G4":
        if files:
            raise ValueError("G4 takes its files from reviews/audit.json; do not pass --files")
        return _open_g4(Path(project), by)
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
    _save_state(project, state)
    return entry


def check_gate(project: Path, gate: str, deliverable: str | None = None) -> tuple[bool, list[str]]:
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
    groups = [entry.get("files", {})]
    if gate == "G4":
        per = entry.get("deliverables")
        if deliverable:
            sub = per.get(deliverable) if isinstance(per, dict) else None
            if not isinstance(sub, dict):
                return False, [f"G4 is not open for the {deliverable}: the author has not opened it after a clean audit"]
            groups = [sub.get("files", {})]
        elif isinstance(per, dict) and per:
            groups = [s.get("files", {}) for s in per.values() if isinstance(s, dict)]
    why = []
    for files in groups:
        for rel, digest in files.items():
            f = project / rel
            if digest is None:          # G4: an input absent at audit time must still be absent
                if not f.exists():
                    continue
                msg = f"{rel} changed since the audit (created after it)"
            elif not f.exists():
                msg = f"{rel} is missing since the audit" if gate == "G4" else f"{rel} is missing since {gate} was locked"
            elif sha256(f) != digest:
                msg = f"{rel} changed since the audit" if gate == "G4" else f"{rel} changed after {gate} was locked"
            else:
                continue
            if msg not in why:
                why.append(msg)
    return (not why), why


def export_problems(project: Path, deliverable: str | None) -> list[str]:
    """Reasons a final export of `deliverable` is not allowed; [] = allowed (see the module docstring)."""
    project = Path(project)
    ok, why = check_gate(project, "G4", deliverable or None)
    problems = [] if ok else list(why)
    waived_g4 = _waived(project, "G4")
    data, awhy = audit_status(project)
    for w in awhy:
        if waived_g4 and data is not None and w.startswith("the audit has "):
            continue
        if w not in problems:
            problems.append(w)
    if data is not None:
        for w in _uncovered(project, data, deliverable):
            if w not in problems:
                problems.append(w)
    covered = [deliverable] if deliverable else (audited_deliverables(data) if data is not None else [])
    if "case-report" in covered:
        import case_lint  # lazy: case_lint imports audit, which imports gate
        if not case_lint.consent_recorded(project):
            problems.append("consent not recorded in decisions.md ('CONSENT: obtained <form, who signed>'); "
                            "a case report is never exported without it")
    return problems


_IMG = re.compile(r"!\[[^\]]*\]\(([^)\s]+)")


def export_files(project: Path, deliverable: str) -> list[Path]:
    """Files a final export depends on: drafts, order.txt and every existing image the drafts reference."""
    project = Path(project)
    base = drafts.folder(project, deliverable)
    paths = list(drafts.tracked_files(project, deliverable))
    for f in drafts.draft_files(project, deliverable):
        for m in _IMG.finditer(f.read_text(encoding="utf-8-sig", errors="replace")):
            src = m.group(1)
            img = Path(src) if Path(src).is_absolute() else base / src
            if img.is_file() and img not in paths:
                paths.append(img)
    return paths


def _uncovered(project: Path, data: dict, deliverable: str | None) -> list[str]:
    """Current drafts, order.txt and images that the audit's file map does not cover (added since the audit)."""
    project = Path(project)
    root = project.resolve()
    known = data["files"]
    ds = [deliverable] if deliverable else audited_deliverables(data)
    out: list[str] = []
    for d in ds:
        if d not in drafts.DELIVERABLES:
            continue
        paths = export_files(project, d)
        for f in paths:
            try:
                rel = f.resolve().relative_to(root).as_posix()
            except ValueError:
                continue            # outside the project: the audit cannot hash it
            if rel not in known and f"{rel} is not covered by the audit (added since)" not in out:
                out.append(f"{rel} is not covered by the audit (added since)")
    return out


def check_line(project: Path, gate: str, ok: bool, why: list[str], deliverable: str | None = None) -> str:
    """Text printed by `check`. "G3: open" means the author approved; it never means "unlocked"."""
    try:
        entry = _load(project).get(gate)
    except ValueError:
        return f"{gate}: closed" + "".join(f"\n  - {w}" for w in why)
    is_open = bool(entry) and entry.get("status") == "open"
    if is_open and gate == "G4" and deliverable:
        is_open = deliverable in entry.get("deliverables", {})
    if not ok:
        if not is_open and not _waived(project, gate):
            return f"{gate}: not open — " + ("not locked yet" if gate == "G3" else "not approved yet" + (
                f" for the {deliverable}" if deliverable else ""))
        if gate == "G4":
            return "G4: closed — " + "; ".join(why)
        return f"{gate}: closed" + "".join(f"\n  - {w}" for w in why)
    if not is_open:
        return f"{gate}: open — waived in decisions.md"
    files = entry.get("files", {})
    if gate == "G4" and deliverable:
        files = entry["deliverables"][deliverable].get("files", {})
    n = sum(1 for v in files.values() if v is not None)     # null = an input absent at audit time
    when = str(entry.get("at", ""))[:10]
    what = {"G3": "results locked", "G4": "approved after a clean audit"}.get(gate, "approved")
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
    ap.add_argument("--deliverable", choices=DELIVERABLES)
    a = ap.parse_args(argv)
    if a.deliverable and (a.gate != "G4" or a.cmd != "check"):
        print("gate: --deliverable only applies to `check <project> G4`", file=sys.stderr)
        return 2
    if a.cmd == "lock" and a.gate == "G4":
        print("gate: G4 opens from the audit: use gate.py open <project> G4 --by NAME", file=sys.stderr)
        return 2
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
        except Refused as e:
            print(f"G4: refused — {e}")
            return 1
        except OSError as e:
            print(f"gate: cannot read {e.filename or e}", file=sys.stderr)
            return 2
        except ValueError as e:
            print(f"gate: {e}", file=sys.stderr)
            return 2
        print(f"{a.gate} open by {a.by}")
        return 0
    ok, why = check_gate(Path(a.project), a.gate, a.deliverable)
    print(check_line(Path(a.project), a.gate, ok, why, a.deliverable))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
