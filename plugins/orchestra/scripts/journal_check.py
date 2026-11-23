#!/usr/bin/env python3
"""Journal facts from open registries for a submission shortlist: signals with sources, never verdicts.

  python journal_check.py <project> lookup <ISSN|title> [...] [--claim medline|scopus] [--open-access] [--concern TEXT]
  python journal_check.py <project> note <key> --source-url URL [--scope TEXT --scope-url URL] [--words N]
                                       [--abstract N] [--ref-style TEXT]
  python journal_check.py <project> table
  python journal_check.py <project> pick <key> --by NAME

lookup asks the NLM Catalog (E-utilities, db=nlmcatalog: MEDLINE indexing status, ISSNs, publisher), DOAJ (listing,
APC as listed, seal) and Crossref (title, publisher, ISSNs) through crolib/http.py and writes one record per journal
to 08_submission/journals.json (every field with its source and the lookup date) and the shortlist table
08_submission/journals.md. A title is first resolved to an ISSN (NLM Catalog, then Crossref); every source is then
asked for that ISSN. Signals: ISSN not found in any registry; an invalid ISSN check digit; a claimed MEDLINE indexing
the NLM Catalog does not confirm; a claimed Scopus indexing (not checkable with these open sources); an open-access
journal absent from DOAJ; publisher or title differing across sources; the author's own concerns. The tool never
judges a journal: it lists signals with their sources and the author decides.
note records what was read on the journal's own pages (scope, word and abstract limits, reference style) with the
page URL and date. pick, after the author has chosen, writes project.yaml target.journal, target.word_limit (abstract
limit) and target.text_words (main-text limit) and records who picked.
Exit codes: 0 = done; 1 = unknown journal key (note, pick); 2 = usage, missing project, network or API error
(nothing written). Standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import itertools
from http.client import HTTPException
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crolib import http  # noqa: E402

NCBI = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
DOAJ = "https://doaj.org/api/search/journals/"
CROSSREF = "https://api.crossref.org/journals"
TOOL = "clinical-research-orchestra"
JSON_REL = "08_submission/journals.json"
MD_REL = "08_submission/journals.md"
ISSN = re.compile(r"^\s*(\d{4})-?(\d{3}[\dXx])\s*$")
NAME_STOP = {"the", "ltd", "limited", "inc", "llc", "co", "publishing", "publishers", "publisher", "press", "group",
             "company", "gmbh", "bv", "sa", "plc", "of", "and"}
MIN_GAP = 0.34          # NCBI: at most 3 requests per second without a key
_last = 0.0
COLS = ("| Journal | ISSN | MEDLINE (NLM Catalog) | Open access / APC (DOAJ) | Limits: words / abstract | "
        "Reference style | Scope fit | Signals |")


class NetworkError(Exception):
    """Exit 2."""


class Refused(Exception):
    """Exit 1."""


def http_get(url: str) -> bytes:
    return http.get(url)


def _get(url: str) -> bytes | None:
    try:
        return http_get(url)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise NetworkError(f"{url.split('?')[0]}: HTTP {e.code}") from e
    except HTTPException as e:     # IncompleteRead, RemoteDisconnected...
        raise NetworkError(f"{url.split('?')[0]}: {e!r}") from e
    except OSError as e:            # URLError, timeouts, refused connections
        raise NetworkError(f"{url.split('?')[0]}: {getattr(e, 'reason', e)}") from e


def _ncbi(endpoint: str, **params) -> bytes | None:
    global _last
    wait = MIN_GAP - (time.monotonic() - _last)
    if wait > 0:
        time.sleep(wait)
    params.setdefault("tool", TOOL)
    try:
        return _get(NCBI + endpoint + "?" + urllib.parse.urlencode(params))
    finally:
        _last = time.monotonic()


def fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s).replace("đ", "d").replace("Đ", "D"))
    return re.sub(r"\s+", " ", "".join(c for c in s if not unicodedata.combining(c))).strip().casefold()


def norm_issn(s) -> str | None:
    m = ISSN.match(str(s or ""))
    return f"{m.group(1)}-{m.group(2).upper()}" if m else None


def issn_check_ok(issn: str) -> bool:
    d = issn.replace("-", "").upper()
    total = sum(int(c) * w for c, w in zip(d[:7], range(8, 1, -1)))
    check = (11 - total % 11) % 11
    return d[7] == ("X" if check == 10 else str(check))


def _tag(e) -> str:
    return e.tag.rsplit("}", 1)[-1]


def nlm(query: str, issn: str | None) -> dict | None:
    term = f"{issn}[issn]" if issn else f'"{query}"[Title]'
    raw = _ncbi("esearch.fcgi", db="nlmcatalog", term=term, retmode="json", retmax=5)
    ids = json.loads(raw).get("esearchresult", {}).get("idlist", []) if raw else []
    if not ids:
        return None
    xml = _ncbi("efetch.fcgi", db="nlmcatalog", id=ids[0], retmode="xml")
    if not xml:
        return None
    root = ET.fromstring(xml)
    els = list(root.iter())
    main = next((e for e in els if _tag(e) == "TitleMain"), None)
    title = next(((t.text or "").strip() for t in (main.iter() if main is not None else els)
                  if _tag(t) == "Title" and (t.text or "").strip()), "")
    publisher = next(((e.text or "").strip() for e in els if _tag(e) in ("Publisher", "Entity") and (e.text or "").strip()), "")
    statuses = [e.get("IndexingStatus", "") for e in els
                if _tag(e) == "IndexingSourceName" and (e.text or "").strip().upper() == "MEDLINE"]
    nlm_id = next(((e.text or "").strip() for e in els if _tag(e) == "NlmUniqueID"), ids[0])
    return {"title": title.rstrip(". "), "publisher": publisher.rstrip(",. "),
            "issns": [(norm_issn(e.text), e.get("IssnType", "")) for e in els if _tag(e) == "ISSN" and norm_issn(e.text)],
            "medline": any("currently" in s.lower() for s in statuses),
            "medline_detail": ", ".join(s for s in statuses if s) or "not listed for MEDLINE",
            "url": f"https://www.ncbi.nlm.nih.gov/nlmcatalog/{nlm_id}"}


def doaj(issn: str) -> dict | None:
    raw = _get(DOAJ + urllib.parse.quote(f"issn:{issn}") + "?pageSize=5")
    res = (json.loads(raw).get("results") or []) if raw else []
    if not res:
        return None
    r = res[0]
    bib = r.get("bibjson") or {}
    apc = bib.get("apc") or {}
    pub = bib.get("publisher")
    prices = [f"{m.get('price')} {m.get('currency', '')}".strip() for m in apc.get("max") or []
              if isinstance(m, dict) and m.get("price") is not None]
    return {"title": str(bib.get("title") or ""),
            "issns": [(i, t) for i, t in ((norm_issn(bib.get("pissn")), "print"), (norm_issn(bib.get("eissn")), "electronic")) if i],
            "publisher": str(pub.get("name", "") if isinstance(pub, dict) else pub or ""),
            "has_apc": apc.get("has_apc"), "apc": prices, "seal": bool((r.get("admin") or {}).get("seal")),
            "url": "https://doaj.org/toc/" + issn}


def crossref(query: str, issn: str | None) -> dict | None:
    if issn:
        raw = _get(f"{CROSSREF}/{issn}")
        items = [json.loads(raw)["message"]] if raw else []
    else:
        raw = _get(f"{CROSSREF}?query={urllib.parse.quote(query)}&rows=5")
        items = json.loads(raw)["message"].get("items", []) if raw else []
    if not items:
        return None
    m = items[0]
    issns = [(norm_issn(x.get("value")), x.get("type", "")) for x in m.get("issn-type") or [] if norm_issn(x.get("value"))]
    issns = issns or [(norm_issn(x), "") for x in m.get("ISSN") or [] if norm_issn(x)]
    return {"title": str(m.get("title") or ""), "publisher": str(m.get("publisher") or ""), "issns": issns,
            "url": f"{CROSSREF}/{issns[0][0]}" if issns else CROSSREF}


def _norm_name(s: str) -> str:
    return " ".join(w for w in re.sub(r"[^a-z0-9 ]+", " ", fold(s)).split() if w not in NAME_STOP)


def _differ(values: list[str]) -> bool:
    vals = sorted({_norm_name(v) for v in values} - {""})
    return any(not (a in b or b in a) for a, b in itertools.combinations(vals, 2))


def _signals(query, issn, claims, open_access, concerns, sources: dict) -> list[dict]:
    n, d, c = sources["NLM Catalog"], sources["DOAJ"], sources["Crossref"]
    out: list[dict] = []

    def add(text: str, source: str) -> None:
        out.append({"signal": text, "source": source})
    if issn and not issn_check_ok(issn):
        add(f"ISSN {issn} has an invalid check digit", "ISSN check digit")
    if not any((n, d, c)):
        add(f"'{query}' not found in the NLM Catalog, DOAJ or Crossref", "NLM Catalog, DOAJ, Crossref")
    if "medline" in claims and not (n and n["medline"]):
        add("claims MEDLINE indexing; the NLM Catalog does not list it as currently indexed for MEDLINE", "NLM Catalog")
    if "scopus" in claims:
        add("claims Scopus indexing; not checkable with the open sources used here; check the Scopus source list",
            "author's information")
    if open_access and d is None:
        add("presents itself as open access but is not listed in DOAJ", "DOAJ")
    for field in ("publisher", "title"):
        vals = {name: s[field] for name, s in sources.items() if s and s[field]}
        if _differ(list(vals.values())):
            add(f"{field} differs across sources: " + "; ".join(f"{k} '{v}'" for k, v in vals.items()),
                ", ".join(vals))
    for text in concerns:
        add(text, "author")
    return out


def lookup(query: str, claims=(), open_access: bool = False, concerns=(), today: str | None = None) -> dict:
    today = today or dt.date.today().isoformat()
    issn = norm_issn(query)
    n, c = nlm(query, issn), crossref(query, issn)
    if not issn:
        issn = next((i for s in (n, c) if s for i, _ in s["issns"]), None)
        if issn and n is None:
            n = nlm(query, issn)
        if issn and c is None:
            c = crossref(query, issn)
    d = doaj(issn) if issn else None
    sources = {"NLM Catalog": n, "DOAJ": d, "Crossref": c}
    issns: list[dict] = []
    for name, s in sources.items():
        for i, typ in (s["issns"] if s else []):
            if not any(x["value"] == i and x["source"] == name for x in issns):
                issns.append({"value": i, "type": typ, "source": name})
    return {
        "key": issn or fold(query), "query": query, "looked_up": today,
        "title": [{"value": s["title"], "source": name} for name, s in sources.items() if s and s["title"]],
        "issn": issns,
        "publisher": [{"value": s["publisher"], "source": name} for name, s in sources.items() if s and s["publisher"]],
        "medline": {"value": n["medline"] if n else None,
                    "detail": n["medline_detail"] if n else "not found in the NLM Catalog",
                    "source": "NLM Catalog", "url": n["url"] if n else ""},
        "doaj": {"listed": d is not None, "has_apc": d["has_apc"] if d else None, "apc": d["apc"] if d else [],
                 "seal": d["seal"] if d else False, "source": "DOAJ", "url": d["url"] if d else ""},
        "crossref": {"listed": c is not None, "source": "Crossref", "url": c["url"] if c else ""},
        "claims": sorted(set(claims)), "open_access_claimed": bool(open_access),
        "signals": _signals(query, issn, set(claims), open_access, list(concerns), sources),
        "notes": {}, "picked": None,
    }


def load(project: Path) -> dict:
    p = Path(project) / JSON_REL
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {"journals": []}


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def _cell(s) -> str:
    return str(s).replace("|", "/").replace("\n", " ")


def table(data: dict) -> str:
    out = ["# Journal shortlist", "",
           "Facts come from tool lookups (source and date in `journals.json`); scope, limits and reference style from "
           "the journal's own pages (URL given). Signals are not verdicts: the author decides "
           "(Think. Check. Submit.: https://thinkchecksubmit.org/).", "", COLS, "|---|---|---|---|---|---|---|---|"]
    for r in data["journals"]:
        notes = r.get("notes") or {}

        def note(k: str) -> str:
            return str(notes[k]["value"]) if k in notes else "not noted"
        med = r["medline"]
        med_txt = {True: "yes", False: "no", None: "unknown"}[med["value"]] + f" ({med['detail']}; {r['looked_up']})"
        dj = r["doaj"]
        if dj["listed"]:
            apc = ", ".join(dj["apc"]) or ("none listed" if dj["has_apc"] is False else "not stated")
            oa = f"in DOAJ; APC {apc}" + ("; DOAJ seal" if dj["seal"] else "")
        else:
            oa = "not in DOAJ"
        scope = notes.get("scope")
        title = r["title"][0]["value"] if r["title"] else r["query"]
        if r.get("picked"):
            title += f" — picked by {r['picked']['by']}"
        cells = (title, ", ".join(dict.fromkeys(i["value"] for i in r["issn"])) or "-", med_txt, oa,
                 f"{note('word_limit')} / {note('abstract_limit')}", note("ref_style"),
                 f"{scope['value']} ({scope['source']})" if scope else "not noted",
                 "; ".join(f"{s['signal']} [{s['source']}]" for s in r["signals"]) or "none")
        out.append("| " + " | ".join(_cell(c) for c in cells) + " |")
    return "\n".join(out) + "\n"


def save(project: Path, data: dict) -> None:
    _write(Path(project) / JSON_REL, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    _write(Path(project) / MD_REL, table(data))


def find(data: dict, key: str) -> dict | None:
    k = norm_issn(key) or fold(key)
    for r in data["journals"]:
        if r["key"] == k or any(i["value"] == k for i in r["issn"]) or any(fold(t["value"]) == k for t in r["title"]):
            return r
    return None


def note(project: Path, key: str, source_url: str, scope=None, scope_url=None, words=None, abstract=None,
         ref_style=None, today: str | None = None) -> dict:
    data = load(project)
    rec = find(data, key)
    if rec is None:
        raise Refused(f"no journal '{key}' in {JSON_REL}: run lookup first")
    today = today or dt.date.today().isoformat()
    for field, val, url in (("scope", scope, scope_url or source_url), ("word_limit", words, source_url),
                            ("abstract_limit", abstract, source_url), ("ref_style", ref_style, source_url)):
        if val is not None:
            rec.setdefault("notes", {})[field] = {"value": val, "source": url, "date": today}
    save(project, data)
    return rec


def set_target(project: Path, values: dict) -> None:
    """Replace or add `  key: value` lines under the top-level `target:` block of project.yaml (LF written)."""
    path = Path(project) / "project.yaml"
    lines = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").split("\n")
    head = re.compile(r"^target:\s*(#.*)?$")
    inline = re.compile(r"^target:\s*(?:\{\s*\}|null|~)?\s*(?:#.*)?$")
    found = next((i for i, ln in enumerate(lines) if ln.startswith("target:")), None)
    if found is None:
        at = len(lines) - 1 if lines and lines[-1] == "" else len(lines)
        lines.insert(at, "target:")
        found = at
    else:       # trailing space, comment, {} or null become a plain block header (projectcfg reads no comments)
        if not (head.match(lines[found]) or inline.match(lines[found])):
            raise ValueError(f"project.yaml: 'target' already has an inline value ({lines[found].strip()!r}); "
                             "make it a block (target:, then indented keys) and rerun")
        lines[found] = "target:"
    start = found
    end = start + 1
    while end < len(lines) and lines[end].startswith(" "):
        end += 1
    for key, val in values.items():
        if val is None:
            text = "null"
        elif isinstance(val, int) and not isinstance(val, bool):
            text = str(val)
        else:       # projectcfg reads no escapes: keep the value inside plain double quotes
            text = '"' + str(val).replace("\\", "/").replace('"', "'") + '"'
        new = f"  {key}: {text}"
        idx = next((i for i in range(start + 1, end) if re.match(rf"^  {re.escape(key)}:", lines[i])), None)
        if idx is None:
            lines.insert(start + 1, new)
            end += 1
        else:
            lines[idx] = new
    _write(path, "\n".join(lines))


def pick(project: Path, key: str, by: str, today: str | None = None) -> dict:
    data = load(project)
    rec = find(data, key)
    if rec is None:
        raise Refused(f"no journal '{key}' in {JSON_REL}: run lookup first")
    notes = rec.get("notes") or {}
    values: dict = {"journal": rec["title"][0]["value"] if rec["title"] else rec["query"]}
    if "abstract_limit" in notes:
        values["word_limit"] = int(notes["abstract_limit"]["value"])
    if "word_limit" in notes:
        values["text_words"] = int(notes["word_limit"]["value"])
    set_target(project, values)
    for r in data["journals"]:
        r["picked"] = None
    rec["picked"] = {"by": by, "at": today or dt.date.today().isoformat()}
    save(project, data)
    return values


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    sub = ap.add_subparsers(dest="cmd", required=True)
    lk = sub.add_parser("lookup")
    lk.add_argument("queries", nargs="+")
    lk.add_argument("--claim", action="append", choices=["medline", "scopus"], default=[])
    lk.add_argument("--open-access", action="store_true")
    lk.add_argument("--concern", action="append", default=[])
    nt = sub.add_parser("note")
    nt.add_argument("key")
    nt.add_argument("--source-url", required=True)
    nt.add_argument("--scope")
    nt.add_argument("--scope-url")
    nt.add_argument("--words", type=int)
    nt.add_argument("--abstract", type=int)
    nt.add_argument("--ref-style")
    sub.add_parser("table")
    pk = sub.add_parser("pick")
    pk.add_argument("key")
    pk.add_argument("--by", required=True)
    a = ap.parse_args(argv)
    project = Path(a.project)
    if not project.is_dir():
        print(f"journal_check: project folder {a.project} not found", file=sys.stderr)
        return 2
    try:
        if a.cmd == "lookup":
            recs = [lookup(q, a.claim, a.open_access, a.concern) for q in a.queries]   # all lookups before any write
            data = load(project)
            for rec in recs:
                old = find(data, rec["key"])
                if old is not None:
                    rec["notes"], rec["picked"] = old.get("notes") or {}, old.get("picked")
                    data["journals"][data["journals"].index(old)] = rec
                else:
                    data["journals"].append(rec)
                title = rec["title"][0]["value"] if rec["title"] else rec["query"]
                print(f"{rec['key']}: {title}; {len(rec['signals'])} signal(s)")
                for s in rec["signals"]:
                    print(f"  signal [{s['source']}]: {s['signal']}")
            save(project, data)
        elif a.cmd == "note":
            note(project, a.key, a.source_url, a.scope, a.scope_url, a.words, a.abstract, a.ref_style)
            print(f"journal_check: noted {a.key}")
        elif a.cmd == "table":
            data = load(project)
            save(project, data)
            print(f"journal_check: {MD_REL} ({len(data['journals'])} journals)")
        else:
            values = pick(project, a.key, a.by)
            print("journal_check: project.yaml target " + ", ".join(f"{k}={v}" for k, v in values.items()))
    except Refused as e:
        print(f"journal_check: {e}")
        return 1
    except (NetworkError, ValueError, KeyError, ET.ParseError, OSError) as e:
        print(f"journal_check: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
