# Knowledge–Maturity Coevolution (KMC): code and supplementary material

Code, results, figures and Supplementary Material S1 for the article

> P. K. de Albuquerque, D. R. Pleffken, C. S. Cerqueira, and L. Galembeck, "Knowledge–Maturity Coevolution: A Coupled Evidence Model for Selecting Simulation and Test Activities in Constrained Engineering Development," submitted to *IEEE Access*, 2026.

Archived version: https://doi.org/10.5281/zenodo.23199997

Equation, table, figure and section numbers below refer to the article.

## Contents

| Folder | Content |
|---|---|
| `code/` | Model, experiments and figure scripts (Python), with the result files they produce (`.json`) |
| `code/tutorial/` | Scripts that reproduce every number and figure of Supplementary Material S1 |
| `code/guide/` | Sources of the S1 guide (`guide.js`) and of the worksheet (`ws.py`) |
| `figures/` | Figures 1–8 of the article (vector PDF and 300-dpi PNG) |
| `supplementary/` | Supplementary Material S1: application guide (`.pdf`, `.docx`) and calibration and decision worksheet (`.xlsx`) |

## Data

The base model inputs are synthetic (Table 5). Section VI uses public data, entered directly in the scripts:

- NIST/SEMATECH e-Handbook of Statistical Methods, reliability-growth datasets (`relgrowth.py`);
- FAA (2005), Guide to Probability of Failure Analysis for New Expendable Launch Vehicles, and Cross and Vesely (2018), early-flight failure data (`launch_calib.py`).

All organizations, projects and records in S1 (Org X, Rocket R, Project N) are fictional.

## Requirements

Python 3.10 or later with the packages in `requirements.txt`:

```
pip install -r requirements.txt
```

Rebuilding the S1 guide from its source also needs Node.js and the `docx` package (`npm install` in `code/guide/`); the worksheet needs `openpyxl`.

## Reproducing the results

From `code/`:

```
./run_all.sh
```

runs every script in order (about 2 h on 2 cores; `extensions.py` and `calib_adaptive.py` resume from checkpoints if interrupted). Each script can also be run alone; the result files are included, so the figure scripts run without the experiments.

| Script | Reproduces | Output |
|---|---|---|
| `kmc_model.py` | Model: ceilings and rates, Eqs. (8)–(11); value iteration, Eq. (12); decision rules, including the headroom procedure of Table 6 and the two-phase threshold baseline; Monte Carlo simulation | module |
| `analysis.py` | Optimal curve and switch points; policy comparison and scenarios (Table 7); planner with misspecified parameters; recoding check (Sec. IV-D); estimation from assessments (Sec. V-F) | `results.json` |
| `envelope.py` | Literature-anchored parameter envelope, 300 sets (Sec. V-D) | `envelope.json` |
| `robustness.py` | Alternative functional forms, Eq. (19) (Sec. V-E, Table 8), and discretization check (Sec. V-A) | `robustness.json` |
| `two_claims.py` | Two claims sharing an integrated test, Eq. (20) (Sec. V-G) | `two_claims.json` |
| `relgrowth.py` | Fit of the saturating dynamics, Eq. (21), to reliability-growth data (Sec. VI-A) | `relgrowth.json` |
| `launch_calib.py` | Test hazard and per-flight knowledge gain from launch data, Eq. (18) (Sec. VI-B) | `launch_calib.json` |
| `launch_variant.py` | Launch-data variants from different starting knowledge (Table 8, last five rows) and procedure with knowledge built only by S or E (Sec. VI-B) | `launch_variant.json` |
| `ktest_variant.py` | Hard exposure limit: the procedure waits for K ≥ K_test, Eq. (17b) (Secs. V-C, V-D) | `ktest_variant.json` |
| `extensions.py` | Hard limit in the scenarios and forms, tuned two-phase threshold baseline, ablations of the couplings, launch-data variants (Secs. V-C, V-H, VI-B) | `extensions.json` |
| `calib_replicates.py` | Estimation from noisy assessments, 40 replications: plans fitted once (Sec. V-F) | `calib_replicates.json` |
| `calib_adaptive.py` | Estimation with re-fitting and re-planning after every assessment, with a weak prior; the policy sees the true state (`true`) or only the noisy assessments (`est`) (Sec. V-F) | `calib_adaptive.json`, `calib_adaptive_est.json` |
| `fig1.py` … `fig8.py` | Figures 1–8 | `../figures/Fig1.pdf` … `Fig8.pdf` (and `.png`) |

Monte Carlo runs use fixed seeds, so the numbers are reproducible on the same platform; other NumPy versions can change the last digit of Monte Carlo means.

### Supplementary Material S1

From `code/tutorial/` (the scripts import `../kmc_model.py`):

```
python3 calib.py     # calibration of Org X -> calib.json
python3 apply.py     # Project N: thresholds, decisions, D_a, Monte Carlo -> apply.json
python3 variant.py   # exposure-limit sweep -> variant.json
python3 update.py    # posterior update after the project -> update.json
python3 figs.py      # Figures S1-S4
```

Then, in `code/guide/`, `node guide.js` rebuilds the guide (`.docx`) and `python3 ws.py` rebuilds the worksheet.

## License

Code: MIT License (`LICENSE`). Figures, supplementary documents and result files: Creative Commons Attribution 4.0 International (CC BY 4.0).

## Citation

Please cite the article and the archived version (`CITATION.cff`).
