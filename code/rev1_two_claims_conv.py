"""Revision 1, R1.4: grid convergence of the four-dimensional dynamic program (Sec. V-G) and a confidence
interval for the cost gap between the weakest-link headroom procedure and the optimal policy.
Paired Monte Carlo: run i of every policy uses the same random stream (seed 1000+i)."""
import json, sys, time, numpy as np
from multiprocessing import Pool
from scipy.ndimage import map_coordinates
import two_claims as tc

N_RUNS = 2000
import os
GRIDS = [tuple(float(x) if "." in x else int(x) for x in g.split(":")) for g in os.environ.get("GRIDS", "21:0.5,26:0.5,31:0.5,36:0.5,41:0.5,46:0.5,36:0.25").split(",")]

def run_pair(args):
    pol, i = args
    return tc.simulate(pol, np.random.default_rng(1000 + i))[0]

_POL = {}
def _eval(args):
    name, i = args
    return tc.simulate(_POL[name], np.random.default_rng(1000 + i))[0]

if __name__ == "__main__":
    out = {"runs": N_RUNS, "grids": []}
    hw = None
    for n, dc in GRIDS:
        t0 = time.time(); g, V, Q, it = tc.solve(n=n, dc=dc)
        v0 = float(map_coordinates(V, [[tc.X0[k] * (n - 1)] for k in range(4)], order=1)[0])
        _POL.clear(); _POL["dp"] = tc.dp_policy(g, Q); _POL["hw"] = tc.headroom_weakest
        with Pool(2) as pool:
            cdp = np.array(pool.map(_eval, [("dp", i) for i in range(N_RUNS)], chunksize=50))
            if hw is None: hw = np.array(pool.map(_eval, [("hw", i) for i in range(N_RUNS)], chunksize=50))
        diff = (hw - cdp) / cdp.mean() * 100
        rng = np.random.default_rng(5); bs = [ (hw[j].mean() - cdp[j].mean()) / cdp[j].mean() * 100 for j in (rng.integers(0, N_RUNS, N_RUNS) for _ in range(4000))]
        rec = dict(n=n, dc=dc, iters=int(it), secs=round(time.time() - t0, 1), V_x0=v0, dp_mean=float(cdp.mean()), dp_sem=float(cdp.std(ddof=1) / np.sqrt(N_RUNS)),
                   hw_mean=float(hw.mean()), gap_pct=float((hw.mean() - cdp.mean()) / cdp.mean() * 100),
                   gap_ci95=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))])
        out["grids"].append(rec); print(rec, flush=True)
        json.dump(out, open(os.environ.get("OUT", "rev1/two_claims_convergence.json"), "w"), indent=1)
