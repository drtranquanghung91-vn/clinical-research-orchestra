#!/usr/bin/env python3
"""Screening log for systematic and scoping reviews (PRISMA 2020 / PRISMA-ScR flow).

  python screening.py <project> import <file> --database NAME
  python screening.py <project> dedupe
  python screening.py <project> decide --stage ta|ft --reviewer NAME --rec REC --decision include|exclude|maybe
                                        [--reason TEXT] [--study ID]
  python screening.py <project> decide --stage ta|ft --reviewer NAME --file SHEET.csv
  python screening.py <project> sheet --stage ta|ft --reviewer NAME
  python screening.py <project> suggest --stage ta|ft --from FILE
  python screening.py <project> conflicts --stage ta|ft
  python screening.py <project> kappa --stage ta|ft
  python screening.py <project> counts
  python screening.py <project> check

Files in 02_evidence/sr/: records.csv (rec_id,database,pmid,doi,title,authors,year,journal,abstract,duplicate_of);
screening.csv (stage,rec_id,reviewer,decision,reason,study,at; append-only, the latest row per stage, record and
reviewer counts); ai-suggestions.csv (never read as a decision); search-log.csv
(database,platform,date_run,string_id,hits,export_file). import reads RIS (.ris), PubMed MEDLINE (.nbib/.txt) or
CSV and warns (E-SCR) when the records per database differ from the hits in search-log.csv. dedupe marks duplicates
by DOI or PMID, then by normalised title + year + first author (both rows stay). decide is refused while gate G2 is
not open, for a reviewer not in project.yaml review.reviewers (AI names never count), for a duplicate, for a
full-text decision on a record that did not pass title/abstract screening, and for a full-text exclusion without a
reason from the protocol's "## Full-text exclusion reasons" list (or "not retrieved"); reviewer "consensus"
resolves a disagreement. sheet writes reviews/tmp/screening-<stage>-<reviewer>.csv with the AI suggestion as a
separate column; decide --file reads its decision column back (blank rows skipped; all rows or none). suggest
validates a role-briefed AI pass into ai-suggestions.csv. counts writes the PRISMA flow as results-ledger records
R-A0-NNN (status observed) and refuses while a reached record is unresolved. check prints the E-SCR findings.
Exit codes: 0 = done / clean; 1 = refused, conflicts listed, or E-SCR block findings; 2 = usage or I/O error.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
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
from crolib import projectcfg, resultlog  # noqa: E402
import gate  # noqa: E402
import results_ledger  # noqa: E402

SR = "02_evidence/sr"
RECORDS = f"{SR}/records.csv"
SCREENING = f"{SR}/screening.csv"
SUGGESTIONS = f"{SR}/ai-suggestions.csv"
SEARCH_LOG = f"{SR}/search-log.csv"
PROTOCOL = "03_protocol/sr-protocol.md"
LOG_REL = "05_analysis/output/screening-log.txt"
DOC_REL = "05_analysis/output/screening-counts.json"
RECORD_COLS = ["rec_id", "database", "pmid", "doi", "title", "authors", "year", "journal", "abstract", "duplicate_of"]
SCREEN_COLS = ["stage", "rec_id", "reviewer", "decision", "reason", "study", "at"]
SUGGEST_COLS = ["stage", "rec_id", "suggestion", "reason", "source"]
SHEET_COLS = ["rec_id", "title", "year", "journal", "abstract", "ai_suggestion", "ai_reason", "decision", "reason", "study"]
STAGES = ("ta", "ft")
DECISIONS = ("include", "exclude", "maybe")
NOT_RETRIEVED = "not retrieved"
CONSENSUS = "consensus"
AI_NAME = re.compile(r"(?i)\b(?:ai|assistant|model|llm|bot|openai|gemini|copilot|llama|mistral|deepseek|grok|bard|perplexity)\b"
                     r"|(?<![a-z])(?:gpt|claude|chatgpt)[a-z0-9_]*")
AI_HINT = ("a human whose name collides with an AI word (for example the Vietnamese given name Ai) "
           "can be written surname-first or as initials")
REASONS_HEAD = re.compile(r"(?im)^#{2,3}\s*(?:full-text exclusion reasons|lý do loại trừ (?:ở bước )?toàn văn)\s*$")
REGISTER_NAME = re.compile(r"(?i)regist|clinicaltrials|ictrp")
RIS_TAG = re.compile(r"^([A-Z][A-Z0-9])  -\s?(.*)$")
NB_TAG = re.compile(r"^([A-Z]{2,4})\s*- (.*)$")
CSV_KEYS = {"title": ("title",), "authors": ("authors", "author"), "year": ("year", "publication year", "py"),
            "journal": ("journal", "source", "source title", "journal/book"), "abstract": ("abstract",),
            "doi": ("doi",), "pmid": ("pmid", "pubmed id")}
FIXED = [  # PRISMA 2020 flow boxes, ids R-A0-001..011 (plan D10)
    ("databases", "records identified from databases"),
    ("registers", "records identified from registers"),
    ("duplicates", "duplicate records removed"),
    ("screened", "records screened"),
    ("excluded", "records excluded at title and abstract"),
    ("sought", "reports sought for retrieval"),
    ("not_retrieved", "reports not retrieved"),
    ("assessed", "reports assessed for eligibility"),
    ("reports_excluded", "reports excluded at full text"),
    ("studies", "studies included"),
    ("reports", "reports included"),
]


class Refused(Exception):
    """An action the screening rules do not allow (exit 1)."""


# ---------------------------------------------------------------- files

def read_csv(path: Path) -> list[dict]:
    if not Path(path).is_file():
        return []
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, cols: list[str], rows: list[dict]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


def append_csv(path: Path, cols: list[str], rows: list[dict]) -> None:
    new = not path.is_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
        if new:
            w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-")


# ---------------------------------------------------------------- import

def _clean_doi(s: str) -> str:
    return re.sub(r"(?i)^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", (s or "").strip())


def _first(d: dict, *tags: str) -> str:
    for t in tags:
        if d.get(t):
            return d[t][0]
    return ""


def _year(text: str) -> str:
    m = re.search(r"\b(1[89]\d\d|20\d\d)\b", text or "")
    return m.group(1) if m else ""


def parse_ris(text: str) -> list[dict]:
    recs, cur, last = [], {}, None
    for line in text.splitlines():
        m = RIS_TAG.match(line)
        if not m:
            if last and line.strip() and cur:
                cur[last][-1] += " " + line.strip()
            continue
        tag, val = m.group(1), m.group(2).strip()
        if tag == "ER":
            if cur:
                recs.append(cur)
            cur, last = {}, None
            continue
        cur.setdefault(tag, []).append(val)
        last = tag
    if cur:
        recs.append(cur)
    return [{"pmid": "", "doi": _clean_doi(_first(d, "DO")), "title": _first(d, "TI", "T1"),
             "authors": "; ".join(d.get("AU") or d.get("A1") or []), "year": _year(_first(d, "PY", "Y1", "DA")),
             "journal": _first(d, "JO", "T2", "JF", "JA"), "abstract": _first(d, "AB", "N2")} for d in recs]


def parse_nbib(text: str) -> list[dict]:
    recs, cur, last = [], {}, None
    for line in text.splitlines() + [""]:
        if not line.strip():
            if cur:
                recs.append(cur)
            cur, last = {}, None
            continue
        if line.startswith("      ") and last:
            cur[last][-1] += " " + line.strip()
            continue
        m = NB_TAG.match(line)
        if m and m.group(1) == "ER":
            if cur:
                recs.append(cur)
            cur, last = {}, None
            continue
        if m:
            last = m.group(1)
            cur.setdefault(last, []).append(m.group(2).strip())
    out = []
    for d in recs:
        doi = next((_clean_doi(v[:-5]) for v in d.get("LID", []) + d.get("AID", []) if v.endswith("[doi]")), "")
        out.append({"pmid": _first(d, "PMID"), "doi": doi, "title": _first(d, "TI"), "authors": "; ".join(d.get("AU", [])),
                    "year": _year(_first(d, "DP")), "journal": _first(d, "JT", "TA"), "abstract": _first(d, "AB")})
    return out


def parse_csv(text: str) -> list[dict]:
    out = []
    for r in csv.DictReader(io.StringIO(text)):
        low = {(k or "").strip().casefold(): (v or "").strip() for k, v in r.items()}
        rec = {key: next((low[n] for n in names if low.get(n)), "") for key, names in CSV_KEYS.items()}
        rec["doi"] = _clean_doi(rec["doi"])
        rec["year"] = _year(rec["year"])
        out.append(rec)
    return out


def hits_findings(project: Path, rows: list[dict]) -> list[tuple[str, str, str]]:
    log = read_csv(Path(project) / SEARCH_LOG)
    if not log:
        return [("warn", f"{SEARCH_LOG}:1", "no search log: record database, platform, date, string and hits (PRISMA-S)")]
    found, logged, lines, per = [], {}, {}, {}
    for r in rows:
        db = (r.get("database") or "").strip().casefold()
        per[db] = per.get(db, 0) + 1
    for i, r in enumerate(log, start=2):
        db = (r.get("database") or "").strip().casefold()
        try:
            hits = int((r.get("hits") or "").strip())
        except ValueError:
            found.append(("warn", f"{SEARCH_LOG}:{i}", f"hits {r.get('hits')!r} is not a whole number"))
            continue
        logged[db] = logged.get(db, 0) + hits
        lines.setdefault(db, i)
    for db in sorted(set(per) | set(logged)):
        if per.get(db, 0) != logged.get(db, 0):
            found.append(("warn", f"{SEARCH_LOG}:{lines.get(db, 1)}",
                          f"{db}: {logged.get(db, 0)} hits logged, {per.get(db, 0)} records imported"))
    return found


def import_file(project: Path, path: Path, database: str) -> tuple[int, list]:
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8-sig")
    if suffix == ".ris" or re.search(r"(?m)^TY  -", text):
        recs = parse_ris(text)
    elif suffix in (".nbib", ".txt"):
        recs = parse_nbib(text)
    elif suffix == ".csv":
        recs = parse_csv(text)
    else:
        raise ValueError(f"{path.name}: unknown export format (use .ris, .nbib/.txt or .csv)")
    if not recs:
        raise ValueError(f"{path.name}: no records found")
    rows = read_csv(project / RECORDS)
    start = max((int(r["rec_id"][4:]) for r in rows if re.fullmatch(r"rec-\d+", r.get("rec_id", ""))), default=0)
    for i, r in enumerate(recs, start=start + 1):
        rows.append(dict(r, rec_id=f"rec-{i:04d}", database=database.strip(), duplicate_of=""))
    write_csv(project / RECORDS, RECORD_COLS, rows)
    return len(recs), hits_findings(project, rows)


# ---------------------------------------------------------------- dedupe

def norm(text: str) -> str:
    s = unicodedata.normalize("NFKD", text or "").casefold()
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())


def first_author(authors: str) -> str:
    first = (authors or "").split(";")[0].strip()
    return norm(re.split(r"[,\s]", first)[0]) if first else ""


def dedupe(project: Path) -> tuple[int, int]:
    rows = read_csv(project / RECORDS)
    if not rows:
        raise ValueError(f"no {RECORDS}: run screening.py import first")
    seen: dict[str, str] = {}
    marked = 0
    for r in rows:
        keys = []
        if r.get("doi"):
            keys.append("doi:" + r["doi"].casefold())
        if r.get("pmid"):
            keys.append("pmid:" + r["pmid"].strip())
        t = norm(r.get("title", ""))
        fa = first_author(r.get("authors", ""))
        if t and r.get("year") and fa:
            keys.append(f"t:{t}|{r['year']}|{fa}")
        orig = next((seen[k] for k in keys if k in seen), None)
        r["duplicate_of"] = orig or ""
        marked += bool(orig)
        for k in keys:
            seen.setdefault(k, orig or r["rec_id"])
    write_csv(project / RECORDS, RECORD_COLS, rows)
    return len(rows), marked


# ---------------------------------------------------------------- decisions

def reviewers(project: Path) -> list[str]:
    rev = projectcfg.read_project_yaml(project).get("review", {})
    return projectcfg.parse_list(rev.get("reviewers", "") if isinstance(rev, dict) else "")


def human_reviewers(project: Path) -> list[str]:
    return [r for r in reviewers(project) if not AI_NAME.search(r)]


def protocol_reasons(project: Path) -> list[str]:
    path = Path(project) / PROTOCOL
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8-sig")
    m = REASONS_HEAD.search(text)
    out: list[str] = []
    for line in (text[m.end():].splitlines() if m else []):
        s = line.strip()
        if s.startswith("#"):
            break
        if s.startswith(("- ", "* ")):
            out.append(s[2:].strip().casefold())
        elif s and out:
            break
    return out


def records(project: Path) -> dict[str, dict]:
    return {r["rec_id"]: r for r in read_csv(Path(project) / RECORDS)}


def latest(project: Path) -> dict[tuple, dict]:
    out = {}
    for i, r in enumerate(read_csv(Path(project) / SCREENING), start=2):
        out[(r.get("stage"), r.get("rec_id"), r.get("reviewer"))] = dict(r, _line=i)
    return out


def resolve(project: Path) -> dict[str, dict[str, dict]]:
    """stage -> rec_id -> {"rows": {reviewer: latest row}, "final": include|exclude|None, "why": text}."""
    recs, humans, lat = records(project), human_reviewers(project), latest(project)
    out: dict[str, dict[str, dict]] = {"ta": {}, "ft": {}}
    for stage in STAGES:
        if stage == "ta":
            reached = [rid for rid, r in recs.items() if not r.get("duplicate_of")]
        else:
            reached = [rid for rid, e in out["ta"].items() if e["final"] == "include"]
        for rid in reached:
            rows = {rv: lat[(stage, rid, rv)] for rv in humans + [CONSENSUS] if (stage, rid, rv) in lat}
            e = {"rows": rows, "final": None, "why": ""}
            if len(humans) < 2:
                e["why"] = f"two human reviewers are needed (review.reviewers lists {len(humans)})"
            elif CONSENSUS in rows and any(h not in rows for h in humans):
                e["why"] = "consensus without both human decisions (not decided by " + ", ".join(h for h in humans if h not in rows) + ")"
            elif CONSENSUS in rows:
                d = rows[CONSENSUS].get("decision")
                e["final"], e["why"] = (d, "consensus") if d in ("include", "exclude") else (None, "consensus row says maybe")
            else:
                missing = [h for h in humans if h not in rows]
                ds = [rows[h]["decision"] for h in humans if h in rows]
                if missing:
                    e["why"] = "not decided by " + ", ".join(missing)
                elif len(set(ds)) == 1 and ds[0] in ("include", "exclude"):
                    field = "reason" if (stage == "ft" and ds[0] == "exclude") else "study" if (stage == "ft" and ds[0] == "include") else ""
                    vals = {(rows[h].get(field) or "").strip().casefold(): (rows[h].get(field) or "").strip()
                            for h in humans} if field else {}
                    vals.pop("", None)
                    if len(vals) > 1:
                        e["why"] = f"conflict: the reviewers gave different {field}s (" + "; ".join(
                            f"{h}: {(rows[h].get(field) or '').strip() or '-'}" for h in humans) + "); a consensus row must settle it"
                    else:
                        e["final"] = ds[0]
                else:
                    e["why"] = "conflict: " + ", ".join(f"{h} {rows[h]['decision']}" for h in humans)
            out[stage][rid] = e
    return out


def decide(project: Path, stage: str, reviewer: str, rows_in: list[dict]) -> int:
    ok, why = gate.check_gate(project, "G2")
    if not ok:
        raise Refused("G2: not open — decisions are recorded only after the author locks the protocol "
                      "(gate.py open . G2 --by NAME --files 03_protocol/sr-protocol.md …): " + "; ".join(why))
    if AI_NAME.search(reviewer):
        raise Refused(f"{reviewer!r} looks like an AI; only the human reviewers named in project.yaml review.reviewers "
                      "record decisions (AI suggestions go to ai-suggestions.csv); " + AI_HINT)
    allowed = human_reviewers(project)
    if reviewer != CONSENSUS and reviewer not in allowed:
        raise Refused(f"reviewer {reviewer!r} is not in project.yaml review.reviewers ({', '.join(allowed) or 'empty'})")
    recs, reasons = records(project), protocol_reasons(project)
    state = resolve(project) if stage == "ft" else None
    probs = []
    lat = latest(project) if reviewer == CONSENSUS else {}
    for r in rows_in:
        rid = (r.get("rec_id") or "").strip()
        dec = (r.get("decision") or "").strip().casefold()
        reason = (r.get("reason") or "").strip()
        if rid not in recs:
            probs.append(f"{rid or '(blank)'}: no such record")
            continue
        if recs[rid].get("duplicate_of"):
            probs.append(f"{rid}: duplicate of {recs[rid]['duplicate_of']}; decide on the original")
            continue
        if dec not in DECISIONS:
            raise ValueError(f"{rid}: decision {dec!r} must be include, exclude or maybe")
        if reviewer == CONSENSUS:
            gone = [h for h in allowed if (stage, rid, h) not in lat]
            if len(allowed) < 2 or gone:
                probs.append(f"{rid}: consensus is refused until both human reviewers have decided this record"
                             + (f" (missing: {', '.join(gone)})" if gone else ""))
                continue
        if stage == "ft" and state["ta"].get(rid, {}).get("final") != "include":
            probs.append(f"{rid}: did not pass title/abstract screening")
        if stage == "ft" and dec == "exclude":
            if not reason:
                probs.append(f"{rid}: a full-text exclusion needs --reason from the protocol list")
            elif reason.casefold() != NOT_RETRIEVED and reason.casefold() not in reasons:
                probs.append(f"{rid}: reason {reason!r} is not in the protocol's full-text exclusion reasons "
                             f"({'; '.join(reasons) or 'none listed'})")
    if probs:
        raise Refused("\n".join(probs))
    at = dt.date.today().isoformat()
    append_csv(Path(project) / SCREENING, SCREEN_COLS,
               [{"stage": stage, "rec_id": r["rec_id"].strip(), "reviewer": reviewer,
                 "decision": r["decision"].strip().casefold(), "reason": (r.get("reason") or "").strip(),
                 "study": (r.get("study") or "").strip(), "at": at} for r in rows_in])
    return len(rows_in)


def sheet(project: Path, stage: str, reviewer: str) -> Path:
    recs, st = records(project), resolve(project)
    sug = {(r.get("stage"), r.get("rec_id")): r for r in read_csv(Path(project) / SUGGESTIONS)}
    rows = []
    for rid in st[stage]:
        rec, s = recs[rid], sug.get((stage, rid), {})
        rows.append({"rec_id": rid, "title": rec.get("title", ""), "year": rec.get("year", ""),
                     "journal": rec.get("journal", ""), "abstract": rec.get("abstract", ""),
                     "ai_suggestion": s.get("suggestion", ""), "ai_reason": s.get("reason", "")})
    path = Path(project) / "reviews" / "tmp" / f"screening-{stage}-{slug(reviewer)}.csv"
    write_csv(path, SHEET_COLS, rows)
    return path


def suggest(project: Path, stage: str, src: Path) -> int:
    recs, probs, out = records(project), [], []
    for i, r in enumerate(read_csv(src), start=2):
        rid = (r.get("rec_id") or "").strip()
        s = (r.get("suggestion") or "").strip().casefold()
        if rid not in recs:
            probs.append(f"line {i}: {rid or '(blank)'} is not a record")
        if s not in DECISIONS:
            probs.append(f"line {i}: suggestion {s!r} must be include, exclude or maybe")
        out.append({"stage": stage, "rec_id": rid, "suggestion": s, "reason": (r.get("reason") or "").strip(),
                    "source": "AI (role screen-suggest)"})
    if probs:
        raise Refused("\n".join(probs))
    keep = [r for r in read_csv(Path(project) / SUGGESTIONS) if r.get("stage") != stage]
    write_csv(Path(project) / SUGGESTIONS, SUGGEST_COLS, keep + out)
    return len(out)


def kappa(project: Path, stage: str) -> tuple[float | None, int, float]:
    humans = human_reviewers(project)
    if len(humans) != 2:
        raise ValueError(f"kappa needs exactly two reviewers in review.reviewers (found {len(humans)})")
    a, b = humans
    lat = latest(project)
    pairs = [(lat[(stage, rid, a)]["decision"], lat[(stage, rid, b)]["decision"]) for rid in resolve(project)[stage]
             if (stage, rid, a) in lat and (stage, rid, b) in lat]
    n = len(pairs)
    if not n:
        return None, 0, 0.0
    po = sum(x == y for x, y in pairs) / n
    cats = {x for pr in pairs for x in pr}
    pe = sum((sum(x == c for x, _ in pairs) / n) * (sum(y == c for _, y in pairs) / n) for c in cats)
    return (None if pe >= 1 else (po - pe) / (1 - pe)), n, po


# ---------------------------------------------------------------- counts and check

def _final_field(e: dict, field: str) -> str:
    rows = e["rows"]
    if CONSENSUS in rows:
        return (rows[CONSENSUS].get(field) or "").strip()
    return next(((r.get(field) or "").strip() for k, r in rows.items() if k != CONSENSUS and (r.get(field) or "").strip()), "")


def compute_counts(project: Path) -> tuple[dict, list[str]]:
    recs, st = records(project), resolve(project)
    unresolved = [f"{s} {rid}: {e['why']}" for s in STAGES for rid, e in st[s].items() if e["final"] is None]
    by_db: dict[str, int] = {}
    for r in recs.values():
        by_db[r.get("database", "")] = by_db.get(r.get("database", ""), 0) + 1
    reg = sum(n for d, n in by_db.items() if REGISTER_NAME.search(d))
    reasons: dict[str, int] = {}
    nr, inc = 0, []
    for rid, e in st["ft"].items():
        if e["final"] == "exclude":
            why = _final_field(e, "reason").casefold()
            if why == NOT_RETRIEVED:
                nr += 1
            else:
                reasons[why] = reasons.get(why, 0) + 1
        elif e["final"] == "include":
            inc.append(_final_field(e, "study") or rid)
    fixed = {"databases": sum(by_db.values()) - reg, "registers": reg,
             "duplicates": sum(1 for r in recs.values() if r.get("duplicate_of")),
             "screened": len(st["ta"]), "excluded": sum(1 for e in st["ta"].values() if e["final"] == "exclude"),
             "sought": len(st["ft"]), "not_retrieved": nr, "assessed": len(st["ft"]) - nr,
             "reports_excluded": sum(reasons.values()), "studies": len(set(inc)), "reports": len(inc)}
    return {"fixed": fixed, "sources": dict(sorted(by_db.items())), "reasons": dict(sorted(reasons.items()))}, unresolved


def labelled(data: dict) -> dict[str, int]:
    out = {label: data["fixed"][key] for key, label in FIXED}
    out.update({f"records identified: {db}": n for db, n in data["sources"].items()})
    out.update({f"reports excluded: {why}": n for why, n in data["reasons"].items()})
    return out


def write_counts(project: Path, data: dict) -> Path:
    if len(data["sources"]) > 29 or len(data["reasons"]) > 49:
        raise ValueError("more than 29 sources or 49 exclusion reasons do not fit the id layout (plan D10)")
    log = resultlog.ResultLog(project, SCREENING, LOG_REL, "screening.py counts")
    for i, (key, label) in enumerate(FIXED, start=1):
        log.add("A0", "observed", label, data["fixed"][key], "n", number=i)
    for i, (db, n) in enumerate(data["sources"].items(), start=21):
        log.add("A0", "observed", f"records identified: {db}", n, "n", number=i)
    for i, (why, n) in enumerate(data["reasons"].items(), start=51):
        log.add("A0", "observed", f"reports excluded: {why}", n, "n", number=i)
    return log.save(DOC_REL)


def check(project: Path) -> list[tuple[str, str, str]]:
    project = Path(project)
    if not (project / RECORDS).is_file():
        return [("block", f"{RECORDS}:1", "no screening log: import the search exports (screening.py import)")]
    found: list[tuple[str, str, str]] = []
    names = reviewers(project)
    for name in names:
        if AI_NAME.search(name):
            found.append(("block", "project.yaml:1", f"{name!r} in review.reviewers looks like an AI; AI never counts as a reviewer ({AI_HINT})"))
    humans = human_reviewers(project)
    if len(humans) < 2:
        found.append(("block", "project.yaml:1", f"review.reviewers lists {len(humans)} human reviewer(s); two are needed"))
    st = resolve(project)
    for stage in STAGES:
        for rid, e in st[stage].items():
            line = max((r["_line"] for r in e["rows"].values()), default=1)
            if e["final"] is None:
                found.append(("block", f"{SCREENING}:{line}", f"{rid} ({stage}): {e['why']}"))
            elif stage == "ft" and e["final"] == "exclude":
                rows = [e["rows"][CONSENSUS]] if CONSENSUS in e["rows"] else [r for k, r in e["rows"].items() if k != CONSENSUS]
                if any(not (r.get("reason") or "").strip() for r in rows):
                    found.append(("block", f"{SCREENING}:{line}", f"{rid}: full-text exclusion without a reason"))
    found += hits_findings(project, list(records(project).values()))
    if not any(s == "block" for s, _, _ in found):
        data, _ = compute_counts(project)
        fresh = labelled(data)
        path = project / "ledgers" / "results-ledger.json"
        led_recs = json.loads(path.read_text(encoding="utf-8-sig")).get("results", []) if path.is_file() else []
        led = {r.get("label"): r.get("value") for r in led_recs if isinstance(r, dict) and r.get("source_file") == LOG_REL}
        if not led:
            found.append(("block", "ledgers/results-ledger.json:1", "PRISMA counts are not in the results ledger: run screening.py counts"))
        elif led != fresh:
            diff = [f"{k}: ledger {led.get(k)}, now {fresh.get(k)}" for k in sorted(set(led) | set(fresh)) if led.get(k) != fresh.get(k)]
            found.append(("block", "ledgers/results-ledger.json:1",
                          "ledger counts differ from a fresh counts run (" + "; ".join(diff[:5]) + "); run screening.py counts"))
    return found


# ---------------------------------------------------------------- CLI

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("import")
    s.add_argument("file")
    s.add_argument("--database", required=True)
    sub.add_parser("dedupe")
    s = sub.add_parser("decide")
    s.add_argument("--stage", choices=STAGES, required=True)
    s.add_argument("--reviewer", required=True)
    s.add_argument("--rec")
    s.add_argument("--decision", choices=DECISIONS)
    s.add_argument("--reason", default="")
    s.add_argument("--study", default="")
    s.add_argument("--file")
    s = sub.add_parser("sheet")
    s.add_argument("--stage", choices=STAGES, required=True)
    s.add_argument("--reviewer", required=True)
    s = sub.add_parser("suggest")
    s.add_argument("--stage", choices=STAGES, required=True)
    s.add_argument("--from", dest="src", required=True)
    for name in ("conflicts", "kappa"):
        sub.add_parser(name).add_argument("--stage", choices=STAGES, required=True)
    sub.add_parser("counts")
    sub.add_parser("check")
    a = ap.parse_args(argv)
    project = Path(a.project)
    if not (project / "project.yaml").is_file():
        print(f"screening: {a.project} is not a project folder (no project.yaml)", file=sys.stderr)
        return 2
    try:
        if a.cmd == "import":
            n, found = import_file(project, Path(a.file), a.database)
            for sev, loc, msg in found:
                print(f"E-SCR {sev} {loc}: {msg}")
            print(f"screening: {n} records imported from {Path(a.file).name} ({a.database})")
            return 0
        if a.cmd == "dedupe":
            n, d = dedupe(project)
            print(f"screening: {n} records, {d} marked as duplicates (both rows kept)")
            return 0
        if a.cmd == "decide":
            if a.file:
                rows = [r for r in read_csv(Path(a.file)) if (r.get("decision") or "").strip()]
            elif a.rec and a.decision:
                rows = [{"rec_id": a.rec, "decision": a.decision, "reason": a.reason, "study": a.study}]
            else:
                print("screening: decide needs --rec and --decision, or --file", file=sys.stderr)
                return 2
            n = decide(project, a.stage, a.reviewer, rows)
            print(f"screening: {n} decision(s) recorded for {a.reviewer} ({a.stage})")
            return 0
        if a.cmd == "sheet":
            path = sheet(project, a.stage, a.reviewer)
            print(f"screening: wrote {path.relative_to(project).as_posix()} (fill 'decision'; the AI columns are "
                  "suggestions, never decisions)")
            return 0
        if a.cmd == "suggest":
            n = suggest(project, a.stage, Path(a.src))
            print(f"screening: {n} AI suggestions for {a.stage} written to {SUGGESTIONS} (suggestions, not decisions)")
            return 0
        if a.cmd == "conflicts":
            lines = [f"{rid}: {e['why']}" for rid, e in resolve(project)[a.stage].items() if e["final"] is None]
            for ln in lines:
                print(ln)
            print(f"screening: {len(lines)} unresolved at {a.stage}")
            return 1 if lines else 0
        if a.cmd == "kappa":
            k, n, po = kappa(project, a.stage)
            if not n:
                print(f"kappa {a.stage}: no record decided by both reviewers")
            elif k is None:
                print(f"kappa {a.stage}: undefined (all decisions in one category; n = {n})")
            else:
                print(f"kappa {a.stage}: {k:.2f} (n = {n}; agreement {po * 100:.1f}%)")
            return 0
        if a.cmd == "counts":
            data, unresolved = compute_counts(project)
            if unresolved:
                for ln in unresolved:
                    print(ln)
                print("screening: counts not written; resolve every record first (conflicts --stage …)")
                return 1
            n, bad = resultlog.import_merged(project, write_counts(project, data))
            if bad:
                for x in bad:
                    print(x)
                return 1
            for label, v in labelled(data).items():
                print(f"{label} = {v}")
            print(f"screening: {n} PRISMA counts in the results ledger (A0, observed)")
            return 0
        found = check(project)
        for sev, loc, msg in found:
            print(f"E-SCR {sev} {loc}: {msg}")
        blocks = sum(1 for f in found if f[0] == "block")
        print(f"screening: {blocks} block, {len(found) - blocks} warn")
        return 1 if blocks else 0
    except Refused as e:
        print(f"screening: refused: {e}")
        return 1
    except results_ledger.LockedError as e:
        print(f"screening: {e}", file=sys.stderr)
        return 1
    except results_ledger.RelabelError as e:
        print(f"{e}\nscreening: labels changed; ledger not written", file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError, csv.Error) as e:
        print(f"screening: {type(e).__name__}: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
