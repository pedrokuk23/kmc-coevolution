"""Alternative functional forms, Eq. (19) (Sec. V-E, Table 8), and discretization check (Sec. V-A)."""
import json, numpy as np, sys
from multiprocessing import Pool
from kmc_model import *

VARIANTS = {
    "Base model": {},
    "Power-law ceilings": dict(kpow=0.5, mpow=2.0, ml=1.0),
    "Knowledge-scaled test rate": dict(trate_b=0.3, trate_k=1.0),
    "Exponential shock hazard": dict(haz="exp", haz_c=0.7225 / np.exp(-0.45)),
    "Simulation maturity credit": dict(sim_mcredit=0.10),
    "All four combined": dict(kpow=0.5, mpow=2.0, ml=1.0, trate_b=0.3, trate_k=1.0,
                              haz="exp", haz_c=0.7225 / np.exp(-0.45), sim_mcredit=0.10),
}

def run_variant(name, n=1000):
    p = dict(P); p.update(VARIANTS[name])
    g, V, pol, Q = solve_dp(p=p)
    pols = {"dp": make_dp_policy(g, pol, Q),
            "headroom": lambda K, M, h: policy_procedure(K, M, h, p=p),
            "coupled": lambda K, M, h: policy_coupled(K, M, h, p=p),
            "gap": lambda K, M, h: policy_derivative(K, M, h, p=p),
            "slope": lambda K, M, h: policy_slope(K, M, h, p=p),
            "analysis_first": lambda K, M, h: policy_analysis_first(K, M, h, p=p),
            "test_first": lambda K, M, h: policy_test_first(K, M, h, p=p),
            "spiral": policy_spiral}
    out = {"variant": name, "K_need": K_need(p)}
    for k, f in pols.items():
        rng = np.random.default_rng(7)
        r = np.array([simulate(f, p=p, rng=rng) for _ in range(n)])
        out[k] = float(r[:, 0].mean()); out[k + "_nr"] = float(np.mean(r[:, 0] >= 200))
    return out

def run_grid(args):
    n, dc = args
    g, V, pol, Q = solve_dp(n=n, dc=dc)
    from scipy.ndimage import map_coordinates
    v0 = float(map_coordinates(V, [[X0[0] * (n - 1)], [X0[1] * (n - 1)]], order=1)[0])
    f = make_dp_policy(g, pol, Q)
    # deterministic switch to T
    K, M = X0; c = 0; kT = None
    while not in_target(K, M, tol=0.005) and c < 100:
        a = f(K, M, {}); fk, fm, h = rates(K, M, a)
        if a == "T" and kT is None: kT = K
        K = min(K + fk * dc, 1); M = min(M + fm * dc, 1); c += dc
    rng = np.random.default_rng(3)
    mc = float(np.mean([simulate(f, dc=dc, rng=rng)[0] for _ in range(500)]))
    return {"n": n, "dc": dc, "V_x0": v0, "K_switch_T": kT, "mc_cost": mc}

if __name__ == "__main__":
    with Pool(2) as pool:
        var = pool.map(run_variant, list(VARIANTS))
        grid = pool.map(run_grid, [(81, 0.1), (121, 0.05), (121, 0.1), (121, 0.2), (161, 0.1)])
    json.dump({"variants": var, "grid": grid}, open("robustness.json", "w"), indent=1)
    for v in var:
        print(v["variant"], round(v["K_need"], 3), {k: round(100 * (v[k] / v["dp"] - 1), 1) for k in
              ["headroom", "coupled", "gap", "slope", "analysis_first", "test_first", "spiral"]}, "dp", round(v["dp"], 1),
              {k: v[k + "_nr"] for k in ["test_first", "slope", "analysis_first"]})
    for gg in grid: print(gg)
