"""Closed-loop estimation (Sec. V-F) -> calib_adaptive.json.

The method re-estimates the coefficients after every assessment (Table 6, steps 2 and 5; Table 11, steps 3 and 5).
Each replicate runs one synthetic project on the true dynamics. K and M are assessed every 3 BU with noise
(sd 0.03); after each assessment the seven rate and ceiling parameters are re-fitted to all assessments so far by
least squares with a weak prior (Table 11, step 2), centered on the midpoints of the literature-anchored ranges of
Sec. V-D and not on the true values, from the previous estimate and 3 random starts within the bounds. The next
activities follow either the dynamic program or the headroom procedure computed from the current estimate.
Two observation models (second command-line argument):
  true  the policy sees the true state (K, M) at every step; only the coefficients are estimated;
  est   the policy sees only the noisy assessments: between assessments it uses the state predicted by the fitted
        model along the activities performed (observed shocks applied), reset after each re-fit to the fitted
        trajectory at the current cost.
Costs are compared with the optimal policy of the true model on the same random numbers.
"""
import json, numpy as np, sys
from multiprocessing import Pool
from scipy.optimize import least_squares
from kmc_model import *

FIT = ["kb", "kl", "mb", "ml", "rS", "rE", "rT"]
LB = np.array([0, 0, 0, 0.2, 0.01, 0.01, 0.01]); UB = np.array([0.9, 1.5, 0.5, 2.0, 1.0, 1.0, 1.0])
PRIOR = np.array([0.30, 0.60, 0.075, 1.05, 0.225, 0.10, 0.285])   # midpoints of the Sec. V-D ranges
PSD = np.array([0.10, 0.10, 0.04, 0.15, 0.09, 0.025, 0.08])       # quarter of each range
NOISE, DT, CMAX = 0.03, 3.0, 60.0   # a project not finished by 60 BU (about 3x the optimum) counts as failed
G0, V0, POL0, Q0 = solve_dp()


def replay(theta, acts, x0=X0):
    p = dict(P); p.update(dict(zip(FIT, theta)))
    K, M = x0; out = [x0]
    for a in acts:
        if a.endswith("!"):
            K = max(K - p["dK"], 0); M = max(M - p["dM"], 0)
        else:
            fk, fm, h = rates(K, M, a, p); K = min(K + fk * 0.1, 1); M = min(M + fm * 0.1, 1)
        out.append((K, M))
    return np.array(out)


def fit(acts, idx, obs, start, rs):
    def res(th):
        r = (replay(th, acts)[idx] - obs).ravel() / NOISE
        return np.concatenate([r, (th - PRIOR) / PSD])
    starts = [start] + list(LB + (UB - LB) * rs.random((3, len(FIT))))
    best = min((least_squares(res, s0, bounds=(LB, UB)) for s0 in starts), key=lambda r: r.cost)
    return best.x


def make_policy(theta, kind):
    pf = dict(P); pf.update(dict(zip(FIT, theta)))
    if kind == "dp":
        g, V, pol, Q = solve_dp(p=pf)
        return make_dp_policy(g, pol, Q), pf
    return (lambda K, M, h: policy_procedure(K, M, h, p=pf)), pf


def run_project(rep, kind, mode):
    """Closed loop on the true dynamics; returns total cost, shocks, number of refits, final estimate."""
    rng = np.random.default_rng(5000 + rep); nrng = np.random.default_rng(6000 + rep); rs = np.random.default_rng(7000 + rep)
    theta = PRIOR.copy(); policy, pf = make_policy(theta, kind)
    K, M = X0; Kh, Mh = X0; c = 0.0; shocks = 0; acts = []; idx = [0]
    obs = [np.clip(np.array(X0) + nrng.normal(0, NOISE, 2), 0, 1)]
    next_assess = DT; refits = 0
    while not in_target(K, M, tol=0.005) and c < CMAX:
        a = policy(K, M, {"c": c}) if mode == "true" else policy(Kh, Mh, {"c": c})
        fk, fm, h = rates(K, M, a, P)
        if rng.random() < min(h * 0.1, 1):
            K = max(K - P["dK"], 0); M = max(M - P["dM"], 0); c += P["rework"]; shocks += 1
            Kh = max(Kh - P["dK"], 0); Mh = max(Mh - P["dM"], 0); a = a + "!"      # shocks are observed events
        else:
            K = min(K + fk * 0.1, 1); M = min(M + fm * 0.1, 1)
            fkh, fmh, _ = rates(Kh, Mh, a, pf); Kh = min(Kh + fkh * 0.1, 1); Mh = min(Mh + fmh * 0.1, 1)
        c += 0.1; acts.append(a)
        if c >= next_assess - 1e-9:
            idx.append(len(acts)); obs.append(np.clip(np.array([K, M]) + nrng.normal(0, NOISE, 2), 0, 1))
            theta = fit(acts, idx, np.array(obs), theta, rs); policy, pf = make_policy(theta, kind); refits += 1
            Kh, Mh = replay(theta, acts)[-1]                   # state estimate: fitted trajectory at the current cost
            next_assess = c + DT
    return float(c), shocks, refits, theta.tolist()


def run(args):
    rep, mode = args
    import os
    ck = f"_ca_{mode}_{rep}.json"          # checkpoint, so an interrupted run can resume
    if os.path.exists(ck):
        return json.load(open(ck))
    out = {"rep": rep}
    for kind in ("dp", "headroom"):
        c, s, n, th = run_project(rep, kind, mode)
        out[kind] = dict(cost=c, shocks=s, refits=n, theta_final=dict(zip(FIT, th)))
    # reference: optimal policy of the true model on the same random numbers
    rng = np.random.default_rng(5000 + rep)
    out["true_dp"] = dict(cost=float(simulate(make_dp_policy(G0, POL0, Q0), rng=rng)[0]))
    json.dump(out, open(ck, "w"))
    return out


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    MODE = sys.argv[2] if len(sys.argv) > 2 else "true"
    with Pool(2) as pool:
        res = pool.map(run, [(r, MODE) for r in range(R)], chunksize=1)
    ref = np.array([r["true_dp"]["cost"] for r in res])
    summ = {"reference_mean": float(ref.mean())}
    for kind in ("dp", "headroom"):
        c = np.array([r[kind]["cost"] for r in res])
        ex = 100 * (c / ref - 1)
        summ[kind] = dict(mean=float(c.mean()), excess_of_means=float(100 * (c.mean() / ref.mean() - 1)),
                          paired_excess_median=float(np.median(ex)), paired_excess_p90=float(np.percentile(ex, 90)),
                          n_not_reached=int(np.sum(c >= CMAX)), refits_median=float(np.median([r[kind]["refits"] for r in res])))
    fn = "calib_adaptive.json" if MODE == "true" else f"calib_adaptive_{MODE}.json"
    json.dump({"state_observation": MODE, "summary": summ, "replicates": res}, open(fn, "w"), indent=1)
    print(json.dumps(summ, indent=1))
