#!/usr/bin/env python3
"""E-CASE: anonymisation, consent and structure checks for a case report.

  python case_lint.py <project> [--strict]

Scans 01_case/dossier.md and the drafts in 06_writing/case-report/. Blocks: calendar dates (dd/mm/yyyy,
yyyy-mm-dd, "tháng 3 năm 2025", "March 2025"), day and month without a year ("5 March", "ngày 5/3"), exact ages ("45 tuổi", "45-year-old", "aged 45"; ranges and
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
import unicodedata
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
ORD = r"(?:st|nd|rd|th)?"
DATES = [re.compile(r"\b\d{1,2}[/.-]\d{1,2}[/.-](?:19|20)\d{2}\b"),
         re.compile(r"\b(?:19|20)\d{2}[/.-]\d{1,2}[/.-]\d{1,2}\b"),
         re.compile(r"(?<![/.\d-])\b\d{1,2}/(?:19|20)\d{2}\b"),
         re.compile(r"(?i)\btháng\s+\d{1,2}(?:\s+năm\s+|\s*/\s*)(?:19|20)\d{2}\b"),
         re.compile(rf"\b(?:\d{{1,2}}{ORD}\s+(?:of\s+)?)?{MONTH}\.?\s+(?:\d{{1,2}}{ORD},?\s+)?(?:19|20)\d{{2}}\b")]
# day and month without a year: still dates the case (block, plan D24)
DAY_MONTH = [re.compile(rf"\b\d{{1,2}}{ORD}\s+(?:of\s+)?{MONTH}\b(?!\.?,?\s*(?:19|20)\d{{2}})"),
              re.compile(rf"\b{MONTH}\.?\s+\d{{1,2}}{ORD}\b(?!\s*,?\s*(?:19|20)\d{{2}})"),
              re.compile(r"(?i)\bngày\s+\d{1,2}\s+tháng\s+\d{1,2}\b(?!\s*(?:năm\s+|/)\s*(?:19|20)\d{2})"),
              re.compile(r"(?i)\bngày\s+\d{1,2}\s*/\s*\d{1,2}\b(?!\s*/\s*\d)")]
_NUM = r"\d{1,3}(?!\d)(?!\s*(?:[–—-]|to|đến)\s*\d)"
AGES = [re.compile(rf"(?i)\b{_NUM}\s*(?:(?:tháng|ngày)\s+)?tuổi\b"),
        re.compile(rf"(?i)\b{_NUM}[- ]?(?:(?:years?|yrs?|months?|weeks?|days?)[- ]old|y/?o)\b"),
        re.compile(rf"(?i)\bage(?:d)?(?:\s*:\s*|\s+){_NUM}\b"),
        re.compile(rf"(?i)\b{_NUM}\s+(?:years?|months?)\s+of\s+age\b")]
AGE_SKIP_BEFORE = re.compile(r"(?i)(?:[≥≤><–—-]|\b(?:over|under|above|below|older than|younger than|than|to|trên|dưới|từ|đến))\s*$")
AGE_SKIP_AFTER = re.compile(r"(?i)^\s*(?:(?:years?|yrs?|tuổi)\s*)?(?:(?:and|or)\s+(?:older|over|above|younger|under|below)|trở\s+(?:lên|xuống))")
CONSENT = re.compile(r"(?im)^\s*(?:[-*]\s+)?CONSENT:\s*obtained\b[ \t]*[,:;-]?[ \t]*(\S.*)$")
CONSENT_PLACEHOLDER = re.compile(r"(?i)<[^>]*>|\b(?:pending|not|tbd)\b|\bchưa\b")
TITLE_WORDS = [("rare", r"\brare\b"), ("first", r"\bfirst\b"), ("hiếm", r"hiếm"), ("đầu tiên", r"đầu tiên")]
TIMELINE = re.compile(r"(?i)timeline|dòng thời gian|diễn tiến theo thời gian")
BULLET = re.compile(r"^\s*(?:[-*]|\d+\.)\s+\S")
RELTIME = [re.compile(r"(?i)\b\d+\s*(?:days?|weeks?|months?|hours?)\s+(?:later|after|before|earlier)\b"),
           re.compile(r"(?i)\b(?:after|within|for|over)\s+\d+\s*(?:days?|weeks?|months?|hours?)\b"),
           re.compile(r"(?i)\b(?:sau|trong|trước)\s+\d+\s*(?:ngày|tuần|tháng|giờ)\b"),
           re.compile(r"(?i)\b\d+\s*(?:ngày|tuần|tháng|giờ)\s+(?:sau|trước)\b"),
           # "day +3", "ngày 14", "week 6", "D14": the only place a signed number is read as a day
           re.compile(r"(?<!\d\s)(?:(?i:\b(?:days?|weeks?|months?|hours?|years?|ngày|tuần|tháng|giờ|năm)\s*(?:thứ\s*)?)"
                      r"|(?<![\w])(?<!itamin )D\s*)[+−-]?\s*\d+\b"
                      r"(?!\s*(?i:lần|times?|doses?|tablets?|viên|liều))")]


def bmj_mode(project: Path) -> bool:
    return str(projectcfg.get(project, "target.journal_style", "") or "").casefold() == "bmj"


def mask_relative_time(text: str) -> str:
    """Blank out relative-time tokens (day +3, ngày 14, 3 days later ...) keeping the length (plan D20)."""
    for rx in RELTIME:
        text = rx.sub(lambda m: " " * len(m.group(0)), text)
    return text


FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")


def _outside_fences(text: str) -> str:
    """The text with every fenced code block (``` or ~~~) removed: an example there records nothing."""
    keep, fence = [], None
    for line in text.splitlines():
        m = FENCE.match(line)
        if fence is None:
            if m:
                fence = m.group(1)
            else:
                keep.append(line)
        elif m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and not line.strip()[len(m.group(1)):].strip():
            fence = None
    return "\n".join(keep)


def consent_recorded(project: Path) -> bool:
    p = Path(project) / "decisions.md"
    return p.is_file() and any(not CONSENT_PLACEHOLDER.search(m.group(1))
                               for m in CONSENT.finditer(_outside_fences(p.read_text(encoding="utf-8-sig"))))


def _fold(text: str) -> str:
    """Case- and diacritic-folded text (Huế -> hue, Hà Nội -> ha noi) for name matching."""
    t = text.replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c)).casefold()


def _name_in(name: str, line: str) -> bool:
    n = " ".join(_fold(name).split())
    return bool(n) and re.search(rf"(?<!\w){re.escape(n)}(?!\w)", " ".join(_fold(line).split())) is not None


def _exact_ages(line: str):
    for rx in AGES:
        for m in rx.finditer(line):
            if AGE_SKIP_BEFORE.search(line[:m.start()]) or AGE_SKIP_AFTER.match(line[m.end():]):
                continue
            yield m


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
            for rx in DAY_MONTH:
                for m in rx.finditer(line):
                    found.append(("E-CASE", "block", f"{rel}:{i}", f'day and month "{m.group(0)}" date the case even '
                                                                   "without a year; use relative time (day 0, day +3, week 6)"))
            for m in _exact_ages(line):
                found.append(("E-CASE", "block", f"{rel}:{i}", f'exact age "{m.group(0)}"; use a range '
                                                               '("in her 40s", "40–49 tuổi")'))
            for n in names:
                if _name_in(n, line):
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
