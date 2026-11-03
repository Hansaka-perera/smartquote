"""Shared geometry + ReportLab rendering of product drawings (used in PDFs)."""
from reportlab.graphics.shapes import Drawing, Rect, Line, String, Polygon
from reportlab.lib import colors


def window_geometry(p: dict) -> dict:
    W, H = float(p["width"]), float(p["height"])
    f, m = float(p.get("frame_mm", 50)), float(p.get("mullion_mm", 40))
    panels = p.get("panels") or [{"type": "sliding"}] * 2
    rows = int(p.get("transoms", 0)) + 1
    n = len(panels)
    iw, ih = W - 2 * f, H - 2 * f
    pw = (iw - (n - 1) * m) / n
    ph = (ih - (rows - 1) * m) / rows
    cells = []
    for i, pn in enumerate(panels):
        for r in range(rows):
            cells.append({"x": f + i * (pw + m), "y": f + r * (ph + m), "w": pw, "h": ph,
                          "type": pn.get("type", "fixed"), "direction": pn.get("direction", "left")})
    return {"W": W, "H": H, "frame": f, "cells": cells}


def window_drawing(p: dict, box_w: float, box_h: float) -> Drawing:
    from ..engines.units import to_mm
    unit = p.get("unit", "mm")
    q = {**p, "width": to_mm(p["width"], unit), "height": to_mm(p["height"], unit)}
    g = window_geometry(q)
    pad = 24
    s = min((box_w - 2 * pad) / g["W"], (box_h - 2 * pad) / g["H"])
    d = Drawing(box_w, box_h)
    ox, oy = (box_w - g["W"] * s) / 2, (box_h - g["H"] * s) / 2 + 4
    d.add(Rect(ox, oy, g["W"] * s, g["H"] * s, fillColor=colors.HexColor("#8E99A4"), strokeColor=colors.HexColor("#2B3440"), strokeWidth=1))
    for c in g["cells"]:
        x, y, w, h = ox + c["x"] * s, oy + c["y"] * s, c["w"] * s, c["h"] * s
        d.add(Rect(x, y, w, h, fillColor=colors.HexColor("#D8EAF3"), strokeColor=colors.HexColor("#2B3440"), strokeWidth=0.6))
        if c["type"] == "sliding":
            ax = 1 if c["direction"] == "right" else -1
            cx, cy = x + w / 2, y + h / 2
            d.add(Line(cx - ax * w * .25, cy, cx + ax * w * .25, cy, strokeColor=colors.HexColor("#1D4E6B"), strokeWidth=1))
            d.add(Polygon([cx + ax * w * .25, cy, cx + ax * w * .17, cy + 3, cx + ax * w * .17, cy - 3], fillColor=colors.HexColor("#1D4E6B"), strokeColor=None))
        elif c["type"] == "casement":
            hx = x if c["direction"] == "right" else x + w   # hinge side
            ox2 = x + w if c["direction"] == "right" else x
            for yy in (y, y + h):
                d.add(Line(ox2, y + h / 2, hx, yy, strokeColor=colors.HexColor("#1D4E6B"), strokeWidth=0.6, strokeDashArray=[3, 2]))
        else:
            d.add(String(x + w / 2, y + h / 2 - 3, "FIX", fontSize=6, fillColor=colors.HexColor("#5A6B78"), textAnchor="middle"))
    d.add(String(ox + g["W"] * s / 2, oy - 12, f"{p['width']:g} {unit}", fontSize=8, textAnchor="middle", fillColor=colors.HexColor("#2B3440")))
    d.add(String(ox - 6, oy + g["H"] * s / 2, f"{p['height']:g}", fontSize=8, textAnchor="end", fillColor=colors.HexColor("#2B3440")))
    return d


def board_drawing(p: dict, calc: dict, box_w: float, box_h: float) -> Drawing:
    dm = calc["dimensions"]
    W, H, D = dm["W_mm"] or 1, dm["H_mm"] or 1, dm["D_mm"]
    pad = 24
    s = min((box_w - 2 * pad) / W, (box_h - 2 * pad) / H)
    d = Drawing(box_w, box_h)
    ox, oy = (box_w - W * s) / 2, (box_h - H * s) / 2 + 4
    d.add(Rect(ox, oy, W * s, H * s, fillColor=colors.HexColor("#E7DCCB"), strokeColor=colors.HexColor("#5C4A33"), strokeWidth=1))
    t = float(p.get("thickness_mm", 18)) * s
    d.add(Rect(ox + t, oy + t, W * s - 2 * t, H * s - 2 * t, fillColor=colors.HexColor("#F4EEE4"), strokeColor=colors.HexColor("#5C4A33"), strokeWidth=0.5))
    unit = dm.get("unit", "mm")
    from ..engines.units import from_mm
    d.add(String(ox + W * s / 2, oy - 12, f"W {from_mm(W, unit):g} x D {from_mm(D, unit):g} {unit}", fontSize=8, textAnchor="middle"))
    d.add(String(ox - 6, oy + H * s / 2, f"H {from_mm(H, unit):g}", fontSize=8, textAnchor="end"))
    return d


def item_drawing(item, box_w, box_h) -> Drawing:
    if item.kind == "aluminium":
        return window_drawing(item.params, box_w, box_h)
    return board_drawing(item.params, item.calc, box_w, box_h)
