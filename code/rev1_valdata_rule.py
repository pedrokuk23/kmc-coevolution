"""Revision 1, R1.1 (continued): a data-aware knowledge step for the headroom procedure.

When separate-effects tests supply validation data faster than demonstration does, the optimum of the
three-dimensional model builds the data first (E), then simulates up to the new ceiling (S), then tests (T). The
greedy knowledge step of Table 6 (most productive activity now) misses this. The data-aware step projects, with the
fitted rates and without shocks, the cost to reach K_target = max(K_need, K_req) along two knowledge plans and takes
the first activity of the cheaper one:
  greedy      the knowledge step of Table 6;
  data-first  separate-effects tests until the data ceiling Kbar(D) clears K_target + delta, then the greedy step,
              for delta in {0.02, 0.05, 0.10, 0.15, 0.20, 0.25} (the projection picks the best margin).
The test gate (step 3) is unchanged. No dynamic program is needed: two deterministic projections per decision.
"""
import json, sys, numpy as np
from multiprocessing import Pool
import rev1_valdata as v
from kmc_model import P, TARGET, X0, K_need, solve_dp, hazard

DELTAS = (0.02, 0.05, 0.10, 0.15, 0.20, 0.25)

def project(K, M, D, p, delta, Kt, dc=0.1, cmax=60.0):
    """Projected cost (BU, expected rework included) to reach K_target; delta=None is the greedy plan."""
    c = 0.0
    while K < Kt and c < cmax:
        if delta is not None and v.Kbar_D(D, p) < Kt + delta and p["rhoE"] > 0: a = "E"
        else:
            a = max(("S", "E", "T"), key=lambda b: float(v.rates3(K, M, D, b, p)[0]) - float(v.rates3(K, M, D, b, p)[3]) * p["dK"])
        fk, fm, fd, h = v.rates3(K, M, D, a, p)
        K = min(K + float(fk) * dc, 1); M = min(M + float(fm) * dc, 1); D = min(D + float(fd) * dc, 1); c += dc + float(h) * dc * p["rework"]
    return c

def make_head_DD(p, base):
    Kn = K_need(p); Kt = max(Kn, TARGET[0])
    def f(K, M, D, haz_max=0.05):
        gK, gM = max(TARGET[0] - K, 0), max(TARGET[1] - M, 0)
        if gM > 0 and K >= Kn - 1e-9 and float(hazard(K, p["lamT"], p)) <= haz_max: return "T"
        if gK > 0 or K < Kn:
            if v.Kbar_D(D, p) < Kt + max(DELTAS):
                g = project(K, M, D, p, None, Kt)
                if any(v.Kbar_D(D, p) < Kt + d and project(K, M, D, p, d, Kt) < g for d in DELTAS): return "E"
            return base(K, M, D)
        return "T"
    return f

_G = {}
def _job(args):
    nm, i = args
    return v.sim3(_G["pols"][nm], _G["p"], np.random.default_rng(10_000 + i))

if __name__ == "__main__":
    nruns = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    out = []
    for name, upd in v.CASES[1:]:
        p = dict(P); p.update(upd)
        g3, V3, Q3, it = v.solve3(p); g2, V2, pol2, Q2 = solve_dp(p=p)
        pols = v.make_policies(p, g3, Q3, g2, pol2, Q2, 0.75)
        pols = {"opt3": pols["opt3"], "head_D": pols["head_D"], "head_DD": make_head_DD(p, pols["head_D"])}
        _G["pols"] = pols; _G["p"] = p
        with Pool(2) as pool:
            res = {nm: np.array(pool.map(_job, [(nm, i) for i in range(nruns)], chunksize=25)) for nm in pols}
        ref = res["opt3"][:, 0]; rec = dict(case=name, policies={})
        for nm, r in res.items():
            d = (r[:, 0] - ref) / ref.mean() * 100; rng = np.random.default_rng(3)
            bs = [d[j].mean() for j in (rng.integers(0, nruns, nruns) for _ in range(2000))]
            rec["policies"][nm] = dict(mean=float(r[:, 0].mean()), excess_pct=float((r[:, 0].mean() / ref.mean() - 1) * 100),
                                       excess_ci95=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))])
        out.append(rec); print(json.dumps(rec), flush=True)
        json.dump(out, open("rev1/valdata_rule.json", "w"), indent=1)
