"""Audit a deliverable before export: one pass over every check, written to reviews/audit.md and reviews/audit.json.

CLI: audit.py <project> [thesis|manuscript] [--online] [--json]
  no deliverable = every deliverable with drafts. Exit 0 no block, 1 blocks, 2 usage / missing project / no drafts /
  --online network error / cannot write reviews/.
Checks (E-REF ledgers and citations, E-NUM, E-STAT, E-LIT, E-CONS, P-codes, E-RG, E-FMT, E-PHI, E-REV) are listed in
ROWS. reviews/audit.json records the sha256 of the tracked drafts, order.txt, referenced images and the ledgers that
exist; gate.py G4 and assemble.py --final refuse when any of them changed afterwards.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
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
from crolib import drafts, ledgers, reviews  # noqa: E402
import analysis_plan  # noqa: E402
import assemble  # noqa: E402
import check_numbers  # noqa: E402
import cite_render  # noqa: E402
import consistency_audit  # noqa: E402
import gate  # noqa: E402
import guideline_checklist  # noqa: E402
import lint_prose  # noqa: E402
import render_results  # noqa: E402
import review_lint  # noqa: E402

ORCH = Path(__file__).resolve().parents[1]
ROWS = [("ledgers", "E-REF"), ("citations", "E-REF"), ("results numbers", "E-NUM"), ("analysis declarations", "E-STAT"),
        ("literature synthesis", "E-LIT"), ("consistency", "E-CONS"), ("prose density", "P00"),
        ("guideline checklist", "E-RG"), ("sections and captions", "E-FMT"), ("identifiers", "E-PHI"),
        ("reviewer reports", "E-REV")]
ROWS_FILE = {"ledgers": "ledgers", "citations": "ledgers/references.json", "results numbers": "ledgers/results-ledger.json",
             "analysis declarations": "03_protocol/sap.md", "guideline checklist": "reviews/guideline-checklist-<deliverable>.json",
             "reviewer reports": "reviews"}
FIX = {
    "en": {"E-REF": "verify or replace the reference (verify_refs.py --write, search_lit.py); never edit its status by hand.",
           "E-NUM": "replace the typed number with its {{R-...}} placeholder, or mark it <!-- not-a-result: ... -->.",
           "E-STAT": "declare the post-hoc analysis or deviation in decisions.md, or label it in the text.",
           "E-LIT": "rewrite the chapter by theme, not paper by paper.",
           "E-CONS": "decide which source is right (the ledger first) and align the other places.",
           "P": "reduce the flagged prose pattern (prose-humanizer).",
           "E-RG": "add the missing guideline item or record why it does not apply; rerun reporting-guideline-checker.",
           "E-FMT": "add the missing section, fix caption numbering or the image, fill every [[AUTHOR: ...]] placeholder.",
           "E-PHI": "remove or de-identify the identifier, then rerun the audit.",
           "E-REV": "rerun the reviewer agent on the current drafts."},
    "vi": {"E-REF": "xác minh hoặc thay tài liệu tham khảo (verify_refs.py --write, search_lit.py); không sửa trạng thái bằng tay.",
           "E-NUM": "thay số gõ tay bằng ô {{R-...}}, hoặc đánh dấu <!-- not-a-result: ... --> nếu không phải kết quả.",
           "E-STAT": "ghi phân tích post-hoc hoặc sai lệch vào decisions.md, hoặc gắn nhãn trong văn bản.",
           "E-LIT": "viết lại chương theo chủ đề, không theo từng bài báo.",
           "E-CONS": "xác định nguồn đúng (sổ cái trước) rồi sửa các chỗ còn lại cho khớp.",
           "P": "giảm mẫu văn phong bị đánh dấu (prose-humanizer).",
           "E-RG": "bổ sung mục hướng dẫn còn thiếu hoặc ghi lý do không áp dụng; chạy lại reporting-guideline-checker.",
           "E-FMT": "thêm phần còn thiếu, sửa số thứ tự chú thích hoặc hình, điền mọi chỗ [[TÁC GIẢ: ...]].",
           "E-PHI": "xoá hoặc ẩn danh định danh, rồi chạy lại audit.",
           "E-REV": "chạy lại agent đánh giá trên bản thảo hiện tại."},
}
COMMENT = re.compile(r"<!--.*?-->", re.S)
PHI_LINE = re.compile(r"^E-PHI (block|warn) (.+):(\d+) (.+)$")
LEDGER_FILES = ("ledgers/references.json", "ledgers/results-ledger.json", "ledgers/claims.json")


class NetworkError(Exception):
    """--online could not reach the literature APIs (exit 2)."""


class Audit:
    def __init__(self, project: Path):
        self.project = Path(project)
        self.findings: list[dict] = []

    def rel(self, p) -> str:
        p = Path(p)
        if p.is_absolute():
            try:
                return p.resolve().relative_to(self.project.resolve()).as_posix()
            except ValueError:
                return p.as_posix()
        return p.as_posix()

    def add(self, check: str, code: str, level: str, loc: str, msg: str) -> None:
        path, sep, line = str(loc).rpartition(":")
        file, n = (path, int(line)) if sep and line.isdigit() else (str(loc), 1)
        self.findings.append({"check": check, "code": code, "level": level, "file": self.rel(file).replace("\\", "/"),
                              "line": n, "msg": msg})


def _masked(path: Path) -> str:
    return COMMENT.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), path.read_text(encoding="utf-8-sig"))


def citation_problem(rec: dict | None) -> str | None:
    if rec is None:
        return "is not in ledgers/references.json"
    if rec.get("retracted"):
        return "is retracted"
    if rec.get("source") == "manual":
        return None if str(rec.get("seen_in") or "").strip() else "is a manual record without 'seen_in'"
    vb = str(rec.get("verified_by") or "")
    return None if vb.endswith("VERIFIED") else f"is not verified (verified_by: {vb or 'none'}); run verify_refs.py --write or replace it"


def verify_online(project: Path, files: list[Path]) -> dict:
    r = subprocess.run([sys.executable, str(ORCH / "scripts" / "verify_refs.py"), str(project), "--json",
                        "--cite", *map(str, files)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode == 2:
        raise NetworkError(r.stderr.strip() or "verify_refs.py could not check every reference")
    return json.loads(r.stdout)


def find_phi_scan() -> Path | None:
    repo = ORCH.parent / "phi-guard" / "scripts" / "phi_scan.py"
    if repo.is_file():
        return repo
    cache = list((ORCH.parent.parent / "phi-guard").glob("*/scripts/phi_scan.py"))
    key = lambda p: tuple(int(x) for x in re.findall(r"\d+", p.parts[-3]))  # noqa: E731
    return max(cache, key=key) if cache else None


def check_citations(a: Audit, files: list[Path], online: bool) -> None:
    refs = {r.get("id"): r for r in ledgers.load_references(a.project / "ledgers" / "references.json") if isinstance(r, dict)}
    cited: set = set()
    for p in files:
        for i, line in enumerate(_masked(p).splitlines(), 1):
            for k in cite_render.cited_ids(line):
                cited.add(k)
                why = citation_problem(refs.get(k))
                if why:
                    a.add("citations", "E-REF", "block", f"{p}:{i}", f"[@{k}] {why}")
    if online and files:
        for r in verify_online(a.project, files).get("references", []):
            if r.get("id") in cited and r.get("status") not in ("VERIFIED", "MANUAL"):
                a.add("citations", "E-REF", "block", "ledgers/references.json:1",
                      f"{r['id']}: {r['status']} online ({'; '.join(r.get('notes', [])) or 'no detail'})")


def check_numbers_(a: Audit, d: str, files: list[Path]) -> None:
    path = a.project / "ledgers" / "results-ledger.json"
    results = json.loads(path.read_text(encoding="utf-8-sig")).get("results", []) if path.is_file() else []
    by_id = {r.get("id"): r for r in results if isinstance(r, dict)}
    lang = drafts.lang_of(a.project, d)
    for p in (f for f in files if drafts.results_bearing(f)):
        rendered, probs = render_results.render_text(p.read_text(encoding="utf-8-sig"), by_id, lang)
        for x in probs:
            line, _, msg = x.partition(": ")
            a.add("results numbers", "E-NUM", "block", f"{p}:{line}", msg)
        for n, tok in check_numbers.find_unmatched(rendered, results, lang):
            a.add("results numbers", "E-NUM", "block", f"{p}:{n}",
                  f"{tok} is not in the results ledger (use a {{{{R-…}}}} placeholder or <!-- not-a-result: … -->)")
        for n, sev, msg in check_numbers.check_derived(rendered, results):
            a.add("results numbers", "E-NUM", sev, f"{p}:{n}", msg)


def check_stat(a: Audit, files: list[Path]) -> None:
    texts = [p for p in files if drafts.results_bearing(p)]
    try:
        found = analysis_plan.check(a.project, texts)
    except Exception as e:  # noqa: BLE001 - InputError, ValueError, OSError, UnicodeDecodeError
        a.add("analysis declarations", "E-STAT", "block", "03_protocol/sap.md:1", f"cannot check analysis declarations: {e}")
        return
    for sev, loc, msg in found:
        loc = {"results.json": "05_analysis/output/results.json", "decisions.md": "decisions.md"}.get(loc, loc)
        a.add("analysis declarations", "E-STAT", sev, loc, msg)


def check_literature(a: Audit, files: list[Path]) -> None:
    for p in (f for f in files if drafts.is_literature(f)):
        rep = review_lint.lint(p.read_text(encoding="utf-8-sig"))
        if rep["blocking"]:
            a.add("literature synthesis", "E-LIT", "block", f"{p}:1",
                  f"written paper by paper: {len(rep['flagged'])}/{rep['paragraphs']} paragraphs; rewrite by theme")


def check_consistency(a: Audit) -> None:
    try:
        files = [p for p in consistency_audit._discover(a.project) if not p.name.endswith(".assembled.md")]
        found = consistency_audit.audit(a.project, files)
    except (OSError, ValueError) as e:
        a.add("consistency", "E-CONS", "block", "06_writing:1", f"consistency_audit could not run: {e}")
        return
    for sev, loc, msg in found:
        a.add("consistency", "E-CONS", sev, loc, msg)


def check_prose(a: Audit, files: list[Path]) -> None:
    for p in files:
        for f in lint_prose.lint_file(str(p), "auto")["findings"]:
            a.add("prose density", f["code"], f["level"], f"{p}:{f['line']}", f["message"])


def pick(project: Path, rel: str, d: str, accept) -> Path | None:
    cands = [project / rel] if (project / rel).is_file() else []
    snaps = (project / "reviews" / "rounds" / d).glob(f"r*/reviews/{Path(rel).name}")
    cands += sorted(snaps, key=lambda p: -int(p.parent.parent.name[1:]) if p.parent.parent.name[1:].isdigit() else 0)
    return next((c for c in cands if accept(c)), None)


def check_guideline(a: Audit, d: str) -> None:
    legacy = a.project / guideline_checklist.CHECKLIST

    def accept(c: Path) -> bool:
        try:
            got = json.loads(c.read_text(encoding="utf-8-sig")).get("deliverable", d)
        except (ValueError, AttributeError):
            return c == legacy
        return got == d
    # the deliverable's own checklist, else the legacy single file when it is for d, else the latest round copy
    per = a.project / guideline_checklist.deliverable_rel(d)
    path = per if per.is_file() else pick(a.project, guideline_checklist.CHECKLIST, d, accept)
    where = f"{guideline_checklist.rel_path(a.project, path) if path else guideline_checklist.deliverable_rel(d)}:1"
    if path is None:
        a.add("guideline checklist", "E-RG", "block", where,
              f"no guideline checklist for the {d}: run the reporting-guideline-checker agent")
        return
    try:
        found = guideline_checklist.check(a.project, checklist_path=path, deliverable=d)
    except guideline_checklist.NoItemList as e:
        a.add("guideline checklist", "E-RG", "warn", where, f"{e}; check the guideline by hand")
        return
    except guideline_checklist.InputError as e:
        a.add("guideline checklist", "E-RG", "block", where, str(e))
        return
    for sev, loc, msg in found:
        a.add("guideline checklist", "E-RG", sev, loc, msg)


def check_format(a: Audit, d: str) -> None:
    for code, level, loc, msg in assemble.format_findings(a.project, d, strict=True):
        a.add("sections and captions", code, level, loc, msg)


def check_phi(a: Audit, d: str, files: list[Path]) -> None:
    script = find_phi_scan()
    if script is None:
        a.add("identifiers", "E-PHI", "warn", f"06_writing/{d}:1", "phi-guard not found; identifiers not scanned (install phi-guard)")
        return
    assembled = drafts.folder(a.project, d) / f"{d}.assembled.md"
    targets = files + ([assembled] if assembled.is_file() else [])
    r = subprocess.run([sys.executable, str(script), "--file", *map(str, targets)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode not in (0, 1):
        a.add("identifiers", "E-PHI", "warn", f"06_writing/{d}:1",
              f"phi_scan could not run (exit {r.returncode}): {r.stderr.strip()}")
        return
    strong = 0
    for line in r.stdout.splitlines():
        m = PHI_LINE.match(line.strip())
        if m:
            strong += m.group(1) == "block"
            a.add("identifiers", "E-PHI", m.group(1), f"{m.group(2)}:{m.group(3)}", f"possible patient identifier: {m.group(4)}")
    if r.returncode == 1 and not strong:
        a.add("identifiers", "E-PHI", "block", f"06_writing/{d}:1", "phi_scan reported a strong finding that could not be read")


def check_reviews(a: Audit, d: str) -> None:
    current = drafts.digest(a.project, d)

    def parsed(c: Path) -> dict:
        return reviews.parse_report(c.read_text(encoding="utf-8-sig"))
    for agent, (rel, _) in reviews.REVIEWERS.items():
        path = pick(a.project, rel, d, lambda c: reviews.scores_for(parsed(c), d) is not None and d in parsed(c)["digests"])
        if path is None:
            a.add("reviewer reports", "E-REV", "block", f"{rel}:1",
                  f"no {agent} report for the {d} with a scores block and a drafts-digest line; run the agent")
        elif parsed(path)["digests"][d] != current:
            a.add("reviewer reports", "E-REV", "warn", f"{a.rel(path)}:1",
                  f"{agent} reviewed an earlier version of the {d} drafts (digest differs); rerun it if the content changed")


def run(project: Path, ds: list[str], named: str | None, online: bool) -> dict:
    a = Audit(project)
    def guarded(label: str, fn, *args) -> None:
        try:
            fn(*args)
        except NetworkError:
            raise
        except Exception as e:  # noqa: BLE001 - a crashed check must never look clean
            a.add(label, dict(ROWS)[label], "block", f"{ROWS_FILE.get(label, '06_writing')}:1",
                  f"{label} could not run: {type(e).__name__}: {e}")

    def ledger_check() -> None:
        for e in ledgers.check_project(a.project):
            a.add("ledgers", "E-REF", "block", f"ledgers/{e.split(':', 1)[0]}:1", e)
    guarded("ledgers", ledger_check)
    guarded("consistency", check_consistency, a)
    hashed: dict = {}
    root = a.project.resolve()
    for d in ds:
        files = drafts.draft_files(a.project, d)
        guarded("citations", check_citations, a, files, online)
        guarded("results numbers", check_numbers_, a, d, files)
        guarded("analysis declarations", check_stat, a, files)
        guarded("literature synthesis", check_literature, a, files)
        guarded("prose density", check_prose, a, files)
        guarded("guideline checklist", check_guideline, a, d)
        guarded("sections and captions", check_format, a, d)
        guarded("identifiers", check_phi, a, d, files)
        guarded("reviewer reports", check_reviews, a, d)
        for p in gate.export_files(a.project, d):
            try:
                hashed[p.resolve().relative_to(root).as_posix()] = gate.sha256(p)
            except ValueError:
                pass            # outside the project: gate skips it too
    hashed.update({rel: gate.sha256(a.project / rel) for rel in LEDGER_FILES if (a.project / rel).is_file()})
    order = {label: i for i, (label, _) in enumerate(ROWS)}
    a.findings.sort(key=lambda f: order.get(f["check"], 99))
    blocks = sum(1 for f in a.findings if f["level"] == "block")
    return {"deliverable": named or "all", "deliverables": ds, "at": dt.datetime.now().isoformat(timespec="seconds"),
            "blocks": blocks, "warns": len(a.findings) - blocks, "online": online, "files": hashed, "findings": a.findings}


def line_of(f: dict) -> str:
    return f"{f['code']} {f['level']} {f['file']}:{f['line']}: {f['msg']}"


def markdown(data: dict, lang: str = "en") -> str:
    mode = "online" if data["online"] else "offline (stored ledger statuses)"
    out = [f"# Audit: {', '.join(data['deliverables'])}", "",
           f"Date: {data['at']} · mode: {mode} · blocks: {data['blocks']} · warns: {data['warns']}", "",
           "| Check | Code | Block | Warn |", "|---|---|---|---|"]
    for label, code in ROWS:
        fs = [f for f in data["findings"] if f["check"] == label]
        b = sum(1 for f in fs if f["level"] == "block")
        out.append(f"| {label} | {code} | {b} | {len(fs) - b} |")
    fix = FIX.get(lang, FIX["en"])
    seen: list = []
    for f in data["findings"]:
        if f["code"] not in seen:
            seen.append(f["code"])
    if seen:
        out += ["", "## Cách sửa / How to fix", ""]
        out += [f"- `{c}`: {fix.get(c) or fix.get(c[:1], '')}" for c in seen]
    out += ["", "## Findings", ""]
    out += (["```text", *map(line_of, data["findings"]), "```"] if data["findings"] else ["No findings."])
    out += ["", "G4: " + ("no block; the author may open G4 (`gate.py open . G4 --by \"<name>\"`)." if not data["blocks"]
                          else "stays closed until every block is fixed and the audit is rerun.")]
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("deliverable", nargs="?", choices=drafts.DELIVERABLES)
    ap.add_argument("--online", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    project = Path(a.project)
    if not project.is_dir():
        print(f"audit: project folder {a.project} not found", file=sys.stderr)
        return 2
    ds = [a.deliverable] if a.deliverable else [d for d in drafts.DELIVERABLES if drafts.draft_files(project, d)]
    if not ds or not all(drafts.draft_files(project, d) for d in ds):
        print(f"audit: no drafts in 06_writing/{a.deliverable or 'thesis|manuscript'}/", file=sys.stderr)
        return 2
    rv = project / "reviews"
    for stale in ("audit.md", "audit.json"):       # a failed run must not leave an older clean report behind
        try:
            (rv / stale).unlink()
        except FileNotFoundError:
            pass
        except OSError as e:
            print(f"audit: cannot remove the old reviews/{stale}: {e}", file=sys.stderr)
            return 2
    try:
        data = run(project, ds, a.deliverable, a.online)
        rv.mkdir(exist_ok=True)
        with open(rv / "audit.json", "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        with open(rv / "audit.md", "w", encoding="utf-8", newline="\n") as fh:
            fh.write(markdown(data, drafts.lang_of(project, ds[0])))
    except NetworkError as e:
        print(f"audit: --online failed, nothing written: {e}", file=sys.stderr)
        return 2
    except Exception as e:  # noqa: BLE001 - never exit 0 or 1 on a crash
        for stale in ("audit.md", "audit.json"):
            try:
                (rv / stale).unlink()
            except OSError:
                pass
        print(f"audit: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        for f in data["findings"]:
            print(line_of(f))
        print(f"audit: {', '.join(ds)} — {data['blocks']} block, {data['warns']} warn; wrote reviews/audit.md, reviews/audit.json")
    return 1 if data["blocks"] else 0


if __name__ == "__main__":
    sys.exit(main())
