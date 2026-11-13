"""Supplementary Material S3: studies added in revision 1 (reads ../rev1/*.json and ../relgrowth.json)."""
import json, sys, os
import numpy as np
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
J = lambda f: json.load(open(os.path.join(D, f)))
FONT, INK, BLUE = "Arial", RGBColor(0x1F, 0x2A, 0x37), RGBColor(0x1D, 0x5B, 0x8F)

def shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr(); s = OxmlElement("w:shd"); s.set(qn("w:val"), "clear"); s.set(qn("w:color"), "auto"); s.set(qn("w:fill"), hexcolor); tcPr.append(s)
def run(p, text, size=10, bold=False, italic=False, color=INK):
    r = p.add_run(text); r.font.name = FONT; r.font.size = Pt(size); r.bold = bold; r.italic = italic; r.font.color.rgb = color
    r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT); return r
def para(doc, text, size=10, bold=False, italic=False, color=INK, align=WD_ALIGN_PARAGRAPH.JUSTIFY, after=6, before=0, keep=False):
    p = doc.add_paragraph(); p.alignment = align; f = p.paragraph_format; f.space_after = Pt(after); f.space_before = Pt(before); f.line_spacing = 1.15
    f.keep_with_next = keep; run(p, text, size, bold, italic, color); return p
def table(doc, cap, head, rows, widths, width, fs=8):
    para(doc, cap, 8.5, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, before=4, after=3, keep=True)
    t = doc.add_table(rows=1, cols=len(head)); t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(head):
        c = t.rows[0].cells[j]; c.text = ""; shade(c, "DCE8F3"); run(c.paragraphs[0], h, fs, bold=True)
    trPr = t.rows[0]._tr.get_or_add_trPr(); e = OxmlElement("w:tblHeader"); e.set(qn("w:val"), "true"); trPr.append(e)
    for r in rows:
        cells = t.add_row().cells
        for j, v in enumerate(r): cells[j].text = ""; run(cells[j].paragraphs[0], str(v), fs)
    for row in t.rows:
        trPr = row._tr.get_or_add_trPr(); e = OxmlElement("w:cantSplit"); e.set(qn("w:val"), "true"); trPr.append(e)
        for j, c in enumerate(row.cells): c.width = int(width * widths[j] / sum(widths))
    para(doc, "", 4, after=4)

