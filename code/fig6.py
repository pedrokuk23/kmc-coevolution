# Figure 6: estimating the KMC curve from noisy assessment history (synthetic).
import json, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from scipy.optimize import least_squares
import kmc_model as km
from kmc_model import *

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.linewidth": 0.8, "savefig.dpi": 300})
C = {"S": "#0072B2", "E": "#009E73", "T": "#D55E00", "ink": "#222222", "mut": "#777777"}
OUT = {}
NMC = 2000

# DP
g, V, pol, Q = solve_dp()
dp_pol = make_dp_policy(g, pol, Q)
OUT["V_x0"] = float(V[int(round(X0[0]*120)), int(round(X0[1]*120))])


def deterministic_path(policy, p=P, dc=0.1, cmax=150):
    """Expected-path proxy: same dynamics with shocks suppressed (rates only)."""
    K, M = X0; c = 0; tr = [(c, K, M, policy(K, M, {"c": 0}))]
    hist = {"c": 0}
    while not in_target(K, M, tol=0.005) and c < cmax:
        a = policy(K, M, hist); fk, fm, h = rates(K, M, a, p)
        K = min(K + fk*dc, 1); M = min(M + fm*dc, 1); c += dc; hist["c"] = c
        tr.append((c, K, M, a))
    return tr


OUT={}

def mc(pdict, p=P, n=NMC, seed=7):
    res = {}
    for k, f in pdict.items():
        rng = np.random.default_rng(seed)
        res[k] = np.array([simulate(f, p=p, rng=rng) for _ in range(n)])
    return res

# fit
true = dict(P)
rng = np.random.default_rng(2026)
c_, sh_, tr = simulate(policy_coupled, rng=rng, record=True)
tr = np.array([(t[0], t[1], t[2]) for t in tr]); acts = [t[3] for t in simulate(policy_coupled, rng=np.random.default_rng(2026), record=True)[2]]
# assessment every 3 BU with assessor noise sd 0.03
obs_c = np.arange(0, tr[-1, 0], 3.0)
idx = [np.argmin(np.abs(tr[:, 0]-cc)) for cc in obs_c]
noise = np.random.default_rng(5).normal(0, 0.03, (len(idx), 2))
obs = np.clip(tr[idx, 1:] + noise, 0, 1)
FIT = ["kb", "kl", "mb", "ml", "rS", "rE", "rT"]


def replay(theta, upto):
    p = dict(P); p.update(dict(zip(FIT, theta)))
    K, M = X0; out = []; j = 0
    for i in range(1, len(acts)):
        if i > upto: break
        a_ = acts[i]
        if a_.endswith("!"):
            K = max(K - p["dK"], 0); M = max(M - p["dM"], 0)
        else:
            fk, fm, h = rates(K, M, a_, p); K = min(K+fk*0.1, 1); M = min(M+fm*0.1, 1)
        out.append((K, M))
    out = [X0] + out
    return np.array(out)


def fit(n_obs):
    sel_i = idx[:n_obs]
    def res(th):
        pathp = replay(th, sel_i[-1])
        return (pathp[sel_i] - obs[:n_obs]).ravel()
    th0 = [P[k]*0.6 + 0.1 for k in FIT]
    lb = [0, 0, 0, 0.2, 0.01, 0.01, 0.01]; ub = [0.9, 1.5, 0.5, 2.0, 1.0, 1.0, 1.0]
    r = least_squares(res, th0, bounds=(lb, ub))
    return r.x

fits = {}
for n_obs in (4, 6, len(idx)):
    th = fit(n_obs)
    p_f = dict(P); p_f.update(dict(zip(FIT, th)))
    gF, VF, polF, QF = solve_dp(p=p_f)
    agree = float(np.mean((polF == pol)[pol >= 0]))
    cost = mc({"x": make_dp_policy(gF, polF, QF)}, n=500, seed=3)["x"][:, 0].mean()
    fits[n_obs] = dict(theta={k: round(float(v), 3) for k, v in zip(FIT, th)},
                       policy_agreement=agree, cost_using_fitted_dp=float(cost),
                       budget_seen=float(obs_c[n_obs-1]))
OUT["fits"] = fits
OUT["true_theta"] = {k: P[k] for k in FIT}
OUT["n_assessments"] = len(idx)

th6 = np.array(list(fits[6]["theta"].values()))
pf = dict(P); pf.update(dict(zip(FIT, th6)))
fig, a = plt.subplots(1, 2, figsize=(7.16, 3.0))
a[0].plot(tr[:, 0], tr[:, 1], color=C["S"], lw=1.2, label="True $K$")
a[0].plot(tr[:, 0], tr[:, 2], color=C["T"], lw=1.2, ls="--", label="True $M$")
a[0].plot(obs_c, obs[:, 0], "o", ms=4, mfc="white", mec=C["S"], label="Assessed $K$")
a[0].plot(obs_c, obs[:, 1], "s", ms=4, mfc="white", mec=C["T"], label="Assessed $M$")
rp = replay(th6, len(acts))
a[0].plot(tr[:len(rp), 0], rp[:, 0], color=C["S"], lw=0.8, alpha=0.6, label="Fitted replay $K$")
a[0].plot(tr[:len(rp), 0], rp[:, 1], color=C["T"], lw=0.8, alpha=0.6, ls=":", label="Fitted replay $M$")
a[0].axvspan(0, obs_c[5], color="#EEEEEE", zorder=0)
a[0].text(obs_c[5]/2, 0.95, "fitting\nwindow", ha="center", va="top", fontsize=7)
a[0].set_xlabel("Cumulative cost $c$ (BU)"); a[0].set_ylabel("Score")
a[0].legend(frameon=False, fontsize=6.5, loc="lower right", ncol=1); a[0].set_ylim(0, 1)
a[0].set_title("(a) Assessments and fitted replay", fontsize=9, loc="left")
gF, VF, polF, QF = solve_dp(p=pf)
dif = np.where(pol < 0, np.nan, (polF != pol).astype(float)).T
a[1].imshow(np.ma.masked_where(polF.T < 0, polF.T), origin="lower", extent=[0, 1, 0, 1],
            cmap=ListedColormap([C["S"], C["E"], C["T"]]), vmin=0, vmax=2, alpha=0.25)
a[1].contour(g, g, np.ma.masked_where(polF < 0, polF).T, levels=[0.5, 1.5], colors="#222222", linewidths=0.6)
for lab, xy in (("S", (0.10, 0.60)), ("E", (0.55, 0.15)), ("T", (0.86, 0.40))):
    a[1].text(*xy, lab, color=C[lab], fontsize=10, weight="bold", bbox=dict(fc="white", ec="none", alpha=0.7, pad=1))
a[1].contourf(g, g, np.nan_to_num(dif), levels=[0.5, 1.5], colors="none", hatches=["////"])
a[1].set_xlabel("$K$"); a[1].set_ylabel("$M$")
a[1].set_title("(b) Policy fitted from 6 assessments",
               fontsize=9, loc="left")
a[1].text(0.03, 0.93, "hatched: differs from true optimum", fontsize=7, bbox=dict(fc="white", ec="none", alpha=0.8))
fig.tight_layout(); fig.savefig("../figures/Fig6.png"); fig.savefig("../figures/Fig6.pdf"); plt.close(fig)

print(OUT["fits"])
