#!/usr/bin/env python3
"""P01-P30: count AI-sounding patterns in academic prose (Vietnamese and English); never count hedges or passive voice.

  python lint_prose.py FILE... [--lang vi|en|auto] [--json]
  python lint_prose.py --count-words FILE
  python lint_prose.py --slides FILE.pptx|FILE.html [--json]
  python lint_prose.py --profile consent FILE...  plain-language warns CF01-CF03 for consent forms (exit 0)

Markdown/text: paragraphs are blank-line separated. Headings (#), table rows (|), fenced code, HTML comments
and {{...}} placeholders are skipped (a placeholder counts as one word). Output lines follow
  <CODE> <block|warn> <file>:<line>: <message>
A paragraph above 3 hits per 100 words gets a warn line per hit; a document above 2 hits per 100 words gets
"P00 block <file>:1: pattern density <d>/100 words". --slides applies S17 (topic title), S20 (explaining the
obvious) and S21 (hype without a hedge in a medical claim); speaker notes are never read.
The catalog is references/writing/prose-patterns.md. Exit codes: 0 = no block line; 1 = a block line;
2 = usage or I/O error (also python-pptx missing for a .pptx).
"""
from __future__ import annotations

import argparse
import html.parser
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

PARA_WARN = 3.0   # hits per 100 words, paragraph (references/judgement-defaults.md)
DOC_BLOCK = 2.0   # hits per 100 words, document

COMMENT = re.compile(r"<!--.*?-->", re.S)
PLACEHOLDER = re.compile(r"\{\{[^{}]*\}\}")
FENCE = re.compile(r"^\s*(```|~~~)")
CITE_GROUP = re.compile(r"\[@[^\]]*\]")
LEAD_LABEL = re.compile(r"^\s*\*\*[^*\n]{1,40}?(?::\*\*|\*\*:)\s*")
HAS_ALNUM = re.compile(r"[^\W_]", re.U)
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[\"“(\[]?[A-ZÀ-ỸĐ])")
CITED = re.compile(r"\[@|\[\d|\(\s*[A-Z][^)]{0,60}\d{4}|\{\{|\^\d")
SO = r"(?:(?<=[.!?]\s)|(?<=\n)|^)"   # sentence opener anchor (MULTILINE)


# --- text preparation -------------------------------------------------------------------------------------

def _blank_comment(m: re.Match) -> str:
    return "\n" * m.group(0).count("\n")


def prepare(text: str) -> list[dict]:
    """Return paragraphs: {line, text, section_end}. Skipped blocks become separators (line numbers kept)."""
    text = unicodedata.normalize("NFC", text).replace("\r\n", "\n").replace("\r", "\n")
    text = COMMENT.sub(_blank_comment, text)
    text = PLACEHOLDER.sub("X", text)
    paras: list[dict] = []
    cur: list[str] = []
    start = 0
    in_fence = False

    def flush(section_end: bool = False):
        nonlocal cur
        if cur:
            paras.append({"line": start, "text": "\n".join(cur), "section_end": section_end})
            cur = []
        elif section_end and paras:
            paras[-1]["section_end"] = True

    for i, line in enumerate(text.split("\n"), 1):
        if FENCE.match(line):
            flush()
            in_fence = not in_fence
            continue
        s = line.strip()
        if in_fence:
            continue
        if not s:
            flush()
        elif s.startswith("#") or s.startswith("|") or re.fullmatch(r"[-*_=\s]{3,}", s):
            flush(section_end=s.startswith("#"))
        else:
            if not cur:
                start = i
            cur.append(line)
    flush(section_end=True)
    return paras


def _words(text: str) -> int:
    return sum(1 for t in text.split() if HAS_ALNUM.search(t))


def word_count(text: str) -> int:
    """Words in prose (symbol-only tokens such as = or % are not words, so "n = 5" is 2; this follows conference
    practice of counting words, not symbols): headings, tables, code, comments, citation groups and a leading **Label:** are excluded;
    a {{placeholder}} counts as one word."""
    n = 0
    for p in prepare(text):
        t = CITE_GROUP.sub("", p["text"])
        t = LEAD_LABEL.sub("", t, count=1)
        n += _words(t.replace("**", " "))
    return n


# --- pattern catalog (mirrors references/writing/prose-patterns.md) ----------------------------------------

STAT_NEAR = re.compile(r"standard error|variance|regress|estimat|sandwich|sensitivity|bootstrap|\bcox\b|model|"
                       r"inference|outlier|missing|\bse\b|sai số|phương sai|hồi quy|ước lượng|độ nhạy|mô hình", re.I)
