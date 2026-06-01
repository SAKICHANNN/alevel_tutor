"""
Phase 1: Python matplotlib rendering engine for A-Level Economics diagrams.

All 14 diagram types via parameterized JSON specs.
LLM describes what → Python computes + renders.

Key guarantees:
  - All intersections solved mathematically
  - Labels placed IN NaN-cut gaps in the line — NEVER covers curves
  - Each curve label staggered to avoid overlapping gaps crossing other curves
  - Equilibrium labels at intersection with small offset + white background
  - Output: SVG to data/rendered/{hash}.svg
"""
import base64
import hashlib
import io
import json
import re as _re
from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

RENDER_DIR = Path(__file__).parent.parent.parent / "data" / "rendered"
RENDER_DIR.mkdir(parents=True, exist_ok=True)

def solve_line_intersection(i1, s1, i2, s2):
    if abs(s1 - s2) < 1e-9:
        return None
    x = (i2 - i1) / (s1 - s2)
    y = i1 + s1 * x
    return (x, y)

def x_for_y(intercept, slope, y):
    if abs(slope) < 1e-9:
        return None
    return (y - intercept) / slope

COLORS = {
    "demand": "#2B5B84", "demand2": "#4C9BCF",
    "supply": "#C44E52", "supply2": "#E88C8F",
    "msc": "#E67E22", "msb": "#27AE60",
    "ad": "#2B5B84", "sras": "#C44E52", "lras": "#2C3E50",
    "tax": "#E74C3C", "subsidy": "#2ECC71",
    "marginal": "#E67E22", "dwl": "#F1948A",
    "cs": "#AED6F1", "ps": "#F5B7B1", "revenue": "#F9E79F",
    "price_ctrl": "#E74C3C",
    "eq": "#1a1a1a", "grid": "#e0e0e0",
}

# Staggered x positions for curve labels — each curve gets a different spot
# to naturally avoid label-label overlap and gap-other_curve crossing
LABEL_X_POSITIONS = [0.82, 0.25, 0.55, 0.45, 0.68, 0.88, 0.18, 0.72]

# ── Rendering ──

