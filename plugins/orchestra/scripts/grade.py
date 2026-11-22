#!/usr/bin/env python3
"""GRADE certainty, absolute effects and the summary of findings for a systematic review; E-GRADE wording check.

  python grade.py <project> run [--table N]
  python grade.py <project> check [--text FILE ...]

run reads 05_analysis/meta/grade.json (per outcome: the pooled result id, design rct|nrsi, the RoB tool,
downgrades risk_of_bias/inconsistency/indirectness/imprecision/publication_bias of 0/-1/-2 with a reason, upgrades
for NRSI only, the assumed comparator risk with its source), computes certainty (start high for RCTs and for NRSI
assessed with ROBINS-I, low otherwise), writes absolute effects per 1000 as R-A<n>-901 (comparator), -902
(intervention, CI), -903 (difference, CI) with kind "absolute" through 05_analysis/output/grade-log.txt into the
results ledger, and writes 06_writing/review/sof.md with placeholders (the table number follows the tables of the
sections before it unless --table is given). check warns (E-GRADE) on a paragraph that cites a low or very low
certainty result without hedged wording from references/review/grade-wording.md (language from project.yaml).
Exit codes: 0 = done / no block (warnings allowed); 1 = the ledger is locked by G3 or a label change is refused;
2 = usage error, invalid grade.json, unknown result id, I/O error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crolib import derived, drafts, projectcfg, resultlog  # noqa: E402
import analysis_plan  # noqa: E402
import results_ledger  # noqa: E402

GRADE_JSON = "05_analysis/meta/grade.json"
LOG_REL = "05_analysis/output/grade-log.txt"
DOC_REL = "05_analysis/output/grade-results.json"
SOF = "06_writing/review/sof.md"
WORDING = Path(__file__).resolve().parents[1] / "references" / "review" / "grade-wording.md"
DOWN = ("risk_of_bias", "inconsistency", "indirectness", "imprecision", "publication_bias")
UP = ("large_effect", "dose_response", "plausible_confounding")
LEVELS = {4: "high", 3: "moderate", 2: "low", 1: "very low"}
SYMBOL = {"high": "⊕⊕⊕⊕", "moderate": "⊕⊕⊕◯", "low": "⊕⊕◯◯", "very low": "⊕◯◯◯"}
NAME = {"en": {"high": "High", "moderate": "Moderate", "low": "Low", "very low": "Very low"},
        "vi": {"high": "Cao", "moderate": "Trung bình", "low": "Thấp", "very low": "Rất thấp"}}
ABSOLUTE_KINDS = ("rr", "or", "hr", "rd")
STEP = {"en": {"down": "down", "up": "up", 1: "one level", 2: "two levels"},  # words, not digits: sof.md is E-NUM checked
        "vi": {"down": "hạ", "up": "nâng", 1: "một bậc", 2: "hai bậc"}}
PLACEHOLDER = re.compile(r"\{\{(R-A(\d+)-(\d{3}))(?:\.\w+)?\}\}")
CAPTION = re.compile(r"^(?:\*\*)?(?:Table|Bảng)\s+(\d+)\.", re.M)
TEXT = {
    "en": {"caption": "Table {n}. Summary of findings",
           "head": "| Outcome | Studies (participants) | Relative effect (95% CI) | Risk with comparator (per 1000 "
                   "<!-- not-a-result: GRADE denominator -->) | Risk with intervention (95% CI) | Difference (95% CI) "
                   "| Certainty |",
           "na": "not applicable (continuous outcome)",
           "foot": "Certainty (GRADE): high, moderate, low, very low. Assumed comparator risk: {src}. Reasons: {why}."},
    "vi": {"caption": "Bảng {n}. Tóm tắt kết quả (summary of findings)",
           "head": "| Kết cục | Số nghiên cứu (người tham gia) | Hiệu quả tương đối (KTC 95%) | Nguy cơ ở nhóm so sánh "
                   "(trên 1000 <!-- not-a-result: mẫu số GRADE -->) | Nguy cơ ở nhóm can thiệp (KTC 95%) | "
                   "Chênh lệch (KTC 95%) | Mức chắc chắn |",
           "na": "không áp dụng (biến liên tục)",
           "foot": "Mức chắc chắn (GRADE): cao, trung bình, thấp, rất thấp. Nguy cơ giả định ở nhóm so sánh: {src}. "
                   "Lý do: {why}."},
}


class Invalid(Exception):
    """grade.json cannot be used (exit 2)."""


def _pair(o: dict, group: str, key: str) -> tuple[int, str]:
    v = (o.get(group) or {}).get(key, [0, ""])
    if not (isinstance(v, list) and len(v) == 2 and isinstance(v[0], int) and not isinstance(v[0], bool)):
        raise Invalid(f"{o.get('outcome')}: {group}.{key} must be [integer, reason]")
    return v[0], str(v[1] or "").strip()


def start_level(o: dict) -> int:
    if o.get("design") == "rct" or (o.get("design") == "nrsi" and o.get("rob_tool") == "ROBINS-I"):
        return 4
    return 2


def certainty(o: dict) -> str:
    total = start_level(o) + sum(_pair(o, "downgrades", k)[0] for k in DOWN)
    if o.get("design") == "nrsi":
        total += sum(_pair(o, "upgrades", k)[0] for k in UP)
    return LEVELS[max(1, min(4, total))]


def validate(doc: dict, ledger: dict) -> list[str]:
    probs = []
    outs = doc.get("outcomes") if isinstance(doc, dict) else None
    if not isinstance(outs, list) or not outs:
        return ["grade.json needs a non-empty 'outcomes' list"]
    for o in outs:
        name = str(o.get("outcome") or "?")
        rid = o.get("result")
        if not (isinstance(rid, str) and re.fullmatch(r"R-A\d+-001", rid)):
            probs.append(f"{name}: result must be a pooled result id R-A<n>-001")
            continue
        if rid not in ledger:
            probs.append(f"{name}: {rid} is not in the results ledger (run meta.py run first)")
            continue
        if o.get("design") not in ("rct", "nrsi"):
            probs.append(f"{name}: design must be rct or nrsi")
        try:
            for k in DOWN:
                v, why = _pair(o, "downgrades", k)
                if v not in (0, -1, -2):
                    probs.append(f"{name}: {k}: a downgrade is 0, -1 or -2")
                elif v and not why:
                    probs.append(f"{name}: {k}: a downgrade needs a reason")
            for k in UP:
                v, why = _pair(o, "upgrades", k)
                if v and o.get("design") != "nrsi":
                    probs.append(f"{name}: {k}: upgrades are for non-randomised studies only")
                elif v not in (0, 1, 2):
                    probs.append(f"{name}: {k}: an upgrade is 0, 1 or 2")
                elif v and not why:
                    probs.append(f"{name}: {k}: an upgrade needs a reason")
        except Invalid as e:
            probs.append(str(e))
        if ledger[rid].get("kind") in ABSOLUTE_KINDS:
            cr = o.get("comparator_risk")
            if not (isinstance(cr, (int, float)) and not isinstance(cr, bool) and 0 < cr < 1):
                probs.append(f"{name}: comparator_risk must be a proportion between 0 and 1")
            if not str(o.get("comparator_source") or "").strip():
                probs.append(f"{name}: comparator_source must say where the assumed risk comes from")
    return probs


def absolute(kind: str, x: float, cr: float) -> float:
    if kind == "rr":
        return min(1.0, x * cr)
    if kind == "or":
        return x * cr / (1 - cr + x * cr)
    if kind == "hr":
        return 1 - (1 - cr) ** x
    if kind == "rd":
        return min(1.0, max(0.0, cr + x))
    raise ValueError(f"no absolute effect for kind {kind!r}")


def _next_table(project: Path) -> int:
    """1 + the highest "Table n." / "Bảng n." caption in the sections placed before sof.md (D21 order)."""
    n = 0
    base = Path(project) / "06_writing" / "review"
    for name in ("02-introduction.md", "03-methods.md", "04-results.md"):
        f = base / name
        if f.is_file():
            n = max([n] + [int(m.group(1)) for m in CAPTION.finditer(f.read_text(encoding="utf-8-sig"))])
    return n + 1


def run(project: Path, table: int | None = None) -> tuple[int, list[str], list[str]]:
    doc = json.loads((project / GRADE_JSON).read_text(encoding="utf-8-sig"))
    ledger = derived.ledger_by_id(project)
    probs = validate(doc, ledger)
    if probs:
        raise Invalid("\n".join(probs))
    lang = "vi" if projectcfg.output_lang(project) == "vi" else "en"
    t = TEXT[lang]
    log = resultlog.ResultLog(project, GRADE_JSON, LOG_REL, "grade.py")
    rows, notes, summary = [], [], []
    for o in doc["outcomes"]:
        rid = o["result"]
        rec, aid = ledger[rid], rid.split("-")[1]
        level = certainty(o)
        reasons = [f"{k.replace('_', ' ')}: {STEP[lang]['down']} {STEP[lang][abs(v)]} ({why})"
                   for k in DOWN for v, why in [_pair(o, "downgrades", k)] if v]
        reasons += [f"{k.replace('_', ' ')}: {STEP[lang]['up']} {STEP[lang][v]} ({why})"
                    for k in UP for v, why in [_pair(o, "upgrades", k)] if v]
        summary.append(f"{o['outcome']}: {level} certainty ({SYMBOL[level]})")
        cells = [o["outcome"], f"{{{{{rid}.count}}}} ({{{{{rid}.n}}}})", f"{{{{{rid}.full}}}}"]
        kind = rec.get("kind")
        if kind in ABSOLUTE_KINDS and rec.get("ci"):
            cr = float(o["comparator_risk"])
            lo, hi = rec["ci"]
            risk = [absolute(kind, x, cr) * 1000 for x in (rec["value"], lo, hi)]
            st = rec.get("status", "prespecified")
            log.add(aid, st, f"{o['outcome']}: assumed comparator risk per 1000", cr * 1000, "absolute", number=901)
            log.add(aid, st, f"{o['outcome']}: risk with intervention per 1000", risk[0], "absolute",
                    ci=[min(risk[1:]), max(risk[1:])], number=902)
            diff = [r - cr * 1000 for r in risk]
            log.add(aid, st, f"{o['outcome']}: difference per 1000", diff[0], "absolute",
                    ci=[min(diff[1:]), max(diff[1:])], number=903)
            cells += [f"{{{{R-{aid}-901.value}}}}", f"{{{{R-{aid}-902.full}}}}", f"{{{{R-{aid}-903.full}}}}"]
        else:
            cells += [t["na"], t["na"], t["na"]]
        cells.append(f"{SYMBOL[level]} {NAME[lang][level]}")
        rows.append("| " + " | ".join(cells) + " |")
        notes.append(t["foot"].format(src=o.get("comparator_source") or "—", why="; ".join(reasons) or "—"))
    n = 0
    if log.results:
        path = log.save(DOC_REL)
        n, bad = resultlog.import_merged(project, path)
        if bad:
            raise ValueError("; ".join(bad))
    sof = project / SOF
    sof.parent.mkdir(parents=True, exist_ok=True)
    body = [t["caption"].format(n=table or _next_table(project)), t["head"],
            "|" + "---|" * (t["head"].count("|") - 1)] + rows + [""] + [f"- {x}" for x in notes]
    with open(sof, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(body) + "\n")
    return n, summary, [SOF]


def load_wording(lang: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"low": [], "very low": []}
    section, sub = None, None
    for line in WORDING.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("## "):
            section, sub = s[3:].strip(), None
        elif s.startswith("### "):
            sub = s[4:].strip()
        elif s.startswith("- ") and section == lang and sub in out:
            out[sub].append(unicodedata.normalize("NFC", s[2:].strip()).casefold())
    return out


def certainty_by_result(project: Path) -> dict[str, str]:
    path = Path(project) / GRADE_JSON
    if not path.is_file():
        return {}
    out = {}
    for o in json.loads(path.read_text(encoding="utf-8-sig")).get("outcomes", []):
        rid = o.get("result")
        if not isinstance(rid, str) or not re.fullmatch(r"R-A\d+-001", rid):
            continue
        try:
            level = certainty(o)
        except Invalid:
            continue
        aid = rid.split("-")[1]
        for suffix in ("001", "005", "901", "902", "903"):
            out[f"R-{aid}-{suffix}"] = level
    return out


def _hedged(text: str, words: list[str], lang: str) -> bool:
    text = unicodedata.normalize("NFC", text)
    words = [unicodedata.normalize("NFC", w) for w in words]
    if lang == "en":
        text = re.sub(r"\bMay\s+\d", " ", text)          # the month ("May 2024"), not the verb
    low = text.casefold()
    if lang == "en":
        return any(re.search(r"(?<![\w-])" + re.escape(w) + r"(?![\w-])", low) for w in words)
    return any(w in low for w in words)


def check_wording(project: Path, files: list) -> list[tuple[str, str, str]]:
    project = Path(project)
    levels = certainty_by_result(project)
    if not levels:
        return []
    lang = "vi" if projectcfg.output_lang(project) == "vi" else "en"
    words = load_wording(lang)
    found = []
    for f in files:
        f = Path(f)
        rel = f.resolve().relative_to(project.resolve()).as_posix() if f.is_absolute() else f.as_posix()
        for start, para in analysis_plan._paragraphs(f.read_text(encoding="utf-8-sig")):
            if para.lstrip().startswith("|"):
                continue
            cited = [m.group(1) for m in PLACEHOLDER.finditer(para) if levels.get(m.group(1)) in ("low", "very low")]
            if not cited:
                continue
            worst = "very low" if any(levels[c] == "very low" for c in cited) else "low"
            allowed = words["very low"] if worst == "very low" else words["low"] + words["very low"]
            if not _hedged(para, allowed, lang):
                found.append(("warn", f"{rel}:{start}", f"{cited[0]} has {worst} certainty (GRADE); hedge the claim "
                                                        f"({', '.join(repr(w) for w in allowed[:3])}, …)"))
    return found


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("cmd", choices=["run", "check"])
    ap.add_argument("--table", type=int)
    ap.add_argument("--text", nargs="*", default=None)
    a = ap.parse_args(argv)
    project = Path(a.project)
    if not (project / "project.yaml").is_file():
        print(f"grade: {a.project} is not a project folder (no project.yaml)", file=sys.stderr)
        return 2
    try:
        if a.cmd == "run":
            n, summary, written = run(project, a.table)
            for line in summary:
                print(line)
            print(f"grade: {n} absolute effects in the results ledger; wrote {', '.join(written)}")
            return 0
        files = [Path(x) for x in a.text] if a.text is not None else [
            p for p in drafts.draft_files(project, "review") if drafts.results_bearing(p)]
        found = check_wording(project, files)
        for sev, loc, msg in found:
            print(f"E-GRADE {sev} {loc}: {msg}")
        print(f"grade: 0 block, {len(found)} warn")
        return 0
    except results_ledger.LockedError as e:
        print(f"grade: {e}", file=sys.stderr)
        return 1
    except results_ledger.RelabelError as e:
        print(f"{e}\ngrade: labels changed; ledger not written", file=sys.stderr)
        return 1
    except Invalid as e:
        print(f"grade: grade.json is not usable:\n{e}", file=sys.stderr)
        return 2
    except (OSError, ValueError, KeyError) as e:
        print(f"grade: {type(e).__name__}: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