ADJ_STOCK = {
    "hiệu quả", "an toàn", "bền vững", "toàn diện", "nhanh chóng", "chính xác", "tiện lợi", "linh hoạt",
    "minh bạch", "đáng tin cậy", "sáng tạo", "efficient", "scalable", "robust", "reliable", "accurate", "effective",
    "safe", "sustainable", "comprehensive", "innovative", "transparent", "flexible", "scalable", "seamless",
    "fast", "cost-effective"}


def _no_stat_context(text: str, m: re.Match) -> bool:
    return not STAT_NEAR.search(text[max(0, m.start() - 45): m.end() + 45])


def _landscape_ok(text: str, m: re.Match) -> bool:
    return not re.match(r"\s+(?:orientation|mode|page|layout)", text[m.end(): m.end() + 14], re.I)


def _sentence_around(text: str, m: re.Match) -> str:
    a = max(text.rfind(".", 0, m.start()), text.rfind("\n\n", 0, m.start()))
    b = text.find(".", m.end())
    return text[a + 1: b if b >= 0 else len(text)]


def _uncited(text: str, m: re.Match) -> bool:
    return not CITED.search(_sentence_around(text, m))


F = re.I | re.M
# (code, lang, regex, filter or None)
PATTERNS: list[tuple[str, str, re.Pattern, object]] = [
    ("P01", "vi", re.compile(r"\bkhông\s+(?:chỉ|những)\b[^.!?]{0,140}?\bmà\s+còn\b", F), None),
    ("P01", "en", re.compile(r"\bnot\s+only\b[^.!?]{0,140}?\bbut\s+also\b", F), None),
    ("P02", "vi", re.compile(r"\b(?:đóng|giữ)\s+vai\s+trò\s+(?:quan\s+trọng|then\s+chốt|thiết\s+yếu|quyết\s+định|trọng\s+yếu)", F), None),
    ("P02", "en", re.compile(r"\bplays?\s+(?:a|an)\s+(?:crucial|pivotal|vital|key|critical|significant|important|central)\s+role", F), None),
    ("P03", "vi", re.compile(SO + r"(?:Trong\s+bối\s+cảnh|Trong\s+thế\s+giới\s+ngày\s+nay|Trong\s+kỷ\s+nguyên)\b", F), None),
    ("P03", "en", re.compile(SO + r"(?:In\s+the\s+context\s+of|In\s+today'?s|In\s+an\s+era\s+of|In\s+the\s+(?:ever-)?(?:changing|evolving)\s+landscape)\b", F), None),
    ("P05", "vi", re.compile(r"\bgóp\s+phần\b", F), None),
    ("P05", "en", re.compile(r"\bcontribut(?:es|ing)\s+to\s+(?:a\s+|the\s+)?(?:broader|growing|overall|better|improved|greater|deeper|wider)", F), None),
    ("P06", "vi", re.compile(SO + r"(?:Tóm\s+lại|Tổng\s+kết\s+lại|Tựu\s+trung)\s*,", F), None),
    ("P06", "en", re.compile(SO + r"(?:In\s+conclusion|In\s+summary|To\s+sum\s+up|To\s+summari[sz]e|Overall|Ultimately)\s*,", F), None),
    ("P10", "vi", re.compile(SO + r"(?:Đáng\s+chú\s+ý|Điều\s+đáng\s+chú\s+ý\s+là)\b", F), None),
    ("P10", "en", re.compile(SO + r"(?:Notably|Importantly|Interestingly|Remarkably|Crucially)\s*,", F), None),
    ("P11", "vi", re.compile(r"\bhơn\s+bao\s+giờ\s+hết\b", F), None),
    ("P11", "en", re.compile(r"\bmore\s+than\s+ever\b", F), None),
    ("P12", "en", re.compile(r"\b(?:delv(?:e|es|ed|ing)|tapestry|realm|underscor(?:e|es|ed|ing)|pivotal|seamless(?:ly)?|holistic|multifaceted|myriad|intricate)\b", F), None),
    ("P12", "en", re.compile(r"\blandscape\b", F), _landscape_ok),
    ("P12", "en", re.compile(r"\brobust\b", F), _no_stat_context),
    ("P12", "vi", re.compile(r"\b(?:bức\s+tranh\s+toàn\s+cảnh|tấm\s+thảm|đa\s+diện|đa\s+chiều|kỷ\s+nguyên)\b", F), None),
    ("P13", "en", re.compile(r"\bit\s+(?:is|'s)\s+(?:worth\s+noting|important\s+to\s+note)\b", F), None),
    ("P13", "vi", re.compile(r"\b(?:đáng\s+lưu\s+ý\s+là|cần\s+lưu\s+ý\s+rằng|cần\s+nhấn\s+mạnh\s+rằng)\b", F), None),
    ("P16", "en", re.compile(r"\b(?:here'?s\s+the\s+(?:thing|catch|truth)|let'?s\s+be\s+(?:honest|clear)|the\s+(?:truth|reality)\s+is\s+that|the\s+hard\s+part\s+is)\b", F), None),
    ("P16", "vi", re.compile(r"\b(?:sự\s+thật\s+là|thành\s+thật\s+mà\s+nói|nói\s+thẳng|điều\s+khó\s+là)\b", F), None),
    ("P17", "en", re.compile(r"\b(?:at\s+its\s+core|at\s+the\s+heart\s+of|the\s+heart\s+of\s+the\s+matter|cornerstone|bedrock|backbone\s+of)\b", F), None),
    ("P17", "vi", re.compile(r"\b(?:cốt\s+lõi\s+của\s+vấn\s+đề|trái\s+tim\s+của|xương\s+sống\s+của|nền\s+tảng\s+vững\s+chắc)\b", F), None),
    ("P18", "en", re.compile(r"\b(?:it'?s|this\s+is|that'?s)\s+not\s+(?:just\s+|merely\s+|simply\s+)?[^.;\n—]{1,50}[,;—]\s*(?:it'?s|but|rather)\b", F), None),
    ("P18", "vi", re.compile(r"\bkhông\s+phải\s+(?:chỉ\s+)?là\s+[^.;\n]{1,50},\s*mà\s+(?:là\s+)?", F), None),
    ("P19", "auto", re.compile(r"\b[A-Za-zÀ-ỹ]{3,12}\.\s+[A-ZÀ-Ỹ][a-zà-ỹ]{2,11}\.\s+[A-ZÀ-Ỹ][a-zà-ỹ]{2,11}\.(?=\s|$)"), None),
    ("P21", "en", re.compile(r"\b(?:incredibly|truly|profoundly|deeply|immensely|tremendously)\s+\w+|\bextremely\s+(?!preterm|low|rare|obese|premature|high\b|elevated)\w+", F), None),
    ("P21", "vi", re.compile(r"\b(?:vô\s+cùng|cực\s+kỳ|hết\s+sức)\s+(?:quan\s+trọng|cần\s+thiết|ý\s+nghĩa|to\s+lớn)", F), None),
    ("P22", "en", re.compile(r"\b(?:a\s+testament\s+to|marks?\s+a\s+(?:pivotal|turning|watershed)\s+(?:moment|point)|setting\s+the\s+stage\s+for|represents?\s+a\s+paradigm\s+shift|paradigm\s+shift)\b", F), None),
    ("P22", "vi", re.compile(r"\b(?:đánh\s+dấu\s+(?:một\s+)?(?:bước\s+ngoặt|cột\s+mốc)|mở\s+ra\s+kỷ\s+nguyên\s+mới|là\s+minh\s+chứng\s+cho)\b", F), None),
    ("P23", "en", re.compile(r"\b(?:groundbreaking|cutting-edge|state-of-the-art|game-chang(?:er|ing)|revolutionary|transformative|breathtaking)\b", F), None),
    ("P23", "vi", re.compile(r"\b(?:mang\s+tính\s+cách\s+mạng|tiên\s+tiến\s+hàng\s+đầu|đột\s+phá\s+vượt\s+bậc|đột\s+phá)\b", F), None),
    ("P24", "en", re.compile(r",\s+(?:highlighting|underscoring|emphasi[sz]ing|showcasing|reflecting|cementing|fostering|demonstrating)\s+(?:the\s+|its\s+|their\s+)?(?:importance|significance|need|role|potential|broader|ongoing|growing|critical)", F), None),
    ("P24", "vi", re.compile(r",\s+qua\s+đó\s+(?:góp\s+phần|khẳng\s+định|nhấn\s+mạnh|làm\s+nổi\s+bật)", F), None),
    ("P25", "en", re.compile(r"\b(?:experts\s+(?:say|believe|argue|agree)|(?:many|some)\s+(?:researchers|experts|critics)\s+(?:say|believe|argue)|studies\s+(?:show|suggest|have\s+shown)|research\s+shows|observers\s+have\s+noted)\b", F), _uncited),
    ("P25", "vi", re.compile(r"\b(?:các\s+chuyên\s+gia\s+(?:cho\s+rằng|nhận\s+định)|nhiều\s+(?:chuyên\s+gia|nghiên\s+cứu)\s+(?:cho\s+(?:thấy|rằng)|nhận\s+định)|một\s+số\s+nghiên\s+cứu\s+cho\s+thấy)\b", F), _uncited),
    ("P26", "en", re.compile(r"\b(?:serves|stands)\s+as\s+(?:a|an)\s+(?:testament|reminder|beacon|cornerstone|catalyst|foundation|bridge)\b", F), None),
    ("P26", "vi", re.compile(r"\blà\s+một\s+(?:minh\s+chứng|lời\s+nhắc\s+nhở|cầu\s+nối|chất\s+xúc\s+tác)\b", F), None),
    ("P27", "en", re.compile(r"\b(?:i\s+hope\s+this\s+helps|let\s+me\s+know\s+if|great\s+question|as\s+an\s+ai\b|certainly!|(?:here\s+is|here'?s)\s+(?:a|an|the)\s+(?:overview|summary|breakdown))", F), None),
    ("P27", "vi", re.compile(r"\b(?:hy\s+vọng\s+điều\s+này\s+(?:giúp|hữu\s+ích)|câu\s+hỏi\s+rất\s+hay|dưới\s+đây\s+là\s+(?:một\s+)?(?:tổng\s+quan|bản\s+tóm\s+tắt|phần\s+tóm\s+tắt))", F), None),
    ("P28", "en", re.compile(r"\b(?:due\s+to\s+the\s+fact\s+that|at\s+this\s+point\s+in\s+time|in\s+the\s+event\s+that|has\s+the\s+ability\s+to|for\s+the\s+purpose\s+of)\b", F), None),
    ("P28", "vi", re.compile(r"\b(?:nhằm\s+mục\s+đích|tại\s+thời\s+điểm\s+hiện\s+tại|do\s+thực\s+tế\s+là|có\s+khả\s+năng\s+để)\b", F), None),
    ("P29", "auto", re.compile("[\U0001F300-\U0001FAFF\U00002700-\U000027BF\U00002B50\U00002705\U0000274C]"), None),
    ("P30", "en", re.compile(r"\b(?:the\s+future\s+(?:looks|is)\s+bright|exciting\s+(?:times|developments)\s+(?:lie\s+)?ahead|a\s+promising\s+future|journey\s+(?:toward|towards))\b", F), None),
    ("P30", "vi", re.compile(r"\b(?:tương\s+lai\s+(?:đầy\s+hứa\s+hẹn|tươi\s+sáng)|hành\s+trình\s+(?:hướng\s+tới|đến\s+với)|mở\s+ra\s+(?:nhiều\s+)?(?:cơ\s+hội|triển\s+vọng)\s+(?:mới|to\s+lớn))\b", F), None),
]

