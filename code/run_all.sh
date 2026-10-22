#!/bin/sh
# Reproduces every result and figure of the article. Run from this folder.
# Total time about 2 h on 2 cores (envelope.py about 45 min).
# Interrupted runs of extensions.py and calib_adaptive.py resume from their checkpoint files (_ext_*.json, _ca_*.json).
set -e
python3 analysis.py       > /dev/null   # results.json (Table 7, Figs. 3, 4, 6)
python3 envelope.py 300                 # envelope.json (Sec. V-D)
python3 robustness.py                   # robustness.json (Table 8, Sec. V-A grid check)
python3 two_claims.py                   # two_claims.json (Sec. V-G)
python3 relgrowth.py      > /dev/null   # relgrowth.json (Sec. VI-A)
python3 launch_calib.py                 # launch_calib.json (Sec. VI-B)
python3 launch_variant.py               # launch_variant.json (Table 8, last five rows)
python3 ktest_variant.py                # ktest_variant.json (hard exposure limit, Secs. V-C, V-D)
python3 extensions.py                   # extensions.json (hard limit, tuned threshold, ablations; Secs. V-C, V-H, VI-B)
python3 calib_replicates.py 40          # calib_replicates.json (one-time fits, Sec. V-F)
python3 calib_adaptive.py 40 true       # calib_adaptive.json (re-estimation with prior, true state, Sec. V-F)
python3 calib_adaptive.py 40 est        # calib_adaptive_est.json (state known only through assessments, Sec. V-F)
for i in 1 2 3 4 5 6 7 8; do python3 fig$i.py > /dev/null; done   # ../figures/Fig1-Fig8 (.pdf, .png)
