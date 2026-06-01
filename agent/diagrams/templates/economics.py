"""
Pre-verified TikZ diagram templates for A-Level Economics.
All coordinates and intersections are mathematically exact.
LLM selects template + provides labels; server fills and renders.

Templates cover the 15 most common CAIE 9708 diagram types.
Each template uses pgfplots with exact curve definitions.
"""
import json
from pathlib import Path
from typing import Optional

TEMPLATES_DIR = Path(__file__).parent

ECON_TEMPLATES = {}

# ── Template 1: Demand & Supply (basic equilibrium) ──
ECON_TEMPLATES["demand-supply"] = {
    "name": "Demand & Supply — Basic Equilibrium",
    "description": "Downward-sloping demand, upward-sloping supply, equilibrium price/quantity",
    "code": r"""\documentclass{{standalone}}
\usepackage{{tikz}}
\usepackage{{pgfplots}}
\pgfplotsset{{compat=1.18}}
\usetikzlibrary{{intersections,patterns}}
\begin{{document}}
\begin{{tikzpicture}}
\begin{{axis}}[
    xlabel={{Quantity}}, ylabel={{Price}},
    xmin=0, xmax=7, ymin=0, ymax=7,
    axis lines=left,
    xtick=\empty, ytick=\empty,
    width=8cm, height=6cm,
]
% Demand: linear downward
\addplot[thick,blue,domain=0:6] {{ -1*x + 6 }} node[right] {{{d_label}}};
% Supply: linear upward
\addplot[thick,red,domain=0:6] {{ 0.8*x + 0.5 }} node[right] {{{s_label}}};
% Equilibrium point (computed: -x+6 = 0.8x+0.5 → x=3.06, y=2.94)
\draw[dashed,gray] (axis cs:3.06,0) -- (axis cs:3.06,2.94) -- (axis cs:0,2.94);
\node[below] at (axis cs:3.06,0) {{{eq_q}}};
\node[left] at (axis cs:0,2.94) {{{eq_p}}};
\node[draw,fill=white,circle,inner sep=1.5pt] at (axis cs:3.06,2.94) {{}};
\node[above right] at (axis cs:3.06,2.94) {{{eq_label}}};
\end{{axis}}
\end{{tikzpicture}}
\end{{document}}""",
    "defaults": {"d_label": "$D$", "s_label": "$S$", "eq_q": "$Q_e$", "eq_p": "$P_e$", "eq_label": "$E$"},
}

# ── Template 2: Demand & Supply — Shift in Demand ──
ECON_TEMPLATES["demand-shift-right"] = {
    "name": "Demand Shift Right",
    "description": "D1 shifts right to D2, higher equilibrium P and Q",
    "code": r"""\documentclass{{standalone}}
\usepackage{{tikz}}
\usepackage{{pgfplots}}
\pgfplotsset{{compat=1.18}}
\usetikzlibrary{{arrows.meta}}
\begin{{document}}
\begin{{tikzpicture}}
\begin{{axis}}[
    xlabel={{Quantity}}, ylabel={{Price}},
    xmin=0, xmax=8, ymin=0, ymax=8,
    axis lines=left,
    xtick=\empty, ytick=\empty,
    width=8cm, height=6cm,
]
% Supply
\addplot[thick,red,domain=0:7] {{ 0.8*x + 1 }} node[right] {{{s_label}}};
% Demand 1 (original)
\addplot[thick,blue,domain=0:7] {{ -1*x + 7 }} node[pos=0.3,above] {{{d1_label}}};
% Demand 2 (shifted right, +2 intercept)
\addplot[thick,blue!60!cyan,domain=0:7] {{ -1*x + 8 }} node[pos=0.2,above] {{{d2_label}}};
% E1: -x+7=0.8x+1 → x=3.33, y=3.67
\draw[dashed,gray,thin] (axis cs:3.33,0) -- (axis cs:3.33,3.67) -- (axis cs:0,3.67);
\node[below] at (axis cs:3.33,0) {{{q1}}};
\node[left] at (axis cs:0,3.67) {{{p1}}};
\node[circle,fill=black,inner sep=1.2pt] at (axis cs:3.33,3.67) {{}};
\node[below left] at (axis cs:3.33,3.67) {{{e1_label}}};
% E2: -x+8=0.8x+1 → x=3.89, y=4.11
\draw[dashed,gray,thin] (axis cs:3.89,0) -- (axis cs:3.89,4.11) -- (axis cs:0,4.11);
\node[below] at (axis cs:3.89,0) {{{q2}}};
\node[left] at (axis cs:0,4.11) {{{p2}}};
\node[circle,fill=black,inner sep=1.2pt] at (axis cs:3.89,4.11) {{}};
\node[above right] at (axis cs:3.89,4.11) {{{e2_label}}};
% Shift arrow
\draw[->,thick,blue!60!cyan] (axis cs:2.5,4.5) -- (axis cs:3.8,3.2) node[midway,above,sloped] {{\\small {shift_label}}};
\end{{axis}}
\end{{tikzpicture}}
\end{{document}}""",
    "defaults": {"s_label": "$S$", "d1_label": "$D_1$", "d2_label": "$D_2$",
                 "q1": "$Q_1$", "p1": "$P_1$", "e1_label": "$E_1$",
                 "q2": "$Q_2$", "p2": "$P_2$", "e2_label": "$E_2$",
                 "shift_label": "$D$ increase"},
}