P04_RX = re.compile(r"\b(?:ngày\s+càng|increasingly|ever-(?:increasing|growing))\b", F)
P07_RX = re.compile(r"(?<=\S)\s?[—–]\s?(?=\S)|(?<=\S)\s--?\s(?=\S)")
RANGE_DASH = re.compile(r"\d\s?[–—-]\s?\d")
P09_RX = re.compile(r"([^,.;\n]{2,25}),\s+([^,.;\n]{2,25}),?\s+(?:và|and|or|hoặc)\s+([^,.;\n]{2,25})", re.I)
P14_START = re.compile(r"^(?:why|what|how|is\s+it|could|can|have\s+you|ever|imagine|liệu|làm\s+thế\s+nào|tại\s+sao|điều\s+gì|vậy|phải\s+chăng)\b", re.I)
P15_RX = re.compile(r"\*\*[^*\n]{2,40}?(?::\*\*|\*\*:)")
STANDARD_LABELS = {
    "background", "methods", "method", "results", "result", "conclusion", "conclusions", "objective", "objectives",
    "aim", "aims", "purpose", "design", "setting", "participants", "interventions", "limitations", "keywords",
    "mục tiêu", "bối cảnh", "đặt vấn đề", "đối tượng", "phương pháp", "đối tượng và phương pháp", "kết quả",
    "kết luận", "hạn chế", "kiến nghị", "từ khóa", "thiết kế", "địa điểm"}
