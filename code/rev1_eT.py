"""Revision 1, R2.4: integrated tests as a major source of knowledge. Sweep of the knowledge credit e_T of
integrated tests in the base model (Table 5 otherwise): optimum of (12), headroom procedure (Table 6), test-first,
analysis-first, 2000 paired runs; share of the optimal policy map assigned to T and K at the first test."""
import json, numpy as np
from multiprocessing import Pool
from kmc_model import P, X0, solve_dp, make_dp_policy, policy_procedure, policy_test_first, policy_analysis_first, simulate, K_need

N = 2000; _G = {}
def _job(a):
    nm, i = a
    return simulate(_G[nm], p=_G["p"], rng=np.random.default_rng(30_000 + i))[0]

if __name__ == "__main__":
    out = []
    for eT in (0.04, 0.08, 0.15, 0.25, 0.40):
        p = dict(P); p["eT"] = eT
        g, V, pol, Q = solve_dp(p=p)
        _G.update(p=p, dp=make_dp_policy(g, pol, Q), headroom=lambda K, M, h, p=p: policy_procedure(K, M, h, p=p),
                  test_first=lambda K, M, h, p=p: policy_test_first(K, M, h, p=p),
                  analysis_first=lambda K, M, h, p=p: policy_analysis_first(K, M, h, p=p))
        with Pool(2) as pool:
            res = {nm: np.array(pool.map(_job, [(nm, i) for i in range(N)], chunksize=100)) for nm in ("dp", "headroom", "test_first", "analysis_first")}
        ref = res["dp"].mean()
        K, M = X0; c = 0.0; f = _G["dp"]   # deterministic path of the optimum: K at the first test
        from kmc_model import rates, in_target
        firstT = None
        while not in_target(K, M, tol=0.005) and c < 100:
            a = f(K, M, {});
            if a == "T" and firstT is None: firstT = round(K, 3)
            fk, fm, h = rates(K, M, a, p); K = min(K + fk * 0.1, 1); M = min(M + fm * 0.1, 1); c += 0.1
        rec = dict(eT=eT, dp_mean=float(ref), K_need=float(K_need(p)), K_first_T_opt=firstT,
                   share_T_map=float(np.mean(pol[pol >= 0] == 2)),
                   excess={nm: float(100 * (r.mean() / ref - 1)) for nm, r in res.items() if nm != "dp"})
        out.append(rec); print(rec, flush=True)
    json.dump(out, open("rev1/eT_sweep.json", "w"), indent=1)
