"""Revision 1, R1.1: validation-data availability separated from demonstrated maturity.

The base model ties the simulation ceiling to demonstrated maturity, Kbar(M) = kb + kl*M (Eq. 10), using M as a
proxy for the validation data available. Here a third state D (validation-data coverage, 0..1) carries the data:
  S: dK = rS [Kbar(D) - K]+,                    dD = 0
  E: dK = rE (1-K), dM = eE [Mbar(K) - M]+,     dD = rhoE (1-D)
  T: dK = eT (1-K), dM = rT [Mbar(K) - M]+,     dD = rhoT (1-D)
with Kbar(D) = min(1, kb + kl*D). Shocks reduce K and M as before and leave D (the data stay). Separate-effects tests
can therefore raise the simulation ceiling without raising M. The 'tied' variant (dD = dM, shocks reduce D like M)
reproduces the base model and checks the three-dimensional solver.
Policies (common random numbers):
  opt3      optimal policy of the three-dimensional dynamic program
  opt2      optimal policy of the base (K, M) model, used with the true K, M: the plan of a model that ignores D
  head_D    headroom procedure (Table 6) whose knowledge step compares the true rates, which depend on D
  head_KM   headroom procedure computed from the base model (ignores D)
  thr_D     two-phase threshold, K_th tuned by simulation on independent runs, true rates
  test_first, analysis_first  stylized proxies (true rates)
"""
import json, sys, time, numpy as np
from multiprocessing import Pool
from scipy.ndimage import map_coordinates
from kmc_model import P, TARGET, X0, Mbar, K_need, hazard, rates as rates2, solve_dp, make_dp_policy, policy_procedure

D0 = 0.10
ACTS = ["S", "E", "T"]

def Kbar_D(D, p): return np.minimum(1.0, p["kb"] + p["kl"] * D)

def rates3(K, M, D, a, p):
    """(dK, dM, dD, hazard) per BU."""
    if p.get("tied"):
        fk, fm, h = rates2(K, M, a, p)
        if a == "S": fk = p["rS"] * np.maximum(Kbar_D(D, p) - K, 0)
        return fk, fm, fm, h
    z = 0 * K
    if a == "S":
        return p["rS"] * np.maximum(Kbar_D(D, p) - K, 0), z, z, z
    if a == "E":
        return p["rE"] * (1 - K), p["eE"] * np.maximum(Mbar(K, p) - M, 0), p["rhoE"] * (1 - D) + z, hazard(K, p["lamE"], p)
    return p["eT"] * (1 - K), p["rT"] * np.maximum(Mbar(K, p) - M, 0), p["rhoT"] * (1 - D) + z, hazard(K, p["lamT"], p)

def in_tgt(K, M, tol=0.0): return (K >= TARGET[0] - tol) & (M >= TARGET[1] - tol)

def solve3(p, n=61, dc=0.1, tol=1e-6, itmax=20000):
    g = np.linspace(0, 1, n)
    K, M, D = np.meshgrid(g, g, g, indexing="ij")
    term = in_tgt(K, M); V = np.where(term, 0.0, 50.0)
    sc = lambda A: np.clip(A, 0, 1).ravel() * (n - 1)
    pre = []
    for a in ACTS:
        fk, fm, fd, h = rates3(K, M, D, a, p); pr = np.minimum(h * dc, 1.0)
        Ds = np.clip(D - p["dM"], 0, 1) if p.get("tied") else D
        pre.append(([sc(K + fk * dc), sc(M + fm * dc), sc(D + fd * dc)], pr,
                    [sc(K - p["dK"]), sc(M - p["dM"]), sc(Ds)]))
    for it in range(itmax):
        Q = np.stack([dc + (1 - pr) * map_coordinates(V, cn, order=1).reshape(V.shape)
                      + pr * (p["rework"] + map_coordinates(V, cs, order=1).reshape(V.shape)) for cn, pr, cs in pre])
        Vn = np.where(term, 0.0, Q.min(0)); err = np.abs(Vn - V).max(); V = Vn
        if err < tol: break
    return g, V, Q, it

def pol_opt3(g, Q):
    n = len(g)
    def f(K, M, D):
        c = [[K * (n - 1)], [M * (n - 1)], [D * (n - 1)]]
        return ACTS[int(np.argmin([map_coordinates(Q[a], c, order=1)[0] for a in range(3)]))]
    return f

def make_policies(p, g3, Q3, g2, pol2, Q2, Kth):
    dp2 = make_dp_policy(g2, pol2, Q2)
    Kn = K_need(p)
    def know(K, M, D, cands=("S", "E", "T")):
        def net(a):
            fk, fm, fd, h = rates3(K, M, D, a, p); return float(fk) - float(h) * p["dK"]
        return max(cands, key=net)
    def head_D(K, M, D, haz_max=0.05):
        gK, gM = max(TARGET[0] - K, 0), max(TARGET[1] - M, 0)
        if gM > 0 and K >= Kn - 1e-9 and float(hazard(K, p["lamT"], p)) <= haz_max: return "T"
        if gK > 0 or K < Kn: return know(K, M, D)
        return "T"
    def thr_D(K, M, D):
        if K < Kth or (M >= TARGET[1] and K < TARGET[0]): return know(K, M, D, ("S", "E"))
        return "T"
    def test_first(K, M, D, eps=0.10):
        if (rates3(K, M, D, "T", p)[1] > eps * p["rT"] or M >= TARGET[1]):
            return "T" if M < TARGET[1] else know(K, M, D, ("S", "E"))
        return know(K, M, D, ("S", "E"))
    def analysis_first(K, M, D, eps=0.10):
        if K < TARGET[0] and rates3(K, M, D, "S", p)[0] > eps * p["rS"]: return "S"
        return "T"
    return {"opt3": pol_opt3(g3, Q3), "opt2": lambda K, M, D: dp2(K, M, {}),
            "head_D": head_D, "head_KM": lambda K, M, D: policy_procedure(K, M, {}, p=p),
            "thr_D": thr_D, "test_first": test_first, "analysis_first": analysis_first}

