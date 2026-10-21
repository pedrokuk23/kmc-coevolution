"""Two claims sharing a budget and an integrated test (Section V-G). Synthetic.
Claim 1: base parameters. Claim 2: weak simulation (F-1-like) and a lower maturity ceiling slope (K_need = 0.83). Actions: S1, S2, E1, E2, T (joint integrated test)."""
import json, numpy as np
from scipy.ndimage import map_coordinates
from kmc_model import P, TARGET, Kbar, Mbar, K_need

P1 = dict(P)
P2 = dict(P); P2.update(rS=0.12, kb=0.25, ml=0.90)   # weak simulation; needs more knowledge to support the test
PS = [P1, P2]
ACTS = ["S1", "S2", "E1", "E2", "T"]
X0 = np.array([0.15, 0.10, 0.15, 0.10])

def done(x):
    return (x[..., 0] >= TARGET[0]) & (x[..., 1] >= TARGET[1]) & (x[..., 2] >= TARGET[0]) & (x[..., 3] >= TARGET[1])

def step(x, a):
    """Returns drift (dx/dc) and per-claim shock hazards (h1, h2)."""
    K1, M1, K2, M2 = x[..., 0], x[..., 1], x[..., 2], x[..., 3]
    d = np.zeros_like(x); h = np.zeros(x.shape[:-1] + (2,))
    Ks, Ms = (K1, K2), (M1, M2)
    if a in ("S1", "S2"):
        i = int(a[1]) - 1; p = PS[i]
        d[..., 2 * i] = p["rS"] * np.maximum(Kbar(Ms[i], p) - Ks[i], 0)
    elif a in ("E1", "E2"):
        i = int(a[1]) - 1; p = PS[i]
        d[..., 2 * i] = p["rE"] * (1 - Ks[i]); d[..., 2 * i + 1] = p["eE"] * np.maximum(Mbar(Ks[i], p) - Ms[i], 0)
        h[..., i] = p["lamE"] * (1 - Ks[i]) ** 2
    else:
        for i in (0, 1):
            p = PS[i]
            d[..., 2 * i] = p["eT"] * (1 - Ks[i]); d[..., 2 * i + 1] = p["rT"] * np.maximum(Mbar(Ks[i], p) - Ms[i], 0)
            h[..., i] = p["lamT"] * (1 - Ks[i]) ** 2
    return d, h

def shock(x, i):
    y = x.copy(); y[..., 2 * i] = np.maximum(y[..., 2 * i] - P["dK"], 0); y[..., 2 * i + 1] = np.maximum(y[..., 2 * i + 1] - P["dM"], 0)
    return y

def solve(n=26, dc=0.5, tol=1e-4, itmax=3000):
    g = np.linspace(0, 1, n)
    X = np.stack(np.meshgrid(g, g, g, g, indexing="ij"), -1)
    term = done(X)
    V = np.where(term, 0.0, 80.0)
    coords = lambda Y: [np.clip(Y[..., k], 0, 1).ravel() * (n - 1) for k in range(4)]
    pre = []
    for a in ACTS:
        d, h = step(X, a); pr = np.minimum(h * dc, 0.49)
        pre.append((coords(np.clip(X + d * dc, 0, 1)), pr, coords(shock(X, 0)), coords(shock(X, 1))))
    for it in range(itmax):
        Q = []
        for (cn, pr, c1, c2) in pre:
            vn = map_coordinates(V, cn, order=1).reshape(V.shape)
            v1 = map_coordinates(V, c1, order=1).reshape(V.shape)
            v2 = map_coordinates(V, c2, order=1).reshape(V.shape)
            p1, p2 = pr[..., 0], pr[..., 1]
            Q.append(dc + (1 - p1 - p2) * vn + p1 * (P["rework"] + v1) + p2 * (P["rework"] + v2))
        Q = np.stack(Q); Vn = np.where(term, 0.0, Q.min(0))
        err = np.abs(Vn - V).max(); V = Vn
        if err < tol: break
    return g, V, Q, it

def dp_policy(g, Q):
    n = len(g)
    def f(x, hist):
        c = [[x[k] * (n - 1)] for k in range(4)]
        return ACTS[int(np.argmin([map_coordinates(Q[a], c, order=1)[0] for a in range(len(ACTS))]))]
    return f

