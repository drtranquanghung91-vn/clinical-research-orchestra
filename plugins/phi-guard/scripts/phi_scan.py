#!/usr/bin/env python3
"""phi-guard: stop patient identifiers leaving the machine, and scan deliverables for them.

Hook mode (PreToolUse, stdin JSON): strong signals (CCCD/CMND, BHYT card, labelled name, date of
birth, record number, address) -> deny; weak signals (phone, email, full date, "BN/ông/bà <Name>")
-> ask. Bash is checked only for outbound commands (search_lit, curl, wget, Invoke-WebRequest,
python -c with urllib/requests).
File mode: python phi_scan.py --file draft.md ... (exit 0 clean or warnings only, 1 on any strong
finding, 2 if a file cannot be read).
Allowlist: one tool-name regex per line in ~/.claude/phi-guard-allow.txt (default ^mcp__ccd_;
override the path with PHI_GUARD_ALLOW_FILE).
Heuristic: a clean scan does not prove a file is free of identifiers; images need a human look.
"""
from __future__ import annotations

import json
import pathlib
import os
import re
import sys
import unicodedata
import urllib.parse

DEFAULT_ALLOW = [r"^mcp__ccd_"]
STRIP = [
    re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"),
    re.compile(r"\b10\.\d{4,9}/\S+"),
    re.compile(r"\bPMC?ID[:\s]*\d+", re.I),
    re.compile(r"\bNCT\d{8}\b"),
]
URL = re.compile(r"https?://\S+")
URL_TRAIL = ")]>.,;:'\""
VI_UPPER = ("AÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬBCDĐEÈÉẺẼẸÊỀẾỂỄỆFGHIÌÍỈĨỊJKLMNOÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢPQRSTUÙÚỦŨỤƯỪỨỬỮỰVWXYỲÝỶỸỴZ")
VI_LOWER = VI_UPPER.lower()
_U, _L = f"[{VI_UPPER}]", f"[{VI_LOWER}]"
_UD = "[" + "".join(c for c in VI_UPPER if not ("A" <= c <= "Z")) + "]"  # upper-case letters with a diacritic
_END = f"(?![{VI_UPPER}{VI_LOWER}])"
_CAPW = f"{_U}{{2,7}}{_END}"
_CAPWD = f"(?={_U}{{2,7}}{_END}){_U}*?{_UD}{_U}*{_END}"  # an all-caps word containing a diacritic
# Title-case name of 2-5 words, or an all-caps name of 3-5 words or of 2+ words with a Vietnamese diacritic
# (so acronyms such as "COPD GOLD" after a label are not taken for a name).
NAME = (rf"(?:{_U}{_L}+(?:\s+{_U}{_L}+){{1,4}}|{_CAPW}(?:\s+{_CAPW}){{2,4}}|"
        rf"(?:{_CAPW}\s+){{1,4}}{_CAPWD}|{_CAPWD}(?:\s+{_CAPW}){{1,4}})")
