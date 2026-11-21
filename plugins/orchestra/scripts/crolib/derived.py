"""Ledger lookup by result id/part and safe evaluation of derived formulas. Standard library only.

Shared by check_numbers.py (`<!-- derived: -->` comments) and figures.py (flow-box counts).
"""
from __future__ import annotations

import ast
import json
import re
from decimal import Decimal
from pathlib import Path

PARTS = ("value", "n", "count", "p", "lo", "hi")
RID = re.compile(r"R-A\d+-\d{3}(?:\.(?:value|n|count|p|lo|hi)\b)?")
ID_PART = re.compile(r"R-A\d+-\d{3}\.([A-Za-z_]\w*)")
PURE = re.compile(r"[\d\s+\-*/().]*")


def ledger_by_id(project: Path) -> dict[str, dict]:
    """Records of `<project>/ledgers/results-ledger.json` keyed by id. Missing file -> FileNotFoundError."""
    path = Path(project) / "ledgers" / "results-ledger.json"
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    results = data.get("results") if isinstance(data, dict) else None
    if not isinstance(results, list):
        raise ValueError(f"{path}: no 'results' list")
    return {r["id"]: r for r in results if isinstance(r, dict) and isinstance(r.get("id"), str)}


def value_of(by_id: dict, ref: str) -> Decimal:
    """Numeric value of `R-A1-001` or `R-A1-001.part` (part in PARTS; lo/hi are the CI bounds)."""
    rid, _, part = ref.partition(".")
    rec = by_id.get(rid)
    if rec is None:
        raise KeyError(f"unknown result id {rid}")
    if part and part not in PARTS:
        raise KeyError(f"{ref}: part .{part} is not allowed (allowed: {', '.join('.' + p for p in PARTS)})")
    if part in ("lo", "hi"):
        ci = rec.get("ci")
        v = ci[0 if part == "lo" else 1] if isinstance(ci, list) and len(ci) == 2 else None
    else:
        v = rec.get(part or "value")
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise KeyError(f"{ref} has no numeric {part or 'value'} in the ledger")
    return Decimal(str(v))


def eval_pure(expr: str) -> Decimal:
    """Evaluate numbers with unary +/- and + - * / only. Anything else raises ValueError."""
    def go(node):
        if isinstance(node, ast.Expression):
            return go(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return Decimal(str(node.value))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            v = go(node.operand)
            return -v if isinstance(node.op, ast.USub) else v
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            a, b = go(node.left), go(node.right)
            if isinstance(node.op, ast.Add):
                return a + b
            if isinstance(node.op, ast.Sub):
                return a - b
            return a * b if isinstance(node.op, ast.Mult) else a / b
        raise ValueError("not a pure formula")
    return go(ast.parse(expr.strip(), mode="eval"))


def evaluate(expr: str, by_id: dict) -> Decimal:
    """Replace result ids in EXPR by their ledger values and evaluate the pure formula.

    Unknown id / missing part -> KeyError; anything that is not a pure formula, a syntax error or an
    arithmetic error (division by zero) -> ValueError.
    """
    vals = {r: value_of(by_id, r) for r in set(RID.findall(expr))}
    bad = [p for p in ID_PART.findall(expr) if p not in PARTS]
    if bad:
        raise KeyError(f"part .{bad[0]} is not allowed (allowed: {', '.join('.' + p for p in PARTS)})")
    try:
        return eval_pure(RID.sub(lambda m: "(" + str(vals[m.group(0)]) + ")", expr))
    except SyntaxError as e:
        raise ValueError(f"cannot parse formula {expr!r}") from e
    except ArithmeticError as e:
        raise ValueError(f"cannot evaluate formula {expr!r}: {e.__class__.__name__}") from e
