#!/usr/bin/env python3
"""Sample size calculator for clinical research designs.

Usage examples:
  python samplesize.py two-means --delta 5 --sd 12 --alpha 0.05 --power 0.8 --dropout 0.15
  python samplesize.py two-props --p1 0.30 --p2 0.45 --ratio 1
  python samplesize.py one-prop --p0 0.20 --p1 0.30
  python samplesize.py one-mean --delta 3 --sd 10
  python samplesize.py paired --delta 4 --sd-diff 9
  python samplesize.py correlation --r 0.3
  python samplesize.py survival --hr 0.70 --p-event-ctrl 0.40 --p-event-trt 0.30
  python samplesize.py noninf-props --p-ctrl 0.85 --p-trt 0.85 --margin 0.10 --alpha 0.025
  python samplesize.py noninf-means --sd 10 --margin 3 --true-diff 0 --alpha 0.025
  python samplesize.py equiv-means --sd 10 --margin 3 --alpha 0.025
  python samplesize.py diag --sens 0.90 --prev 0.25 --width 0.10
  python samplesize.py prevalence --p 0.15 --width 0.05
  python samplesize.py prevalence --p 0.15 --relative-precision 0.2 --deff 2
  python samplesize.py prevalence --p 0.12 --width 0.03 --n-clusters 10 --icc 0.01 --dropout 0.1
  python samplesize.py sensitivity --design prevalence --p 0.12 --width 0.03 --n-clusters 10 --icc 0.01 --vary icc --values 0.005,0.01,0.02,0.04
  python samplesize.py sensitivity --design regression-epv --predictors 10 --p-outcome 0.12 --vary epv --values 10,15,20
  python samplesize.py regression-epv --predictors 8 --epv 10 --p-outcome 0.25
  python samplesize.py power --design two-props --n 100 --p1 0.30 --p2 0.45
  python samplesize.py sensitivity --design two-means --delta 5 --sd 12 --vary delta --values 3,4,5,6,7
  python samplesize.py sensitivity --design two-props --p1 0.30 --p2 0.20 --vary p1 --values 0.2,0.3,0.4 --link rr

Common options: --alpha (2-sided, default .05) --power (.80) --dropout (0) --ratio (k = n2/n1, default 1)
Cluster options: --cluster-size m --icc rho  (design effect = 1 + (m-1)*rho)
Add --json for machine-readable output.
"""
import argparse
import json
import math

try:  # scipy is optional: the script only needs the standard normal ppf/cdf
    from scipy.stats import norm
except ImportError:  # Python >= 3.8 standard library fallback, identical to double precision
    from statistics import NormalDist as _NormalDist

    class norm:  # minimal stand-in for scipy.stats.norm
        _nd = _NormalDist()
        ppf = staticmethod(_nd.inv_cdf)
        cdf = staticmethod(_nd.cdf)


def z(p):
    return norm.ppf(p)


def ceil(x):
    return int(math.ceil(x - 1e-9))


# ---------- core formulas: each returns n for group 1 (before dropout / design effect) ----------

def n_two_means(delta, sd, alpha, power, ratio=1.0, sided=2):
    """Normal approximation + Guenther (1981) correction z_a^2/4 so results match t-test software."""
    if delta == 0:
        raise SystemExit("delta == 0: effect size is zero, sample size is infinite.")
    za = z(1 - alpha / sided)
    zb = z(power)
    return (1 + 1 / ratio) * (sd * (za + zb) / delta) ** 2 + za ** 2 / 4


def n_two_props(p1, p2, alpha, power, ratio=1.0, sided=2, continuity=False):
    if p1 == p2:
        raise SystemExit("p1 == p2: effect size is zero, sample size is infinite. Use --link rr|arr when varying p1.")
    za = z(1 - alpha / sided)
    zb = z(power)
    pbar = (p1 + ratio * p2) / (1 + ratio)
    num = za * math.sqrt((1 + 1 / ratio) * pbar * (1 - pbar)) + zb * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2) / ratio)
    n1 = (num / (p1 - p2)) ** 2
    if continuity:  # Fleiss continuity correction
        n1 = n1 / 4 * (1 + math.sqrt(1 + 2 * (1 + ratio) / (n1 * ratio * abs(p1 - p2)))) ** 2
    return n1