NAME3 = rf"{_U}{_L}+(?:\s+{_U}{_L}+){{2,4}}"  # 3-5 title-case words
STRONG = [
    ("CCCD number", re.compile(r"(?<!\d)0\d{2}[\s.]?\d{3}[\s.]?\d{6}(?!\d)")),
    ("BHYT card", re.compile(r"\b[A-Z]{2}\d{13}\b")),
    ("patient name", re.compile(r"(?i:họ\s*(?:và\s*)?tên|tên\s*(?:bệnh\s*nhân|người\s*bệnh)|bệnh\s*nhân|"
                                r"người\s*bệnh|\bBN|patient(?:'s)?[\s_]*name|\bname|\bpatient)\s*[:：]\s*" + NAME)),
    ("date of birth", re.compile(r"(?i:ngày\s*sinh|sinh\s*ngày|năm\s*sinh|\bDOB|date\s*of\s*birth)\s*[:：]?\s*"
                                 r"\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4}")),
    ("record number", re.compile(r"(?i:mã\s*(?:bệnh\s*án|hồ\s*sơ|BN|bệnh\s*nhân|người\s*bệnh)|số\s*(?:bệnh\s*án|"
                                 r"hồ\s*sơ|lưu\s*trữ)|\bMRN|\bPID)\s*[:：#]?\s*"
                                 r"(?=[A-Za-z./\-]*\d)[A-Za-z0-9][A-Za-z0-9./\-]{3,}")),
    ("CMND number", re.compile(r"(?i:CMND|chứng\s*minh\s*(?:nhân\s*dân|thư))\s*[:：]?\s*\d{9}\b")),
    ("address", re.compile(r"(?i:địa\s*chỉ|address)\s*[:：]\s*\S+(?:\s+\S+){2,}")),
]
WEAK = [
    ("phone number", re.compile(r"(?<![\d.])(?:\+?84|0)[35789](?:[\s.\-]?\d){8}(?!\d)")),
    ("email", re.compile(r"\b[\w.+\-]+@[\w\-]+\.[\w.\-]+\b")),
    ("full date", re.compile(r"\b(?:0?[1-9]|[12]\d|3[01])[/.\-](?:0?[1-9]|1[0-2])[/.\-](?:19|20)\d{2}\b")),
    ("possible patient name", re.compile(r"(?i:\bBN|\bbệnh\s+nhân|\bngười\s+bệnh|\bông|\bbà|\banh|\bchị)\s+"
                                         + NAME3)),
]
# Bash is checked only when the command sends something out (search_lit queries, HTTP clients).
BASH_OUTBOUND = re.compile(r"search_lit|\bcurl\b|\bwget\b|Invoke-WebRequest", re.I)
BASH_PY_C = re.compile(r"\bpython[0-9.]*(?:\.exe)?\b[^|;&\n]*?\s-c\b", re.I)
BASH_PY_NET = re.compile(r"\burllib\b|\brequests\b")


def bash_is_outbound(command: str) -> bool:
    return bool(BASH_OUTBOUND.search(command) or (BASH_PY_C.search(command) and BASH_PY_NET.search(command)))


def _allow_patterns() -> list:
    pats = []
    lines = list(DEFAULT_ALLOW)
    f = pathlib.Path(os.environ.get("PHI_GUARD_ALLOW_FILE") or (pathlib.Path.home() / ".claude" / "phi-guard-allow.txt"))
    try:
        if f.exists():
            lines += [l.strip() for l in f.read_text(encoding="utf-8", errors="replace").splitlines()
                      if l.strip() and not l.strip().startswith("#")]
    except OSError as e:
        print(f"[phi-guard] cannot read allowlist {f}: {e}", file=sys.stderr)
    for l in lines:
        try:
            pats.append(re.compile(l))
        except re.error as e:
            print(f"[phi-guard] ignoring invalid allowlist regex {l!r}: {e}", file=sys.stderr)
    return pats


def allowed(tool: str) -> bool:
    return any(p.search(tool) for p in _allow_patterns())


def _url_text(m: "re.Match") -> str:
    raw = m.group(0)
    url = raw.rstrip(URL_TRAIL)
    tail = raw[len(url):]
    try:
        parts = urllib.parse.urlsplit(url)
        text = urllib.parse.unquote_plus(parts.path + " " + parts.query + " " + parts.fragment)
    except ValueError:
        text = urllib.parse.unquote_plus(url)  # unparseable: scan the raw URL text
    return " " + text.replace("&", " ").replace("=", " ") + " " + tail


