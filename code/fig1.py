# Figure 1: schematic evidence update and recovery for one claim in the K-M plane.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.linewidth": 0.8, "savefig.dpi": 300})
BLUE, RED = "#0072B2", "#BD302A"
P = {"init": (0.18, 0.15), "before": (0.53, 0.30), "after": (0.43, 0.23), "assim": (0.68, 0.52), "further": (0.85, 0.77)}
fig, ax = plt.subplots(figsize=(3.5, 2.5))
ax.grid(color="#e8e8e8", lw=0.6); ax.set_axisbelow(True)
def arr(a, b, col, ls="-"):
    ax.annotate("", xy=P[b], xytext=P[a], arrowprops=dict(arrowstyle="-|>,head_length=0.5,head_width=0.25",
                color=col, lw=1.6, ls=ls, shrinkA=3, shrinkB=4))
arr("init", "before", BLUE); arr("before", "after", RED, (0, (3, 2))); arr("after", "assim", BLUE); arr("assim", "further", BLUE)
for k, (x, y) in P.items():
    ax.plot(x, y, "o", ms=5, color=RED if k == "after" else BLUE, mfc="white" if k == "after" else BLUE, mew=1.4, zorder=5)
lab = {"init": ("Initial", (0.0, -0.07), "center"), "before": ("Before test", (0.03, -0.06), "left"),
       "after": ("After discrepancy\n(epistemic shock)", (-0.03, 0.09), "right"),
       "assim": ("After assimilation\n(recovery)", (0.03, -0.06), "left"), "further": ("Further\ndemonstration", (-0.04, 0.03), "right")}
for k, (t, (dx, dy), ha) in lab.items():
    ax.text(P[k][0] + dx, P[k][1] + dy, t, ha=ha, va="center", fontsize=7.5, color=RED if k == "after" else "#222222")
ax.set_xlim(0, 1); ax.set_ylim(0, 1)
ax.set_xlabel("Validated knowledge $K$"); ax.set_ylabel("Evidence-backed maturity $M$")
fig.tight_layout(); fig.savefig("../figures/Fig1.png"); fig.savefig("../figures/Fig1.pdf"); plt.close(fig)
