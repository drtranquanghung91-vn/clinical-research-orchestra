#!/usr/bin/env python3
"""SAP analysis register and E-STAT checks.

  python analysis_plan.py register <project>
  python analysis_plan.py check <project> [--text FILE ...]

check compares 05_analysis/output/results.json with the "Analysis register" table in 03_protocol/sap.md
and with POST-HOC / DEVIATION lines in decisions.md; --text also checks that post-hoc results are labelled
in a results document and warns on causal wording with an observational design.
Exit codes: 0 = clean (warnings allowed); 1 = block findings, or register missing/invalid; 2 = usage or I/O.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crolib import projectcfg  # noqa: E402

HEADING = re.compile(r"(?im)^#{2,3}\s.*(analysis register|đăng ký phân tích).*$")
DECL = re.compile(r"(?m)^\s*(?:[-*]\s+)?(POST-HOC|DEVIATION) (A\d+):")
PLACEHOLDER = re.compile(r"\{\{(R-A\d+-\d{3})(?:\.\w+)?\}\}")
LABEL = re.compile(r"(?i)post[- ]hoc|exploratory|thăm dò|hậu kiểm")
CAUSAL = re.compile(r"(?i)\b(?:causes?|caused|leads? to|led to|prevents?|prevented)\b|gây ra|dẫn đến|làm giảm|làm tăng|phòng ngừa")
OBSERVATIONAL = {"cohort", "case-control", "cross-sectional", "diagnostic-accuracy", "prediction-model"}


def parse_register(sap_text: str) -> list[dict]:
    m = HEADING.search(sap_text)
    if not m:
        raise ValueError("no 'Analysis register' heading in the SAP")
    rows = []
    for line in sap_text[m.end():].splitlines():
        if line.strip().startswith("|"):
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
        elif rows:
            break
    if len(rows) < 3:
        raise ValueError("the analysis register table has no rows")
    header = [h.lower() for h in rows[0]]
    reg, seen = [], set()
    for cells in rows[2:]:
        rec = dict(zip(header, cells))
        aid = rec.get("id", "")
        if not re.fullmatch(r"A\d+", aid):
            raise ValueError(f"register ID '{aid}' must be A<n>")
        if aid in seen:
            raise ValueError(f"register ID {aid} appears twice")
        seen.add(aid)
        reg.append(rec)
    return reg


def declared(decisions_text: str) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {"POST-HOC": set(), "DEVIATION": set()}
    for kind, aid in DECL.findall(decisions_text):
        out[kind].add(aid)
    return out


def _paragraphs(text: str):
    start, buf = 1, []
    for n, line in enumerate(text.split("\n"), start=1):
        if line.strip():
            if not buf:
                start = n
            buf.append(line)
        elif buf:
            yield start, "\n".join(buf)
            buf = []
    if buf:
        yield start, "\n".join(buf)


class InputError(Exception):
    """Unusable input file (exit 2)."""


def _load_results(path: Path) -> list:
    try:
        doc = json.loads(path.read_text(encoding="utf-8-sig"))
    except ValueError as e:  # JSONDecodeError, UnicodeDecodeError
        raise InputError(f"{path} is not valid JSON/UTF-8: {e}")
    if not isinstance(doc, dict):
        raise InputError(f"{path}: top level must be a JSON object")
    results = doc.get("results", [])
    if not isinstance(results, list):
        raise InputError(f"{path}: 'results' must be a list")
    return results


def check(project: Path, text_files: list[Path]) -> list[tuple[str, str, str]]:
    reg_ids = {r["id"] for r in parse_register((project / "03_protocol" / "sap.md").read_text(encoding="utf-8-sig"))}
    results = _load_results(project / "05_analysis" / "output" / "results.json")
    dec_path = project / "decisions.md"
    dec = declared(dec_path.read_text(encoding="utf-8-sig") if dec_path.is_file() else "")
    found: list[tuple[str, str, str]] = []
    reported = set()
    for n, r in enumerate(results, start=1):
        if not isinstance(r, dict) or not isinstance(r.get("id"), str) or not isinstance(r.get("analysis_id"), str):
            found.append(("block", "results.json", f"record {n} is malformed (needs an object with string id and analysis_id)"))
            continue
        rid, aid, status = r.get("id"), r.get("analysis_id"), r.get("status")
        reported.add(aid)
        if status == "prespecified" and aid != "A0" and aid not in reg_ids:
            found.append(("block", "results.json", f"{rid}: prespecified result for {aid}, which is not in the analysis register"))
        if status in ("posthoc", "deviation"):
            key = "POST-HOC" if status == "posthoc" else "DEVIATION"
            if aid not in dec[key]:
                found.append(("block", "results.json", f'{rid}: {status} result for {aid} has no "{key} {aid}:" line in decisions.md'))
    for aid in sorted(reg_ids - reported - dec["DEVIATION"], key=lambda a: int(a[1:])):
        found.append(("block", "03_protocol/sap.md",
                      f'{aid} is in the register but has no result and no "DEVIATION {aid}:" line (selective reporting)'))
    status_of = {r.get("id"): r.get("status") for r in results if isinstance(r, dict)}
    observational = projectcfg.read_project_yaml(project).get("design") in OBSERVATIONAL
    for f in text_files:
        text = Path(f).read_text(encoding="utf-8-sig")
        for start, para in _paragraphs(text):
            ids = PLACEHOLDER.findall(para)
            post = [i for i in ids if status_of.get(i) == "posthoc"]
            if post and not LABEL.search(para):
                found.append(("block", f"{f}:{start}", f"post-hoc result {post[0]} is not labelled (post-hoc / exploratory / thăm dò / hậu kiểm)"))
            if observational:
                m = CAUSAL.search(para)
                if m:
                    found.append(("warn", f"{f}:{start}", f'causal wording "{m.group(0)}" with an observational design'))
    return found


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["register", "check"])
    ap.add_argument("project")
    ap.add_argument("--text", nargs="*", default=[])
    a = ap.parse_args(argv)
    project = Path(a.project)
    try:
        if a.cmd == "register":
            sap = (project / "03_protocol" / "sap.md").read_text(encoding="utf-8-sig")
            try:
                print(json.dumps(parse_register(sap), ensure_ascii=False, indent=2))
            except ValueError as e:
                print(f"analysis_plan: {e}", file=sys.stderr)
                return 1
            return 0
        found = check(project, [Path(t) for t in a.text])
    except (InputError, UnicodeDecodeError) as e:
        print(f"analysis_plan: {e}", file=sys.stderr)
        return 2
    except ValueError as e:
        print(f"analysis_plan: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"analysis_plan: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    for sev, loc, msg in found:
        print(f"E-STAT {sev} {loc}: {msg}")
    blocks = sum(1 for s, _, _ in found if s == "block")
    print(f"analysis_plan: {blocks} block, {len(found) - blocks} warn")
    return 1 if blocks else 0


if __name__ == "__main__":
    sys.exit(main())
