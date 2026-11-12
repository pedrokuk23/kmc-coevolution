"""Revision 1, R1.4 (second round): Sec. V-G table on the grid whose optimal policy had the lowest simulated cost in
rev1_two_claims_conv2.py (terminal test on the successor state), all policies on the same independent streams
(seeds 50000 + i). Gaps are relative to that best policy (a lower bound on the gap to the exact optimum).
Writes rev1/two_claims_final2.json (format of two_claims.json, plus intervals)."""
import json, os, numpy as np
from multiprocessing import Pool
from scipy.ndimage import map_coordinates
import two_claims as tc
from rev1_two_claims_conv2 import solve_cont, SEED0

C = json.load(open("rev1/two_claims_convergence2.json")); N = C["runs"]
best = min(C["grids"], key=lambda r: r["mean"])
_P = {}
def _ev(a):
    nm, i = a
    return tc.simulate(_P[nm], np.random.default_rng(SEED0 + i))

if __name__ == "__main__":
    g, V, Q, it = solve_cont(best["n"], best["dc"])
    _P.update({"Optimal (dynamic programming)": tc.dp_policy(g, Q), "Headroom, weakest link": tc.headroom_weakest,
               "Headroom, averaged knowledge": tc.headroom_average, "Analysis-first": tc.analysis_first, "Test-first": tc.test_first})
    with Pool(2) as pool:
        R = {k: np.array(pool.map(_ev, [(k, i) for i in range(N)], chunksize=100)) for k in _P}
    ref = R["Optimal (dynamic programming)"][:, 0]
    assert abs(ref.mean() - best["mean"]) < 1e-6, (ref.mean(), best["mean"])
    out = {"grid": best["n"], "dc": best["dc"], "runs": N, "seed0": SEED0, "V_x0": best["V_x0"], "policies": {}}
    rng = np.random.default_rng(5)
    for k, r in R.items():
        d = (r[:, 0] - ref) / ref.mean() * 100
        bs = [d[j].mean() for j in (rng.integers(0, N, N) for _ in range(4000))]
        out["policies"][k] = dict(mean=float(r[:, 0].mean()), p90=float(np.percentile(r[:, 0], 90)), shocks=float(r[:, 1].mean()),
                                  nr=float(np.mean(r[:, 0] >= 250)), excess_pct=float((r[:, 0].mean() / ref.mean() - 1) * 100),
                                  excess_ci95=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))])
        print(k, out["policies"][k], flush=True)
    # gap of the weakest-link procedure against each grid's policy (same streams)
    hw = np.array(C["fixed"]["Headroom, weakest link"])
    out["gap_by_grid"] = [dict(n=r["n"], dc=r["dc"], dp_mean=r["mean"], gap_pct=float(100 * (hw.mean() / r["mean"] - 1))) for r in C["grids"]]
    for k, f in [("weakest", tc.headroom_weakest), ("average", tc.headroom_average)]:
        x = tc.X0.copy(); c = 0
        while not tc.done(x + 0.005) and c < 100:
            a = f(x, {})
            if a == "T": out[f"first_T_{k}"] = dict(c=round(c, 1), x=[round(float(v), 3) for v in x]); break
            x = np.clip(x + tc.step(x, a)[0] * 0.1, 0, 1); c += 0.1
    json.dump(out, open("rev1/two_claims_final2.json", "w"), indent=1)
