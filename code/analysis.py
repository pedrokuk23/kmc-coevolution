"""Base experiments of Section V -> results.json.

Optimal curve and switch points (Fig. 3), policy comparison and scenarios (Table 7, Fig. 4),
misspecified planner, recoding check (Sec. IV-D) and estimation of the curve from noisy
assessments (Sec. V-F, Fig. 6). Figures are drawn by fig3.py, fig4.py and fig6.py.
"""
import json, numpy as np
from scipy.optimize import least_squares
from kmc_model import *

OUT = {}
NMC = 2000

# ------------------------------------------------------------ 1. DP and optimal curve
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

opt = deterministic_path(dp_pol)
c_o = np.array([t[0] for t in opt]); K_o = np.array([t[1] for t in opt]); M_o = np.array([t[2] for t in opt])
A_o = [t[3] for t in opt]
switches = [(round(c_o[i], 1), A_o[i-1], A_o[i], round(K_o[i], 3), round(M_o[i], 3))
            for i in range(1, len(A_o)) if A_o[i] != A_o[i-1]]
OUT["opt_det_cost"] = float(c_o[-1]); OUT["switches"] = switches

# optimal curve in the "cheap, safe tests" scenario (dashed line in Fig. 3a)
p_cheap = dict(P); p_cheap.update(rT=0.44, lamT=0.20)
g2, V2, pol2, Q2 = solve_dp(p=p_cheap)
tr2 = deterministic_path(make_dp_policy(g2, pol2, Q2), p=p_cheap)
OUT["cheap_switches"] = [(round(tr2[i][0], 1), tr2[i-1][3], tr2[i][3], round(tr2[i][1], 3), round(tr2[i][2], 3))
                         for i in range(1, len(tr2)) if tr2[i][3] != tr2[i-1][3]]
OUT["cheap_det_cost"] = float(tr2[-1][0])


# ------------------------------------------------------------ 2. Policy comparison (Monte Carlo)
pols = {"Analysis-first (Vee-like)": policy_analysis_first,
        "Test-first (RID-DE-like)": policy_test_first,
        "Fixed alternation (Spiral-like)": policy_spiral,
        "Naive slope rule": policy_slope,
        "Gap-weighted derivative rule": policy_derivative,
        "Coupling-aware derivative rule": policy_coupled,
        "Headroom procedure (Table 6)": policy_procedure,
        "Optimal (dynamic programming)": dp_pol}


def mc(pdict, p=P, n=NMC, seed=7):
    res = {}
    for k, f in pdict.items():
        rng = np.random.default_rng(seed)
        r = np.array([simulate(f, p=p, rng=rng) for _ in range(n)])
        res[k] = r
    return res

base = mc(pols)
OUT["mc_base"] = {k: dict(mean=float(r[:, 0].mean()), p10=float(np.percentile(r[:, 0], 10)),
                          p90=float(np.percentile(r[:, 0], 90)), shocks=float(r[:, 1].mean()))
                  for k, r in base.items()}


# ------------------------------------------------------------ 3. Sensitivity scenarios
scen = {
    "Base": dict(),
    "Cheap, safe tests": dict(rT=0.44, lamT=0.20),
    "Costly, risky tests": dict(lamT=0.80, rework=4.0),
    "Weak simulation": dict(rS=0.12, kb=0.25),
}
OUT["scenarios"] = {}
for sname, mod in scen.items():
    p2 = dict(P); p2.update(mod)
    g2, V2, pol2, Q2 = solve_dp(p=p2)
    pd = {"Analysis-first (Vee-like)": lambda K, M, h, p2=p2: policy_analysis_first(K, M, h, p=p2),
          "Test-first (RID-DE-like)": lambda K, M, h, p2=p2: policy_test_first(K, M, h, p=p2),
          "Fixed alternation (Spiral-like)": policy_spiral,
          "Naive slope rule": lambda K, M, h, p2=p2: policy_slope(K, M, h, p=p2),
          "Gap-weighted derivative rule": lambda K, M, h, p2=p2: policy_derivative(K, M, h, p=p2),
          "Coupling-aware derivative rule": lambda K, M, h, p2=p2: policy_coupled(K, M, h, p=p2),
          "Optimal (dynamic programming)": make_dp_policy(g2, pol2, Q2)}
    r = mc(pd, p=p2, n=1000)
    OUT["scenarios"][sname] = {k: float(v[:, 0].mean()) for k, v in r.items()}
    OUT["scenarios"][sname]["share_T_map"] = float(np.mean(pol2[pol2 >= 0] == 2))