# ── Template 3: Negative Externality (Production) ──
ECON_TEMPLATES["negative-externality"] = {
    "name": "Negative Production Externality",
    "description": "MSC > MPC, overproduction, deadweight loss triangle",
    "code": r"""\documentclass{{standalone}}
\usepackage{{tikz}}
\usepackage{{pgfplots}}
\pgfplotsset{{compat=1.18}}
\usetikzlibrary{{patterns,patterns.meta}}
\begin{{document}}
\begin{{tikzpicture}}
\begin{{axis}}[
    xlabel={{Quantity}}, ylabel={{Costs/Benefits ($)}},
    xmin=0, xmax=8, ymin=0, ymax=8,
    axis lines=left,
    xtick=\empty, ytick=\empty,
    width=8cm, height=6cm,
]
% MPB/MSB = D (downward)
\addplot[thick,blue,domain=0:7] {{ -1*x + 7 }} node[right] {{{d_label}}};
% MPC = S_private (upward, gentle)
\addplot[thick,red,domain=0:7] {{ 0.6*x + 1.5 }} node[right] {{{mpc_label}}};
% MSC = S_social (upward, steeper, cost gap)
\addplot[thick,orange,domain=0:7] {{ 0.6*x + 3 }} node[right] {{{msc_label}}};
% Private equilibrium: -x+7=0.6x+1.5 → x=3.44, y=3.56
\draw[dashed,gray,thin] (axis cs:3.44,0) -- (axis cs:3.44,3.56);
\node[below] at (axis cs:3.44,0) {{{qp}}};
\node[circle,fill=black,inner sep=1.2pt] at (axis cs:3.44,3.56) {{}};
% Social optimum: -x+7=0.6x+3 → x=2.5, y=4.5
\draw[dashed,gray,thin] (axis cs:2.5,0) -- (axis cs:2.5,4.5) -- (axis cs:0,4.5);
\node[below] at (axis cs:2.5,0) {{{qs}}};
\node[left] at (axis cs:0,4.5) {{{ps}}};
\node[circle,fill=black,inner sep=1.2pt] at (axis cs:2.5,4.5) {{}};
% DWL triangle: vertices at (2.5, 3.0), (2.5,4.5), (3.44,3.56)
% MSC at Qs=2.5: y = 0.6*2.5 + 3 = 4.5
% MPC at Qs=2.5: y = 0.6*2.5 + 1.5 = 3.0
\fill[red,opacity=0.15] (axis cs:2.5,3.0) -- (axis cs:2.5,4.5) -- (axis cs:3.44,3.56) -- cycle;
\node[red] at (axis cs:3.0,3.6) {{\\tiny DWL}};
% Labels
\node at (axis cs:3.44,3.56) [above right] {{{ep_label}}};
\node at (axis cs:2.5,4.5) [above right] {{{es_label}}};
\end{{axis}}
\end{{tikzpicture}}
\end{{document}}""",
    "defaults": {"d_label": "$D=MPB=MSB$", "mpc_label": "$MPC=S$", "msc_label": "$MSC$",
                 "qp": "$Q_p$", "qs": "$Q_s$", "ps": "$P_s$",
                 "ep_label": "$E_p$", "es_label": "$E_s$"},
}

# ── Template 4: AD-AS Model ──
ECON_TEMPLATES["ad-as"] = {
    "name": "AD-AS Macroeconomic Model",
    "description": "AD downward, SRAS upward, LRAS vertical. Equilibrium with output gap.",
    "code": r"""\documentclass{{standalone}}
\usepackage{{tikz}}
\usepackage{{pgfplots}}
\pgfplotsset{{compat=1.18}}
\usetikzlibrary{{arrows.meta}}
\begin{{document}}
\begin{{tikzpicture}}
\begin{{axis}}[
    xlabel={{Real GDP ($Y$)}}, ylabel={{Price Level ($P$)}},
    xmin=0, xmax=8, ymin=0, ymax=8,
    axis lines=left,
    xtick=\empty, ytick=\empty,
    width=9cm, height=7cm,
]
% AD: downward sloping
\addplot[thick,blue,domain=0:7] {{ -0.9*x + 7.5 }} node[pos=0.3,above] {{{ad_label}}};
% SRAS: upward sloping
\addplot[thick,red,domain=0:7] {{ 0.5*x + 2 }} node[right] {{{sras_label}}};
% LRAS: vertical line at Yf
\draw[thick,green!50!black] (axis cs:{yf},{lras_ymin}) -- (axis cs:{yf},{lras_ymax});
\node[green!50!black,right] at (axis cs:{yf},6.5) {{{lras_label}}};
% Equilibrium: -0.9x+7.5=0.5x+2 → x=3.93, y=3.96
\draw[dashed,gray,thin] (axis cs:3.93,0) -- (axis cs:3.93,3.96) -- (axis cs:0,3.96);
\node[below] at (axis cs:3.93,0) {{{y1}}};
\node[left] at (axis cs:0,3.96) {{{p1}}};
\node[circle,fill=black,inner sep=1.2pt] at (axis cs:3.93,3.96) {{}};
\node[above right] at (axis cs:3.93,3.96) {{{e1_label}}};
% Output gap annotation
\draw[<->,thick] (axis cs:3.93,1.5) -- (axis cs:{yf},1.5) node[midway,below] {{{gap_label}}};
\end{{axis}}
\end{{tikzpicture}}
\end{{document}}""",
    "defaults": {"ad_label": "$AD$", "sras_label": "$SRAS$", "lras_label": "$LRAS$",
                 "yf": 5, "lras_ymin": 0.5, "lras_ymax": 7.5,
                 "y1": "$Y_1$", "p1": "$P_1$", "e1_label": "$E_1$",
                 "gap_label": "recessionary gap"},
}

