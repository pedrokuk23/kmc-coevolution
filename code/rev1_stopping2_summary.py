"""Summary of rev1_stopping2.py runs -> rev1/stopping2.json (Sec. V-F, S3.2-S3.3)."""
import json, glob, numpy as np
import calib_adaptive as ca
from kmc_model import make_dp_policy
OPT = make_dp_policy(ca.G0, ca.POL0, ca.Q0)
R = [json.load(open(f)) for f in glob.glob("rev1/ck/_s2_*.json")]
reps = sorted({r["rep"] for r in R})
ORACLE = {i: float(ca.simulate(OPT, rng=np.random.default_rng(5000 + i))[0]) for i in reps}
rng = np.random.default_rng(11)
def boot(x, f=np.mean, B=2000):
    x = np.asarray(x); b = [f(x[rng.integers(0, len(x), len(x))]) for _ in range(B)]
    return [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))]
def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [float(c - h), float(c + h)]
out = {"oracle_mean": float(np.mean(list(ORACLE.values()))), "conditions": {}}
groups = {}
for r in R: groups.setdefault((r["noise"], r["margin"], r["kind"]), []).append(r)
for (noise, margin, kind), rr in sorted(groups.items()):
    rr = sorted(rr, key=lambda r: r["rep"]); n = len(rr)
    orc = np.array([ORACLE[r["rep"]] for r in rr])
    rec = {"n": n, "noise": noise, "margin": margin, "kind": kind, "reviews_mean": float(np.mean([r["reviews"] for r in rr])),
           "not_accepted": int(sum(not r["accepted"] for r in rr))}
    k = sum(r["premature"] for r in rr); rec["premature_rate"] = k / n; rec["premature_ci95"] = wilson(k, n)
    dfc = [r["deficit"] for r in rr if r["premature"]]; rec["deficit_when_premature"] = float(np.mean(dfc)) if dfc else 0.0
    for C in (0.5, 1.0, 2.0):
        tot = np.array([r["cost_act"] + C * r["reviews"] for r in rr])
        ex = (tot - orc) / orc.mean() * 100
        rec[f"C{C}"] = dict(mean=float(tot.mean()), mean_ci95=boot(tot), excess_vs_oracle=float(100 * (tot.mean() / orc.mean() - 1)), excess_ci95=boot(ex))
    D = [d for r in rr for d in r["decisions"]]
    if D:
        ag = np.array([d["a"] == d["a_true"] for d in D]); tm = np.array([d["K"] - d["Kneed"] for d in D])
        em = np.array([d["Kh"] - d["Kneed_hat"] for d in D]); sd = np.array([d["sd"] for d in D])
        bins = [(-9, -0.15), (-0.15, -0.03), (-0.03, 0.03), (0.03, 0.15), (0.15, 9)]
        rec["agreement"] = float(ag.mean()); rec["decisions"] = len(D)
        rec["agreement_by_true_margin"] = {f"{a}..{b}": [float(ag[(tm >= a) & (tm < b)].mean()) if ((tm >= a) & (tm < b)).any() else None, int(((tm >= a) & (tm < b)).sum())] for a, b in bins}
        rec["agreement_by_est_margin"] = {f"{a}..{b}": [float(ag[(em >= a) & (em < b)].mean()) if ((em >= a) & (em < b)).any() else None, int(((em >= a) & (em < b)).sum())] for a, b in bins}
        if kind != "dp_known":
            ok = np.isfinite(sd) & (sd > 0)
            out_band = ok & (np.abs(em) > 2 * sd); in_band = ok & ~out_band
            rec["criterion_2sd"] = dict(share_outside=float(out_band[ok].mean()), agree_outside=float(ag[out_band].mean()) if out_band.any() else None,
                                        agree_inside=float(ag[in_band].mean()) if in_band.any() else None, sd_median=float(np.median(sd[ok])))
            # observable alternative: standard deviation of the K_need estimates recorded at the decision points of the
            # last 6 BU (time window c_i - 6 <= c <= c_i; about two assessments and their re-fits)
            ags, ems, chs = [], [], []
            for r in rr:
                D_ = r["decisions"]
                for i, d in enumerate(D_):
                    w = [x["Kneed_hat"] for x in D_[: i + 1] if x["c"] >= d["c"] - 6.0 - 1e-9]
                    if len(w) > 2: ags.append(d["a"] == d["a_true"]); ems.append(d["Kh"] - d["Kneed_hat"]); chs.append(np.std(w))
            ags, ems, chs = map(np.array, (ags, ems, chs)); ob = np.abs(ems) > 2 * chs
            rec["criterion_refit_2s"] = dict(share_outside=float(ob.mean()), agree_outside=float(ags[ob].mean()), agree_inside=float(ags[~ob].mean()),
                                             s_median=float(np.median(chs)))
            rec["Kneed_abs_error_median"] = float(np.median([abs(d["Kneed_hat"] - d["Kneed"]) for d in D]))
    out["conditions"][f"{noise}|{margin}|{kind}"] = rec
# Information-matched comparison (second round): headroom with estimated coefficients against the same rule with the
# coefficients known and the same information (known_hr). For each margin of the estimating procedure, the reference is
# the cheapest known-coefficient condition whose premature-acceptance rate is equal or lower (same noise level).
out["matched"] = {}
for noise in sorted({v["noise"] for v in out["conditions"].values()}):
    est = [v for v in out["conditions"].values() if v["noise"] == noise and v["kind"] == "headroom"]
    kn = [v for v in out["conditions"].values() if v["noise"] == noise and v["kind"] == "known_hr"]
    rows = []
    for e in sorted(est, key=lambda v: v["margin"]):
        ok = [k for k in kn if k["premature_rate"] <= e["premature_rate"] + 1e-12]
        if not ok: continue
        k = min(ok, key=lambda v: v["C1.0"]["mean"])
        rows.append(dict(margin=e["margin"], premature_est=e["premature_rate"], cost_est=e["C1.0"]["mean"],
                         known_margin=k["margin"], premature_known=k["premature_rate"], cost_known=k["C1.0"]["mean"],
                         excess_pct=100 * (e["C1.0"]["mean"] / k["C1.0"]["mean"] - 1)))
    out["matched"][str(noise)] = rows
json.dump(out, open("rev1/stopping2.json", "w"), indent=1)
for k, v in out["conditions"].items():
    print(k, v["n"], round(v["C1.0"]["mean"], 2), round(v["C1.0"]["excess_vs_oracle"], 1), round(v["premature_rate"], 3), v["not_accepted"],
          round(v.get("agreement", 0), 3), v.get("criterion_2sd"))
print("oracle", out["oracle_mean"])
