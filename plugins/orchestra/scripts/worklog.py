"""Revise loop for the drafts of a deliverable (thesis, manuscript, case-report, review): scores reviewer reports, decides KEEP / REVERT / STOP,
snapshots each round, restores a kept round, and drafts out/author-decisions.md. Standard library only.

Commands
  worklog.py score <project> <d> --round N [--json]
      Prints the round, the 8 scores, notes, requests, `total T/16` and, as the last line, KEEP, REVERT or STOP;
      exit 0 for any decision. Exit 2 (nothing recorded) on: round != last + 1, round > 3, loop already stopped,
      no drafts, missing report (reviews/<agent>-<d>.md, or the legacy reviews/<agent>.md holding a scores block for <d>), missing scores block, bad score value, stale digest, missing checklist,
      consistency/lint failure.
  worklog.py revert <project> <d> [--to N]
      Restores reviews/rounds/<d>/r<K>/ (K = last kept round or N) exactly: snapshot files are copied back and
      tracked files absent from the snapshot are deleted (they remain in the later round's snapshot); appends
      an `events` entry; exit 0.
  worklog.py digest <project> <d>
      Prints `drafts-digest: <d> <sha256>`; exit 0 (2 when there are no drafts).
  worklog.py decisions <project>
      Writes out/author-decisions.md (exit 0); when the existing file differs from the last generated one it
      writes reviews/tmp/author-decisions.new.md instead and exits 1.

Decision rules: higher than the kept round keeps; lower reverts; equal with a lost criterion reverts; equal
without a loss stops; a total of 16 or round 3 stops. Guideline, consistency and prose are measured here.

reviews/worklog.json: {"rounds": [{"deliverable", "round", "at", "scores": {8 keys}, "total", "max": 16,
"decision", "kept", "compared_with", "compared_total", "drafts_digest", "files_changed",
"requests": [{"agent", "text"}], "notes"}], "events": [...], "decisions_sha256": "..."}

Snapshot layout: reviews/rounds/<d>/r<N>/<draft files and order.txt>, r<N>/reviews/<report files under their own names>,
r<N>/reviews/guideline-checklist.json (a copy of the deliverable's reviews/guideline-checklist-<d>.json, or of
the legacy reviews/guideline-checklist.json when that one is for <d>).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crolib import drafts, projectcfg, reviews  # noqa: E402
import consistency_audit  # noqa: E402
import guideline_checklist  # noqa: E402
import lint_prose  # noqa: E402

ORCH = Path(__file__).resolve().parents[1]
LOG = "reviews/worklog.json"
MAX_ROUNDS = 3
MAX_TOTAL = 2 * len(reviews.CRITERIA)
SCRIPTED = ("guideline", "consistency", "prose")
HEAD = re.compile(r"(?:Giả định\s*/\s*Assumptions|Assumptions\s*/\s*Giả định)", re.I)
QUOTE = re.compile(r"^\s*>[ \t]?")
BULLET = re.compile(r"^\s*[-*]\s+(.*)")
WAIVE = re.compile(r"^\s*(?:[-*]\s+)?(WAIVE G\d:.*?)\s*$")
SOURCES = ("01_question/question.md", "03_protocol/protocol.md", "03_protocol/sample-size.md",
           "03_protocol/sap.md", "decisions.md")
TEXT = {
    "vi": {"title": "# Quyết định của tác giả",
           "note": "> Bản nháp do `worklog.py decisions` tạo. Tác giả đọc, ghi quyết định và chịu trách nhiệm; "
                   "công cụ không quyết định thay tác giả.",
           "req": "## 1. Yêu cầu phân tích mới (chưa đưa vào bài)", "ask": "Quyết định của tác giả: …",
           "ass": "## 2. Giả định / Assumptions", "waive": "## 3. Miễn cổng (WAIVE)", "none": "- Không có.",
           "round": "vòng", "thesis": "luận văn", "manuscript": "bài báo",
           "case-report": "báo cáo ca bệnh", "review": "bài tổng quan"},
    "en": {"title": "# Author decisions",
           "note": "> Draft written by `worklog.py decisions`. The author records each decision and is responsible "
                   "for it; the tool decides nothing.",
           "req": "## 1. Requests for new analyses (not in the text)", "ask": "Author's decision: …",
           "ass": "## 2. Assumptions (Giả định / Assumptions)", "waive": "## 3. Gate waivers (WAIVE)", "none": "- None.",
           "round": "round", "thesis": "thesis", "manuscript": "manuscript",
           "case-report": "case report", "review": "review"},
}


class UsageError(Exception):
    """Exit 2 with this message; nothing is recorded."""


def _now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def load_log(project: Path) -> dict:
    p = Path(project) / LOG
    if not p.is_file():
        return {"rounds": [], "events": []}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except ValueError as e:
        raise UsageError(f"{LOG} is unreadable: {e}") from e
    if not isinstance(data, dict):
        raise UsageError(f"{LOG} must be a JSON object")
    data.setdefault("rounds", [])
    data.setdefault("events", [])
    if not isinstance(data["rounds"], list) or not isinstance(data["events"], list):
        raise UsageError(f"{LOG}: 'rounds' and 'events' must be lists")
    for e in data["rounds"]:
        if (not isinstance(e, dict) or type(e.get("round")) is not int
                or e.get("deliverable") not in drafts.DELIVERABLES):
            raise UsageError(f"{LOG}: every round needs an integer 'round' and a known 'deliverable'")
    return data


def save_log(project: Path, log: dict) -> None:
    path = Path(project) / LOG
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(log, ensure_ascii=False, indent=2) + "\n")
    os.replace(tmp, path)


def round_dir(project: Path, deliverable: str, n: int) -> Path:
    return Path(project) / "reviews" / "rounds" / deliverable / f"r{n}"


def guideline_score(project: Path, deliverable: str) -> tuple[int, str]:
    p = guideline_checklist.checklist_path(project, deliverable)
    rel = guideline_checklist.rel_path(project, p)
    if not p.is_file():
        raise UsageError(f"{rel} not found: run reporting-guideline-checker on the {deliverable} first")
    try:
        data = json.loads(p.read_text(encoding="utf-8-sig"))
    except ValueError as e:
        raise UsageError(f"{rel} is unreadable: {e}") from e
    said = data.get("deliverable") if isinstance(data, dict) else None
    if said and said != deliverable:
        raise UsageError(f"{rel} is for the {said}, not the {deliverable}: "
                         f"rerun reporting-guideline-checker on the {deliverable}")
    entries = data.get("items", {}) if isinstance(data, dict) else {}
    absent = sum(1 for e in entries.values() if isinstance(e, dict) and e.get("status") == "absent")
    items = ORCH / "references" / "reporting-guidelines" / "items" / f"{data.get('guideline', '')}.json"
    if items.is_file():
        absent += sum(1 for it in json.loads(items.read_text(encoding="utf-8"))["items"] if it["id"] not in entries)
    return (2 if absent == 0 else 1 if absent <= 3 else 0), f"{absent} absent item(s)"


def consistency_score(project: Path) -> tuple[int, str]:
    try:
        found = consistency_audit.audit(Path(project))
    except (OSError, ValueError) as e:
        raise UsageError(f"consistency_audit could not run: {e}") from e
    blocks = sum(1 for sev, _, _ in found if sev == "block")
    warns = len(found) - blocks
    return (0 if blocks else 1 if warns else 2), f"{blocks} E-CONS block, {warns} warn"


def prose_score(project: Path, deliverable: str) -> tuple[int, str]:
    hits = words = 0
    p00 = False
    for p in drafts.draft_files(project, deliverable):
        r = lint_prose.lint_file(str(p), "auto")
        hits, words = hits + r["hits"], words + r["words"]
        p00 = p00 or any(f["code"] == "P00" for f in r["findings"])
    per200 = hits * 200.0 / words if words else 0.0
    return (0 if p00 else 2 if per200 <= 1 else 1), f"{hits} pattern hits in {words} words"


def _decide(scores: dict, total: int, rnd: int, kept: dict | None) -> str:
    if kept is not None:
        loss = [c for c in reviews.CRITERIA if scores[c] < kept["scores"].get(c, 0)]
        if total < kept["total"] or (total == kept["total"] and loss):
            return "REVERT"
        if total == kept["total"]:
            return "STOP"
    if total == MAX_TOTAL or rnd >= MAX_ROUNDS:
        return "STOP"
    return "KEEP"


def snapshot(project: Path, deliverable: str, n: int) -> Path:
    dest = round_dir(project, deliverable, n)
    if dest.exists():
        shutil.rmtree(dest)
    (dest / "reviews").mkdir(parents=True)
    for p in drafts.tracked_files(project, deliverable):
        shutil.copyfile(p, dest / p.name)
    for agent in reviews.REVIEWERS:
        src = reviews.report_path(project, agent, deliverable)
        if src.is_file():
            shutil.copyfile(src, dest / "reviews" / src.name)
    gl = guideline_checklist.checklist_path(project, deliverable)
    if gl.is_file():
        shutil.copyfile(gl, dest / "reviews" / "guideline-checklist.json")
    return dest


def _changed(snap: Path, prev: Path | None) -> list[str]:
    now = {p.name: _sha(p) for p in snap.iterdir() if p.is_file()}
    before = {p.name: _sha(p) for p in prev.iterdir() if p.is_file()} if prev and prev.is_dir() else {}
    return sorted(n for n in set(now) | set(before) if now.get(n) != before.get(n))


def score(project: Path, deliverable: str, rnd: int) -> dict:
    project = Path(project)
    log = load_log(project)
    mine = [e for e in log["rounds"] if e.get("deliverable") == deliverable]
    last = max((e["round"] for e in mine), default=0)
    if mine and mine[-1].get("decision") in ("REVERT", "STOP"):
        raise UsageError(f"the {deliverable} loop stopped at round {last} ({mine[-1]['decision']}); no further rounds")
    if rnd != last + 1:
        raise UsageError(f"--round must be {last + 1} for the {deliverable}")
    if rnd > MAX_ROUNDS:
        raise UsageError(f"at most {MAX_ROUNDS} rounds")
    if not drafts.draft_files(project, deliverable):
        raise UsageError(f"no drafts in 06_writing/{deliverable}/")
    current = drafts.digest(project, deliverable)
    scores: dict = {}
    said: dict = {}
    notes: list = []
    requests: list = []
    for agent, (_, crits) in reviews.REVIEWERS.items():
        path = reviews.report_path(project, agent, deliverable)
        rel = path.relative_to(project).as_posix()
        if not path.is_file():
            raise UsageError(f"{rel} not found: run the {agent} agent on the {deliverable} and save its reply there")
        parsed = reviews.parse_report(path.read_text(encoding="utf-8-sig"))
        if parsed["bad_scores"]:
            raise UsageError(f"{rel} has a malformed ```scores block (not a JSON object); fix it and rerun {agent}")
        if sum(1 for b in parsed["scores"] if b.get("deliverable") == deliverable) > 1:
            raise UsageError(f"{rel} has more than one ```scores block for the {deliverable}; keep one")
        block = reviews.scores_for(parsed, deliverable)
        if block is None:
            raise UsageError(f"{rel} has no ```scores block for the {deliverable}")
        if parsed["digests"].get(deliverable) != current:
            raise UsageError(f"{rel}: its drafts-digest does not match the current {deliverable} drafts; rerun {agent}")
        for c in crits:
            v = block.get(c)
            if c in SCRIPTED:
                if v is not None:
                    said[c] = v
                continue
            if type(v) is not int or v not in (0, 1, 2):
                raise UsageError(f"{rel}: '{c}' must be 0, 1 or 2 (got {v!r})")
            scores[c] = v
        requests += [{"agent": agent, "text": t} for t in parsed["requests"]]
    for key, (val, why) in (("guideline", guideline_score(project, deliverable)), ("consistency", consistency_score(project)),
                            ("prose", prose_score(project, deliverable))):
        scores[key] = val
        notes.append(f"{key} {val}: {why}")
        if key in said and said[key] != val:
            notes.append(f"{key}: the reviewer gave {said[key]}, the script measured {val}; the script value is used")
    total = sum(scores[c] for c in reviews.CRITERIA)
    kept = next((e for e in reversed(mine) if e.get("kept")), None)
    decision = _decide(scores, total, rnd, kept)
    prev = round_dir(project, deliverable, last) if last else None
    snap = snapshot(project, deliverable, rnd)
    entry = {"deliverable": deliverable, "round": rnd, "at": _now(),
             "scores": {c: scores[c] for c in reviews.CRITERIA}, "total": total, "max": MAX_TOTAL,
             "decision": decision, "kept": decision != "REVERT",
             "compared_with": kept["round"] if kept else None, "compared_total": kept["total"] if kept else None,
             "drafts_digest": current, "files_changed": _changed(snap, prev), "requests": requests, "notes": notes}
    log["rounds"].append(entry)
    save_log(project, log)
    return entry


def unscored_reports(project: Path, deliverable: str) -> tuple[int, list[str]]:
    """(last scored round, reports for <d> whose bytes differ from that round's snapshot copy; all of them when no
    round is scored). Audit warns on each (A1: one scored round per reviewer pass)."""
    project = Path(project)
    mine = [e for e in load_log(project)["rounds"] if e.get("deliverable") == deliverable]
    last = max((e["round"] for e in mine), default=0)
    out = []
    for agent in reviews.REVIEWERS:
        p = reviews.report_path(project, agent, deliverable)
        if not p.is_file() or reviews.scores_for(reviews.parse_report(p.read_text(encoding="utf-8-sig")), deliverable) is None:
            continue
        snap = round_dir(project, deliverable, last) / "reviews" / p.name if last else None
        if snap is None or not snap.is_file() or _sha(snap) != _sha(p):
            out.append(p.relative_to(project).as_posix())
    return last, out


def revert(project: Path, deliverable: str, to: int | None = None) -> dict:
    project = Path(project)
    log = load_log(project)
    mine = [e for e in log["rounds"] if e.get("deliverable") == deliverable]
    if to is None:
        kept = [e for e in mine if e.get("kept")]
        if not kept:
            raise UsageError(f"no kept round of the {deliverable} to revert to")
        to = kept[-1]["round"]
    target = next((e for e in mine if e["round"] == to), None)
    if target is not None and not target.get("kept"):
        raise UsageError(f"round {to} of the {deliverable} was itself reverted; choose a kept round")
    snap = round_dir(project, deliverable, to)
    if not snap.is_dir():
        raise UsageError(f"snapshot reviews/rounds/{deliverable}/r{to} not found")
    base = drafts.folder(project, deliverable)
    want = sorted(p.name for p in snap.iterdir() if p.is_file())
    removed = []
    for p in drafts.tracked_files(project, deliverable):
        if p.name not in want:
            p.unlink()
            removed.append(p.name)
    for name in want:
        shutil.copyfile(snap / name, base / name)
    event = {"deliverable": deliverable, "at": _now(), "event": "revert", "to_round": to,
             "restored": want, "removed": removed}
    log["events"].append(event)
    save_log(project, log)
    return event


def assumptions(project: Path) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for rel in SOURCES:
        p = Path(project) / rel
        if not p.is_file():
            continue
        lines = [QUOTE.sub("", ln) for ln in p.read_text(encoding="utf-8-sig").splitlines()]
        i = 0
        while i < len(lines):
            m0 = HEAD.search(lines[i])
            if not m0:
                i += 1
                continue
            before = len(out)
            j, skipped = i + 1, 0
            while j < len(lines) and lines[j].strip() and not BULLET.match(lines[j]) and skipped < 3:
                j, skipped = j + 1, skipped + 1
            while j < len(lines) and lines[j].strip():
                m = BULLET.match(lines[j])
                if m:
                    out.append((f"{rel}:{j + 1}", m.group(1).strip()))
                elif len(out) > before and lines[j][:1] in (" ", "\t"):
                    out[-1] = (out[-1][0], out[-1][1] + " " + lines[j].strip())
                else:
                    break
                j += 1
            if len(out) == before:
                # a prose box: the whole paragraph is one assumption
                k = i + 1
                while k < len(lines) and lines[k].strip():
                    k += 1
                para = " ".join(ln.strip() for ln in [lines[i][m0.end():]] + lines[i + 1:k] if ln.strip())
                para = para.lstrip("*_ .:").strip()
                if para:
                    out.append((f"{rel}:{i + 1}", para))
                j = k
            i = max(j, i + 1)
    return out


def waivers(project: Path) -> list[tuple[str, str]]:
    p = Path(project) / "decisions.md"
    if not p.is_file():
        return []
    return [(f"decisions.md:{n}", m.group(1)) for n, ln in enumerate(p.read_text(encoding="utf-8-sig").splitlines(), 1)
            if (m := WAIVE.match(ln))]


def decisions_text(project: Path, log: dict) -> str:
    t = TEXT["vi" if projectcfg.output_lang(project) == "vi" else "en"]
    lines = [t["title"], "", t["note"], "", t["req"], ""]
    seen, reqs = set(), []
    for e in log["rounds"]:
        for r in e.get("requests", []):
            key = (e["deliverable"], r["text"])
            if key not in seen and not reviews.is_none(r["text"]):   # "none — …" logged before the fix
                seen.add(key)
                reqs.append(f"- [{t[e['deliverable']]}, {t['round']} {e['round']}, {r['agent']}] {r['text']} — {t['ask']}")
    lines += reqs or [t["none"]]
    lines += ["", t["ass"], ""]
    lines += [f"- {text} (`{loc}`)" for loc, text in assumptions(project)] or [t["none"]]
    lines += ["", t["waive"], ""]
    lines += [f"- `{text}` (`{loc}`)" for loc, text in waivers(project)] or [t["none"]]
    return "\n".join(lines) + "\n"


def write_decisions(project: Path) -> tuple[int, Path]:
    project = Path(project)
    log = load_log(project)
    text = decisions_text(project, log)
    out = project / "out" / "author-decisions.md"
    if out.is_file() and _sha(out) != log.get("decisions_sha256"):
        alt = project / "reviews" / "tmp" / "author-decisions.new.md"
        _write(alt, text)
        return 1, alt
    _write(out, text)
    log["decisions_sha256"] = _sha(out)
    save_log(project, log)
    return 0, out


def _print_round(e: dict) -> None:
    head = f"worklog: {e['deliverable']} round {e['round']}"
    if e["compared_with"]:
        head += f" (kept round {e['compared_with']}: {e['compared_total']}/{e['max']})"
    print(head)
    print(" · ".join(f"{c} {e['scores'][c]}" for c in reviews.CRITERIA))
    for n in e["notes"]:
        print(f"  note: {n}")
    for r in e["requests"]:
        print(f"  request ({r['agent']}): {r['text']} -> out/author-decisions.md (never into the text)")
    print(f"total {e['total']}/{e['max']}")
    if e["decision"] == "REVERT":
        print(f"next: worklog.py revert <project> {e['deliverable']} (restores round {e['compared_with']}); the loop stops")
    print(e["decision"])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["score", "revert", "digest", "decisions"])
    ap.add_argument("project")
    ap.add_argument("deliverable", nargs="?", choices=drafts.DELIVERABLES)
    ap.add_argument("--round", type=int, dest="rnd")
    ap.add_argument("--to", type=int)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    project = Path(a.project)
    if not project.is_dir():
        print(f"worklog: project folder {a.project} not found", file=sys.stderr)
        return 2
    try:
        if a.cmd != "decisions" and not a.deliverable:
            raise UsageError(f"{a.cmd} needs a deliverable ({', '.join(drafts.DELIVERABLES)})")
        if a.cmd == "digest":
            if not drafts.draft_files(project, a.deliverable):
                raise UsageError(f"no drafts in 06_writing/{a.deliverable}/")
            print(f"drafts-digest: {a.deliverable} {drafts.digest(project, a.deliverable)}")
            return 0
        if a.cmd == "score":
            if a.rnd is None:
                raise UsageError("score needs --round N")
            e = score(project, a.deliverable, a.rnd)
            if a.json:
                print(json.dumps(e, ensure_ascii=False, indent=2))
            else:
                _print_round(e)
            return 0
        if a.cmd == "revert":
            ev = revert(project, a.deliverable, a.to)
            print(f"worklog: {a.deliverable} restored to round {ev['to_round']}: {', '.join(ev['restored'])}"
                  + (f"; removed {', '.join(ev['removed'])} (kept in the later round's snapshot)" if ev["removed"] else ""))
            return 0
        code, path = write_decisions(project)
        rel = path.relative_to(project).as_posix()
        if code:
            print(f"worklog: out/author-decisions.md was edited after it was generated; not overwritten. New draft: {rel}")
            return 1
        print(f"worklog: wrote {rel}")
        return 0
    except UsageError as e:
        print(f"worklog: {e}", file=sys.stderr)
        return 2
    except (OSError, ValueError) as e:
        print(f"worklog: {type(e).__name__}: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
