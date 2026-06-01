"""
Phase 1: Python matplotlib rendering engine for A-Level Economics diagrams.

All 14 diagram types via parameterized JSON specs.
LLM describes what → Python computes + renders.

Key guarantees:
  - All intersections solved mathematically (scipy.optimize)
  - All labels positioned by computed coordinates
  - Output: SVG to data/rendered/{hash}.svg
  - Short URL reference: /diagrams/{hash}.svg
"""
import base64
import hashlib
import io
import json
import math
import re
from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

RENDER_DIR = Path(__file__).parent.parent.parent / "data" / "rendered"
RENDER_DIR.mkdir(parents=True, exist_ok=True)

# ── Math utilities ──

def solve_line_intersection(i1, s1, i2, s2):
    """Solve intercept+slope*x for two lines."""
    if abs(s1 - s2) < 1e-9:
        return None
    x = (i2 - i1) / (s1 - s2)
    y = i1 + s1 * x
    return (x, y)

def x_for_y(intercept, slope, y):
    if abs(slope) < 1e-9:
        return None
    return (y - intercept) / slope

# ── Color palette ──

COLORS = {
    "demand": "#2B5B84",
    "demand2": "#4C9BCF",
    "supply": "#C44E52",
    "supply2": "#E88C8F",
    "msc": "#E67E22",
    "msb": "#27AE60",
    "ad": "#2B5B84",
    "sras": "#C44E52",
    "lras": "#2C3E50",
    "tax": "#E74C3C",
    "subsidy": "#2ECC71",
    "marginal": "#E67E22",
    "dwl": "#F1948A",
    "cs": "#AED6F1",
    "ps": "#F5B7B1",
    "revenue": "#F9E79F",
    "price_ctrl": "#E74C3C",
    "eq": "#1a1a1a",
    "grid": "#e0e0e0",
}

# ── Rendering ──

def _hash_spec(spec: dict) -> str:
    raw = json.dumps(spec, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()[:12]

def render_economics(spec: dict) -> Optional[str]:
    """Render economics diagram. Returns compact base64 PNG data URI."""
    spec_hash = _hash_spec(spec)
    out_path = RENDER_DIR / f"econ_{spec_hash}.svg"
    
    try:
        fig, ax = _plot(spec)
        # Save full-quality SVG to disk
        fig.savefig(str(out_path), format='svg', bbox_inches='tight',
                    facecolor='white', edgecolor='none', pad_inches=0.2)
        # Also generate compact PNG for inline display
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight',
                    facecolor='white', edgecolor='none', pad_inches=0.15)
        plt.close(fig)
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode('ascii')
        return f"data:image/png;base64,{b64}"
    except Exception as e:
        print(f"Render error: {e}")
        return None

def _plot(spec: dict):
    curves = spec.get("curves", [])
    equilibria = spec.get("equilibria", [])
    shading = spec.get("shading", [])
    axes = spec.get("axes", {"x": "Q", "y": "P"})
    x_max = spec.get("x_max", 10)
    y_max = spec.get("y_max", 10)

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_xlim(0, x_max)
    ax.set_ylim(0, y_max)
    ax.set_xlabel(axes.get("x", "Quantity"), fontsize=16, fontweight='bold', labelpad=12)
    ax.set_ylabel(axes.get("y", "Price"), fontsize=16, fontweight='bold', labelpad=12)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)

    # Draw curves
    drawn = {}
    for c in curves:
        ctype = c.get("type", "line")
        if ctype == "line":
            _draw_line(ax, c, x_max, y_max, drawn)
        elif ctype == "vertical":
            _draw_vline(ax, c, y_max, drawn)
        elif ctype == "horizontal":
            _draw_hline(ax, c, x_max, drawn)

    # Compute & draw equilibrium points
    for eq in equilibria:
        c1, c2 = eq.get("c1"), eq.get("c2")
        if not (c1 and c2 and c1 in drawn and c2 in drawn):
            continue
        d1, d2 = drawn[c1], drawn[c2]
        xy = None
        if d1["type"] == "line" and d2["type"] == "line":
            xy = solve_line_intersection(d1["i"], d1["s"], d2["i"], d2["s"])
        elif d1["type"] == "vertical":
            xy = (d1["x"], d2["i"] + d2["s"] * d1["x"]) if d2["type"] == "line" else None
        elif d2["type"] == "vertical":
            xy = (d2["x"], d1["i"] + d1["s"] * d2["x"]) if d1["type"] == "line" else None
        elif d1["type"] == "horizontal":
            xv = x_for_y(d2["i"], d2["s"], d1["y"]) if d2["type"] == "line" else None
            xy = (xv, d1["y"]) if xv else None
        elif d2["type"] == "horizontal":
            xv = x_for_y(d1["i"], d1["s"], d2["y"]) if d1["type"] == "line" else None
            xy = (xv, d2["y"]) if xv else None

        if xy and 0 <= xy[0] <= x_max and 0 <= xy[1] <= y_max:
            _draw_eq_point(ax, xy, eq)

    # Draw shading
    for sh in shading:
        _draw_shading(ax, sh, drawn, x_max)

    return fig, ax

