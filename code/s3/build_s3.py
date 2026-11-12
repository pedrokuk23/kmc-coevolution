"""Supplementary Material S3: studies added in revision 1 (reads ../rev1/*.json and ../relgrowth.json)."""
import json, sys, os
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
def table(doc, cap, head, rows, widths, width):
    para(doc, cap, 8.5, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, before=4, after=3, keep=True)
    t = doc.add_table(rows=1, cols=len(head)); t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(head):
        c = t.rows[0].cells[j]; c.text = ""; shade(c, "DCE8F3"); run(c.paragraphs[0], h, 8, bold=True)
    trPr = t.rows[0]._tr.get_or_add_trPr(); e = OxmlElement("w:tblHeader"); e.set(qn("w:val"), "true"); trPr.append(e)
    for r in rows:
        cells = t.add_row().cells
        for j, v in enumerate(r): cells[j].text = ""; run(cells[j].paragraphs[0], str(v), 8)
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
    VD = J("rev1/valdata_1_2_3_4_5_6.json"); VR = {c["case"]: c for c in J("rev1/valdata_rule.json")}; V0 = J("rev1/valdata_0.json")[0]
    H1("S3.1 Validation-data availability separated from maturity (Section V-H)")
    P("Equation (10) writes the simulation ceiling as K̄(M) = min(1, k_b + k_l M), taking demonstrated maturity as the proxy for the validation data available. The extended model adds a third state D ∈ [0, 1], the coverage of validation data. Simulation raises K at r_S[K̄(D) − K]+ with K̄(D) = min(1, k_b + k_l D) and does not change D; separate-effects tests raise K at r_E(1 − K), M at e_E[M̄(K) − M]+ and D at ρ_E(1 − D); integrated tests raise K at e_T(1 − K), M at r_T[M̄(K) − M]+ and D at ρ_T(1 − D). Shocks reduce K and M as in the base model and leave D unchanged, and D_0 = 0.10 = M_0. The other parameters are those of Table 5. The optimal policy was computed by value iteration on a 61³ grid (Δc = 0.1 BU). With D tied to M (dD = dM, shocks reducing D like M) the model reduces to the base model: the three-dimensional value at x_0 was within "
      f"{abs(V0['V3_x0']/V0['V2_x0']-1)*100:.1f}% of the two-dimensional value, and the plans of the two models gave the same mean cost within {abs(V0['policies']['opt2']['excess_pct']):.2f}%.")
    P("Policies: opt3, the optimum of the extended model; opt2, the optimum of the base model applied to the true (K, M), i.e., a plan that ignores D; headroom, the procedure of Table 6 with the true rates (its knowledge step takes the most productive activity at each moment, which depends on D); data-aware headroom, the same procedure whose knowledge step compares, by deterministic projection with the rates and without a dynamic program, the cost to reach K_target = max(K_need, K_req) with the greedy step and with first raising D by separate-effects tests until K̄(D) ≥ K_target + δ, for δ ∈ {0.02, 0.05, 0.10, 0.15, 0.20, 0.25}, and takes the first activity of the cheaper plan; threshold, the two-phase rule with K_th tuned by simulation on independent runs; and the stylized proxies. 1000 runs per policy (scripts rev1_valdata.py and rev1_valdata_rule.py).")
    rows = []
    for c in VD:
        pp = c["policies"]; r = VR.get(c["case"], {}).get("policies", {})
        f = lambda d: f"{d['excess_pct']:.1f} [{d['excess_ci95'][0]:.1f}, {d['excess_ci95'][1]:.1f}]"
        rows.append([f"ρ_E = {c['params']['rhoE']:.2f}, ρ_T = {c['params']['rhoT']:.2f}", f"{pp['opt3']['mean']:.2f}", f(pp["opt2"]), f(pp["head_D"]),
                     f(r["head_DD"]) if "head_DD" in r else "—", f"{pp['thr_D']['excess_pct']:.1f} (K_th = {c['K_th']:.2f})",
                     f"{pp['analysis_first']['excess_pct']:.0f}", f"{pp['test_first']['excess_pct']:.0f}"])
    table(doc, "TABLE S3-1. Excess mean cost over the optimum of the extended model (%, 95% interval).",
          ["Case", "opt3 (BU)", "opt2 (base plan)", "Headroom", "Data-aware headroom", "Tuned threshold", "Analysis-first", "Test-first"], rows, [1.5, 0.7, 1.1, 1.1, 1.1, 1.1, 0.7, 0.7], W)
    P("When separate-effects tests supply validation data slowly (ρ_E ≤ 0.10, with integrated tests supplying it at about their maturity rate), the state (K, M) is nearly sufficient: the plan of the base model is within about 1% of the optimum of the extended model. When they supply it fast, the optimum first builds the data with E, then simulates up to the raised ceiling, and only then tests; a greedy knowledge step and a tuned threshold miss that sequence, while the data-aware step recovers most of it.")

    # 2. observable acceptance
    ST = J("rev1/stopping.json")["summary"]
    H1("S3.2 Observable acceptance (Section V-F)")
    P("The closed-loop experiment of Section V-F (40 synthetic projects, assessments every 3 BU with noise of standard deviation 0.03 on each axis, coefficients re-fitted after each assessment with a weak prior) was repeated with an acceptance rule that uses only observations: when the estimated state, or the latest assessment, is in the target region, a confirmation assessment costing 1 BU is bought, and the claim is accepted if it reads at least the target plus a margin (0 or 0.03) on both axes; otherwise the assessment joins the data, the model is re-fitted, and work continues, with no new review within 1 BU. The reference ('oracle') is the optimal policy of the true model stopping when the true state reaches the target, as in the article. 'Optimum, known coefficients' acts on the same noisy assessments with the true coefficients, which separates the cost of observing the state from the cost of estimating the coefficients (script rev1_stopping.py).")
    rows = []
    names = {"dp_known": "Optimum, known coefficients", "dp": "Optimum, re-planned", "headroom": "Headroom, estimated"}
    for m, s in ST.items():
        for k in ("dp_known", "dp", "headroom"):
            x = s[k]
            rows.append([m, names[k], f"{x['mean']:.1f}", f"{x['excess_vs_oracle']:.1f}", f"{x['reviews_mean']:.1f}", f"{100*x['premature_rate']:.1f}", f"{x['deficit_when_premature']:.3f}", str(x["not_accepted"])])
    table(doc, f"TABLE S3-2. Cost with an observable acceptance rule (oracle reference {ST['0.0']['ref_oracle_mean']:.1f} BU).",
          ["Margin", "Policy", "Mean cost (BU)", "Excess over oracle (%)", "Reviews", "Premature acceptance (%)", "Mean deficit if premature", "Not accepted by 60 BU"], rows, [0.6, 1.6, 0.8, 0.9, 0.7, 0.9, 0.9, 0.8], W)

    # 3. decision agreement
    DA = J("rev1/decision_agreement.json")
    H1("S3.3 Reliability of the recommended activity (Section V-F)")
    P("Every 1 BU of the runs of S3.2, the activity chosen with estimated coefficients and estimated state was compared with the activity that the same rule chooses at the true state with the true coefficients (for the re-planned optimum, the optimum of the true model). The table groups the decision points by the true margin K − K_need.")
    rows = []
    for key, v in DA.items():
        m, k = key.split("|")
        rows.append([m, names[k], f"{100*v['overall']:.0f}", str(v["n"])] + [("—" if v["by_true_margin"][b][0] is None else f"{100*v['by_true_margin'][b][0]:.0f} ({v['by_true_margin'][b][1]})") for b in v["by_true_margin"]])
    bins = list(next(iter(DA.values()))["by_true_margin"].keys())
    table(doc, "TABLE S3-3. Agreement of decisions with those at the true state (%; number of decision points in parentheses), by K − K_need.",
          ["Margin", "Policy", "All", "Points"] + [b.replace("-9", "<").replace("..9", "+").replace("..", " to ") for b in bins], rows, [0.6, 1.5, 0.5, 0.6, 0.9, 0.9, 0.9, 0.9, 0.9], W)

    # 4. assessors
    AS = J("rev1/assessors.json")
    H1("S3.4 Assessor disagreement (Sections III-H and V-F)")
    P("With the coefficients known, K and M are assessed every 3 BU by an assessor whose reading differs from the true state by a random error (a different assessor each time) and/or a persistent bias; between assessments the decision maker uses the model prediction from the last assessment, and acceptance uses the review of S3.2 (margin 0). On the rubric of Table 4 (K = Σκ_j/20), a disagreement of one level on one criterion moves K by 0.05. 'Excess' is relative to the same policy observing the true state (plus one review). 'Early tests' is the share of integrated tests started while the true K < K_need (script rev1_assessors.py, 600 runs per condition).")
    rows = []
    for k, v in AS["results"].items():
        c, pname = k.split(" | ")
        rows.append([c, pname, f"{v['mean']:.1f}", f"{v['excess_vs_true_state']:.1f}", f"{100*v['decision_agreement']:.0f}", f"{100*v['early_test_share']:.0f}", f"{100*v['premature_acceptance']:.0f}"])
    table(doc, "TABLE S3-4. Effect of assessor disagreement.", ["Condition", "Policy", "Mean cost (BU)", "Excess (%)", "Decision agreement (%)", "Early tests (%)", "Premature acceptance (%)"], rows, [1.6, 0.8, 0.8, 0.7, 0.9, 0.8, 0.9], W)

    # 5. constrained benchmark
    CL = J("rev1/constrained.json")
    H1("S3.5 Exposure limit imposed on the benchmark (Section V-C)")
    e = CL["envelope"]; lh = CL["launch_hazard"]
    P(f"The headroom procedure with a hard exposure limit (h_max = 0.05 BU⁻¹; step 3b builds knowledge until K ≥ K_test) is compared with the optimum of (12) computed with the same limit: an activity whose hazard per BU exceeds h_max at the current state is inadmissible. Over the {e['n']} parameter sets of Section V-D (150 runs each, the seeds of the envelope study), the limit was binding (K_haz > K_need) in {e['binding']} sets. The median excess over the limited optimum was {e['excess_vs_limited_median']:.1f}% (90th percentile {e['excess_vs_limited_p90']:.1f}%, maximum {e['excess_vs_limited_max']:.1f}%), against {e['excess_vs_unconstrained_median']:.1f}% when measured against the unconstrained optimum as in the submitted version. With the launch-data hazard (λ_T = 0.90 BU⁻¹, K_haz = {lh['K_haz']:.2f} > K_need = {lh['K_need']:.2f}), the limited optimum cost {lh['dp_limited']:.1f} BU and the procedure {lh['headroom_hard']:.1f} BU ({lh['excess_vs_limited']:.1f}%; script rev1_constrained.py).")

    # 6. grid convergence
    g = J("rev1/two_claims_convergence_part1.json")["grids"] + J("rev1/two_claims_convergence_part2.json")["grids"]
    H1("S3.6 Grid convergence of the two-claim model (Section V-G)")
    P("The four-dimensional dynamic program of Section V-G was solved on grids of 21⁴ to 46⁴ points (and with Δc = 0.25 BU on 36⁴). Each optimal policy and the weakest-link headroom procedure were simulated on the same 2000 random streams. The policy obtained on coarse grids is itself suboptimal; the 0.2% gap reported in the submitted version came from a 26⁴ grid. On the finest grids the gap is 3–4% (script rev1_two_claims_conv.py).")
    rows = [[f"{r['n']}⁴", f"{r['dc']:.2f}", f"{r['V_x0']:.2f}", f"{r['dp_mean']:.2f} ± {r['dp_sem']:.2f}", f"{r['hw_mean']:.2f}", f"{r['gap_pct']:.1f} [{r['gap_ci95'][0]:.1f}, {r['gap_ci95'][1]:.1f}]", f"{r['secs']/60:.0f}"] for r in sorted(g, key=lambda r: (r['dc'] < 0.5, r['n']))]
    table(doc, "TABLE S3-5. Convergence of the optimal policy (2000 paired runs).", ["Grid", "Δc (BU)", "V(x₀) (BU)", "Optimal policy mean (BU)", "Headroom, weakest link (BU)", "Gap (%), 95% interval", "Solve time (min)"], rows, [0.6, 0.6, 0.8, 1.1, 1.0, 1.2, 0.7], W)
    TF = J("rev1/two_claims_final.json")
    rows = [[k, f"{v['mean']:.1f}", f"{v['p90']:.1f}", f"{v['shocks']:.2f}", f"{v['excess_pct']:.1f} [{v['excess_ci95'][0]:.1f}, {v['excess_ci95'][1]:.1f}]"] for k, v in TF["policies"].items()]
    table(doc, f"TABLE S3-6. Two claims sharing an integrated test, {TF['grid']}⁴ grid, Δc = {TF['dc']} BU ({TF['runs']} paired runs).", ["Policy", "Mean (BU)", "P90 (BU)", "Shocks", "Excess over optimum (%), 95% interval"], rows, [1.8, 0.7, 0.7, 0.6, 1.4], W)

    # 7. NIST interval
    RG = J("relgrowth.json"); r2 = list(RG.values())[1]; r1 = list(RG.values())[0]
    H1("S3.7 Corrected profile-likelihood interval (Section VI-A)")
    P(f"For the second NIST dataset, the 90% profile-likelihood interval of the ceiling M_∞ in (21) is {r2['m_CI90'][0]:.3f}–{r2['m_CI90'][1]:.3f} (point estimate {r2['kmc']['m']:.3f}), obtained by profiling over φ_0 > 0 and ν > 0 with the likelihood-ratio cutoff χ²₁(0.90) = 2.706 and locating each endpoint by root search. The submitted version reported 0.67–0.96 because the profile optimizer started from too few values of ν and missed the profile minimum for M_∞ near 1, where ν must be small; no additional parameter bound was imposed. For the first dataset the interval runs from {r1['m_CI90'][0]:.3f} to the upper bound, so eight failures do not bound the ceiling. The corrected script is relgrowth.py.")
    cp = doc.core_properties; cp.author = "Pedro K. de Albuquerque"; cp.last_modified_by = "Pedro K. de Albuquerque"; cp.title = "KMC Supplementary Material S3: Studies Added in Revision"; cp.comments = ""
    doc.save(out)

if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "KMC_Supplementary_S3_Revision_Studies.docx")