# headroom procedure (Table 6) in each scenario
OUT["procedure"] = {}
for sname, mod in scen.items():
    p2 = dict(P); p2.update(mod); rng = np.random.default_rng(7)
    r = np.array([simulate(lambda K, M, h, p2=p2: policy_procedure(K, M, h, p=p2), p=p2, rng=rng)
                  for _ in range(NMC if sname == "Base" else 1000)])
    OUT["procedure"][sname] = dict(mean=float(r[:, 0].mean()), p90=float(np.percentile(r[:, 0], 90)),
                                   shocks=float(r[:, 1].mean()))
    OUT["scenarios"][sname]["Headroom procedure"] = OUT["procedure"][sname]["mean"]

# misspecified DP: planner uses perturbed parameters, reality = base
rng = np.random.default_rng(11); mis = []
for rep in range(20):
    p3 = {k: (v * rng.uniform(0.7, 1.3) if k not in ("dK", "dM") else v) for k, v in P.items()}
    g3, V3, pol3, Q3 = solve_dp(p=p3)
    r = mc({"x": make_dp_policy(g3, pol3, Q3)}, n=300, seed=rep)["x"]
    mis.append(r[:, 0].mean())
mis = np.array(mis); stuck = mis >= 200          # plan never reaches the terminal region
OUT["dp_misspecified_pm30"] = dict(mean=float(np.mean(mis)), min=float(np.min(mis)), max=float(np.max(mis)),
                                   median=float(np.median(mis)), n_stuck=int(stuck.sum()),
                                   mean_excl_stuck=float(np.mean(mis[~stuck])))

# ------------------------------------------------------------ 4. Coding (re-scaling) invariance check
# Monotone recoding of both axes: K' = K^2, M' = sqrt(M). Slope-based rules are recomputed in
# the recoded coordinates; DP decisions depend only on cost-to-go, a scalar, and are unchanged.
def recoded_slope_rule(K, M):
    Kp, Mp = K**2, np.sqrt(max(M, 1e-9))
    tKp, tMp = TARGET[0]**2, np.sqrt(TARGET[1])
    gK, gM = max(tKp - Kp, 1e-9), max(tMp - Mp, 0)
    ang = np.arctan2(gM, gK); best, db = None, 1e9
    for a_ in ACTS:
        fk, fm, h = rates(K, M, a_)
        fkp, fmp = 2*K*fk, fm/(2*np.sqrt(max(M, 1e-9)))  # chain rule
        if fkp + fmp < 1e-12: continue
        d = abs(np.arctan2(fmp, fkp) - ang)
        if d < db: best, db = a_, d
    return best or "E"

pts = [(k, m) for k in np.linspace(0.02, 0.98, 49) for m in np.linspace(0.02, 0.98, 49)
       if not in_target(k, m)]
flip = np.mean([policy_slope(k, m, {}) != recoded_slope_rule(k, m) for k, m in pts])
OUT["slope_rule_flip_fraction_under_recoding"] = float(flip)

# ------------------------------------------------------------ 5. Fitting the curve from assessment history
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

# headroom procedure run with the fitted coefficients
OUT["procedure_fitted"] = {}
for n_obs, f in fits.items():
    pf = dict(P); pf.update(f["theta"]); rng = np.random.default_rng(7)
    OUT["procedure_fitted"][str(n_obs)] = float(np.mean([simulate(lambda K, M, h: policy_procedure(K, M, h, p=pf),
                                                                  rng=rng)[0] for _ in range(1000)]))


json.dump(OUT, open("results.json", "w"), indent=1, default=float)
print(json.dumps(OUT, indent=1, default=float))
