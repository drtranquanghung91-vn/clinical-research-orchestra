#!/usr/bin/env python3
"""Double extraction, risk of bias and charting checks for systematic and scoping reviews (E-SCR).

  python extract_check.py <project>

Extraction: 04_data/sr/extraction-<reviewer>.csv, one file per human reviewer in project.yaml review.reviewers
(<reviewer> = lower-case name, non-alphanumerics → "-"), rows keyed by study_id,outcome,timepoint,group. Every
differing cell is listed (warn); the consensus 04_data/sr/extraction.csv must exist when they differ, and each of
its cells must match one extractor unless the row has a consensus_note (block). Risk of bias:
04_data/sr/rob.csv (study_id,outcome,tool,domain,judgement,support,reviewer); tools RoB 2 (D1-D5) and ROBINS-I
(D1-D7), each with an "overall" row that is never better than the worst domain (the tool's algorithm, never a
summed score); the reviewer column names both human reviewers. Scoping reviews: 04_data/sr/charting.csv needs
extracted_by and verified_by, two different human reviewers; no risk of bias.
Exit codes: 0 = no block (warnings allowed); 1 = block findings; 2 = usage or I/O error.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crolib import projectcfg  # noqa: E402
import screening  # noqa: E402

SRD = "04_data/sr"
EXTRACTION = f"{SRD}/extraction.csv"
ROB = f"{SRD}/rob.csv"
CHARTING = f"{SRD}/charting.csv"
KEY = ("study_id", "outcome", "timepoint", "group")
SKIP = set(KEY) | {"consensus_note", "notes"}
TOOLS = {
    "RoB 2": {"domains": [f"D{i}" for i in range(1, 6)], "levels": ["low", "some concerns", "high"]},
    "ROBINS-I": {"domains": [f"D{i}" for i in range(1, 8)],
                 "levels": ["low", "moderate", "serious", "critical", "no information"]},
}
NUM = re.compile(r"-?\d+(?:[.,]\d+)?")


def _same(a: str, b: str) -> bool:
    a, b = (a or "").strip(), (b or "").strip()
    if NUM.fullmatch(a) and NUM.fullmatch(b):
        return float(a.replace(",", ".")) == float(b.replace(",", "."))
    return a.casefold() == b.casefold()


def _keyed(path: Path, rel: str, found: list) -> dict[tuple, tuple[int, dict]]:
    out: dict[tuple, tuple[int, dict]] = {}
    for i, r in enumerate(screening.read_csv(path), start=2):
        k = tuple((r.get(c) or "").strip() for c in KEY)
        if k in out:
            found.append(("block", f"{rel}:{i}", f"duplicate row for {' / '.join(k)}"))
        out[k] = (i, r)
    return out


def check_extraction(project: Path, humans: list[str]) -> list[tuple[str, str, str]]:
    found: list[tuple[str, str, str]] = []
    files = sorted((project / SRD).glob("extraction-*.csv")) if (project / SRD).is_dir() else []
    if not files:
        if (project / EXTRACTION).is_file():
            found.append(("block", f"{EXTRACTION}:1", "extraction.csv has no source: two extraction-<reviewer>.csv files "
                                                      "(one per human reviewer) are needed"))
        return found
    by_slug = {screening.slug(h): h for h in humans}
    named = []
    for f in files:
        s = f.stem[len("extraction-"):]
        if s not in by_slug or screening.AI_NAME.search(s):
            found.append(("block", f"{SRD}/{f.name}:1", f"{f.name}: '{s}' is not a reviewer in project.yaml review.reviewers"))
        else:
            named.append((by_slug[s], f))
    if len(named) != 2:
        found.append(("block", f"{SRD}:1", f"two extraction files are needed, one per human reviewer (found {len(named)})"))
        return found
    (na, fa), (nb, fb) = named
    ra, rb = (_keyed(f, f"{SRD}/{f.name}", found) for f in (fa, fb))
    diffs = 0
    for k in sorted(set(ra) | set(rb)):
        label = " / ".join(k)
        if k not in ra or k not in rb:
            who, f, (line, _) = (na, fb, rb[k]) if k not in ra else (nb, fa, ra[k])
            found.append(("warn", f"{SRD}/{f.name}:{line}", f"{label}: not extracted by {who}"))
            diffs += 1
            continue
        (la, xa), (_, xb) = ra[k], rb[k]
        for col in sorted((set(xa) | set(xb)) - SKIP):
            if not _same(xa.get(col, ""), xb.get(col, "")):
                found.append(("warn", f"{SRD}/{fa.name}:{la}",
                              f"{label}: {col} {na}={xa.get(col, '')}, {nb}={xb.get(col, '')}"))
                diffs += 1
    cons_path = project / EXTRACTION
    if not cons_path.is_file():
        if diffs:
            found.append(("block", f"{EXTRACTION}:1", f"no consensus file: {diffs} difference(s) between the extractors"))
        return found
    cons = _keyed(cons_path, EXTRACTION, found)
    for k in sorted((set(ra) | set(rb)) - set(cons)):
        found.append(("block", f"{EXTRACTION}:1", f"{' / '.join(k)}: extracted by the reviewers but missing from extraction.csv"))
    for k, (line, row) in cons.items():
        if (row.get("consensus_note") or "").strip():
            continue
        label = " / ".join(k)
        a, b = ra.get(k, (0, {}))[1], rb.get(k, (0, {}))[1]
        if not a and not b:
            found.append(("block", f"{EXTRACTION}:{line}", f"{label}: not in either extraction and no consensus_note"))
            continue
        for col in sorted(set(row) - SKIP):
            v = row.get(col, "")
            if not (_same(v, a.get(col, "")) or _same(v, b.get(col, ""))):
                found.append(("block", f"{EXTRACTION}:{line}",
                              f"{label}: {col} = {v} matches neither extractor and the row has no consensus_note"))
    return found


def _rank(tool: str, level: str) -> int:
    order = [x for x in TOOLS[tool]["levels"] if x != "no information"]
    return order.index(level) if level in order else -1


def check_rob(project: Path, humans: list[str]) -> list[tuple[str, str, str]]:
    found: list[tuple[str, str, str]] = []
    groups: dict[tuple, list[tuple[int, dict]]] = {}
    for i, r in enumerate(screening.read_csv(project / ROB), start=2):
        groups.setdefault(((r.get("study_id") or "").strip(), (r.get("outcome") or "").strip()), []).append((i, r))
    want = {h.casefold() for h in humans}
    for (study, outcome), rows in groups.items():
        where = f"{ROB}:{rows[0][0]}"
        label = f"{study} / {outcome}"
        tools = {(r.get("tool") or "").strip() for _, r in rows}
        if len(tools) != 1:
            found.append(("block", where, f"{label}: one tool per study and outcome (found {', '.join(sorted(tools))})"))
            continue
        tool = tools.pop()
        if tool not in TOOLS:
            found.append(("warn", where, f"{label}: tool {tool!r} is not checked by this script; check it by hand"))
            continue
        spec, doms = TOOLS[tool], {}
        for line, r in rows:
            dom, j = (r.get("domain") or "").strip(), (r.get("judgement") or "").strip().casefold()
            loc = f"{ROB}:{line}"
            if NUM.fullmatch(j):
                found.append(("block", loc, f"{label} {dom}: numeric judgement {j}; judgements follow the tool's algorithm, never a summed score"))
                continue
            if dom not in spec["domains"] + ["overall"]:
                found.append(("block", loc, f"{label}: domain {dom!r} is not a {tool} domain"))
                continue
            if j not in spec["levels"]:
                found.append(("block", loc, f"{label} {dom}: judgement {j!r} not in {spec['levels']}"))
                continue
            doms[dom] = j
            names = {x.strip().casefold() for x in (r.get("reviewer") or "").split(";") if x.strip()}
            if len(want) < 2 or names != want:
                found.append(("block", loc, f"{label} {dom}: confirmed by both reviewers ({'; '.join(humans)}) is required; "
                                            f"found {r.get('reviewer')!r} (an AI draft is never final)"))
            if not (r.get("support") or "").strip():
                found.append(("warn", loc, f"{label} {dom}: no supporting quote"))
        for dom in spec["domains"] + ["overall"]:
            if dom not in doms:
                found.append(("block", where, f"{label}: {dom} missing"))
        if "overall" in doms and doms["overall"] != "no information":
            worst = max((doms[d] for d in spec["domains"] if d in doms), key=lambda x: _rank(tool, x), default=None)
            if worst and _rank(tool, doms["overall"]) < _rank(tool, worst):
                found.append(("block", where, f"{label}: overall {doms['overall']!r} is better than the worst domain {worst!r}"))
    return found


def check_charting(project: Path, humans: list[str]) -> list[tuple[str, str, str]]:
    found: list[tuple[str, str, str]] = []
    ok = {h.casefold() for h in humans}
    for i, r in enumerate(screening.read_csv(project / CHARTING), start=2):
        e, v = (r.get("extracted_by") or "").strip(), (r.get("verified_by") or "").strip()
        loc = f"{CHARTING}:{i}"
        if not e or not v:
            found.append(("block", loc, f"line {i}: extracted_by and verified_by are both required"))
        elif e.casefold() == v.casefold():
            found.append(("block", loc, f"line {i}: extracted_by and verified_by are the same person"))
        elif e.casefold() not in ok or v.casefold() not in ok:
            found.append(("block", loc, f"line {i}: {e!r} or {v!r} is not a human reviewer in review.reviewers"))
    return found


def check(project: Path) -> list[tuple[str, str, str]]:
    project = Path(project)
    humans = screening.human_reviewers(project)
    scoping = projectcfg.read_project_yaml(project).get("design") == "scoping-review"
    found = check_extraction(project, humans)
    if scoping:
        found += check_charting(project, humans)
        if (project / ROB).is_file():
            found.append(("warn", f"{ROB}:1", "scoping reviews do not assess risk of bias (PRISMA-ScR); rob.csv is not used"))
    elif (project / ROB).is_file():
        found += check_rob(project, humans)
    return found


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    a = ap.parse_args(argv)
    project = Path(a.project)
    if not (project / "project.yaml").is_file():
        print(f"extract_check: {a.project} is not a project folder (no project.yaml)", file=sys.stderr)
        return 2
    try:
        found = check(project)
    except (OSError, ValueError) as e:
        print(f"extract_check: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    for sev, loc, msg in found:
        print(f"E-SCR {sev} {loc}: {msg}")
    blocks = sum(1 for f in found if f[0] == "block")
    print(f"extract_check: {blocks} block, {len(found) - blocks} warn")
    return 1 if blocks else 0


if __name__ == "__main__":
    sys.exit(main())
