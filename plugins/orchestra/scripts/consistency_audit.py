#!/usr/bin/env python3
"""Cross-file consistency audit of a project's writing and presentation text (E-CONS).

  python consistency_audit.py <project> [FILES...] [--lang vi|en]

Default files: 06_writing/**/*.md and 07_present/**/*.md (<stem>.rendered.md preferred when it exists),
plus every string value in 07_present/**/*.json (reported as <file>:<json-path>). Placeholders in a
file without a rendered copy are rendered in memory from ledgers/results-ledger.json.

Checks: same quantity (same words before a number, same unit, different value) = block; sample size
written approximately or as a decimal = block; date ranges sharing one end but not the other = block;
abstract numbers found nowhere else = warn; percentage columns not summing to the total row = warn;
term variants (project.yaml terms: + built-ins) = warn. A line containing <!-- cons-ok: reason --> is
skipped. 03_protocol/sample-size.md, when present, is read as a reference source for the same-quantity
check only: a typed number elsewhere that differs from it under the same key words is a warn (per-group and
total sizes share key words, so never a block); no other check runs on it. Exit 0 = no block; 1 = at least one block; 2 = usage or I/O error. Standard library only.

Deliberate blind spots (noise trade-offs; the consistency-auditor agent covers them):
- integers <= 10 and years 1900-2100 are never compared as quantities ("5 deaths" vs "7 deaths");
- a quantity whose last key word is p, or, rr, hr, ci, ktc, sd, auc, a group word (nhóm, group) or a
  reference word (mục, bảng, hình, figure, table...) is skipped; so are CI bounds, ranges (7-9%),
  comparisons (<7%) and anything inside a CI expression ("OR 1,42" vs "OR 1,52" is not caught);
- the key is only the words BEFORE the number, so "tỷ lệ đáp ứng là 85%" and "có 86,3% tỷ lệ đáp ứng"
  are different keys;
- date ranges are compared globally, so an enrolment and a follow-up window sharing a start can block
  (escape with cons-ok);
- the percentage-sum check only runs on a row whose first cell is Tổng / Tổng cộng / Total and says 100%.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crolib import numfmt, projectcfg  # noqa: E402
import render_results  # noqa: E402

SAMPLE_SIZE = "03_protocol/sample-size.md"
STOP = frozenset("là của có và được trong với ở cho các những một này "
                 "is was of the a an in at to".split())
SKIP_LAST = frozenset({"p", "pvalue", "p-value", "ci", "ktc", "or", "rr", "hr", "sd", "auc"})
REF_WORDS = frozenset("mục bảng hình đồ chương lục xem section table figure fig appendix".split())
GROUP_WORDS = frozenset({"nhóm", "group", "arm"})
CI_WORDS = frozenset({"ktc", "ci"})
TIME_UNITS = frozenset("ngày tháng năm tuần giờ day days month months year years week weeks hour hours".split())
_N = r"\d+(?:[.,]\d+)*%?"
CMP = re.compile(r"(?<![\w.,])[<>≤≥]=?\s*" + _N + r"|(?<![\w.,])" + _N + r"\s*[–—-]\s*" + _N)
THOUSANDS = {"vi": re.compile(r"\d{1,3}(?:\.\d{3})+"), "en": re.compile(r"\d{1,3}(?:,\d{3})+")}
FOLLOW = re.compile(r"[^\w]*([^\W\d_]+)")
BUILTIN_TERMS = {"HbA1c": ["HbA1C", "Hba1c", "HBA1C"], "đái tháo đường": ["tiểu đường"]}

CONS_OK = re.compile(r"<!--\s*cons-ok\b[^>]*-->", re.I)
FENCE = re.compile(r"^\s*(```|~~~)")
HEADING = re.compile(r"^\s{0,3}#{1,6}\s")
REF_HEADING = re.compile(r"^\s{0,3}#{1,6}\s*(tài liệu tham khảo|references?|bibliography|danh mục tài liệu)", re.I)
LIST_MARK = re.compile(r"\s*(?:[-*+]\s+)?\d+[.)]\s")
MASKS = [re.compile(p, re.S) for p in (
    r"\{\{[^{}]*\}\}", r"<!--.*?-->", r"https?://\S+", r"`[^`]*`", r"\[[^\]]*\]",
    r"\bR-[A-Za-z0-9]+-\d+(?:\.\w+)?")]
CUT = re.compile(r"[;!?|()\[\]{}]|[.,](?=\s|$)")
WORD = re.compile(r"\w+(?:[.,]\d+)*")
NEXT_WORD = re.compile(r"\s*([^\W\d_]+)")

_MON = (r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|"
        r"sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)")
MONTHS = {m: i for i, m in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split(), 1)}
DATE = re.compile(
    r"(?<![\w/.])(?:"
    r"(?P<vi>tháng\s+(?P<vm>\d{1,2})\s*(?:/|năm)\s*(?P<vy>\d{4}))"
    r"|(?P<dmy>(?P<dd>\d{1,2})/(?P<dm>\d{1,2})/(?P<dy>\d{4}))"
    r"|(?P<my>(?P<mm>\d{1,2})/(?P<my_y>\d{4}))"
    r"|(?P<iso>(?P<iy>\d{4})-(?P<im>\d{2})(?:-(?P<id>\d{2}))?)"
    r"|(?P<mon>(?P<mn>" + _MON + r")\.?,?\s+(?P<mony>\d{4}))"
    r")(?![\d/])", re.I)
DATE_SEP = re.compile(r"\s*(?:–|—|-|đến|to|until)\s*", re.I)

APPROX = re.compile(r"≈|~|(?<!\w)(?:khoảng|xấp xỉ|about|approximately)(?!\w)", re.I)
TOK = re.compile(r"\d+(?:[.,]\d+)?%?|[^\W\d_]+")
PART = re.compile(r"(?<!\w)(?:bệnh nhân|người bệnh|đối tượng|trường hợp|ca|patients?|participants?|"
                  r"subjects?|cases?)(?!\w)", re.I)
PRE_N = re.compile(r"(?:(?<!\w)n|cỡ mẫu|sample size)[^.;|\d]{0,20}$", re.I)
PRE_N_DEC = re.compile(r"(?:(?<!\w)n\s*[=:≈~]?|cỡ mẫu[^.;|\d]{0,20}|sample size[^.;|\d]{0,20})\s*$", re.I)
TOTAL_ROW = re.compile(r"^[\s*_]*(tổng|tổng cộng|total)[\s*_:.]*$", re.I)
SEP_CELL = re.compile(r"^\s*:?-{2,}:?\s*$")


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def _blank(text: str, pattern) -> str:
    return pattern.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)


def mask(text: str) -> str:
    for p in MASKS:
        text = _blank(text, p)
    return text


class Line:
    __slots__ = ("loc", "text", "skip", "nonum")

    def __init__(self, loc, text, skip=False, nonum=False):
        self.loc, self.text, self.skip, self.nonum = loc, text, skip, nonum


class Doc:
    def __init__(self, label, lines, is_abstract=False):
        self.label, self.lines, self.is_abstract = label, lines, is_abstract


# ---- loading -------------------------------------------------------------------------------------

def _label(path: Path, project: Path) -> str:
    try:
        return path.resolve().relative_to(project.resolve()).as_posix()
    except ValueError:
        return str(path)


def _md_lines(label: str, text: str) -> list[Line]:
    out: list[Line] = []
    fence = in_front = in_refs = False
    for n, raw in enumerate(text.split("\n"), start=1):
        line = raw.rstrip("\r")
        skip = nonum = False
        if n == 1 and line.strip() == "---":
            in_front = True
            skip = True
        elif in_front:
            skip = True
            if line.strip() in ("---", "..."):
                in_front = False
        elif FENCE.match(line):
            fence = not fence
            skip = True
        elif fence:
            skip = True
        else:
            if HEADING.match(line):
                in_refs = bool(REF_HEADING.match(line))
                nonum = True
            elif in_refs:
                nonum = True
            if CONS_OK.search(line):
                skip = True
        out.append(Line(f"{label}:{n}", line, skip, nonum))
    return out


def _json_strings(node, path=""):
    if isinstance(node, str):
        yield path, node
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from _json_strings(v, f"{path}.{k}" if path else str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _json_strings(v, f"{path}[{i}]")


def _load_ledger(project: Path) -> dict:
    try:
        with open(project / "ledgers" / "results-ledger.json", encoding="utf-8-sig") as fh:
            data = json.load(fh)
        res = data.get("results") if isinstance(data, dict) else None
        return {r["id"]: r for r in res if isinstance(r, dict) and isinstance(r.get("id"), str)} if isinstance(res, list) else {}
    except (OSError, ValueError):
        return {}


def _load_doc(path: Path, project: Path, by_id: dict, lang: str, findings: list) -> Doc:
    label = _label(path, project)
    is_abs = "abstract" in path.name.lower()
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        findings.append(("warn", label, "file is not valid UTF-8, skipped"))
        return Doc(label, [], is_abs)
    if path.suffix.lower() == ".json":
        try:
            data = json.loads(text)
        except ValueError as e:
            findings.append(("warn", label, f"invalid JSON, skipped: {e}"))
            return Doc(label, [], is_abs)
        lines = []
        for jp, s in _json_strings(data):
            if by_id and "{{" in s:
                s = render_results.render_text(s, by_id, lang)[0]
            for part in s.split("\n"):
                lines.append(Line(f"{label}:{jp}", part, bool(CONS_OK.search(part))))
        return Doc(label, lines, is_abs)
    if by_id and "{{" in text:
        text = render_results.render_text(text, by_id, lang)[0]
    return Doc(label, _md_lines(label, text), is_abs)


def _numbered_copy(p: Path) -> bool:
    """x.numbered.md (or its rendered form) when the plain x.md / x.rendered.md exists."""
    stem = p.name[:-len(".rendered.md")] if p.name.endswith(".rendered.md") else p.name[:-len(".md")]
    if not stem.endswith(".numbered"):
        return False
    plain = stem[:-len(".numbered")]
    return p.with_name(plain + ".md").exists() or p.with_name(plain + ".rendered.md").exists()


def _discover(project: Path) -> list[Path]:
    found: list[Path] = []
    for sub in ("06_writing", "07_present"):
        base = project / sub
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*.md")):
            if _numbered_copy(p):
                continue
            if p.name.endswith(".rendered.md"):
                found.append(p)
            elif not p.with_name(p.stem + ".rendered.md").exists():
                found.append(p)
    pres = project / "07_present"
    if pres.is_dir():
        found.extend(sorted(pres.rglob("*.json")))
    return found


# ---- terms ---------------------------------------------------------------------------------------

def _unq(s: str) -> str:
    s = s.strip()
    return s[1:-1] if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'" else s


def _read_terms(project: Path) -> dict[str, list[str]]:
    terms = {k: list(v) for k, v in BUILTIN_TERMS.items()}
    path = project / "project.yaml"
    if not path.is_file():
        return terms
    in_terms, cur = False, None
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        s = raw.strip()
        if indent == 0:
            in_terms, cur = s == "terms:" or s.startswith("terms:"), None
            continue
        if not in_terms:
            continue
        if s.startswith("- "):
            if cur is not None:
                terms[cur].append(_unq(re.sub(r"\s+#.*$", "", s[2:])))
            continue
        key, _, val = s.partition(":")
        cur = _unq(key)
        terms.setdefault(cur, [])
        val = re.sub(r"\s+#.*$", "", val).strip()
        if val.startswith("[") and val.endswith("]"):
            terms[cur].extend(_unq(x) for x in val[1:-1].split(",") if x.strip())
        elif val:
            terms[cur].append(_unq(val))
    return terms


# ---- numbers and dates ----------------------------------------------------------------------------

def _locate(line: str, tok: str, pos: int) -> int:
    """Index of the token the way numfmt matched it (not inside a longer word or number)."""
    i = line.find(tok, pos)
    while i > 0 and (line[i - 1].isalnum() or line[i - 1] in "_.,"):
        i = line.find(tok, i + 1)
    return i


def _tokens(dm: str, lang: str = "vi") -> list[tuple[str, Decimal, int, int]]:
    out, pos = [], 0
    thousands = THOUSANDS.get(lang)
    for tok, val, dec in numfmt.parse_tokens(dm, "any"):
        i = _locate(dm, tok, pos)
        if i < 0:
            continue
        pos = i + len(tok)
        body = tok.rstrip("%")
        if thousands is not None and thousands.fullmatch(body):
            val, dec = Decimal(re.sub(r"[.,]", "", body)), 0
        out.append((tok, val, dec, i))
    return out


def _date_value(m) -> tuple[int, int] | None:
    g = m.groupdict()
    if g["vi"]:
        mo, y = int(g["vm"]), int(g["vy"])
    elif g["dmy"]:
        if not 1 <= int(g["dd"]) <= 31:
            return None
        mo, y = int(g["dm"]), int(g["dy"])
    elif g["my"]:
        mo, y = int(g["mm"]), int(g["my_y"])
    elif g["iso"]:
        if g["id"] and not 1 <= int(g["id"]) <= 31:
            return None
        mo, y = int(g["im"]), int(g["iy"])
    else:
        mo, y = MONTHS[g["mn"].lower()[:3]], int(g["mony"])
    return (y, mo) if 1 <= mo <= 12 else None


def _dates(text: str):
    """Return (masked text, [(start, end, written text)])."""
    dates = []
    for m in DATE.finditer(text):
        v = _date_value(m)
        if v is not None:
            dates.append((m, v))
    ranges = []
    for (a, va), (b, vb) in zip(dates, dates[1:]):
        if DATE_SEP.fullmatch(text[a.end():b.start()]):
            ranges.append((va, vb, text[a.start():b.end()]))
    masked = text
    for m, _ in dates:
        masked = masked[:m.start()] + " " * (m.end() - m.start()) + masked[m.end():]
    return masked, ranges


class Info:
    __slots__ = ("loc", "dm", "km", "tokens", "ranges", "cmp_idx")


def _analyse(doc: Doc, lang: str = "vi") -> list[Info]:
    out = []
    for ln in doc.lines:
        if ln.skip:
            continue
        info = Info()
        info.loc = ln.loc
        masked = mask(ln.text)
        info.dm, info.ranges = _dates(masked)
        info.km, info.cmp_idx = info.dm, set()
        for m in CMP.finditer(info.dm):
            info.km = info.km[:m.start()] + " " * (m.end() - m.start()) + info.km[m.end():]
            info.cmp_idx.update(range(m.start(), m.end()))
        if ln.nonum:
            info.tokens = []
        else:
            info.tokens = _tokens(info.dm, lang)
            lm = LIST_MARK.match(info.dm)
            if lm:
                ds = re.search(r"\d", info.dm).start()
                info.tokens = [t for t in info.tokens if t[3] != ds]
        out.append(info)
    return out


def _unit(tok: str, dec: int) -> str:
    return "%" if tok.endswith("%") else ("dec" if dec else "int")


def _trivial(tok: str, val: Decimal, dec: int) -> bool:
    if dec == 0 and not tok.endswith("%"):
        if 1900 <= val <= 2100 or abs(val) <= 10:
            return True
    return False


def _same(v1: Decimal, d1: int, v2: Decimal, d2: int) -> bool:
    d = min(d1, d2)
    return numfmt.round_half_up(v1, d) == numfmt.round_half_up(v2, d)


def _key(dm: str, idx: int, end: int, unit: str):
    seg = CUT.split(dm[:idx])[-1]
    words = [w for w in (nfc(x.lower()) for x in WORD.findall(seg)) if w not in STOP]
    prefix = tuple(words[-4:])
    ci = bool(CI_WORDS & set(words)) or "khoảng tin cậy" in " ".join(words)
    nxt = ""
    if unit != "%":
        mm = NEXT_WORD.match(dm, end)
        if mm:
            w = nfc(mm.group(1).lower())
            if w in TIME_UNITS:  # a time point: keyed with its unit and the words after it
                follow, pos = [], mm.start(1)
                while len(follow) < 4:
                    fm = FOLLOW.match(dm, pos)
                    if not fm:
                        break
                    follow.append(nfc(fm.group(1).lower()))
                    pos = fm.end()
                nxt = " ".join(follow)
            else:
                nxt = "" if w in STOP else w
    return prefix, nxt, ci


def _suffix(a: tuple, b: tuple) -> bool:
    s, l = (a, b) if len(a) <= len(b) else (b, a)
    return l[len(l) - len(s):] == s


# ---- the checks ----------------------------------------------------------------------------------

def _check_quantities(infos: list[Info], out: list) -> None:
    buckets: dict[tuple, list] = {}
    seen: set = set()
    for info in infos:
        for tok, val, dec, idx in info.tokens:
            unit = _unit(tok, dec)
            if _trivial(tok, val, dec) or idx in info.cmp_idx:
                continue
            prefix, nxt, ci = _key(info.km, idx, idx + len(tok), unit)
            if ci or len(prefix) < 2 or prefix[-1] in SKIP_LAST | REF_WORDS | GROUP_WORDS:
                continue
            bucket = buckets.setdefault((unit, nxt, prefix[-2:]), [])
            for o_tok, o_val, o_dec, o_prefix, o_loc in bucket:
                if not _suffix(prefix, o_prefix) or _same(val, dec, o_val, o_dec):
                    continue
                short = prefix if len(prefix) <= len(o_prefix) else o_prefix
                tag = (unit, nxt, short, frozenset((tok, o_tok)))
                if tag not in seen:
                    seen.add(tag)
                    out.append(("block", info.loc,
                                f'"{" ".join(short)}" is {tok} here but {o_tok} in {o_loc}'))
                break
            bucket.append((tok, val, dec, prefix, info.loc))


def _check_sample_size(infos: list[Info], out: list) -> None:
    msg = 'sample size must be a whole number rounded up, not "{}"'
    for info in infos:
        dm, quotes = info.dm, []
        for m in APPROX.finditer(dm):
            rest = dm[m.end():]
            toks = list(TOK.finditer(rest))[:6]
            num = next((t for t in toks[:3] if t.group(0)[0].isdigit()), None)
            if num is None or num.group(0).endswith("%"):
                continue
            ok = bool(PRE_N.search(dm[:m.start()]))
            if not ok and toks:
                window = rest[num.end():toks[-1].end()]
                pm = PART.search(window)
                ok = bool(pm) and not any(t.group(0)[0].isdigit() for t in toks
                                          if t.start() >= num.end() and t.start() < num.end() + pm.start())
            if ok:
                quotes.append(dm[m.start():m.end() + num.end()].strip())
        for tok, val, dec, idx in info.tokens:
            if dec == 0 or tok.endswith("%"):
                continue
            before, after = dm[:idx], dm[idx + len(tok):].lstrip()
            if PRE_N_DEC.search(before) or PART.match(after):
                q = tok
                nm = re.search(r"((?:(?<!\w)n|cỡ mẫu|sample size)[^.;|\d]{0,20})$", before, re.I)
                quotes.append((nm.group(1) + tok).strip() if nm else q)
        done = set()
        for q in quotes:
            if q not in done and not any(q in d or d in q for d in done):
                done.add(q)
                out.append(("block", info.loc, msg.format(q)))


def _check_dates(infos: list[Info], out: list) -> None:
    seen_ranges: list = []
    reported: set = set()
    for info in infos:
        for s, e, text in info.ranges:
            for os_, oe, otext, oloc in seen_ranges:
                if (os_ == s) != (oe == e) and (os_ == s or oe == e):
                    tag = frozenset(((s, e), (os_, oe)))
                    if tag not in reported:
                        reported.add(tag)
                        which = "same start, different end" if os_ == s else "same end, different start"
                        out.append(("block", info.loc,
                                    f"date range {text} here but {otext} in {oloc} ({which})"))
                    break
            seen_ranges.append((s, e, text, info.loc))


def _ledger_numbers(by_id: dict, lang: str) -> set:
    vals: set = set()
    for rec in by_id.values():
        strings = []
        for part in ("value", "ci", "p", "n", "count", "full"):
            try:
                strings.append(numfmt.render(rec, part, lang))
            except (KeyError, TypeError, ValueError, IndexError, ArithmeticError):
                pass
        d = numfmt.PRECISION.get(rec.get("kind") or "other", 2)
        for key in ("ci", "iqr"):
            if isinstance(rec.get(key), (list, tuple)):
                strings += [numfmt.fmt(x, d, lang) for x in rec[key] if isinstance(x, (int, float))]
        if isinstance(rec.get("sd"), (int, float)):
            strings.append(numfmt.fmt(rec["sd"], d, lang))
        for s in strings:
            vals.update((v, dec) for _, v, dec in numfmt.parse_tokens(s, "any"))
    return vals


def _matches_rounded(val, dec: int, others: set) -> bool:
    """True when some (value, decimals) in `others`, printed with at least as many decimals, equals `val`
    once rounded (half up) to the abstract's `dec` decimals: 85 matches 85.0 and 85,04."""
    q = Decimal(1).scaleb(-dec)
    for ov, od in others:
        if od > dec and Decimal(ov).quantize(q, rounding=ROUND_HALF_UP) == Decimal(val):
            return True
    return False