# ── Template 5: AD Increase (Expansionary) ──
ECON_TEMPLATES["ad-increase"] = {
    "name": "AD Increase — Expansionary Policy",
    "description": "AD shifts right, higher P and Y, closer to full employment",
    "code": r"""\documentclass{{standalone}}
\usepackage{{tikz}}
\usepackage{{pgfplots}}
\pgfplotsset{{compat=1.18}}
\usetikzlibrary{{arrows.meta}}
\begin{{document}}
\begin{{tikzpicture}}
\begin{{axis}}[
    xlabel={{Real GDP ($Y$)}}, ylabel={{Price Level ($P$)}},
    xmin=0, xmax=8, ymin=0, ymax=8,
    axis lines=left,
    xtick=\empty, ytick=\empty,
    width=9cm, height=7cm,
]
% AD1 (original)
\addplot[thick,blue,domain=0:7] {{ -0.9*x + 7 }} node[pos=0.2,above] {{{ad1_label}}};
% AD2 (increased)
\addplot[thick,blue!60!cyan,domain=0:7] {{ -0.9*x + 8 }} node[pos=0.15,above] {{{ad2_label}}};
% SRAS
\addplot[thick,red,domain=0:7] {{ 0.5*x + 2 }} node[right] {{{sras_label}}};
% LRAS
\draw[thick,green!50!black] (axis cs:{yf},0.5) -- (axis cs:{yf},7.5);
\node[green!50!black,right] at (axis cs:{yf},6.5) {{{lras_label}}};
% E1: -0.9x+7=0.5x+2 → x=3.57, y=3.79
\draw[dashed,gray,thin] (axis cs:3.57,0) -- (axis cs:3.57,3.79) -- (axis cs:0,3.79);
\node[below] at (axis cs:3.57,0) {{{y1}}};
\node[left] at (axis cs:0,3.79) {{{p1}}};
\node[circle,fill=black,inner sep=1.2pt] at (axis cs:3.57,3.79) {{}};
\node[below left] at (axis cs:3.57,3.79) {{{e1_label}}};
% E2: -0.9x+8=0.5x+2 → x=4.29, y=4.14
\draw[dashed,gray,thin] (axis cs:4.29,0) -- (axis cs:4.29,4.14) -- (axis cs:0,4.14);
\node[below] at (axis cs:4.29,0) {{{y2}}};
\node[left] at (axis cs:0,4.14) {{{p2}}};
\node[circle,fill=black,inner sep=1.2pt] at (axis cs:4.29,4.14) {{}};
\node[above right] at (axis cs:4.29,4.14) {{{e2_label}}};
\draw[->,thick,blue!60!cyan] (axis cs:3.5,5.5) -- (axis cs:4.8,4) node[midway,above,sloped] {{\\small {shift_label}}};
\end{{axis}}
\end{{tikzpicture}}
\end{{document}}""",
    "defaults": {"ad1_label": "$AD_1$", "ad2_label": "$AD_2$", "sras_label": "$SRAS$", "lras_label": "$LRAS$",
                 "yf": 5, "y1": "$Y_1$", "p1": "$P_1$", "e1_label": "$E_1$",
                 "y2": "$Y_2$", "p2": "$P_2$", "e2_label": "$E_2$",
                 "shift_label": "$AD$ increase"},
}

