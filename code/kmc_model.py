"""
KMC dynamics: coupled knowledge-maturity growth under three activity types.
All parameters are illustrative (synthetic). Cost unit: BU (budget units).

State x = (K, M) on interval scales:
  K = 1 - U/U0     (U: validation uncertainty of the intended-use prediction)
  M = demonstrated fraction of the required envelope (weighted test points passed)

Activities (per BU spent):
  S  simulation/analysis     : K -> data-limited ceiling Kbar(M); no M credit
  E  separate-effects test   : K -> 1 (causal observability); small M credit
  T  integrated test/flight  : M -> knowledge-limited ceiling Mbar(K); small K credit
Discrepancy (epistemic shock) hazard for tests grows with (1-K)^2.
"""
import numpy as np
from scipy.ndimage import map_coordinates

P = dict(
    kb=0.40, kl=0.60,          # Kbar(M) = min(1, kb + kl*M)
    mb=0.05, ml=1.05,          # Mbar(K) = min(1, mb + ml*K)
    rS=0.30,                   # simulation rate toward Kbar
    rE=0.10, eE=0.05,          # separate-effects: K rate, M credit rate
    rT=0.22, eT=0.04,          # integrated test: M rate, K credit rate
    lamE=0.05, lamT=0.40,      # shock hazard per BU = lam*(1-K)^2
    dK=0.06, dM=0.15, rework=2.0,  # shock: K,M decrements and extra BU
)
ACTS = ["S", "E", "T"]
TARGET = (0.75, 0.80)
X0 = (0.15, 0.10)


def Kbar(M, p=P): return np.minimum(1.0, p["kb"] + p["kl"] * M ** p.get("kpow", 1.0))
def Mbar(K, p=P): return np.minimum(1.0, p["mb"] + p["ml"] * K ** p.get("mpow", 1.0))


def hazard(K, lam, p=P):
    if p.get("haz", "quad") == "exp":
        return lam * p.get("haz_c", 1.0) * np.exp(-3.0 * K)
    return lam * (1 - K) ** 2


def K_haz(p=P, haz_max=0.05):
    """Smallest K whose integrated-test hazard lambda_T (1-K)^2 is within the exposure limit (quadratic form)."""
    if p["lamT"] <= 0:
        return 0.0
    return float(np.clip(1 - np.sqrt(haz_max / p["lamT"]), 0, 1))


def K_test(p=P, tgt=TARGET, haz_max=0.05):
    """Test threshold: knowledge must support the target maturity and keep exposure within the limit."""
    return max(K_need(p, tgt), K_haz(p, haz_max))


def K_need(p=P, tgt=TARGET):
    """Smallest K whose knowledge-limited ceiling clears the target maturity, Eq. (16b).
    Returns inf when the target is infeasible under these parameters (Mbar(1) = mb + ml < M_req)."""
    gap = tgt[1] - p["mb"]
    if gap <= 0:
        return 0.0
    if p["ml"] <= 0 or p["mb"] + p["ml"] < tgt[1]:
        return float("inf")
    return float(min((gap / p["ml"]) ** (1.0 / p.get("mpow", 1.0)), 1.0))


def rates(K, M, a, p=P):
    """(dK/dc, dM/dc, hazard per BU) for activity a."""
    if a == "S":
        gm = p.get("sim_mcredit", 0.0) * K ** 3 * (1 - M)
        return p["rS"] * np.maximum(Kbar(M, p) - K, 0), gm + 0 * K, 0 * K
    if a == "E":
        return (p["rE"] * (1 - K), p["eE"] * np.maximum(Mbar(K, p) - M, 0),
                hazard(K, p["lamE"], p))
    if a == "T":
        scale = (p.get("trate_b", 1.0) + p.get("trate_k", 0.0) * K)
        fkT = p["eT"] * (1 - K)
        if "tk_g" in p:   # data-informed flight learning g(1-K)^q, applied only for K >= tk_kmin (default: everywhere)
            fkT = np.where(K >= p.get("tk_kmin", 0.0), p["tk_g"] * (1 - K) ** p["tk_q"], fkT)
        return (fkT, p["rT"] * scale * np.maximum(Mbar(K, p) - M, 0),
                hazard(K, p["lamT"], p))


def in_target(K, M, tgt=TARGET, tol=0.0): return (K >= tgt[0] - tol) & (M >= tgt[1] - tol)


