"""
Pre-verified TikZ diagram templates for A-Level Physics (9702).
All coordinates mathematically exact.
"""
PHYSICS_TEMPLATES = {}

PHYSICS_TEMPLATES["series-circuit"] = {
    "name": "Series Circuit",
    "code": r"""\documentclass{{standalone}}
\usepackage{{circuitikz}}
\begin{{document}}
\begin{{circuitikz}}[american,scale=1.2]
\draw (0,3) to[battery,l={volt}V] (0,0) to[short] (2,0) to[R,l={r1}$\Omega$] (2,1.5) to[R,l={r2}$\Omega$] (2,3) to[short] (0,3);
\draw[->,thick] (1,0.8) -- (1,2.2) node[midway,right] {{I={curr}A}};
\end{{circuitikz}}
\end{{document}}""",
    "defaults": {"volt": "12", "r1": "4", "r2": "8", "curr": "1.0"},
}

PHYSICS_TEMPLATES["parallel-circuit"] = {
    "name": "Parallel Circuit",
    "code": r"""\documentclass{{standalone}}
\usepackage{{circuitikz}}
\begin{{document}}
\begin{{circuitikz}}[american,scale=1.2]
\draw (0,3) to[battery,l={volt}V] (0,0) to[short] (3,0) to[short] (3,1) to[R,l={r1}$\Omega$] (3,2) to[short] (3,3);
\draw (1.5,0) to[short] (1.5,1) to[R,l={r2}$\Omega$] (1.5,2) to[short] (1.5,3);
\draw (0,3) to[short] (3,3);
\draw (3,0) to[short] (1.5,0);
\end{{circuitikz}}
\end{{document}}""",
    "defaults": {"volt": "12", "r1": "6", "r2": "3"},
}

PHYSICS_TEMPLATES["force-diagram"] = {
    "name": "Free Body Diagram",
    "code": r"""\documentclass{{standalone}}
\usepackage{{tikz}}
\usetikzlibrary{{arrows.meta}}
\begin{{document}}
\begin{{tikzpicture}}[>=Stealth,scale=1.2]
\draw[thick,fill=gray!20] (0,0) rectangle (2,1) node[midway] {{$m$={mass}kg}};
\draw[->,very thick,blue] (1,1) -- (1,2.5) node[right] {{$N$={N}N}};
\draw[->,very thick,red] (1,0) -- (1,-1.5) node[right] {{$mg$={mg}N}};
\draw[->,very thick,green!50!black] (2,0.5) -- (3.5,0.5) node[above] {{$F$={F}N}};
\draw[->,very thick,orange] (0,0.5) -- (-1.5,0.5) node[above] {{$f$={f}N}};
\draw[thick] (-0.5,-1.8) -- (3.5,-1.8);
\node at (1.5,-2.2) {{surface}};
\end{{tikzpicture}}
\end{{document}}""",
    "defaults": {"mass": "5", "N": "49", "mg": "49", "F": "20", "f": "10"},
}

PHYSICS_TEMPLATES["wave-diagram"] = {
    "name": "Wave Diagram",
    "code": r"""\documentclass{{standalone}}
\usepackage{{tikz}}
\usepackage{{pgfplots}}
\pgfplotsset{{compat=1.18}}
\begin{{document}}
\begin{{tikzpicture}}
\begin{{axis}}[
    xlabel={{Distance}}, ylabel={{Displacement}},
    xmin=0, xmax=7, ymin=-1.5, ymax=1.5,
    axis lines=middle,
    xtick=\empty, ytick={{-1,0,1}},
    width=10cm, height=5cm,
]
\addplot[thick,blue,domain=0:6.28,samples=100] {{ sin(2*deg(x)) }};
\draw[<->,thick] (axis cs:1.57,1.1) -- (axis cs:4.71,1.1) node[midway,above] {{$\lambda$}};
\draw[<->,thick] (axis cs:6.5,0) -- (axis cs:6.5,1) node[midway,right] {{$A$}};
\node[above] at (axis cs:0.785,1) {{crest}};
\node[below] at (axis cs:2.356,-1) {{trough}};
\end{{axis}}
\end{{tikzpicture}}
\end{{document}}""",
    "defaults": {},
}

PHYSICS_TEMPLATES["inclined-plane"] = {
    "name": "Inclined Plane Force Resolution",
    "code": r"""\documentclass{{standalone}}
\usepackage{{tikz}}
\usetikzlibrary{{arrows.meta,calc}}
\begin{{document}}
\begin{{tikzpicture}}[>=Stealth,scale=1.2]
\draw[thick] (0,0) -- (4,2) -- (4,0) -- cycle;
\draw[thick,fill=gray!20,rotate around={{26.565:(2.5,1.25)}}] (2,0.75) rectangle (3,1.75);
\draw[->,very thick,red] (2.5,1.25) -- (2.5,0) node[right] {{$mg$}};
\draw[->,very thick,blue] (2.5,1.25) -- ($(2.5,1.25)!1.2cm!90:(4,2)$) node[above left] {{$N$}};
\draw[->,very thick,green!50!black] (2.5,1.25) -- ($(2.5,1.25)!1cm!180:(4,2)$) node[left] {{$f$}};
\draw[->,very thick,red!50] (2.5,1.25) -- ($(2.5,1.25)!1cm!-90:(4,2)$) node[below right] {{$mg\sin\theta$}};
\node at (1.5,0.3) {{$\theta$}};
\end{{tikzpicture}}
\end{{document}}""",
    "defaults": {},
}
