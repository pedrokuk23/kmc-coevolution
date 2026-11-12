"""Revision 1, R1.4 (second round): grid convergence of the four-dimensional dynamic program of Sec. V-G with the
terminal test applied to the continuous successor state.

In two_claims.solve the terminal region enters only through the grid nodes, so with a grid spacing that does not
divide the targets (K_req = 0.75, M_req = 0.80) the effective target is raised to the next node (e.g. K_req = 0.771
on 36^4), which biases V(x0) and the policy. Here a successor that lies in X_f has value 0 exactly, wherever it falls
between nodes. Every optimal policy and the headroom procedures are then evaluated on N independent random streams
(seeds 50000 + i, not used in any earlier run), and the gap of the weakest-link procedure is reported against the
best policy found, which is a lower bound on its gap to the true optimum."""
import json, os, time, numpy as np
from multiprocessing import Pool
from scipy.ndimage import map_coordinates
import two_claims as tc
from kmc_model import P

N = int(os.environ.get("NRUNS", 4000)); SEED0 = 50000
GRIDS = [tuple(float(x) if "." in x else int(x) for x in g.split(":")) for g in os.environ.get("GRIDS", "26:0.5,31:0.5,36:0.5,41:0.5,46:0.5,51:0.5").split(",")]
OUT = os.environ.get("OUT", "rev1/two_claims_convergence2.json")

def solve_cont(n, dc, tol=1e-4, itmax=3000):
    g = np.linspace(0, 1, n)
    X = np.stack(np.meshgrid(g, g, g, g, indexing="ij"), -1)
    term = tc.done(X)
    V = np.where(term, 0.0, 80.0)
    co = lambda Y: [(np.clip(Y[..., k], 0, 1) * (n - 1)).astype(np.float32).ravel() for k in range(4)]
    pre = []
    for a in tc.ACTS:
        d, h = tc.step(X, a); pr = np.minimum(h * dc, 0.49).astype(np.float32)
        Xn = np.clip(X + d * dc, 0, 1); tn = tc.done(Xn)
        pre.append((co(Xn), tn, pr, co(tc.shock(X, 0)), co(tc.shock(X, 1))))
        del Xn
    del X
    for it in range(itmax):
        Q = []
        for (cn, tn, pr, c1, c2) in pre:
            vn = np.where(tn, 0.0, map_coordinates(V, cn, order=1).reshape(V.shape))
            v1 = map_coordinates(V, c1, order=1).reshape(V.shape)
            v2 = map_coordinates(V, c2, order=1).reshape(V.shape)
            p1, p2 = pr[..., 0], pr[..., 1]
            Q.append((dc + (1 - p1 - p2) * vn + p1 * (P["rework"] + v1) + p2 * (P["rework"] + v2)).astype(np.float32))
        Q = np.stack(Q); Vn = np.where(term, 0.0, Q.min(0))
        err = np.abs(Vn - V).max(); V = Vn
        if err < tol: break
    return g, V, Q, it

_POL = {}
def _ev(a):
    k, i = a
    return tc.simulate(_POL[k], np.random.default_rng(SEED0 + i))[0]

if __name__ == "__main__":
    out = json.load(open(OUT)) if os.path.exists(OUT) else {"runs": N, "seed0": SEED0, "grids": [], "fixed": {}}
    done_g = {(r["n"], r["dc"]) for r in out["grids"]}
    def evaluate(k):
        with Pool(2) as pool:
            return np.array(pool.map(_ev, [(k, i) for i in range(N)], chunksize=100))
    if True:
        if not out["fixed"]:
            for k, f in [("Headroom, weakest link", tc.headroom_weakest), ("Headroom, averaged knowledge", tc.headroom_average)]:
                _POL.clear(); _POL[k] = f
                out["fixed"][k] = evaluate(k).tolist()
        for n, dc in GRIDS:
            if (n, dc) in done_g: continue
            t0 = time.time(); g, V, Q, it = solve_cont(n, dc)
            v0 = float(map_coordinates(V, [[tc.X0[k] * (n - 1)] for k in range(4)], order=1)[0])
            _POL.clear(); _POL["dp"] = tc.dp_policy(g, Q)
            c = evaluate("dp")
            rec = dict(n=n, dc=dc, iters=int(it), secs=round(time.time() - t0, 1), V_x0=v0, mean=float(c.mean()),
                       sem=float(c.std(ddof=1) / np.sqrt(N)), costs=c.tolist())
            out["grids"].append(rec); print({k: v for k, v in rec.items() if k != "costs"}, flush=True)
            json.dump(out, open(OUT, "w"))
            del V, Q
