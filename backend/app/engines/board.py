"""Board / MDF furniture calculation engine (pure functions, no DB)."""
import math
from .safe_eval import evaluate, FormulaError
from .units import to_mm, M2_TO_FT2
from .sheet_optimizer import pack_sheets
from .costing import make_line, add_wastage
from .aluminium import MissingMaterial, _mat

FINISH_CODES = {"paint": "FIN-PAINT", "laminate": "FIN-LAM", "polish": "FIN-POLISH"}
EDGE_CODE = "EDGE-PVC"


def _dim(v, unit, var, what):
    """Numbers are in the design unit; strings are formulas in mm."""
    if v is None or v == "":
        return 0.0
    if isinstance(v, str):
        try:
            return to_mm(float(v), unit)
        except ValueError:
            return evaluate(v, var)
    return to_mm(v, unit)


def calculate(design: dict, materials: dict, quantity: int = 1, kerf_mm: float = 3.0,
              charge_mode: str = "sheets", allow_rotation: bool = True) -> dict:
    """design: {unit, overall:{W,H,D}, thickness_mm, components[], hardware[]}."""
    if quantity < 1:
        raise ValueError("Quantity must be at least 1")
    unit = design.get("unit", "mm")
    ov = design.get("overall") or {}
    var = {"W": to_mm(ov.get("W", 0), unit), "H": to_mm(ov.get("H", 0), unit),
           "D": to_mm(ov.get("D", 0), unit), "t": float(design.get("thickness_mm", 18))}
    for k in ("W", "H", "D"):
        if var[k] < 0:
            raise FormulaError(f"Overall {k} cannot be negative")
    comps_in = design.get("components") or []
    if not comps_in:
        raise ValueError("Add at least one component to calculate")

    rows, by_mat, by_thk = [], {}, {}
    for c in comps_in:
        name = c.get("name") or "Component"
        qty = evaluate(c.get("qty", 1), var)
        if qty <= 0 or abs(qty - round(qty)) > 1e-9:
            raise FormulaError(f"'{name}': quantity must be a positive whole number")
        qty = int(round(qty))
        L, Wd, Ht = (_dim(c.get(k), unit, var, name) for k in ("length", "width", "height"))
        basis = c.get("area_basis", "LW")
        pair = {"LW": (L, Wd), "LH": (L, Ht), "WH": (Wd, Ht)}.get(basis)
        if pair is None:
            raise ValueError(f"'{name}': area_basis must be LW, LH or WH")
        a, b = pair
        if a <= 0 or b <= 0:
            raise FormulaError(f"'{name}': both dimensions of its area basis ({basis}) must be greater than zero")
        code = c.get("material_code")
        if not code:
            raise ValueError(f"'{name}': choose a board material")
        m = _mat(materials, code)
        thk = float(m.get("thickness_mm") or c.get("thickness") or 0)
        area_each = a * b / 1e6
        total_area = area_each * qty
        edge_len = qty * (int(c.get("edges_length", 0)) * a + int(c.get("edges_width", 0)) * b) / 1000
        sides = int(c.get("finish_sides", 1))
        fin = c.get("finish", "none")
        fin_area = total_area * sides if fin != "none" else 0.0
        rows.append({"name": name, "qty": qty, "length_mm": round(a, 1), "width_mm": round(b, 1),
                     "thickness_mm": thk, "material_code": code, "area_basis": basis,
                     "area_each_sqm": round(area_each, 5), "area_total_sqm": round(total_area, 5),
                     "edge_banding_m": round(edge_len, 3), "finish": fin, "finish_area_sqm": round(fin_area, 5),
                     "rotatable": bool(c.get("rotatable", True))})
        d = by_mat.setdefault(code, {"area_sqm": 0.0, "pieces": 0, "name": m["name"]})
        d["area_sqm"] += total_area
        d["pieces"] += qty
        by_thk[str(thk)] = by_thk.get(str(thk), 0.0) + total_area

    total_area = sum(r["area_total_sqm"] for r in rows)
    lines, skip, sheets_out = [], set(), {}

    # sheet usage per board material: theoretical vs practical (cutting layout)
    for code, d in by_mat.items():
        m = _mat(materials, code)
        waste = float(m.get("wastage_pct") or 0)
        sl, sw = m.get("sheet_length_mm"), m.get("sheet_width_mm")
        price = float(m["purchase_price"])
        if m.get("unit") in ("sheet", "sheets") and sl and sw:
            sheet_area = sl * sw / 1e6
            batch_area = d["area_sqm"] * quantity
            exact = batch_area / sheet_area
            theo = math.ceil(batch_area * (1 + waste / 100) / sheet_area - 1e-9)
            pieces = [{"label": r["name"], "l": r["length_mm"], "w": r["width_mm"],
                       "qty": r["qty"] * quantity, "rotatable": r["rotatable"]}
                      for r in rows if r["material_code"] == code]
            plan = pack_sheets(pieces, sl, sw, kerf_mm, allow_rotation)
            sheets_out[code] = {"name": m["name"], "sheet_size_mm": [sl, sw],
                                "area_sqm": round(batch_area, 4),
                                "theoretical_sheets_exact": round(exact, 3),
                                "theoretical_sheets_with_wastage": theo,
                                "practical_sheets": plan["sheets_needed"],
                                "utilisation_pct": plan["utilisation_pct"], "layout": plan}
            if charge_mode == "sheets":
                qty_s = plan["sheets_needed"] / quantity
                skip.add(code)
            else:
                qty_s = exact / quantity
            lines.append(make_line("raw_materials", code, m["name"], qty_s, "sheet", price, waste))
        else:  # priced per m2
            lines.append(make_line("raw_materials", code, m["name"], d["area_sqm"], m.get("unit", "m2"), price, waste))

    # finishing + edge banding (per single unit)
    for kind, code in FINISH_CODES.items():
        area = sum(r["finish_area_sqm"] for r in rows if r["finish"] == kind)
        if area > 0:
            m = _mat(materials, (design.get("finish_codes") or {}).get(kind, code))
            lines.append(make_line("finishing", m["code"], m["name"], area, m.get("unit", "m2"),
                                   float(m["purchase_price"]), m.get("wastage_pct", 0)))
    edge = sum(r["edge_banding_m"] for r in rows)
    if edge > 0:
        m = _mat(materials, design.get("edge_code", EDGE_CODE))
        lines.append(make_line("finishing", m["code"], m["name"], edge, m.get("unit", "m"),
                               float(m["purchase_price"]), m.get("wastage_pct", 0)))

    hw_out = []
    for h in design.get("hardware") or []:
        m = _mat(materials, h["code"])
        q = float(h["qty"])
        hw_out.append({"code": h["code"], "name": m["name"], "qty": q, "unit": m.get("unit", "pcs")})
        lines.append(make_line("accessories", h["code"], m["name"], q, m.get("unit", "pcs"),
                               float(m["purchase_price"]), m.get("wastage_pct", 0)))

    lines = add_wastage(lines, skip_codes=skip)
    footprint = var["W"] * var["H"] / 1e6
    return {
        "kind": "board",
        "dimensions": {"W_mm": var["W"], "H_mm": var["H"], "D_mm": var["D"], "unit": unit},
        "area_sqm": round(footprint, 4),
        "components": rows,
        "total_board_area_sqm": round(total_area, 4),
        "total_board_area_sqft": round(total_area * M2_TO_FT2, 3),
        "area_by_material": {k: {**v, "area_sqm": round(v["area_sqm"], 4)} for k, v in by_mat.items()},
        "area_by_thickness_mm": {k: round(v, 4) for k, v in by_thk.items()},
        "sheets": sheets_out, "hardware": hw_out, "lines": lines,
        "batch_quantity": quantity, "charge_mode": charge_mode,
    }
