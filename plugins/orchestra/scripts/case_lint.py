#!/usr/bin/env python3
"""E-CASE: anonymisation, consent and structure checks for a case report.

  python case_lint.py <project> [--strict]

Scans 01_case/dossier.md and the drafts in 06_writing/case-report/. Blocks: calendar dates (dd/mm/yyyy,
yyyy-mm-dd, "tháng 3 năm 2025", "March 2025"), exact ages ("45 tuổi", "45-year-old", "aged 45"; ranges and
decades pass), the institution or city named in project.yaml (institution.name, institution.city), identifiers
phi-guard reports as strong, unverified references in 01_case/similar-cases.csv (E-REF), and — with --strict, the
final-export path — consent not recorded in decisions.md as "CONSENT: obtained <form, who signed>". Warns:
consent missing (without --strict), a title with "rare"/"first"/"hiếm"/"đầu tiên" (and "case report" in BMJ mode),
a summary over target.word_limit, learning points outside 3-5 (BMJ mode), a similar-cases table with fewer than 3
rows, no timeline table, phi-guard weak identifiers.
Exit codes: 0 = no block; 1 = block findings; 2 = usage or I/O error.
"""
from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crolib import drafts, ledgers, projectcfg  # noqa: E402

DOSSIER = "01_case/dossier.md"
SIMILAR = "01_case/similar-cases.csv"
DRAFTS = "06_writing/case-report"
SIMILAR_COLS = ("ref_id", "age_range", "sex", "presentation", "key_finding", "treatment", "outcome")
MONTH = (r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sep(?:t(?:ember)?)?"
         r"|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)")
DATES = [re.compile(r"\b\d{1,2}[/.-]\d{1,2}[/.-](?:19|20)\d{2}\b"),
         re.compile(r"\b(?:19|20)\d{2}-\d{1,2}-\d{1,2}\b"),
         re.compile(r"(?i)\btháng\s+\d{1,2}(?:\s+năm\s+|\s*/\s*)(?:19|20)\d{2}\b"),
         re.compile(rf"\b(?:\d{{1,2}}\s+)?{MONTH}\.?\s+(?:\d{{1,2}},?\s+)?(?:19|20)\d{{2}}\b")]
AGES = [re.compile(r"(?i)(?<![\d–—-])\b\d{1,3}\s*(?:(?:tháng|ngày)\s+)?tuổi\b"),
        re.compile(r"(?i)\b\d{1,3}[- ](?:year|month|week|day)[- ]old\b"),
        re.compile(r"(?i)\baged\s+\d{1,3}\b"),
        re.compile(r"(?i)\b\d{1,3}\s+(?:years?|months?)\s+of\s+age\b")]
CONSENT = re.compile(r"(?im)^\s*(?:[-*]\s+)?CONSENT:\s*obtained\b[ \t]*[,:;-]?[ \t]*(\S.*)$")
TITLE_WORDS = [("rare", r"\brare\b"), ("first", r"\bfirst\b"), ("hiếm", r"hiếm"), ("đầu tiên", r"đầu tiên")]
TIMELINE = re.compile(r"(?i)timeline|dòng thời gian|diễn tiến theo thời gian")
BULLET = re.compile(r"^\s*(?:[-*]|\d+\.)\s+\S")
RELTIME = [re.compile(r"(?i)\b(?:days?|weeks?|months?|hours?|years?|ngày|tuần|tháng|giờ|năm)\s*(?:thứ\s*)?[+−-]?\s*\d+\b"),
           re.compile(r"(?i)(?<![\w.])[+−]\d+\b"),
           re.compile(r"(?i)\b\d+\s*(?:days?|weeks?|months?|hours?)\s+(?:later|after|before|earlier)\b"),
           re.compile(r"(?i)\b(?:after|within|for|over)\s+\d+\s*(?:days?|weeks?|months?|hours?)\b"),
           re.compile(r"(?i)\b(?:sau|trong|trước)\s+\d+\s*(?:ngày|tuần|tháng|giờ)\b"),
           re.compile(r"(?i)\b\d+\s*(?:ngày|tuần|tháng|giờ)\s+(?:sau|trước)\b")]


def bmj_mode(project: Path) -> bool:
    return str(projectcfg.get(project, "target.journal_style", "") or "").casefold() == "bmj"


def mask_relative_time(text: str) -> str:
    """Blank out relative-time tokens (day +3, ngày 14, 3 days later ...) keeping the length (plan D20)."""
    for rx in RELTIME:
        text = rx.sub(lambda m: " " * len(m.group(0)), text)
    return text


def consent_recorded(project: Path) -> bool:
    p = Path(project) / "decisions.md"
    return p.is_file() and CONSENT.search(p.read_text(encoding="utf-8-sig")) is not None


def _files(project: Path) -> list[Path]:
    out = [project / DOSSIER] if (project / DOSSIER).is_file() else []
    d = project / DRAFTS
    if d.is_dir():
        out += sorted((p for p in d.glob("*.md") if p.is_file() and drafts.is_draft(p.name)), key=lambda p: p.name)
    return out


def _rel(project: Path, p: Path) -> str:
    return p.resolve().relative_to(project.resolve()).as_posix()