def n_one_prop(p0, p1, alpha, power, sided=2):
    za = z(1 - alpha / sided)
    zb = z(power)
    return ((za * math.sqrt(p0 * (1 - p0)) + zb * math.sqrt(p1 * (1 - p1))) / (p1 - p0)) ** 2


def n_one_mean(delta, sd, alpha, power, sided=2):
    za = z(1 - alpha / sided)
    zb = z(power)
    return (sd * (za + zb) / delta) ** 2 + za ** 2 / 2


def n_correlation(r, alpha, power, sided=2):
    za = z(1 - alpha / sided)
    zb = z(power)
    fz = 0.5 * math.log((1 + r) / (1 - r))
    return ((za + zb) / fz) ** 2 + 3


def events_logrank(hr, alpha, power, ratio=1.0, sided=2):
    """Schoenfeld: total number of events required."""
    za = z(1 - alpha / sided)
    zb = z(power)
    p1 = 1 / (1 + ratio)
    p2 = ratio / (1 + ratio)
    return (za + zb) ** 2 / (p1 * p2 * math.log(hr) ** 2)


def n_noninf_props(p_ctrl, p_trt, margin, alpha, power, ratio=1.0):
    """Non-inferiority for proportions; alpha is ONE-sided. margin > 0 = max acceptable worsening."""
    za = z(1 - alpha)
    zb = z(power)
    diff = p_trt - p_ctrl  # true difference (usually 0)
    return (za + zb) ** 2 * (p_ctrl * (1 - p_ctrl) + p_trt * (1 - p_trt) / ratio) / (diff + margin) ** 2


def n_noninf_means(sd, margin, true_diff, alpha, power, ratio=1.0):
    za = z(1 - alpha)
    zb = z(power)
    return (1 + 1 / ratio) * (sd * (za + zb) / (margin - abs(true_diff))) ** 2


def n_equiv_means(sd, margin, true_diff, alpha, power, ratio=1.0):
    """TOST equivalence: two one-sided tests, beta split -> z(1 - beta/2)."""
    za = z(1 - alpha)
    zb = z(1 - (1 - power) / 2)
    return (1 + 1 / ratio) * (sd * (za + zb) / (margin - abs(true_diff))) ** 2


def n_diag(acc, prev, width, alpha, is_sens=True):
    """Buderer 1996: n so that the CI half-width for sensitivity (or specificity) equals `width`."""
    za = z(1 - alpha / 2)
    n_cases = za ** 2 * acc * (1 - acc) / width ** 2
    denom = prev if is_sens else (1 - prev)
    return n_cases, n_cases / denom


def n_prevalence(p, width, alpha, finite_pop=None):
    za = z(1 - alpha / 2)
    n = za ** 2 * p * (1 - p) / width ** 2
    if finite_pop:
        n = n / (1 + (n - 1) / finite_pop)
    return n


# ---------- power (reverse calculation) ----------

def power_two_means(n1, delta, sd, alpha, ratio=1.0, sided=2):
    za = z(1 - alpha / sided)
    se = sd * math.sqrt(1 / n1 + 1 / (ratio * n1))
    return norm.cdf(abs(delta) / se - za)


def power_two_props(n1, p1, p2, alpha, ratio=1.0, sided=2):
    za = z(1 - alpha / sided)
    n2 = ratio * n1
    pbar = (n1 * p1 + n2 * p2) / (n1 + n2)
    se0 = math.sqrt(pbar * (1 - pbar) * (1 / n1 + 1 / n2))
    se1 = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    return norm.cdf((abs(p1 - p2) - za * se0) / se1)


def power_logrank(events, hr, alpha, ratio=1.0, sided=2):
    za = z(1 - alpha / sided)
    p1 = 1 / (1 + ratio)
    p2 = ratio / (1 + ratio)
    return norm.cdf(abs(math.log(hr)) * math.sqrt(events * p1 * p2) - za)


# ---------- finishing: design effect + dropout inflation ----------

def finish(n1, args, extra=None, per_group=True):
    de = 1.0
    if args.cluster_size and args.icc is not None:
        de = 1 + (args.cluster_size - 1) * args.icc
    n1_de = n1 * de
    n1_final = ceil(n1_de / (1 - args.dropout))
    n2_final = ceil(n1_de * args.ratio / (1 - args.dropout)) if per_group else None
    out = {
        "design": args.cmd,
        "alpha": args.alpha, "sided": getattr(args, "sided", 2), "power": args.power,
        "ratio_n2_n1": args.ratio if per_group else None,
        "n1_raw": round(n1, 2),
        "design_effect": round(de, 3),
        "dropout": args.dropout,
        "n1_final": n1_final,
        "n2_final": n2_final,
        "n_total_final": n1_final + (n2_final or 0),
    }
    if args.cluster_size and args.icc is not None:
        out["clusters_per_arm"] = ceil(n1_final / args.cluster_size)
    if extra:
        out.update(extra)
    return out


