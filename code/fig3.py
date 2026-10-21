# Figure 3: optimal KMC curve (base scenario): policy map, rates and slope versus required slope.
import json, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import matplotlib.patheffects as pe
from kmc_model import *
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.linewidth": 0.8, "savefig.dpi": 300})
C = {"S": "#0072B2", "E": "#009E73", "T": "#D55E00", "ink": "#222222", "mut": "#777777"}
g, V, pol, Q = solve_dp(); dp = make_dp_policy(g, pol, Q)
def det(policy, p=P, dc=0.1):
    K, M = X0; c = 0; tr = [(0, K, M, policy(K, M, {"c": 0}))]
    while not in_target(K, M, tol=0.005) and c < 150:
        a = policy(K, M, {"c": c}); fk, fm, h = rates(K, M, a, p)
        K = min(K+fk*dc, 1); M = min(M+fm*dc, 1); c += dc; tr.append((c, K, M, a))
    return tr
def arr(tr): return (np.array([t[0] for t in tr]), np.array([t[1] for t in tr]), np.array([t[2] for t in tr]), [t[3] for t in tr])
c_o, K_o, M_o, A_o = arr(det(dp))
sw = [i for i in range(1, len(A_o)) if A_o[i] != A_o[i-1]]
# alternative scenario optimal curve (cheap, safe tests)
p2 = dict(P); p2.update(rT=0.44, lamT=0.20)
g2, V2, pol2, Q2 = solve_dp(p=p2)
c2, K2, M2, A2 = arr(det(make_dp_policy(g2, pol2, Q2), p=p2))
sw2 = [(round(c2[i],1), A2[i-1], A2[i], round(K2[i],3), round(M2[i],3)) for i in range(1, len(A2)) if A2[i] != A2[i-1]]
print("cheap-test switches", sw2, "cost", c2[-1])

fig, ax = plt.subplots(1, 3, figsize=(7.16, 2.75), gridspec_kw={"width_ratios": [1.05, 1, 1]})
a = ax[0]
a.imshow(np.ma.masked_where(pol < 0, pol).T, origin="lower", extent=[0, 1, 0, 1],
         cmap=ListedColormap([C["S"], C["E"], C["T"]]), vmin=0, vmax=2, alpha=0.25, aspect="equal")
a.contour(g, g, np.ma.masked_where(pol < 0, pol).T, levels=[0.5, 1.5], colors=C["ink"], linewidths=0.6)
a.add_patch(plt.Rectangle(TARGET, 1-TARGET[0], 1-TARGET[1], fc="none", ec=C["ink"], lw=1.0, ls="--"))
a.text(0.88, 0.93, "$X_f$", ha="center", va="center", fontsize=7.5)
mm = np.linspace(0, 1, 50); a.plot(Kbar(mm), mm, color=C["mut"], lw=0.9, ls=":")
a.text(0.47, 0.03, r"$\bar K(M)$", color=C["mut"], fontsize=7.5)
kk = np.linspace(0, 1, 50); a.plot(kk, Mbar(kk), color=C["mut"], lw=0.9, ls="-.")
a.text(0.08, 0.25, r"$\bar M(K)$", color=C["mut"], fontsize=7.5, rotation=45)
a.plot(K2, M2, color=C["ink"], lw=0.9, ls="--")
a.text(0.70, 0.62, "cheap\ntests", fontsize=6.5, color=C["ink"], ha="right")
a.plot(K_o, M_o, color="white", lw=4.0, solid_capstyle="round")
for i in range(1, len(c_o)):
    a.plot(K_o[i-1:i+1], M_o[i-1:i+1], color=C[A_o[i]], lw=2.2, solid_capstyle="round")
a.plot(*X0, "o", ms=5.5, mfc="white", mec=C["ink"])
for i in sw: a.plot(K_o[i], M_o[i], "s", ms=4.5, mfc="white", mec=C["ink"])
a.text(0.18, 0.62, "S", color=C["S"], fontsize=10, weight="bold")
a.text(0.55, 0.12, "E", color=C["E"], fontsize=10, weight="bold")
a.text(0.87, 0.35, "T", color=C["T"], fontsize=10, weight="bold")
a.set_xlim(0, 1); a.set_ylim(0, 1); a.set_xlabel("Knowledge $K$"); a.set_ylabel("Maturity $M$")
a.set_title("(a) Policy map and KMC curve", fontsize=8.5, loc="left")
dK = np.gradient(K_o, c_o); dM = np.gradient(M_o, c_o)
b = ax[1]
b.plot(c_o, dK, color=C["S"], lw=1.6); b.plot(c_o, dM, color=C["T"], lw=1.6, ls="--")
b.text(3, 0.075, "$dK/dc$", color=C["S"]); b.text(15.5, 0.085, "$dM/dc$", color=C["T"])
for i in sw: b.axvline(c_o[i], color=C["mut"], lw=0.7, ls=":")
b.set_ylim(0, 0.12); b.set_xlabel("Cumulative cost (BU)"); b.set_ylabel("Gain per BU")
b.set_title("(b) Marginal rates", fontsize=8.5, loc="left")
c = ax[2]
s = np.where(dK > 1e-4, dM/np.maximum(dK, 1e-4), np.nan)
c.semilogy(c_o, s, color=C["ink"], lw=1.4)
Sreq = (TARGET[1]-M_o)/np.maximum(TARGET[0]-K_o, 1e-3)
ok = K_o < TARGET[0]-0.02
c.semilogy(c_o[ok], Sreq[ok], color=C["mut"], lw=1.0, ls="--")
c.text(1.0, 2.6, r"$S_{req}$", color=C["mut"], fontsize=8)
c.text(6, 0.12, r"$dM/dK$", color=C["ink"], fontsize=8)
for i in sw: c.axvline(c_o[i], color=C["mut"], lw=0.7, ls=":")
c.set_ylim(0.01, 100); c.set_xlabel("Cumulative cost (BU)"); c.set_ylabel("Slope (log scale)")
c.set_title("(c) Slope vs required slope", fontsize=8.5, loc="left")
fig.tight_layout(); fig.savefig("../figures/Fig3.png"); fig.savefig("../figures/Fig3.pdf"); plt.close(fig)
