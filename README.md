# Knowledge–Maturity Coevolution (KMC): code and supplementary material

Code, results, figures and Supplementary Materials S1–S3 for the article

> P. K. de Albuquerque, D. R. Pleffken, C. S. Cerqueira, and L. Galembeck, "Knowledge–Maturity Coevolution: A Coupled Evidence Model for Selecting Simulation and Test Activities in Constrained Engineering Development," submitted to *IEEE Access*, 2026.

Archived versions (this DOI always resolves to the latest): https://doi.org/10.5281/zenodo.23199996

Equation, table, figure and section numbers below refer to the article.

## Contents

| Folder | Content |
|---|---|
| `code/` | Model, experiments and figure scripts (Python), with the result files they produce (`.json`) |
| `code/tutorial/` | Scripts that reproduce every number and figure of Supplementary Material S1 |
| `code/guide/` | Sources of the S1 guide (`guide.js`) and of the worksheet (`ws.py`) |
| `code/s2/` | Source of Supplementary Material S2 (`build_s2.py`) and of its figures (`figs_s2.py`) |
| `code/s3/` | Source of Supplementary Material S3, studies added in revision (`build_s3.py`) |
| `code/rev1/` | Results of the revision studies |
| `figures/` | Figures 1–8 of the submitted article (vector PDF and 300-dpi PNG); in the revised article Fig4 is Fig. S3-1 and Fig5–Fig8 are Figs. 4–7 |
| `supplementary/` | Supplementary Material S1: application guide (`.pdf`, `.docx`) and calibration and decision worksheet (`.xlsx`); Supplementary Material S2: documented programs (`.pdf`, `.docx`); Supplementary Material S3: studies added in revision (`.pdf`, `.docx`) |

## Revision 1 (v1.1.0)

Version 1.1.0 adds the studies made in response to the reviewers (scripts `code/rev1_*.py`, results in `code/rev1/`, Supplementary Material S3 built by `code/s3/build_s3.py`) and two corrections:

- `relgrowth.py`: the profile-likelihood interval of Eq. (21) now profiles from several starting values of ν and locates each endpoint by root search. The 90% interval for the second NIST dataset is 0.664–0.988 (0.67–0.96 in v1.0.0, where the inner optimizer missed the profile minimum for M_∞ near 1).
- `fig8.py`: the test branch of the flowchart now includes the maturity-deficit condition of Table 6 (M < M_req), as in `kmc_model.policy_procedure`, which generated all results; the flowchart also shows the acceptance step (Table 6, step 6).

In the revised article the box plot of policy costs (`Fig4`, produced by `fig4.py`) moved to S3 (Fig. S3-1), so the files `Fig5`–`Fig8` here are Figs. 4–7 of the revised article. Section V-G now uses `rev1/two_claims_final2.json` (best policy found, 51⁴ grid, terminal test on the successor state) instead of `two_claims.json` (26⁴).

| Script | Reviewer item | Output |
|---|---|---|
| `rev1_valdata.py` | Validation-data state D separated from maturity; 3-D dynamic program (R1.1) | `rev1/valdata_*.json` |
| `rev1_valdata_rule.py` | Data-aware knowledge step of the headroom procedure (R1.1) | `rev1/valdata_rule.json` |
| `rev1_stopping.py` | Observable acceptance review with confirmation cost; decision agreement with the true state (R1.2, R2.3) | `rev1/stopping.json` |
| `rev1_constrained.py` | Optimum recomputed under the same hard exposure limit (R1.3) | `rev1/constrained.json` |
| `rev1_two_claims_conv.py`, `rev1_two_claims_final.py` | Grid convergence and confidence interval of the two-claim gap (R1.4) | `rev1/two_claims_*.json` |
| `rev1_assessors.py` | Assessor disagreement and bias (R2.2) | `rev1/assessors.json` |
| `rev1_valdata_rule2.py`, `rev1_valdata_rule2_cases.py`, `rev1_valdata_env.py` | Look-ahead knowledge step with data from E or T (a finding, not part of Table 6); six cases and 12 envelope sets (R1.1, R2.4) | `rev1/valdata_rule2.json`, `rev1/valdata_env.json` |
| `rev1_stopping2.py`, `rev1_stopping2_summary.py` | Acceptance review in 200 projects: operating characteristics (margin, confirmation cost, noise), information-matched known-coefficient benchmark (`known_hr`, `known_dp`), and observable reliability criterion (R1.2, R2.3) | `rev1/ck/`, `rev1/stopping2.json` |
| `rev1_budget.py` | Fixed budget as a finite horizon: probability of reaching the target, raised test gates (R1.3, R2.5) | `rev1/budget2.json` |
| `rev1_two_claims_conv2.py`, `rev1_two_claims_final2.py` | Two claims: terminal test on the successor state, grids 26^4-51^4, independent streams, gap against the best policy (R1.4) | `rev1/two_claims_convergence2.json`, `rev1/two_claims_final2.json` |
| `rev1_eT.py` | Sweep of the knowledge credit of integrated tests (R2.4) | `rev1/eT_sweep.json` |
| `rev1_launch_oos.py` | Exploratory out-of-sample check of the launch-data loss rates, 2003-2025 (S3.9; not used in the article); protocol `rev1/launch_oos_protocol.md`, records `rev1/launch_oos_records.csv` | `rev1/launch_oos.json` |

The first-round scripts `rev1_stopping.py`, `rev1_two_claims_conv.py`, `rev1_two_claims_final.py` and `rev1_valdata_rule.py` are kept for traceability; the article uses the second-round results listed above.

## Data

The base model inputs are synthetic (Table 5). Section VI uses public data, entered directly in the scripts:

- NIST/SEMATECH e-Handbook of Statistical Methods, reliability-growth datasets (`relgrowth.py`);
- FAA (2005), Guide to Probability of Failure Analysis for New Expendable Launch Vehicles, and Cross and Vesely (2018), early-flight failure data (`launch_calib.py`).

All organizations, projects and records in S1 (Org X, Rocket R, Project N) are fictional. S2 uses only public documents on real programs.

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

runs every script in order (about 2 h on 2 cores for the submitted version and about 10 h more for the revision scripts; `extensions.py` and `calib_adaptive.py` resume from checkpoints if interrupted). Each script can also be run alone; the result files are included, so the figure scripts run without the experiments.

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

### Supplementary Material S2

S2 expands Section VI-C: the readings of the six documented programs, the X-43A corpus and coverage audit, and the retrospective tables. All sources are public and cited by the article's reference numbers. From `code/s2/`:

```
python3 figs_s2.py      # Figures S2-1 and S2-2
python3 build_s2.py     # KMC_Supplementary_S2_Documented_Programs.docx (convert to PDF with LibreOffice)
```

## License

Code: MIT License (`LICENSE`). Figures, supplementary documents and result files: Creative Commons Attribution 4.0 International (CC BY 4.0).

## Citation

Please cite the article and the archived version (`CITATION.cff`).