def print_out(out, as_json):
    if as_json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return
    for k, v in out.items():
        if v is not None:
            print(f"{k:>22}: {v}")


# ---------- CLI ----------

def add_common(p, per_group=True):
    p.add_argument("--alpha", type=float, default=0.05)
    p.add_argument("--power", type=float, default=0.80)
    p.add_argument("--dropout", type=float, default=0.0, help="expected attrition fraction, e.g. 0.15")
    p.add_argument("--sided", type=int, choices=[1, 2], default=2)
    p.add_argument("--cluster-size", type=float, default=None)
    p.add_argument("--icc", type=float, default=None)
    p.add_argument("--json", action="store_true")
    if per_group:
        p.add_argument("--ratio", type=float, default=1.0, help="allocation ratio n2/n1")
    else:
        p.set_defaults(ratio=1.0)


def build():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)

    p = sp.add_parser("two-means"); add_common(p)
    p.add_argument("--delta", type=float, required=True, help="clinically important mean difference")
    p.add_argument("--sd", type=float, required=True, help="pooled SD of the outcome")

    p = sp.add_parser("two-props"); add_common(p)
    p.add_argument("--p1", type=float, required=True)
    p.add_argument("--p2", type=float, required=True)
    p.add_argument("--continuity", action="store_true", help="Fleiss continuity correction")

    p = sp.add_parser("one-prop"); add_common(p, per_group=False)
    p.add_argument("--p0", type=float, required=True, help="null / reference proportion")
    p.add_argument("--p1", type=float, required=True, help="expected proportion")

    p = sp.add_parser("one-mean"); add_common(p, per_group=False)
    p.add_argument("--delta", type=float, required=True)
    p.add_argument("--sd", type=float, required=True)

    p = sp.add_parser("paired"); add_common(p, per_group=False)
    p.add_argument("--delta", type=float, required=True, help="mean of within-pair differences")
    p.add_argument("--sd-diff", type=float, required=True, help="SD of within-pair differences (~ sd*sqrt(2(1-r)))")

    p = sp.add_parser("correlation"); add_common(p, per_group=False)
    p.add_argument("--r", type=float, required=True)

    p = sp.add_parser("survival"); add_common(p)
    p.add_argument("--hr", type=float, required=True)
    p.add_argument("--p-event-ctrl", type=float, required=True, help="prob. of event in control over follow-up")
    p.add_argument("--p-event-trt", type=float, default=None, help="default: 1-(1-p_ctrl)^HR")

    p = sp.add_parser("noninf-props"); add_common(p)
    p.add_argument("--p-ctrl", type=float, required=True)
    p.add_argument("--p-trt", type=float, required=True)
    p.add_argument("--margin", type=float, required=True, help="non-inferiority margin (absolute, >0)")

    p = sp.add_parser("noninf-means"); add_common(p)
    p.add_argument("--sd", type=float, required=True)
    p.add_argument("--margin", type=float, required=True)
    p.add_argument("--true-diff", type=float, default=0.0)

    p = sp.add_parser("equiv-means"); add_common(p)
    p.add_argument("--sd", type=float, required=True)
    p.add_argument("--margin", type=float, required=True)
    p.add_argument("--true-diff", type=float, default=0.0)

    p = sp.add_parser("diag"); add_common(p, per_group=False)
    p.add_argument("--sens", type=float, default=None)
    p.add_argument("--spec", type=float, default=None)
    p.add_argument("--prev", type=float, required=True)
    p.add_argument("--width", type=float, required=True, help="CI half-width")

    p = sp.add_parser("prevalence"); add_common(p, per_group=False)
    p.add_argument("--p", type=float, required=True)
    p.add_argument("--width", type=float, default=None, help="absolute precision d (CI half-width), e.g. 0.05")
    p.add_argument("--relative-precision", type=float, default=None, help="relative precision epsilon: d = epsilon * p")
    p.add_argument("--deff", type=float, default=None, help="design effect for cluster/multistage sampling (e.g. 2)")
    p.add_argument("--n-clusters", type=float, default=None,
                   help="FIXED number of clusters (e.g. 10 communes); with --icc solves for n and cluster size")
    p.add_argument("--finite-pop", type=float, default=None)

    p = sp.add_parser("regression-epv"); add_common(p, per_group=False)
    p.add_argument("--predictors", type=int, required=True, help="number of candidate parameters (dummy variables count separately)")
    p.add_argument("--epv", type=float, default=10, help="events per variable (10 minimum, 20 safer)")
    p.add_argument("--p-outcome", type=float, required=True, help="expected proportion with the less frequent outcome")

    p = sp.add_parser("power"); add_common(p)
    p.add_argument("--design", choices=["two-means", "two-props", "survival"], required=True)
    p.add_argument("--n", type=float, required=True, help="n per group 1 (or total events for survival)")
    p.add_argument("--delta", type=float)
    p.add_argument("--sd", type=float)
    p.add_argument("--p1", type=float)
    p.add_argument("--p2", type=float)
    p.add_argument("--hr", type=float)

    p = sp.add_parser("sensitivity"); add_common(p)
    p.add_argument("--design", choices=["two-means", "two-props", "survival", "prevalence", "regression-epv"], required=True)
    p.add_argument("--vary", required=True, help="parameter to vary: delta|sd|p1|p2|hr|power|dropout|icc|p_event_ctrl")
    p.add_argument("--link", choices=["rr", "arr", "d"], default=None,
                   help="when varying p1 (or sd), keep RR / absolute risk reduction / Cohen d constant by recomputing p2 (or delta)")
    p.add_argument("--values", required=True, help="comma-separated values")
    p.add_argument("--delta", type=float)
    p.add_argument("--sd", type=float)
    p.add_argument("--p1", type=float)
    p.add_argument("--p2", type=float)
    p.add_argument("--hr", type=float)
    p.add_argument("--p-event-ctrl", type=float)
    # prevalence / regression-epv (vary: p|width|relative_precision|deff|icc|n_clusters|epv|p_outcome|predictors|dropout)
    p.add_argument("--p", type=float)
    p.add_argument("--width", type=float)
    p.add_argument("--relative-precision", type=float)
    p.add_argument("--deff", type=float)
    p.add_argument("--n-clusters", type=float)
    p.add_argument("--finite-pop", type=float)
    p.add_argument("--predictors", type=int)
    p.add_argument("--epv", type=float, default=10)
    p.add_argument("--p-outcome", type=float)
    return ap


