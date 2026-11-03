"""Aluminium window / door calculation engine (pure functions, no DB)."""
from .safe_eval import evaluate, FormulaError
from .cutting import optimize_cuts
from .costing import make_line, add_wastage


class MissingMaterial(ValueError):
    def __init__(self, code):
        super().__init__(f"Material '{code}' is not in the material library. "
                         f"Add it under Materials (or edit the aluminium system).")
        self.code = code


def _mat(materials: dict, code: str) -> dict:
    if code not in materials:
        raise MissingMaterial(code)
    m = materials[code]
    if not m.get("active", True):
        raise ValueError(f"Material '{code}' is inactive. Re-activate it or change the system.")
    return m


def panel_counts(panels: list[dict]) -> dict:
    return {t: sum(1 for p in panels if p.get("type") == t) for t in ("sliding", "fixed", "casement")}


def calculate(params: dict, system: dict, materials: dict, quantity: int = 1,
              kerf_mm: float = 3.0, charge_mode: str = "consumed") -> dict:
    """params (mm): width, height, panels[{type,direction}], transoms, glass_thickness,
    frame_mm, mullion_mm, overrides{}.  charge_mode: 'consumed' | 'bars'."""
    W, H = float(params["width"]), float(params["height"])
    if not (200 <= W <= 12000 and 200 <= H <= 12000):
        raise FormulaError("Width and height must be between 200 mm and 12000 mm")
    if quantity < 1:
        raise ValueError("Quantity must be at least 1")
    panels = params.get("panels") or [{"type": "sliding"}, {"type": "sliding"}]
    if not 1 <= len(panels) <= 8:
        raise ValueError("A design needs between 1 and 8 panels")
    cnt = panel_counts(panels)
    transoms = int(params.get("transoms", 0))
    if not 0 <= transoms <= 5:
        raise ValueError("Transoms must be between 0 and 5")
    thk = int(params.get("glass_thickness", 6))

    var = {k: float(v) for k, v in system["constants"].items()}
    var.update({k: float(v) for k, v in (params.get("overrides") or {}).items()})
    var.update({"W": W, "H": H, "panels": len(panels), **{k: float(v) for k, v in cnt.items()},
                "transoms": transoms, "rows": transoms + 1, "glass_thk": thk,
                "frame": float(params.get("frame_mm", 50)), "mullion": float(params.get("mullion_mm", 40))})

    # 1. cut list
    cuts = []
    for c in system["cuts"]:
        if c.get("when") and not evaluate(c["when"], var):
            continue
        qty = int(round(evaluate(c["qty"], var)))
        if qty <= 0:
            continue
        length = evaluate(c["length"], var)
        if length <= 0:
            raise FormulaError(f"'{c['role']}' computes to {length:.0f} mm - dimensions are too small for this system")
        cuts.append({"role": c["role"], "profile": c["profile"], "qty": qty, "length": round(length, 1)})

    # 2. optimise per profile for the whole batch
    plans, lines, skip = {}, [], set()
    by_profile: dict[str, list] = {}
    for c in cuts:
        by_profile.setdefault(c["profile"], []).append(c)
    for code, items in by_profile.items():
        m = _mat(materials, code)
        bar = float(m.get("bar_length_mm") or 6000)
        allow = float(m.get("cutting_allowance_mm") or 0)
        plan = optimize_cuts([{"label": i["role"], "length": i["length"], "qty": i["qty"] * quantity}
                              for i in items], bar, kerf_mm, allow)
        plans[code] = plan
        price = float(m["purchase_price"])
        if charge_mode == "bars":
            qty_m = plan["bars_needed"] * bar / 1000 / quantity
            skip.add(code)
        else:
            qty_m = plan["consumed_mm"] / 1000 / quantity
        lines.append(make_line("raw_materials", code, m["name"], qty_m, "m", price, m.get("wastage_pct", 0)))

    # 3. glass
    g = system["glass"]
    gw, gh = evaluate(g["w"], var), evaluate(g["h"], var)
    gq = int(round(evaluate(g["qty"], var)))
    if gw <= 0 or gh <= 0:
        raise FormulaError("Glass size computes to zero or less - dimensions are too small")
    glass_area = gw * gh * gq / 1e6
    glass_perimeter = 2 * (gw + gh) * gq
    gcode = system.get("glass_code", "GLASS-{glass_thk}").format(glass_thk=thk)
    gm = _mat(materials, gcode)
    lines.append(make_line("glass", gcode, gm["name"], glass_area, gm.get("unit", "m2"),
                           float(gm["purchase_price"]), gm.get("wastage_pct", 0)))
    var.update({"glass_perimeter": glass_perimeter, "glass_area": glass_area})

    # 4. accessories, gaskets, extras
    acc_out = []
    for a in system["accessories"]:
        qty = evaluate(a["qty"], var)
        if qty <= 0:
            continue
        m = _mat(materials, a["code"])
        if m.get("unit") in ("pcs", "pc", "set", "pair"):
            qty = float(int(-(-qty // 1)))  # whole pieces, rounded up
        acc_out.append({"code": a["code"], "name": m["name"], "qty": round(qty, 3), "unit": m.get("unit", "pcs")})
        lines.append(make_line("accessories", a["code"], m["name"], qty, m.get("unit", "pcs"),
                               float(m["purchase_price"]), m.get("wastage_pct", 0)))
    for e in params.get("extras") or []:
        m = _mat(materials, e["code"])
        lines.append(make_line("accessories", e["code"], m["name"], float(e["qty"]), m.get("unit", "pcs"),
                               float(m["purchase_price"]), m.get("wastage_pct", 0)))

    lines = add_wastage(lines, skip_codes=skip)
    return {
        "kind": "aluminium",
        "dimensions": {"width_mm": W, "height_mm": H, "panels": len(panels), "rows": transoms + 1,
                       "glass_thickness_mm": thk, **cnt},
        "area_sqm": round(W * H / 1e6, 4),
        "cuts": cuts,
        "cutting": plans,
        "glass": {"code": gcode, "width_mm": round(gw, 1), "height_mm": round(gh, 1), "qty": gq,
                  "area_sqm": round(glass_area, 4), "perimeter_mm": round(glass_perimeter, 1)},
        "accessories": acc_out,
        "lines": lines,
        "batch_quantity": quantity,
        "charge_mode": charge_mode,
    }