def sim3(policy, p, rng, dc=0.1, cmax=200):
    K, M = X0; D = D0; c = 0.0; sh = 0
    while not in_tgt(K, M, 0.005) and c < cmax:
        a = policy(K, M, D); fk, fm, fd, h = rates3(K, M, D, a, p)
        if rng.random() < min(float(h) * dc, 1):
            K = max(K - p["dK"], 0); M = max(M - p["dM"], 0); c += p["rework"]; sh += 1
            if p.get("tied"): D = max(D - p["dM"], 0)
        else:
            K = min(K + float(fk) * dc, 1); M = min(M + float(fm) * dc, 1); D = min(D + float(fd) * dc, 1)
        c += dc
    return c, sh

_G = {}
def _job(args):
    name, i = args
    return sim3(_G["pols"][name], _G["p"], np.random.default_rng(10_000 + i))

def tune_threshold(p, g3, Q3, g2, pol2, Q2, nruns=300):
    best = None
    for kth in np.arange(0.40, 0.91, 0.05):
        pol = make_policies(p, g3, Q3, g2, pol2, Q2, kth)["thr_D"]
        c = np.mean([sim3(pol, p, np.random.default_rng(90_000 + i))[0] for i in range(nruns)])   # independent seeds
        if best is None or c < best[1]: best = (float(kth), float(c))
    return best[0]

def case(name, upd, nruns):
    p = dict(P); p.update(upd)
    t0 = time.time(); g3, V3, Q3, it = solve3(p)
    g2, V2, pol2, Q2 = solve_dp(p=p)          # base model: Kbar depends on M
    v3 = float(map_coordinates(V3, [[X0[0] * 60], [X0[1] * 60], [D0 * 60]], order=1)[0])
    kth = tune_threshold(p, g3, Q3, g2, pol2, Q2) if not p.get("tied") else None
    pols = make_policies(p, g3, Q3, g2, pol2, Q2, kth if kth is not None else 0.7)
    _G["pols"] = pols; _G["p"] = p
    res = {}
    names = list(pols) if not p.get("tied") else ["opt3", "opt2"]
    with Pool(2) as pool:
        for nm in names:
            r = np.array(pool.map(_job, [(nm, i) for i in range(nruns)], chunksize=25))
            res[nm] = r
    ref = res["opt3"][:, 0]
    out = dict(case=name, params={k: p[k] for k in ("rhoE", "rhoT") if k in p}, tied=bool(p.get("tied")), V3_x0=v3,
               V2_x0=float(map_coordinates(V2, [[X0[0] * 120], [X0[1] * 120]], order=1)[0]), iters=int(it),
               K_th=kth, secs=round(time.time() - t0, 1), policies={})
    for nm, r in res.items():
        d = (r[:, 0] - ref) / ref.mean() * 100
        rng = np.random.default_rng(3); bs = [d[j].mean() for j in (rng.integers(0, nruns, nruns) for _ in range(2000))]
        out["policies"][nm] = dict(mean=float(r[:, 0].mean()), excess_pct=float((r[:, 0].mean() / ref.mean() - 1) * 100),
                                   excess_ci95=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
                                   shocks=float(r[:, 1].mean()), not_reached=float(np.mean(r[:, 0] >= 200)))
    return out

CASES = [("tied (check: reproduces base)", dict(tied=True)),
         ("rhoE=0.05, rhoT=0.22", dict(rhoE=0.05, rhoT=0.22)),
         ("rhoE=0.10, rhoT=0.22", dict(rhoE=0.10, rhoT=0.22)),
         ("rhoE=0.20, rhoT=0.22", dict(rhoE=0.20, rhoT=0.22)),
         ("rhoE=0.40, rhoT=0.22", dict(rhoE=0.40, rhoT=0.22)),
         ("rhoE=0.20, rhoT=0.10", dict(rhoE=0.20, rhoT=0.10)),
         ("rhoE=0.40, rhoT=0.05", dict(rhoE=0.40, rhoT=0.05))]

if __name__ == "__main__":
    nruns = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    which = sys.argv[2].split(",") if len(sys.argv) > 2 else None
    allout = []
    for i, (nm, up) in enumerate(CASES):
        if which and str(i) not in which: continue
        o = case(nm, up, nruns); allout.append(o); print(json.dumps(o), flush=True)
        json.dump(allout, open(f"rev1/valdata{'_' + '_'.join(which) if which else ''}.json", "w"), indent=1)
