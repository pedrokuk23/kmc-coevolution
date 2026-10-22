// KMC Application Guide (supplementary material) — docx-js
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, ImageRun, LevelFormat, Footer, PageNumber, PageBreak,
} = require("docx");

const FONT = "Calibri";
// mini markup: _{sub} ^{sup} **bold** *italic*
function runs(text, base = {}) {
  const out = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*|_\{[^}]*\}|\^\{[^}]*\})/g;
  let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), font: FONT, ...base }));
    const t = m[0];
    if (t.startsWith("**")) out.push(...runs(t.slice(2, -2), { ...base, bold: true }));
    else if (t.startsWith("_{")) out.push(new TextRun({ text: t.slice(2, -1), font: FONT, subScript: true, ...base }));
    else if (t.startsWith("^{")) out.push(new TextRun({ text: t.slice(2, -1), font: FONT, superScript: true, ...base }));
    else out.push(...runs(t.slice(1, -1), { ...base, italics: true }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), font: FONT, ...base }));
  return out;
}
const P = (t, o = {}) => new Paragraph({ children: runs(t, o.run || {}), spacing: { after: 120, line: 276 }, alignment: o.align, ...o.p });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: runs(t), spacing: { before: 280, after: 140 } });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: runs(t), spacing: { before: 220, after: 100 } });
const EQ = (t) => new Paragraph({ children: runs(t, { font: "Cambria Math", size: 23 }), alignment: AlignmentType.CENTER, spacing: { before: 80, after: 120 } });
const B = (t) => new Paragraph({ numbering: { reference: "bul", level: 0 }, children: runs(t), spacing: { after: 60, line: 276 } });
const N = (t, ref = "num") => new Paragraph({ numbering: { reference: ref, level: 0 }, children: runs(t), spacing: { after: 60, line: 276 } });
const BOX = (title, lines) => new Table({
  width: { size: 9026, type: WidthType.DXA }, columnWidths: [9026],
  rows: [new TableRow({ children: [new TableCell({
    width: { size: 9026, type: WidthType.DXA },
    shading: { fill: "EEF3F8", type: ShadingType.CLEAR, color: "auto" },
    margins: { top: 120, bottom: 120, left: 180, right: 180 },
    borders: { left: { style: BorderStyle.SINGLE, size: 18, color: "1D5B8F" }, top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE } },
    children: [new Paragraph({ children: runs(title, { bold: true, color: "1D5B8F" }), spacing: { after: 80 } }), ...lines.map((l) => P(l))],
  })] })],
});
function TBL(head, rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  const cell = (t, i, hdr) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA },
    shading: hdr ? { fill: "DCE4ED", type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({ children: runs(String(t), { bold: !!hdr, size: 19 }) })],
  });
  return new Table({
    width: { size: total, type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, children: head.map((h, i) => cell(h, i, true)) }),
      ...rows.map((r) => new TableRow({ children: r.map((c, i) => cell(c, i, false)) }))],
  });
}
const IMG = (file, w, h, cap) => [
  new Paragraph({ alignment: AlignmentType.CENTER, children: [new ImageRun({ type: "png", data: fs.readFileSync(file), transformation: { width: w, height: h } })], spacing: { before: 120, after: 60 } }),
  new Paragraph({ alignment: AlignmentType.CENTER, children: runs(cap, { size: 18, italics: true }), spacing: { after: 160 } }),
];
const SP = () => new Paragraph({ children: [], spacing: { after: 60 } });

