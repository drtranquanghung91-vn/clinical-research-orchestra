#!/usr/bin/env python3
"""Draw the figures of a project from 07_present/figures/figures.json.

  python figures.py <project> [--only F1,F2] [--dpi 300]

Types: forest, km (Kaplan-Meier from the de-identified CSV), rates, flow. Every plotted estimate comes
from the results ledger by id; nothing is typed. Writes F<n>.svg, .pdf, .png and F<n>.data.json (every number
drawn plus the native-chart series slides use) into 07_present/figures/. Format: references/presenting/figures-spec.md.
Needs matplotlib (the install hint is printed when it is missing).
Exit codes: 0 = done; 2 = usage error, bad spec, unknown ledger id, bad data file, or matplotlib missing.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import textwrap
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crolib import derived, numfmt, projectcfg  # noqa: E402

SPEC_REL = "07_present/figures/figures.json"
OUT_REL = "07_present/figures"
TYPES = ("forest", "km", "rates", "flow")
ID_OK = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*\Z")
PALETTE = ["#1f4e79", "#c0504d", "#4f9a4f", "#8064a2", "#e69f00", "#2c9fb0"]
GREY = "#555555"
FLOW_BOX_CM, FLOW_GAP_CM = 1.7, 1.1


class FigureError(Exception):
    pass


def _lang_text(lang: str, vi: str, en: str) -> str:
    return vi if lang == "vi" else en


def _esc(s: str) -> str:
    return str(s).replace("$", r"\$")


def _num(x) -> float:
    return float(x)


# ---------------------------------------------------------------- ledger access

def _record(fid: str, by_id: dict, ref: str, need_ci: bool) -> dict:
    """Ledger record for a whole result id (a `.part` is validated, then refused: estimates are whole results)."""
    try:
        derived.value_of(by_id, ref)
    except KeyError as e:
        raise FigureError(f"{fid}: {e.args[0]}") from e
    if "." in ref:
        raise FigureError(f"{fid}: {ref} is a single part; use the whole result id (value and CI come from the ledger)")
    rec = by_id[ref]
    if need_ci and not (isinstance(rec.get("ci"), list) and len(rec["ci"]) == 2):
        raise FigureError(f"{fid}: {ref} has no confidence interval in the ledger")
    return rec


def _est_text(rec: dict, lang: str) -> str:
    v = numfmt.render(rec, "value", lang)
    if isinstance(rec.get("ci"), list) and len(rec["ci"]) == 2:
        return f"{v} ({numfmt.render(rec, 'ci', lang)})"
    return v


def _rows(fig: dict, by_id: dict, lang: str, need_ci: bool) -> list[dict]:
    fid = fig["id"]
    rows = fig.get("rows")
    if not isinstance(rows, list) or not rows:
        raise FigureError(f"{fid}: 'rows' must be a non-empty list")
    out = []
    for i, row in enumerate(rows):
        if not isinstance(row, dict) or not isinstance(row.get("label"), str) or not isinstance(row.get("result"), str):
            raise FigureError(f"{fid}: row {i + 1} needs 'label' and 'result'")
        rec = _record(fid, by_id, row["result"], need_ci)
        has_ci = isinstance(rec.get("ci"), list) and len(rec["ci"]) == 2
        out.append({"label": row["label"], "ref": row["result"], "est": _num(rec["value"]),
                    "lo": _num(rec["ci"][0]) if has_ci else None, "hi": _num(rec["ci"][1]) if has_ci else None,
                    "text": _est_text(rec, lang), "filled": row.get("filled", True) is not False})
    return out


# ---------------------------------------------------------------- Kaplan-Meier (stdlib)

def km_curve(obs: list[tuple[float, int]], max_time: float) -> list[list[float]]:
    """Product-limit estimate as step-plot points [[t, S], ...]. Times above max_time are censored at max_time."""
    clipped = [(min(t, max_time), e if t <= max_time else 0) for t, e in obs]
    s = 1.0
    pts: list[list[float]] = [[0, 1.0]]
    for t in sorted({t for t, e in clipped if e}):
        at_risk = sum(1 for tt, _ in clipped if tt >= t)
        d = sum(1 for tt, e in clipped if e and tt == t)
        new = s * (1 - d / at_risk)
        pts.append([_clean_t(t), round(s, 6)])
        pts.append([_clean_t(t), round(new, 6)])
        s = new
    if pts[-1][0] < max_time:
        pts.append([_clean_t(max_time), round(s, 6)])
    return pts


def _clean_t(t: float):
    return int(t) if float(t).is_integer() else t


def _surv_at(points: list[list[float]], t: float) -> float:
    s = 1.0
    for x, y in points:
        if x <= t:
            s = y
    return s


def _read_km(project: Path, fig: dict) -> tuple[dict, str, str]:
    fid = fig["id"]
    for k in ("data", "time", "event", "group"):
        if not isinstance(fig.get(k), str):
            raise FigureError(f"{fid}: km needs '{k}'")
    rel = fig["data"]
    root = (project / "04_data").resolve()
    path = (project / rel).resolve()
    if path.parent != root or not path.name.lower().endswith(".deid.csv"):
        raise FigureError(f"{fid}: km data must be a 04_data/*.deid.csv file inside the project (got {rel})")
    try:
        raw = path.read_bytes()
    except OSError as e:
        raise FigureError(f"{fid}: cannot read {rel}: {e}") from e
    sha = hashlib.sha256(raw).hexdigest()
    reader = csv.DictReader(raw.decode("utf-8-sig").splitlines())
    for k in ("time", "event", "group"):
        if fig[k] not in (reader.fieldnames or []):
            raise FigureError(f"{fid}: column {fig[k]!r} not found in {rel}")
    groups: dict[str, list[tuple[float, int]]] = {}
    skipped = 0
    for row in reader:
        t, e, g = (row[fig["time"]] or "").strip(), (row[fig["event"]] or "").strip(), (row[fig["group"]] or "").strip()
        if not t or not e or not g:
            skipped += 1
            continue
        try:
            tv, ev = float(t), int(float(e))
        except ValueError as exc:
            raise FigureError(f"{fid}: non-numeric time/event value in {rel}: {t!r}, {e!r}") from exc
        if ev not in (0, 1) or tv < 0:
            raise FigureError(f"{fid}: event must be 0/1 and time >= 0 in {rel} (got time={t}, event={e})")
        groups.setdefault(g, []).append((tv, ev))
    if skipped:
        print(f"figures.py: {fid}: {skipped} row(s) with a blank time, event or group skipped", file=sys.stderr)
    order = fig.get("order")
    if order is None:
        order = sorted(groups)
        print(f"figures.py: {fid}: no 'order' given, groups sorted alphabetically: {order}", file=sys.stderr)
    elif not isinstance(order, list):
        raise FigureError(f"{fid}: 'order' must be a list")
    missing = [g for g in order if g not in groups]
    if missing:
        raise FigureError(f"{fid}: group level(s) {missing} not found in {rel} (found: {sorted(groups)})")
    extra = [g for g in groups if g not in order]
    if extra:
        print(f"figures.py: {fid}: group level(s) {extra} are not in 'order' and are not drawn", file=sys.stderr)
    return {g: groups[g] for g in order}, sha, rel


# ---------------------------------------------------------------- drawing helpers

class Ctx:
    def __init__(self, plt, style: dict, lang: str, dpi: int):
        self.plt, self.lang, self.dpi = plt, lang, dpi
        self.colors = style.get("colors") if isinstance(style.get("colors"), dict) else {}
        self.font = str(style.get("font", "Arial"))
        self.size = float(style.get("font_size", 9))
        self.width_cm = float(style.get("width_cm", 16))

    def color(self, key: str, i: int = 0) -> str:
        return self.colors.get(key) or PALETTE[i % len(PALETTE)]

    def figure(self, fig: dict, height_cm: float):
        width = float(fig.get("width_cm", self.width_cm)) / 2.54
        return self.plt.figure(figsize=(width, height_cm / 2.54))

    def fmt_axis(self, v: float) -> str:
        s = f"{v:g}"
        return s.replace(".", ",") if self.lang == "vi" else s


def _style_axes(ax) -> None:
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=3, width=0.6)
    for side in ("left", "bottom"):
        ax.spines[side].set_linewidth(0.6)


def _source_note(ctx: Ctx, f, text: str | None) -> None:
    if text:
        f.text(0.01, 0.012, _esc(text), ha="left", va="bottom", fontsize=ctx.size - 1.5, color=GREY)


def _save(ctx: Ctx, f, outdir: Path, fid: str) -> None:
    for ext in ("svg", "pdf", "png"):
        kw = {"dpi": ctx.dpi} if ext == "png" else {}
        if ext == "svg":
            kw["metadata"] = {"Date": None}
        elif ext == "pdf":
            kw["metadata"] = {"CreationDate": None, "Creator": "figures.py"}
        f.savefig(outdir / f"{fid}.{ext}", format=ext, **kw)
    ctx.plt.close(f)


def _draw_forest(ctx: Ctx, fig: dict, rows: list[dict]):
    n = len(rows)
    height = 3.2 + 0.85 * n + (0.9 if fig.get("title") else 0)
    f = ctx.figure(fig, height)
    bottom = 1.9 / height
    top = 1 - (1.1 if fig.get("title") else 0.5) / height
    ax = f.add_axes([0.27, bottom, 0.45, top - bottom])
    null = fig.get("null", 1)
    ys = list(range(n, 0, -1))
    col = ctx.color("forest", 0)
    for y, r in zip(ys, rows):
        ax.plot([r["lo"], r["hi"]], [y, y], color=col, lw=1.1, solid_capstyle="butt")
        ax.plot([r["est"]], [y], marker="s", ms=5.5, color=col, mfc=col if r["filled"] else "white", mew=1.1)
    ax.axvline(null, color=GREY, lw=0.8, ls="--")
    if fig.get("log_scale"):
        ax.set_xscale("log")
        lo, hi = min(r["lo"] for r in rows + [{"lo": null}]), max(r["hi"] for r in rows + [{"hi": null}])
        ticks = [t for t in (0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50) if lo / 1.6 <= t <= hi * 1.6]
        if ticks:
            ax.set_xticks(ticks)
        ax.set_xticklabels([ctx.fmt_axis(t) for t in ticks])
        ax.minorticks_off()
    ax.set_yticks(ys)
    ax.set_yticklabels([_esc(r["label"]) for r in rows])
    ax.set_ylim(0.4, n + 0.6)
    ax.set_xlabel(_esc(fig.get("x_label", "")))
    _style_axes(ax)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    tr = ax.get_yaxis_transform()
    ax.text(1.06, n + 0.5, _lang_text(ctx.lang, "Ước lượng (KTC 95%)", "Estimate (95% CI)"), transform=tr, ha="left",
            va="bottom", fontsize=ctx.size, fontweight="bold")
    for y, r in zip(ys, rows):
        ax.text(1.06, y, _esc(r["text"]), transform=tr, ha="left", va="center", fontsize=ctx.size)
    if fig.get("title"):
        f.text(0.01, 1 - 0.3 / height, _esc(fig["title"]), ha="left", va="top", fontsize=ctx.size + 1, fontweight="bold")
    _source_note(ctx, f, fig.get("source"))
    return f


def _draw_rates(ctx: Ctx, fig: dict, rows: list[dict]):
    n = len(rows)
    height = 3.0 + 0.9 * n + (0.9 if fig.get("title") else 0)
    f = ctx.figure(fig, height)
    bottom = 1.9 / height
    top = 1 - (1.1 if fig.get("title") else 0.5) / height
    ax = f.add_axes([0.2, bottom, 0.5, top - bottom])
    ys = list(range(n, 0, -1))
    xmax = max((r["hi"] if r["hi"] is not None else r["est"]) for r in rows)
    for i, (y, r) in enumerate(zip(ys, rows)):
        col = ctx.color(r["label"], i)
        ax.barh(y, r["est"], height=0.55, color=col if r["filled"] else "white", edgecolor=col, linewidth=1.1)
        if r["lo"] is not None:
            ax.plot([r["lo"], r["hi"]], [y, y], color="black", lw=1.0)
            for x in (r["lo"], r["hi"]):
                ax.plot([x, x], [y - 0.14, y + 0.14], color="black", lw=1.0)
    ax.set_xlim(0, xmax * 1.08)
    ax.set_ylim(0.4, n + 0.6)
    ax.set_yticks(ys)
    ax.set_yticklabels([_esc(r["label"]) for r in rows])
    ax.set_xlabel(_esc(fig.get("unit", "")))
    ax.xaxis.set_major_formatter(ctx.plt.FuncFormatter(lambda v, _p: ctx.fmt_axis(v)))
    _style_axes(ax)
    tr = ax.get_yaxis_transform()
    for y, r in zip(ys, rows):
        ax.text(1.04, y, _esc(r["text"]), transform=tr, ha="left", va="center", fontsize=ctx.size)
    if fig.get("title"):
        f.text(0.01, 1 - 0.3 / height, _esc(fig["title"]), ha="left", va="top", fontsize=ctx.size + 1, fontweight="bold")
    _source_note(ctx, f, fig.get("source"))
    return f


def _draw_km(ctx: Ctx, fig: dict, series: list[dict], groups: dict, at_risk: dict, max_time, labels: dict, note: str):
    k = len(series)
    height = 8.0 + 0.55 * (k + 1) + (0.8 if fig.get("title") else 0)
    f = ctx.figure(fig, height)
    tbl_h = (0.55 * (k + 0.8)) / height
    tbl_b = 1.45 / height
    ax_b = tbl_b + tbl_h + 1.6 / height
    top = 1 - (1.1 if fig.get("title") else 0.5) / height
    ax = f.add_axes([0.14, ax_b, 0.8, top - ax_b])
    for i, s in enumerate(series):
        col = ctx.color(s["name"], i)
        xs, ys = [p[0] for p in s["points"]], [p[1] for p in s["points"]]
        ax.plot(xs, ys, color=col, lw=1.4, label=_esc(s["name"]), solid_joinstyle="miter")
        cens = [(t, _surv_at(s["points"], t)) for t, e in groups[s["name"]] if not e and t < max_time]
        if cens:
            ax.plot([c[0] for c in cens], [c[1] for c in cens], ls="none", marker="|", ms=4, mew=0.7, color=col)
    ax.set_xlim(0, max_time)
    ax.set_ylim(0, 1.02)
    ax.set_xticks(at_risk["times"])
    ax.yaxis.set_major_formatter(ctx.plt.FuncFormatter(lambda v, _p: ctx.fmt_axis(round(v, 1))))
    ax.set_xlabel(_esc(labels["x"]))
    ax.set_ylabel(_esc(labels["y"]))
    _style_axes(ax)
    ax.legend(frameon=False, loc="lower left", fontsize=ctx.size)
    tb = f.add_axes([0.14, tbl_b, 0.8, tbl_h], sharex=ax)
    tb.set_ylim(-0.6, k - 0.4)
    tb.set_yticks(range(k))
    tb.set_yticklabels([_esc(r["name"]) for r in reversed(at_risk["rows"])])
    for tick, r in zip(tb.get_yticklabels(), reversed(at_risk["rows"])):
        tick.set_color(ctx.color(r["name"], [s["name"] for s in series].index(r["name"])))
    for spine in tb.spines.values():
        spine.set_visible(False)
    tb.tick_params(axis="x", length=0, labelbottom=False)
    tb.tick_params(axis="y", length=0, pad=18)
    for j, r in enumerate(reversed(at_risk["rows"])):
        for t, nn in zip(at_risk["times"], r["n"]):
            tb.text(t, j, str(nn), ha="center", va="center", fontsize=ctx.size - 0.5)
    f.text(0.14, tbl_b + tbl_h + 0.05 / height * 0 + 0.25 / height, _lang_text(ctx.lang, "Số người còn trong theo dõi",
           "Number at risk"), ha="left", va="bottom", fontsize=ctx.size - 0.5, fontweight="bold")
    if fig.get("title"):
        f.text(0.01, 1 - 0.3 / height, _esc(fig["title"]), ha="left", va="top", fontsize=ctx.size + 1, fontweight="bold")
    _source_note(ctx, f, note)
    return f


def _draw_flow(ctx: Ctx, fig: dict, nodes: list[dict], edges: list[dict]):
    n_main = sum(1 for n in nodes if n["id"].startswith("n"))
    content = n_main * FLOW_BOX_CM + (n_main - 1) * FLOW_GAP_CM  # the diagram's content box, in cm
    height = content + 1.3 + (0.8 if fig.get("title") else 0)
    f = ctx.figure(fig, height)
    bottom = 0.9 / height
    top = bottom + content / height
    ax = f.add_axes([0.02, bottom, 0.96, top - bottom])
    ax.set_xlim(0, 1)
    ax.set_ylim(1, 0)
    ax.axis("off")
    from matplotlib.patches import FancyArrowPatch, Rectangle
    by = {n["id"]: n for n in nodes}
    for n in nodes:
        side = not n["id"].startswith("n")
        ax.add_patch(Rectangle((n["x"], n["y"]), n["w"], n["h"], fill=True, facecolor="#f2f2f2" if side else "white",
                               edgecolor="black", linewidth=0.9))
        lines = n["text"].split("\n")
        body = "\n".join(textwrap.fill(s, 30 if n["w"] > 0.35 else 24) for s in lines)
        ax.text(n["x"] + n["w"] / 2, n["y"] + n["h"] / 2, _esc(body), ha="center", va="center", fontsize=ctx.size)
    for e in edges:
        a, b = by[e["from"]], by[e["to"]]
        if "from_side" in e:  # exclusion: from the middle of the gap under `from`, to the left edge of the side box
            ymid = b["y"] + b["h"] / 2
            xs = a["x"] + a["w"] / 2
            ax.plot([xs, xs], [a["y"] + a["h"], ymid], color="black", lw=0.9)
            p = FancyArrowPatch((xs, ymid), (b["x"], ymid), arrowstyle="-|>", mutation_scale=8, color="black", lw=0.9,
                                shrinkA=0, shrinkB=0)
        else:
            xs = a["x"] + a["w"] / 2
            p = FancyArrowPatch((xs, a["y"] + a["h"]), (b["x"] + b["w"] / 2, b["y"]), arrowstyle="-|>",
                                mutation_scale=8, color="black", lw=0.9, shrinkA=0, shrinkB=0)
        ax.add_patch(p)
    if fig.get("title"):
        f.text(0.01, 1 - 0.3 / height, _esc(fig["title"]), ha="left", va="top", fontsize=ctx.size + 1, fontweight="bold")
    _source_note(ctx, f, fig.get("source"))
    return f


# ---------------------------------------------------------------- figure builders (data + drawing)

def build_forest(ctx: Ctx, fig: dict, by_id: dict, lang: str, **_):
    rows = _rows(fig, by_id, lang, need_ci=True)
    f = _draw_forest(ctx, fig, rows)
    log = bool(fig.get("log_scale"))
    null = fig.get("null", 1)
    data = {"values": [{k: r[k] for k in ("label", "ref", "est", "lo", "hi", "text")} for r in rows],
            "chart": {"kind": "forest", "log": log, "null": null, "x_label": fig.get("x_label", ""),
                      "rows": [{k: r[k] for k in ("label", "est", "lo", "hi")} for r in rows]}}
    return f, fig.get("source", ""), data


def build_rates(ctx: Ctx, fig: dict, by_id: dict, lang: str, **_):
    rows = _rows(fig, by_id, lang, need_ci=False)
    f = _draw_rates(ctx, fig, rows)
    data = {"values": [{k: r[k] for k in ("label", "ref", "est", "lo", "hi", "text")} for r in rows],
            "chart": {"kind": "bar", "unit": fig.get("unit", ""), "categories": [r["label"] for r in rows],
                      "series": [{"name": fig.get("title") or fig.get("unit") or "value",
                                  "values": [r["est"] for r in rows]}],
                      "labels": [r["text"] for r in rows]}}
    return f, fig.get("source", ""), data


def build_km(ctx: Ctx, fig: dict, project: Path, lang: str, **_):
    fid = fig["id"]
    groups, sha, rel = _read_km(project, fig)
    allt = [t for g in groups.values() for t, _e in g]
    if not allt:
        raise FigureError(f"{fid}: no usable rows in {rel}")
    max_time = fig.get("max_time", max(allt))
    if not isinstance(max_time, (int, float)) or max_time <= 0:
        raise FigureError(f"{fid}: 'max_time' must be a positive number")
    max_time = _clean_t(max_time)
    times = fig.get("at_risk")
    if times is None:
        times = [_clean_t(round(max_time * i / 4, 1)) for i in range(5)]
    if not (isinstance(times, list) and times and all(isinstance(t, (int, float)) for t in times)):
        raise FigureError(f"{fid}: 'at_risk' must be a list of times")
    series, rows, vals = [], [], []
    for g, obs in groups.items():
        pts = km_curve(obs, max_time)
        series.append({"name": g, "points": pts})
        clipped = [min(t, max_time) for t, _e in obs]
        rows.append({"name": g, "n": [sum(1 for c in clipped if c >= t) for t in times]})
        vals.append({"label": g, "n": len(obs), "events": sum(1 for t, e in obs if e and t <= max_time),
                     "derivation": f"product-limit estimate from {rel}"})
    unit = fig.get("time_unit") or _lang_text(lang, "ngày", "days")
    labels = {"x": fig.get("x_label") or _lang_text(lang, f"Thời gian ({unit})", f"Time ({unit})"),
              "y": fig.get("y_label") or _lang_text(lang, "Xác suất không có biến cố", "Event-free probability")}
    note = _lang_text(lang, f"Vẽ lại từ {rel}", f"Redrawn from {rel}")
    at_risk = {"times": times, "rows": rows}
    f = _draw_km(ctx, fig, series, groups, at_risk, max_time, labels, note)
    data = {"values": vals, "data_file": rel, "data_sha256": sha,
            "chart": {"kind": "km", "time_unit": unit, "x_label": labels["x"], "y_label": labels["y"],
                      "series": series, "at_risk": at_risk}}
    return f, note, data


def _n_of(fid: str, by_id: dict, expr, lang: str) -> tuple:
    if not isinstance(expr, str) or not derived.RID.search(expr):
        raise FigureError(f"{fid}: 'n' must be a ledger id (R-A0-001.n) or a formula over ledger ids, got {expr!r}")
    try:
        v = derived.evaluate(expr, by_id)
    except (KeyError, ValueError) as e:
        raise FigureError(f"{fid}: n = {expr!r}: {e.args[0]}") from e
    return float(v), numfmt.fmt(float(v), 0, lang)


def build_flow(ctx: Ctx, fig: dict, by_id: dict, lang: str, **_):
    fid = fig["id"]
    boxes, excl = fig.get("boxes"), fig.get("exclusions") or []
    if not isinstance(boxes, list) or not boxes:
        raise FigureError(f"{fid}: 'boxes' must be a non-empty list")
    if not isinstance(excl, list):
        raise FigureError(f"{fid}: 'exclusions' must be a list")
    n_box = len(boxes)
    content = n_box * FLOW_BOX_CM + (n_box - 1) * FLOW_GAP_CM
    h = FLOW_BOX_CM / content
    step = (FLOW_BOX_CM + FLOW_GAP_CM) / content
    mx, mw = (0.08, 0.46) if excl else (0.3, 0.4)
    nodes, edges, values = [], [], []

    def make(prefix: str, i: int, item, x: float, y: float, w: float):
        if not isinstance(item, dict) or not isinstance(item.get("text"), str):
            raise FigureError(f"{fid}: every box needs 'text'")
        nid = f"{prefix}{i + 1}"
        text = item["text"]
        if "n" in item:
            est, shown = _n_of(fid, by_id, item["n"], lang)
            text += f"\nn = {shown}"
            values.append({"label": item["text"], "ref": item["n"], "est": est, "text": f"n = {shown}"})
        nodes.append({"id": nid, "text": text, "x": round(x, 4), "y": round(y, 4), "w": w, "h": round(h, 4)})
        return nid

    for i, b in enumerate(boxes):
        make("n", i, b, mx, i * step, mw)
        if i:
            edges.append({"from": f"n{i}", "to": f"n{i + 1}"})
    for k, x in enumerate(excl):
        after = x.get("after", k + 1) if isinstance(x, dict) else k + 1
        if not isinstance(after, int) or not 1 <= after < n_box:
            raise FigureError(f"{fid}: exclusion {k + 1}: 'after' must be a box number from 1 to {n_box - 1}")
        y = after * step - (step - h) / 2 - h / 2
        make("x", k, x, 0.66, max(0.0, y), 0.32)
        edges.append({"from": f"n{after}", "to": f"x{k + 1}", "from_side": 2, "to_side": 1})
    f = _draw_flow(ctx, fig, nodes, edges)
    return f, fig.get("source", ""), {"values": values,
                                       "chart": {"kind": "diagram", "nodes": nodes, "edges": edges}}


BUILDERS = {"forest": build_forest, "rates": build_rates, "km": build_km, "flow": build_flow}


# ---------------------------------------------------------------- main

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Draw figures from 07_present/figures/figures.json (ledger values only).")
    ap.add_argument("project")
    ap.add_argument("--only", default="", help="comma-separated figure ids")
    ap.add_argument("--dpi", type=int, default=300)
    args = ap.parse_args(argv)
    project = Path(args.project)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import logging
        import matplotlib.pyplot as plt
        logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
    except ImportError:
        print("figures.py needs matplotlib: python -m pip install matplotlib", file=sys.stderr)
        return 2
    try:
        return _run(project, args, plt, matplotlib)
    except FigureError as e:
        print(f"figures.py: {e}", file=sys.stderr)
        return 2


def _run(project: Path, args, plt, matplotlib) -> int:
    spec_path = project / SPEC_REL
    if not project.is_dir():
        raise FigureError(f"project folder not found: {project}")
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8-sig"))
    except OSError as e:
        raise FigureError(f"cannot read {SPEC_REL}: {e}") from e
    except ValueError as e:
        raise FigureError(f"{SPEC_REL} is not valid JSON: {e}") from e
    figs = spec.get("figures") if isinstance(spec, dict) else None
    if not isinstance(figs, list) or not figs:
        raise FigureError(f"{SPEC_REL}: 'figures' must be a non-empty list")
    seen = set()
    for fig in figs:
        fid = fig.get("id") if isinstance(fig, dict) else None
        if not isinstance(fid, str) or not ID_OK.match(fid):
            raise FigureError(f"{SPEC_REL}: every figure needs an 'id' made of letters, digits, - and _")
        if fid in seen:
            raise FigureError(f"{SPEC_REL}: duplicate figure id {fid}")
        seen.add(fid)
        if fig.get("type") not in TYPES:
            raise FigureError(f"{fid}: unknown type {fig.get('type')!r} (allowed: {', '.join(TYPES)})")
    only = [s.strip() for s in args.only.split(",") if s.strip()]
    unknown = [s for s in only if s not in seen]
    if unknown:
        raise FigureError(f"--only: no such figure id {', '.join(unknown)} (in spec: {', '.join(sorted(seen))})")
    if args.dpi < 30:
        raise FigureError("--dpi must be at least 30")
    style = spec.get("style") if isinstance(spec.get("style"), dict) else {}
    lang = projectcfg.output_lang(project)
    ctx_style = style
    rc = matplotlib.rcParams
    rc["svg.fonttype"] = "none"
    rc["pdf.fonttype"] = 42
    rc["svg.hashsalt"] = "clinical-research-orchestra"
    family = str(ctx_style.get("font", "Arial"))
    rc["font.family"] = "sans-serif"
    rc["font.sans-serif"] = [family, "DejaVu Sans"]
    rc["font.size"] = float(ctx_style.get("font_size", 9))
    rc["axes.unicode_minus"] = False
    ctx = Ctx(plt, ctx_style, lang, args.dpi)
    by_id = None
    outdir = project / OUT_REL
    outdir.mkdir(parents=True, exist_ok=True)
    for fig in figs:
        fid = fig["id"]
        if only and fid not in only:
            continue
        if fig["type"] != "km" and by_id is None:
            try:
                by_id = derived.ledger_by_id(project)
            except (OSError, ValueError) as e:
                raise FigureError(f"{fid}: cannot read the results ledger: {e}") from e
        f, source, data = BUILDERS[fig["type"]](ctx, fig, by_id=by_id, lang=lang, project=project)
        _save(ctx, f, outdir, fid)
        out = {"id": fid, "type": fig["type"], "source": source, "values": data["values"]}
        for k in ("data_file", "data_sha256"):
            if k in data:
                out[k] = data[k]
        out["chart"] = data["chart"]
        (outdir / f"{fid}.data.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{fid} {fig['type']} → {OUT_REL}/{fid}.{{svg,pdf,png}}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
