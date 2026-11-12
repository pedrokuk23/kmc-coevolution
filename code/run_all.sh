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
# Revision 1 (v1.1.0): studies added in response to the reviewers (results in rev1/, details in S3)
python3 rev1_valdata.py 1000 0                      # rev1/valdata_0.json (D tied to M: reduces to the base model)
python3 rev1_valdata.py 1000 1,2,3,4,5,6            # rev1/valdata_1_2_3_4_5_6.json (Sec. V-H, Table S3-1)
python3 rev1_valdata_rule.py 1000                   # rev1/valdata_rule.json (data-aware knowledge step)
python3 rev1_stopping.py 40 0,0.03                  # rev1/stopping.json, rev1/decision_agreement.json (Sec. V-F)
python3 rev1_assessors.py                           # rev1/assessors.json (Sec. V-F, Table S3-4)
python3 rev1_constrained.py                         # rev1/constrained.json (Sec. V-C)
GRIDS=21:0.5,26:0.5,31:0.5,36:0.5 OUT=rev1/two_claims_convergence_part1.json python3 rev1_two_claims_conv.py   # Table S3-5
GRIDS=41:0.5,46:0.5,36:0.25 OUT=rev1/two_claims_convergence_part2.json python3 rev1_two_claims_conv.py
python3 rev1_two_claims_final.py                    # rev1/two_claims_final.json (Sec. V-G, 46^4 grid)
(cd s3 && python3 build_s3.py)                      # Supplementary Material S3 (.docx)