const body = [
  new Paragraph({ children: [new TextRun({ text: "Supplementary Material S1", font: FONT, size: 22, color: "8A6A4F", bold: true })], spacing: { after: 60 } }),
  new Paragraph({ children: [new TextRun({ text: "Applying Knowledge–Maturity Coevolution: a step-by-step guide with a worked example", font: FONT, size: 36, bold: true })], spacing: { after: 160 } }),
  P("This guide shows how to apply the method of the paper to a real development claim, from an organization's past records to the decision at each review. It uses the paper's notation and step numbers (Table 6, headroom procedure; Table 11, calibration protocol; Fig. 8, flowchart). Every number in the worked example was computed with the paper's code; the organization (\"Org X\"), its projects and records are **fictional** and serve only to illustrate the arithmetic."),
  BOX("What you need", [
    "• An assessment log for one or more past programs (cost, activity class, K, M, shocks), or at least the outcome history of past integrated tests.",
    "• A review board that scores K and M for each claim at each review (Section 1).",
    "• A spreadsheet. The companion workbook KMC_Worksheet.xlsx implements Sections 3–5; the Python code (kmc_model.py) is needed only for the optional checks of Section 7.",
  ]),
  SP(),
  TBL(["Step", "What you do", "Where in the paper", "This guide"], [
    ["0", "Define the claim, the target region, budget and exposure limit", "Sec. III-C, Table 6 step 1", "Sec. 4.1"],
    ["1", "Score K and M at every review; keep the log", "Sec. III-H, IV-A; Tables 4, 11-1", "Sec. 1–2"],
    ["2", "Calibrate the coefficients from records + public priors", "Table 11, steps 2–4", "Sec. 3"],
    ["3", "Compute the test threshold K_{test} = max(K_{need}, K_{haz})", "Eq. (17b), Table 6 steps 3/3b", "Sec. 4.2"],
    ["4", "At each review, choose the next activity", "Table 6, steps 0 and 3–5; Fig. 8", "Sec. 4.3–4.5"],
    ["5", "After the project, update the coefficients", "Table 11, steps 5–6", "Sec. 5"],
  ], [600, 3700, 2700, 2026]),

  H1("1. Scoring K and M"),
  P("Both quantities are scored **per claim** (for example, \"combustion is stable across the operating envelope\"), never averaged across subsystems."),
  H2("1.1 Validated knowledge K"),
  EQ("K = 1 − U / U_{0}"),
  P("U is the width of the validated prediction uncertainty for the intended-use quantity (for example, the area validation metric of the model against the most representative data, or the width of a credibility-weighted prediction interval), and U_{0} its value at the start of the program. If the initial model predicts the stability margin within ±40% and today's validated model within ±10%, then K = 1 − 10/40 = 0.75."),
  P("When no quantitative uncertainty is available yet, use the rubric of Table 4: score each K criterion 0–4, take the lowest mandatory criterion (never the average), and map 0, 1, 2, 3, 4 to K ≈ 0, 0.25, 0.5, 0.75, 1 as a first coding. Record the coding convention and keep it fixed within a program; the decision rule of Section 4 is insensitive to monotone recoding (paper, Sec. IV-D), but the calibrated coefficients are not."),
  H2("1.2 Evidence-backed maturity M"),
  EQ("M = Σ_{v} w_{v} s_{v}"),
  P("List the test points v of the required demonstration envelope with weights w_{v} that sum to one (by risk or by envelope area), and set s_{v} = 1 where the acceptance criteria have been met under representative and repeatable conditions, 0 otherwise. Example: 20 equally weighted points, 8 passed: M = 0.40. Missing evidence is \"not assessed\", never zero."),
  H2("1.3 Cost"),
  P("Cumulative cost c is measured in one budget unit (BU) for the whole program, for example one integrated flight or one month of the test campaign. Only differences of c matter."),

  H1("2. The assessment log"),
  P("Record one line per review and per claim. Five columns are indispensable: cumulative cost, activity class performed since the last review (S simulation/analysis, E separate-effects test, T integrated test), K, M, and any shock (discrepancy) with its rework cost."),
  TBL(["Date", "Project", "Cum. cost (BU)", "Activity", "K", "M", "Event"], [
    ["2014-06", "Rocket R", "0.0", "—", "0.10", "0.05", "baseline review"],
    ["2014-11", "Rocket R", "2.0", "T", "0.16", "0.05", "flight 1 lost (shock)"],
    ["2019-03", "Engine E-1", "1.0", "E", "0.37", "0.12", "—"],
    ["2021-08", "CFD-2", "3.0", "S", "0.57", "0.30", "simulation plateau"],
  ], [1100, 1300, 1300, 1000, 800, 800, 2726]),
  SP(),

  H1("3. Calibrating the coefficients"),
  P("The model has thirteen coefficients (paper, Eqs. (8)–(10) and Table 5). Calibrate first those that drive the plan most: the test hazard λ_{T}, the two ceilings and the main rates. Keep the paper's base values as priors for the others until records exist."),
  TBL(["Coefficient", "Meaning", "Record needed", "Method"], [
    ["λ_{T}", "integrated-test shock hazard per BU, × (1 − K)^{2}", "outcomes of past integrated tests and K before each", "likelihood + public prior (3.1)"],
    ["e_{T}", "knowledge gained per BU of integrated testing", "K before consecutive tests", "least squares (3.2)"],
    ["r_{S}, r_{E}, r_{T}", "main rates of S, E, T", "K or M versus cost within a campaign", "log-linear fit (3.3)"],
    ["k_{b}, k_{l}; m_{b}, m_{l}", "ceilings K̄(M) and M̄(K)", "plateaus of S and T campaigns", "linear regression (3.4)"],
    ["e_{E}, λ_{E}, δ_{K}, δ_{M}, ρ", "secondary credit, small-test hazard, shock size, rework", "—", "paper base values"],
  ], [1700, 2800, 2526, 2000]),
  H2("3.1 Test hazard λ_{T}: likelihood and prior"),
  P("For integrated test n with cost c_{f} and assessed knowledge K_{n}, the probability of a discrepancy is"),
  EQ("p_{n}(λ) = 1 − exp[ −λ (1 − K_{n})^{2} c_{f} ]"),
  P("and the likelihood of the observed history (failures F, successes S) is L(λ) = Π_{n∈F} p_{n} · Π_{n∈S} (1 − p_{n}). Maximize ln L over λ with a one-dimensional search (the workbook does it on a grid). Because a few tests give a wide estimate, combine L with a public prior, for example ln λ ~ Normal(ln 0.90, 0.5^{2}) from the FAA first-flight data of the paper (Sec. VI-B), and use the posterior median."),
  BOX("Worked example: Rocket R (8 launches, 2014–2024, first success on flight 8, c_{f} = 2 BU)", [
    "K before flights 1–8: 0.10, 0.16, 0.21, 0.27, 0.32, 0.37, 0.42, 0.47; outcomes: seven failures, then success.",
    "Data only: λ̂_{T} = **2.55** per BU (flight 1: 1 − exp(−2.55 × 0.90^{2} × 2) = 0.98).",
    "With the FAA prior: posterior median **1.48** per BU, 90% interval 0.80–2.68. Org X uses **λ_{T} = 1.5**.",
  ]),
  ...IMG("../tutorial/t_rocket.png", 480, 252, "Figure S1. Rocket R: failure probability per flight from the data alone (dashed) and from the posterior median (bars)."),
  H2("3.2 Knowledge per integrated test e_{T}"),
  P("With ΔK_{n} the increase of K between consecutive tests and x_{n} = (1 − K_{n}) c_{f}, fit ΔK_{n} = e_{T} x_{n} through the origin:"),
  EQ("ê_{T} = Σ ΔK_{n} x_{n} / Σ x_{n}^{2}"),
  P("Rocket R: ΔK = 0.06, 0.05, 0.06, 0.05, 0.05, 0.05, 0.05 and x = 1.80 … 1.16 give **e_{T} = 0.035** per BU. If the increments shrink faster than (1 − K), use the power form g(1 − K)^{q} of the paper (Sec. VI-B)."),
  H2("3.3 Rates: a straight line through logarithms"),
  P("Each activity closes a fixed fraction of its remaining gap per BU, so the gap decays exponentially. Within one campaign, regress the logarithm of the gap on cost; minus the slope is the rate:"),
  EQ("ln(1 − K) = ln(1 − K_{0}) − r_{E} c        (separate-effects tests)"),
  EQ("ln(K̄ − K) = ln(K̄ − K_{0}) − r_{S} c        (simulation, K̄ at the campaign's M)"),
  EQ("ln(M̄ − M) = ln(M̄ − M_{0}) − r_{T} c        (integrated tests, M̄ at the campaign's K)"),
  TBL(["Campaign", "Data", "Slope", "Rate"], [
    ["Engine E-1 (E)", "c = 0…4; K = .30, .37, .43, .48, .53", "−0.099", "r_{E} = 0.10"],
    ["CFD (S), K̄ = 0.464", "c = 0…3; K = .20, .27, .32, .36", "−0.309", "r_{S} = 0.30"],
    ["Ground tests (T), K = 0.50, M̄ = 0.574", "c = 0…3; M = .10, .20, .28, .34", "−0.236", "r_{T} = 0.24"],
  ], [2800, 3400, 1200, 1626]),
  H2("3.4 Ceilings: regress the plateaus"),
  P("A plateau is the level at which an activity's marginal rate has fallen below about 10% of its initial value (Table 6, step 2). Regress the simulation plateaus on the demonstrated M of each campaign, and the integrated-test plateaus on the K at which they were run:"),
  EQ("K̄(M) = k_{b} + k_{l} M,        M̄(K) = m_{b} + m_{l} K"),
  P("Org X: simulation plateaus K = 0.47, 0.57, 0.71, 0.82 at M = 0.10, 0.30, 0.50, 0.70 give **K̄ = 0.40 + 0.60 M**; test plateaus M = 0.36, 0.53, 0.67, 0.84 at K = 0.30, 0.45, 0.60, 0.75 give **M̄ = 0.05 + 1.05 K**."),
  ...IMG("../tutorial/t_fits.png", 600, 150, "Figure S2. Fits of the rates and ceilings for Org X."),
  H2("3.5 The parameter card"),
  TBL(["Coefficient", "Org X", "Paper base", "Source"], [
    ["k_{b}, k_{l}", "0.40, 0.60", "0.40, 0.60", "CFD plateaus"],
    ["m_{b}, m_{l}", "0.05, 1.05", "0.05, 1.05", "test plateaus"],
    ["r_{S}; r_{E}; r_{T}", "0.30; 0.10; 0.24", "0.30; 0.10; 0.22", "campaign rates"],
    ["**λ_{T}**", "**1.5**", "0.40", "Rocket R + FAA prior"],
    ["e_{T}", "0.035", "0.04", "Rocket R increments"],
    ["e_{E}, λ_{E}", "0.05, 0.05", "0.05, 0.05", "prior"],
    ["δ_{K}, δ_{M}, ρ", "0.06, 0.15, 2 BU", "0.06, 0.15, 2 BU", "prior"],
  ], [2300, 2200, 2200, 2326]),

  H1("4. Applying the procedure to a new project"),
  H2("4.1 Define the problem (Table 6, step 1)"),
  P("Project N (fictional): qualify a new upper-stage engine. Claim C1: combustion is stable across the operating envelope. First review: (K, M) = (0.20, 0.10). Target region: K ≥ K_{req} = 0.75 and M ≥ M_{req} = 0.80. Budget: 30 BU. Exposure limit set by Org X: λ_{T}(1 − K)^{2} ≤ h_{max} = 0.05 per BU, about a 10% chance of losing a 2-BU integrated test."),
  H2("4.2 The test threshold"),
  P("An integrated test is worth running only when knowledge supports the target maturity (headroom) and the test hazard is within the exposure limit:"),
  EQ("K_{need} = (M_{req} − m_{b}) / m_{l},        K_{haz} = 1 − (h_{max}/λ_{T})^{1/2},        K_{test} = max(K_{need}, K_{haz})"),
  P("Org X: K_{need} = (0.80 − 0.05)/1.05 = **0.714**; K_{haz} = 1 − √(0.05/1.5) = **0.817**; so K_{test} = 0.817 and the exposure limit, not the headroom, decides. In the paper's base case (λ_{T} = 0.40), K_{haz} = 0.65 and headroom decides."),
  P("When K_{haz} > K_{need}, step 3b of Table 6 leaves three options: reduce exposure (configuration or envelope), re-approve the limit, or keep building knowledge until K ≥ K_{test}. Org X chooses the third. The paper's simulations use the second (the test proceeds once no knowledge deficit remains); Section 4.6 shows how to weigh the two."),
  TBL(["K at the integrated test", "Chance of losing a 2-BU test"], [
    ["0.20 (today)", "85%"], ["0.50", "53%"], ["0.714 (K_{need})", "22%"], ["0.817 (K_{haz})", "10%"],
  ], [4513, 4513]),
  H2("4.3 The decision at each review (Table 6, steps 0 and 3–4)"),
  N("First screen every candidate activity against cost, schedule and exposure (step 0); the steps below choose only among the admissible ones."),
  N("If M < M_{req} and K ≥ K_{test}: run the **integrated test** T (step 3)."),
  N("Otherwise (K < K_{req}, K < K_{need}, or the hazard is above the limit, step 3b): run the activity with the largest **net knowledge rate** (step 4):"),
  EQ("net_{a} = F_{a}(K, M) − λ_{a}(1 − K)^{2} δ_{K},    with F_{S} = r_{S}[K̄(M) − K]_{+},  F_{E} = r_{E}(1 − K),  F_{T} = e_{T}(1 − K)"),
  BOX("Worked example: first decision at (0.20, 0.10)", [
    "K̄(0.10) = 0.40 + 0.60 × 0.10 = 0.46;   K = 0.20 < K_{test} → step 4.",
    "S: 0.30 × (0.46 − 0.20) = 0.0780;   hazard 0 → net **0.0780**.",
    "E: 0.10 × (1 − 0.20) = 0.080;   hazard 0.05 × 0.64 = 0.032;   loss 0.032 × 0.06 = 0.0019 → net **0.0781**.",
    "T: 0.035 × 0.80 = 0.028;   hazard 1.5 × 0.64 = 0.96;   loss 0.0576 → net **−0.030**.",
    "Decision: **E** (separate-effects tests), practically tied with S. The exact derivative D_{a} of the paper (Eq. (13a)), computed by value iteration, gives +0.98, +0.94 and −2.47 BU saved per BU for S, E and T: the same ranking of T and the same near-tie of S and E.",
  ]),
  H2("4.4 The review log of Project N (expected path)"),
  TBL(["Cost (BU)", "K", "M", "K̄(M)", "net S", "net E", "net T", "hazard T", "Decision"], [
    ["0", ".200", ".100", ".460", ".078", ".078", "−.030", ".96", "E"],
    ["4", ".465", ".156", ".494", ".009", ".053", "−.007", ".43", "E"],
    ["8", ".642", ".244", ".546", ".000", ".035", ".001", ".19", "E"],
    ["12", ".760", ".343", ".606", ".000", ".024", ".003", ".086", "E (3b)"],
    ["14.8", ".819", ".414", ".648", "—", "—", "—", ".049", "**T** (step 3)"],
    ["20.4", ".85", ".80", "—", "—", "—", "—", "—", "target"],
  ], [900, 800, 800, 900, 900, 900, 900, 1000, 1926]),
  P("Simulation saturates near 5 BU (K reaches K̄(M)); K passes K_{need} near 10 BU, but the hazard is still above the limit, so separate-effects testing continues; at 14.8 BU both conditions hold and integrated testing begins. Without shocks the procedure reaches the target at 20.4 BU; the optimum of the paper's dynamic program needs 20.2 BU."),
  ...IMG("../tutorial/t_plane.png", 380, 350, "Figure S3. KMC curve of Project N: procedure (colored) and optimum (grey)."),
  H2("4.5 When a shock happens (Table 6, step 5)"),
  P("Re-assess after every material result. In one simulated realization, a discrepancy during the first hot-fire series at 16.0 BU lowered K from 0.83 to 0.77 and M from 0.54 to 0.39, with 2 BU of rework. K was again below K_{test}, so the procedure returned to separate-effects tests until K ≥ 0.817 (20.7 BU) and then completed the integrated tests at 25.9 BU, within budget. The procedure needs no memory: it reads the new state and asks the same two questions."),
  ...IMG("../tutorial/t_run.png", 560, 258, "Figure S4. One realization with a shock, rework and re-plan."),
  H2("4.6 Choosing the exposure limit"),
  TBL(["h_{max} (per BU)", "K_{haz}", "Mean cost (BU)", "P90 cost (BU)", "Shocks per run"], [
    ["0.03", "0.859", "23.1", "27.9", "0.28"],
    ["**0.05**", "0.817", "**22.3**", "26.4", "0.39"],
    ["0.07", "0.784", "22.6", "28.5", "0.55"],
    ["0.10", "0.742", "24.1", "32.5", "0.90"],
    ["optimum (DP)", "≈0.81", "22.2", "26.2", "0.40"],
  ], [1900, 1600, 1800, 1800, 1926]),
  P("1000 Monte Carlo runs per row. A limit that is too strict pays for knowledge the test does not need; a loose limit buys shocks and a long tail. For Org X, 0.05 per BU is within 0.4% of the optimum, and the budget of 30 BU is exceeded in about 1 run in 20. Logics that test early (test-first, the naive slope rule) never reach the target with this hazard. The answer depends on the organization: across the 300 parameter sets of the paper (Sec. V-D), waiting for K_{test} raised the median excess cost over the optimum from 1.4% to 1.6%, while with the launch-data hazard of Sec. VI-B it lowered it from 1.5% to 0.7%. Run this sweep with your own card before fixing h_{max}."),

  H1("5. Learning from the project (Table 11, steps 5–6)"),
  P("After the project, add its records to the log and update the coefficients; the old posterior becomes the new prior. For the test hazard, the integrated testing of Project N accumulated an exposure E = Σ (1 − K)^{2} Δc = 0.187 over 6.6 BU with one shock. With a Poisson likelihood P(1 | λ) = λE e^{−λE}, the posterior median moves from 1.48 to **1.62** per BU (90%: 0.89–2.89), and the next project's exposure threshold becomes K_{haz} = 1 − √(0.05/1.62) = 0.824."),
  P("Track the coefficients across projects and process changes as organizational indicators: a test hazard above the industry value (0.90) points to more ground and rig testing before flight; a low simulation ceiling with no test data (k_{b}) points to validation-data campaigns; a low knowledge gain per test (e_{T}) points to better instrumentation."),

  H1("6. One-page checklist"),
  N("Log cost, activity, K, M and shocks at every review, per claim.", "chk"),
  N("Fit λ_{T} by likelihood on past integrated tests; combine with the public prior.", "chk"),
  N("Fit the rates with log-linear regressions and the ceilings with regressions on plateaus.", "chk"),
  N("Keep the paper's base values for coefficients without records.", "chk"),
  N("Define the claim, target region, budget and exposure limit h_{max}.", "chk"),
  N("Compute K_{need}, K_{haz} and K_{test} = max(K_{need}, K_{haz}).", "chk"),
  N("At each review: if M < M_{req} and K ≥ K_{test}, integrated test; otherwise the activity with the largest net knowledge rate.", "chk"),
  N("Screen the activity against cost, schedule and exposure.", "chk"),
  N("Re-assess after every result, shock or saturation; repeat.", "chk"),
  N("After the project, update the posteriors and track the coefficients.", "chk"),

  H1("7. Optional checks with the code"),
  P("The procedure above needs only the spreadsheet. The Python package archived with the paper adds three checks: the optimal policy and the exact derivative D_{a} (solve_dp), a Monte Carlo of the plan (simulate), and a sweep of the exposure limit. Replace the dictionary P in kmc_model.py with the organization's parameter card, set TARGET and X0, and call policy_procedure(K, M, hist, p, tgt, haz_max, wait_haz=True) at each review (wait_haz=False reproduces the paper, where step 3b re-approves the limit). The scripts that reproduce this guide (tutorial/calib.py, apply.py, update.py, figs.py) are included."),
  ...IMG("../../figures/Fig8.png", 330, 462, "Figure S5. The procedure inside the calibration loop (paper, Fig. 8)."),
];

const doc = new Document({
  styles: {
    default: { document: { run: { font: FONT, size: 21 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 28, bold: true, color: "1F2A37", font: FONT }, paragraph: { spacing: { before: 280, after: 140 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 23, bold: true, color: "1D5B8F", font: FONT }, paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [
    { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] },
    { reference: "num", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 300 } } } }] },
    { reference: "chk", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 300 } } } }] },
  ] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1300, bottom: 1300, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "KMC — Supplementary Material S1 — page ", font: FONT, size: 16, color: "7A8290" }), new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 16, color: "7A8290" })] })] }) },
    children: body,
  }],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync("KMC_Supplementary_S1_Application_Guide.docx", b); console.log("ok"); });
