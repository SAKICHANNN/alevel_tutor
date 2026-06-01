"""
Unified Diagram Generator — renders academic diagrams via Kroki API.

Supported engines (via https://kroki.io):
  - mermaid:  Flowcharts, graphs, simple diagrams
  - tikz:     Circuits (circuitikz), chemical structures (chemfig),
              force diagrams, energy cycles, coordinate geometry,
              economic graphs (pgfplots), wave diagrams, field lines
  - vega-lite: Data charts, spectra, economic data visualization
  - graphviz:  Directed graphs, decision trees
  - plantuml:  UML, sequence diagrams
  - blockdiag: Block diagrams

All engines return SVG, converted to base64 data URI for markdown embedding.
"""
import base64
import json
import re
import time
from pathlib import Path
from typing import Optional

import requests

KROKI_BASE = "https://kroki.io"

# ── Engine capabilities ──

ENGINE_CAPABILITIES = {
    "tikz": {
        "packages": ["tikz", "pgfplots", "circuitikz", "chemfig", "mhchem",
                      "tikz-3dplot", "amsmath", "amssymb"],
        "best_for": [
            "circuits", "force_diagrams", "energy_cycles", "coordinate_graphs",
            "trig_graphs", "mechanics_diagrams", "vector_diagrams", "field_lines",
            "wave_diagrams", "economic_graphs", "chemical_structures",
            "molecular_geometry", "structural_formulas", "experimental_setup",
        ],
        "doc": "Full LaTeX document with \\documentclass{standalone} required",
    },
    "mermaid": {
        "best_for": ["flowcharts", "process_diagrams", "state_machines",
                      "simple_circuits", "block_diagrams", "sequence_diagrams"],
        "doc": "Mermaid.js syntax, no wrapper needed",
    },
    "vegalite": {
        "best_for": ["data_charts", "spectra", "rate_graphs", "titration_curves",
                      "ph_curves", "iv_characteristics", "economic_scatter"],
        "doc": "Vega-Lite JSON specification",
    },
    "graphviz": {
        "best_for": ["reaction_pathways", "decision_trees", "concept_maps"],
        "doc": "DOT language",
    },
}

# ── LaTeX templates for common diagram types ──

TIKZ_TEMPLATES = {
    "circuit": r"""\documentclass{{standalone}}
\usepackage{{circuitikz}}
\begin{{document}}
\begin{{circuitikz}}[american]
{content}
\end{{circuitikz}}
\end{{document}}""",

    "graph": r"""\documentclass{{standalone}}
\usepackage{{tikz}}
\usepackage{{pgfplots}}
\pgfplotsset{{compat=1.18}}
\begin{{document}}
{content}
\end{{document}}""",

    "chemfig": r"""\documentclass{{standalone}}
\usepackage{{chemfig}}
\begin{{document}}
{content}
\end{{document}}""",

    "mechanism": r"""\documentclass{{standalone}}
\usepackage{{tikz}}
\usepackage{{chemfig}}
\begin{{document}}
{content}
\end{{document}}""",

    "force": r"""\documentclass{{standalone}}
\usepackage{{tikz}}
\usetikzlibrary{{arrows.meta,positioning,patterns}}
\begin{{document}}
\begin{{tikzpicture}}[>=Stealth]
{content}
\end{{tikzpicture}}
\end{{document}}""",

    "general": r"""\documentclass{{standalone}}
\usepackage{{tikz}}
\usepackage{{pgfplots}}
\usepackage{{circuitikz}}
\usepackage{{chemfig}}
\usepackage[version=4]{{mhchem}}
\usepackage{{amsmath}}
\usepackage{{amssymb}}
\pgfplotsset{{compat=1.18}}
\usetikzlibrary{{arrows.meta,positioning,patterns,calc,shapes,decorations}}
\begin{{document}}
{content}
\end{{document}}""",
}


def render_mermaid(code: str) -> Optional[str]:
    """Render Mermaid code → base64 SVG data URI."""
    try:
        resp = requests.post(
            f"{KROKI_BASE}/mermaid/svg",
            data=code.encode("utf-8"),
            headers={"Content-Type": "text/plain"},
            timeout=15,
        )
        if resp.status_code == 200:
            b64 = base64.b64encode(resp.content).decode("ascii")
            return f"data:image/svg+xml;base64,{b64}"
    except Exception:
        pass
    return None