def run_prevalence(args):
    if (args.width is None) == (args.relative_precision is None):
        raise SystemExit("prevalence: give exactly one of --width (absolute d) or --relative-precision (epsilon).")
    width = args.width if args.width is not None else args.relative_precision * args.p
    n0 = n_prevalence(args.p, width, args.alpha, args.finite_pop)
    out = {"design": "prevalence", "p": args.p, "ci_half_width": round(width, 4),
           "precision_type": "absolute" if args.width is not None else f"relative (epsilon={args.relative_precision})",
           "alpha": args.alpha, "n_srs": round(n0, 2)}
    n_clusters = getattr(args, "n_clusters", None)
    if n_clusters:
        # fixed number of clusters k, cluster size m = n/k unknown: n = n0*(1 + (n/k - 1)*icc)
        if args.icc is None:
            raise SystemExit("--n-clusters needs --icc.")
        if n0 * args.icc >= n_clusters:
            raise SystemExit(
                f"INFEASIBLE: with {n_clusters:g} clusters and ICC={args.icc}, the effective sample size can never "
                f"exceed k/ICC = {n_clusters / args.icc:.0f} < required {n0:.0f}. Increase the number of clusters "
                f"(need > {n0 * args.icc:.1f}), relax the precision, or justify a smaller ICC.")
        n = n0 * (1 - args.icc) / (1 - n0 * args.icc / n_clusters)
        de = n / n0
        out.update({"n_clusters": n_clusters, "icc": args.icc, "cluster_size_m": round(n / n_clusters, 1)})
    else:
        de = args.deff
        if de is None and args.cluster_size and args.icc is not None:
            de = 1 + (args.cluster_size - 1) * args.icc
        de = de or 1.0
        n = n0 * de
    out.update({"design_effect": round(de, 3), "n_after_deff": ceil(n), "dropout": args.dropout,
                "n_total_final": ceil(n / (1 - args.dropout)), "method": "Wald CI precision"})
    if n_clusters:
        out["per_cluster_final"] = ceil(out["n_total_final"] / n_clusters)
    elif args.cluster_size:
        out["clusters_needed"] = ceil(out["n_total_final"] / args.cluster_size)
    return out


