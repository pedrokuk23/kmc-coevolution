"""Data-informed variants of Sec. VI-B (Table 8, last rows) -> launch_variant.json.
lambda_T = 0.90 BU^-1 from FAA (2005) first-flight data; flight learning g(1-K)^q with g = 0.97 BU^-1, q = 2.5,
fitted to Cross and Vesely (2018) in the range K ~ 0.72-0.91 (conditional on reading their estimates as knowledge).
Rows: hazard only (new developer, K0 = 0.15); flight learning extrapolated from K0 = 0.15; flight learning from
experienced-developer knowledge (K0 = 0.57, FAA; K0 = 0.72, Cross and Vesely); flight learning applied only within
the fitted range (K >= 0.72; base gain below) from K0 = 0.15."""
import json, numpy as np
from kmc_model import *
from robustness import run_variant, VARIANTS
VARIANTS["Launch-data hazard only"] = dict(lamT=0.90)
VARIANTS["Launch-data informed"] = dict(lamT=0.90, tk_g=0.97, tk_q=2.5)
VARIANTS["Launch-data informed, fitted range only"] = dict(lamT=0.90, tk_g=0.97, tk_q=2.5, tk_kmin=0.72)
ROWS = [("Launch-data hazard only", 0.15), ("Launch-data informed", 0.15), ("Launch-data informed", 0.57),
        ("Launch-data informed", 0.72), ("Launch-data informed, fitted range only", 0.15)]
out = []
for name, k0 in ROWS:
    x0 = (k0, 0.10)
    v = run_variant(name, x0=x0); v["K0"] = k0
    p = dict(P); p.update(VARIANTS[name]); rng = np.random.default_rng(7)
    # restricted procedure: knowledge built only by S or E
    r = np.array([simulate(lambda K, M, h: policy_procedure_SE(K, M, h, p=p), p=p, x0=x0, rng=rng) for _ in range(1000)])
    v["headroom_SE"] = float(r[:, 0].mean())
    out.append(v)
json.dump(out, open("launch_variant.json", "w"), indent=1)
for v in out:
    print(v["variant"], v["K0"], "dp", round(v["dp"], 1), {k: round(100 * (v[k] / v["dp"] - 1), 1) for k in
          ["headroom", "headroom_SE", "coupled", "gap", "slope", "analysis_first", "test_first", "spiral"]})