def build(out):
    doc = Document(); sec = doc.sections[0]; sec.page_width, sec.page_height = Inches(8.5), Inches(11)
    for s in ("left_margin", "right_margin", "top_margin", "bottom_margin"): setattr(sec, s, Inches(0.9))
    W = sec.page_width - sec.left_margin - sec.right_margin
    H1 = lambda t: para(doc, t, 12, bold=True, color=BLUE, align=WD_ALIGN_PARAGRAPH.LEFT, before=8, after=4, keep=True)
    P = lambda t: para(doc, t)
    para(doc, "Supplementary Material S3: Studies Added in Revision", 15, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, after=4)
    para(doc, "Knowledge–Maturity Coevolution: A Coupled Evidence Model for Selecting Simulation and Test Activities in Constrained Engineering Development. P. K. de Albuquerque, D. R. Pleffken, C. S. Cerqueira, and L. Galembeck.", 9, italic=True, align=WD_ALIGN_PARAGRAPH.LEFT, after=8)
    P("This supplement gives the details of the studies added in response to the reviewers. Equation, table, and section numbers refer to the article. All inputs are synthetic or public; costs are in budget units (BU). Every number is produced by the scripts named in each section (folder code/ of the archived package); Monte Carlo comparisons use common random numbers, and intervals are 95% bootstrap intervals of the paired differences.")

    # 0. cost distributions (moved from the article)
    H1("S3.0 Cost distributions in the base scenario (Section V-C)")
    P("To make room for the revision, the box plot of the policy costs in the base scenario (Fig. 4 of the submitted version) was moved here. Table 7 of the article gives the means and 90th percentiles of the same runs.")
    doc.add_picture(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fig_s3_1.png"), width=Inches(6.4))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    para(doc, "Fig. S3-1. Cost to reach the terminal region by policy (base scenario, 2000 runs). Boxes: quartiles; whiskers: 5th–95th percentiles; labels: mean cost and mean shocks per run.", 8.5, align=WD_ALIGN_PARAGRAPH.LEFT, after=8)

    # 1. validation data
    VD = J("rev1/valdata_1_2_3_4_5_6.json"); VR = {c["case"]: c for c in J("rev1/valdata_rule2.json")}; V0 = J("rev1/valdata_0.json")[0]
    H1("S3.1 Validation-data availability separated from maturity (Section V-H)")
    P("Equation (10) writes the simulation ceiling as K̄(M) = min(1, k_b + k_l M), taking demonstrated maturity as the proxy for the validation data available. The extended model adds a third state D ∈ [0, 1], the share of the intended-use domain covered by validation-grade data. Simulation raises K at r_S[K̄(D) − K]+ with K̄(D) = min(1, k_b + k_l D) and does not change D; separate-effects tests raise K at r_E(1 − K), M at e_E[M̄(K) − M]+ and D at ρ_E(1 − D); integrated tests raise K at e_T(1 − K), M at r_T[M̄(K) − M]+ and D at ρ_T(1 − D). Shocks reduce K and M as in the base model and leave D unchanged, and D_0 = 0.10 = M_0. The optimum was computed by value iteration on a 61³ grid (Δc = 0.1 BU). With D tied to M (dD = dM, shocks reducing D like M) the model reduces to the base model: the three-dimensional value at x_0 was within "
      f"{abs(V0['V3_x0']/V0['V2_x0']-1)*100:.1f}% of the two-dimensional value, and the plans of the two models gave the same mean cost within {abs(V0['policies']['opt2']['excess_pct']):.2f}%.")
    P("Policies: opt3, the optimum of the extended model; opt2, the optimum of the base model applied to the true (K, M), a plan that ignores D; headroom, the procedure of Table 6 with the true rates; look-ahead headroom (a finding, not part of Table 6, because D and its rates are not estimated here), the same procedure whose knowledge step compares, by deterministic projection with the rates of the model (the true ones here) and without a dynamic program, the cost to reach K_target = max(K_need, K_req) along the greedy plan and along plans that first raise D by separate-effects tests or by integrated tests until K̄(D) ≥ K_target + δ, δ ∈ {0.02, 0.05, 0.10, 0.15, 0.20, 0.25}, and takes the first activity of the cheapest plan; threshold, the two-phase rule with K_th tuned by simulation on independent runs; and the stylized proxies. 1000 paired runs per policy (scripts rev1_valdata.py, rev1_valdata_rule2.py, rev1_valdata_rule2_cases.py).")
    rows = []
    for c in VD:
        pp = c["policies"]; r = VR.get(c["case"], {}).get("policies", {})
        f = lambda d: f"{d['excess_pct']:.1f} [{d['excess_ci95'][0]:.1f}, {d['excess_ci95'][1]:.1f}]"
        rows.append([f"ρ_E = {c['params']['rhoE']:.2f}, ρ_T = {c['params']['rhoT']:.2f}", f"{pp['opt3']['mean']:.2f}", f(pp["opt2"]), f(pp["head_D"]),
                     f(r["head_DD2"]) if "head_DD2" in r else "—", f"{pp['thr_D']['excess_pct']:.1f} (K_th = {c['K_th']:.2f})",
                     f"{pp['analysis_first']['excess_pct']:.0f}", f"{pp['test_first']['excess_pct']:.0f}"])
    table(doc, "TABLE S3-1. Excess mean cost over the optimum of the extended model (%, 95% interval), base parameters.",
          ["Case", "opt3 (BU)", "opt2 (base plan)", "Headroom", "Look-ahead headroom", "Tuned threshold", "Analysis-first", "Test-first"], rows, [1.5, 0.7, 1.1, 1.1, 1.1, 1.1, 0.7, 0.7], W)
    VE = J("rev1/valdata_env.json"); E_ = VE["envelope"]
    P(f"Envelope: for the first {len(E_)} reachable parameter sets of Section V-D (same draws as the article), with ρ_T = r_T and ρ_E = 0.05 or 0.40, the extended model was solved on a 41³ grid (targets on grid nodes; on the base set with ρ_E = 0.40 the 41³ and 61³ grids gave the same excess within about 1 point) and each policy was simulated on 300 paired runs (script rev1_valdata_env.py).")
    rows = [[str(r["seed"]), *[f"{r[k][pol]:.1f}" for k in ("0.05", "0.4") for pol in ("opt2", "head_D", "head_DD2")]] for r in E_]
    table(doc, "TABLE S3-2. Excess over the optimum of the extended model (%) in each envelope set (ρ_T = r_T); with 12 sets, no percentiles are given.",
          ["Set", "ρ_E = 0.05: base plan", "headroom", "look-ahead", "ρ_E = 0.40: base plan", "headroom", "look-ahead"], rows, [0.5, 1.0, 0.9, 0.9, 1.0, 0.9, 0.9], W)
    rows = [[nm.replace("base, ", "Base set, "), f"{v['opt2']:.1f}", f"{v['head_D']:.1f}", f"{v['head_DD2']:.1f}"] for nm, v in VE["base_variants"].items()]
    table(doc, "TABLE S3-2b. Single variants of the base set (41³ grid).", ["Case", "Base plan", "Headroom", "Look-ahead headroom"], rows, [2.2, 1.0, 1.0, 1.2], W)
    P("In sets 8 and 10 with ρ_E = 0.05, integrated tests (ρ_T = r_T) raised D faster than M, and the base plan lost 13–14%: the relevant condition is whether validation-data coverage tracks demonstrated maturity, not which activity supplies the data. The look-ahead step helped in most sets where coverage outran maturity, but not in all, and it is not free: it added 4.5 points in set 9 with ρ_E = 0.05, where coverage tracked maturity, and 8.6 points in set 10 with ρ_E = 0.05, where integrated tests outran it (23.1% against the headroom procedure's 14.5%). All sets start from the base initial state, not from the initial maturity sampled in Section V-D. The values of ρ_E and ρ_T are illustrative, not calibrated; an observable symptom of the fast-data regime is a rise of the simulation ceiling after separate-effects tests without a corresponding rise of M.")

    # 2. acceptance review and operating characteristics
    S2 = J("rev1/stopping2.json"); C2 = S2["conditions"]
    H1("S3.2 Observable acceptance and operating characteristics (Section V-F)")
    P(f"Closed loop of Section V-F: assessments every 3 BU with noise of standard deviation σ on each axis; coefficients re-fitted after each assessment with the weak prior; between assessments the policy acts on the state predicted by the fitted model. Acceptance review (Table 6, step 6): when the estimated state, or the latest assessment, is in X_f, a confirmation assessment is bought and the claim is accepted if it reads at least the target plus a margin on both axes; otherwise the assessment joins the data and work continues (no new review within 1 BU). Review costs are added outside the activity clock, so totals for any confirmation cost C are exact from one run. The reference is the optimal policy of the true model stopping when the true state reaches X_f ({S2['oracle_mean']:.1f} BU on the same random numbers). Premature: true state outside X_f at acceptance (95% Wilson interval). Script rev1_stopping2.py, summary rev1_stopping2_summary.py.")
    nm = {"headroom": "Headroom", "dp": "Re-planned optimum", "dp_known": "CE, raw readings", "known_hr": "Headroom, known coeff.", "known_dp": "Optimum, known coeff."}
    rows = []
    for k in sorted(C2, key=lambda s: (float(s.split("|")[0]), float(s.split("|")[1]), s.split("|")[2])):
        v = C2[k]
        rows.append([f"{v['noise']:.2f}", f"{v['margin']:.3f}", nm[v["kind"]], str(v["n"]),
                     f"{v['C1.0']['mean']:.1f} [{v['C1.0']['mean_ci95'][0]:.1f}, {v['C1.0']['mean_ci95'][1]:.1f}]",
                     f"{v['C0.5']['mean']:.1f} / {v['C2.0']['mean']:.1f}", f"{v['C1.0']['excess_vs_oracle']:.1f}",
                     f"{100*v['premature_rate']:.1f} [{100*v['premature_ci95'][0]:.0f}, {100*v['premature_ci95'][1]:.0f}]", f"{v['deficit_when_premature']:.3f}",
                     f"{v['reviews_mean']:.1f}", str(v["not_accepted"])])
    P("Information-matched benchmarks (rows 'known coeff.'): the same rule with the true coefficients and the same information as the estimating procedure (exact initial state, observed shocks, model replay between assessments), so its state estimate is exact. All runs assume the initial state and the size of each shock known. The row 'CE, raw readings' (optimal policy of the true model acting on the latest raw assessment) uses less information than the estimating procedures and is not a fair benchmark; it is kept for traceability. The optimal policy of the true model is not defined beyond X_f, so with a margin it may stall after a failed confirmation (column 'Not accepted'). Premature acceptances with a mean deficit of 0.000 are states within the 0.005 tolerance of the simulator, counted as premature because the classification uses the exact target.")
    table(doc, "TABLE S3-3. Operating characteristics of the acceptance review.",
          ["σ", "Margin", "Policy", "Projects", "Mean cost, C = 1 BU [95%]", "C = 0.5 / 2 BU", "Excess over reference (%)", "Premature (%) [95%]", "Mean deficit if premature", "Reviews", "Not accepted"],
          rows, [0.4, 0.5, 1.0, 0.55, 1.15, 0.85, 0.75, 1.05, 0.7, 0.55, 0.55], W, fs=7)

    rows = [[n_, f"{r['margin']:.3f}", f"{100*r['premature_est']:.1f}", f"{r['cost_est']:.2f}", f"{r['known_margin']:.3f}", f"{100*r['premature_known']:.1f}", f"{r['cost_known']:.2f}", f"{r['excess_pct']:.1f}"] for n_, rr in S2["matched"].items() for r in rr]
    P("The matching uses point estimates of premature rates that rest on few events (for example 7 of 200 projects), whose Wilson intervals overlap; the excess should be read as an order of magnitude (about a tenth of the budget), not as a precise value.")
    table(doc, "TABLE S3-3b. Cost of estimating the coefficients at matched premature acceptance: headroom with estimated coefficients against the cheapest known-coefficient condition with an equal or lower premature rate.",
          ["σ", "Margin (est.)", "Premature, est. (%)", "Cost, est. (BU)", "Margin (known)", "Premature, known (%)", "Cost, known (BU)", "Excess (%)"], rows, [0.5, 0.7, 0.8, 0.8, 0.7, 0.8, 0.8, 0.7], W)

    # 3. decision reliability
    H1("S3.3 Reliability of the recommended activity (Section V-F)")
    P("At every 1 BU of the runs of S3.2, the activity chosen with estimated coefficients and estimated state is compared with the activity that the same rule chooses at the true state with the true coefficients (for the re-planned optimum and the certainty-equivalent policy, the optimal policy of the true model). Decisions are grouped by the estimated margin K̂ − K̂_need, which the decision maker can compute. The observable criterion compares |K̂ − K̂_need| with twice the standard deviation s of the estimates of K_need over the re-fits of the last 6 BU.")
    bins = list(C2["0.03|0.0|headroom"]["agreement_by_est_margin"].keys())
    rows = []
    for k in ("0.02|0.0|headroom", "0.03|0.0|headroom", "0.05|0.0|headroom", "0.03|0.0|dp"):
        v = C2[k]; cr = v["criterion_refit_2s"]
        rows.append([f"{v['noise']:.2f}", nm[v["kind"]], f"{100*v['agreement']:.0f}"] +
                    [("—" if v["agreement_by_est_margin"][b][0] is None else f"{100*v['agreement_by_est_margin'][b][0]:.0f} ({v['agreement_by_est_margin'][b][1]})") for b in bins] +
                    [f"{100*cr['share_outside']:.0f}", f"{100*cr['agree_outside']:.0f} / {100*cr['agree_inside']:.0f}", f"{v['Kneed_abs_error_median']:.3f}"])
    table(doc, "TABLE S3-4. Agreement with the decision at the true state (%; decision points in parentheses), by estimated margin K̂ − K̂_need, and the observable criterion.",
          ["σ", "Policy", "All"] + [b.replace("-9..", "< ").replace("..9", " +").replace("..", " to ") for b in bins] + ["Outside 2s (%)", "Agreement outside / inside", "Median |K̂_need − K_need|"],
          rows, [0.35, 0.95, 0.35, 0.8, 0.8, 0.8, 0.8, 0.5, 0.6, 0.75, 0.7], W, fs=7)
    P("The standard deviation of K̂_need from the curvature of the least-squares fit, which includes the weak prior, had a median of about 0.07 and did not separate reliable from unreliable decisions; the scatter over successive re-fits (median about 0.013) did.")

    # 4. assessors
    AS = J("rev1/assessors.json")
    H1("S3.4 Assessor disagreement (Sections III-H and V-F)")
    P("With the coefficients known, K and M are assessed every 3 BU by an assessor whose reading differs from the true state by a random error (a different assessor each time) and/or a persistent bias; between assessments the decision maker uses the model prediction from the last assessment, and acceptance uses the review of S3.2 (margin 0). Errors are stated in units of K and are assumed, not estimated. As an illustrative conversion only, a difference of one level on one of the five K criteria of Table 4 would move K by 0.05 if the anchors were equally spaced, which Section III-H does not assume. 'Excess' is relative to the same policy observing the true state (plus one review). 'Early tests' is the share of integrated tests started while the true K < K_need (script rev1_assessors.py, 600 runs per condition).")
    rows = []
    for k, v in AS["results"].items():
        c, pname = k.split(" | ")
        rows.append([c, pname, f"{v['mean']:.1f}", f"{v['excess_vs_true_state']:.1f}", f"{100*v['decision_agreement']:.0f}", f"{100*v['early_test_share']:.0f}", f"{100*v['premature_acceptance']:.0f}"])
    table(doc, "TABLE S3-5. Effect of assessor disagreement.", ["Condition", "Policy", "Mean cost (BU)", "Excess (%)", "Decision agreement (%)", "Early tests (%)", "Premature acceptance (%)"], rows, [1.6, 0.8, 0.8, 0.7, 0.9, 0.8, 0.9], W)

    # 5. constrained benchmark
    CL = J("rev1/constrained.json")
    H1("S3.5 Exposure limit imposed on the benchmark (Section V-C)")
    e = CL["envelope"]; lh = CL["launch_hazard"]
    P(f"The headroom procedure with a hard exposure limit (h_max = 0.05 BU⁻¹; step 3b builds knowledge until K ≥ K_test) is compared with the optimum of (12) computed with the same limit: an activity whose hazard per BU exceeds h_max at the current state is inadmissible. Over the {e['n']} parameter sets of Section V-D (150 runs each, the seeds of the envelope study), the limit was binding (K_haz > K_need) in {e['binding']} sets. The median excess over the limited optimum was {e['excess_vs_limited_median']:.1f}% (90th percentile {e['excess_vs_limited_p90']:.1f}%, maximum {e['excess_vs_limited_max']:.1f}%), against {e['excess_vs_unconstrained_median']:.1f}% when measured against the unconstrained optimum as in the submitted version. With the launch-data hazard (λ_T = 0.90 BU⁻¹, K_haz = {lh['K_haz']:.2f} > K_need = {lh['K_need']:.2f}), the limited optimum cost {lh['dp_limited']:.1f} BU and the procedure {lh['headroom_hard']:.1f} BU ({lh['excess_vs_limited']:.1f}%). Only the headroom procedure was run under the limit; the other rules are compared without it (script rev1_constrained.py).")

    # 6. budget
    BU = J("rev1/budget2.json")
    H1("S3.6 A fixed budget as a finite horizon (Sections IV-C and V-C)")
    P("Cost is the independent variable of (8), so a budget B is a finite horizon of B/Δc steps. The budget-aware policy maximizes the probability of reaching X_f within B: W_b(x) = max_a [(1 − p_a) W_{b−1}(x + f_a Δc) + p_a W_{b−1−ρ/Δc}(x − δ)], W = 1 on X_f and W_b = 0 for b ≤ 0 outside X_f, solved by backward induction on a 241² grid with the same terminal tolerance as the simulator (0.005); the action is taken from the stored W_b by linear interpolation at the successor states, with near-ties broken by the cost-optimal policy. On the 121² grid of (12), numerical diffusion of the sharp success front made this policy noticeably suboptimal (a raised-gate headroom variant beat it), which motivated the finer grid. Each policy was simulated with the same budget on 4000 common random streams; budgets are 1.0, 1.25, and 1.5 times the mean cost of the cost-optimal policy. The headroom procedure was also run with its test gate raised to K_need + δ. Schedule enters the same way when activity durations are proportional to cost (script rev1_budget.py; paired differences with bootstrap intervals in rev1/budget2.json).")
    rows = []
    for sc, v in BU.items():
        for f, r in v["budgets"].items():
            pp = r["policies"]
            rows.append([sc.replace("Costly, risky tests", "Costly, risky"), f"{r['B']:.1f} ({f}×)"] + [f"{100*pp[k]['p_success']:.1f}" for k in ("budget", "dp", "threshold", "headroom", "headroom+0.03", "headroom+0.06", "headroom+0.1")] +
                        [f"{pp[k]['first_T_K_median']:.2f}" for k in ("budget", "headroom")])
    table(doc, "TABLE S3-6. Probability (%) of reaching X_f within the budget (4000 runs; standard error at most 0.8 points), and median K at the first integrated test.",
          ["Scenario", "Budget (BU)", "Budget-aware", "Cost-optimal", "Tuned threshold", "Headroom", "Gate +0.03", "Gate +0.06", "Gate +0.10", "K first T: budget-aware", "headroom"],
          rows, [0.9, 0.8, 0.65, 0.65, 0.65, 0.65, 0.6, 0.6, 0.6, 0.75, 0.65], W, fs=7)

    # 7. two claims
    G2 = J("rev1/two_claims_convergence2.json"); TF = J("rev1/two_claims_final2.json")
    H1("S3.7 Grid convergence of the two-claim model (Section V-G)")
    hw = float(np.mean(G2["fixed"]["Headroom, weakest link"]))
    P(f"In the submitted version, the four-dimensional program enforced the terminal region only at grid nodes, so on grids whose spacing does not divide the targets (K_req = 0.75, M_req = 0.80) the effective target rose to the next node, which biased V(x_0) and the policy (on 36⁴, V(x_0) = 42.9 BU against about 40 BU on the neighboring grids). After the correction, V(x_0) on 36⁴ (40.7 BU) still differs from the neighboring grids (40.2 BU), because the targets do not fall on its nodes and the value is interpolated near the boundary of X_f; the simulated costs of the policies, which the article uses, decrease monotonically with the grid. The revised solver applies the terminal condition to the successor state itself. Each optimal policy and the headroom procedures were simulated on {G2['runs']} streams not used before (seeds from {G2['seed0']}). Because every policy's mean cost bounds the optimum from above, gaps are given against each grid's policy and against the best policy found; they are lower bounds on the gaps to the exact optimum (scripts rev1_two_claims_conv2.py and rev1_two_claims_final2.py).")
    rows = [[f"{r['n']}⁴", f"{r['dc']:.2f}", f"{r['V_x0']:.2f}", f"{r['mean']:.2f} ± {r['sem']:.2f}", f"{100*(hw/r['mean']-1):.1f}", f"{r['secs']/60:.0f}"] for r in sorted(G2["grids"], key=lambda r: (r['dc'] < 0.5, r['n']))]
    table(doc, f"TABLE S3-7. Convergence of the optimal policy (weakest-link headroom procedure: {hw:.2f} BU on the same streams).",
          ["Grid", "Δc (BU)", "V(x₀) (BU)", "Optimal policy mean (BU)", "Weakest-link gap (%)", "Solve time (min)"], rows, [0.6, 0.6, 0.8, 1.2, 1.0, 0.8], W)
    rows = [[k if k != "Optimal (dynamic programming)" else "Best policy found", f"{v['mean']:.1f}", f"{v['p90']:.1f}", f"{v['shocks']:.2f}", f"{v['excess_pct']:.1f} [{v['excess_ci95'][0]:.1f}, {v['excess_ci95'][1]:.1f}]"] for k, v in TF["policies"].items()]
    table(doc, f"TABLE S3-8. Two claims sharing an integrated test, best policy found ({TF['grid']}⁴ grid, Δc = {TF['dc']} BU), {TF['runs']} paired runs.", ["Policy", "Mean (BU)", "P90 (BU)", "Shocks", "Excess over best policy (%), 95% interval"], rows, [1.8, 0.7, 0.7, 0.6, 1.4], W)

    # 8. e_T sweep
    ET = J("rev1/eT_sweep.json")
    H1("S3.8 Integrated tests as a major source of knowledge (Sections IV-B and V-H)")
    P("The knowledge credit e_T of integrated tests was varied in the base model (2000 paired runs per policy; script rev1_eT.py).")
    rows = [[f"{r['eT']:.2f}", f"{r['dp_mean']:.1f}", f"{100*r['share_T_map']:.0f}", f"{r['K_first_T_opt']:.2f}", f"{r['excess']['headroom']:.1f}", f"{r['excess']['test_first']:.1f}", f"{r['excess']['analysis_first']:.1f}"] for r in ET]
    table(doc, "TABLE S3-9. Effect of the knowledge credit of integrated tests.", ["e_T (BU⁻¹)", "Optimum (BU)", "Share of T in the policy map (%)", "K at first test (optimum)", "Headroom excess (%)", "Test-first excess (%)", "Analysis-first excess (%)"], rows, [0.6, 0.7, 0.9, 0.8, 0.8, 0.8, 0.9], W)

    # 9. launch out-of-sample
    LO = J("rev1/launch_oos.json")
    H1("S3.9 Exploratory out-of-sample check of the launch-data loss rates (not used in the article)")
    P("The protocol (code/rev1/launch_oos_protocol.md) was written before the records were compiled. Fixed values from the FAA 1980–2002 history: λ_T = 0.90 BU⁻¹, c_f = 2 BU, K = 0.15 for new developers and 0.57 for experienced ones, giving predicted loss probabilities per attempt of 0.73 and 0.28 by (18). Group N: every orbital attempt from 2003 to 2025 by a developer that had not yet reached orbit with its own vehicle, up to and including its first success. Group E: the first orbital attempt of each new vehicle family by a developer with a prior orbital success of its own (a simpler criterion than the FAA's, which used demonstrated failure probability). Suborbital tests, pad explosions before liftoff, variants of existing vehicles, and existing vehicles under a new operator are excluded; partial failures count as failures. Records and sources (mostly Gunter's Space Page, with news and agency releases) are in code/rev1/launch_oos_records.csv; about a dozen outcomes were read as successes because the cited source lists no failure. Classifications that depend on judgment (e.g., state groups separate from the main state launcher, first stages new versus derived) are flagged and excluded in the sensitivity row. The protocol also allowed moving them to the other group; most alternatives noted in the records are exclusions, so only the exclusion of all flagged records is reported.")
    rows = []
    for lab, s in (("All records", LO["all"]), ("Unambiguous only", LO["unambiguous_only"])):
        for g in ("N", "E"):
            x = s[g]; rows.append([lab, "New developers" if g == "N" else "Experienced, new family", f"{x['failures']} / {x['n']}", f"{100*x['share']:.0f} [{100*x['ci90'][0]:.0f}, {100*x['ci90'][1]:.0f}]", f"{100*x['predicted']:.0f}", f"{x['p_value']:.2f}"])
    table(doc, "TABLE S3-10. Observed loss share (2003–2025) against the fixed prediction (exact binomial 90% interval; two-sided binomial p-value).", ["Records", "Group", "Losses / attempts", "Observed (%)", "Predicted (%)", "p"], rows, [1.2, 1.5, 0.9, 1.0, 0.8, 0.5], W)
    P("What this checks: the two predicted loss probabilities are, by construction, the FAA 1980–2002 group rates (8/11 and 5/18), so the check asks whether those group rates persisted in 2003–2025; it does not test the functional form of the hazard or the dynamics, and it ignores the uncertainty of the calibration, so its power is low. New developers lost fewer attempts than predicted (61% against 73%, two-sided p = 0.09). Applying the protocol's exclusion of variants strictly leaves the unambiguous rows (4 of 18 experienced first flights lost). The protocol also allowed moving ambiguous records to the other group; that variant was not computed. The records were compiled by a search assistant starting from a list of candidate vehicles; one record (Zenit-3SLB) entered because it was on that list and is flagged. The check was not used in the article and is reported for completeness (script rev1_launch_oos.py).")

    # 10. NIST interval
    RG = J("relgrowth.json"); r2 = list(RG.values())[1]; r1 = list(RG.values())[0]
    H1("S3.10 Corrected profile-likelihood interval (Section VI-A)")
    P(f"For the second NIST dataset, the 90% profile-likelihood interval of the ceiling M_∞ in (21) is {r2['m_CI90'][0]:.3f}–{r2['m_CI90'][1]:.3f} (point estimate {r2['kmc']['m']:.3f}), obtained by profiling over φ_0 > 0 and ν > 0 with the likelihood-ratio cutoff χ²₁(0.90) = 2.706 and locating each endpoint by root search. The submitted version reported 0.67–0.96 because the profile optimizer started from too few values of ν and missed the profile minimum for M_∞ near 1, where ν must be small; no additional parameter bound was imposed. For the first dataset the interval runs from {r1['m_CI90'][0]:.3f} to the upper bound, so eight failures do not bound the ceiling. The corrected script is relgrowth.py.")
    cp = doc.core_properties; cp.author = "Pedro K. de Albuquerque"; cp.last_modified_by = "Pedro K. de Albuquerque"; cp.title = "KMC Supplementary Material S3: Studies Added in Revision"; cp.comments = ""
    doc.save(out)

if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "KMC_Supplementary_S3_Revision_Studies.docx")