def _check_abstract(docs: list[Doc], infos_by_doc: list[list[Info]], by_id: dict, lang: str, out: list) -> None:
    per_doc = [{(v, d) for info in infos for _, v, d, _ in info.tokens} for infos in infos_by_doc]
    ledger = _ledger_numbers(by_id, lang)
    for i, doc in enumerate(docs):
        if not doc.is_abstract:
            continue
        others = set(ledger)
        for j, s in enumerate(per_doc):
            if j != i:
                others |= s
        if not others:
            continue
        reported: set = set()
        for info in infos_by_doc[i]:
            for tok, val, dec, _ in info.tokens:
                if _trivial(tok, val, dec) or (val, dec) in ((Decimal(95), 0), (Decimal("0.05"), 2)):
                    continue
                if (val, dec) in reported:
                    continue
                if (val, dec) in others or _matches_rounded(val, dec, others):
                    continue
                reported.add((val, dec))
                out.append(("warn", info.loc,
                            f'abstract number "{tok}" appears in no other audited file and no ledger value'))


def _split_row(text: str) -> list[str]:
    return text.strip().strip("|").split("|")


def _first_pct(cell: str):
    for tok, val, _ in numfmt.parse_tokens(cell, "any"):
        if tok.endswith("%"):
            return tok, val
    return None