def _texts(obj, out: list) -> None:
    """Collect scannable strings: every string value raw, plus 'key: value' for each dict entry."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.append(str(k))
            if isinstance(v, (dict, list, tuple)):
                _texts(v, out)
            elif isinstance(v, str):
                out.append(f"{k}: {v}")
                out.append(v)
            elif v is not None:
                out.append(str(v))
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _texts(v, out)
    elif obj is not None:
        out.append(str(obj))


def scan(text: str) -> tuple[list[str], list[str]]:
    text = URL.sub(_url_text, unicodedata.normalize("NFC", text))
    for rx in STRIP:
        text = rx.sub(" ", text)
    return [l for l, rx in STRONG if rx.search(text)], [l for l, rx in WEAK if rx.search(text)]


def decide(tool: str, tool_input) -> dict | None:
    if allowed(tool):
        return None
    if tool == "Bash":
        command = str(tool_input.get("command", "")) if isinstance(tool_input, dict) else str(tool_input)
        if not bash_is_outbound(command):
            return None  # local command: nothing leaves the machine
        tool_input = {"command": command}
    texts: list = []
    _texts(tool_input, texts)
    strong: list = []
    weak: list = []
    for t in texts:
        st, wk = scan(t)
        strong += [x for x in st if x not in strong]
        weak += [x for x in wk if x not in weak]
    if strong:
        return {"permissionDecision": "deny", "permissionDecisionReason": (
            f"[phi-guard] Blocked: input to {tool} looks like it contains a patient identifier "
            f"({', '.join(strong)}). Remove names, dates of birth, ID/insurance/record numbers and addresses; "
            "keep clinical facts only (e.g. 'male, 67, type 2 diabetes') and call again. / "
            "Đã chặn: đầu vào có vẻ chứa thông tin định danh người bệnh. Bỏ họ tên, ngày sinh, CCCD/CMND, "
            "mã BHYT, mã hồ sơ, địa chỉ; chỉ giữ dữ kiện lâm sàng rồi gọi lại.")}
    if weak:
        return {"permissionDecision": "ask", "permissionDecisionReason": (
            f"[phi-guard] Input to {tool} contains {', '.join(weak)}. If this belongs to a patient, choose No "
            "and remove it. / Nếu đây là thông tin của người bệnh (định danh), chọn Không và bỏ thông tin đó.")}
    return None


def scan_file(path: pathlib.Path) -> list[dict]:
    """Scan each line, and each line joined to the next (a label and its value on two lines).
    A finding that needs both lines is reported on the first one."""
    lines = pathlib.Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    alone = [scan(line) for line in lines]
    findings = []
    for i, line in enumerate(lines):
        strong, weak = list(alone[i][0]), list(alone[i][1])
        if i + 1 < len(lines):
            ps, pw = scan(line + "\n" + lines[i + 1])
            strong += [l for l in ps if l not in strong and l not in alone[i + 1][0]]
            weak += [l for l in pw if l not in weak and l not in alone[i + 1][1]]
        findings += [{"code": "E-PHI", "severity": "block", "file": str(path), "line": i + 1, "label": l}
                     for l in strong]
        findings += [{"code": "E-PHI", "severity": "warn", "file": str(path), "line": i + 1, "label": l}
                     for l in weak]
    return findings


def self_test() -> int:
    cases = [({"q": "CCCD 079 123 456789"}, "deny"), ({"q": "liên hệ 0903 123 456"}, "ask"),
             ({"q": "nam 72 tuổi, eGFR 28"}, None)]
    bad = 0
    for ti, want in cases:
        d = decide("mcp__x__y", ti)
        got = d["permissionDecision"] if d else None
        bad += got != want
        print(("OK   " if got == want else "FAIL ") + f"{want!s:>5} <- {json.dumps(ti, ensure_ascii=False)}")
    return 1 if bad else 0


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return self_test()
    if argv and argv[0] == "--file":
        if not argv[1:]:
            print("usage: python phi_scan.py --file FILE [FILE ...]", file=sys.stderr)
            return 2
        findings = []
        for p in argv[1:]:
            try:
                findings += scan_file(pathlib.Path(p))
            except OSError as e:
                print(f"phi_scan: cannot read {p}: {e.strerror or e}", file=sys.stderr)
                return 2
        for f in findings:
            print(f"{f['code']} {f['severity']} {f['file']}:{f['line']} {f['label']}")
        return 1 if any(f["severity"] == "block" for f in findings) else 0
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8-sig", errors="replace"))
        if not isinstance(data, dict):
            raise ValueError("input is not a JSON object")
        d = decide(str(data.get("tool_name", "")), data.get("tool_input", {}))
    except Exception as e:  # fail safe: never let an error silently allow the call
        d = {"permissionDecision": "ask", "permissionDecisionReason": (
            f"[phi-guard] could not check this input ({type(e).__name__}: {e}); review it before allowing. / "
            "Không kiểm tra được đầu vào, hãy xem lại trước khi cho phép.")}
    if d:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", **d}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass
    sys.exit(main())