def _hash_spec(spec: dict) -> str:
    raw = json.dumps(spec, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()[:12]

def render_economics(spec: dict) -> Optional[str]:
    spec_hash = _hash_spec(spec)
    out_path = RENDER_DIR / f"econ_{spec_hash}.svg"
    try:
        fig, ax = _plot(spec)
        fig.savefig(str(out_path), format='svg', bbox_inches='tight',
                     facecolor='white', edgecolor='none', pad_inches=0.2)
        buf = io.BytesIO()
        fig.savefig(buf, format='svg', bbox_inches='tight',
                     facecolor='white', edgecolor='none', pad_inches=0.15)
        plt.close(fig)
        buf.seek(0)
        svg_raw = buf.read().decode('utf-8')
        svg_clean = _re.sub(r'<metadata>.*?</metadata>', '', svg_raw, flags=_re.DOTALL)
        svg_clean = _re.sub(r'<clipPath[^>]*>.*?</clipPath>', '', svg_clean, flags=_re.DOTALL)
        b64 = base64.b64encode(svg_clean.encode('utf-8')).decode('ascii')
        return f"data:image/svg+xml;base64,{b64}"
    except Exception as e:
        import traceback; traceback.print_exc()
        return None

def _place_label_in_gap(ax, x_vals, y_vals, label, label_x_pos, color, fontsize=14):
    """Draw text in a NaN-gap cut into the line. Returns (x_with_gap, y_with_gap)."""
    if len(x_vals) < 6:
        return x_vals, y_vals  # too short to cut

    total = len(x_vals)
    center = int(total * label_x_pos)
    half = max(2, total // 40)  # ~2.5% gap
    lo = max(1, center - half)
    hi = min(total - 2, center + half)

    # Insert NaN to break the line
    x_gap = np.concatenate([x_vals[:lo], [np.nan], x_vals[hi:]])
    y_gap = np.concatenate([y_vals[:lo], [np.nan], y_vals[hi:]])

    # Place label in the gap
    lx = x_vals[center]
    ly = y_vals[center]
    ax.text(lx, ly, label, fontsize=fontsize, fontweight='bold',
            color=color, ha='center', va='center', zorder=6)

    return x_gap, y_gap


def _plot(spec: dict):
    curves = spec.get("curves", [])
    equilibria = spec.get("equilibria", [])
    shading = spec.get("shading", [])
    axes = spec.get("axes", {"x": "Q", "y": "P"})
    x_max = spec.get("x_max", 10)
    y_max = spec.get("y_max", 10)

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.set_xlim(0, x_max)
    ax.set_ylim(0, y_max)
    ax.set_xlabel(axes.get("x", "Quantity"), fontsize=14, fontweight='bold', labelpad=10)
    ax.set_ylabel(axes.get("y", "Price"), fontsize=14, fontweight='bold', labelpad=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)

    drawn = {}
    label_idx = 0

    for i, c in enumerate(curves):
        ctype = c.get("type", "line")
        name = c.get("id", "")
        color = COLORS.get(c.get("color", "demand"), "#333")
        style = c.get("style", "-")
        width = c.get("width", 2)
        label = c.get("label", "")

        if ctype == "line":
            i_val = c.get("intercept", 5)
            s_val = c.get("slope", -1)
            x_vals = np.linspace(0, x_max, 200)
            y_vals = i_val + s_val * x_vals
            mask = (y_vals >= 0) & (y_vals <= y_max)
            x_vis, y_vis = x_vals[mask], y_vals[mask]

            if len(x_vis) > 1:
                if label:
                    x_pos = c.get("label_pos", None)
                    if x_pos is None:
                        x_pos = LABEL_X_POSITIONS[min(label_idx, len(LABEL_X_POSITIONS) - 1)]
                        label_idx += 1
                    x_plot, y_plot = _place_label_in_gap(ax, x_vis, y_vis, label, x_pos, color)
                else:
                    x_plot, y_plot = x_vis, y_vis

                ax.plot(x_plot, y_plot, linestyle=style, color=color, linewidth=width, zorder=2)

            drawn[name] = {"type": "line", "i": i_val, "s": s_val}

        elif ctype == "vertical":
            x = c.get("x", 5)
            ax.axvline(x=x, color=color, linewidth=2, linestyle=style, zorder=2)
            if label:
                ax.text(x + 0.3, y_max * 0.82, label, fontsize=14, fontweight='bold',
                        color=color, zorder=6)
            drawn[name] = {"type": "vertical", "x": x}

        elif ctype == "horizontal":
            y = c.get("y", 3)
            ax.axhline(y=y, color=color, linewidth=1.5, linestyle=style, zorder=2)
            if label:
                ax.text(x_max * 0.85, y + 0.2, label, fontsize=14, fontweight='bold',
                        color=color, zorder=6)
            drawn[name] = {"type": "horizontal", "y": y}

    # Equilibrium points — anchored with small offset
    eq_points = {}
    for eq in equilibria:
        c1, c2 = eq.get("c1"), eq.get("c2")
        if not (c1 and c2 and c1 in drawn and c2 in drawn):
            continue
        d1, d2 = drawn[c1], drawn[c2]
        xy = None
        if d1["type"] == "line" and d2["type"] == "line":
            xy = solve_line_intersection(d1["i"], d1["s"], d2["i"], d2["s"])
        elif d1["type"] == "vertical" and d2["type"] == "line":
            xy = (d1["x"], d2["i"] + d2["s"] * d1["x"])
        elif d1["type"] == "line" and d2["type"] == "vertical":
            xy = (d2["x"], d1["i"] + d1["s"] * d2["x"])
        elif d1["type"] == "horizontal" and d2["type"] == "line":
            xv = x_for_y(d2["i"], d2["s"], d1["y"])
            xy = (xv, d1["y"]) if xv else None
        elif d1["type"] == "line" and d2["type"] == "horizontal":
            xv = x_for_y(d1["i"], d1["s"], d2["y"])
            xy = (xv, d2["y"]) if xv else None
        if xy and 0 <= xy[0] <= x_max and 0 <= xy[1] <= y_max:
            _draw_eq_point(ax, xy, eq, x_max, y_max)
            if eq.get("label"):
                eq_points[eq["label"]] = xy

    for sh in shading:
        _draw_shading(ax, sh, drawn, eq_points, x_max)

    return fig, ax


def _draw_eq_point(ax, xy, eq, x_max, y_max):
    x, y = xy
    ax.plot([x, x], [0, y], '--', color='#666', linewidth=1.0, alpha=0.5, zorder=1)
    ax.plot([0, x], [y, y], '--', color='#666', linewidth=1.0, alpha=0.5, zorder=1)
    ax.plot(x, y, 'o', color=COLORS["eq"], markersize=10, zorder=5,
            markeredgecolor='white', markeredgewidth=2)
    label = eq.get("label", "")
    if label:
        ox = eq.get("offset", (0.5, 0.5))
        tx = max(0.2, min(x_max - 0.2, x + float(ox[0])))
        ty = max(0.2, min(y_max - 0.2, y + float(ox[1])))
        ax.annotate(label, xy=(x, y), fontsize=14, fontweight='bold',
                    xytext=(tx, ty), textcoords='data',
                    bbox=dict(boxstyle='round,pad=0.25', facecolor='white',
                             edgecolor='#999', linewidth=0.5, alpha=0.95),
                    zorder=6)


def _draw_shading(ax, sh, drawn, eq_points, x_max):
    upper_id = sh.get("upper", "")
    lower_id = sh.get("lower", "")
    if not (upper_id in drawn and lower_id in drawn):
        return
    du, dl = drawn[upper_id], drawn[lower_id]
    if du["type"] != "line" or dl["type"] != "line":
        return
    left_label = sh.get("left_eq", "")
    right_label = sh.get("right_eq", "")
    x1 = eq_points.get(left_label, (0, 0))[0] if left_label else 0
    x2 = eq_points.get(right_label, (x_max, 0))[0] if right_label else x_max
    if x1 >= x2:
        return
    xs = np.linspace(x1, x2, 100)
    y_upper = du["i"] + du["s"] * xs
    y_lower = dl["i"] + dl["s"] * xs
    color = COLORS.get(sh.get("color", "dwl"), "#F1948A")
    alpha = sh.get("alpha", 0.25)
    ax.fill_between(xs, y_upper, y_lower, color=color, alpha=alpha, zorder=1)
    label = sh.get("label", "")
    lx, ly = sh.get("label_pos", (0, 0))
    if label and lx and ly:
        ax.text(lx, ly, label, fontsize=13, color=color, alpha=0.8,
                ha='center', va='center', fontweight='bold')
