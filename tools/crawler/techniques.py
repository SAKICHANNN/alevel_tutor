"""
Study guides with exam techniques, command words, common mistakes, and scoring strategies
for Cambridge A-Level subjects: 9701, 9702, 9708, 9709.

Sources: Cambridge examiner reports, tutopiya, blackwoodprep, papersdaddy, 3auk, exampilot.
"""

import json
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

DATA_DIR = Path(__file__).parent.parent / "data"
GUIDES_DIR = DATA_DIR / "study_guides"

GUIDES = {
    "9701_chemistry": {
        "title": "Chemistry 9701 - Exam Techniques & Common Mistakes",
        "command_words": {
            "State": "Short, precise answer. Don't overwrite.",
            "Define": "Exact definition, word-perfect. Learn syllabus definitions by heart.",
            "Describe": "What happens. No explanation needed. Observations, trends, patterns.",
            "Explain": "Why/how it happens. Use 'because'. Connect cause → mechanism → effect.",
            "Suggest": "Apply knowledge to an unfamiliar context. Think beyond textbook.",
            "Calculate": "Show ALL working. Formula → substitution → answer → units.",
            "Predict": "What will happen based on principles. Justify your prediction.",
            "Compare": "Both similarities AND differences. Use comparative language.",
            "Evaluate": "Judge with evidence. Weigh pros/cons. Reach a conclusion.",
            "Deduce": "Work it out from given information. Show reasoning chain.",
            "Draw": "Displayed formula with correct bonds and structure.",
        },
        "keywords": [
            {"term": "Ionic bond", "correct": "Electrostatic attraction between oppositely charged ions", "avoid": "'Shared electrons'"},
            {"term": "Covalent bond", "correct": "Shared pair of electrons", "avoid": "'Transfer of electrons'"},
            {"term": "Electrophile", "correct": "Electron-deficient species; accepts electron pair", "avoid": "Confusing with nucleophile"},
            {"term": "Nucleophile", "correct": "Electron-rich species; donates electron pair", "avoid": "Confusing with electrophile"},
            {"term": "Activation energy", "correct": "Minimum energy required for a reaction to occur", "avoid": "'Energy to start the reaction'"},
            {"term": "Le Chatelier", "correct": "System shifts to oppose the change imposed", "avoid": "'System balances out'"},
            {"term": "Oxidation", "correct": "Loss of electrons", "avoid": "Gain of oxygen only"},
            {"term": "Reduction", "correct": "Gain of electrons", "avoid": "Loss of oxygen only"},
            {"term": "Buffer", "correct": "Resists changes in pH when small amounts of acid/base are added", "avoid": "'Neutraliser'"},
            {"term": "Enthalpy change", "correct": "Heat change at constant pressure (ΔH)", "avoid": "Just 'heat change'"},
            {"term": "Intermolecular forces", "correct": "Forces BETWEEN molecules", "avoid": "Intramolecular (within molecule)"},
            {"term": "Hydrogen bonding", "correct": "Strong dipole-dipole between H (bonded to N/O/F) and lone pair on N/O/F", "avoid": "'Strong bond' - it's an IMF, not a bond"},
        ],
        "common_mistakes": [
            "**Molecular geometry**: Guessing bond angles from diagrams instead of calculating. Learn VSEPR: tetrahedral=109.5°, trigonal planar=120°, linear=180°.",
            "**Curly arrows**: Must start from lone pair OR middle of bond, point to atom/bond being formed. No arrow = no mark.",
            "**Balancing equations**: Check charge balance AND atom balance. Especially for half-equations.",
            "**Significant figures vs decimal places**: 3 s.f. and 3 d.p. are different. Read the question.",
            "**Explain questions**: Must show reasoning chain. 'X happens because... which leads to... therefore...'",
            "**Rounding too early**: Keep intermediate values in calculator. Only round final answer.",
            "**Confusing orbital and subshell**: One 3p orbital = max 2 electrons. 3p subshell = 3 orbitals = max 6 electrons.",
            "**Enthalpy of hydration**: Always EXOthermic. Bond formation releases energy. ΔH_hydration < 0.",
            "**Limiting reagent**: Calculate moles of each. Compare with stoichiometric ratio.",
            "**Isomer counting**: Be systematic. Draw all possibilities. Don't miss structural isomers.",
        ],
        "paper_specific_tips": [
            "**Paper 1 (MCQ)**: 40 questions, 60 min. 1.5 min/question. Eliminate wrong answers. For 'which is NOT correct', note the NOT.",
            "**Paper 2 (AS Structured)**: Show working. Use bullet points for clarity. Mark allocation guides answer length.",
            "**Paper 3 (Practical)**: Record readings to correct precision. Tabulate with units. Graph must fill >50% grid. Identify anomalies.",
            "**Paper 4 (A2 Structured)**: Multi-step questions. Link to AS knowledge. Organic mechanisms with precise curly arrows.",
            "**Paper 5 (Planning/Analysis)**: State independent/dependent/control variables. Method step-by-step. Suggest REALISTIC improvements (not 'be more careful'). Identify specific error sources. Calculate uncertainties.",
        ],
        "calculation_rules": [
            "Show formula → substitution → answer → units",
            "Don't round intermediate values - keep in calculator",
            "Final answer to 3 s.f. unless specified otherwise",
            "For pH: [H+] = 10^(-pH), pH = -log[H+]",
            "ΔH calculations: sign matters! Exothermic = negative, Endothermic = positive",
            "Kc/Kp: products over reactants, raised to stoichiometric coefficients",
        ],
        "organic_mechanism_tips": [
            "Curly arrows show ELECTRON MOVEMENT, not atom movement",
            "Arrow from bond → shows bond breaking (heterolytic)",
            "Arrow from lone pair → shows nucleophilic attack",
            "SN1: 2 steps, carbocation intermediate, racemisation",
            "SN2: 1 step, inversion of configuration, primary > secondary > tertiary",
            "Electrophilic addition: electrophile attacks C=C, carbocation forms, nucleophile attacks",
            "Always show all bonds and charges on intermediates",
        ],
    },

    "9702_physics": {
        "title": "Physics 9702 - Exam Techniques & Common Mistakes",
        "command_words": {
            "State": "Short answer. Formula, value, or brief statement.",
            "Define": "Precise meaning. Often requires equation. e.g. 'Velocity is rate of change of displacement: v=Δs/Δt'",
            "Describe": "What happens. Observations. No explanation.",
            "Explain": "Why/how. Use physics principles. 'Because...' required.",
            "Calculate": "Formula → substitution → answer → unit. Show ALL working.",
            "Show that": "Prove the given value. EVERY step must be shown. No gaps.",
            "Determine": "Work out with full working. Method marks available.",
            "Sketch": "Rough graph. Show key features (intercept, asymptote, shape).",
            "Plot": "Accurate graph. Sensible scale. Points must fill >50% grid.",
            "Compare": "Similarities AND differences. Use comparative language.",
            "Evaluate": "Weigh evidence. Judge reliability. Suggest improvements.",
            "Deduce": "Reason from given information. Show logic.",
        },
        "keywords": [
            {"term": "Velocity", "correct": "Rate of change of displacement (vector)", "avoid": "Speed"},
            {"term": "Acceleration", "correct": "Rate of change of velocity", "avoid": "'Getting faster'"},
            {"term": "Work done", "correct": "Force × displacement in direction of force", "avoid": "'Effort'"},
            {"term": "Potential difference", "correct": "Work done per unit charge", "avoid": "'Voltage' as only term"},
            {"term": "e.m.f.", "correct": "Energy converted from other forms to electrical per unit charge", "avoid": "Same as p.d."},
            {"term": "Phase difference", "correct": "Fraction of a cycle between two oscillations, in radians/degrees", "avoid": "'Out of sync'"},
            {"term": "Coherence", "correct": "Constant phase difference between waves", "avoid": "'Same wavelength'"},
            {"term": "Photon", "correct": "Quantum of electromagnetic radiation, E=hf", "avoid": "'Particle of light'"},
            {"term": "Capacitance", "correct": "C = Q/V; charge stored per unit p.d.", "avoid": "'Stores charge' without formula"},
            {"term": "Lenz's law", "correct": "Induced current opposes the change causing it", "avoid": "'Opposes the field'"},
            {"term": "Half-life", "correct": "Time for half the radioactive nuclei to decay", "avoid": "'Half the time'"},
        ],
        "common_mistakes": [
            "**Rounding intermediate answers**: Keep all values in calculator. Only round final answer.",
            "**Equations without subject**: Always state the subject. 'v = u + at' not just 'use suvat'.",
            "**Not reading command words**: 'State and explain' needs BOTH. Just stating loses half the marks.",
            "**Unit conversions**: mm² to m² is ÷10⁶, not ÷10³. cm³ to m³ is ÷10⁶. Check prefixes.",
            "**Significant figures**: Match question data's s.f. 2 or 3 s.f. is standard.",
            "**Direction in mechanics**: Forces are vectors. Indicate direction explicitly.",
            "**Paper 5 planning**: Vague improvements ('repeat and average') don't score. Be specific.",
            "**Graph plotting**: Points must fill >50% of grid. Don't use false origin unnecessarily.",
            "**Error bars**: Not just 'smallest division'. Factor in experimental difficulty.",
            "**Definitions**: Missing 'per unit...' loses the mark. Be exact.",
        ],
        "paper_specific_tips": [
            "**Paper 1 (MCQ)**: Read each option. Calculate BEFORE looking at choices. Watch for prefixes (k, μ, M).",
            "**Paper 2 (AS Structured)**: Read entire question first. Later parts often depend on earlier results.",
            "**Paper 3 (Practical)**: Record to correct precision. Table with units divided from heading. Graph: sensible scales.",
            "**Paper 4 (A2 Structured)**: Multi-step reasoning. Link topics (e.g. mechanics + energy). Show derivations.",
            "**Paper 5 (Planning/Analysis)**: Variables (independent, dependent, controlled). Method detail including apparatus. Graph analysis method. Specific safety precautions for YOUR experiment. REALISTIC error sources and improvements.",
        ],
        "calculation_patterns": [
            "**SUVAT**: Identify known variables. Choose correct equation. Substitute with units.",
            "**Moments**: Clockwise = anticlockwise for equilibrium. Perpendicular distance!",
            "**Kirchhoff's laws**: ΣI_in = ΣI_out; ΣV around loop = 0. Sign convention matters.",
            "**Capacitor**: Q=CV, E=½CV², τ=RC. Exponential decay: V=V₀e^(-t/RC)",
            "**Magnetic flux**: Φ=BAcosθ. Faraday: ε=-dΦ/dt. Lenz determines direction.",
            "**Photoelectric**: hf=Φ+KE_max. Threshold frequency when KE=0.",
        ],
        "paper5_template": {
            "planning": [
                "1. Identify: independent variable, dependent variable, controlled variables (list 3+)",
                "2. Apparatus: list with justification for each item",
                "3. Method: step-by-step, enough detail to replicate",
                "4. Data collection: what to measure, how, with what precision",
                "5. Analysis: what graph to plot (y=mx+c form), how to extract required quantity",
                "6. Safety: specific to YOUR experiment, not generic lab rules",
                "7. Additional detail: repeat readings, averaging, range of values",
            ],
            "analysis": [
                "1. Table: quantities with units in headings. Correct s.f./d.p.",
                "2. Calculated quantities: show one example calculation",
                "3. Graph: labelled axes with units, sensible scales, plot points, error bars",
                "4. Line of best fit: balanced points above/below",
                "5. Worst acceptable line: steepest/shallowest through error bars",
                "6. Gradient and y-intercept: show triangle method or calculation",
                "7. Uncertainty: Δgrad = |best - worst| / 2 (approximately)",
            ],
            "evaluation": [
                "1. State conclusion: what does the result show?",
                "2. Identify limitations: specific problems with THIS experiment",
                "3. Suggest improvements: SPECIFIC actions, not 'be more careful'",
                "4. Assess reliability: comment on uncertainty and spread of data",
                "5. Discuss systematic vs random errors",
            ],
        },
    },

    "9708_economics": {
        "title": "Economics 9708 - Exam Techniques & Essay Frameworks",
        "command_words": {
            "State / Identify": "Short answer. Pick from data.",
            "Define": "Precise economic meaning. 'Opportunity cost is the next best alternative forgone.'",
            "Describe": "What data/diagram shows. Quote figures. No explanation.",
            "Explain": "Why/how. Cause→mechanism→effect. Use 'because'.",
            "Analyse": "Break down into parts. Show relationships. Use diagrams.",
            "Assess": "Judge importance. Both sides. Reach conclusion.",
            "Evaluate": "Weigh arguments. Question validity. Substantiated conclusion. THIS IS 30%+ of marks.",
            "Discuss": "Explore multiple aspects. Balance. Conclusion required.",
            "Compare": "Similarities AND differences. Not a list.",
            "Calculate": "Show working. e.g. PED = %ΔQd / %ΔP",
        },
        "keywords": [
            {"term": "Opportunity cost", "correct": "The next best alternative forgone", "avoid": "Just 'cost'"},
            {"term": "PED", "correct": "Responsiveness of quantity demanded to change in price. %ΔQd/%ΔP", "avoid": "Sensitivity (too vague)"},
            {"term": "Allocative efficiency", "correct": "P = MC. Resources allocated to maximise social welfare.", "avoid": "Just 'efficiency'"},
            {"term": "Public good", "correct": "Non-excludable AND non-rivalrous", "avoid": "Provided by government"},
            {"term": "Real GDP", "correct": "GDP adjusted for inflation", "avoid": "Just GDP"},
            {"term": "Fiscal policy", "correct": "Government spending and taxation to influence the economy", "avoid": "Any government policy"},
            {"term": "Monetary policy", "correct": "Central bank controlling interest rates and money supply", "avoid": "Fiscal policy"},
            {"term": "Multiplier", "correct": "Ratio of change in national income to initial injection", "avoid": "The effect (vague)"},
            {"term": "Exchange rate", "correct": "Price of one currency in terms of another", "avoid": "Value of money"},
            {"term": "Current account", "correct": "Trade in goods/services + primary/secondary income", "avoid": "Just trade balance"},
        ],
        "ao_explanation": {
            "AO1": "Knowledge & Understanding (33%): Define terms, recall facts, draw and label diagrams correctly.",
            "AO2": "Analysis (37%): Cause-and-effect chains. Explain WHY and HOW. Apply theory to context. Use diagrams with explanation.",
            "AO3": "Evaluation (30%): Weigh arguments. Question assumptions. Consider SR vs LR, elasticity, unintended consequences. Reach a reasoned conclusion.",
        },
        "essay_framework": {
            "8_mark": "Definition → One developed chain of reasoning (cause→mechanism→effect) → Diagram with explanation → Brief judgement.",
            "12_mark": "Definition → Two developed chains → Diagram → Evaluation point → Conclusion.",
            "20_mark": "Introduction (2-3 min): Define key terms, rephrase the issue.\n"
                       "Core Analysis (10-12 min): Explain theory with diagrams. Apply to context.\n"
                       "Impacts (7-8 min): Multiple outcomes. SR vs LR. Effects on macro objectives.\n"
                       "Evaluation (10-12 min): Question effectiveness. Consider limitations (elasticity, time lags, assumptions). Suggest alternatives.\n"
                       "Conclusion (2-3 min): Supported judgement. Answer the question directly.",
        },
        "evaluation_dimensions": [
            "**Short-run vs Long-run**: SR effects often differ from LR. What works now may fail later.",
            "**Elasticity dependence**: Effectiveness depends on PED, PES, YED, XED values.",
            "**Time lags**: Recognition lag, implementation lag, impact lag.",
            "**Assumptions**: Ceteris paribus rarely holds in reality.",
            "**Unintended consequences**: Policy may create new problems.",
            "**Distributional effects**: Who benefits? Who loses? Equity concerns.",
            "**Government failure**: Intervention may be worse than market failure.",
            "**Empirical evidence**: What does real-world data show?",
        ],
        "common_mistakes": [
            "**One-sided essays**: 'Evaluate' requires BOTH sides. One-sided earns zero evaluation marks.",
            "**Diagrams without explanation**: A diagram alone is not analysis. Must be explained and linked to the question.",
            "**Unlabelled diagrams**: Axes, curves, equilibrium points MUST be labelled.",
            "**Vague evaluation**: 'It depends' is not evaluation. Say WHAT it depends on and WHY.",
            "**Not using data**: In data response, quote figures from the extract.",
            "**Generic conclusions**: Must directly answer the specific question.",
            "**Confusing analysis with evaluation**: Analysis = explaining what happens. Evaluation = judging how significant/effective it is.",
            "**Defining terms imprecisely**: 'Inflation is when prices go up' loses marks. Say 'sustained increase in general price level'.",
        ],
        "data_response_tips": [
            "Part (a): Define key terms. Use data directly. 2-4 marks.",
            "Part (b): Explain with diagram. Refer to data. 4-6 marks.",
            "Part (c): Analyse using extract. At least 2 developed chains. 6-8 marks.",
            "Part (d): Evaluate. Both sides. Use data to support. Conclusion. 8-10 marks.",
            "Always quote figures: 'As shown in Table 1, GDP grew by 3.2%...'",
        ],
    },

    "9709_mathematics": {
        "title": "Mathematics 9709 - Exam Techniques & Problem Solving",
        "command_words": {
            "Calculate / Work out": "Formula → substitution → answer. Show working.",
            "Show that": "Prove the given result. EVERY algebraic step visible.",
            "Find": "Obtain the answer. Method marks available for correct working.",
            "Solve": "Find values satisfying equation. Show method (factorisation, formula, substitution).",
            "Simplify": "Express in simplest form. Combine like terms.",
            "Prove": "Deductive proof. Each step follows logically from previous.",
            "Sketch": "Show key features (intercepts, turning points, asymptotes). Approximate shape.",
            "Draw": "Accurate graph. Plot points if needed. Use graph paper if provided.",
            "Determine": "Calculate with working shown.",
            "Verify": "Check by substitution. Different from 'prove'.",
        },
        "golden_rules": [
            "**SHOW WORKING**: 'No marks for unsupported answers from a calculator.' This is printed on every paper.",
            "**Quadratic equations**: Must show factorisation, quadratic formula with values substituted, OR completing the square. Calculator output alone = 0 marks.",
            "**Definite integrals**: Show antiderivative → substitute limits → evaluate. Calculator integration = no marks.",
            "**Trigonometric equations**: Show all solutions in given interval. Use CAST diagram or graph.",
            "**Exact answers**: Leave in surd form, π, fractions when 'exact' is specified. Rounding = 0 marks.",
            "**Method marks**: Even with a wrong final answer, correct reasoning can earn most of the marks.",
            "**Presentation**: Clear layout. Don't cram work. Cross out unwanted attempts. Use pen, not pencil over ink.",
        ],
        "topic_specific": {
            "quadratics": [
                "Discriminant: b²-4ac > 0 = two distinct roots, = 0 = repeated/tangent, < 0 = none",
                "Completing the square: a(x + b/2a)² + (c - b²/4a)",
                "Quadratic formula: x = [-b ± √(b²-4ac)] / 2a",
            ],
            "differentiation": [
                "Chain rule: dy/dx = dy/du × du/dx",
                "Product rule: d(uv)/dx = u(dv/dx) + v(du/dx)",
                "Quotient rule: d(u/v)/dx = [v(du/dx) - u(dv/dx)] / v²",
                "Stationary points: dy/dx = 0. Second derivative test for nature.",
                "Connected rates: dy/dt = dy/dx × dx/dt",
            ],
            "integration": [
                "Reverse of differentiation: ∫xⁿ dx = xⁿ⁺¹/(n+1) + C (n ≠ -1)",
                "Definite integral: [F(x)]ᵇₐ = F(b) - F(a). Show substitution explicitly.",
                "Area: ∫ y dx between limits. Check if curve crosses x-axis (split integral).",
                "Volume of revolution: π ∫ y² dx",
                "ALWAYS write +C for indefinite integrals!",
            ],
            "trigonometry": [
                "sin²θ + cos²θ = 1",
                "tanθ = sinθ/cosθ",
                "sin(A±B) = sinA cosB ± cosA sinB",
                "cos(A±B) = cosA cosB ∓ sinA sinB",
                "Double angle: sin2θ = 2sinθ cosθ, cos2θ = cos²θ - sin²θ = 2cos²θ - 1 = 1 - 2sin²θ",
                "Solving: Find all solutions in given interval. Use periodicity.",
            ],
            "vectors": [
                "Position vector, direction vector",
                "Dot product: a·b = |a||b|cosθ. For perpendicular: a·b = 0",
                "Line equation: r = a + λd",
                "Angle between vectors: cosθ = a·b / (|a||b|)",
            ],
            "mechanics": [
                "SUVAT: v=u+at, s=ut+½at², v²=u²+2as, s=½(u+v)t. Know which to use.",
                "F=ma: Resolve forces in perpendicular directions first.",
                "Moments: Force × perpendicular distance. Clockwise = anticlockwise.",
                "Connected particles: Same acceleration. Tension same throughout light inextensible string.",
                "Energy: KE=½mv², GPE=mgh, Work=Fd. Conservation of energy.",
            ],
            "statistics": [
                "Mean = Σx/n. Variance = Σ(x-μ)²/n = Σx²/n - μ²",
                "Probability: P(A∪B) = P(A)+P(B)-P(A∩B)",
                "Binomial: X~B(n,p), P(X=r) = ⁿCᵣ pʳ qⁿ⁻ʳ",
                "Normal: X~N(μ,σ²). Standardise: Z = (X-μ)/σ",
                "Hypothesis test: State H₀, H₁. Find critical region or p-value. Conclusion in context.",
            ],
        },
        "common_mistakes": [
            "**No working shown**: Calculator answer alone = 0 marks for quadratics, integration, trig equations.",
            "**Wrong trig quadrant**: Missing solutions. Always check how many solutions should exist.",
            "**Missing +C**: Every indefinite integral loses a mark without +C.",
            "**Algebraic sign errors**: Especially when expanding brackets or rearranging. Check each line.",
            "**Wrong discriminant interpretation**: b²-4ac = 0 means tangent, not 'touches or intersects'. > 0 means two intersections.",
            "**Premature rounding**: Use calculator-stored values. Final answer only to specified accuracy.",
            "**In binomial expansion**: Sign errors on negative terms. Formula: (1+x)ⁿ = 1 + nx + n(n-1)x²/2! + ...",
            "**Mechanics direction**: Forces are vectors. Indicate positive direction at the start.",
            "**Statistical conclusion**: Must be in context. 'Reject H₀' alone is NOT enough. Say what it means.",
        ],
        "time_management": [
            "Pure 1: 75 marks / 1h50m ≈ 1.5 min per mark. 10-mark question ≈ 15 min.",
            "Pure 3: similar pacing. Leave 15 min at end for checking.",
            "Mechanics/Stats: Show all working. Diagrams in mechanics save time.",
            "Don't get stuck. Mark the question and return later.",
            "If a question says 'Hence', use the PREVIOUS result. Don't start from scratch.",
        ],
    },
}


