"""Estimation from noisy assessments, replicated (Sec. V-F) -> calib_replicates.json.

Each replicate simulates one synthetic project under the coupling-aware rule (own seed), assesses K and M
every 3 BU with independent noise (sd 0.03), and fits the seven rate and ceiling parameters by least squares
from 8 random starts drawn inside the bounds (no information from the true values). The plan computed from the
fitted parameters and the headroom procedure with fitted parameters are then evaluated on the true dynamics.
"""
import json, numpy as np, sys
from multiprocessing import Pool
from scipy.optimize import least_squares
from kmc_model import *

FIT = ["kb", "kl", "mb", "ml", "rS", "rE", "rT"]
LB = np.array([0, 0, 0, 0.2, 0.01, 0.01, 0.01]); UB = np.array([0.9, 1.5, 0.5, 2.0, 1.0, 1.0, 1.0])
NOBS = (4, 6, 8)
g0, V0, POL0, Q0 = solve_dp()


def replay(theta, acts, upto):
    p = dict(P); p.update(dict(zip(FIT, theta)))
    K, M = X0; out = [X0]
    for i in range(1, min(len(acts), upto + 1)):
        a = acts[i]
        if a.endswith("!"):
            K = max(K - p["dK"], 0); M = max(M - p["dM"], 0)
        else:
            fk, fm, h = rates(K, M, a, p); K = min(K + fk * 0.1, 1); M = min(M + fm * 0.1, 1)
        out.append((K, M))
    return np.array(out)


def run(rep):
    c, sh, tr = simulate(policy_coupled, rng=np.random.default_rng(1000 + rep), record=True)
    acts = [t[3] for t in tr]; trc = np.array([t[0] for t in tr]); xy = np.array([(t[1], t[2]) for t in tr])
    obs_c = np.arange(0, trc[-1], 3.0)
    idx = [int(np.argmin(np.abs(trc - cc))) for cc in obs_c]
    obs = np.clip(xy[idx] + np.random.default_rng(2000 + rep).normal(0, 0.03, (len(idx), 2)), 0, 1)
    out = {"rep": rep, "n_assessments": len(idx), "fits": {}}
    rs = np.random.default_rng(3000 + rep)
    starts = LB + (UB - LB) * rs.random((8, len(FIT)))
    for n in NOBS:
        if n > len(idx): continue
        sel = idx[:n]
        res = lambda th: (replay(th, acts, sel[-1])[sel] - obs[:n]).ravel()
        best = min((least_squares(res, s0, bounds=(LB, UB)) for s0 in starts), key=lambda r: r.cost)
        J = best.jac; sv = np.linalg.svd(J, compute_uv=False)
        rank = int(np.sum(sv > 1e-3 * sv[0])) if sv[0] > 0 else 0
        pf = dict(P); pf.update(dict(zip(FIT, best.x)))
        gF, VF, polF, QF = solve_dp(p=pf)
        agree = float(np.mean((polF == POL0)[POL0 >= 0]))
        rng = np.random.default_rng(7)
        dpf = make_dp_policy(gF, polF, QF)
        cost_dp = float(np.mean([simulate(dpf, rng=rng)[0] for _ in range(300)]))
        rng = np.random.default_rng(7)
        cost_hr = float(np.mean([simulate(lambda K, M, h: policy_procedure(K, M, h, p=pf), rng=rng)[0] for _ in range(300)]))
        out["fits"][str(n)] = dict(theta=dict(zip(FIT, map(float, best.x))), rank=rank, n_scalar_obs=2 * (n - 1),
                                   budget_seen=float(obs_c[n - 1]), agreement=agree,
                                   cost_fitted_dp=cost_dp, cost_fitted_headroom=cost_hr)
    return out


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    with Pool(2) as pool:
        res = pool.map(run, range(R), chunksize=1)
    rng = np.random.default_rng(7); dp0 = make_dp_policy(g0, POL0, Q0)
    ref = float(np.mean([simulate(dp0, rng=rng)[0] for _ in range(2000)]))
    summ = {}
    for n in NOBS:
        f = [r["fits"][str(n)] for r in res if str(n) in r["fits"]]
        ex = np.array([100 * (x["cost_fitted_dp"] / ref - 1) for x in f])
        eh = np.array([100 * (x["cost_fitted_headroom"] / ref - 1) for x in f])
        ag = np.array([x["agreement"] for x in f]); rk = np.array([x["rank"] for x in f])
        summ[str(n)] = dict(n=len(f), excess_dp_median=float(np.median(ex)), excess_dp_p10=float(np.percentile(ex, 10)),
                            excess_dp_p90=float(np.percentile(ex, 90)), excess_dp_max=float(ex.max()),
                            share_dp_within_5pct=float(np.mean(ex <= 5)),
                            excess_headroom_median=float(np.median(eh)), excess_headroom_p90=float(np.percentile(eh, 90)),
                            excess_headroom_max=float(eh.max()),
                            agreement_median=float(np.median(ag)), agreement_p10=float(np.percentile(ag, 10)),
                            rank_median=float(np.median(rk)), rank_min=int(rk.min()), rank_max=int(rk.max()),
                            param_relerr_median={k: float(np.median([abs(x["theta"][k] / P[k] - 1) for x in f])) for k in FIT})
    json.dump({"reference_dp_cost": ref, "summary": summ, "replicates": res}, open("calib_replicates.json", "w"), indent=1)
    print(json.dumps({"ref": ref, "summary": summ}, indent=1))