def run_design(args):
    c = args.cmd
    if c == "two-means":
        return finish(n_two_means(args.delta, args.sd, args.alpha, args.power, args.ratio, args.sided), args,
                      {"delta": args.delta, "sd": args.sd, "cohen_d": round(args.delta / args.sd, 3)})
    if c == "two-props":
        return finish(n_two_props(args.p1, args.p2, args.alpha, args.power, args.ratio, args.sided, args.continuity), args,
                      {"p1": args.p1, "p2": args.p2, "abs_diff": round(args.p2 - args.p1, 4),
                       "rr": round(args.p2 / args.p1, 3),
                       "or": round((args.p2 / (1 - args.p2)) / (args.p1 / (1 - args.p1)), 3)})
    if c == "one-prop":
        return finish(n_one_prop(args.p0, args.p1, args.alpha, args.power, args.sided), args,
                      {"p0": args.p0, "p1": args.p1}, per_group=False)
    if c == "one-mean":
        return finish(n_one_mean(args.delta, args.sd, args.alpha, args.power, args.sided), args,
                      {"delta": args.delta, "sd": args.sd}, per_group=False)
    if c == "paired":
        return finish(n_one_mean(args.delta, args.sd_diff, args.alpha, args.power, args.sided), args,
                      {"delta": args.delta, "sd_diff": args.sd_diff, "note": "n = number of pairs"}, per_group=False)
    if c == "correlation":
        return finish(n_correlation(args.r, args.alpha, args.power, args.sided), args, {"r": args.r}, per_group=False)
    if c == "survival":
        p_trt = args.p_event_trt if args.p_event_trt is not None else 1 - (1 - args.p_event_ctrl) ** args.hr
        ev = events_logrank(args.hr, args.alpha, args.power, args.ratio, args.sided)
        p_avg = (args.p_event_ctrl + args.ratio * p_trt) / (1 + args.ratio)
        n1 = (ev / p_avg) / (1 + args.ratio)
        return finish(n1, args, {"hr": args.hr, "events_required": ceil(ev), "p_event_ctrl": args.p_event_ctrl,
                                 "p_event_trt": round(p_trt, 4), "method": "Schoenfeld (log-rank)"})
    if c == "noninf-props":
        args.sided = 1
        return finish(n_noninf_props(args.p_ctrl, args.p_trt, args.margin, args.alpha, args.power, args.ratio), args,
                      {"p_ctrl": args.p_ctrl, "p_trt": args.p_trt, "margin": args.margin, "note": "alpha is one-sided"})
    if c == "noninf-means":
        args.sided = 1
        return finish(n_noninf_means(args.sd, args.margin, args.true_diff, args.alpha, args.power, args.ratio), args,
                      {"sd": args.sd, "margin": args.margin, "true_diff": args.true_diff, "note": "alpha is one-sided"})
    if c == "equiv-means":
        args.sided = 1
        return finish(n_equiv_means(args.sd, args.margin, args.true_diff, args.alpha, args.power, args.ratio), args,
                      {"sd": args.sd, "margin": args.margin, "true_diff": args.true_diff,
                       "method": "TOST, alpha one-sided each"})
    if c == "diag":
        out = {"design": c, "prev": args.prev, "ci_half_width": args.width, "alpha": args.alpha, "dropout": args.dropout}
        if args.sens is not None:
            nc, nt = n_diag(args.sens, args.prev, args.width, args.alpha, True)
            out.update({"sens": args.sens, "n_diseased": ceil(nc), "n_total_for_sens": ceil(nt / (1 - args.dropout))})
        if args.spec is not None:
            nc, nt = n_diag(args.spec, args.prev, args.width, args.alpha, False)
            out.update({"spec": args.spec, "n_nondiseased": ceil(nc), "n_total_for_spec": ceil(nt / (1 - args.dropout))})
        cands = [v for k, v in out.items() if k.startswith("n_total_for")]
        out["n_total_final"] = max(cands) if cands else None
        out["method"] = "Buderer 1996"
        return out
    if c == "prevalence":
        return run_prevalence(args)
    if c == "regression-epv":
        n = args.predictors * args.epv / args.p_outcome
        out = {"design": c, "candidate_parameters": args.predictors, "events_per_variable": args.epv,
               "p_outcome": args.p_outcome, "events_required": ceil(args.predictors * args.epv),
               "n_raw": round(n, 2), "dropout": args.dropout, "n_total_final": ceil(n / (1 - args.dropout)),
               "method": "EPV rule of thumb (Peduzzi 1996); for prediction models use Riley 2020 criteria (pmsampsize)"}
        if getattr(args, "cluster_size", None) or getattr(args, "icc", None) is not None:
            out["note"] = ("cluster options ignored: EPV counts events, not independent people; "
                           "handle clustering in the analysis (mixed model / GEE)")
        return out
    if c == "power":
        if args.design == "two-means":
            pw = power_two_means(args.n, args.delta, args.sd, args.alpha, args.ratio, args.sided)
        elif args.design == "two-props":
            pw = power_two_props(args.n, args.p1, args.p2, args.alpha, args.ratio, args.sided)
        else:
            pw = power_logrank(args.n, args.hr, args.alpha, args.ratio, args.sided)
        return {"design": args.design, "n_input": args.n, "alpha": args.alpha, "sided": args.sided, "power": round(pw, 4)}
    if c == "sensitivity" and args.design in ("prevalence", "regression-epv"):
        rows = []
        for v in [float(x) for x in args.values.split(",")]:
            b = argparse.Namespace(**vars(args))
            b.cmd = args.design
            key = args.vary.replace("-", "_")
            if not hasattr(b, key):
                raise SystemExit(f"cannot vary {args.vary} for {args.design}")
            setattr(b, key, int(v) if key == "predictors" else v)
            try:
                r = run_design(b)
                row = {args.vary: v, "n1": r["n_total_final"], "n2": None, "n_total": r["n_total_final"]}
                if "design_effect" in r:
                    row["design_effect"] = r["design_effect"]
                if "events_required" in r:
                    row["events"] = r["events_required"]
            except SystemExit as e:
                row = {args.vary: v, "n1": "INFEASIBLE", "n2": None, "n_total": "INFEASIBLE", "note": str(e)}
            rows.append(row)
        return {"design": args.design, "vary": args.vary, "rows": rows}
    if c == "sensitivity":
        rows = []
        base = dict(cmd=args.design, alpha=args.alpha, power=args.power, dropout=args.dropout, ratio=args.ratio,
                    sided=args.sided, cluster_size=args.cluster_size, icc=args.icc, delta=args.delta, sd=args.sd,
                    p1=args.p1, p2=args.p2, hr=args.hr, p_event_ctrl=args.p_event_ctrl, p_event_trt=None,
                    continuity=False)
        for v in [float(x) for x in args.values.split(",")]:
            b = dict(base)
            b[args.vary] = v
            if args.link == "rr" and args.vary == "p1":
                b["p2"] = v * (args.p2 / args.p1)
            elif args.link == "arr" and args.vary == "p1":
                b["p2"] = v + (args.p2 - args.p1)
            elif args.link == "d" and args.vary == "sd":
                b["delta"] = v * (args.delta / args.sd)
            r = run_design(argparse.Namespace(**b))
            row = {args.vary: v, "n1": r["n1_final"], "n2": r["n2_final"], "n_total": r["n_total_final"]}
            if "p2" in r: row["p2"] = round(r["p2"], 4)
            if "delta" in r: row["delta"] = r["delta"]
            if "events_required" in r: row["events"] = r["events_required"]
            rows.append(row)
        return {"design": args.design, "vary": args.vary, "rows": rows}
    raise SystemExit(f"unknown design {c}")


def main():
    args = build().parse_args()
    out = run_design(args)
    if args.cmd == "sensitivity" and not args.json:
        print(f"design={out['design']}  vary={out['vary']}")
        print(f"{out['vary']:>10} | {'n1':>6} | {'n2':>6} | {'total':>6}")
        for r in out["rows"]:
            print(f"{r[out['vary']]:>10} | {r['n1']:>6} | {r['n2'] or '':>6} | {r['n_total']:>6}")
        return
    print_out(out, args.json)


if __name__ == "__main__":
    main()
