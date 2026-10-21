# Figure 5: mean cost relative to the optimum over the parameter envelope (reads envelope.json).
import json, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7.5, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.linewidth": 0.7, "savefig.dpi": 300})
E = json.load(open("envelope.json"))
names = [("headroom", "Headroom procedure"), ("coupled", "Coupling-aware rule"), ("spiral", "Fixed alternation"),
         ("analysis_first", "Analysis-first"), ("slope", "Naive slope rule"), ("test_first", "Test-first")]
fig, a = plt.subplots(figsize=(3.5, 2.2))
for i, (k, lab) in enumerate(names):
    r = np.array([e[k] / e["dp"] for e in E])
    lo, med, hi = np.percentile(r, [10, 50, 90])
    col = "#0072B2" if k == "headroom" else "#555555"
    a.plot([lo, hi], [i, i], color=col, lw=1.6, solid_capstyle="round")
    a.plot(med, i, "o", color=col, ms=5)
    a.text(hi * 1.08, i, (f"{100*(med-1):.1f}%" if med < 1.1 else f"{100*(med-1):.0f}%"), va="center", fontsize=7, color="#222222")
a.set_xscale("log"); a.axvline(1, color="#999999", lw=0.8, ls="--")
a.set_yticks(range(len(names))); a.set_yticklabels([n[1] for n in names]); a.invert_yaxis()
a.set_xlabel("Mean cost / optimal cost (log scale)")
a.set_xticks([1, 1.5, 2, 3, 5, 10]); a.set_xticklabels(["1", "1.5", "2", "3", "5", "10"])
a.set_xlim(0.9, 14)
fig.tight_layout(); fig.savefig("../figures/Fig5.png"); fig.savefig("../figures/Fig5.pdf")
print({k: [round(x, 3) for x in np.percentile([e[k] / e["dp"] for e in E], [10, 50, 90])] for k, _ in names})
