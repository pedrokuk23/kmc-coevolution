"""Revision 1, R1.1/R2.4: data-aware knowledge step with both data sources.

Extends rev1_valdata_rule.make_head_DD: the projection compares the greedy knowledge plan with raising the data
coverage D first by separate-effects tests (E) or by integrated tests (T), each until the data ceiling Kbar(D) clears
K_target + delta (delta in DELTAS), with the expected rework of shocks included, and takes the first activity of the
cheapest plan. Rates are those of the model (known here; fitted in practice)."""
import numpy as np
import rev1_valdata as v
from rev1_valdata_rule import DELTAS
from kmc_model import TARGET, K_need, hazard

def project(K, M, D, p, src, delta, Kt, dc=0.1, cmax=60.0):
    c = 0.0
    while K < Kt and c < cmax:
        if src is not None and v.Kbar_D(D, p) < Kt + delta: a = src
        else:
            a = max(("S", "E", "T"), key=lambda b: float(v.rates3(K, M, D, b, p)[0]) - float(v.rates3(K, M, D, b, p)[3]) * p["dK"])
        fk, fm, fd, h = v.rates3(K, M, D, a, p)
        K = min(K + float(fk) * dc, 1); M = min(M + float(fm) * dc, 1); D = min(D + float(fd) * dc, 1); c += dc + float(h) * dc * p["rework"]
    return c

def make_head_DD2(p, base):
    Kn = K_need(p); Kt = max(Kn, TARGET[0])
    def f(K, M, D, haz_max=0.05):
        gK, gM = max(TARGET[0] - K, 0), max(TARGET[1] - M, 0)
        if gM > 0 and K >= Kn - 1e-9 and float(hazard(K, p["lamT"], p)) <= haz_max: return "T"
        if gK > 0 or K < Kn:
            if v.Kbar_D(D, p) < Kt + max(DELTAS):
                best, cb = None, project(K, M, D, p, None, 0, Kt)
                for src in ("E", "T"):
                    if p.get("rho" + src, 0) <= 0: continue
                    for d in DELTAS:
                        if v.Kbar_D(D, p) < Kt + d:
                            cc = project(K, M, D, p, src, d, Kt)
                            if cc < cb: best, cb = src, cc
                if best: return best
            return base(K, M, D)
        return "T"
    return f
