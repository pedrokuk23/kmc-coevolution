import json, numpy as np
from kmc_model import *
from robustness import run_variant, VARIANTS
# data-informed: lambda_T = 0.90 BU^-1 (FAA 1980-2002 first flights), knowledge gain per BU of integrated testing 0.97(1-K)^2.5 (Cross & Vesely 2018)
VARIANTS["Launch-data informed"] = dict(lamT=0.90, tk_g=0.97, tk_q=2.5)
VARIANTS["Launch-data hazard only"] = dict(lamT=0.90)
out = [run_variant(k) for k in ["Launch-data hazard only", "Launch-data informed"]]
for v in out:  # restricted procedure: knowledge built only by S or E (Sec. VI-B)
    p = dict(P); p.update(VARIANTS[v["variant"]]); rng = np.random.default_rng(7)
    r = np.array([simulate(lambda K, M, h: policy_procedure_SE(K, M, h, p=p), p=p, rng=rng) for _ in range(1000)])
    v["headroom_SE"] = float(r[:, 0].mean())
json.dump(out, open("launch_variant.json", "w"), indent=1)
for v in out:
    print(v["variant"], "dp", round(v["dp"],1), {k: round(100*(v[k]/v["dp"]-1),1) for k in ["headroom","coupled","gap","slope","analysis_first","test_first","spiral"]}, {k:v[k+"_nr"] for k in ["test_first","slope"]})