def generate_markdown():
    GUIDES_DIR.mkdir(parents=True, exist_ok=True)

    for key, guide in GUIDES.items():
        md = []
        md.append(f"# {guide['title']}\n")

        md.append("## Command Words (What Examiners Expect)\n")
        md.append("| Command Word | What To Do | Common Mistake |")
        md.append("|-------------|------------|----------------|")
        for cmd, desc in guide["command_words"].items():
            md.append(f"| **{cmd}** | {desc} | |")
        md.append("")

        if "keywords" in guide:
            md.append("## Keywords (Must Use Precisely)\n")
            md.append("| Term | Correct Usage | Avoid |")
            md.append("|------|-------------|-------|")
            for kw in guide["keywords"]:
                md.append(f"| {kw['term']} | {kw['correct']} | {kw['avoid']} |")
            md.append("")

        if "common_mistakes" in guide:
            md.append("## Common Mistakes (From Examiner Reports)\n")
            for m in guide["common_mistakes"]:
                md.append(f"- {m}")
            md.append("")

        if "calculation_rules" in guide:
            md.append("## Calculation Rules\n")
            for r in guide["calculation_rules"]:
                md.append(f"- {r}")
            md.append("")

        if "paper_specific_tips" in guide:
            md.append("## Paper-Specific Tips\n")
            for p in guide["paper_specific_tips"]:
                md.append(f"- {p}")
            md.append("")

        if "organic_mechanism_tips" in guide:
            md.append("## Organic Mechanism Tips\n")
            for t in guide["organic_mechanism_tips"]:
                md.append(f"- {t}")
            md.append("")

        if "ao_explanation" in guide:
            md.append("## Assessment Objectives\n")
            for ao, desc in guide["ao_explanation"].items():
                md.append(f"- **{ao}**: {desc}")
            md.append("")

        if "essay_framework" in guide:
            md.append("## Essay Framework\n")
            for qtype, framework in guide["essay_framework"].items():
                md.append(f"### {qtype.replace('_', ' ').title()}\n{framework}\n")
            md.append("")

        if "evaluation_dimensions" in guide:
            md.append("## Evaluation Dimensions (For Level 4 Marks)\n")
            for d in guide["evaluation_dimensions"]:
                md.append(f"- {d}")
            md.append("")

        if "data_response_tips" in guide:
            md.append("## Data Response Tips\n")
            for t in guide["data_response_tips"]:
                md.append(f"- {t}")
            md.append("")

        if "golden_rules" in guide:
            md.append("## Golden Rules\n")
            for r in guide["golden_rules"]:
                md.append(f"- {r}")
            md.append("")

        if "topic_specific" in guide:
            md.append("## Topic-Specific Techniques\n")
            for topic, tips in guide["topic_specific"].items():
                md.append(f"### {topic.title()}\n")
                for t in tips:
                    md.append(f"- {t}")
                md.append("")

        if "time_management" in guide:
            md.append("## Time Management\n")
            for t in guide["time_management"]:
                md.append(f"- {t}")
            md.append("")

        if "paper5_template" in guide:
            md.append("## Paper 5 Template\n")
            for section, points in guide["paper5_template"].items():
                md.append(f"### {section.title()}\n")
                for p in points:
                    md.append(f"- {p}")
                md.append("")

        filepath = GUIDES_DIR / f"{key}.md"
        filepath.write_text("\n".join(md))
        console.print(f"[green]Generated: {filepath}[/green]")

    # Generate master index
    index = ["# A-Level Exam Techniques Master Index\n"]
    for key, guide in GUIDES.items():
        index.append(f"- [{guide['title']}](./{key}.md)")
    (GUIDES_DIR / "index.md").write_text("\n".join(index))

    console.print("[bold green]All study guides generated![/bold green]")


def show_summary():
    console.print(Panel.fit("[bold cyan]Study Guides Generated[/bold cyan]"))
    table = Table(title="Available Study Guides")
    table.add_column("Subject", style="cyan")
    table.add_column("Code", style="yellow")
    table.add_column("Content", style="white")
    content_desc = {
        "9701_chemistry": "Command words, keywords, common mistakes, calculation rules, paper tips, organic mechanisms",
        "9702_physics": "Command words, keywords, common mistakes, calculation patterns, Paper 5 template",
        "9708_economics": "Command words, keywords, AO breakdown, essay frameworks, evaluation dimensions, data response tips",
        "9709_mathematics": "Command words, golden rules, topic techniques, common mistakes, time management",
    }
    for key, guide in GUIDES.items():
        table.add_row(guide["title"].split(" - ")[0], key.split("_")[0], content_desc.get(key, ""))
    console.print(table)


if __name__ == "__main__":
    generate_markdown()
    show_summary()