def _words(path: Path) -> int:
    text = re.sub(r"<!--.*?-->", " ", path.read_text(encoding="utf-8-sig"), flags=re.S)
    return sum(len(ln.split()) for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#"))


def _phi(project: Path, files: list[Path]) -> list[tuple]:
    import audit  # lazy: audit.py imports this module
    script = audit.find_phi_scan()
    if script is None:
        return [("E-CASE", "warn", f"{DRAFTS}:1", "phi-guard not found; identifiers not scanned (install phi-guard)")]
    r = subprocess.run([sys.executable, str(script), "--file", *map(str, files)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode not in (0, 1):
        return [("E-CASE", "warn", f"{DRAFTS}:1", f"phi_scan could not run (exit {r.returncode})")]
    out = []
    for line in r.stdout.splitlines():
        m = audit.PHI_LINE.match(line.strip())
        if m:
            loc = Path(m.group(2))
            try:
                rel = _rel(project, loc) if loc.is_absolute() else loc.as_posix()
            except ValueError:
                rel = loc.as_posix()
            out.append(("E-CASE", m.group(1), f"{rel}:{m.group(3)}", f"possible patient identifier: {m.group(4)}"))
    return out


def lint(project: Path, strict: bool = False, phi: bool = True) -> list[tuple[str, str, str, str]]:
    import audit  # lazy, see _phi
    project = Path(project)
    found: list[tuple[str, str, str, str]] = []
    files = _files(project)
    names = [str(projectcfg.get(project, k) or "").strip() for k in ("institution.name", "institution.city")]
    names = [n for n in names if len(n) >= 3]
    for f in files:
        rel = _rel(project, f)
        for i, line in enumerate(f.read_text(encoding="utf-8-sig").splitlines(), 1):
            for rx in DATES:
                for m in rx.finditer(line):
                    found.append(("E-CASE", "block", f"{rel}:{i}", f'calendar date "{m.group(0)}"; use relative time '
                                                                   "(day 0, day +3, week 6)"))
            for rx in AGES:
                for m in rx.finditer(line):
                    found.append(("E-CASE", "block", f"{rel}:{i}", f'exact age "{m.group(0)}"; use a range '
                                                                   '("in her 40s", "40–49 tuổi")'))
            for n in names:
                if n.casefold() in line.casefold():
                    found.append(("E-CASE", "block", f"{rel}:{i}", f'names the institution or city "{n}" '
                                                                   "(project.yaml institution); remove it"))
    if phi and files:
        found += _phi(project, files)
    if not consent_recorded(project):
        found.append(("E-CASE", "block" if strict else "warn", "decisions.md:1",
                      "consent not recorded: add 'CONSENT: obtained <form, who signed>' to decisions.md "
                      "(the final export is refused without it)"))
    bmj = bmj_mode(project)
    d = project / DRAFTS
    title = d / "00-title.md"
    if title.is_file():
        first = next((ln.lstrip("# ").strip() for ln in title.read_text(encoding="utf-8-sig").splitlines() if ln.strip()), "")
        words = TITLE_WORDS + ([("case report", r"case report")] if bmj else [])
        for word, rx in words:
            if re.search(rx, first, re.I):
                found.append(("E-CASE", "warn", f"{DRAFTS}/00-title.md:1", f"title contains '{word}'; journals "
                                                                           "discourage it (claim it only with evidence)"))
    limit = projectcfg.get(project, "target.word_limit")
    summary = d / ("01-summary.md" if bmj else "01-abstract.md")
    if summary.is_file() and isinstance(limit, str) and limit.isdigit() and _words(summary) > int(limit):
        found.append(("E-CASE", "warn", f"{DRAFTS}/{summary.name}:1",
                      f"{_words(summary)} words, over the {limit}-word limit (target.word_limit)"))
    lp = d / "09-learning-points.md"
    if bmj and lp.is_file():
        n = sum(1 for ln in lp.read_text(encoding="utf-8-sig").splitlines() if BULLET.match(ln))
        if not 3 <= n <= 5:
            found.append(("E-CASE", "warn", f"{DRAFTS}/09-learning-points.md:1", f"{n} learning points; BMJ asks for 3-5"))
    sim = project / SIMILAR
    if not sim.is_file():
        found.append(("E-CASE", "warn", f"{SIMILAR}:1", "no similar-cases table (01_case/similar-cases.csv)"))
    else:
        with open(sim, encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            missing = [c for c in SIMILAR_COLS if c not in (reader.fieldnames or [])]
            rows = list(reader)
        if missing:
            found.append(("E-CASE", "block", f"{SIMILAR}:1", f"missing column(s) {', '.join(missing)}"))
        if len(rows) < 3:
            found.append(("E-CASE", "warn", f"{SIMILAR}:1", f"similar-cases table has fewer than 3 rows ({len(rows)})"))
        refs = {r.get("id"): r for r in ledgers.load_references(project / "ledgers" / "references.json") if isinstance(r, dict)}
        for i, r in enumerate(rows, 2):
            why = audit.citation_problem(refs.get((r.get("ref_id") or "").strip()))
            if why:
                found.append(("E-REF", "block", f"{SIMILAR}:{i}", f"[@{r.get('ref_id')}] {why}"))
    has_timeline = any(TIMELINE.search(t) and any(ln.lstrip().startswith("|") for ln in t.splitlines())
                       for t in (p.read_text(encoding="utf-8-sig") for p in files if p.parent == d))
    if d.is_dir() and not has_timeline:
        found.append(("E-CASE", "warn", f"{DRAFTS}:1", "no timeline table (CARE item 7)"))
    return found


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args(argv)
    project = Path(a.project)
    if not (project / "project.yaml").is_file():
        print(f"case_lint: {a.project} is not a project folder (no project.yaml)", file=sys.stderr)
        return 2
    try:
        found = lint(project, a.strict)
    except (OSError, ValueError, csv.Error) as e:
        print(f"case_lint: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    for code, sev, loc, msg in found:
        print(f"{code} {sev} {loc}: {msg}")
    blocks = sum(1 for f in found if f[1] == "block")
    print(f"case_lint: {blocks} block, {len(found) - blocks} warn")
    return 1 if blocks else 0


if __name__ == "__main__":
    sys.exit(main())