def _draw_line(ax, c, x_max, y_max, drawn):
    i = c.get("intercept", 5)
    s = c.get("slope", -1)
    name = c.get("id", "")
    color = COLORS.get(c.get("color", "demand"), "#333")
    style = c.get("style", "-")
    width = c.get("width", 2)
    label = c.get("label", "")
    label_pos = c.get("label_pos", 0.7)

    # Compute visible range
    x_vals = np.linspace(0, x_max, 200)
    y_vals = i + s * x_vals
    mask = (y_vals >= 0) & (y_vals <= y_max)
    x_vals, y_vals = x_vals[mask], y_vals[mask]
    if len(x_vals) > 1:
        ax.plot(x_vals, y_vals, linestyle=style, color=color, linewidth=width, zorder=2)

    if label:
        idx = min(int(len(x_vals) * label_pos), len(x_vals) - 1)
        if idx >= 0:
            ax.annotate(label, xy=(x_vals[idx], y_vals[idx]),
                        fontsize=13, color=color, fontweight='bold',
                        xytext=(8, 8), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                                 edgecolor=color, linewidth=0.8, alpha=0.9))

    drawn[name] = {"type": "line", "i": i, "s": s}

def _draw_vline(ax, c, y_max, drawn):
    x = c.get("x", 5)
    name = c.get("id", "")
    color = COLORS.get(c.get("color", "lras"), "#333")
    style = c.get("style", "-")
    label = c.get("label", "")
    ax.axvline(x=x, color=color, linewidth=2, linestyle=style, zorder=2)
    if label:
        ax.annotate(label, xy=(x, y_max * 0.85), fontsize=10, color=color,
                    fontweight='bold', xytext=(5, 0), textcoords='offset points')
    drawn[name] = {"type": "vertical", "x": x}

def _draw_hline(ax, c, x_max, drawn):
    y = c.get("y", 3)
    name = c.get("id", "")
    color = COLORS.get(c.get("color", "price_ctrl"), "#333")
    style = c.get("style", "--")
    label = c.get("label", "")
    ax.axhline(y=y, color=color, linewidth=1.5, linestyle=style, zorder=2)
    if label:
        ax.annotate(label, xy=(x_max * 0.95, y), fontsize=10, color=color,
                    xytext=(5, 3), textcoords='offset points')
    drawn[name] = {"type": "horizontal", "y": y}

def _draw_eq_point(ax, xy, eq):
    x, y = xy
    # Projection lines to axes — Cambridge standard: dashed from equilibrium
    ax.plot([x, x], [0, y], '--', color='#666', linewidth=1.0, alpha=0.5, zorder=1)
    ax.plot([0, x], [y, y], '--', color='#666', linewidth=1.0, alpha=0.5, zorder=1)
    # Equilibrium dot
    ax.plot(x, y, 'o', color=COLORS["eq"], markersize=10, zorder=5,
            markeredgecolor='white', markeredgewidth=2)
    label = eq.get("label", "")
    if label:
        offset = eq.get("offset", (12, 12))
        ax.annotate(label, xy=(x, y), fontsize=14, fontweight='bold',
                    xytext=offset, textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.25', facecolor='white',
                             edgecolor='#999', linewidth=0.5, alpha=0.9))

def _draw_shading(ax, sh, drawn, x_max):
    stype = sh.get("type", "between")
    c1_id = sh.get("c1", "")
    c2_id = sh.get("c2", "")
    if not (c1_id in drawn and c2_id in drawn):
        return
    d1, d2 = drawn[c1_id], drawn[c2_id]
    if d1["type"] != "line" or d2["type"] != "line":
        return

    x1 = sh.get("x1", 0)
    x2 = sh.get("x2", x_max)
    xs = np.linspace(x1, x2, 100)
    y1 = d1["i"] + d1["s"] * xs
    y2 = d2["i"] + d2["s"] * xs
    color = COLORS.get(sh.get("color", "dwl"), "#F1948A")
    alpha = sh.get("alpha", 0.25)
    ax.fill_between(xs, y1, y2, color=color, alpha=alpha, zorder=1)

    label = sh.get("label", "")
    lx, ly = sh.get("label_pos", (0, 0))
    if label and lx and ly:
        ax.annotate(label, xy=(lx, ly), fontsize=9, color=color, alpha=0.8,
                    ha='center', va='center')
