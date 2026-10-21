# Figure 4: cost to reach the terminal region by policy (base scenario, 2000 runs).
import json, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from kmc_model import *
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.linewidth": 0.8, "savefig.dpi": 300})
g, V, pol, Q = solve_dp()
pols = {"Analysis-first (Vee-like)": policy_analysis_first,
        "Test-first (RID-DE-like)": policy_test_first,
        "Fixed alternation (Spiral-like)": policy_spiral,
        "Naive slope rule": policy_slope,
        "Gap-weighted derivative rule": policy_derivative,
        "Coupling-aware derivative rule": policy_coupled,
        "Headroom procedure (Table 6)": policy_procedure,
        "Optimal (dynamic programming)": make_dp_policy(g, pol, Q)}
base = {}
for k, f in pols.items():
    rng = np.random.default_rng(7)
    base[k] = np.array([simulate(f, rng=rng) for _ in range(2000)])
stats = {k: dict(mean=float(r[:, 0].mean()), p10=float(np.percentile(r[:, 0], 10)),
                        p90=float(np.percentile(r[:, 0], 90)), shocks=float(r[:, 1].mean())) for k, r in base.items()}
fig, a = plt.subplots(figsize=(7.16, 3.2))
names = list(base.keys())
bp = a.boxplot([base[k][:, 0] for k in names], vert=False, whis=(5, 95), showfliers=False, widths=0.55,
               patch_artist=True, medianprops=dict(color="#222222", lw=1.4))
for i, bx in enumerate(bp["boxes"]):
    n = names[i]
    bx.set_facecolor("#F6D7C3" if ("Optimal" in n or "Headroom" in n) else ("#CFE3F0" if "rule" in n else "#E6E6E6"))
    bx.set_edgecolor("#222222"); bx.set_linewidth(0.8)
for i, k in enumerate(names):
    a.text(np.percentile(base[k][:, 0], 95) + 2, i+1,
           f"mean {base[k][:,0].mean():.1f} BU · {base[k][:,1].mean():.1f} shocks", va="center", fontsize=7.5)
a.set_yticks(range(1, len(names)+1)); a.set_yticklabels(names)
a.set_xlabel("Cost to reach the terminal region (BU); whiskers: 5th–95th percentiles")
a.set_xlim(0, 105); a.invert_yaxis()
fig.tight_layout(); fig.savefig("../figures/Fig4.png"); fig.savefig("../figures/Fig4.pdf"); plt.close(fig)
for k in names: print(k, stats[k])
