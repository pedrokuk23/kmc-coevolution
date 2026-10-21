"""Calibrate the integrated-test hazard and per-flight knowledge gain from published launch-vehicle early-flight data."""
import numpy as np, json
from scipy.optimize import least_squares
n = np.array([0, 1, 2, 3, 5, 10]); p = np.array([0.134, 0.070, 0.048, 0.036, 0.024, 0.013])  # Cross & Vesely 2018, Table 4
K0, c = 0.15, 2.0
lc = -np.log(1 - 8 / 11) / (1 - K0) ** 2            # FAA 2005: inexperienced developers 8/11 first-flight failures
Kexp = 1 - np.sqrt(-np.log(1 - 5 / 18) / lc)        # experienced developers 5/18
u = np.sqrt(-np.log(1 - p) / lc)
def sim(q, g, u0, N=10):
    us = [u0]
    for i in range(N): us.append(us[-1] - g * us[-1] ** q)
    return np.array(us)
r1 = least_squares(lambda th: sim(1, th[0], th[1])[n] - u, [0.3, 0.28], bounds=([0, 0], [10, 1]))
rq = least_squares(lambda th: sim(th[2], th[0], th[1])[n] - u, [0.5, 0.28, 2], bounds=([0, 0, 0.5], [50, 1, 6]))
out = dict(lambda_c=lc, lambda_T=lc / c, K_exp=Kexp, K_implied=list(1 - u), q=rq.x[2], g_per_flight=rq.x[0],
           g_per_BU=rq.x[0] / c, rmse_q=float(np.sqrt(np.mean(rq.fun ** 2))), rmse_1=float(np.sqrt(np.mean(r1.fun ** 2))))
json.dump(out, open("launch_calib.json", "w"), indent=1); print(out)