def best_knowledge(x):
    """Most productive knowledge-building action among claims with a knowledge deficit."""
    best, br = None, -1
    for i in (0, 1):
        p = PS[i]; Kreq = max(TARGET[0], K_need(p))
        if x[2 * i] >= Kreq - 1e-9: continue
        for a in (f"S{i+1}", f"E{i+1}"):
            r = step(x, a)[0][2 * i]
            if r > br: best, br = a, r
    return best

def t_stalled(x, eps=0.10):
    d = step(x, "T")[0]
    return all(d[2 * i + 1] < eps * PS[i]["rT"] for i in (0, 1) if x[2 * i + 1] < TARGET[1])

def headroom_weakest(x, hist, haz_max=0.05):
    need_M = any(x[2 * i + 1] < TARGET[1] for i in (0, 1))
    ready = all(x[2 * i] >= K_need(PS[i]) - 1e-9 for i in (0, 1))
    if need_M and ready and step(x, "T")[1].sum() <= haz_max and not t_stalled(x): return "T"
    a = best_knowledge(x)
    return a or "T"

def headroom_average(x, hist, haz_max=0.05):
    """Compensatory variant: averages knowledge across claims (non-conservative aggregation, Sec. V-G)."""
    need_M = any(x[2 * i + 1] < TARGET[1] for i in (0, 1))
    ready = np.mean([x[0], x[2]]) >= np.mean([K_need(PS[0]), K_need(PS[1])])
    if need_M and ready and not t_stalled(x): return "T"
    return best_knowledge(x) or "T"

def test_first(x, hist, eps=0.10):
    d, h = step(x, "T")
    if max(d[1], d[3]) > eps * P["rT"]: return "T"
    return best_knowledge(x) or "T"

def analysis_first(x, hist, eps=0.10):
    for i in (0, 1):
        p = PS[i]
        if x[2 * i] < TARGET[0] and step(x, f"S{i+1}")[0][2 * i] > eps * p["rS"]: return f"S{i+1}"
    return "T"

def simulate(policy, rng, dc=0.1, cmax=250):
    x = X0.copy(); c = 0.0; shocks = 0
    while not done(x + 0.005) and c < cmax:
        a = policy(x, {}); d, h = step(x, a)
        u = rng.random(); p1, p2 = min(h[0] * dc, 0.49), min(h[1] * dc, 0.49)
        if u < p1: x = shock(x, 0); c += P["rework"]; shocks += 1
        elif u < p1 + p2: x = shock(x, 1); c += P["rework"]; shocks += 1
        else: x = np.clip(x + d * dc, 0, 1)
        c += dc
    return c, shocks

if __name__ == "__main__":
    import time
    t0 = time.time(); g, V, Q, it = solve(); print("dp", time.time() - t0, it)
    v0 = float(map_coordinates(V, [[X0[k] * (len(g) - 1)] for k in range(4)], order=1)[0])
    pols = {"Optimal (dynamic programming)": dp_policy(g, Q), "Headroom, weakest link": headroom_weakest,
            "Headroom, averaged knowledge": headroom_average, "Analysis-first": analysis_first, "Test-first": test_first}
    out = {"V_x0": v0, "K_need": [K_need(PS[0]), K_need(PS[1])], "policies": {}}
    for k, f in pols.items():
        rng = np.random.default_rng(11)
        r = np.array([simulate(f, rng) for _ in range(600)])
        out["policies"][k] = dict(mean=float(r[:, 0].mean()), p90=float(np.percentile(r[:, 0], 90)),
                                  shocks=float(r[:, 1].mean()), nr=float(np.mean(r[:, 0] >= 250)))
        print(k, out["policies"][k])
    # trajectory of first integrated test under each headroom variant (deterministic)
    for k, f in [("weakest", headroom_weakest), ("average", headroom_average)]:
        x = X0.copy(); c = 0
        while not done(x + 0.005) and c < 100:
            a = f(x, {})
            if a == "T": out[f"first_T_{k}"] = dict(c=round(c, 1), x=[round(float(v), 3) for v in x]); break
            x = np.clip(x + step(x, a)[0] * 0.1, 0, 1); c += 0.1
    json.dump(out, open("two_claims.json", "w"), indent=1)
    print(out.get("first_T_weakest"), out.get("first_T_average"), "V0", v0)
