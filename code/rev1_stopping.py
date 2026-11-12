"""Revision 1, R1.2 and R2.3: closed-loop estimation with an observation-based stopping rule.

As calib_adaptive.py in mode 'est' (the policy sees only noisy assessments; between assessments it uses the state
predicted by the fitted model), but the project no longer stops when the TRUE state reaches the target. It stops
only after an acceptance review: when the estimated state, or the latest assessment, is in the target region, a
confirmation assessment is bought (cost C_CONF BU) and the claim is accepted if the confirmation reads at least
TARGET + margin on both coordinates. If it fails, the assessment joins the data, the model is re-fitted and work
continues (no new review within 1 BU). Reported per policy: total cost including reviews, number of reviews, the
premature-acceptance rate (true state outside the target at acceptance) and the true deficit at acceptance.
Reference costs on the same random numbers:
  ref_oracle  optimal policy of the true model, stopping when the true state reaches the target (as in the paper);
  dp_known    optimal policy of the true model (coefficients known) acting on the noisy assessments with the same
              review rule: isolates the cost of observing the state from the cost of estimating the coefficients.
R2.3: every 1 BU the activity chosen is compared with the optimal activity at the TRUE state (true model), together
with the margin K - K_need(estimated) and the error of the estimated K_need.
"""
import json, sys, os, numpy as np
from multiprocessing import Pool
import calib_adaptive as ca
from kmc_model import P, TARGET, X0, rates, in_target, solve_dp, make_dp_policy, policy_procedure, K_need

C_CONF = float(os.environ.get("C_CONF", 1.0))
G0, V0, POL0, Q0 = ca.G0, ca.V0, ca.POL0, ca.Q0
OPT_TRUE = make_dp_policy(G0, POL0, Q0)

def run_project(rep, kind, margin):
    rng = np.random.default_rng(5000 + rep); nrng = np.random.default_rng(6000 + rep); rs = np.random.default_rng(7000 + rep)
    crng = np.random.default_rng(8000 + rep)                       # confirmation noise
    known = kind == "dp_known"
    theta = np.array([P[k] for k in ca.FIT]) if known else ca.PRIOR.copy()
    policy, pf = (OPT_TRUE, dict(P)) if known else ca.make_policy(theta, kind)
    K, M = X0; obs0 = np.clip(np.array(X0) + nrng.normal(0, ca.NOISE, 2), 0, 1)
    Kh, Mh = (obs0 if known else X0)
    c = 0.0; shocks = 0; acts = []; idx = [0]; obs = [obs0]
    next_assess = ca.DT; last_review = -9.0; reviews = 0; accepted = False; dec = []; next_dec = 0.0
    while not accepted and c < ca.CMAX:
        # acceptance review
        last_in = obs[-1][0] >= TARGET[0] and obs[-1][1] >= TARGET[1]
        if (in_target(Kh, Mh) or last_in) and c - last_review >= 1.0 - 1e-9:
            c += C_CONF; reviews += 1; last_review = c
            o = np.clip(np.array([K, M]) + crng.normal(0, ca.NOISE, 2), 0, 1)
            if o[0] >= TARGET[0] + margin and o[1] >= TARGET[1] + margin:
                accepted = True; break
            idx.append(len(acts)); obs.append(o)
            if known: Kh, Mh = o
            else:
                theta = ca.fit(acts, idx, np.array(obs), theta, rs); policy, pf = ca.make_policy(theta, kind)
                Kh, Mh = ca.replay(theta, acts)[-1]
            continue
        a = policy(Kh, Mh, {"c": c})
        if c >= next_dec - 1e-9:
            dec.append(dict(c=round(c, 1), K=float(K), M=float(M), a=a, a_opt=OPT_TRUE(K, M, {}),
                            Kneed_hat=float(min(K_need(pf), 1.5)), Kneed=float(K_need(P)))); next_dec += 1.0
        fk, fm, h = rates(K, M, a, P)
        if rng.random() < min(h * 0.1, 1):
            K = max(K - P["dK"], 0); M = max(M - P["dM"], 0); c += P["rework"]; shocks += 1
            Kh = max(Kh - P["dK"], 0); Mh = max(Mh - P["dM"], 0); a = a + "!"
        else:
            K = min(K + fk * 0.1, 1); M = min(M + fm * 0.1, 1)
            fkh, fmh, _ = rates(Kh, Mh, a, pf); Kh = min(Kh + fkh * 0.1, 1); Mh = min(Mh + fmh * 0.1, 1)
        c += 0.1; acts.append(a)
        if c >= next_assess - 1e-9:
            idx.append(len(acts)); obs.append(np.clip(np.array([K, M]) + nrng.normal(0, ca.NOISE, 2), 0, 1))
            if known: Kh, Mh = obs[-1]
            else:
                theta = ca.fit(acts, idx, np.array(obs), theta, rs); policy, pf = ca.make_policy(theta, kind)
                Kh, Mh = ca.replay(theta, acts)[-1]
            next_assess = c + ca.DT
    return dict(cost=float(c), shocks=shocks, reviews=reviews, accepted=accepted,
                premature=bool(accepted and not in_target(K, M)), K_end=float(K), M_end=float(M),
                deficit=float(max(TARGET[0] - K, 0) + max(TARGET[1] - M, 0)), decisions=dec)

