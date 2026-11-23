#!/usr/bin/env python3
"""Autorater: judge a skill-text change old versus new on fixed cases (maintainer tool; never in CI).

  python tools/autorater.py list [--skill NAME]
  python tools/autorater.py run <case> [<case> ...] --base <git-ref> [--model sonnet] [--judge-model opus] [--keep]
  python tools/autorater.py report

A case is evals/cases/<name>/ with case.json ({"fixture": "<repo-relative folder>", "allowed_tools": "...",
"max_turns": N, "skills": [...]}), prompt.md and rubric.md. run extracts plugins/ at <git-ref> (git archive) as
the old side and copies the working tree's plugins/ as the new side, runs `claude -p` on a fresh copy of the
fixture for each side with the scenario isolation flags (tests/scenarios/README.md), then asks a judge
(`claude -p --model opus`, Read only) twice with the two attempts in swapped order. The verdict is old, new or tie
only when both judgements agree; otherwise inconsistent (an unreadable judgement counts as disagreement).
Results: evals/results/<case>-<UTC stamp>.json (git-ignored). Needs git and a logged-in claude CLI; costs money.
Exit codes: 0 = done; 1 = a claude run or judge call exited non-zero; 2 = usage, unknown case, git error.
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
    answer, cost, turns, calls = "", 0.0, 0, []
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
            cost = float(ev.get("total_cost_usd") or 0)
            turns = int(ev.get("num_turns") or 0)
    after = _files(run_dir) if Path(run_dir).is_dir() else {}
    return {"answer": answer, "cost_usd": cost, "turns": turns, "tool_calls": calls,
            "changed": sorted(k for k in after if before.get(k) != after[k])}


def materials(prompt: str, a: dict, a_dir: Path, b: dict, b_dir: Path) -> str:
    parts = ["# Task prompt", "", prompt, ""]
    for label, s, folder in (("A", a, a_dir), ("B", b, b_dir)):
        parts += [f"# Attempt {label}", "", "## Final answer", "", s["answer"] or "(none)", "", "## Tool calls", ""]
        parts += [f"- {c}" for c in s["tool_calls"]] or ["(none)"]
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
            parts += [f"### {rel}", FENCE, body[:room], FENCE, ""]
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


def judge(workdir: Path, mats: str, rubric: str, model: str) -> tuple[str, float, int]:
    workdir.mkdir(parents=True, exist_ok=True)
    for name, text in (("materials.md", mats), ("rubric.md", rubric)):
        with open(workdir / name, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    out = workdir.parent / f"{workdir.name}.jsonl"
    code = run_claude(["-p", JUDGE, "--model", model, "--allowedTools", "Read", *ISOLATION, *STREAM], workdir, out)
    s = summarize(out, {}, workdir)
    return s["answer"], s["cost_usd"], code


def run_case(name: str, base: str, model: str = "sonnet", judge_model: str = "opus", results: Path = RESULTS,
             keep: bool = False) -> dict:
    case = load_case(name)
    scratch = Path(tempfile.mkdtemp(prefix=f"autorater-{name}-"))
    try:
        plugins = {"old": extract_base(base, scratch / "old"), "new": copy_head(scratch / "new")}
        summary, dirs = {}, {}
        for side, root in plugins.items():
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
            dirs[side] = run_dir
        judgements = []
        for order, (a, b) in (("old-new", ("old", "new")), ("new-old", ("new", "old"))):
            text, cost, code = judge(scratch / f"judge-{order}", materials(case["prompt"], summary[a], dirs[a],
                                                                           summary[b], dirs[b]), case["rubric"], judge_model)
            parsed = parse_judgement(text)
            judgements.append({"order": order, "exit": code, "cost_usd": cost,
                               "winner": parsed["winner"] if parsed else None,
                               "reasons": str(parsed.get("reasons", "")) if parsed else text[:500],
                               "rubric": parsed.get("rubric", []) if parsed else []})
        result = {"case": name, "base": base, "head": git("rev-parse", "HEAD").decode().strip(),
                  "dirty": bool(git("status", "--porcelain").strip()),
                  "at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                  "model": model, "judge_model": judge_model,
                  "runs": {s: {k: summary[s][k] for k in ("exit", "cost_usd", "turns", "changed", "answer")}
                           for s in summary},
                  "judgements": judgements,
                  "verdict": verdict(judgements[0]["winner"], judgements[1]["winner"]),
                  "cost_usd": round(sum(s["cost_usd"] for s in summary.values())
                                    + sum(j["cost_usd"] for j in judgements), 4)}
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
        for name in a.cases:
            r = run_case(name, a.base, a.model, a.judge_model, Path(a.results), a.keep)
            failed |= any(r["runs"][s]["exit"] for s in r["runs"]) or any(j["exit"] for j in r["judgements"])
            print(f"{name}: {r['verdict']} (USD {r['cost_usd']}) → {r['file']}")
        return 1 if failed else 0
    except Usage as e:
        print(f"autorater: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
