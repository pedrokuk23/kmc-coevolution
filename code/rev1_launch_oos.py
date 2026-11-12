"""Revision 1, R2.1: out-of-sample check of the launch-data hazard (protocol: rev1/launch_oos_protocol.md).
Predictions fixed from the FAA 1980-2002 calibration of Sec. VI-B; records 2003-2025 in rev1/launch_oos_records.csv."""
import csv, json, numpy as np
from scipy.stats import binomtest
LAM, CF = 0.90, 2.0
PRED = {g: 1 - np.exp(-LAM * (1 - K) ** 2 * CF) for g, K in (("N", 0.15), ("E", 0.57))}
R = list(csv.DictReader(open("rev1/launch_oos_records.csv")))
def stats(rows):
    out = {}
    for g in ("N", "E"):
        rr = [r for r in rows if r["group"] == g]; n = len(rr); f = sum(r["outcome"].lower().startswith("f") for r in rr)
        bt = binomtest(f, n, PRED[g]); ci = bt.proportion_ci(0.90, "exact")
        out[g] = dict(n=n, failures=f, share=f / n, ci90=[ci.low, ci.high], predicted=float(PRED[g]), p_value=bt.pvalue)
    return out
amb = lambda r: r["ambiguous"].strip().lower() in ("yes", "y", "true", "1")
res = {"all": stats(R), "unambiguous_only": stats([r for r in R if not amb(r)])}
json.dump(res, open("rev1/launch_oos.json", "w"), indent=1); print(json.dumps(res, indent=1))