# ---------------------------------------------------------------- DP
def solve_dp(p=P, tgt=TARGET, n=121, dc=0.1, tol=1e-6, itmax=20000):
    g = np.linspace(0, 1, n)
    K, M = np.meshgrid(g, g, indexing="ij")
    V = np.where(in_target(K, M, tgt), 0.0, 50.0)
    term = in_target(K, M, tgt)

    def interp(V, Kq, Mq):
        Kq = np.clip(Kq, 0, 1) * (n - 1); Mq = np.clip(Mq, 0, 1) * (n - 1)
        return map_coordinates(V, [Kq, Mq], order=1, mode="nearest")

    pre = {}
    for a in ACTS:
        fk, fm, h = rates(K, M, a, p)
        pr = np.minimum(h * dc, 1.0)
        pre[a] = (K + fk * dc, M + fm * dc, pr,
                  np.clip(K - p["dK"], 0, 1), np.clip(M - p["dM"], 0, 1))
    for it in range(itmax):
        Q = []
        for a in ACTS:
            Kn, Mn, pr, Ks, Ms = pre[a]
            q = dc + (1 - pr) * interp(V, Kn, Mn) + pr * (p["rework"] + interp(V, Ks, Ms))
            Q.append(q)
        Q = np.stack(Q)
        Vn = np.where(term, 0.0, Q.min(0))
        err = np.max(np.abs(Vn - V)); V = Vn
        if err < tol: break
    pol = np.where(term, -1, Q.argmin(0))
    return g, V, pol, Q


# ---------------------------------------------------------------- policies
def make_dp_policy(g, pol, Q):
    n = len(g)
    def f(K, M, hist):
        c = [[K * (n - 1)], [M * (n - 1)]]
        q = [map_coordinates(Q[k], c, order=1, mode="nearest")[0] for k in range(3)]
        return ACTS[int(np.argmin(q))]
    return f


def policy_analysis_first(K, M, hist, p=P, tgt=TARGET, eps=0.10):
    """Vee-like: analyse until simulation saturates, then test; separate-effects only if both stall."""
    if K < tgt[0] and rates(K, M, "S", p)[0] > eps * p["rS"]:
        return "S"
    return "T"


def policy_test_first(K, M, hist, p=P, tgt=TARGET, eps=0.10):
    """RID-DE-like: integrated testing; fall back to analysis only when tests stall."""
    if rates(K, M, "T", p)[1] > eps * p["rT"] or M >= tgt[1]:
        return "T" if M < tgt[1] else "S"
    return "S"


