"""Additional checks: hard exposure limit, tuned threshold baseline, coupling ablations, and launch-data
variants started from experienced-developer knowledge (Secs. V-C, V-H, VI-B) -> extensions.json."""
import json, numpy as np, sys
from multiprocessing import Pool
from kmc_model import *
from robustness import VARIANTS

SCEN = {"Base": {}, "Cheap, safe tests": dict(rT=0.44, lamT=0.20),
        "Costly, risky tests": dict(lamT=0.80, rework=4.0), "Weak simulation": dict(rS=0.12, kb=0.25)}
ABL = {"Base model": {},
       "No data-limited knowledge ceiling": dict(kb=1.0, kl=0.0),
       "No knowledge-limited maturity ceiling": dict(mb=1.0, ml=0.0),
       "Neither ceiling": dict(kb=1.0, kl=0.0, mb=1.0, ml=0.0),
       "No epistemic shocks": dict(lamE=0.0, lamT=0.0)}
LAUNCH = {"Launch-data hazard only": dict(lamT=0.90),
          "Launch-data informed": dict(lamT=0.90, tk_g=0.97, tk_q=2.5),
          "Launch-data informed, fitted range only": dict(lamT=0.90, tk_g=0.97, tk_q=2.5, tk_kmin=0.72)}
KSTAR = np.round(np.arange(0.30, 0.951, 0.025), 3)


def mc(f, p, x0, n, seed):
    rng = np.random.default_rng(seed)
    r = np.array([simulate(f, p=p, x0=x0, rng=rng) for _ in range(n)])
    return dict(mean=float(r[:, 0].mean()), p90=float(np.percentile(r[:, 0], 90)),
                shocks=float(r[:, 1].mean()), nr=float(np.mean(r[:, 0] >= 200)))


def tune_threshold(p, x0, n=300, seed=101):
    """K* minimizing mean cost on training runs (seed 101); evaluated later on independent runs (seed 7)."""
    best = None
    for ks in KSTAR:
        m = mc(lambda K, M, h, ks=ks: policy_threshold(K, M, h, p=p, Kstar=ks), p, x0, n, seed)["mean"]
        if best is None or m < best[1]: best = (float(ks), m)
    return best[0]


def evaluate(args):
    group, name, mod, x0, n = args
    import os
    ck = f"_ext_{group}_{name}_{x0[0]}.json".replace(" ", "_").replace(",", "")
    if os.path.exists(ck):
        return json.load(open(ck))
    p = dict(P); p.update(mod)
    g, V, pol, Q = solve_dp(p=p)
    ks = tune_threshold(p, x0)
    pols = {"dp": make_dp_policy(g, pol, Q),
            "headroom": lambda K, M, h: policy_procedure(K, M, h, p=p),
            "headroom_hard": lambda K, M, h: policy_procedure(K, M, h, p=p, wait_haz=True),
            "threshold_tuned": lambda K, M, h: policy_threshold(K, M, h, p=p, Kstar=ks),
            "coupled": lambda K, M, h: policy_coupled(K, M, h, p=p),
            "slope": lambda K, M, h: policy_slope(K, M, h, p=p),
            "analysis_first": lambda K, M, h: policy_analysis_first(K, M, h, p=p),
            "test_first": lambda K, M, h: policy_test_first(K, M, h, p=p),
            "spiral": policy_spiral}
    out = {"group": group, "name": name, "x0": list(x0), "K_need": K_need(p), "K_haz": K_haz(p),
           "Kstar": ks, "share_T_map": float(np.mean(pol[pol >= 0] == 2))}
    for k, f in pols.items():
        out[k] = mc(f, p, x0, n, 7)
    json.dump(out, open(ck, "w"))
    return out


if __name__ == "__main__":
    jobs = [("scenario", k, v, X0, 2000 if k == "Base" else 1000) for k, v in SCEN.items()]
    jobs += [("form", k, v, X0, 1000) for k, v in VARIANTS.items() if k != "Base model"]
    jobs += [("ablation", k, v, X0, 1000) for k, v in ABL.items() if k != "Base model"]
    for k0 in (0.15, 0.57, 0.72):
        jobs += [("launch", k, v, (k0, 0.10), 1000) for k, v in LAUNCH.items()]
    with Pool(2) as pool:
        res = pool.map(evaluate, jobs, chunksize=1)
    json.dump(res, open("extensions.json", "w"), indent=1)
    for r in res:
        d = r["dp"]["mean"]
        print(r["group"], r["name"], r["x0"][0], "dp", round(d, 2), "K*", r["Kstar"],
              {k: round(100 * (r[k]["mean"] / d - 1), 1) for k in
               ["headroom", "headroom_hard", "threshold_tuned", "coupled", "slope", "analysis_first", "test_first", "spiral"]})