def render_tikz(code: str, template: str = "general") -> Optional[str]:
    """Render TikZ code → base64 SVG data URI."""
    wrapper = TIKZ_TEMPLATES.get(template, TIKZ_TEMPLATES["general"])
    full_code = wrapper.format(content=code)

    try:
        resp = requests.post(
            f"{KROKI_BASE}/tikz/svg",
            data=full_code.encode("utf-8"),
            headers={"Content-Type": "text/plain"},
            timeout=30,
        )
        if resp.status_code == 200:
            b64 = base64.b64encode(resp.content).decode("ascii")
            return f"data:image/svg+xml;base64,{b64}"
    except Exception:
        pass
    return None


def render_vegalite(spec_json: str) -> Optional[str]:
    """Render Vega-Lite JSON → base64 SVG data URI."""
    try:
        resp = requests.post(
            f"{KROKI_BASE}/vegalite/svg",
            data=spec_json.encode("utf-8"),
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
        if resp.status_code == 200:
            b64 = base64.b64encode(resp.content).decode("ascii")
            return f"data:image/svg+xml;base64,{b64}"
    except Exception:
        pass
    return None


def render_graphviz(code: str) -> Optional[str]:
    """Render Graphviz DOT → base64 SVG data URI."""
    try:
        resp = requests.post(
            f"{KROKI_BASE}/graphviz/svg",
            data=code.encode("utf-8"),
            headers={"Content-Type": "text/plain"},
            timeout=15,
        )
        if resp.status_code == 200:
            b64 = base64.b64encode(resp.content).decode("ascii")
            return f"data:image/svg+xml;base64,{b64}"
    except Exception:
        pass
    return None


def render_diagram(code: str, engine: str = "mermaid",
                   template: str = "general") -> Optional[str]:
    """Unified render entry point. Returns base64 data URI or None."""
    if engine == "mermaid":
        return render_mermaid(code)
    elif engine == "tikz":
        return render_tikz(code, template)
    elif engine in ("vegalite", "vega-lite"):
        return render_vegalite(code)
    elif engine == "graphviz":
        return render_graphviz(code)
    return None


def extract_and_render_mermaid(content: str) -> str:
    """Find ```mermaid blocks in text and replace with rendered SVG images."""
    pattern = re.compile(r'```mermaid\s*\n(.*?)```', re.DOTALL)

    def _replace(match):
        code = match.group(1).strip()
        uri = render_mermaid(code)
        if uri:
            return f'\n\n![diagram]({uri})\n\n'
        return match.group(0)

    return pattern.sub(_replace, content)


def extract_and_render_tikz(content: str) -> str:
    """Find ```tikz blocks in text and replace with rendered SVG images."""
    pattern = re.compile(r'```tikz(?:\s+template=(\w+))?\s*\n(.*?)```', re.DOTALL)

    def _replace(match):
        template = match.group(1) or "general"
        code = match.group(2).strip()
        uri = render_tikz(code, template)
        if uri:
            return f'\n\n![diagram]({uri})\n\n'
        return match.group(0)

    return pattern.sub(_replace, content)


def extract_and_render_vegalite(content: str) -> str:
    """Find ```vegalite / ```vega-lite blocks and replace with rendered SVG."""
    pattern = re.compile(r'```(?:vegalite|vega-lite)\s*\n(.*?)```', re.DOTALL)

    def _replace(match):
        code = match.group(1).strip()
        uri = render_vegalite(code)
        if uri:
            return f'\n\n![diagram]({uri})\n\n'
        return match.group(0)

    return pattern.sub(_replace, content)


def extract_and_render_plot(content: str) -> str:
    """Find ```plot blocks → render via matplotlib → compact base64 PNG."""
    pattern = re.compile(r'```plot\s*\n(.*?)```', re.DOTALL)

    def _replace(match):
        try:
            spec = json.loads(match.group(1).strip())
            from agent.diagrams.plotter import render_economics
            uri = render_economics(spec)
            if uri:
                return f'\n\n![diagram]({uri})\n\n'
        except (json.JSONDecodeError, Exception):
            pass
        return match.group(0)

    return pattern.sub(_replace, content)


def render_all_diagrams(content: str) -> str:
    """Post-process LLM output: render all diagram code blocks to images."""
    content = extract_and_render_plot(content)
    content = extract_and_render_mermaid(content)
    content = extract_and_render_tikz(content)
    content = extract_and_render_vegalite(content)
    return content