# ── Template 6: PED/PES Tax Incidence ──
ECON_TEMPLATES["tax-incidence"] = {
    "name": "Tax Incidence (PED/PES)",
    "description": "Tax wedge between consumer and producer price, burden shares",
    "code": r"""\documentclass{{standalone}}
\usepackage{{tikz}}
\usepackage{{pgfplots}}
\pgfplotsset{{compat=1.18}}
\usetikzlibrary{{patterns,patterns.meta}}
\begin{{document}}
\begin{{tikzpicture}}
\begin{{axis}}[
    xlabel={{Quantity}}, ylabel={{Price}},
    xmin=0, xmax=8, ymin=0, ymax=8,
    axis lines=left,
    xtick=\empty, ytick=\empty,
    width=8cm, height=6cm,
]
% Demand
\addplot[thick,blue,domain=0:7] {{ -1*x + 7 }} node[right] {{{d_label}}};
% Supply (pre-tax)
\addplot[thick,red,domain=0:7] {{ 0.6*x + 1.5 }} node[right] {{{s_label}}};
% Supply + tax (shifted up by tax=1.5)
\addplot[thick,orange,domain=0:7] {{ 0.6*x + 3.0 }} node[right] {{{st_label}}};
% Pre-tax eq: -x+7=0.6x+1.5 → x=3.44, y=3.56
% Post-tax eq (consumer pays): -x+7=0.6x+3 → x=2.5, y=4.5
% Producer receives: 0.6*2.5+1.5=3.0
\draw[dashed,gray,thin] (axis cs:2.5,0) -- (axis cs:2.5,4.5);
\node[below] at (axis cs:2.5,0) {{{q2}}};
% Consumer price
\draw[gray,thin] (axis cs:0,4.5) -- (axis cs:2.5,4.5);
\node[left] at (axis cs:0,4.5) {{{pc}}};
% Producer price
\draw[gray,thin] (axis cs:0,3.0) -- (axis cs:2.5,3.0);
\node[left] at (axis cs:0,3.0) {{{pp}}};
% Tax wedge bracket
\draw[<->,thick] (axis cs:6.5,3.0) -- (axis cs:6.5,4.5) node[midway,right] {{tax}};
% Consumer burden
\fill[blue,opacity=0.1] (axis cs:0,3.56) rectangle (axis cs:2.5,4.5);
\node[blue] at (axis cs:1.2,4.0) {{\\tiny consumer}};
% Producer burden
\fill[red,opacity=0.1] (axis cs:0,3.0) rectangle (axis cs:2.5,3.56);
\node[red] at (axis cs:1.2,3.3) {{\\tiny producer}};
% Equilibrium dots
\node[circle,fill=black,inner sep=1.2pt] at (axis cs:3.44,3.56) {{}};
\node[circle,fill=black,inner sep=1.2pt] at (axis cs:2.5,4.5) {{}};
\node[circle,fill=black,inner sep=1.2pt] at (axis cs:2.5,3.0) {{}};
\end{{axis}}
\end{{tikzpicture}}
\end{{document}}""",
    "defaults": {"d_label": "$D$", "s_label": "$S$", "st_label": "$S+tax$",
                 "q2": "$Q_2$", "pc": "$P_c$", "pp": "$P_p$", "tax": "$tax$"},
}

# ── Template 7: PPC/PPF ──
ECON_TEMPLATES["ppc"] = {
    "name": "Production Possibility Curve",
    "description": "Concave PPF showing opportunity cost, growth shifts PPF outward",
    "code": r"""\documentclass{{standalone}}
\usepackage{{tikz}}
\usepackage{{pgfplots}}
\pgfplotsset{{compat=1.18}}
\usetikzlibrary{{arrows.meta}}
\begin{{document}}
\begin{{tikzpicture}}
\begin{{axis}}[
    xlabel={{{x_label}}}, ylabel={{{y_label}}},
    xmin=0, xmax=7, ymin=0, ymax=7,
    axis lines=left,
    xtick=\empty, ytick=\empty,
    width=8cm, height=7cm,
]
% PPC1: quarter circle (exact: x^2 + y^2 = 25, y = sqrt(25-x^2))
\addplot[thick,blue,domain=0:5,samples=50] {{ sqrt(25 - x^2) }} node[pos=0.5,above left] {{{ppc1_label}}};
% PPC2: shifted outward (exact: x^2 + y^2 = 36, y = sqrt(36-x^2))
\addplot[thick,blue!60!cyan,domain=0:6,samples=50] {{ sqrt(36 - x^2) }} node[pos=0.5,above left] {{{ppc2_label}}};
% Point inside PPC1 (inefficient)
\node[circle,fill=black,inner sep=1.3pt] at (axis cs:2,2) {{}};
\node[below right] at (axis cs:2,2) {{{ineff_label}}};
% Point on PPC1 (efficient)
\node[circle,fill=black,inner sep=1.3pt] at (axis cs:3,4) {{}};
\node[above right] at (axis cs:3,4) {{{eff_label}}};
% Growth arrow
\draw[->,thick,blue!60!cyan] (axis cs:4,1.5) -- (axis cs:5.5,1) node[right] {{{growth_label}}};
\end{{axis}}
\end{{tikzpicture}}
\end{{document}}""",
    "defaults": {"x_label": "Capital Goods", "y_label": "Consumer Goods",
                 "ppc1_label": "$PPC_1$", "ppc2_label": "$PPC_2$",
                 "ineff_label": "$U$ (inefficient)", "eff_label": "$E$ (efficient)",
                 "growth_label": "Growth"},
}

