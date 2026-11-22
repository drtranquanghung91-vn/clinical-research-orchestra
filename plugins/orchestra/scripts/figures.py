#!/usr/bin/env python3
"""Draw the figures of a project from 07_present/figures/figures.json.

  python figures.py <project> [--only F1,F2] [--dpi 300] [--profile document|poster]

Types: forest (optional pooled diamond and prediction-interval bar), km (Kaplan-Meier from the de-identified CSV), rates, flow,
prisma (PRISMA 2020 flow from ledger ids), rob (risk-of-bias traffic light from 04_data/sr/rob.csv). Every plotted estimate comes
from the results ledger by id; nothing is typed. Writes F<n>.svg, .pdf, .png and F<n>.data.json (every number
drawn plus the native-chart series slides use) into 07_present/figures/. --profile poster writes
F<n>.poster.{svg,pdf,png} at poster_width_cm / font_pt instead (no data.json). Format: references/presenting/figures-spec.md.
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
TYPES = ("forest", "km", "rates", "flow", "prisma", "rob")
ROB_REL = "04_data/sr/rob.csv"
ROB_STYLE = {"low": ("#4f9a4f", "+"), "some concerns": ("#e6b800", "−"), "moderate": ("#e6b800", "−"),
             "high": ("#c0504d", "×"), "serious": ("#c0504d", "×"), "critical": ("#7a1f1f", "!"),
             "no information": ("#bfbfbf", "?")}
ROB_NAME = {"en": {k: k for k in ROB_STYLE},
            "vi": {"low": "thấp", "some concerns": "một số lo ngại", "moderate": "trung bình", "high": "cao",
                   "serious": "nghiêm trọng", "critical": "rất nghiêm trọng", "no information": "không có thông tin"}}
PRISMA_REQUIRED = ("identified", "duplicates", "screened", "excluded", "sought", "not_retrieved", "assessed",
                   "reports_excluded", "studies")
PROFILES = ("document", "poster")
POSTER_WIDTH_CM, POSTER_FONT_PT = 30.0, 24.0
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
#
# Layout rule: every distance is a multiple of the font size ("em", 1 em = font_pt in cm) or a width measured
# from the rendered text, never a fixed number of cm. Text columns are measured with matplotlib's renderer,
# the plot area gets what is left of the figure width, and the figure only grows (never clips) when the text
# needs more room than the requested width gives.

PT_CM = 2.54 / 72
MIN_AXES_EM = 10.0  # narrowest plot area, in em


class Ctx:
    def __init__(self, plt, style: dict, lang: str, dpi: int, size: float | None = None, width_cm: float | None = None):
        self.plt, self.lang, self.dpi = plt, lang, dpi
        self.colors = style.get("colors") if isinstance(style.get("colors"), dict) else {}
        self.font = str(style.get("font", "Arial"))
        self.size = float(size if size is not None else style.get("font_size", 9))
        self.width_cm = float(width_cm if width_cm is not None else style.get("width_cm", 16))
        self.em = self.size * PT_CM  # cm
        self.s = self.size / 9.0  # scale for line widths, markers, tick lengths
        self._scratch = None
        self._cache: dict = {}
        self.labels: list[str] = []  # group/series labels this figure looked up a colour for

    def color(self, key: str, i: int = 0, label: bool = True) -> str:
        if label and key not in self.labels:
            self.labels.append(key)
        return self.colors.get(key) or PALETTE[i % len(PALETTE)]

    def colour_warning(self, fid: str) -> str | None:
        """Warn when a style.colors key matches none of this figure's labels while some label has no colour
        (a likely key typo, e.g. '<7' for '<7%'); figures without group labels (forest, flow) never warn."""
        uncoloured = [lb for lb in self.labels if lb not in self.colors]
        unused = [k for k in self.colors if k not in self.labels and k != "forest"]
        if not (uncoloured and unused):
            return None
        q = ", ".join
        return (f"{fid}: style.colors key(s) {q(repr(k) for k in unused)} match no group label of this figure "
                f"(labels: {q(repr(lb) for lb in self.labels)}); {q(repr(lb) for lb in uncoloured)} take the default palette")

    def figure(self, height_cm: float, width_cm: float | None = None):
        self.plt.rcParams["font.size"] = self.size
        width = (width_cm if width_cm is not None else self.width_cm) / 2.54
        return self.plt.figure(figsize=(width, height_cm / 2.54))

    def fmt_axis(self, v: float) -> str:
        s = f"{v:g}"
        return s.replace(".", ",") if self.lang == "vi" else s

    # -- measuring text with the renderer
    def measure(self, text: str, size: float | None = None, bold: bool = False) -> tuple:
        """(width_cm, height_cm) of `text` as rendered, with a 3 % margin for dpi/hinting differences."""
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        from matplotlib.figure import Figure
        key = (text, size or self.size, bold)
        if key in self._cache:
            return self._cache[key]
        if self._scratch is None:
            fg = Figure(figsize=(4, 4), dpi=100)
            FigureCanvasAgg(fg)
            self._scratch = fg
        fg = self._scratch
        t = fg.text(0, 0, _esc(text), fontsize=size or self.size, fontweight="bold" if bold else "normal")
        bb = t.get_window_extent(fg.canvas.get_renderer())
        t.remove()
        k = 2.54 / fg.dpi
        self._cache[key] = (bb.width * k * 1.03, bb.height * k)
        return self._cache[key]

    def width(self, text: str, size: float | None = None, bold: bool = False) -> float:
        return self.measure(text, size, bold)[0]

    def wrap(self, text: str, max_cm: float, size: float | None = None, bold: bool = False) -> str:
        """Greedy word wrap so every line is at most `max_cm` wide as rendered (long words split by character)."""
        out = []
        for para in str(text).split("\n"):
            line = ""
            for word in para.split(" "):
                cand = f"{line} {word}" if line else word
                if not line or self.width(cand, size, bold) <= max_cm:
                    line = cand
                    continue
                out.append(line)
                line = word
            while len(line) > 1 and self.width(line, size, bold) > max_cm:
                k = len(line) - 1
                while k > 1 and self.width(line[:k], size, bold) > max_cm:
                    k -= 1
                out.append(line[:k])
                line = line[k:]
            out.append(line)
        return "\n".join(out)

    def lines_h(self, text: str, size: float | None = None) -> float:
        """Height in cm of a block of text lines at 1.3 line spacing."""
        return (str(text).count("\n") + 1) * (size or self.size) * PT_CM * 1.3


def _style_axes(ctx: Ctx, ax) -> None:
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=3 * ctx.s, width=0.6 * ctx.s, labelsize=ctx.size, pad=3.5 * ctx.s)
    for side in ("left", "bottom"):
        ax.spines[side].set_linewidth(0.6 * ctx.s)


def _note_size(ctx: Ctx) -> float:
    return ctx.size if ctx.size >= 18 else ctx.size * 0.85  # big (poster) text is never below the body size


def _title_size(ctx: Ctx) -> float:
    return ctx.size + ctx.size / 9


class Frame:
    """Vertical bookkeeping shared by every figure: title block on top, source note at the bottom."""

    def __init__(self, ctx: Ctx, fig: dict, source: str | None, width: float):
        self.ctx, self.width = ctx, width
        em = ctx.em
        self.margin = 0.8 * em
        text_w = max(width - 2 * self.margin, 4 * em)
        title = fig.get("title")
        self.title = ctx.wrap(title, text_w, _title_size(ctx), True) if title else ""
        self.title_h = (ctx.lines_h(self.title, _title_size(ctx)) + 0.6 * em) if title else 0.0
        self.note = ctx.wrap(source, text_w, _note_size(ctx)) if source else ""
        self.note_h = (ctx.lines_h(self.note, _note_size(ctx)) + 0.4 * em) if source else 0.0
        self.top = 0.6 * em + self.title_h  # cm above the plot area
        self.bottom0 = self.note_h + 0.2 * em  # cm reserved at the bottom for the source note

    def finish(self, f, height: float) -> None:
        ctx = self.ctx
        if self.title:
            f.text(self.margin / self.width, 1 - 0.3 * ctx.em / height, _esc(self.title), ha="left", va="top",
                   fontsize=_title_size(ctx), fontweight="bold", linespacing=1.15)
        if self.note:
            f.text(self.margin / self.width, 0.2 * ctx.em / height, _esc(self.note), ha="left", va="bottom",
                   fontsize=_note_size(ctx), color=GREY, linespacing=1.15)


def _xlabel_block(ctx: Ctx, label: str, axes_w: float) -> tuple:
    """(wrapped label, height in cm of tick labels + axis label below the axis)."""
    lab = ctx.wrap(label, axes_w, ctx.size) if label else ""
    h = ctx.em * (0.35 + 0.4 + 1.3) + (ctx.lines_h(lab) + 0.5 * ctx.em if lab else 0.0)
    return lab, h


def _save(ctx: Ctx, f, outdir: Path, fid: str, suffix: str = "") -> None:
    for ext in ("svg", "pdf", "png"):
        kw = {"dpi": ctx.dpi} if ext == "png" else {}
        if ext == "svg":
            kw["metadata"] = {"Date": None}
        elif ext == "pdf":
            kw["metadata"] = {"CreationDate": None, "Creator": "figures.py"}
        out = outdir / f"{fid}{suffix}.{ext}"
        f.savefig(out, format=ext, **kw)
        if ext == "svg":  # matplotlib writes SVG in text mode: CRLF on Windows; keep LF on every OS
            out.write_bytes(out.read_bytes().replace(b"\r\n", b"\n"))
    ctx.plt.close(f)


def _draw_forest(ctx: Ctx, fig: dict, rows: list[dict], pooled: dict | None = None):
    from matplotlib.patches import Polygon
    from matplotlib.transforms import blended_transform_factory
    every = rows + ([pooled] if pooled else [])
    n, em, s = len(every), ctx.em, ctx.s
    row_h = 2.6 * em
    hdr = _lang_text(ctx.lang, "Ước lượng (KTC 95%)", "Estimate (95% CI)")
    left = 0.8 * em + max(ctx.width(r["label"]) for r in every) + 0.5 * em
    right = 1.0 * em + max([ctx.width(hdr, bold=True)] + [ctx.width(r["text"]) for r in every]) + 0.8 * em
    width = max(ctx.width_cm, left + right + MIN_AXES_EM * em)
    axes_w = width - left - right
    fr = Frame(ctx, fig, fig.get("source"), width)
    xlab, xblock = _xlabel_block(ctx, fig.get("x_label", ""), axes_w)
    hdr_h = 1.6 * em
    axes_h = n * row_h
    height = fr.top + hdr_h + axes_h + xblock + fr.bottom0
    f = ctx.figure(height, width)
    ax = f.add_axes([left / width, (fr.bottom0 + xblock) / height, axes_w / width, axes_h / height])
    null = fig.get("null", 1)
    ys = list(range(n, 0, -1))
    col = ctx.color("forest", 0, label=False)
    for y, r in zip(ys, rows):
        ax.plot([r["lo"], r["hi"]], [y, y], color=col, lw=1.1 * s, solid_capstyle="butt")
        ax.plot([r["est"]], [y], marker="s", ms=5.5 * s, color=col, mfc=col if r["filled"] else "white", mew=1.1 * s)
    lows, highs = [r["lo"] for r in every] + [null], [r["hi"] for r in every] + [null]
    if pooled:
        if pooled.get("pi"):
            ax.plot(list(pooled["pi"]), [1, 1], color=GREY, lw=2.0 * s, solid_capstyle="butt", zorder=1)
            lows.append(pooled["pi"][0])
            highs.append(pooled["pi"][1])
        h = 0.3
        ax.add_patch(Polygon([(pooled["lo"], 1), (pooled["est"], 1 + h), (pooled["hi"], 1), (pooled["est"], 1 - h)],
                             closed=True, facecolor=col, edgecolor=col, zorder=2))
        ax.axhline(1.5, color=GREY, lw=0.6 * s)
    ax.axvline(null, color=GREY, lw=0.8 * s, ls="--")
    if fig.get("log_scale"):
        ax.set_xscale("log")
        lo, hi = min(lows), max(highs)
        ticks = [t for t in (0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50) if lo / 1.6 <= t <= hi * 1.6]
        if ticks:
            ax.set_xticks(ticks)
        ax.set_xticklabels([ctx.fmt_axis(t) for t in ticks])
        ax.minorticks_off()
    elif pooled:
        pad = 0.05 * (max(highs) - min(lows) or 1)
        ax.set_xlim(min(lows) - pad, max(highs) + pad)
    ax.set_yticks(ys)
    ax.set_yticklabels([_esc(r["label"]) for r in every])
    ax.set_ylim(0.5, n + 0.5)
    ax.set_xlabel(_esc(xlab), fontsize=ctx.size, labelpad=0.4 * ctx.size)
    _style_axes(ctx, ax)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0, pad=0.5 * ctx.size)
    tr = blended_transform_factory(f.transFigure, ax.transData)
    x_text = (left + axes_w + 1.0 * em) / width
    ax.text(x_text, n + 0.5, hdr, transform=tr, ha="left", va="bottom", fontsize=ctx.size, fontweight="bold",
            clip_on=False)
    for y, r in zip(ys, every):
        ax.text(x_text, y, _esc(r["text"]), transform=tr, ha="left", va="center", fontsize=ctx.size, clip_on=False,
                fontweight="bold" if r is pooled else "normal")
    fr.finish(f, height)
    return f


def _draw_rates(ctx: Ctx, fig: dict, rows: list[dict]):
    from matplotlib.transforms import blended_transform_factory
    n, em, s = len(rows), ctx.em, ctx.s
    row_h = 2.6 * em
    left = 0.8 * em + max(ctx.width(r["label"]) for r in rows) + 0.5 * em
    right = 0.8 * em + max(ctx.width(r["text"]) for r in rows) + 0.8 * em
    width = max(ctx.width_cm, left + right + MIN_AXES_EM * em)
    axes_w = width - left - right
    fr = Frame(ctx, fig, fig.get("source"), width)
    xlab, xblock = _xlabel_block(ctx, fig.get("unit", ""), axes_w)
    axes_h = n * row_h
    height = fr.top + 0.4 * em + axes_h + xblock + fr.bottom0
    f = ctx.figure(height, width)
    ax = f.add_axes([left / width, (fr.bottom0 + xblock) / height, axes_w / width, axes_h / height])
    ys = list(range(n, 0, -1))
    xmax = max((r["hi"] if r["hi"] is not None else r["est"]) for r in rows)
    for i, (y, r) in enumerate(zip(ys, rows)):
        col = ctx.color(r["label"], i)
        ax.barh(y, r["est"], height=0.55, color=col if r["filled"] else "white", edgecolor=col, linewidth=1.1 * s)
        if r["lo"] is not None:
            ax.plot([r["lo"], r["hi"]], [y, y], color="black", lw=1.0 * s)
            for x in (r["lo"], r["hi"]):
                ax.plot([x, x], [y - 0.14, y + 0.14], color="black", lw=1.0 * s)
    ax.set_xlim(0, xmax * 1.08)
    ax.set_ylim(0.4, n + 0.6)
    ax.set_yticks(ys)
    ax.set_yticklabels([_esc(r["label"]) for r in rows])
    ax.set_xlabel(_esc(xlab), fontsize=ctx.size, labelpad=0.4 * ctx.size)
    ax.xaxis.set_major_formatter(ctx.plt.FuncFormatter(lambda v, _p: ctx.fmt_axis(v)))
    _style_axes(ctx, ax)
    tr = blended_transform_factory(f.transFigure, ax.transData)
    x_text = (left + axes_w + 0.8 * em) / width
    for y, r in zip(ys, rows):
        ax.text(x_text, y, _esc(r["text"]), transform=tr, ha="left", va="center", fontsize=ctx.size, clip_on=False)
    fr.finish(f, height)
    return f


def _draw_km(ctx: Ctx, fig: dict, series: list[dict], groups: dict, at_risk: dict, max_time, labels: dict, note: str):
    k, em, s = len(series), ctx.em, ctx.s
    names = [r["name"] for r in at_risk["rows"]]
    nums = [str(v) for r in at_risk["rows"] for v in r["n"]]
    num_w = max(ctx.width(x, ctx.size) for x in nums)
    tick_w = max(ctx.width(ctx.fmt_axis(v)) for v in (0.0, 0.5, 1.0))
    xt_w = max(ctx.width(ctx.fmt_axis(t)) for t in at_risk["times"])
    ylab_w, ylab_h = ctx.measure(labels["y"])
    table_pad = num_w / 2 + 1.0 * em  # names sit left of the first number, which is centred on x = 0
    names_w = max(ctx.width(nm) for nm in names) + table_pad
    ylabel_col = ylab_h + 0.6 * em + tick_w + 0.6 * em  # rotated y label + gap + tick labels + tick
    left = 0.6 * em + max(ylabel_col, names_w)
    right = max(0.8 * em, num_w / 2 + 0.3 * em, xt_w / 2 + 0.3 * em)
    width = max(ctx.width_cm, left + right + MIN_AXES_EM * em)
    axes_w = width - left - right
    fr = Frame(ctx, fig, note, width)
    xlab, xblock = _xlabel_block(ctx, labels["x"], axes_w)
    row = 2.0 * em
    tbl_h = row * (k + 0.8)
    hdr_h = 1.5 * em
    gap = xblock + hdr_h + 0.5 * em  # x tick labels + x label + "number at risk" header, between plot and table
    axes_h = max(0.42 * axes_w, ylab_w + 2 * em, 14 * em, (k + 1) * 1.8 * em)
    height = fr.top + axes_h + gap + tbl_h + fr.bottom0
    f = ctx.figure(height, width)
    tbl_b = fr.bottom0
    ax_b = tbl_b + tbl_h + gap
    ax = f.add_axes([left / width, ax_b / height, axes_w / width, axes_h / height])
    for i, sr in enumerate(series):
        col = ctx.color(sr["name"], i)
        xs, ys = [p[0] for p in sr["points"]], [p[1] for p in sr["points"]]
        ax.plot(xs, ys, color=col, lw=1.4 * s, label=_esc(sr["name"]), solid_joinstyle="miter")
        cens = [(t, _surv_at(sr["points"], t)) for t, e in groups[sr["name"]] if not e and t < max_time]
        if cens:
            ax.plot([c[0] for c in cens], [c[1] for c in cens], ls="none", marker="|", ms=4 * s, mew=0.7 * s, color=col)
    ax.set_xlim(0, max_time)
    ax.set_ylim(0, 1.02)
    ax.set_xticks(at_risk["times"])
    ax.yaxis.set_major_formatter(ctx.plt.FuncFormatter(lambda v, _p: ctx.fmt_axis(round(v, 1))))
    ax.set_xlabel(_esc(xlab), fontsize=ctx.size, labelpad=0.4 * ctx.size)
    ax.set_ylabel(_esc(labels["y"]), fontsize=ctx.size, labelpad=0.4 * ctx.size)
    _style_axes(ctx, ax)
    ax.legend(frameon=False, loc="lower left", fontsize=ctx.size)
    tb = f.add_axes([left / width, tbl_b / height, axes_w / width, tbl_h / height], sharex=ax)
    tb.set_ylim(-0.6, k - 0.4)
    tb.set_yticks(range(k))
    tb.set_yticklabels([_esc(r["name"]) for r in reversed(at_risk["rows"])])
    for tick, r in zip(tb.get_yticklabels(), reversed(at_risk["rows"])):
        tick.set_color(ctx.color(r["name"], [x["name"] for x in series].index(r["name"])))
    for spine in tb.spines.values():
        spine.set_visible(False)
    tb.tick_params(axis="x", length=0, labelbottom=False)
    tb.tick_params(axis="y", length=0, pad=table_pad / PT_CM, labelsize=ctx.size)
    for j, r in enumerate(reversed(at_risk["rows"])):
        for t, nn in zip(at_risk["times"], r["n"]):
            tb.text(t, j, str(nn), ha="center", va="center", fontsize=ctx.size)
    f.text(left / width, (tbl_b + tbl_h + 0.3 * em) / height, _lang_text(ctx.lang, "Số người còn trong theo dõi",
           "Number at risk"), ha="left", va="bottom", fontsize=ctx.size, fontweight="bold")
    fr.finish(f, height)
    return f


def _flow_geometry(ctx: Ctx, texts: list, widths: list, width: float) -> tuple:
    """Wrap every box text to its box width; return (uniform box height cm, gap cm)."""
    em = ctx.em
    wrapped = [ctx.wrap(t, w * 0.96 * width - 1.2 * em) for t, w in zip(texts, widths)]
    need = max(ctx.lines_h(t) for t in wrapped) + 1.0 * em
    return max(FLOW_BOX_CM * ctx.s, need), max(FLOW_GAP_CM * ctx.s, 1.6 * em)


def _draw_flow(ctx: Ctx, fig: dict, nodes: list[dict], edges: list[dict], content: float, width: float):
    em, s = ctx.em, ctx.s
    fr = Frame(ctx, fig, fig.get("source"), width)
    height = fr.top + content + 0.4 * em + fr.bottom0
    f = ctx.figure(height, width)
    bottom = fr.bottom0 + 0.2 * em
    ax = f.add_axes([0.02, bottom / height, 0.96, content / height])
    ax.set_xlim(0, 1)
    ax.set_ylim(1, 0)
    ax.axis("off")
    from matplotlib.patches import FancyArrowPatch, Rectangle
    by = {n["id"]: n for n in nodes}
    for n in nodes:
        side = not n["id"].startswith("n")
        ax.add_patch(Rectangle((n["x"], n["y"]), n["w"], n["h"], fill=True, facecolor="#f2f2f2" if side else "white",
                               edgecolor="black", linewidth=0.9 * s))
        body = ctx.wrap(n["text"], n["w"] * 0.96 * width - 1.2 * em)
        ax.text(n["x"] + n["w"] / 2, n["y"] + n["h"] / 2, _esc(body), ha="center", va="center", fontsize=ctx.size,
                linespacing=1.15)
    for e in edges:
        a, b = by[e["from"]], by[e["to"]]
        if "from_side" in e:  # exclusion: from the middle of the gap under `from`, to the left edge of the side box
            ymid = b["y"] + b["h"] / 2
            xs = a["x"] + a["w"] / 2
            ax.plot([xs, xs], [a["y"] + a["h"], ymid], color="black", lw=0.9 * s)
            p = FancyArrowPatch((xs, ymid), (b["x"], ymid), arrowstyle="-|>", mutation_scale=8 * s, color="black",
                                lw=0.9 * s, shrinkA=0, shrinkB=0)
        else:
            xs = a["x"] + a["w"] / 2
            p = FancyArrowPatch((xs, a["y"] + a["h"]), (b["x"] + b["w"] / 2, b["y"]), arrowstyle="-|>",
                                mutation_scale=8 * s, color="black", lw=0.9 * s, shrinkA=0, shrinkB=0)
        ax.add_patch(p)
    fr.finish(f, height)
    return f


# ---------------------------------------------------------------- figure builders (data + drawing)

def build_forest(ctx: Ctx, fig: dict, by_id: dict, lang: str, **_):
    fid = fig["id"]
    rows = _rows(fig, by_id, lang, need_ci=True)
    pooled = None
    if fig.get("pooled"):
        rec = _record(fid, by_id, fig["pooled"], need_ci=True)
        pooled = {"label": fig.get("pooled_label") or _lang_text(lang, "Ước lượng gộp", "Pooled estimate"),
                  "ref": fig["pooled"], "est": _num(rec["value"]), "lo": _num(rec["ci"][0]), "hi": _num(rec["ci"][1]),
                  "text": _est_text(rec, lang), "filled": True, "pi": None}
        if fig.get("prediction"):
            prec = _record(fid, by_id, fig["prediction"], need_ci=True)
            pooled["pi"] = (_num(prec["ci"][0]), _num(prec["ci"][1]))
            pooled["text"] += _lang_text(lang, "; KDB 95% ", "; 95% PI ") + numfmt.render(prec, "ci", lang)
    elif fig.get("prediction"):
        raise FigureError(f"{fid}: 'prediction' needs 'pooled'")
    f = _draw_forest(ctx, fig, rows, pooled)
    log = bool(fig.get("log_scale"))
    null = fig.get("null", 1)
    every = rows + ([pooled] if pooled else [])
    data = {"values": [{k: r[k] for k in ("label", "ref", "est", "lo", "hi", "text")} for r in every],
            "chart": {"kind": "forest", "log": log, "null": null, "x_label": fig.get("x_label", ""),
                      "rows": [{k: r[k] for k in ("label", "est", "lo", "hi")} for r in rows]}}
    if pooled:
        data["chart"]["pooled"] = {k: pooled[k] for k in ("label", "est", "lo", "hi")}
        data["chart"]["prediction"] = list(pooled["pi"]) if pooled["pi"] else None
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
    bad_t = [t for t in times if t < 0 or t > max_time]
    if bad_t:
        raise FigureError(f"{fid}: 'at_risk' times must lie between 0 and max_time ({max_time}); "
                          f"got {', '.join(str(t) for t in bad_t)}")
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
    mx, mw = (0.08, 0.46) if excl else (0.3, 0.4)
    width = ctx.width_cm
    texts = [b.get("text", "") if isinstance(b, dict) else "" for b in boxes] + \
        [x.get("text", "") if isinstance(x, dict) else "" for x in excl]
    texts = [t + "\nn = 0" if isinstance(t, str) else "" for t in texts]  # room for the "n = ..." line
    ws = [mw] * n_box + [0.32] * len(excl)
    box_cm, gap_cm = _flow_geometry(ctx, [t if isinstance(t, str) else "" for t in texts], ws, width)
    content = n_box * box_cm + (n_box - 1) * gap_cm
    h = box_cm / content
    step = (box_cm + gap_cm) / content
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
    f = _draw_flow(ctx, fig, nodes, edges, content, width)
    return f, fig.get("source", ""), {"values": values,
                                       "chart": {"kind": "diagram", "nodes": nodes, "edges": edges}}


def _prisma_ref(fid: str, item: dict, key: str) -> str:
    v = item.get(key)
    terms = [t.strip() for t in v.split("+")] if isinstance(v, str) else []
    if not terms or not all(re.fullmatch(r"R-A\d+-\d{3}(\.(value|n))?", t) for t in terms):
        raise FigureError(f"{fid}: prisma '{key}' must be a ledger id such as R-A0-001, or ids added with + "
                          "(typed numbers are not allowed)")
    return " + ".join(t if "." in t else f"{t}.value" for t in terms)


def build_prisma(ctx: Ctx, fig: dict, by_id: dict, lang: str, **_):
    fid = fig["id"]
    missing = [k for k in PRISMA_REQUIRED if k not in fig]
    if missing:
        raise FigureError(f"{fid}: prisma needs ledger ids for {', '.join(missing)}")
    t = lambda vi, en: _lang_text(lang, vi, en)  # noqa: E731
    extra: list[dict] = []

    def shown(item: dict, key: str, label: str) -> str:
        ref = _prisma_ref(fid, item, key)
        est, txt = _n_of(fid, by_id, ref, lang)
        extra.append({"label": label, "ref": ref, "est": est, "text": f"n = {txt}"})
        return txt

    ident = t("Bản ghi từ cơ sở dữ liệu", "Records identified from databases")
    if "registers" in fig:
        ident += "\n" + t("và sổ đăng ký", "and registers") + f" (n = {shown(fig, 'registers', 'registers')})"
    reasons = fig.get("reasons") or []
    if not isinstance(reasons, list):
        raise FigureError(f"{fid}: 'reasons' must be a list of {{text, n}}")
    excl = t("Báo cáo bị loại", "Reports excluded")
    for r in reasons:
        if not isinstance(r, dict) or not isinstance(r.get("text"), str):
            raise FigureError(f"{fid}: every reason needs 'text' and 'n'")
        excl += f"\n{r['text']} (n = {shown(r, 'n', r['text'])})"
    included = t("Nghiên cứu được đưa vào", "Studies included in review")
    if "reports" in fig:
        included += "\n" + t("Báo cáo của các nghiên cứu", "Reports of included studies") + \
            f" (n = {shown(fig, 'reports', 'reports')})"
    ref = lambda k: _prisma_ref(fid, fig, k)  # noqa: E731
    flow = {"id": fid, "title": fig.get("title"), "source": fig.get("source"),
            "boxes": [{"text": ident, "n": ref("identified")},
                      {"text": t("Bản ghi được sàng lọc", "Records screened"), "n": ref("screened")},
                      {"text": t("Báo cáo cần tìm toàn văn", "Reports sought for retrieval"), "n": ref("sought")},
                      {"text": t("Báo cáo được đánh giá tính phù hợp", "Reports assessed for eligibility"), "n": ref("assessed")},
                      {"text": included, "n": ref("studies")}],
            "exclusions": [{"text": t("Bản ghi trùng lặp bị loại", "Duplicate records removed"), "n": ref("duplicates"), "after": 1},
                           {"text": t("Bản ghi bị loại", "Records excluded"), "n": ref("excluded"), "after": 2},
                           {"text": t("Báo cáo không tìm được", "Reports not retrieved"), "n": ref("not_retrieved"), "after": 3},
                           {"text": excl, "n": ref("reports_excluded"), "after": 4}]}
    f, source, data = build_flow(ctx, flow, by_id, lang)
    ax = f.axes[0]
    nodes = {n["id"]: n for n in data["chart"]["nodes"]}
    stages = [(t("Nhận diện", "Identification"), "n1", "n1"), (t("Sàng lọc", "Screening"), "n2", "n4"),
              (t("Đưa vào", "Included"), "n5", "n5")]
    for label, a, b in stages:
        mid = (nodes[a]["y"] + nodes[b]["y"] + nodes[b]["h"]) / 2
        ax.text(0.035, mid, _esc(label), rotation=90, ha="center", va="center", fontsize=ctx.size, fontweight="bold")
    data["values"] += extra
    data["chart"]["stages"] = [{"label": lab, "from": a, "to": b} for lab, a, b in stages]
    return f, source, data


def _read_rob(project: Path, fig: dict) -> tuple[list, list, dict, str]:
    fid = fig["id"]
    for k in ("outcome", "tool"):
        if not isinstance(fig.get(k), str) or not fig[k].strip():
            raise FigureError(f"{fid}: rob needs '{k}'")
    try:
        raw = (project / ROB_REL).read_bytes()
    except OSError as e:
        raise FigureError(f"{fid}: cannot read {ROB_REL}: {e}") from e
    cells: dict[tuple, str] = {}
    for r in csv.DictReader(raw.decode("utf-8-sig").splitlines()):
        if (r.get("outcome") or "").strip() != fig["outcome"] or (r.get("tool") or "").strip() != fig["tool"]:
            continue
        j = (r.get("judgement") or "").strip().casefold()
        if j not in ROB_STYLE:
            raise FigureError(f"{fid}: judgement {j!r} is not one of {', '.join(ROB_STYLE)}")
        cells[((r.get("study_id") or "").strip(), (r.get("domain") or "").strip())] = j
    if not cells:
        raise FigureError(f"{fid}: no rows for outcome {fig['outcome']!r} and tool {fig['tool']!r} in {ROB_REL}")
    studies = sorted({st for st, _ in cells})
    doms = sorted({d for _, d in cells if d != "overall"}, key=lambda d: (int(d[1:]) if d[1:].isdigit() else 99, d))
    if any(d == "overall" for _, d in cells):
        doms.append("overall")
    return studies, doms, cells, hashlib.sha256(raw).hexdigest()


def _draw_rob(ctx: Ctx, fig: dict, studies: list, domains: list, cells: dict):
    from matplotlib.patches import Circle
    em, s = ctx.em, ctx.s
    heads = [_lang_text(ctx.lang, "Tổng thể", "Overall") if d == "overall" else d for d in domains]
    cell = 2.2 * em
    left = 0.8 * em + max(ctx.width(x) for x in studies) + 0.6 * em
    width = max(ctx.width_cm, left + cell * len(domains) + 1.0 * em)
    fr = Frame(ctx, fig, fig.get("source"), width)
    used = [j for j in ROB_STYLE if j in set(cells.values())]
    legend = ctx.wrap("   ".join(f"{ROB_STYLE[j][1]} {ROB_NAME[ctx.lang if ctx.lang in ROB_NAME else 'en'][j]}" for j in used),
                      width - 2 * fr.margin)
    legend_h = ctx.lines_h(legend) + 0.8 * em
    hdr_h, grid_h = 1.6 * em, len(studies) * cell
    height = fr.top + hdr_h + grid_h + legend_h + fr.bottom0
    f = ctx.figure(height, width)
    ax = f.add_axes([left / width, (fr.bottom0 + legend_h) / height, cell * len(domains) / width, grid_h / height])
    ax.set_xlim(0, len(domains))
    ax.set_ylim(len(studies), 0)
    ax.axis("off")
    for i, st in enumerate(studies):
        ax.text(-0.25, i + 0.5, _esc(st), ha="right", va="center", fontsize=ctx.size, clip_on=False)
        for j, d in enumerate(domains):
            colour, sym = ROB_STYLE.get(cells.get((st, d)), ("white", ""))
            ax.add_patch(Circle((j + 0.5, i + 0.5), 0.38, facecolor=colour, edgecolor="black", linewidth=0.6 * s))
            ax.text(j + 0.5, i + 0.5, sym, ha="center", va="center", fontsize=ctx.size, fontweight="bold")
    for j, h in enumerate(heads):
        ax.text(j + 0.5, -0.2, _esc(h), ha="center", va="bottom", fontsize=ctx.size, fontweight="bold", clip_on=False)
    f.text(fr.margin / width, (fr.bottom0 + legend_h - 0.3 * em) / height, _esc(legend), ha="left", va="top",
           fontsize=ctx.size, linespacing=1.2)
    fr.finish(f, height)
    return f


def build_rob(ctx: Ctx, fig: dict, project: Path, lang: str, **_):
    studies, domains, cells, sha = _read_rob(Path(project), fig)
    f = _draw_rob(ctx, fig, studies, domains, cells)
    values = [{"label": f"{st} {d}", "ref": ROB_REL, "text": cells[(st, d)]}
              for st in studies for d in domains if (st, d) in cells]
    return f, fig.get("source", ""), {"values": values, "data_file": ROB_REL, "data_sha256": sha,
                                       "chart": {"kind": "rob", "tool": fig["tool"], "studies": studies,
                                                 "domains": domains,
                                                 "cells": [[cells.get((st, d), "") for d in domains] for st in studies]}}


BUILDERS = {"forest": build_forest, "rates": build_rates, "km": build_km, "flow": build_flow, "prisma": build_prisma,
            "rob": build_rob}


def _num_key(fid: str, fig: dict, key: str, default: float) -> float:
    v = fig.get(key, default)
    if isinstance(v, bool) or not isinstance(v, (int, float)) or v <= 0:
        raise FigureError(f"{fid}: '{key}' must be a positive number")
    return float(v)


def _ctx_for(plt, style: dict, lang: str, dpi: int, fig: dict, profile: str) -> Ctx:
    """Font size and width for one figure. document: style font_size / width_cm (figure width_cm overrides);
    poster: figure font_pt (default 24) and poster_width_cm (default 30)."""
    fid = fig["id"]
    if profile == "poster":
        return Ctx(plt, style, lang, dpi, size=_num_key(fid, fig, "font_pt", POSTER_FONT_PT),
                   width_cm=_num_key(fid, fig, "poster_width_cm", POSTER_WIDTH_CM))
    return Ctx(plt, style, lang, dpi, width_cm=_num_key(fid, fig, "width_cm", float(style.get("width_cm", 16))))


def _configure(matplotlib, style: dict) -> None:
    rc = matplotlib.rcParams
    rc["svg.fonttype"] = "none"
    rc["pdf.fonttype"] = 42
    rc["svg.hashsalt"] = "clinical-research-orchestra"
    rc["font.family"] = "sans-serif"
    rc["font.sans-serif"] = [str(style.get("font", "Arial")), "DejaVu Sans"]
    rc["axes.unicode_minus"] = False


def render_figure(project: Path, fig: dict, *, width_cm: float, font_pt: float, lang: str | None = None,
                  style: dict | None = None, dpi: int = 100):
    """Draw one figure spec at an explicit width and font size and return (matplotlib figure, source, data)
    without saving. The caller closes the figure. Used by the tests and by anything that needs the geometry."""
    import logging
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
    project = Path(project)
    style = style or {}
    _configure(matplotlib, style)
    lang = lang or projectcfg.output_lang(project)
    ctx = Ctx(plt, style, lang, dpi, size=font_pt, width_cm=width_cm)
    by_id = None if fig["type"] in ("km", "rob") else derived.ledger_by_id(project)
    return BUILDERS[fig["type"]](ctx, fig, by_id=by_id, lang=lang, project=project)


def text_artists(f) -> list:
    """Every visible, non-empty text artist of a figure: free text, axes text, titles, axis labels, tick labels,
    legend entries."""
    out = []

    def add(t):
        if t.get_visible() and t.get_text().strip():
            out.append(t)

    for t in f.texts:
        add(t)
    for ax in f.axes:
        if not ax.axison:
            for t in ax.texts:
                add(t)
            continue
        for t in ax.texts:
            add(t)
        for t in (ax.title, ax.xaxis.label, ax.yaxis.label):
            add(t)
        for axis in (ax.xaxis, ax.yaxis):
            lo, hi = sorted(axis.get_view_interval())
            labels, locs = axis.get_majorticklabels(), axis.get_majorticklocs()
            for t, loc in zip(labels, locs):  # ticks outside the view are not drawn
                if lo - 1e-9 <= loc <= hi + 1e-9:
                    add(t)
        leg = ax.get_legend()
        if leg is not None:
            for t in leg.get_texts():
                add(t)
    return out


# ---------------------------------------------------------------- main

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Draw figures from 07_present/figures/figures.json (ledger values only).")
    ap.add_argument("project")
    ap.add_argument("--only", default="", help="comma-separated figure ids")
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--profile", choices=PROFILES, default="document",
                    help="document (default: font_size, width_cm; F<n>.*) or poster (poster_width_cm default 30, "
                         "font_pt default 24; F<n>.poster.*)")
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


def content_digest(data: dict) -> str:
    """SHA-256 of the numbers a figure draws (values + chart); poster_build compares it to spot a stale poster figure."""
    blob = json.dumps({"values": data.get("values"), "chart": data.get("chart")}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _record_poster_render(path: Path, render: dict) -> None:
    """Add render.poster (printed font_pt, drawn width_cm, digest of the drawn numbers) to an existing data.json."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return  # no document run yet: nothing to annotate (data.json stays one per figure)
    if not isinstance(data, dict):
        return
    rec = dict(render, data_digest=content_digest(data))
    data.setdefault("render", {})["poster"] = rec
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


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
    _configure(matplotlib, ctx_style)
    by_id = None
    outdir = project / OUT_REL
    outdir.mkdir(parents=True, exist_ok=True)
    for fig in figs:
        fid = fig["id"]
        if only and fid not in only:
            continue
        if fig["type"] not in ("km", "rob") and by_id is None:
            try:
                by_id = derived.ledger_by_id(project)
            except (OSError, ValueError) as e:
                raise FigureError(f"{fid}: cannot read the results ledger: {e}") from e
        ctx = _ctx_for(plt, ctx_style, lang, args.dpi, fig, args.profile)
        f, source, data = BUILDERS[fig["type"]](ctx, fig, by_id=by_id, lang=lang, project=project)
        warn = ctx.colour_warning(fid)
        if warn:
            print(f"figures.py: {warn}", file=sys.stderr)
        render = {"width_cm": round(float(f.get_figwidth()) * 2.54, 2), "font_pt": ctx.size}
        for k in ("width_cm", "font_pt"):
            if render[k] == int(render[k]):
                render[k] = int(render[k])
        if args.profile == "poster":
            _record_poster_render(outdir / f"{fid}.data.json", render)  # before the files, so they stay newer
            _save(ctx, f, outdir, fid, ".poster")
            print(f"{fid} {fig['type']} → {OUT_REL}/{fid}.poster.{{svg,pdf,png}}")
            continue
        _save(ctx, f, outdir, fid)
        out = {"id": fid, "type": fig["type"], "source": source, "values": data["values"]}
        for k in ("data_file", "data_sha256"):
            if k in data:
                out[k] = data[k]
        out["chart"] = data["chart"]
        out["render"] = {"document": render}
        (outdir / f"{fid}.data.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(f"{fid} {fig['type']} → {OUT_REL}/{fid}.{{svg,pdf,png}}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
