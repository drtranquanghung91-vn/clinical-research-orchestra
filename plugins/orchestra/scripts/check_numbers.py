#!/usr/bin/env python3
"""E-NUM: every literal number in a results document must come from the results ledger.

  python check_numbers.py <project> <file> [<file> ...] [--lang en|vi]

Numbers written as {{R-…}} placeholders are not checked here (render_results.py checks them). A number
computed from ledger values carries an inline comment right after it: 0.83 <!-- derived: R-A1-001.hi - 1.96, note -->.
EXPR is the text up to the first "," or ";". Result ids may carry .value (default), .n, .count, .p, .lo, .hi.
No id in EXPR -> E-NUM block. A pure formula (ids, numbers, + - * / and parentheses) is evaluated and must equal the
number at its printed decimals (half up), else block. Ids in a non-pure EXPR -> E-NUM warn (not evaluated). Unknown id -> block.
A record of kind "p" (or any record with p < 0.001) lets "< 0.001" pass.
A number that is not a result (an age range in eligibility criteria, a ward code) carries a marker
right after it, same as derived: 18–65 <!-- not-a-result: eligibility --> (both numbers of a range are skipped).
Headings, citation groups, table/figure/section references, dates, "95%" in CI labels, integers 0–10 and
years in context (after năm, in, since, from, until, during, between, before, after, từ, đến, trước, sau, giai đoạn,
thời kỳ, period, a month, `tháng N/`, `N/`, `et al.,`, `và cộng sự`, inside a parenthesised author-year citation, or a
parenthesised year range; not before patients/participants/people/cases/subjects/người/bệnh nhân/ca/trường hợp) are not
checked; any other 1900-2100 integer is (defaults in references/judgement-defaults.md).
Trend words (tăng dần, giảm dần, xu hướng, peak/peaked, trend, increasing) in a sentence need two `{{R-…}}` values or one
trend-test result (label with trend, Cochran-Armitage, Jonckheere, Mann-Kendall, Cuzick, p for trend, joinpoint), unless
negated: `E-NUM warn` (run it on the text with placeholders).
Thousands separators are not parsed (this project never writes them): an author-typed "1,070" (en) or
"1.070" (vi) is expected to produce an E-NUM finding; the fix is a placeholder.
Exit codes: 0 = clean (warnings allowed); 1 = E-NUM block findings (listed); 2 = usage or I/O error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crolib import derived, numfmt, projectcfg  # noqa: E402

PLACEHOLDER = re.compile(r"\{\{R-A\d+-\d{3}(?:\.\w+)?\}\}")
DERIVED = re.compile(r"-?\d+(?:[.,]\d+)?%?\s*<!--\s*derived:.*?-->")
COMMENT = re.compile(r"<!--.*?-->")
CITE = re.compile(r"\[[^\[\]]*@[^\[\]]*\]|\[\d+(?:\s*[–,-]\s*\d+)*\]")
REFS = re.compile(r"(?:Bảng|Table|Hình|Figure|Biểu đồ|Sơ đồ|mục|Mục|section|Section|Chương|Chapter)\s+\d+(?:\.\d+)*")
DATES = re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b")
NOTRES = re.compile(r"-?\d+(?:[.,]\d+)?%?(?:\s*[–-]\s*-?\d+(?:[.,]\d+)?%?)?\s*<!--\s*not-a-result:.*?-->")
CI95 = re.compile(r"95\s*%\s*(?=CI\b|KTC|CrI\b|confidence interval|khoảng tin cậy)"
                  r"|(?:KTC|CI|CrI|khoảng tin cậy)\s*95\s*%", re.IGNORECASE)
THRESH = re.compile(r"(?:\bp|α|\balpha)\s*[<≤=>≥]\s*0[.,](?:05|01|1)(?!\d)", re.IGNORECASE)
NAMES = re.compile(r"(?<=[^\W\d_])-\d+(?!\d|[.,]\d)")  # COVID-19 yes; OR-1.84 and baseline-3.7 stay checked
PSMALL = re.compile(r"[<≤]\s*0[.,]001")
YEAR = r"(?:19\d{2}|20\d{2}|2100)"
MONTHS = (r"(?:January|February|March|April|May|June|July|August|September|October|November|December|"
          r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)")
NOT_A_YEAR_AFTER = r"(?!\s+(?:patients?|participants?|people|persons|cases|subjects|người|bệnh nhân|ca\b|trường hợp))"
YEAR_CTX = re.compile(
    rf"(?:\b(?:năm|in|since|from|until|during|between|before|after|từ|đến|trước|sau|giai đoạn|thời kỳ|period)\s+(?:năm\s+)?"
    rf"|\b{MONTHS}\.?\s+(?:\d{{1,2}},?\s+)?|\btháng\s*\d{{1,2}}\s*(?:/\s*|\s+năm\s+)|\b\d{{1,2}}/"
    rf"|\bet al\.?,?\s+|\bvà (?:cộng sự|cs\.?),?\s+)"
    rf"{YEAR}[a-z]?(?:\s*(?:[–-]|to|and|đến|và)\s*{YEAR})?(?!\d){NOT_A_YEAR_AFTER}", re.IGNORECASE)
CITE_YEAR = re.compile(rf"\([^()]*[A-Za-zÀ-ỹĐđ]{{2,}}[^()]*?,?\s+{YEAR}[a-z]?\s*\)|\(\s*{YEAR}\s*[–-]\s*{YEAR}\s*\)")
TREND = re.compile(r"(?i)\btăng dần\b|\bgiảm dần\b|\bxu hướng\b|\bpeak(?:s|ed|ing)?\b|\btrends?\b|\bincreasing(?:ly)?\b")
TREND_TEST = re.compile(r"(?i)trend|xu hướng|cochran|armitage|jonckheere|mann[- ]kendall|cuzick|joinpoint")
NEGATION = re.compile(r"(?i)\b(?:no|not|without|neither|không|chưa)\b")
SENTENCE = re.compile(r"(?<=[.!?;])\s+")
PLACEHOLDER_ID = re.compile(r"\{\{(R-A\d+-\d{3})")


def trend_findings(text: str, results: list[dict]) -> list[tuple[int, str, str]]:
    """Warn per sentence with trend wording that cites fewer than two ledger values and no trend-test result."""
    trend_ids = {r.get("id") for r in results if isinstance(r, dict)
                 and TREND_TEST.search(f"{r.get('label', '')} {r.get('test', '')}")}
    out = []
    for n, line in enumerate(text.split("\n"), start=1):
        if line.lstrip().startswith("#"):
            continue
        for sent in SENTENCE.split(COMMENT.sub(" ", line)):
            m = TREND.search(sent)
            if not m or NEGATION.search(sent):
                continue
            ids = set(PLACEHOLDER_ID.findall(sent))
            if len(ids) >= 2 or ids & trend_ids:
                continue
            out.append((n, "warn", f'trend wording "{m.group(0)}" without two ledger values or a trend-test result '
                                   "in the sentence: cite them as {{R-…}} or reword (no trend test, no trend claim)"))
    return out


DERIVED_FULL = re.compile(r"(-?\d+(?:[.,]\d+)?)(%?)\s*<!--\s*derived:(.*?)-->", re.DOTALL)
DERIVED_OPEN = re.compile(r"<!--\s*derived:")
PARTS, RID, ID_PART, PURE = derived.PARTS, derived.RID, derived.ID_PART, derived.PURE
_id_value, _eval = derived.value_of, derived.eval_pure


def check_derived(text: str, ledger_results: list[dict]) -> list[tuple[int, str, str]]:
    """Judge each `<number> <!-- derived: EXPR[, note] -->`. Returns (line, 'block'|'warn', message).

    No result id in EXPR -> block. Pure formula (ids, numbers, + - * / ( )) -> evaluated and compared with the
    number at its printed decimals (half up); mismatch -> block. Ids in a non-pure EXPR -> warn. Unknown id -> block.
    """
    by_id = {r["id"]: r for r in ledger_results if isinstance(r, dict) and isinstance(r.get("id"), str)}
    out = []
    for n, line in enumerate(text.split("\n"), start=1):
        line = line.replace("−", "-")
        owned = {m.start(3) for m in DERIVED_FULL.finditer(line)}
        for o in DERIVED_OPEN.finditer(line):
            if o.end() not in owned:
                out.append((n, "block", "derived comment must directly follow its number on the same line"))
        for m in DERIVED_FULL.finditer(line):
            num, tok = m.group(1).replace(",", "."), m.group(1) + m.group(2)
            expr = re.split(r"[,;]", m.group(3), maxsplit=1)[0].strip()
            refs = RID.findall(expr)
            bad_parts = [p for p in ID_PART.findall(expr) if p not in PARTS]
            if bad_parts:
                out.append((n, "block", f"{tok}: derived comment uses part .{bad_parts[0]} "
                                        f"(allowed: {', '.join('.' + p for p in PARTS)})"))
                continue
            if not refs:
                out.append((n, "block", f"{tok}: derived comment names no ledger result"))
                continue
            try:
                vals = {r: _id_value(by_id, r) for r in set(refs)}
            except KeyError as e:
                out.append((n, "block", f"{tok}: derived comment: {e.args[0]}"))
                continue
            if not PURE.fullmatch(RID.sub(" ", expr)):
                out.append((n, "warn", f"{tok}: derived formula not evaluated"))
                continue
            dec = len(num.split(".")[1]) if "." in num else 0
            try:
                got = _eval(RID.sub(lambda mm: "(" + str(vals[mm.group(0)]) + ")", expr)).quantize(
                    Decimal(1).scaleb(-dec), rounding=ROUND_HALF_UP)
            except (SyntaxError, ValueError, ArithmeticError):
                out.append((n, "block", f"{tok}: derived formula '{expr}' cannot be evaluated"))
                continue
            if got != Decimal(num):
                out.append((n, "block", f"{tok} does not match derived formula '{expr}' = {got}"))
    return out


def find_unmatched(text: str, ledger_results: list[dict], lang: str) -> list[tuple[int, str]]:
    xs = [x for r in ledger_results if isinstance(r, dict) for x in numfmt.candidates(r)]

    def small_p(r):
        return isinstance(r, dict) and any(
            isinstance(r.get(k), (int, float)) and not isinstance(r.get(k), bool) and r[k] < 0.001
            for k in (("p", "value") if r.get("kind") == "p" else ("p",)))
    has_small_p = any(small_p(r) for r in ledger_results)
    found = []
    for n, line in enumerate(text.split("\n"), start=1):
        if line.lstrip().startswith("#"):
            continue
        s = PLACEHOLDER.sub(" ", line.replace("−", "-"))
        s = NOTRES.sub(" ", s)
        s = DERIVED.sub(" ", s)
        s = COMMENT.sub(" ", s)
        s = CITE.sub(" ", s)
        s = REFS.sub(" ", s)
        s = DATES.sub(" ", s)
        s = YEAR_CTX.sub(" ", s)
        s = CITE_YEAR.sub(" ", s)
        s = CI95.sub(" ", s)
        s = THRESH.sub(" ", s)
        s = NAMES.sub(" ", s)
        if has_small_p:
            s = PSMALL.sub(" ", s)
        for tok, value, decimals in numfmt.parse_tokens(s, lang):
            if decimals == 0 and not tok.endswith("%") and 0 <= value <= 10:
                continue
            if not numfmt.matches(value, decimals, xs):
                found.append((n, tok))
    return found


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--lang", choices=["en", "vi"])
    a = ap.parse_args(argv)
    project = Path(a.project)
    try:
        with open(project / "ledgers" / "results-ledger.json", encoding="utf-8-sig") as fh:
            ledger = json.load(fh)
        texts = {}
        for f in a.files:
            with open(f, encoding="utf-8", newline="") as fh:
                texts[f] = fh.read()
        lang = a.lang or projectcfg.output_lang(project)
    except (OSError, ValueError) as e:
        print(f"check_numbers: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    results = ledger.get("results") if isinstance(ledger, dict) else None
    if not isinstance(results, list) or not all(isinstance(r, dict) for r in results):
        print("check_numbers: results ledger must be an object with a 'results' list of objects",
              file=sys.stderr)
        return 2
    total = warns = 0
    for f, text in texts.items():
        for n, tok in find_unmatched(text, results, lang):
            print(f"E-NUM block {f}:{n}: {tok} is not in the results ledger")
            total += 1
        for n, sev, msg in check_derived(text, results):
            print(f"E-NUM {sev} {f}:{n}: {msg}")
            if sev == "block":
                total += 1
            else:
                warns += 1
        for n, sev, msg in trend_findings(text, results):
            print(f"E-NUM {sev} {f}:{n}: {msg}")
            warns += 1
    print(f"check_numbers: {total} findings" + (f", {warns} warnings" if warns else ""))
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