P08_CUE = re.compile(r"^(?:như\s+vậy|vì\s+vậy|do\s+đó|nói\s+cách\s+khác|điều\s+này\s+cho\s+thấy|thus|therefore|"
                     r"in\s+short|ultimately|simply\s+put|in\s+other\s+words|this\s+(?:shows|underscores|highlights))\b", re.I)
P20_SKIP = {"nhóm", "group", "bệnh", "patients", "participants", "the", "this", "these", "a", "an", "in", "of", "we",
            "chúng", "tôi", "it", "các", "những", "mỗi", "each", "all", "tất", "there", "trong", "at"}


def _line_of(par: dict, text: str, pos: int) -> int:
    return par["line"] + text.count("\n", 0, pos)


def _para_hits(par: dict, prev: dict | None, lang: str) -> list[tuple[int, str, str]]:
    text = par["text"]
    hits: list[tuple[int, str, str]] = []
    use = {"vi": ("vi",), "en": ("en",), "auto": ("vi", "en")}[lang]

    for code, pl, rx, flt in PATTERNS:
        if pl != "auto" and pl not in use:
            continue
        for m in rx.finditer(text):
            if flt is not None and not flt(text, m):
                continue
            hits.append((_line_of(par, text, m.start()), code, " ".join(m.group(0).split())))

    # P04 stacking: two or more in one paragraph
    ms = list(P04_RX.finditer(text))
    if len(ms) >= 2:
        hits += [(_line_of(par, text, m.start()), "P04", m.group(0)) for m in ms]

    # P07 dashes: more than 2 per paragraph (numeric ranges are fine)
    dashes = [m for m in P07_RX.finditer(text) if not RANGE_DASH.search(text[max(0, m.start() - 1): m.end() + 1])]
    if len(dashes) > 2:
        hits.append((_line_of(par, text, dashes[0].start()), "P07", f"{len(dashes)} dashes"))

    # P08 one-sentence closer that restates (last paragraph of a section, after a developed paragraph)
    sents = [s for s in SENT_SPLIT.split(" ".join(text.split())) if s.strip()]
    if (len(sents) == 1 and par["section_end"] and prev is not None and _words(prev["text"]) >= 40
            and _words(text) <= 35 and P08_CUE.match(text.strip())):
        hits.append((par["line"], "P08", sents[0][:60]))

    # P09 forced triads of stock adjectives
    for m in P09_RX.finditer(text):
        items = [g.strip().lower() for g in m.groups()]
        if sum(1 for it in items if it in ADJ_STOCK) >= 2:
            hits.append((_line_of(par, text, m.start()), "P09", " ".join(m.group(0).split())))

    # P14 rhetorical-question opener
    first = (SENT_SPLIT.split(" ".join(text.split()), 1) or [""])[0].strip()
    if first.endswith("?") and P14_START.match(first):
        hits.append((par["line"], "P14", first[:70]))

    # P15 bold labels inside prose (a standard abstract label at the start of a paragraph is a heading)
    for m in P15_RX.finditer(text):
        label = re.sub(r"[*:]", "", m.group(0)).strip().lower()
        at_start = text[: m.start()].strip() == ""
        if at_start and label in STANDARD_LABELS:
            continue
        hits.append((_line_of(par, text, m.start()), "P15", m.group(0)))

    # P20 same first word on three consecutive sentences
    firsts = []
    pos = 0
    flat = " ".join(text.split())
    for s in SENT_SPLIT.split(flat):
        w = re.match(r"[^\W\d_]+", s.strip(), re.U)
        firsts.append(w.group(0).lower() if w else "")
    run = 1
    for i in range(1, len(firsts)):
        run = run + 1 if firsts[i] and firsts[i] == firsts[i - 1] else 1
        if run >= 3 and firsts[i] not in P20_SKIP and len(firsts[i]) >= 3:
            hits.append((par["line"], "P20", f"3 sentences open with \"{firsts[i]}\""))
    _ = pos
    return hits


