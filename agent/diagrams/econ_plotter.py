"""
Unified Economics Diagram Renderer — matplotlib-based, exact math.

Covers ALL Cambridge 9708 A-Level diagram types via parameterized JSON spec.
LLM outputs JSON → Python computes intersections and renders.
All coordinates mathematically exact (not LLM-generated).

Architecture:
  LLM JSON spec → solve_intersections() → plot_economics() → base64 PNG
"""
import base64
import io
import json
import math
from typing import Optional, Tuple, List

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.patches import FancyBboxPatch

# ── Math: Line intersection solver ──

def line_y(x, intercept, slope):
    """y = intercept + slope * x"""
    return intercept + slope * x

def solve_intersection(i1, s1, i2, s2):
    """Solve intercept+slope*x for two lines. Returns (x, y) or None."""
    if abs(s1 - s2) < 1e-9:
        return None
    x = (i2 - i1) / (s1 - s2)
    y = i1 + s1 * x
    return (x, y)

def solve_x_for_y(intercept, slope, y_target):
    """x where line crosses given y. Returns None if slope is 0."""
    if abs(slope) < 1e-9:
        return None
    return (y_target - intercept) / slope

# ── Style ──
STYLE = {
    "figsize": (8.5, 6.5),
    "dpi": 140,
    "d_color": "#2B5B84",
    "s_color": "#C44E52",
    "d2_color": "#4C9BCF",
    "s2_color": "#E88C8F",
    "msc_color": "#E67E22",
    "msb_color": "#27AE60",
    "lras_color": "#2C3E50",
    "tax_color": "#E74C3C",
    "sub_color": "#2ECC71",
    "dwl_color": "#F1948A",
    "cs_color": "#AED6F1",
    "ps_color": "#F5B7B1",
    "rev_color": "#F9E79F",
    "eq_color": "#1a1a1a",
    "grid": False,
    "font_family": "DejaVu Sans",
}

# ── Main render function ──

def render_economics(spec: dict) -> Optional[str]:
    """Render an economics diagram from JSON spec. Returns base64 PNG data URI."""
    try:
        fig, ax = _plot_from_spec(spec)
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=STYLE['dpi'], bbox_inches='tight',
                    facecolor='white', edgecolor='none', pad_inches=0.3)
        plt.close(fig)
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode('ascii')
        return f"data:image/png;base64,{b64}"
    except Exception as e:
        print(f"Econ render error: {e}")
        return None


def _plot_from_spec(spec: dict):
    plt.rcParams['font.family'] = STYLE['font_family']
    fig, ax = plt.subplots(figsize=STYLE['figsize'])

    curves = spec.get("curves", [])
    points = spec.get("points", [])
    areas = spec.get("areas", [])
    labels = spec.get("labels", {})
    axes = spec.get("axes", {"x": "Quantity", "y": "Price"})
    x_max = spec.get("x_max", 10)
    y_max = spec.get("y_max", 10)

    # ── Axes ──
    ax.set_xlim(0, x_max)
    ax.set_ylim(0, y_max)
    ax.set_xlabel(axes.get("x", "Q"), fontsize=13, labelpad=8)
    ax.set_ylabel(axes.get("y", "P"), fontsize=13, labelpad=8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)

    # ── Draw curves ──
    drawn_curves = {}
    for c in curves:
        ctype = c.get("type", "line")
        if ctype == "line":
            _draw_line(ax, c, x_max, drawn_curves)
        elif ctype == "vertical":
            _draw_vertical(ax, c, y_max)
        elif ctype == "horizontal":
            _draw_horizontal(ax, c, x_max)

    # ── Compute and draw intersection points ──
    for pt in points:
        c1_name = pt.get("curve1")
        c2_name = pt.get("curve2")
        if c1_name and c2_name and c1_name in drawn_curves and c2_name in drawn_curves:
            l1 = drawn_curves[c1_name]
            l2 = drawn_curves[c2_name]
            if l1["type"] == "line" and l2["type"] == "line":
                xy = solve_intersection(l1["intercept"], l1["slope"],
                                        l2["intercept"], l2["slope"])
            elif l1["type"] == "vertical" and l2["type"] == "line":
                xy = (l1["x"], line_y(l1["x"], l2["intercept"], l2["slope"]))
            elif l1["type"] == "line" and l2["type"] == "vertical":
                xy = (l2["x"], line_y(l2["x"], l1["intercept"], l1["slope"]))
            elif l1["type"] == "horizontal" and l2["type"] == "line":
                xy = (solve_x_for_y(l2["intercept"], l2["slope"], l1["y"]), l1["y"])
            elif l1["type"] == "line" and l2["type"] == "horizontal":
                xy = (solve_x_for_y(l1["intercept"], l1["slope"], l2["y"]), l2["y"])
            else:
                xy = None

            if xy and 0 <= xy[0] <= x_max and 0 <= xy[1] <= y_max:
                _draw_point(ax, xy, pt)

    # ── Draw shaded areas ──
    for area in areas:
        _draw_area(ax, area, drawn_curves, x_max)

    # ── Custom labels ──
    for lbl in spec.get("annotations", []):
        ax.annotate(lbl.get("text", ""), xy=(lbl["x"], lbl["y"]),
                    fontsize=lbl.get("size", 10), color=lbl.get("color", "#333"),
                    ha=lbl.get("ha", "center"), va=lbl.get("va", "center"))

    return fig, ax


