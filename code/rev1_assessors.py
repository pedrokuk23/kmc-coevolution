"""Revision 1, R2.2: sensitivity of activity selection to assessor disagreement (coefficients known).

K and M are assessed every 3 BU by an assessor whose score differs from the true state by a random error (sd sigma,
a fresh assessor each time) and/or a persistent bias. On the rubric of Table 4 (K = sum kappa_j / 20), a one-level
disagreement on one criterion moves K by 0.05. Between assessments the decision maker uses the state predicted by
the (known) model from the last assessment. Acceptance uses the same review rule as rev1_stopping.py (confirmation
assessment of cost C_CONF, accepted when it reads at least the target). Reported for the headroom procedure and the
optimal policy: excess cost over the same policy with the true state observed, agreement of each decision with the
decision at the true state, share of integrated tests started while the true K < K_need, premature acceptance.
"""
import json, numpy as np
from multiprocessing import Pool
from kmc_model import P, TARGET, X0, rates, in_target, solve_dp, make_dp_policy, policy_procedure, K_need, simulate

C_CONF, DT, CMAX, N = 1.0, 3.0, 60.0, 600
G0, V0, POL0, Q0 = solve_dp()
POLS = {"headroom": lambda K, M: policy_procedure(K, M, {}), "optimal": (lambda f: (lambda K, M: f(K, M, {})))(make_dp_policy(G0, POL0, Q0))}
CONDS = [("sd 0.05", 0.05, (0, 0)), ("sd 0.10", 0.10, (0, 0)), ("K bias +0.05", 0.0, (0.05, 0)),
         ("K bias -0.05", 0.0, (-0.05, 0)), ("K,M bias +0.05", 0.0, (0.05, 0.05)), ("sd 0.05, K bias +0.05", 0.05, (0.05, 0))]
KN = K_need(P)

def run(args):
    pname, sd, bias, rep = args
    pol = POLS[pname]; rng = np.random.default_rng(5000 + rep); arng = np.random.default_rng(9000 + rep)
    assess = lambda K, M: np.clip(np.array([K, M]) + np.array(bias) + arng.normal(0, sd, 2) * (sd > 0), 0, 1)
    K, M = X0; Kh, Mh = assess(K, M); c = 0.0; nxt = DT; last_rev = -9; accepted = False
    agree = []; early_T = 0; nT = 0; prem = False
    while not accepted and c < CMAX:
        if in_target(Kh, Mh) and c - last_rev >= 1.0 - 1e-9:
            c += C_CONF; last_rev = c; o = assess(K, M)
            if o[0] >= TARGET[0] and o[1] >= TARGET[1]: accepted = True; prem = not in_target(K, M); break
            Kh, Mh = o; continue
        a = pol(Kh, Mh); agree.append(a == pol(K, M))
        if a == "T": nT += 1; early_T += K < KN - 1e-9
        fk, fm, h = rates(K, M, a, P)
        if rng.random() < min(h * 0.1, 1):
            K = max(K - P["dK"], 0); M = max(M - P["dM"], 0); c += P["rework"]; Kh = max(Kh - P["dK"], 0); Mh = max(Mh - P["dM"], 0)
        else:
            K = min(K + fk * 0.1, 1); M = min(M + fm * 0.1, 1)
            fkh, fmh, _ = rates(Kh, Mh, a, P); Kh = min(Kh + fkh * 0.1, 1); Mh = min(Mh + fmh * 0.1, 1)
        c += 0.1
        if c >= nxt - 1e-9: Kh, Mh = assess(K, M); nxt = c + DT
    return dict(cost=c, agree=float(np.mean(agree)), early_T=early_T / max(nT, 1), premature=prem, accepted=accepted)

def ref(args):
    pname, rep = args
    return simulate(lambda K, M, h: POLS[pname](K, M), rng=np.random.default_rng(5000 + rep))[0] + C_CONF

if __name__ == "__main__":
    out = {"runs": N, "C_CONF": C_CONF, "K_need": KN, "results": {}}
    with Pool(2) as pool:
        refs = {p: np.array(pool.map(ref, [(p, r) for r in range(N)], chunksize=50)) for p in POLS}
        for cname, sd, bias in CONDS:
            for p in POLS:
                rr = pool.map(run, [(p, sd, bias, r) for r in range(N)], chunksize=25)
                c = np.array([x["cost"] for x in rr])
                out["results"][f"{cname} | {p}"] = dict(mean=float(c.mean()), excess_vs_true_state=float(100 * (c.mean() / refs[p].mean() - 1)),
                    decision_agreement=float(np.mean([x["agree"] for x in rr])), early_test_share=float(np.mean([x["early_T"] for x in rr])),
                    premature_acceptance=float(np.mean([x["premature"] for x in rr])), not_accepted=int(sum(not x["accepted"] for x in rr)))
                print(cname, p, out["results"][f"{cname} | {p}"], flush=True)
    out["ref_true_state_plus_review"] = {p: float(v.mean()) for p, v in refs.items()}
    json.dump(out, open("rev1/assessors.json", "w"), indent=1)