def _analyse(text: str, lang: str) -> tuple[list[dict], list[tuple[int, str, str, dict]]]:
    paras = prepare(text)
    out = []
    prev = None
    for par in paras:
        for ln, code, m in _para_hits(par, prev, lang):
            out.append((ln, code, m, par))
        prev = par
    out.sort(key=lambda h: (h[0], h[1]))
    return paras, out


def find_hits(text: str, lang: str = "auto") -> list[tuple[int, str, str]]:
    """(line, code, matched text) for every pattern hit; skipped blocks never match."""
    if lang not in ("vi", "en", "auto"):
        raise ValueError("lang must be vi, en or auto")
    _, hits = _analyse(text, lang)
    return [(ln, c, m) for ln, c, m, _ in hits]


# --- prose files ------------------------------------------------------------------------------------------

def _fmt(d: float) -> str:
    return f"{round(d, 1):g}"


def lint_file(path: str, lang: str) -> dict:
    text = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    paras, hits = _analyse(text, lang)
    total_words = sum(_words(p["text"]) for p in paras)
    findings: list[dict] = []
    for ln, code, m, par in hits:
        w = _words(par["text"])
        n = sum(1 for h in hits if h[3] is par)
        dens = n * 100.0 / w if w else 0.0
        if dens > PARA_WARN:
            findings.append({"code": code, "level": "warn", "file": path, "line": ln,
                             "message": f"\"{m}\" ({_fmt(dens)} hits / 100 words)"})
    density = len(hits) * 100.0 / total_words if total_words else 0.0
    if density > DOC_BLOCK:
        findings.append({"code": "P00", "level": "block", "file": path, "line": 1,
                         "message": f"pattern density {_fmt(density)}/100 words"})
    return {"file": path, "paragraphs": len(paras), "hits": len(hits), "words": total_words,
            "density": round(density, 2), "findings": findings}


