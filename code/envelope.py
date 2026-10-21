"""Literature-anchored parameter envelope: robustness of decision rules (Section V-D)."""
import numpy as np, json, sys
from multiprocessing import Pool
from kmc_model import *

def draw(seed):
    rng = np.random.default_rng(1000 + seed)
    p = dict(P)
    fef = rng.uniform(0.55, 0.85)                 # MIL-HDBK-189C Table I range of fix effectiveness
    p["ml"] = 1.05 * fef / 0.70                   # knowledge-limited ceiling slope scaled by FEF
    p["mb"] = rng.uniform(0.0, 0.15)
    p["lamT"] = rng.uniform(0.40, 1.40)           # early integrated-test failure frequency (X-43A 1/3 ... Falcon 1 3/4)
    p["rS"] = rng.uniform(0.05, 0.40)             # weak (F-1 type) to strong predictive simulation
    p["kb"] = rng.uniform(0.10, 0.50)
    p["kl"] = rng.uniform(0.40, 0.80)
    p["rT"] = rng.uniform(0.12, 0.45)
    p["rE"] = rng.uniform(0.05, 0.15)
    p["rework"] = rng.uniform(1.0, 4.0)
    m0 = rng.uniform(0.05, 0.30)
    return p, (0.15, m0)

def run(seed, n=150):
    p, x0 = draw(seed)
    # target must be reachable: Mbar(1) >= Mreq
    if p["mb"] + p["ml"] < TARGET[1] + 0.02:
        return None
    g, V, pol, Q = solve_dp(p=p)
    pols = {"dp": make_dp_policy(g, pol, Q),
            "headroom": lambda K, M, h: policy_procedure(K, M, h, p=p),
            "coupled": lambda K, M, h: policy_coupled(K, M, h, p=p),
            "slope": lambda K, M, h: policy_slope(K, M, h, p=p),
            "analysis_first": lambda K, M, h: policy_analysis_first(K, M, h, p=p),
            "test_first": lambda K, M, h: policy_test_first(K, M, h, p=p),
            "spiral": policy_spiral}
    out = {"seed": seed, "params": {k: float(v) for k, v in p.items()}, "x0": x0}
    for k, f in pols.items():
        rng = np.random.default_rng(seed)
        r = np.array([simulate(f, p=p, x0=x0, rng=rng) for _ in range(n)])
        out[k] = float(r[:, 0].mean()); out[k + "_nr"] = float(np.mean(r[:, 0] >= 200))
    return out

if __name__ == "__main__":
    N = int(sys.argv[1])
    with Pool(2) as pool:
        res = [r for r in pool.map(run, range(N)) if r is not None]
    json.dump(res, open("envelope.json", "w"), indent=0)
    print(len(res))
