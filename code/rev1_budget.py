"""Revision 1, R2.5 (and R1.3): a fixed budget as a finite horizon.

Cost is the independent variable of (8), so a budget B is a finite horizon of B/dc steps. The budget-aware policy
maximizes the probability of reaching X_f before the budget is spent: W_b(x) = max_a [(1 - p_a) W_{b-1}(x + f_a dc)
+ p_a W_{b-1-rho/dc}(x - delta)], W = 1 on X_f, W_b = 0 for b <= 0 outside X_f, solved by backward induction on a
241^2 grid (finer than the 121^2 grid of (12); on 121^2 numerical diffusion of the sharp success front made the
policy noticeably suboptimal) (targets on grid nodes; a successor within 0.005 of X_f counts as success, the tolerance used by
the simulator). The headroom procedure is also run with its test gate raised to K_need + delta (delta = 0.03, 0.06, 0.10),
the remedy suggested by the results. Differences in success probability against the budget-aware policy are paired
(same streams), with 95% bootstrap intervals. The cost-optimal policy of (12), the
headroom procedure (Table 6), and the tuned two-phase threshold are evaluated on the same random streams with the
same budget: the share of projects that reach X_f within B. Budgets: 1.0, 1.25 and 1.5 times the mean cost of the
cost-optimal policy. Schedule enters the same way when activity durations are proportional to cost."""
import json, os, sys, numpy as np
from multiprocessing import Pool
from scipy.ndimage import map_coordinates
from kmc_model import P, TARGET, X0, ACTS, rates, in_target, solve_dp, make_dp_policy, policy_procedure, policy_threshold

DC = 0.1; N = int(os.environ.get("NRUNS", 4000)); n = int(os.environ.get("NGRID", 241))
SCEN = {"Base": ({}, 0.75), "Costly, risky tests": (dict(lamT=0.80, rework=4.0), 0.775)}   # K_th tuned (extensions.json)

TOL = 0.005
def headroom_gate(K, M, h, p, delta):
    """Table 6 with the test gate raised from K_need to K_need + delta."""
    from kmc_model import K_need
    gK, gM = max(TARGET[0] - K, 0), max(TARGET[1] - M, 0); Kg = K_need(p) + delta
    if gM > 0 and K >= Kg - 1e-9 and float(rates(K, M, "T", p)[2]) <= 0.05: return "T"
    if gK > 0 or K < Kg:
        return max(["S", "E", "T"], key=lambda a: float(rates(K, M, a, p)[0]) - float(rates(K, M, a, p)[2]) * p["dK"])
    return "T"

def solve_budget(p, B):
    g = np.linspace(0, 1, n); K, M = np.meshgrid(g, g, indexing="ij"); term = in_target(K, M, tol=TOL)
    nb = int(round(B / DC)); R = int(round(p["rework"] / DC))
    pre = []
    for a in ACTS:
        fk, fm, h = rates(K, M, a, p); pr = np.minimum(h * DC, 1.0)
        Kn, Mn = np.clip(K + fk * DC, 0, 1), np.clip(M + fm * DC, 0, 1)
        pre.append(([Kn.ravel() * (n - 1), Mn.ravel() * (n - 1)], in_target(Kn, Mn, tol=TOL), pr,
                    [np.clip(K - p["dK"], 0, 1).ravel() * (n - 1), np.clip(M - p["dM"], 0, 1).ravel() * (n - 1)]))
    W = np.zeros((nb + 1, n, n), np.float32); A = np.zeros((nb + 1, n, n), np.int8); W[:, term] = 1.0
    for b in range(1, nb + 1):
        Qs = []
        for cn, tn, pr, cs in pre:
            wn = np.where(tn, 1.0, map_coordinates(W[b - 1], cn, order=1, mode="nearest").reshape(n, n))
            ws = map_coordinates(W[b - 1 - R], cs, order=1, mode="nearest").reshape(n, n) if b - 1 - R >= 0 else 0.0
            Qs.append((1 - pr) * wn + pr * ws)
        Qs = np.stack(Qs); W[b] = np.where(term, 1.0, Qs.max(0)); A[b] = Qs.argmax(0)
    return g, W, A