# --- consent profile (plan D4) ------------------------------------------------------------------------------
CONSENT_WORDS = {"en": 25, "vi": 40}     # Vietnamese words are syllables
VI_LETTER = re.compile(r"[ăâđêôơưàảãáạằẳẵắặầẩẫấậèẻẽéẹềểễếệìỉĩíịòỏõóọồổỗốộờởỡớợùủũúụừửữứựỳỷỹýỵ]", re.I)
JARGON = re.compile(r"(?i)\b(?:randomi[sz](?:ed|ation)|placebo|double[- ]blind|single[- ]blind|cohort|biomarkers?|"
                    r"pharmacokinetics?|adverse events?|pseudonymi[sz](?:ed|ation)|de-?identified|ngẫu nhiên ho[áa]|"
                    r"giả dược|mù đôi|mù đơn|đoàn hệ|dấu ấn sinh học|dược động học|biến cố bất lợi|mã ho[áa])\b")
EXPLAIN = re.compile(r"\(|\bnghĩa là\b|\btức là\b|\bthat is\b|\bwhich means\b|\bmeaning\b|\bi\.e\.")
OBLIGATION = re.compile(r"(?i)\b(?:must|shall|will) be [a-z]+(?:ed|en)\b|\b(?:is|are) (?:required|obliged|expected) to\b|"
                        r"\bphải được\b|\bbắt buộc phải\b|\bđược yêu cầu\b")
CONSENT_SPLIT = re.compile(r"(?<=[.!?;])\s+")


def lint_consent(path: str) -> dict:
    """Plain-language warns for a consent form or information sheet: CF01 long sentence, CF02 unexplained jargon,
    CF03 passive obligation. Headings, tables, fences and HTML comments are skipped."""
    text = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    text = re.sub(r"<!--.*?-->", lambda m: re.sub(r"[^\n]", " ", m.group(0)), text, flags=re.S)
    findings, sentences, fence = [], 0, False

    def add(code: str, n: int, msg: str) -> None:
        findings.append({"code": code, "level": "warn", "file": path, "line": n, "message": msg})

    for n, line in enumerate(text.splitlines(), 1):
        if FENCE.match(line):
            fence = not fence
            continue
        s = line.strip()
        if fence or not s or s.startswith(("#", "|")):
            continue
        s = re.sub(r"^(?:[-*+]|\d+[.)])\s+", "", s)
        s = re.sub(r"\[\[[^\]]*\]\]|\{\{[^{}]*\}\}", "X", s)
        for sent in CONSENT_SPLIT.split(s):
            if not sent.strip():
                continue
            sentences += 1
            nw = len(re.findall(r"[^\W_]+", sent))
            limit = CONSENT_WORDS["vi" if VI_LETTER.search(sent) else "en"]
            if nw > limit:
                add("CF01", n, f"sentence of {nw} words (plain-language target ≤ {limit}); split it")
            for m in JARGON.finditer(sent):
                if not EXPLAIN.search(sent[m.end():m.end() + 25]):
                    add("CF02", n, f'"{m.group(0)}" is not explained in plain words right after it')
            for m in OBLIGATION.finditer(sent):
                add("CF03", n, f'"{m.group(0)}" is a passive obligation; say who does what ("you sign", '
                               '"the study team keeps")')
    return {"file": path, "sentences": sentences, "findings": findings}


# --- slides -----------------------------------------------------------------------------------------------

VERBS = {
    "is", "are", "was", "were", "be", "been", "has", "have", "had", "does", "do", "did", "can", "could", "may",
    "might", "should", "will", "would", "improves", "improve", "improved", "reduces", "reduce", "increases",
    "increase", "lowers", "lower", "predicts", "predict", "shows", "show", "causes", "cause", "leads", "lead",
    "fails", "fail", "works", "work", "differs", "differ", "associated", "linked", "needs", "need", "means",
    "là", "có", "được", "bị", "giảm", "tăng", "làm", "gây", "dẫn", "khác", "cho", "thấy", "liên", "quan", "không",
    "cần", "nên", "đã", "sẽ", "đang", "cải", "thiện", "dự", "báo", "tốt", "kém"}
