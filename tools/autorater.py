#!/usr/bin/env python3
"""Autorater: judge a skill-text change old versus new on fixed cases (maintainer tool; never in CI).

  python tools/autorater.py list [--skill NAME]
  python tools/autorater.py run <case> [<case> ...] --base <git-ref> [--model sonnet] [--judge-model opus]
                                         [--max-usd 20] [--keep]
  python tools/autorater.py report

A case is evals/cases/<name>/ with case.json ({"fixture": "<repo-relative folder>", "allowed_tools": "...",
"max_turns": N, "skills": [...]}), prompt.md and rubric.md. run extracts plugins/ at <git-ref> (git archive) as
the old side and copies the working tree's plugins/ as the new side, runs `claude -p` on a fresh copy of the
fixture for each side with the scenario isolation flags (tests/scenarios/README.md), then asks a judge
(`claude -p --model opus`, Read only) twice: both orders are judged (old as A, then new as A), not randomised.
The judge runs in a fresh temp folder with a neutral name, and run paths in its materials are replaced by
<RUN_A> / <RUN_B>, so nothing tells it which attempt is old. The verdict is old, new or tie
only when both judgements agree; otherwise inconsistent (an unreadable judgement counts as disagreement).
--max-usd (default 20) caps spend: the cost each claude run reports is summed and no further run starts once the
total reaches the cap (the result is marked "stopped: budget"); a call that reports no cost counts as unknown and
is flagged. An estimate (cases x 2 runs + 2 judgements) is printed first.
Results: evals/results/<case>-<UTC stamp>.json (git-ignored). Needs git and a logged-in claude CLI; costs money.
Exit codes: 0 = done; 1 = a claude run or judge call exited non-zero, or the budget stopped a run; 2 = usage, unknown case, git error.
Standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import uuid
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "evals" / "cases"
RESULTS = ROOT / "evals" / "results"
PLUGINS = ("orchestra", "phi-guard")
ISOLATION = ["--setting-sources", "", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}', "--no-chrome"]
STREAM = ["--output-format", "stream-json", "--verbose"]
FILE_CAP, TOTAL_CAP = 6000, 30000
FENCE = "`" * 3
JUDGE = ("You judge two attempts (A and B) at the same task by a Claude Code plugin. Read materials.md (the task "
         "prompt, then attempt A, then attempt B: final answer, tool calls, files written or changed) and rubric.md "
         "in this folder. Judge only against the rubric; ignore style, length and which attempt comes first. Answer "
         f"with exactly one fenced JSON object and nothing after it:\n{FENCE}json\n"
         '{"winner": "A" | "B" | "tie", "reasons": "<at most 80 words>", '
         '"rubric": [{"item": "<rubric line>", "A": "met|partly|not met", "B": "met|partly|not met"}]}'
         f"\n{FENCE}")


class Usage(Exception):
    """Exit 2."""


def git(*args: str) -> bytes:
    r = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True)
    if r.returncode:
        raise Usage(f"git {' '.join(args)}: {r.stderr.decode('utf-8', 'replace').strip()}")
    return r.stdout


def extract_base(ref: str, dest: Path) -> Path:
    data = git("archive", "--format=tar", ref, "plugins")
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        if hasattr(tarfile, "data_filter"):
            tar.extractall(dest, filter="data")
        else:                                   # older 3.10 patch releases; the archive is this repository's own
            tar.extractall(dest)  # noqa: S202
    return dest / "plugins"


def copy_head(dest: Path) -> Path:
    shutil.copytree(ROOT / "plugins", dest / "plugins", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return dest / "plugins"


def run_claude(args: list[str], cwd: Path, out: Path) -> int:
    with open(out, "wb") as fh, open(Path(out).with_suffix(".err"), "wb") as err:
        return subprocess.run(["claude", *args], cwd=cwd, stdin=subprocess.DEVNULL, stdout=fh, stderr=err).returncode


def load_case(name: str) -> dict:
    folder = CASES / name
    if not (folder / "case.json").is_file():
        raise Usage(f"unknown case {name!r}: no evals/cases/{name}/case.json")
    case = json.loads((folder / "case.json").read_text(encoding="utf-8"))
    case["name"] = name
    case["prompt"] = (folder / "prompt.md").read_text(encoding="utf-8").strip()
    case["rubric"] = (folder / "rubric.md").read_text(encoding="utf-8").strip()
    if not (ROOT / case.get("fixture", "")).is_dir():
        raise Usage(f"{name}: fixture {case.get('fixture')!r} not found")
    return case


def list_cases(skill: str | None = None) -> list[str]:
    out = []
    for cj in sorted(CASES.glob("*/case.json")):
        if skill is None or skill in json.loads(cj.read_text(encoding="utf-8")).get("skills", []):
            out.append(cj.parent.name)
    return out


def _files(folder: Path) -> dict[str, str]:
    return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in Path(folder).rglob("*") if p.is_file()}


def summarize(transcript: Path, before: dict, run_dir: Path) -> dict:
    answer, cost, turns, calls = "", None, 0, []
    text = Path(transcript).read_text(encoding="utf-8", errors="replace") if Path(transcript).is_file() else ""
    for line in text.splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev.get("type") == "assistant":
            for part in (ev.get("message") or {}).get("content") or []:
                if isinstance(part, dict) and part.get("type") == "tool_use":
                    calls.append(f"{part.get('name')}: {json.dumps(part.get('input'), ensure_ascii=False)[:200]}")
        elif ev.get("type") == "result":
            answer = str(ev.get("result") or "")
            cost = float(ev["total_cost_usd"]) if ev.get("total_cost_usd") is not None else None
            turns = int(ev.get("num_turns") or 0)
    after = _files(run_dir) if Path(run_dir).is_dir() else {}
    return {"answer": answer, "cost_usd": cost, "turns": turns, "tool_calls": calls,
            "changed": sorted(k for k in after if before.get(k) != after[k])}


def _variants(p: Path) -> list[str]:
    v = {str(p), Path(p).as_posix(), str(p).replace("\\", "\\\\")}
    return sorted(v, key=len, reverse=True)


def mask(text: str, root: Path | None, label: str) -> str:
    """Replace every spelling of an absolute side root by a neutral placeholder."""
    for v in _variants(root) if root else []:
        text = text.replace(v, f"<{label}>")
    return text


def materials(prompt: str, a: dict, a_dir: Path, b: dict, b_dir: Path,
              a_root: Path | None = None, b_root: Path | None = None) -> str:
    parts = ["# Task prompt", "", prompt, ""]
    for label, s, folder, root in (("A", a, a_dir, a_root), ("B", b, b_dir, b_root)):
        ph = f"RUN_{label}"
        parts += [f"# Attempt {label}", "", "## Final answer", "", mask(s["answer"], root, ph) or "(none)", "",
                  "## Tool calls", ""]
        parts += [f"- {mask(c, root, ph)}" for c in s["tool_calls"]] or ["(none)"]
        parts += ["", "## Files written or changed", ""]
        total = 0
        for rel in s["changed"]:
            room = min(FILE_CAP, TOTAL_CAP - total)
            if room <= 0:
                parts.append(f"### {rel} (not shown: size cap)")
                continue
            try:
                body = (Path(folder) / rel).read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                parts += [f"### {rel}", "(binary or unreadable)", ""]
                continue
            total += min(len(body), room)
            parts += [f"### {rel}", FENCE, mask(body[:room], root, ph), FENCE, ""]
    return "\n".join(parts)


def parse_judgement(text: str) -> dict | None:
    candidates = re.findall(FENCE + r"(?:json)?\s*(\{.*?\})\s*" + FENCE, text, re.S) or re.findall(r"\{.*\}", text, re.S)
    for c in reversed(candidates):
        try:
            obj = json.loads(c)
        except ValueError:
            continue
        if isinstance(obj, dict) and obj.get("winner") in ("A", "B", "tie"):
            return obj
    return None


def verdict(w_old_new: str | None, w_new_old: str | None) -> str:
    """w_old_new: winner when A=old, B=new; w_new_old: winner when A=new, B=old."""
    first = {"A": "old", "B": "new", "tie": "tie"}.get(w_old_new or "")
    second = {"A": "new", "B": "old", "tie": "tie"}.get(w_new_old or "")
    return first if first is not None and first == second else "inconsistent"


def judge(mats: str, rubric: str, model: str) -> tuple[str, float | None, int]:
    """Run the judge in a fresh temp folder with a neutral random name; nothing beside it says old or new."""
    tmp = Path(tempfile.gettempdir())
    workdir, outdir = tmp / f"ar{uuid.uuid4().hex[:12]}", tmp / f"ar{uuid.uuid4().hex[:12]}"
    try:
        workdir.mkdir(parents=True)
        outdir.mkdir(parents=True)
        for name, text in (("materials.md", mats), ("rubric.md", rubric)):
            with open(workdir / name, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
        out = outdir / "j.jsonl"
        code = run_claude(["-p", JUDGE, "--model", model, "--allowedTools", "Read", *ISOLATION, *STREAM], workdir, out)
        s = summarize(out, {}, workdir)
        return s["answer"], s["cost_usd"], code
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
        shutil.rmtree(outdir, ignore_errors=True)


class Budget:
    def __init__(self, cap: float | None = None):
        self.cap, self.spent, self.unknown = cap, 0.0, 0

    def add(self, cost: float | None) -> None:
        if cost is None:
            self.unknown += 1
        else:
            self.spent += cost

    def over(self) -> bool:
        return self.cap is not None and self.spent >= self.cap


def run_case(name: str, base: str, model: str = "sonnet", judge_model: str = "opus", results: Path = RESULTS,
             keep: bool = False, budget: Budget | None = None) -> dict:
    case = load_case(name)
    budget = budget or Budget()
    stopped = False
    scratch = Path(tempfile.mkdtemp(prefix=f"autorater-{name}-"))
    try:
        plugins = {"old": extract_base(base, scratch / "old"), "new": copy_head(scratch / "new")}
        summary, dirs = {}, {}
        for side, root in plugins.items():
            if budget.over():
                stopped = True
                break
            run_dir = scratch / side / "run" / name
            shutil.copytree(ROOT / case["fixture"], run_dir)
            before = _files(run_dir)
            args = ["-p", case["prompt"], "--model", model, "--allowedTools", case["allowed_tools"],
                    "--max-turns", str(case.get("max_turns", 60)), *ISOLATION, *STREAM]
            for pl in PLUGINS:
                args += ["--plugin-dir", str(root / pl)]
            out = scratch / side / "run.jsonl"
            code = run_claude(args, run_dir, out)
            summary[side] = dict(summarize(out, before, run_dir), exit=code)
            budget.add(summary[side]["cost_usd"])
            dirs[side] = run_dir
        judgements = []
        for order, (a, b) in (("old-new", ("old", "new")), ("new-old", ("new", "old"))):
            if stopped or budget.over():
                stopped = True
                break
            mats = materials(case["prompt"], summary[a], dirs[a], summary[b], dirs[b], scratch / a, scratch / b)
            text, cost, code = judge(mats, case["rubric"], judge_model)
            budget.add(cost)
            parsed = parse_judgement(text)
            judgements.append({"order": order, "exit": code, "cost_usd": cost,
                               "winner": parsed["winner"] if parsed else None,
                               "reasons": str(parsed.get("reasons", "")) if parsed else text[:500],
                               "rubric": parsed.get("rubric", []) if parsed else []})
        costs = [s["cost_usd"] for s in summary.values()] + [j["cost_usd"] for j in judgements]
        result = {"case": name, "base": base, "head": git("rev-parse", "HEAD").decode().strip(),
                  "dirty": bool(git("status", "--porcelain").strip()),
                  "at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                  "model": model, "judge_model": judge_model,
                  "runs": {s: {k: summary[s][k] for k in ("exit", "cost_usd", "turns", "changed", "answer")}
                           for s in summary},
                  "judgements": judgements,
                  "verdict": ("stopped: budget" if stopped
                              else verdict(judgements[0]["winner"], judgements[1]["winner"])),
                  "stopped": "budget" if stopped else None,
                  "unknown_cost_calls": sum(1 for c in costs if c is None),
                  "cost_usd": round(sum(c for c in costs if c is not None), 4)}
        results.mkdir(parents=True, exist_ok=True)
        path = results / f"{name}-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        result["file"] = str(path)
        return result
    finally:
        if keep:
            print(f"autorater: scratch kept at {scratch}", file=sys.stderr)
        else:
            shutil.rmtree(scratch, ignore_errors=True)


def report(results: Path = RESULTS) -> str:
    rows = []
    for p in sorted(Path(results).glob("*.json")):
        try:
            r = json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            continue
        head = str(r.get("head", ""))[:7] + ("+dirty" if r.get("dirty") else "")
        rows.append(f"| {r.get('case')} | {str(r.get('at', ''))[:16]} | {r.get('base')} | {head} | "
                    f"{r.get('verdict')} | {r.get('cost_usd')} |")
    if not rows:
        return "autorater: no results yet"
    return "\n".join(["| case | at (UTC) | base | head | verdict | cost USD |", "|---|---|---|---|---|---|", *rows])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    ls = sub.add_parser("list")
    ls.add_argument("--skill")
    rn = sub.add_parser("run")
    rn.add_argument("cases", nargs="+")
    rn.add_argument("--base", required=True)
    rn.add_argument("--model", default="sonnet")
    rn.add_argument("--judge-model", default="opus")
    rn.add_argument("--max-usd", type=float, default=20.0, help="stop starting runs once this much is spent")
    rn.add_argument("--keep", action="store_true")
    rn.add_argument("--results", default=str(RESULTS))
    rp = sub.add_parser("report")
    rp.add_argument("--results", default=str(RESULTS))
    a = ap.parse_args(argv)
    try:
        if a.cmd == "list":
            print("\n".join(list_cases(a.skill)) or "autorater: no case exercises that skill")
            return 0
        if a.cmd == "report":
            print(report(Path(a.results)))
            return 0
        for name in a.cases:            # validate every case before spending anything
            load_case(name)
        failed = False
        budget = Budget(a.max_usd)
        print(f"autorater: estimate {len(a.cases)} case(s) x (2 runs + 2 judgements) = {len(a.cases) * 4} claude "
              f"calls; stops starting runs at USD {a.max_usd:g} (a cost is known only after its call)", file=sys.stderr)
        for name in a.cases:
            if budget.over():
                print(f"{name}: stopped: budget (USD {budget.spent:.2f} >= {a.max_usd:g})")
                failed = True
                continue
            r = run_case(name, a.base, a.model, a.judge_model, Path(a.results), a.keep, budget)
            failed |= bool(r["stopped"]) | any(r["runs"][s]["exit"] for s in r["runs"]) or any(j["exit"] for j in r["judgements"])
            note = f"; {r['unknown_cost_calls']} call(s) reported no cost" if r["unknown_cost_calls"] else ""
            print(f"{name}: {r['verdict']} (USD {r['cost_usd']}{note}) → {r['file']}")
        return 1 if failed else 0
    except Usage as e:
        print(f"autorater: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
