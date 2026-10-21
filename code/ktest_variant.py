"""Variant of the headroom procedure that resolves Table 6 step 3b by building knowledge until
K >= K_test = max(K_need, K_haz) (wait_haz=True). Reproduces the numbers quoted at the end of Sec. V-D."""
import json, numpy as np
from kmc_model import *
from robustness import VARIANTS
VARIANTS = dict(VARIANTS); VARIANTS["Launch-data hazard (lamT = 0.90)"] = dict(lamT=0.90)
E = json.load(open("envelope.json"))          # parameter sets and DP costs of Sec. V-D
h = []
for e in E:
    p = e["params"]; x0 = tuple(e["x0"]); rng = np.random.default_rng(e["seed"])
    rr = np.array([simulate(lambda K, M, hh: policy_procedure(K, M, hh, p=p, wait_haz=True), p=p, x0=x0, rng=rng) for _ in range(150)])
    h.append(100 * (rr[:, 0].mean() / e["dp"] - 1))
h = np.array(h); out = {"envelope": dict(median=float(np.median(h)), p90=float(np.percentile(h, 90)), max=float(h.max()))}
LV = json.load(open("launch_variant.json"))[0]   # launch-data hazard only: DP cost
p = dict(P); p.update(lamT=0.90); rng = np.random.default_rng(7)
rr = np.array([simulate(lambda K, M, hh: policy_procedure(K, M, hh, p=p, wait_haz=True), p=p, rng=rng) for _ in range(1000)])
out["launch_hazard_only"] = 100 * (rr[:, 0].mean() / LV["dp"] - 1)
json.dump(out, open("ktest_variant.json", "w"), indent=1); print(out)
