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


# ── Extraction + Rendering ──

def extract_and_render_plot(content: str) -> str:
    """Extract ```plot JSON blocks and render via matplotlib."""
    from agent.diagrams.plotter import render_economics
    from agent.diagrams.spec_builder import build_spec

    pattern = re.compile(r'```plot\n(.*?)```', re.DOTALL)
    def _replace(m):
        try:
            params = json.loads(m.group(1))
            if "type" in params and "curves" not in params:
                spec = build_spec(params)
            else:
                spec = params
            uri = render_economics(spec)
            if uri:
                return f"![diagram]({uri})"
        except Exception:
            pass
        return m.group(0)
    return pattern.sub(_replace, content)


def extract_and_render_mermaid(content: str) -> str:
    """Extract ```mermaid blocks and render. Fallback to code block."""
    pattern = re.compile(r'```mermaid\n(.*?)```', re.DOTALL)
    def _replace(m):
        uri = render_mermaid(m.group(1))
        if uri:
            return f"![diagram]({uri})"
        return m.group(0)
    return pattern.sub(_replace, content)


def extract_and_render_tikz(content: str) -> str:
    """Extract ```tikz blocks and render. Fallback to code block."""
    template_pattern = re.compile(r'^```tikz\s+template=(\w+)\n(.*?)```', re.DOTALL | re.MULTILINE)
    bare_pattern = re.compile(r'^```tikz\n(.*?)```', re.DOTALL)

    def _render_template(m):
        uri = render_tikz(m.group(2), m.group(1))
        if uri:
            return f"![diagram]({uri})"
        return m.group(0)

    def _render_bare(m):
        uri = render_tikz(m.group(1), "general")
        if uri:
            return f"![diagram]({uri})"
        return m.group(0)

    content = template_pattern.sub(_render_template, content)
    content = bare_pattern.sub(_render_bare, content)
    return content


def extract_and_render_vegalite(content: str) -> str:
    """Extract ```vega-lite JSON blocks and render. Fallback."""
    pattern = re.compile(r'```(?:vegalite|vega-lite)\n(.*?)```', re.DOTALL)
    def _replace(m):
        uri = render_vegalite(m.group(1))
        if uri:
            return f"![diagram]({uri})"
        return m.group(0)
    return pattern.sub(_replace, content)


def render_all_diagrams(content: str) -> str:
    """Master post-processor: extract + render all diagram code blocks."""
    errors = 0
    try:
        content = extract_and_render_plot(content)
    except Exception:
        errors += 1
    try:
        content = extract_and_render_mermaid(content)
    except Exception:
        errors += 1
    try:
        content = extract_and_render_tikz(content)
    except Exception:
        errors += 1
    try:
        content = extract_and_render_vegalite(content)
    except Exception:
        errors += 1

    if errors > 0:
        import sys
        print(f"[diagrams] {errors} renderer(s) failed silently", file=sys.stderr, flush=True)

    return content