S20_RX = re.compile(r"\b(?:this|the)\s+(?:chart|graph|figure|slide|plot|table)\s+shows?\b|\bas\s+shown\s+(?:in\s+the\s+(?:figure|chart|graph)|above|below)\b|"
                    r"\b(?:biểu\s+đồ|hình|bảng|slide)\s+(?:này|trên|dưới)\s+cho\s+thấy\b|\bnhư\s+(?:hình|biểu\s+đồ|bảng)\s+(?:trên|dưới)\b", re.I)
HYPE_RX = re.compile(
    r"\b(?:dramatically|remarkably|greatly|vastly|massively|completely|totally)\s+(?:improv|reduc|increas|decreas|lower|rais|prevent|eliminat|cur)\w*|"
    r"\b(?:cures?|proven\s+to|undoubtedly|definitively|guarantees?|breakthrough|revolutionary|game-chang(?:er|ing)|groundbreaking)\b|"
    r"\b(?:vượt\s+trội|ngoạn\s+mục|rõ\s+rệt|triệt\s+để|chữa\s+khỏi\s+hoàn\s+toàn|đột\s+phá|mang\s+tính\s+cách\s+mạng)\b|\bchắc\s+chắn\s+(?:hiệu\s+quả|giảm|tăng)", re.I)
HEDGE_RX = re.compile(r"\b(?:may|might|could|suggests?|appears?|possibly|potentially|likely|tends?\s+to|có\s+thể|gợi\s+ý|có\s+xu\s+hướng|"
                      r"dường\s+như|nhiều\s+khả\s+năng)\b", re.I)


def topic_title(title: str) -> bool:
    toks = re.findall(r"[^\W_]+(?:[-'’][^\W_]+)*", title, re.U)
    if not toks or len(toks) > 4:
        return False
    return not any(t.lower() in VERBS or (t.lower().endswith("ed") and len(t) > 4) for t in toks)


class _SlideHTML(html.parser.HTMLParser):
    """A slide is a <section> (class "slide" or plain) or, without sections, everything from one heading to the next."""
    VOID = {"br", "img", "hr", "meta", "link", "input", "source", "wbr", "area", "col", "embed", "param", "track"}
    SKIP_TAGS = {"script", "style", "template", "aside", "svg", "noscript"}
    NOTES_CLS = re.compile(r"\b(?:notes?|speaker-notes|footer|credit|source|cite)\b", re.I)

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.slides: list[dict] = []
        self.stack: list[tuple[str, bool]] = []   # tag, skip
        self.cur: dict | None = None
        self.sections_open = 0
        self.head_buf: list[str] | None = None
        self.head_tag = ""
        self.seen_heading = False

    def _new(self) -> dict:
        self.cur = {"title": "", "body": [], "index": len(self.slides) + 1, "is_title_layout": False}
        self.slides.append(self.cur)
        return self.cur

    def _slide(self) -> dict:
        return self.cur if self.cur is not None else self._new()

    def handle_starttag(self, tag, attrs):
        if tag in self.VOID:
            return
        cls = dict(attrs).get("class", "") or ""
        skip = tag in self.SKIP_TAGS or bool(self.NOTES_CLS.search(cls))
        if tag == "section" and not any(s for _, s in self.stack):
            self.sections_open += 1
            self._new()
        self.stack.append((tag, skip))
        if tag in ("h1", "h2", "h3") and not any(s for _, s in self.stack[:-1]):
            self.head_buf = []
            self.head_tag = tag

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        while self.stack:
            t, _ = self.stack.pop()
            if t == tag:
                break
        if self.head_buf is not None and tag == self.head_tag:
            title = " ".join("".join(self.head_buf).split())
            self.head_buf = None
            if not self.sections_open and (self.cur is None or self.cur["title"]):
                self._new()   # no sections: each heading starts a slide
            sl = self._slide()
            if not sl["title"]:
                sl["title"] = title
                if tag == "h1" and not self.seen_heading:
                    sl["is_title_layout"] = True   # the first h1 is the deck title
            else:
                sl["body"].append(title)
            self.seen_heading = True
        if tag == "section" and self.sections_open:
            self.sections_open -= 1
            if not self.sections_open:
                self.cur = None

    def handle_data(self, data):
        if any(skip for _, skip in self.stack):
            return
        if self.head_buf is not None:
            self.head_buf.append(data)
            return
        txt = " ".join(data.split())
        if txt and (self.cur is not None or self.seen_heading or self.sections_open):
            self._slide()["body"].append(txt)


def _load_html(path: str) -> list[dict]:
    p = _SlideHTML()
    p.feed(unicodedata.normalize("NFC", Path(path).read_text(encoding="utf-8-sig", errors="replace")))
    return p.slides