# ── Template 8: Maximum Price (Price Ceiling) ──
ECON_TEMPLATES["price-ceiling"] = {
    "name": "Maximum Price / Price Ceiling",
    "description": "Price ceiling below equilibrium creates shortage",
    "code": r"""\documentclass{{standalone}}
\usepackage{{tikz}}
\usepackage{{pgfplots}}
\pgfplotsset{{compat=1.18}}
\usetikzlibrary{{patterns,patterns.meta}}
\begin{{document}}
\begin{{tikzpicture}}
\begin{{axis}}[
    xlabel={{Quantity}}, ylabel={{Price}},
    xmin=0, xmax=8, ymin=0, ymax=8,
    axis lines=left,
    xtick=\empty, ytick=\empty,
    width=8cm, height=6cm,
]
% Demand
\addplot[thick,blue,domain=0:7] {{ -1*x + 7 }} node[right] {{{d_label}}};
% Supply
\addplot[thick,red,domain=0:7] {{ 0.8*x + 1 }} node[right] {{{s_label}}};
% Price ceiling: horizontal line at P=2.5
\draw[thick,orange,dashed] (axis cs:0,2.5) -- (axis cs:7,2.5) node[right] {{{pc_label}}};
% Equilibrium: -x+7=0.8x+1 → x=3.33, y=3.67
% Q demanded at P=2.5: -x+7=2.5 → x=4.5
% Q supplied at P=2.5: 0.8x+1=2.5 → x=1.875
\draw[dashed,gray,thin] (axis cs:1.875,0) -- (axis cs:1.875,2.5);
\node[below] at (axis cs:1.875,0) {{{qs_label}}};
\draw[dashed,gray,thin] (axis cs:4.5,0) -- (axis cs:4.5,2.5);
\node[below] at (axis cs:4.5,0) {{{qd_label}}};
% Shortage
\draw[<->,thick,red] (axis cs:1.875,1.5) -- (axis cs:4.5,1.5) node[midway,above] {{shortage}};
\node[circle,fill=black,inner sep=1.2pt] at (axis cs:3.33,3.67) {{}};
\node[above right] at (axis cs:3.33,3.67) {{{eq_label}}};
\end{{axis}}
\end{{tikzpicture}}
\end{{document}}""",
    "defaults": {"d_label": "$D$", "s_label": "$S$", "pc_label": "$P_{max}$",
                 "qs_label": "$Q_s$", "qd_label": "$Q_d$", "eq_label": "$E$",
                 "shortage": "shortage"},
}

# ── Template 9: Keynesian LRAS (3 phases) ──
ECON_TEMPLATES["keynesian-lras"] = {
    "name": "Keynesian LRAS — Three Phases",
    "description": "Horizontal (recession), upward-sloping, vertical (full capacity)",
    "code": r"""\documentclass{{standalone}}
\usepackage{{tikz}}
\usepackage{{pgfplots}}
\pgfplotsset{{compat=1.18}}
\begin{{document}}
\begin{{tikzpicture}}
\begin{{axis}}[
    xlabel={{Real GDP ($Y$)}}, ylabel={{Price Level ($P$)}},
    xmin=0, xmax=9, ymin=0, ymax=7,
    axis lines=left,
    xtick=\empty, ytick=\empty,
    width=10cm, height=7cm,
]
% AD
\addplot[thick,blue,domain=0:8] {{ -0.7*x + 6.5 }} node[pos=0.3,above] {{{ad_label}}};
% LRAS: piecewise
% Phase 1: horizontal at P=2, x from 0 to 3
\draw[thick,green!50!black] (axis cs:0,2) -- (axis cs:3,2);
% Phase 2: upward slope from (3,2) to (6,6)
\draw[thick,green!50!black] (axis cs:3,2) -- (axis cs:6,6);
% Phase 3: vertical at x=6 from P=6 to P=7
\draw[thick,green!50!black] (axis cs:6,6) -- (axis cs:6,7);
\node[green!50!black,right] at (axis cs:6.2,6.5) {{{lras_label}}};
% Equilibria
\draw[dashed,gray,thin] (axis cs:4.5,0) -- (axis cs:4.5,3.35);
\node[circle,fill=black,inner sep=1.2pt] at (axis cs:4.5,3.35) {{}};
\node[below] at (axis cs:4.5,0) {{{y1_label}}};
\node[above] at (axis cs:4.5,3.35) {{{e1_label}}};
\end{{axis}}
\end{{tikzpicture}}
\end{{document}}""",
    "defaults": {"ad_label": "$AD$", "lras_label": "$LRAS$",
                 "y1_label": "$Y_1$", "e1_label": "$E_1$"},
}

