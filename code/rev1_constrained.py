"""Revision 1, R1.3: hard exposure limit enforced on the benchmark as well.

In the paper, the headroom procedure with a hard exposure limit (step 3b resolved by building knowledge until
K >= K_test, wait_haz=True) was compared with the UNCONSTRAINED optimum. Here the optimum is recomputed with the
same limit: an activity whose hazard per BU exceeds h_max = 0.05 at the current state is inadmissible (Bellman
equation (12) restricted to admissible activities). Envelope sets and seeds are those of Sec. V-D (envelope.json).
"""
import json, sys, numpy as np
from multiprocessing import Pool
from scipy.ndimage import map_coordinates
from kmc_model import *

HMAX = 0.05; BIG = 1e6

def solve_dp_limit(p=P, tgt=TARGET, n=121, dc=0.1, tol=1e-6, itmax=20000, hmax=HMAX):
    g = np.linspace(0, 1, n); K, M = np.meshgrid(g, g, indexing="ij")
    term = in_target(K, M, tgt); V = np.where(term, 0.0, 50.0)
    interp = lambda V, Kq, Mq: map_coordinates(V, [np.clip(Kq, 0, 1) * (n - 1), np.clip(Mq, 0, 1) * (n - 1)], order=1, mode="nearest")
    pre = {}
    for a in ACTS:
        fk, fm, h = rates(K, M, a, p)
        pre[a] = (K + fk * dc, M + fm * dc, np.minimum(h * dc, 1.0), np.clip(K - p["dK"], 0, 1), np.clip(M - p["dM"], 0, 1), h > hmax + 1e-12)
    for it in range(itmax):
        Q = []
        for a in ACTS:
            Kn, Mn, pr, Ks, Ms, bad = pre[a]
            q = dc + (1 - pr) * interp(V, Kn, Mn) + pr * (p["rework"] + interp(V, Ks, Ms))
            Q.append(np.where(bad, BIG, q))
        Q = np.stack(Q); Vn = np.where(term, 0.0, np.minimum(Q.min(0), BIG)); err = np.max(np.abs(Vn - V)); V = Vn
        if err < tol: break
    return g, V, np.where(term, -1, Q.argmin(0)), Q

def evaluate(p, x0, seed, n):
    g, V, pol, Q = solve_dp_limit(p=p)
    dpc = make_dp_policy(g, pol, Q)
    rng = np.random.default_rng(seed); a = np.array([simulate(dpc, p=p, x0=x0, rng=rng) for _ in range(n)])
    rng = np.random.default_rng(seed); b = np.array([simulate(lambda K, M, h: policy_procedure(K, M, h, p=p, wait_haz=True), p=p, x0=x0, rng=rng) for _ in range(n)])
    return float(a[:, 0].mean()), float(b[:, 0].mean()), float(np.mean(a[:, 0] >= 200)), float(np.mean(b[:, 0] >= 200)), K_haz(p), K_need(p)

def job(e):
    dp_lim, hr_hard, nr_dp, nr_hr, kh, kn = evaluate(e["params"], tuple(e["x0"]), e["seed"], 150)
    return dict(seed=e["seed"], binding=bool(kh > kn), dp_unc=e["dp"], dp_lim=dp_lim, hr_hard=hr_hard, nr_dp=nr_dp, nr_hr=nr_hr,
                excess_vs_lim=100 * (hr_hard / dp_lim - 1), excess_vs_unc=100 * (hr_hard / e["dp"] - 1), cost_of_limit=100 * (dp_lim / e["dp"] - 1))

if __name__ == "__main__":
    E = json.load(open("envelope.json"))
    with Pool(2) as pool: res = pool.map(job, E, chunksize=2)
    ex = np.array([r["excess_vs_lim"] for r in res]); exu = np.array([r["excess_vs_unc"] for r in res]); b = np.array([r["binding"] for r in res])
    p = dict(P); p.update(lamT=0.90)
    lh = evaluate(p, X0, 7, 1000)
    out = dict(hmax=HMAX, envelope=dict(n=len(res), binding=int(b.sum()), excess_vs_limited_median=float(np.median(ex)), excess_vs_limited_p90=float(np.percentile(ex, 90)),
               excess_vs_limited_max=float(ex.max()), excess_vs_unconstrained_median=float(np.median(exu)),
               cost_of_limit_median=float(np.median([r["cost_of_limit"] for r in res])),
               binding_excess_vs_limited_median=float(np.median(ex[b])) if b.any() else None),
               launch_hazard=dict(dp_limited=lh[0], headroom_hard=lh[1], excess_vs_limited=100 * (lh[1] / lh[0] - 1), K_haz=lh[4], K_need=lh[5]),
               sets=res)
    json.dump(out, open("rev1/constrained.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "sets"}, indent=1))
