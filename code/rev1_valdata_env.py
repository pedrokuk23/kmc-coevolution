"""Revision 1, R1.1 (second round): the validation-data state D over the literature-anchored envelope.
All runs start from the base initial state X0 (and D0 = 0.10), not from the initial maturity sampled by envelope.draw.

For the first NSETS reachable parameter sets of envelope.py (Sec. V-D), the three-dimensional model of
rev1_valdata.py is solved on a 41^3 grid (targets on grid nodes) with integrated tests supplying data at their maturity
rate (rho_T = r_T) and separate-effects tests supplying it slowly (rho_E = 0.05) or fast (rho_E = 0.40). Policies:
opt3 (optimum of the extended model), opt2 (optimum of the base model, ignores D), head_D (Table 6 with the true
rates), head_DD2 (headroom with the look-ahead knowledge step, a finding of Sec. V-H, not part of Table 6; data from E or T; rates known). 300 paired runs per policy and set.
Also, high data supply from integrated tests (rho_T = 0.50) and strong knowledge credit of integrated tests
(e_T = 0.25) in the base set (R2.4)."""
import json, sys, numpy as np
from multiprocessing import Pool
import rev1_valdata as v, rev1_valdata_rule2 as vr2, envelope as env
from kmc_model import P, TARGET, solve_dp

NG = 41; NR = 300
_G = {}
def _job(a):
    nm, i = a
    return v.sim3(_G["pols"][nm], _G["p"], np.random.default_rng(20_000 + i))[0]

def evaluate(p):
    g3, V3, Q3, it = v.solve3(p, n=NG); g2, V2, pol2, Q2 = solve_dp(p=p)
    pols = v.make_policies(p, g3, Q3, g2, pol2, Q2, 0.75)
    pols = {"opt3": pols["opt3"], "opt2": pols["opt2"], "head_D": pols["head_D"], "head_DD2": vr2.make_head_DD2(p, pols["head_D"]),
            "test_first": pols["test_first"]}
    _G["pols"] = pols; _G["p"] = p
    with Pool(2) as pool:
        res = {nm: np.array(pool.map(_job, [(nm, i) for i in range(NR)], chunksize=30)) for nm in pols}
    ref = res["opt3"].mean()
    return {nm: float(100 * (r.mean() / ref - 1)) for nm, r in res.items()} | {"opt3_mean": float(ref)}

if __name__ == "__main__":
    NSETS = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    out = {"grid": NG, "runs": NR, "base_variants": {}, "envelope": []}
    for name, upd in [("base, rhoE=0.40 (41^3 grid check)", dict(rhoE=0.40, rhoT=0.22)), ("base, rhoE=0.05", dict(rhoE=0.05, rhoT=0.22)),
                      ("base, rhoE=0.05, rhoT=0.50", dict(rhoE=0.05, rhoT=0.50)),
                      ("base, rhoE=0.05, rhoT=0.50, eT=0.25", dict(rhoE=0.05, rhoT=0.50, eT=0.25)),
                      ("base, rhoE=0.40, rhoT=0.50, eT=0.25", dict(rhoE=0.40, rhoT=0.50, eT=0.25))]:
        p = dict(P); p.update(upd); out["base_variants"][name] = evaluate(p); print(name, out["base_variants"][name], flush=True)
    seed = 0
    while len(out["envelope"]) < NSETS:
        p, x0 = env.draw(seed); seed += 1
        if p["mb"] + p["ml"] < TARGET[1] + 0.02: continue
        rec = {"seed": seed - 1}
        for rhoE in (0.05, 0.40):
            q = dict(p); q.update(rhoE=rhoE, rhoT=p["rT"]); rec[str(rhoE)] = evaluate(q)
        out["envelope"].append(rec); print(rec, flush=True)
        json.dump(out, open("rev1/valdata_env.json", "w"), indent=1)
