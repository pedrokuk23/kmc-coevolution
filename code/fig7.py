# Figure 7: KMC saturating dynamics fitted to NIST reliability-growth data (reads relgrowth.json).
import json, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from relgrowth import DATA
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7.5, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.linewidth": 0.7, "savefig.dpi": 300})
R = json.load(open("relgrowth.json"))
fig, axs = plt.subplots(1, 2, figsize=(3.5, 1.9), sharey=True)
for ax, (name, (t, T)), lab in zip(axs, DATA.items(), ["(a) Dataset 1", "(b) Dataset 2"]):
    r = R[name]; k = r["kmc"]; p = r["powerlaw"]
    tt = np.linspace(0.5, T, 400)
    Lk = k["a"] * ((1 - k["m"]) * tt + k["m"] * (1 - np.exp(-k["r"] * tt)) / k["r"])
    Lp = p["lam"] * tt ** p["beta"]
    ax.step([0] + list(t) + [T], list(range(len(t) + 1)) + [len(t)], where="post", color="#222222", lw=1.0, label="Observed")
    ax.plot(tt, Lk, color="#0072B2", lw=1.5, label="KMC saturating")
    ax.plot(tt, Lp, color="#D55E00", lw=1.2, ls="--", label="Crow–AMSAA")
    ax.set_title(lab, fontsize=7.5, loc="left"); ax.set_xlabel("Test time (h)")
axs[0].set_ylabel("Cumulative failures"); axs[0].set_yticks(range(0, 11, 2)); axs[0].legend(frameon=False, fontsize=6.5, loc="upper left")
fig.tight_layout(); fig.savefig("../figures/Fig7.png"); fig.savefig("../figures/Fig7.pdf")
