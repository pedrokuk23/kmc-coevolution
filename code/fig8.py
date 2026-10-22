"""Flowchart: applying KMC (headroom procedure, Table 6, inside the calibration loop, Table 11)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 6.6, "savefig.dpi": 300})
W, H = 106, 140
fig = plt.figure(figsize=(3.3, 3.3 * H / W))
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")

def box(x, y, w, h, t, fc="#F4F4F2", ec="#6B6B6B", bold=False, tc="black"):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0,rounding_size=1.5",
                                fc=fc, ec=ec, lw=0.7))
    ax.text(x, y, t, ha="center", va="center", fontweight="bold" if bold else "normal", color=tc, linespacing=1.25)

def dia(x, y, w, h, t):
    ax.add_patch(Polygon([(x - w / 2, y), (x, y + h / 2), (x + w / 2, y), (x, y - h / 2)], closed=True,
                         fc="#FFF3E6", ec="#C8572A", lw=0.8))
    ax.text(x, y, t, ha="center", va="center", linespacing=1.2)

def arr(pts, dashed=False, color="#333333"):
    for (x0, y0), (x1, y1) in zip(pts[:-2], pts[1:-1]):
        ax.plot([x0, x1], [y0, y1], color=color, lw=0.7, ls="--" if dashed else "-")
    ax.annotate("", xy=pts[-1], xytext=pts[-2],
                arrowprops=dict(arrowstyle="-|>", lw=0.7, color=color, ls="--" if dashed else "-",
                                shrinkA=0, shrinkB=0, mutation_scale=6))

def lab(x, y, t, ha="left"):
    ax.text(x, y, t, ha=ha, va="center", style="italic", color="#444444", fontsize=6.2)

# nodes
box(50, 133, 70, 8, "Priors from public data (Table 11, step 2)", fc="#ECECEC")
box(50, 120, 80, 10, "Define claim, target region $X_f$, and cost,\nschedule, and exposure limits")
box(50, 107, 80, 8, "Assess $K$, $M$, and cumulative cost (Table 11, step 1)")
box(50, 94, 80, 10, "Fit rates and ceilings of (8)–(10); update $\\bar{K}$, $\\bar{M}$,\nand $K_{need}$ (Table 6, step 2; Table 11, steps 3–4)")
dia(50, 79, 30, 12, "$x \\in X_f$?")
box(84, 79, 24, 9, "Decision\ncheckpoint", fc="#1F3A5F", ec="#1F3A5F", bold=True, tc="white")
box(16, 79, 30, 11, "Reduce exposure,\nbuild knowledge,\nor re-approve (3b)", fc="#F4F4F2")
box(50, 66, 64, 9, "Screen (4): cost, schedule, $h_i$, exposure;\nretain admissible activities (step 0)", fc="#FFFFFF", ec="#1F3A5F")
dia(50, 51, 28, 12, "$K \\geq K_{need}$?")
dia(16, 51, 28, 12, "Hazard\nwithin limit?")
box(16, 37, 26, 9, "Integrated\ntest T (step 3)", fc="#F7E1D3", ec="#C8572A")
box(84, 51, 26, 16, "Most productive\nadmissible\nS, E, or T, net\nof shock (step 4)", fc="#DCE8F3", ec="#1D5B8F")
box(50, 24, 80, 8, "Execute; record result, cost, and any shock")
box(50, 9, 80, 9, "Track fitted coefficients across projects and\nprocess changes (Table 11, step 6)", fc="#ECECEC")

# arrows, main spine
arr([(50, 129), (50, 125)]); arr([(50, 115), (50, 111)]); arr([(50, 103), (50, 99)])
arr([(50, 89), (50, 85)])
arr([(65, 79), (72, 79)]); lab(66, 81.5, "yes")
arr([(50, 73), (50, 70.5)]); lab(51.5, 72, "no")
arr([(50, 61.5), (50, 57)])
arr([(36, 51), (30, 51)]); lab(31, 53.5, "yes")
arr([(64, 51), (71, 51)]); lab(64.6, 53.6, "no")
arr([(16, 45), (16, 41.5)]); lab(17.5, 43.2, "yes")
arr([(16, 57), (16, 73.5)]); lab(17.5, 59.5, "no")
arr([(16, 84.5), (16, 89)])                     # 3b -> re-fit
arr([(16, 32.5), (16, 28)])
arr([(84, 43), (84, 28)])
# loop back to assessment
arr([(90, 24), (100, 24), (100, 107), (90, 107)], color="#C8572A")
ax.text(102.2, 65, "reassess after each result or saturation (step 5)",
        rotation=90, ha="left", va="center", color="#C8572A", fontsize=6.0)
arr([(50, 20), (50, 13.5)], dashed=True, color="#777777")

fig.savefig("../figures/Fig8.png"); fig.savefig("../figures/Fig8.pdf"); plt.close(fig)