def policy_spiral(K, M, hist, block=3.0):
    """Fixed alternation S -> E -> T, block BU each."""
    c = hist["c"]
    return ACTS[int(c // block) % 3]


def policy_derivative(K, M, hist, p=P, tgt=TARGET):
    """Practitioner rule using only local derivatives (marginal rates) and the gap to target.
    Score = progress per BU projected on the remaining-gap direction minus expected shock loss."""
    gK, gM = max(tgt[0] - K, 0), max(tgt[1] - M, 0)
    nrm = np.hypot(gK, gM) + 1e-12
    wK, wM = gK / nrm, gM / nrm
    best, sb = None, -1e9
    for a in ACTS:
        fk, fm, h = rates(K, M, a, p)
        loss = h * (wK * p["dK"] + wM * p["dM"] + 0.05 * p["rework"])
        s = wK * fk + wM * fm - loss
        if s > sb: best, sb = a, s
    return best


# ---------------------------------------------------------------- simulation
def simulate(policy, p=P, tgt=TARGET, x0=X0, dc=0.1, cmax=200, rng=None, record=False):
    rng = rng or np.random.default_rng()
    K, M = x0; c = 0.0; shocks = 0
    hist = dict(c=0.0)
    tr = [(c, K, M, "-")]
    while not in_target(K, M, tgt, tol=0.005) and c < cmax:
        a = policy(K, M, hist)
        fk, fm, h = rates(K, M, a, p)
        if rng.random() < min(h * dc, 1):
            K = max(K - p["dK"], 0); M = max(M - p["dM"], 0)
            c += p["rework"]; shocks += 1
            a = a + "!"
        else:
            K = min(K + fk * dc, 1); M = min(M + fm * dc, 1)
        c += dc; hist["c"] = c
        if record: tr.append((c, K, M, a))
    return (c, shocks, tr) if record else (c, shocks)


def policy_slope(K, M, hist, p=P, tgt=TARGET):
    """Naive slope rule: compare the required slope S_req = gapM/gapK with each activity's
    instantaneous slope dM/dK and pick the activity whose direction is closest (no shock or coupling terms)."""
    gK, gM = max(tgt[0] - K, 1e-9), max(tgt[1] - M, 0)
    ang_req = np.arctan2(gM, gK)
    best, db = None, 1e9
    for a in ACTS:
        fk, fm, h = rates(K, M, a, p)
        if fk + fm < 1e-9: continue
        d = abs(np.arctan2(fm, fk) - ang_req)
        if d < db: best, db = a, d
    return best or "E"


def phi(K, M, p=P, tgt=TARGET):
    """Coupling-aware potential: knowledge gap includes the knowledge needed to SUPPORT the target maturity."""
    Kneed = max(tgt[0], K_need(p, tgt))
    return max(Kneed - K, 0) + max(tgt[1] - M, 0)


def policy_coupled(K, M, hist, p=P, tgt=TARGET, dc=0.1):
    """Coupling-aware derivative rule: choose the activity with the largest expected
    rate of decrease of phi per BU (one-step lookahead, includes shock expectation)."""
    best, sb = None, -1e9
    f0 = phi(K, M, p, tgt)
    for a in ACTS:
        fk, fm, h = rates(K, M, a, p)
        pr = min(h * dc, 1)
        ok = phi(min(K + fk * dc, 1), min(M + fm * dc, 1), p, tgt)
        bad = phi(max(K - p["dK"], 0), max(M - p["dM"], 0), p, tgt)
        # convert rework BU into phi units using the current best progress rate
        dphi = f0 - ((1 - pr) * ok + pr * bad)
        rate = dphi / (dc + pr * p["rework"])
        if rate > sb: best, sb = a, rate
    return best


def policy_procedure(K, M, hist, p=P, tgt=TARGET, haz_max=0.05, wait_haz=False):
    """Headroom procedure (Table 6, steps 3-4): maturity gap + knowledge headroom (K >= K_need) + exposure limit."""
    gK, gM = max(tgt[0] - K, 0), max(tgt[1] - M, 0)
    Kneed = K_need(p, tgt)
    fkS = rates(K, M, "S", p)[0]
    hazT = float(rates(K, M, "T", p)[2])
    if gM > 0 and K >= Kneed - 1e-9 and hazT <= haz_max:
        return "T"                       # maturity deficit, knowledge supports the test, exposure within limit
    if gK > 0 or K < Kneed or (wait_haz and gM > 0 and hazT > haz_max):
        # knowledge deficit (absolute or to support testing); with wait_haz=True also when the test
        # hazard exceeds the exposure limit (step 3b by reducing exposure through knowledge: K >= K_test).
        # Default (paper results): step 3b is resolved by re-approving the limit, i.e. the test proceeds.
        # most productive knowledge-building activity, net of expected shock loss (T included when tests teach)
        # with wait_haz=True (hard limit) only activities whose hazard is within the limit are admissible (step 0)
        cand = [a for a in ["S", "E", "T"] if not wait_haz or float(rates(K, M, a, p)[2]) <= haz_max]
        def net(a):
            fk, fm, h = rates(K, M, a, p)
            return float(fk) - float(h) * p["dK"]
        return max(cand, key=net)
    return "T"


def policy_threshold(K, M, hist, p=P, tgt=TARGET, Kstar=0.7):
    """Two-phase threshold rule (tuned baseline): build knowledge with the more productive of S and E
    (net of expected shock loss) until K >= Kstar, then integrated testing; knowledge again if K < K_req
    once M_req is reached. Kstar is tuned by simulation for each parameter set."""
    if K < Kstar or (M >= tgt[1] and K < tgt[0]):
        def net(a):
            fk, fm, h = rates(K, M, a, p)
            return float(fk) - float(h) * p["dK"]
        return max(["S", "E"], key=net)
    return "T"


def policy_procedure_SE(K, M, hist, p=P, tgt=TARGET, haz_max=0.05, wait_haz=False):
    """Restricted headroom procedure: knowledge built only by S or E (no integrated test in step 4)."""
    gK, gM = max(tgt[0] - K, 0), max(tgt[1] - M, 0)
    Kneed = K_need(p, tgt)
    if gM > 0 and K >= Kneed - 1e-9 and float(rates(K, M, "T", p)[2]) <= haz_max:
        return "T"
    if gK > 0 or K < Kneed or (wait_haz and gM > 0 and float(rates(K, M, "T", p)[2]) > haz_max):
        return "S" if rates(K, M, "S", p)[0] >= rates(K, M, "E", p)[0] else "E"
    return "T"