def run(args):
    kind, sc, B, i = args
    p = dict(P); p.update(SCEN[sc][0]); rng = np.random.default_rng(70000 + i)
    K, M = X0; c = 0.0; firstT = None
    while not in_target(K, M, tol=0.005) and c < B - 1e-9:
        if kind == "budget":
            a = budget_action(sc, B, p, K, M, c)
        else:
            a = _POL[(kind, sc)](K, M, {})
        if a == "T" and firstT is None: firstT = (round(c, 1), round(K, 3))
        fk, fm, h = rates(K, M, a, p)
        if rng.random() < min(h * DC, 1):
            K = max(K - p["dK"], 0); M = max(M - p["dM"], 0); c += p["rework"]
        else:
            K = min(K + fk * DC, 1); M = min(M + fm * DC, 1)
        c += DC
    ok = bool(in_target(K, M, tol=0.005)) and c <= B + 1e-9
    return ok, c, firstT

_A, _POL = {}, {}

def budget_action(sc, B, p, K, M, c):
    """Action that maximizes the probability of success with the remaining budget, from the stored W_b (linear
    interpolation at the successor states); near-ties (within 1e-4, e.g. when success is certain) are broken by the
    cost-optimal policy of (12)."""
    W = _A[(sc, B)]; b = int(round((B - c) / DC)); R = int(round(p["rework"] / DC))
    if b <= 0: return _POL[("dp", sc)](K, M, {})
    q = []
    for a in ACTS:
        fk, fm, h = rates(K, M, a, p); pr = min(float(h) * DC, 1.0)
        Kn, Mn = min(K + float(fk) * DC, 1), min(M + float(fm) * DC, 1)
        wn = 1.0 if in_target(Kn, Mn, tol=TOL) else float(map_coordinates(W[b - 1], [[Kn * (n - 1)], [Mn * (n - 1)]], order=1, mode="nearest")[0])
        Ks, Ms = max(K - p["dK"], 0), max(M - p["dM"], 0)
        ws = float(map_coordinates(W[b - 1 - R], [[Ks * (n - 1)], [Ms * (n - 1)]], order=1, mode="nearest")[0]) if b - 1 - R >= 0 else 0.0
        q.append((1 - pr) * wn + pr * ws)
    best = max(q); a_dp = _POL[("dp", sc)](K, M, {})
    return a_dp if q[ACTS.index(a_dp)] >= best - 1e-4 else ACTS[int(np.argmax(q))]
if __name__ == "__main__":
    out = {}
    for sc, (upd, kth) in SCEN.items():
        p = dict(P); p.update(upd)
        g, V, pol, Q = solve_dp(p=p)
        _POL[("dp", sc)] = make_dp_policy(g, pol, Q)
        _POL[("headroom", sc)] = lambda K, M, h, p=p: policy_procedure(K, M, h, p=p)
        _POL[("threshold", sc)] = lambda K, M, h, p=p, k=kth: policy_threshold(K, M, h, p=p, Kstar=k)
        for dl in (0.03, 0.06, 0.10):
            _POL[(f"headroom+{dl}", sc)] = lambda K, M, h, p=p, dl=dl: headroom_gate(K, M, h, p, dl)
        with Pool(2) as pool:   # mean cost of the cost-optimal policy (no budget)
            cmean = float(np.mean([r[1] for r in pool.map(run, [("dp", sc, 1e9, i) for i in range(N)], chunksize=200)]))
        out[sc] = {"E_C_opt": cmean, "budgets": {}}
        for f in (1.0, 1.25, 1.5):
            B = round(f * cmean, 1); g, W, A = solve_budget(p, B); _A[(sc, B)] = W
            v0 = float(map_coordinates(W[-1], [[X0[0] * (n - 1)], [X0[1] * (n - 1)]], order=1)[0])
            rec = {"B": B, "W_x0": v0, "policies": {}}
            with Pool(2) as pool:
                ok_all = {}
                for kind in ("budget", "dp", "headroom", "threshold", "headroom+0.03", "headroom+0.06", "headroom+0.1"):
                    r = pool.map(run, [(kind, sc, B, i) for i in range(N)], chunksize=200)
                    okv = np.array([x[0] for x in r], float); ok_all[kind] = okv
                    ft = [x[2] for x in r if x[2] is not None]
                    rec["policies"][kind] = dict(p_success=float(okv.mean()), se=float(okv.std(ddof=1) / np.sqrt(N)),
                        first_T_K_median=float(np.median([x[1] for x in ft])) if ft else None,
                        first_T_c_median=float(np.median([x[0] for x in ft])) if ft else None)
            rb = np.random.default_rng(9)
            for kind, okv in ok_all.items():
                d = ok_all["budget"] - okv
                bs = [d[j].mean() for j in (rb.integers(0, N, N) for _ in range(2000))]
                rec["policies"][kind]["diff_vs_budget_aware"] = [float(d.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
            out[sc]["budgets"][str(f)] = rec; print(sc, f, json.dumps(rec), flush=True)
            json.dump(out, open("rev1/budget2.json", "w"), indent=1)
