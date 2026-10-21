#!/bin/sh
# Reproduces every result and figure of the article. Run from this folder.
# Total time about 1 h on 2 cores, most of it in envelope.py.
set -e
python3 analysis.py       > /dev/null   # results.json (Table 7, Figs. 3, 4, 6 numbers)
python3 envelope.py 300                 # envelope.json (Sec. V-D)
python3 robustness.py                   # robustness.json (Table 8)
python3 two_claims.py                   # two_claims.json (Sec. V-G)
python3 relgrowth.py      > /dev/null   # relgrowth.json (Sec. VI-A)
python3 launch_calib.py                 # launch_calib.json (Sec. VI-B)
python3 launch_variant.py               # launch_variant.json (Table 8, last two rows)
python3 ktest_variant.py                # ktest_variant.json (end of Sec. V-D)
for i in 1 2 3 4 5 6 7 8; do python3 fig$i.py > /dev/null; done   # ../figures/Fig1-Fig8 (.pdf, .png)