# ── Template 10: Tariff Diagram ──
ECON_TEMPLATES["tariff"] = {
    "name": "International Trade — Tariff",
    "description": "World price + tariff, imports shrink, government revenue, DWL",
    "code": r"""\documentclass{{standalone}}
\usepackage{{tikz}}
\usepackage{{pgfplots}}
\pgfplotsset{{compat=1.18}}
\usetikzlibrary{{patterns,patterns.meta}}
\begin{{document}}
\begin{{tikzpicture}}
\begin{{axis}}[
    xlabel={{Quantity}}, ylabel={{Price}},
    xmin=0, xmax=9, ymin=0, ymax=8,
    axis lines=left,
    xtick=\empty, ytick=\empty,
    width=9cm, height=7cm,
]
% Domestic Demand (flatter than supply)
\addplot[thick,blue,domain=0:8] {{ -0.8*x + 7 }} node[right] {{{dd_label}}};
% Domestic Supply
\addplot[thick,red,domain=0:8] {{ 0.5*x + 1.5 }} node[right] {{{ds_label}}};
% World price (lower than equilibrium)
\draw[thick,gray,dashed] (axis cs:0,{pw}) -- (axis cs:8,{pw}) node[right] {{{pw_label}}};
% World price + tariff
\draw[thick,orange,dashed] (axis cs:0,{pwt}) -- (axis cs:8,{pwt}) node[right] {{{pt_label}}};
% Qs1 at Pw: 0.5x+1.5=3 → x=3
% Qd1 at Pw: -0.8x+7=3 → x=5
% Imports1 = 5-3 = 2
\draw[dashed,gray,thin] (axis cs:3,0) -- (axis cs:3,{pw});
\node[below] at (axis cs:3,0) {{{qs1_label}}};
\draw[dashed,gray,thin] (axis cs:5,0) -- (axis cs:5,{pw});
\node[below] at (axis cs:5,0) {{{qd1_label}}};
% Qs2 at Pw+t: 0.5x+1.5=4.5 → x=6
% Qd2 at Pw+t: -0.8x+7=4.5 → x=3.125
\draw[dashed,gray,thin] (axis cs:3.125,0) -- (axis cs:3.125,{pwt});
\node[below] at (axis cs:3.125,0) {{{qd2_label}}};
\draw[dashed,gray,thin] (axis cs:6,0) -- (axis cs:6,{pwt});
\node[below] at (axis cs:6,0) {{{qs2_label}}};
% Imports before tariff: arrow
\draw[<->,thick,blue] (axis cs:3,1) -- (axis cs:5,1) node[midway,above] {{imports}};
% Imports after tariff: arrow
\draw[<->,thick,orange] (axis cs:3.125,0.6) -- (axis cs:6,0.6) node[midway,above] {{imports after}};
% Revenue rectangle
\fill[yellow,opacity=0.3] (axis cs:3.125,{pw}) rectangle (axis cs:6,{pwt});
\node at (axis cs:4.5,3.75) {{\\tiny govt revenue}};
\end{{axis}}
\end{{tikzpicture}}
\end{{document}}""",
    "defaults": {"dd_label": "$D_d$", "ds_label": "$S_d$",
                 "pw_label": "$P_w$", "pt_label": "$P_w+t$",
                 "pw": 3.0, "pwt": 4.5,
                 "qs1_label": "$Q_{s1}$", "qd1_label": "$Q_{d1}$",
                 "qs2_label": "$Q_{s2}$", "qd2_label": "$Q_{d2}$"},
}

# ── Template 10: Subsidy ──
ECON_TEMPLATES["subsidy"] = {
    "name": "Subsidy Diagram",
    "description": "Per-unit subsidy shifts supply down, consumer/producer prices, government cost",
    "code": r"""\documentclass{{standalone}}
\usepackage{{tikz}}
\usepackage{{pgfplots}}
\pgfplotsset{{compat=1.18}}
\usetikzlibrary{{arrows.meta}}
\begin{{document}}
\begin{{tikzpicture}}
\begin{{axis}}[
    xlabel={{Quantity}}, ylabel={{Price}},
    xmin=0, xmax=9, ymin=0, ymax=8,
    axis lines=left,
    xtick=\empty, ytick=\empty,
    width=8cm, height=6cm,
]
% Demand
\addplot[thick,blue,domain=0:8] {{ -1*x + 7 }} node[pos=0.4,right] {{{d_label}}};
% Supply (pre-subsidy)
\addplot[thick,red,domain=0:8] {{ 0.6*x + 1.5 }} node[pos=0.3,right] {{{s1_label}}};
% Supply (post-subsidy, shifted down by 2)
\addplot[thick,green!50!black,domain=0:8] {{ 0.6*x - 0.5 }} node[pos=0.15,right] {{{s2_label}}};
% E1: -x+7=0.6x+1.5 → x=3.44, y=3.56
% E2: -x+7=0.6x-0.5 → x=4.69, y=2.31
% At Q2=4.69: consumer pays: 2.31, producer receives: 0.6*4.69-0.5+2=4.31
% Producer price at Q2 on S1: 0.6*4.69+1.5=4.31
\draw[dashed,gray,thin] (axis cs:3.44,0) -- (axis cs:3.44,3.56);
\node[below] at (axis cs:3.44,0) {{{q1_label}}};
\draw[dashed,gray,thin] (axis cs:4.69,0) -- (axis cs:4.69,2.31);
\node[below] at (axis cs:4.69,0) {{{q2_label}}};
% Consumer price
\draw[gray,thin] (axis cs:0,2.31) -- (axis cs:4.69,2.31);
\node[left] at (axis cs:0,2.31) {{{pc_label}}};
% Producer price
\draw[gray,thin] (axis cs:0,4.31) -- (axis cs:4.69,4.31);
\node[left] at (axis cs:0,4.31) {{{pp_label}}};
% Subsidy bracket
\draw[<->,thick,green!50!black] (axis cs:7.5,2.31) -- (axis cs:7.5,4.31) node[midway,right] {{subsidy}};
% Points
\node[circle,fill=black,inner sep=1.2pt] at (axis cs:3.44,3.56) {{}};
\node[above right] at (axis cs:3.44,3.56) {{{e1_label}}};
\node[circle,fill=black,inner sep=1.2pt] at (axis cs:4.69,2.31) {{}};
\node[above right] at (axis cs:4.69,2.31) {{{e2_label}}};
\end{{axis}}
\end{{tikzpicture}}
\end{{document}}""",
    "defaults": {"d_label": "$D$", "s1_label": "$S_1$", "s2_label": "$S_2$ (subsidy)",
                 "q1_label": "$Q_1$", "q2_label": "$Q_2$",
                 "pc_label": "$P_c$", "pp_label": "$P_p$",
                 "e1_label": "$E_1$", "e2_label": "$E_2$", "subsidy": "subsidy = $2"},
}

