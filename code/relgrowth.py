"""Fit the KMC integrated-test maturity dynamics to public reliability-growth data (NIST/SEMATECH e-Handbook).
KMC (T at fixed K, M0=0): M(t) = m(1-exp(-r t)),  failure intensity lam(t) = a[1 - M(t)] = a[(1-m) + m exp(-r t)]
Crow-AMSAA power law:   lam(t) = l*b*t^(b-1)."""
import numpy as np, json
from scipy.optimize import minimize
from scipy.stats import chi2
DATA = {"NIST 8.1.9.2 (Duane plot example)": ([33, 76, 145, 347, 555, 811, 1212, 1499], 1500.0),
        "NIST 8.4.5.2 (power-law case study)": ([5, 40, 43, 175, 389, 712, 747, 795, 1299, 1478], 1500.0)}

def nll_kmc(th, t, T):
    la, lm, lr = th; a = np.exp(la); m = 1 / (1 + np.exp(-lm)); r = np.exp(lr)
    lam = a * ((1 - m) + m * np.exp(-r * t))
    Lam = a * ((1 - m) * T + m * (1 - np.exp(-r * T)) / r)
    return -(np.sum(np.log(lam)) - Lam)

def fit_kmc(t, T):
    best = None
    for lm0 in (-1, 0.5, 2, 4):
        for lr0 in np.log([1e-4, 1e-3, 1e-2, 5e-2]):
            res = minimize(nll_kmc, [np.log(len(t) / T * 3), lm0, lr0], args=(t, T), method="Nelder-Mead",
                           options=dict(maxiter=20000, xatol=1e-8, fatol=1e-10))
            if best is None or res.fun < best.fun: best = res
    la, lm, lr = best.x
    return dict(a=float(np.exp(la)), m=float(1 / (1 + np.exp(-lm))), r=float(np.exp(lr)), nll=float(best.fun)), best.x

def profile_m(t, T, nll_hat):
    ms = np.linspace(0.01, 0.995, 200); prof = []
    for m in ms:
        lm = np.log(m / (1 - m))
        f = lambda th: nll_kmc([th[0], lm, th[1]], t, T)
        best = min((minimize(f, [np.log(len(t) / T * 3), lr0], method="Nelder-Mead") for lr0 in np.log([1e-4, 1e-3, 1e-2])), key=lambda r: r.fun)
        prof.append(best.fun)
    prof = np.array(prof); ok = ms[prof - nll_hat <= chi2.ppf(0.90, 1) / 2]
    return float(ok.min()), float(ok.max())

def fit_pl(t, T):
    n = len(t); b = n / np.sum(np.log(T / t)); l = n / T ** b
    nll = -(n * np.log(l * b) + (b - 1) * np.sum(np.log(t)) - l * T ** b)
    return dict(beta=float(b), lam=float(l), nll=float(nll))

if __name__ == "__main__":
    out = {}
    for name, (t, T) in DATA.items():
        t = np.array(t, float)
        k, _ = fit_kmc(t, T); pl = fit_pl(t, T)
        lo, hi = profile_m(t, T, k["nll"])
        aic_k = 2 * 3 + 2 * k["nll"]; aic_p = 2 * 2 + 2 * pl["nll"]
        mtbf_end_k = 1 / (k["a"] * ((1 - k["m"]) + k["m"] * np.exp(-k["r"] * T)))
        mtbf_end_p = 1 / (pl["lam"] * pl["beta"] * T ** (pl["beta"] - 1))
        out[name] = dict(n=len(t), T=T, kmc=k, m_CI90=(lo, hi), powerlaw=pl, AIC_kmc=aic_k, AIC_pl=aic_p,
                         MTBF_end_kmc=float(mtbf_end_k), MTBF_end_pl=float(mtbf_end_p),
                         M_end=float(k["m"] * (1 - np.exp(-k["r"] * T))))
    json.dump(out, open("relgrowth.json", "w"), indent=1)
    for k, v in out.items(): print(k, json.dumps(v, indent=0)[:900])
