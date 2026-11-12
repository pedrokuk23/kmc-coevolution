"""Revision 1, R1.2 and R2.3 (second round): observable acceptance review, operating characteristics, and the
reliability of the recommended activity judged from quantities the decision maker can compute.

Same closed loop as rev1_stopping.py (the policy sees only noisy assessments every 3 BU and acts between them on the
state predicted by the fitted model; coefficients re-fitted after each assessment with the weak prior of
calib_adaptive.py), with three changes:
  1. Reviews are counted, and their cost is added outside the activity clock, so the total cost for any
     confirmation cost C is cost_activities + C * reviews (operating characteristics for several C from one run).
  2. Each decision (every 1 BU) records the activity chosen, the activity that the SAME rule chooses at the true
     state with the true coefficients (headroom: Table 6 with the true parameters; optimum: the optimal policy of the
     true model), the estimated margin K_hat - K_need_hat, and the standard deviation of K_need_hat from the
     fit (delta method on the Gauss-Newton covariance of the least-squares fit, prior included).
  3. Noise level and acceptance margin are arguments.
Reference: the optimal policy of the true model stopping when the true state reaches the target (oracle).
Usage: python3 rev1_stopping2.py R noise margins kinds   e.g.  120 0.03 0,0.015,0.03,0.045 headroom,dp_known"""
import json, sys, os, numpy as np
from multiprocessing import Pool
from scipy.optimize import least_squares
import calib_adaptive as ca
from kmc_model import P, TARGET, X0, rates, in_target, make_dp_policy, policy_procedure, K_need

OPT_TRUE = make_dp_policy(ca.G0, ca.POL0, ca.Q0)
DT, CMAX = ca.DT, ca.CMAX
TRUE_RULE = {"headroom": lambda K, M: policy_procedure(K, M, {}, p=P), "dp": lambda K, M: OPT_TRUE(K, M, {}),
             "dp_known": lambda K, M: OPT_TRUE(K, M, {})}

def fit(acts, idx, obs, start, rs, noise):
    def res(th):
        r = (ca.replay(th, acts)[idx] - obs).ravel() / noise
        return np.concatenate([r, (th - ca.PRIOR) / ca.PSD])
    starts = [start] + list(ca.LB + (ca.UB - ca.LB) * rs.random((3, len(ca.FIT))))
    best = min((least_squares(res, s0, bounds=(ca.LB, ca.UB)) for s0 in starts), key=lambda r: r.cost)
    J = best.jac
    try: cov = np.linalg.pinv(J.T @ J)
    except Exception: cov = np.full((len(ca.FIT),) * 2, np.nan)
    return best.x, cov

def kneed_sd(theta, cov):
    """Delta method for K_need = (M_req - m_b) / m_l (interior case)."""
    mb, ml = theta[2], theta[3]
    g = np.zeros(len(theta)); g[2] = -1 / ml; g[3] = -(TARGET[1] - mb) / ml ** 2
    v = float(g @ cov @ g)
    return float(np.sqrt(v)) if v > 0 else float("nan")

def run_project(rep, kind, margin, noise):
    rng = np.random.default_rng(5000 + rep); nrng = np.random.default_rng(6000 + rep); rs = np.random.default_rng(7000 + rep)
    crng = np.random.default_rng(8000 + rep)
    known = kind == "dp_known"
    theta = np.array([P[k] for k in ca.FIT]) if known else ca.PRIOR.copy(); cov = np.diag(ca.PSD ** 2)
    policy, pf = (OPT_TRUE, dict(P)) if known else ca.make_policy(theta, kind)
    K, M = X0; obs0 = np.clip(np.array(X0) + nrng.normal(0, noise, 2), 0, 1)
    Kh, Mh = (obs0 if known else X0)
    c = 0.0; shocks = 0; acts = []; idx = [0]; obs = [obs0]
    next_assess = DT; last_review = -9.0; reviews = 0; accepted = False; dec = []; next_dec = 0.0
    while not accepted and c < CMAX:
        last_in = obs[-1][0] >= TARGET[0] and obs[-1][1] >= TARGET[1]
        if (in_target(Kh, Mh) or last_in) and c - last_review >= 1.0 - 1e-9:
            reviews += 1; last_review = c
            o = np.clip(np.array([K, M]) + crng.normal(0, noise, 2), 0, 1)
            if o[0] >= TARGET[0] + margin and o[1] >= TARGET[1] + margin:
                accepted = True; break
            idx.append(len(acts)); obs.append(o)
            if known: Kh, Mh = o
            else:
                theta, cov = fit(acts, idx, np.array(obs), theta, rs, noise); policy, pf = ca.make_policy(theta, kind)
                Kh, Mh = ca.replay(theta, acts)[-1]
            continue
        a = policy(Kh, Mh, {"c": c})
        if c >= next_dec - 1e-9:
            kn_hat = float(min(K_need(pf), 1.5))
            dec.append(dict(c=round(c, 1), K=float(K), Kh=float(Kh), a=a, a_true=TRUE_RULE[kind](K, M),
                            Kneed_hat=kn_hat, Kneed=float(K_need(P)), sd=(0.0 if known else kneed_sd(theta, cov))))
            next_dec += 1.0
        fk, fm, h = rates(K, M, a, P)
        if rng.random() < min(h * 0.1, 1):
            K = max(K - P["dK"], 0); M = max(M - P["dM"], 0); c += P["rework"]; shocks += 1
            Kh = max(Kh - P["dK"], 0); Mh = max(Mh - P["dM"], 0); a = a + "!"
        else:
            K = min(K + fk * 0.1, 1); M = min(M + fm * 0.1, 1)
            fkh, fmh, _ = rates(Kh, Mh, a, pf); Kh = min(Kh + fkh * 0.1, 1); Mh = min(Mh + fmh * 0.1, 1)
        c += 0.1; acts.append(a)
        if c >= next_assess - 1e-9:
            idx.append(len(acts)); obs.append(np.clip(np.array([K, M]) + nrng.normal(0, noise, 2), 0, 1))
            if known: Kh, Mh = obs[-1]
            else:
                theta, cov = fit(acts, idx, np.array(obs), theta, rs, noise); policy, pf = ca.make_policy(theta, kind)
                Kh, Mh = ca.replay(theta, acts)[-1]
            next_assess = c + DT
    return dict(cost_act=float(c), shocks=shocks, reviews=reviews, accepted=accepted,
                premature=bool(accepted and not in_target(K, M)), deficit=float(max(TARGET[0] - K, 0) + max(TARGET[1] - M, 0)),
                decisions=dec)

def run(args):
    rep, kind, margin, noise = args
    ck = f"rev1/ck/_s2_{kind}_{margin}_{noise}_{rep}.json"
    if os.path.exists(ck): return json.load(open(ck))
    out = dict(rep=rep, kind=kind, margin=margin, noise=noise, **run_project(rep, kind, margin, noise))
    json.dump(out, open(ck, "w")); return out

def oracle(rep):
    return float(ca.simulate(OPT_TRUE, rng=np.random.default_rng(5000 + rep))[0])

if __name__ == "__main__":
    R = int(sys.argv[1]); noise = float(sys.argv[2]); margins = [float(x) for x in sys.argv[3].split(",")]; kinds = sys.argv[4].split(",")
    os.makedirs("rev1/ck", exist_ok=True)
    jobs = [(r, k, m, noise) for m in margins for k in kinds for r in range(R)]
    with Pool(2) as pool:
        pool.map(run, jobs, chunksize=1)
        ref = pool.map(oracle, range(R))
    print("done", len(jobs), float(np.mean(ref)))
