"""
Phase 1: Python matplotlib rendering engine for A-Level Economics diagrams.

All 14 diagram types via parameterized JSON specs.
LLM describes what → Python computes + renders.

Key guarantees:
  - All intersections solved mathematically
  - Curve labels ON the line (matplotlib-label-lines, white outline cuts through)
  - Each curve label at a different x-position to avoid overlap
  - Equilibrium labels at intersection point with small offset
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
from labellines import labelLines

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

    # Staggered x positions for curve labels to avoid overlap
    label_x_positions = [0.78, 0.30, 0.55, 0.45, 0.65, 0.85, 0.22, 0.70]

    drawn = {}
    line_objects = []  # matplotlib Line2D objects for labellines
    line_labels = []   # labels to apply
    label_xvals = []   # x positions for each label

    for i, c in enumerate(curves):
        ctype = c.get("type", "line")
        label = c.get("label", "")
        color = COLORS.get(c.get("color", "demand"), "#333")
        style = c.get("style", "-")
        width = c.get("width", 2)

        if ctype == "line":
            line, info = _draw_line(ax, c, x_max, y_max, color, style, width)
            drawn[info["name"]] = info
            if label and line:
                line.set_label(label)
                line_objects.append(line)
                line_labels.append(label)
                x_pos = c.get("label_pos", None) or label_x_positions[min(i, len(label_x_positions)-1)]
                label_xvals.append(x_pos * x_max)

        elif ctype == "vertical":
            info = _draw_vline(ax, c, y_max, color, style)
            drawn[info["name"]] = info
            if label:
                line = ax.axvline(x=c.get("x", 5), color=color, linewidth=0, linestyle='None')
                # Use labellines for vertical too — but it needs data points
                # Instead, annotate vertical lines manually
                line.set_label(label)
                line_objects.append(line)
                line_labels.append(label)
                label_xvals.append(c.get("x", 5) * 0.95)

        elif ctype == "horizontal":
            info = _draw_hline(ax, c, x_max, color, style)
            drawn[info["name"]] = info
            if label:
                line = ax.axhline(y=c.get("y", 3), color=color, linewidth=0, linestyle='None')
                line.set_label(label)
                line_objects.append(line)
                line_labels.append(label)
                label_xvals.append(x_max * 0.85)

    # Apply labellines: places each label ON its curve at the specified x position
    if line_objects:
        labelLines(line_objects, xvals=label_xvals, fontsize=14, fontweight='bold',
                   outline_color='white', outline_width=3, zorder=6)

    # Equilibrium points
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


def _draw_line(ax, c, x_max, y_max, color, style, width):
    i = c.get("intercept", 5)
    s = c.get("slope", -1)
    name = c.get("id", "")
    x_vals = np.linspace(0, x_max, 200)
    y_vals = i + s * x_vals
    mask = (y_vals >= 0) & (y_vals <= y_max)
    x_vis, y_vis = x_vals[mask], y_vals[mask]
    line = None
    if len(x_vis) > 1:
        line, = ax.plot(x_vis, y_vis, linestyle=style, color=color, linewidth=width, zorder=2)
    return line, {"type": "line", "i": i, "s": s, "name": name}


def _draw_vline(ax, c, y_max, color, style):
    x = c.get("x", 5)
    name = c.get("id", "")
    ax.axvline(x=x, color=color, linewidth=2, linestyle=style, zorder=2)
    # Manual label — labellines doesn't handle pure vertical lines well
    label = c.get("label", "")
    if label:
        ax.text(x + 0.25, y_max * 0.82, label, fontsize=14, fontweight='bold',
                color=color, zorder=6,
                bbox=dict(boxstyle='round,pad=0.15', facecolor='white', edgecolor='none', alpha=0.85))
    return {"type": "vertical", "x": x, "name": name}


def _draw_hline(ax, c, x_max, color, style):
    y = c.get("y", 3)
    name = c.get("id", "")
    ax.axhline(y=y, color=color, linewidth=1.5, linestyle=style, zorder=2)
    label = c.get("label", "")
    if label:
        ax.text(x_max * 0.88, y + 0.2, label, fontsize=14, fontweight='bold',
                color=color, zorder=6,
                bbox=dict(boxstyle='round,pad=0.1', facecolor='white', edgecolor='none', alpha=0.85))
    return {"type": "horizontal", "y": y, "name": name}


def _draw_eq_point(ax, xy, eq, x_max, y_max):
    x, y = xy
    ax.plot([x, x], [0, y], '--', color='#666', linewidth=1.0, alpha=0.5, zorder=1)
    ax.plot([0, x], [y, y], '--', color='#666', linewidth=1.0, alpha=0.5, zorder=1)
    ax.plot(x, y, 'o', color=COLORS["eq"], markersize=10, zorder=5,
            markeredgecolor='white', markeredgewidth=2)
    label = eq.get("label", "")
    if label:
        ox = eq.get("offset", (0.6, 0.6))
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