def _draw_line(ax, c, x_max, drawn):
    intercept = c.get("intercept", 5)
    slope = c.get("slope", -1)
    name = c.get("name", "")
    color = c.get("color", STYLE["d_color"])
    style = c.get("style", "-")
    width = c.get("width", 2)
    label = c.get("label", "")
    label_pos = c.get("label_pos", 0.7)

    # Compute visible domain
    x_start = max(0, solve_x_for_y(y_target=0, intercept=intercept, slope=slope) or 0)
    x_end = min(x_max, solve_x_for_y(y_target=x_max * 0 + 10, intercept=intercept, slope=slope) or x_max)
    if slope > 0:
        x_vals = np.linspace(0, min(x_max, max(0.1, (10 - intercept) / slope if slope > 0 else x_max)), 100)
    else:
        y_at_max = max(0, intercept + slope * x_max)
        y_at_0 = intercept
        if y_at_0 < 0 and y_at_max < 0:
            return
        x_vals = np.linspace(0, x_max, 100)
    y_vals = intercept + slope * x_vals

    # Filter to visible range
    mask = (y_vals >= -1) & (y_vals <= 12) & (x_vals >= 0) & (x_vals <= x_max)
    x_vals, y_vals = x_vals[mask], y_vals[mask]
    if len(x_vals) > 1:
        ax.plot(x_vals, y_vals, linestyle=style, color=color, linewidth=width, zorder=2)

    # Label — positioned with offset to avoid curve overlap
    if label:
        idx = min(int(len(x_vals) * label_pos), len(x_vals) - 1)
        if idx >= 0:
            # Use small background box to make label readable
            ax.annotate(label, xy=(x_vals[idx], y_vals[idx]),
                        fontsize=10, color=color, fontweight='bold',
                        xytext=(8, 8), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.1', facecolor='white',
                                 edgecolor='none', alpha=0.85))

    drawn[name] = {"type": "line", "intercept": intercept, "slope": slope, "color": color}
    return drawn


def _draw_vertical(ax, c, y_max):
    x = c.get("x", 5)
    color = c.get("color", STYLE["lras_color"])
    label = c.get("label", "")
    ax.axvline(x=x, color=color, linewidth=2, linestyle=c.get("style", "-"), zorder=2)
    if label:
        ax.annotate(label, xy=(x, y_max * 0.9), fontsize=11, color=color, fontweight='bold',
                    xytext=(5, 0), textcoords='offset points')
    return {"type": "vertical", "x": x}


def _draw_horizontal(ax, c, x_max):
    y = c.get("y", 3)
    color = c.get("color", "#E74C3C")
    label = c.get("label", "")
    style = c.get("style", "--")
    ax.axhline(y=y, color=color, linewidth=1.5, linestyle=style, zorder=2)
    if label:
        ax.annotate(label, xy=(x_max * 0.95, y), fontsize=10, color=color,
                    xytext=(5, 3), textcoords='offset points')
    return {"type": "horizontal", "y": y}


def _draw_point(ax, xy, pt):
    x, y = xy
    # Draw projection lines (Cambridge standard)
    if pt.get("projection", True):
        ax.plot([x, x], [0, y], '--', color='#999', linewidth=0.8, alpha=0.5, zorder=1)
        ax.plot([0, x], [y, y], '--', color='#999', linewidth=0.8, alpha=0.5, zorder=1)
    # Equilibrium dot
    ax.plot(x, y, 'o', color=STYLE["eq_color"], markersize=7, zorder=5, 
            markeredgecolor='white', markeredgewidth=1.5)
    label = pt.get("label", "")
    if label:
        offset = pt.get("offset", (10, 10))
        ax.annotate(label, xy=(x, y), fontsize=11, fontweight='bold',
                    xytext=offset, textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white', 
                             edgecolor='none', alpha=0.8))


def _draw_area(ax, area, curves, x_max):
    area_type = area.get("type", "triangle")
    color = area.get("color", STYLE["dwl_color"])
    label = area.get("label", "")
    alpha = area.get("alpha", 0.25)

    if area_type == "triangle":
        verts = area.get("vertices", [])
        if len(verts) == 3:
            poly = plt.Polygon(verts, color=color, alpha=alpha, zorder=1)
            ax.add_patch(poly)
    elif area_type == "rectangle":
        verts = area.get("vertices", [])
        if len(verts) == 4:
            poly = plt.Polygon(verts, color=color, alpha=alpha, zorder=1)
            ax.add_patch(poly)
    elif area_type == "between":
        c1 = curves.get(area.get("curve1", ""))
        c2 = curves.get(area.get("curve2", ""))
        x1 = area.get("x1", 0)
        x2 = area.get("x2", x_max)
        if c1 and c2 and c1["type"] == "line" and c2["type"] == "line":
            xs = np.linspace(x1, x2, 100)
            y1 = c1["intercept"] + c1["slope"] * xs
            y2 = c2["intercept"] + c2["slope"] * xs
            ax.fill_between(xs, y1, y2, color=color, alpha=alpha, zorder=1)

    if label and area.get("label_pos"):
        lx, ly = area["label_pos"]
        ax.annotate(label, xy=(lx, ly), fontsize=9, color=color, alpha=0.8,
                    ha='center', va='center')