def _check_sums(docs: list[Doc], lang: str, out: list) -> None:
    for doc in docs:
        block: list[Line] = []
        for ln in doc.lines + [Line("", "")]:
            if ln.text.strip().startswith("|"):
                block.append(ln)
                continue
            if block:
                _sum_table(block, lang, out)
            block = []


def _sum_table(block: list[Line], lang: str, out: list) -> None:
    rows = [(ln, _split_row(mask(ln.text))) for ln in block]
    header = None
    if len(rows) > 1 and all(SEP_CELL.match(c) for c in rows[1][1]):
        header = rows[0][1]
        rows = rows[2:]
    rows = [(ln, c) for ln, c in rows if not all(SEP_CELL.match(x) for x in c)]
    total_rows = [(ln, c) for ln, c in rows if c and TOTAL_ROW.match(c[0])]
    data_rows = [(ln, c) for ln, c in rows if (ln, c) not in total_rows and not ln.skip]
    for tln, tcells in total_rows:
        if tln.skip:
            continue
        for j in range(1, len(tcells)):
            tp = _first_pct(tcells[j])
            if tp is None or abs(tp[1] - 100) > Decimal("0.5"):
                continue
            vals, valid = [], True
            for _, cells in data_rows:
                cell = cells[j] if j < len(cells) else ""
                if cell.strip() in ("", "-", "–", "—"):
                    continue
                p = _first_pct(cell)
                if p is None:
                    valid = False
                    break
                vals.append(p[1])
            if not valid or len(vals) < 2:
                continue
            total = sum(vals, Decimal(0))
            if abs(total - tp[1]) > Decimal("0.5"):
                name = (header[j].strip(" *") if header and j < len(header) else f"{j + 1}")
                out.append(("warn", tln.loc,
                            f'percentages in column "{name}" sum to {numfmt.fmt(float(total), 1, lang)}% '
                            f'but the total row says {tp[0]}'))


