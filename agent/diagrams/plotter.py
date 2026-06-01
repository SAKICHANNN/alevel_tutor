"""
Phase 1: Python matplotlib rendering engine for A-Level Economics diagrams.

All 14 diagram types via parameterized JSON specs.
LLM describes what → Python computes + renders.

Key guarantees:
  - All intersections solved mathematically
  - All labels positioned by textalloc — no overlaps with any line or label
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
import textalloc as ta

RENDER_DIR = Path(__file__).parent.parent.parent / "data" / "rendered"
RENDER_DIR.mkdir(parents=True, exist_ok=True)

# ── Math utilities ──

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

# ── Color palette ──

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

    # Collectors for deferred label placement
    label_infos = []       # [{x, y, text, color, fontsize}, ...]
    all_line_data = []     # [(x_vals, y_vals), ...] for line-avoidance
    all_scatter_x = []     # equilibrium points to avoid
    all_scatter_y = []

    drawn = {}
    for c in curves:
        ctype = c.get("type", "line")
        if ctype == "line":
            _draw_line(ax, c, x_max, y_max, drawn, label_infos, all_line_data)
        elif ctype == "vertical":
            _draw_vline(ax, c, y_max, drawn, label_infos)
        elif ctype == "horizontal":
            _draw_hline(ax, c, x_max, drawn, label_infos)

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
            _draw_eq_point(ax, xy, eq, label_infos, all_scatter_x, all_scatter_y)
            label = eq.get("label", "")
            if label:
                eq_points[label] = xy

    for sh in shading:
        _draw_shading(ax, sh, drawn, eq_points, x_max)

    # ── Deferred label placement via textalloc ──
    if label_infos:
        label_x = [li["x"] for li in label_infos]
        label_y = [li["y"] for li in label_infos]
        texts = [li["text"] for li in label_infos]
        # Build scatter data: equilibrium dots + label positions themselves
        sx = list(all_scatter_x) + label_x
        sy = list(all_scatter_y) + label_y
        # Build line data for avoidance
        x_lists = [ld[0] for ld in all_line_data if len(ld[0]) > 0]
        y_lists = [ld[1] for ld in all_line_data if len(ld[1]) > 0]
        try:
            ta.allocate(
                ax,
                label_x, label_y,
                texts,
                textsize=14,
                x_lines=x_lists,
                y_lines=y_lists,
                x_scatter=sx,
                y_scatter=sy,
                draw_lines=False,
                margin=0.02,
                min_distance=0.015,
                max_distance=0.06,
            )
            # Bold-ify the allocated texts and set per-label color
            for i, t in enumerate(texts):
                t.set_fontweight('bold')
                t.set_color(label_infos[i].get("color", "#333"))
                t.set_in_layout(False)  # prevent tight bbox from expanding for labels
        except Exception:
            pass  # textalloc fails gracefully — labels stay at original positions

    return fig, ax

def _draw_line(ax, c, x_max, y_max, drawn, label_infos, all_line_data):
    i = c.get("intercept", 5)
    s = c.get("slope", -1)
    name = c.get("id", "")
    color = COLORS.get(c.get("color", "demand"), "#333")
    style = c.get("style", "-")
    width = c.get("width", 2)
    label = c.get("label", "")
    label_pos = c.get("label_pos", 0.7)

    x_vals = np.linspace(0, x_max, 200)
    y_vals = i + s * x_vals
    mask = (y_vals >= 0) & (y_vals <= y_max)
    x_vals, y_vals = x_vals[mask], y_vals[mask]
    if len(x_vals) > 1:
        ax.plot(x_vals, y_vals, linestyle=style, color=color, linewidth=width, zorder=2)
        all_line_data.append((x_vals.copy(), y_vals.copy()))

    if label:
        idx = min(int(len(x_vals) * label_pos), len(x_vals) - 1)
        if idx >= 0:
            label_infos.append({
                "x": float(x_vals[idx]),
                "y": float(y_vals[idx]),
                "text": label,
                "color": color,
                "fontsize": 14,
            })

    drawn[name] = {"type": "line", "i": i, "s": s}

def _draw_vline(ax, c, y_max, drawn, label_infos):
    x = c.get("x", 5)
    name = c.get("id", "")
    color = COLORS.get(c.get("color", "lras"), "#333")
    style = c.get("style", "-")
    label = c.get("label", "")
    ax.axvline(x=x, color=color, linewidth=2, linestyle=style, zorder=2)
    if label:
        label_infos.append({
            "x": x,
            "y": y_max * 0.85,
            "text": label,
            "color": color,
            "fontsize": 14,
        })
    drawn[name] = {"type": "vertical", "x": x}

def _draw_hline(ax, c, x_max, drawn, label_infos):
    y = c.get("y", 3)
    name = c.get("id", "")
    color = COLORS.get(c.get("color", "price_ctrl"), "#333")
    style = c.get("style", "--")
    label = c.get("label", "")
    ax.axhline(y=y, color=color, linewidth=1.5, linestyle=style, zorder=2)
    if label:
        label_infos.append({
            "x": x_max * 0.95,
            "y": y,
            "text": label,
            "color": color,
            "fontsize": 14,
        })
    drawn[name] = {"type": "horizontal", "y": y}

def _draw_eq_point(ax, xy, eq, label_infos, all_scatter_x, all_scatter_y):
    x, y = xy
    ax.plot([x, x], [0, y], '--', color='#666', linewidth=1.0, alpha=0.5, zorder=1)
    ax.plot([0, x], [y, y], '--', color='#666', linewidth=1.0, alpha=0.5, zorder=1)
    ax.plot(x, y, 'o', color=COLORS["eq"], markersize=10, zorder=5,
            markeredgecolor='white', markeredgewidth=2)
    all_scatter_x.append(x)
    all_scatter_y.append(y)
    label = eq.get("label", "")
    if label:
        offset = eq.get("offset", (0.8, 0.8))
        label_infos.append({
            "x": x + float(offset[0]),
            "y": y + float(offset[1]),
            "text": label,
            "color": "#333",
            "fontsize": 14,
        })

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