def _shape_texts(shapes, skip=None):
    """Text paragraphs of shapes, descending into groups and table cells; notes are never reached."""
    for sh in shapes:
        if skip is not None and sh.shape_id == skip.shape_id:
            continue
        if hasattr(sh, "shapes"):   # group shape
            yield from _shape_texts(sh.shapes)
            continue
        if getattr(sh, "has_table", False):
            paras = [p for row in sh.table.rows for cell in row.cells for p in cell.text_frame.paragraphs]
        elif getattr(sh, "has_text_frame", False):
            paras = list(sh.text_frame.paragraphs)
        else:
            continue
        for para in paras:
            t = unicodedata.normalize("NFC", "".join(r.text for r in para.runs)).strip()
            if t:
                yield t


def _load_pptx(path: str) -> list[dict]:
    try:
        from pptx import Presentation  # type: ignore
    except ImportError:
        print("lint_prose: reading a .pptx needs python-pptx. Install it: python -m pip install python-pptx",
              file=sys.stderr)
        sys.exit(2)
    prs = Presentation(path)
    slides = []
    for i, s in enumerate(prs.slides, 1):
        title_shape = s.shapes.title
        title = unicodedata.normalize("NFC", title_shape.text_frame.text).strip() if title_shape is not None and title_shape.has_text_frame else ""
        body = list(_shape_texts(s.shapes, title_shape))
        slides.append({"title": title, "body": body, "index": i,
                       "is_title_layout": s.slide_layout.name.lower() == "title slide"})
    return slides


def lint_slides(path: str) -> dict:
    slides = _load_pptx(path) if path.lower().endswith(".pptx") else _load_html(path)
    findings: list[dict] = []

    def add(code, idx, msg):
        findings.append({"code": code, "level": "warn", "file": path, "line": idx, "message": msg})

    for s in slides:
        t = s["title"]
        if t and not s.get("is_title_layout") and topic_title(t):
            add("S17", s["index"], f"topic title \"{t}\" (state the finding as a claim)")
        for chunk in ([t] if t else []) + s["body"]:
            for sent in SENT_SPLIT.split(chunk):
                m = S20_RX.search(sent)
                if m:
                    add("S20", s["index"], f"\"{m.group(0)}\" explains the obvious; say what the reader should see")
                h = HYPE_RX.search(sent)
                if h and not HEDGE_RX.search(sent):
                    add("S21", s["index"], f"\"{h.group(0)}\" without a hedge in a medical claim")
    return {"file": path, "slides": len(slides), "findings": findings}


# --- CLI --------------------------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Count AI-sounding patterns in academic prose (P01-P30, S17/S20/S21).")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--lang", choices=["vi", "en", "auto"], default="auto")
    ap.add_argument("--slides", action="store_true", help="lint .pptx/.html slide text (S17, S20, S21)")
    ap.add_argument("--count-words", action="store_true", help="print the prose word count and exit 0")
    ap.add_argument("--profile", choices=["academic", "consent"], default="academic")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    for f in args.files:
        if not Path(f).is_file():
            print(f"lint_prose: file not found: {f}", file=sys.stderr)
            return 2

    if args.profile == "consent" and args.slides:
        print("lint_prose: --profile consent is for text files, not --slides", file=sys.stderr)
        return 2

    try:
        if args.count_words:
            for f in args.files:
                n = word_count(Path(f).read_text(encoding="utf-8-sig", errors="replace"))
                print(f"words: {n}" if len(args.files) == 1 else f"{f}: words: {n}")
            return 0
        results = [lint_consent(f) if args.profile == "consent" else (lint_slides(f) if args.slides else lint_file(f, args.lang))
                   for f in args.files]
    except OSError as e:
        print(f"lint_prose: {e}", file=sys.stderr)
        return 2

    findings = [x for r in results for x in r["findings"]]
    if args.json:
        print(json.dumps({"files": [{k: v for k, v in r.items() if k != "findings"} for r in results],
                          "findings": findings}, ensure_ascii=False, indent=2))
    else:
        for r in results:
            for x in r["findings"]:
                print(f"{x['code']} {x['level']} {x['file']}:{x['line']}: {x['message']}")
            if args.profile == "consent":
                print(f"lint_prose: consent profile, {r['sentences']} sentences, {len(r['findings'])} warnings")
            elif args.slides:
                print(f"lint_prose: {r['slides']} slides, {len(r['findings'])} findings")
            else:
                print(f"lint_prose: {r['paragraphs']} paragraphs, {r['hits']} hits, {_fmt(r['density'])}/100 words")
    return 1 if any(x["level"] == "block" for x in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