def run(args):
    rep, margin = args
    ck = f"rev1/_stop_{margin}_{rep}.json"
    if os.path.exists(ck): return json.load(open(ck))
    out = {"rep": rep, "margin": margin}
    for kind in ("dp_known", "dp", "headroom"):
        out[kind] = run_project(rep, kind, margin)
    out["ref_oracle"] = dict(cost=float(ca.simulate(OPT_TRUE, rng=np.random.default_rng(5000 + rep))[0]))
    json.dump(out, open(ck, "w")); return out

if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    margins = [float(x) for x in (sys.argv[2].split(",") if len(sys.argv) > 2 else ["0", "0.03"])]
    with Pool(2) as pool:
        res = pool.map(run, [(r, m) for m in margins for r in range(R)], chunksize=1)
    summ = {}
    for m in margins:
        rr = [r for r in res if r["margin"] == m]; ref = np.array([r["ref_oracle"]["cost"] for r in rr])
        s = {"ref_oracle_mean": float(ref.mean())}
        for kind in ("dp_known", "dp", "headroom"):
            c = np.array([r[kind]["cost"] for r in rr]); acc = np.array([r[kind]["accepted"] for r in rr])
            pm = np.array([r[kind]["premature"] for r in rr]); dfc = np.array([r[kind]["deficit"] for r in rr])
            decs = [d for r in rr for d in r[kind]["decisions"]]
            agree = np.array([d["a"] == d["a_opt"] for d in decs]) if decs else np.array([])
            s[kind] = dict(mean=float(c.mean()), excess_vs_oracle=float(100 * (c.mean() / ref.mean() - 1)),
                           reviews_mean=float(np.mean([r[kind]["reviews"] for r in rr])),
                           not_accepted=int((~acc).sum()), premature_rate=float(pm.mean()),
                           deficit_when_premature=float(dfc[pm].mean()) if pm.any() else 0.0,
                           decision_agreement=float(agree.mean()) if decs else None)
            if decs and kind != "dp_known":
                marg = np.array([d["K"] - d["Kneed_hat"] for d in decs]); err = np.array([abs(d["Kneed_hat"] - d["Kneed"]) for d in decs])
                bins = [(-9, -0.15), (-0.15, -0.05), (-0.05, 0.05), (0.05, 0.15), (0.15, 9)]
                s[kind]["agreement_by_margin"] = {f"{a}..{b}": [float(agree[(marg >= a) & (marg < b)].mean()) if ((marg >= a) & (marg < b)).any() else None,
                                                               int(((marg >= a) & (marg < b)).sum())] for a, b in bins}
                s[kind]["Kneed_abs_error_median"] = float(np.median(err))
        summ[str(m)] = s
    json.dump({"C_CONF": C_CONF, "summary": summ}, open("rev1/stopping.json", "w"), indent=1)
    print(json.dumps(summ, indent=1))
