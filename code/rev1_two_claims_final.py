"""Revision 1, R1.4: Sec. V-G recomputed on the finest grid of the convergence study (46^4, dc = 0.5 BU),
all policies on the same 2000 random streams (paired), 95% bootstrap intervals for the excess over the optimum.
Writes two_claims.json in the format read by the manuscript build, plus the intervals."""
import json, os, numpy as np
from multiprocessing import Pool
from scipy.ndimage import map_coordinates
import two_claims as tc

N = int(os.environ.get("NRUNS", 2000)); NG = int(os.environ.get("NG", 46)); DC = float(os.environ.get("DC", 0.5))
_P = {}
def _ev(a):
    nm, i = a
    return tc.simulate(_P[nm], np.random.default_rng(1000 + i))

if __name__ == "__main__":
    g, V, Q, it = tc.solve(n=NG, dc=DC)
    _P.update({"Optimal (dynamic programming)": tc.dp_policy(g, Q), "Headroom, weakest link": tc.headroom_weakest,
               "Headroom, averaged knowledge": tc.headroom_average, "Analysis-first": tc.analysis_first, "Test-first": tc.test_first})
    with Pool(2) as pool:
        R = {k: np.array(pool.map(_ev, [(k, i) for i in range(N)], chunksize=50)) for k in _P}
    ref = R["Optimal (dynamic programming)"][:, 0]
    out = {"grid": NG, "dc": DC, "runs": N, "V_x0": float(map_coordinates(V, [[tc.X0[k] * (NG - 1)] for k in range(4)], order=1)[0]),
           "K_need": [tc.K_need(tc.PS[0]), tc.K_need(tc.PS[1])], "policies": {}}
    rng = np.random.default_rng(5)
    for k, r in R.items():
        d = (r[:, 0] - ref) / ref.mean() * 100
        bs = [d[j].mean() for j in (rng.integers(0, N, N) for _ in range(4000))]
        out["policies"][k] = dict(mean=float(r[:, 0].mean()), p90=float(np.percentile(r[:, 0], 90)), shocks=float(r[:, 1].mean()),
                                  nr=float(np.mean(r[:, 0] >= 250)), excess_pct=float((r[:, 0].mean() / ref.mean() - 1) * 100),
                                  excess_ci95=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))])
        print(k, out["policies"][k], flush=True)
    for k, f in [("weakest", tc.headroom_weakest), ("average", tc.headroom_average)]:
        x = tc.X0.copy(); c = 0
        while not tc.done(x + 0.005) and c < 100:
            a = f(x, {})
            if a == "T": out[f"first_T_{k}"] = dict(c=round(c, 1), x=[round(float(v), 3) for v in x]); break
            x = np.clip(x + tc.step(x, a)[0] * 0.1, 0, 1); c += 0.1
    json.dump(out, open("rev1/two_claims_final.json", "w"), indent=1)
