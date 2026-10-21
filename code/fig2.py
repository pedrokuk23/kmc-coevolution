# Figure 2: path screening with a hypothetical terminal region (schematic).
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12, "savefig.dpi": 300})
A, B, C, RED = "#0072B2", "#E69F00", "#222222", "#BD302A"
fig, ax = plt.subplots(figsize=(6.7, 4.0))
ax.grid(color="#e6e6e6", lw=0.8); ax.set_axisbelow(True)
ax.add_patch(plt.Rectangle((0.78, 0.76), 0.22, 0.24, fc="#ececec", ec="#555555", lw=1.2, ls="--"))
ax.text(0.765, 0.955, "Terminal region", ha="right", va="top", fontsize=11, color="#444444")
def path(pts, col, mk, ls="-"):
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="-|>,head_length=0.6,head_width=0.3", color=col, lw=2.2, ls=ls, shrinkA=0, shrinkB=2))
    ax.plot([p[0] for p in pts], [p[1] for p in pts], mk, color=col, ms=6, ls="none", zorder=4)
def disc(p0, p1):
    ax.annotate("", xy=p1, xytext=p0, arrowprops=dict(arrowstyle="-|>,head_length=0.6,head_width=0.3", color=RED, lw=2.6, ls=(0, (4, 2.5)), shrinkA=0, shrinkB=4))
    ax.plot(*p1, "o", ms=8, mfc="white", mec=RED, mew=2, zorder=5)
s = (0.12, 0.10)
# path A: no discrepancy
path([s, (0.54, 0.19), (0.72, 0.43), (0.89, 0.88)], A, "o")
# path B: early integrated test, discrepancy, recovery
path([s, (0.31, 0.68)], B, "s"); disc((0.31, 0.68), (0.08, 0.27)); path([(0.08, 0.27), (0.58, 0.72), (0.85, 0.84)], B, "s")
# path C: discrepancy after analysis, recovery
path([s, (0.63, 0.51)], C, "^"); disc((0.63, 0.51), (0.42, 0.24)); path([(0.42, 0.24), (0.68, 0.66), (0.81, 0.80)], C, "^")
ax.plot(*s, "o", color="#555555", ms=7, zorder=6)
ax.text(0.545, 0.135, "A", color=A, fontsize=13, weight="bold")
ax.text(0.325, 0.69, "B", color=B, fontsize=13, weight="bold")
ax.text(0.645, 0.47, "C", color=C, fontsize=13, weight="bold")
ax.text(0.035, 0.96, "Red dashed arrows:\nreassessment after discrepancy", va="top", fontsize=11, color=RED)
ax.set_xlim(0, 1); ax.set_ylim(0, 1)
ax.set_xlabel("Validated knowledge $K$"); ax.set_ylabel("Evidence-backed maturity $M$")
fig.tight_layout(); fig.savefig("../figures/Fig2.png"); fig.savefig("../figures/Fig2.pdf"); plt.close(fig)