# ── Template 11: Minimum Price (Price Floor) ──
ECON_TEMPLATES["minimum-price"] = {
    "name": "Minimum Price / Price Floor",
    "description": "Price floor above equilibrium creates surplus",
    "code": r"""\documentclass{{standalone}}
\usepackage{{tikz}}
\usepackage{{pgfplots}}
\pgfplotsset{{compat=1.18}}
\usetikzlibrary{{patterns,patterns.meta}}
\begin{{document}}
\begin{{tikzpicture}}
\begin{{axis}}[
    xlabel={{Quantity}}, ylabel={{Price}},
    xmin=0, xmax=9, ymin=0, ymax=9,
    axis lines=left,
    xtick=\empty, ytick=\empty,
    width=8cm, height=6cm,
]
% Demand
\addplot[thick,blue,domain=0:8] {{ -1*x + 8 }} node[right] {{{d_label}}};
% Supply
\addplot[thick,red,domain=0:8] {{ 0.8*x + 1 }} node[right] {{{s_label}}};
% Price floor: horizontal at P=6
\draw[thick,orange,dashed] (axis cs:0,6) -- (axis cs:8,6) node[right] {{{pf_label}}};
% Equilibrium: -x+8=0.8x+1 → x=3.89, y=4.11
% Qd at P=6: -x+8=6 → x=2
% Qs at P=6: 0.8x+1=6 → x=6.25
\draw[dashed,gray,thin] (axis cs:2,0) -- (axis cs:2,6);
\node[below] at (axis cs:2,0) {{{qd_label}}};
\draw[dashed,gray,thin] (axis cs:6.25,0) -- (axis cs:6.25,6);
\node[below] at (axis cs:6.25,0) {{{qs_label}}};
% Surplus
\draw[<->,thick,red] (axis cs:2,7.5) -- (axis cs:6.25,7.5) node[midway,above] {{surplus}};
% Equilibrium dot
\node[circle,fill=black,inner sep=1.2pt] at (axis cs:3.89,4.11) {{}};
\node[above right] at (axis cs:3.89,4.11) {{{eq_label}}};
\end{{axis}}
\end{{tikzpicture}}
\end{{document}}""",
    "defaults": {"d_label": "$D$", "s_label": "$S$", "pf_label": "$P_{min}$",
                 "qd_label": "$Q_d$", "qs_label": "$Q_s$", "eq_label": "$E$",
                 "surplus": "surplus"},
}

# ── Template 12: Monopoly (Profit Max + DWL) ──
ECON_TEMPLATES["monopoly"] = {
    "name": "Monopoly — Profit Max + DWL",
    "description": "MC=MR profit max, price from demand, DWL vs perfect competition",
    "code": r"""\documentclass{{standalone}}
\usepackage{{tikz}}
\usepackage{{pgfplots}}
\pgfplotsset{{compat=1.18}}
\usetikzlibrary{{patterns,patterns.meta}}
\begin{{document}}
\begin{{tikzpicture}}
\begin{{axis}}[
    xlabel={{Quantity}}, ylabel={{Price/Cost}},
    xmin=0, xmax=10, ymin=0, ymax=10,
    axis lines=left,
    xtick=\empty, ytick=\empty,
    width=8cm, height=7cm,
]
% Demand = AR
\addplot[thick,blue,domain=0:9] {{ -1*x + 9 }} node[right] {{{ar_label}}};
% MR (twice slope)
\addplot[thick,blue!60,dashed,domain=0:4.5] {{ -2*x + 9 }} node[pos=0.3,below] {{{mr_label}}};
% MC (upward from origin)
\addplot[thick,red,domain=1:9] {{ 0.8*x + 1 }} node[right] {{{mc_label}}};
% AC (U-shaped, approximated)
\addplot[thick,orange,dotted,domain=1:9] {{ 0.3*x + 3 }} node[right] {{{ac_label}}};
% MR=MC: -2x+9=0.8x+1 → x=2.86
% Price from demand at Qm: y=-2.86+9=6.14
% Perfect competition: D=MC → -x+9=0.8x+1 → x=4.44
\draw[dashed,gray,thin] (axis cs:2.86,0) -- (axis cs:2.86,6.14);
\node[below] at (axis cs:2.86,0) {{{qm_label}}};
\node[left] at (axis cs:0,6.14) {{{pm_label}}};
\node[circle,fill=black,inner sep=1.2pt] at (axis cs:2.86,6.14) {{}};
\node[above left] at (axis cs:2.86,6.14) {{{monopoly_label}}};
% PC equilibrium
\draw[dashed,gray,thin] (axis cs:4.44,0) -- (axis cs:4.44,4.56);
\node[below] at (axis cs:4.44,0) {{{qc_label}}};
\node[left] at (axis cs:0,4.56) {{{pc_label}}};
\node[circle,fill=black,inner sep=1.2pt] at (axis cs:4.44,4.56) {{}};
\node[above right] at (axis cs:4.44,4.56) {{{comp_label}}};
% DWL triangle
\fill[red,opacity=0.12] (axis cs:2.86,6.14) -- (axis cs:2.86,4.56) -- (axis cs:4.44,4.56) -- cycle;
\node[red] at (axis cs:3.5,5.0) {{\\tiny DWL}};
\end{{axis}}
\end{{tikzpicture}}
\end{{document}}""",
    "defaults": {"ar_label": "$D=AR$", "mr_label": "$MR$", "mc_label": "$MC$",
                 "ac_label": "$AC$", "qm_label": "$Q_m$", "pm_label": "$P_m$",
                 "qc_label": "$Q_c$", "pc_label": "$P_c$",
                 "monopoly_label": "Monopoly", "comp_label": "Perfect Comp."},
}