def _check_terms(docs: list[Doc], terms: dict[str, list[str]], out: list) -> None:
    pats = []
    for preferred, variants in terms.items():
        for v in variants:
            if not v or v == preferred:
                continue
            flags = 0 if v.lower() == preferred.lower() else re.I
            pats.append((v, preferred, re.compile(r"(?<!\w)" + re.escape(v) + r"(?!\w)", flags)))
    for doc in docs:
        for ln in doc.lines:
            if ln.skip:
                continue
            for v, preferred, pat in pats:
                for _ in pat.finditer(ln.text):
                    out.append(("warn", ln.loc, f'term "{v}" should be "{preferred}"'))


# ---- API and CLI -----------------------------------------------------------------------------------

def audit(project: Path, files: list[Path] | None = None, lang: str | None = None) -> list[tuple[str, str, str]]:
    project = Path(project)
    lang = lang or projectcfg.output_lang(project)
    by_id = _load_ledger(project)
    findings: list[tuple[str, str, str]] = []
    if files is None:
        paths = _discover(project)
    else:
        paths = []
        for f in files:
            p = Path(f)
            if not p.is_file() and not p.is_absolute() and (project / p).is_file():
                p = project / p
            if not p.is_file():
                raise FileNotFoundError(f"no such file: {f}")
            paths.append(p)
    docs = [_load_doc(p, project, by_id, lang, findings) for p in paths]
    infos_by_doc = [_analyse(d, lang) for d in docs]
    infos = [i for infos_ in infos_by_doc for i in infos_]
    ref_infos: list = []
    if files is None and (project / SAMPLE_SIZE).is_file():
        ref_infos = _analyse(_load_doc(project / SAMPLE_SIZE, project, by_id, lang, findings), lang)
    _check_quantities(infos, findings)  # the cross-document pass is unchanged: its blocks stay blocks
    if ref_infos:  # separate pass: only what disagrees with sample-size.md, always a warn
        quantities: list = []
        _check_quantities(ref_infos + infos, quantities)  # reference first: a finding sits on the later, typed copy
        for _sev, loc, msg in quantities:
            if str(loc).startswith(SAMPLE_SIZE) or SAMPLE_SIZE not in msg:
                continue
            findings.append(("warn", loc, msg))
    _check_sample_size(infos, findings)
    _check_dates(infos, findings)
    _check_abstract(docs, infos_by_doc, by_id, lang, findings)
    _check_sums(docs, lang, findings)
    _check_terms(docs, _read_terms(project), findings)
    return findings


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("files", nargs="*")
    ap.add_argument("--lang", choices=["en", "vi"])
    a = ap.parse_args(argv)
    project = Path(a.project)
    if not project.is_dir():
        print(f"consistency_audit: project folder not found: {project}", file=sys.stderr)
        return 2
    try:
        res = audit(project, [Path(f) for f in a.files] or None, a.lang)
    except (OSError, ValueError) as e:
        print(f"consistency_audit: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    for sev, loc, msg in res:
        print(f"E-CONS {sev} {loc}: {msg}")
    b = sum(1 for r in res if r[0] == "block")
    print(f"consistency_audit: {b} block, {len(res) - b} warn")
    return 1 if b else 0


if __name__ == "__main__":
    sys.exit(main())