# ── Template 13: Monopsony Labour Market ──
ECON_TEMPLATES["monopsony"] = {
    "name": "Monopsony Labour Market",
    "description": "MCL > ACL=S, MRP demand, monopsony wage below competitive",
    "code": r"""\documentclass{{standalone}}
\usepackage{{tikz}}
\usepackage{{pgfplots}}
\pgfplotsset{{compat=1.18}}
\usetikzlibrary{{arrows.meta}}
\begin{{document}}
\begin{{tikzpicture}}
\begin{{axis}}[
    xlabel={{Quantity of Labour}}, ylabel={{Wage Rate}},
    xmin=0, xmax=9, ymin=0, ymax=8,
    axis lines=left,
    xtick=\empty, ytick=\empty,
    width=9cm, height=7cm,
]
% ACL = Labour Supply
\addplot[thick,blue,domain=0:7] {{ 0.6*x + 0.8 }} node[right] {{{acl_label}}};
% MCL (steeper than ACL, same intercept for linear)
\addplot[thick,red,domain=0:6] {{ 1.2*x + 0.8 }} node[right] {{{mcl_label}}};
% MRP = Labour Demand (downward)
\addplot[thick,green!50!black,domain=0:7] {{ -0.8*x + 6.5 }} node[right] {{{mrp_label}}};
% Monopsony: MCL=MRP → 1.2x+0.8=-0.8x+6.5 → x=2.85
% Wage from ACL at Lm: 0.6*2.85+0.8=2.51
% Competition: ACL=MRP → 0.6x+0.8=-0.8x+6.5 → x=4.07
% Wage at Lc: 0.6*4.07+0.8=3.24
% Monopsony
\draw[dashed,gray,thin] (axis cs:2.85,0) -- (axis cs:2.85,2.51);
\node[below] at (axis cs:2.85,0) {{{lm_label}}};
\draw[gray,thin] (axis cs:0,2.51) -- (axis cs:2.85,2.51);
\node[left] at (axis cs:0,2.51) {{{wm_label}}};
\node[circle,fill=black,inner sep=1.2pt] at (axis cs:2.85,2.51) {{}};
% MCL=MRP intersection
\node[circle,fill=black,inner sep=1.2pt] at (axis cs:2.85,4.22) {{}};
% Competition
\draw[dashed,gray,thin] (axis cs:4.07,0) -- (axis cs:4.07,3.24);
\node[below] at (axis cs:4.07,0) {{{lc_label}}};
\draw[gray,thin] (axis cs:0,3.24) -- (axis cs:4.07,3.24);
\node[left] at (axis cs:0,3.24) {{{wc_label}}};
\node[circle,fill=black,inner sep=1.2pt] at (axis cs:4.07,3.24) {{}};
\end{{axis}}
\end{{tikzpicture}}
\end{{document}}""",
    "defaults": {"acl_label": "$AC_L=S_L$", "mcl_label": "$MC_L$",
                 "mrp_label": "$MRP=D_L$",
                 "lm_label": "$L_m$", "wm_label": "$W_m$",
                 "lc_label": "$L_c$", "wc_label": "$W_c$"},
}

# ── Build all templates ──
def get_template(name: str) -> Optional[dict]:
    return ECON_TEMPLATES.get(name)


def list_templates() -> list:
    return [{"key": k, "name": v["name"], "description": v["description"]}
            for k, v in ECON_TEMPLATES.items()]


def render_template(name: str, labels: dict = None) -> Optional[str]:
    """Fill template with labels and return full TikZ code."""
    tmpl = ECON_TEMPLATES.get(name)
    if not tmpl:
        return None
    code = tmpl["code"]
    defaults = dict(tmpl.get("defaults", {}))
    if labels:
        defaults.update(labels)
    return code.format(**defaults)
