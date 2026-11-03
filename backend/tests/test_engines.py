import pytest
from app.engines import cutting, aluminium, board, costing, units
from app.engines.safe_eval import evaluate, FormulaError
from app.engines.default_systems import DEFAULT_SYSTEMS
from app.engines.furniture_templates import generate
from app.sample_data import MATERIALS


def mats():
    out = {}
    for m in MATERIALS:
        d = dict(m)
        d.setdefault("active", True)
        out[d["code"]] = d
    return out

SYS = {s["code"]: s["config"] for s in DEFAULT_SYSTEMS}


# ---- formulas & units
def test_formula_basic_and_safety():
    assert evaluate("W/2+10", {"W": 100}) == 60
    assert evaluate("(H>1200)*2", {"H": 1300}) == 2
    for bad in ("__import__('os')", "W.real", "open('x')", "[1]"):
        with pytest.raises(FormulaError):
            evaluate(bad, {"W": 1})
    with pytest.raises(FormulaError):
        evaluate("W/0", {"W": 1})

def test_units():
    assert units.to_mm(8, "ft") == pytest.approx(2438.4)
    assert units.to_mm(4, "in") == pytest.approx(101.6)
    assert units.parse_length("5'6\"") == pytest.approx(1676.4)
    assert units.parse_length("3 1/2 in") == pytest.approx(88.9)


# ---- cutting optimiser
def test_cutting_simple_fit():
    r = cutting.optimize_cuts([{"label": "a", "length": 2000, "qty": 3}], 6000, kerf=0, allowance=0)
    assert r["bars_needed"] == 1 and r["waste_mm"] == 0

def test_cutting_kerf_forces_second_bar():
    # 3x2000 only fits in 6000 if the last cut is free: 2 kerfs between pieces
    r = cutting.optimize_cuts([{"label": "a", "length": 2000, "qty": 3}], 6000, kerf=3)
    assert r["bars_needed"] == 2
    r = cutting.optimize_cuts([{"label": "a", "length": 1990, "qty": 3}], 6000, kerf=3)
    assert r["bars_needed"] == 1

def test_cutting_bfd_and_accounting():
    pcs = [{"label": "x", "length": 3500, "qty": 2}, {"label": "y", "length": 2400, "qty": 2}]
    r = cutting.optimize_cuts(pcs, 6000, kerf=3, allowance=0)
    assert r["bars_needed"] == 2
    assert r["net_cut_mm"] == 11800
    assert r["waste_mm"] == pytest.approx(12000 - 11800)
    assert sum(len(b["cuts"]) for b in r["bars"]) == 4

def test_cutting_rejects_oversize():
    with pytest.raises(cutting.CuttingError):
        cutting.optimize_cuts([{"label": "long", "length": 6100, "qty": 1}], 6000)


# ---- aluminium
def test_window_1800x1200_sliding():
    p = {"width": 1800, "height": 1200, "panels": [{"type": "sliding"}, {"type": "sliding"}], "glass_thickness": 6}
    r = aluminium.calculate(p, SYS["SLIDING-WIN-2T"], mats())
    cuts = {c["role"]: c for c in r["cuts"]}
    assert cuts["Frame head"]["length"] == 1800 and cuts["Frame jamb"]["qty"] == 2
    assert cuts["Sash stile"]["qty"] == 4 and cuts["Sash stile"]["length"] == 1125
    assert cuts["Sash rail"]["length"] == (1800 - 70) / 2 + 25
    g = r["glass"]
    assert g["qty"] == 2 and g["width_mm"] == pytest.approx((1800 - 70) / 2 + 25 - 55)
    assert g["area_sqm"] == pytest.approx(g["width_mm"] * g["height_mm"] * 2 / 1e6, rel=1e-3)
    assert {l["category"] for l in r["lines"]} >= {"raw_materials", "glass", "accessories", "wastage"}

def test_dimension_change_changes_result():
    base = {"panels": [{"type": "sliding"}] * 2, "glass_thickness": 6, "height": 1200}
    a = aluminium.calculate({**base, "width": 1800}, SYS["SLIDING-WIN-2T"], mats())
    b = aluminium.calculate({**base, "width": 2400}, SYS["SLIDING-WIN-2T"], mats())
    assert b["glass"]["area_sqm"] > a["glass"]["area_sqm"]
    assert sum(l["amount"] for l in b["lines"]) > sum(l["amount"] for l in a["lines"])

def test_price_change_changes_cost_and_missing_material():
    p = {"width": 1500, "height": 1200, "panels": [{"type": "casement"}, {"type": "fixed"}], "glass_thickness": 5}
    m = mats()
    t1 = sum(l["amount"] for l in aluminium.calculate(p, SYS["CASEMENT-WIN"], m)["lines"])
    m["AL-FR-HEAD"]["purchase_price"] *= 2
    t2 = sum(l["amount"] for l in aluminium.calculate(p, SYS["CASEMENT-WIN"], m)["lines"])
    assert t2 > t1
    del m["GLASS-5"]
    with pytest.raises(aluminium.MissingMaterial):
        aluminium.calculate(p, SYS["CASEMENT-WIN"], m)

def test_batch_quantity_reduces_waste():
    p = {"width": 1800, "height": 1200, "panels": [{"type": "sliding"}] * 2, "glass_thickness": 6}
    one = aluminium.calculate(p, SYS["SLIDING-WIN-2T"], mats(), 1, charge_mode="bars")
    ten = aluminium.calculate(p, SYS["SLIDING-WIN-2T"], mats(), 10, charge_mode="bars")
    c1 = sum(l["amount"] for l in one["lines"] if l["category"] == "raw_materials")
    c10 = sum(l["amount"] for l in ten["lines"] if l["category"] == "raw_materials")
    assert c10 <= c1

def test_doors_calculate():
    for code in ("SLIDING-DOOR", "HINGED-DOOR"):
        p = {"width": 1800 if "SLIDING" in code else 900, "height": 2100,
             "panels": [{"type": "sliding" if "SLIDING" in code else "casement"}] * (2 if "SLIDING" in code else 1),
             "glass_thickness": 8}
        r = aluminium.calculate(p, SYS[code], mats())
        assert r["lines"] and r["glass"]["area_sqm"] > 0

def test_too_small_window_rejected():
    with pytest.raises(FormulaError):
        aluminium.calculate({"width": 150, "height": 1200, "panels": [{"type": "sliding"}], "glass_thickness": 6},
                            SYS["SLIDING-WIN-2T"], mats())


# ---- board
def design(**kw):
    d = {"unit": "mm", "overall": {"W": 900, "H": 1800, "D": 450}, "thickness_mm": 18,
         "components": generate("cupboard", {"shelves": 2, "doors": 2}), "hardware": [{"code": "HNG-CAB", "qty": 4}]}
    d.update(kw)
    return d

def test_board_area_rectangular_formula():
    d = {"unit": "mm", "overall": {"W": 0, "H": 0, "D": 0},
         "components": [{"name": "Panel", "qty": 3, "length": 1000, "width": 500, "material_code": "MDF-18"}]}
    r = board.calculate(d, mats())
    assert r["components"][0]["area_total_sqm"] == pytest.approx(3 * 1.0 * 0.5)
    assert r["area_by_thickness_mm"]["18.0"] == pytest.approx(1.5)

def test_board_feet_inches_conversion():
    d = {"unit": "ft", "overall": {"W": 0, "H": 0, "D": 0},
         "components": [{"name": "Top", "qty": 1, "length": 4, "width": 2, "material_code": "MDF-18"}]}
    r = board.calculate(d, mats())
    assert r["total_board_area_sqft"] == pytest.approx(8.0, rel=1e-3)
    d["unit"] = "in"
    d["components"][0].update(length=48, width=24)
    assert board.calculate(d, mats())["total_board_area_sqft"] == pytest.approx(8.0, rel=1e-3)

def test_side_panel_uses_length_and_height():
    d = {"unit": "mm", "overall": {"W": 0, "H": 0, "D": 0},
         "components": [{"name": "Side", "qty": 2, "length": 450, "width": 18, "height": 1800,
                         "area_basis": "LH", "material_code": "MDF-18"}]}
    assert board.calculate(d, mats())["components"][0]["area_total_sqm"] == pytest.approx(2 * 0.45 * 1.8)

def test_theoretical_vs_practical_sheets_and_cost_modes():
    r = board.calculate(design(), mats())
    s = r["sheets"]["MDF-18"]
    assert s["practical_sheets"] >= s["theoretical_sheets_exact"]
    assert s["practical_sheets"] >= 1 and 0 < s["utilisation_pct"] <= 100
    by_sheet = [l for l in r["lines"] if l["code"] == "MDF-18" and l["category"] == "raw_materials"][0]
    assert by_sheet["quantity"] == s["practical_sheets"]
    r2 = board.calculate(design(), mats(), charge_mode="area")
    by_area = [l for l in r2["lines"] if l["code"] == "MDF-18" and l["category"] == "raw_materials"][0]
    assert by_area["quantity"] == pytest.approx(s["theoretical_sheets_exact"], rel=1e-3)

def test_layout_pieces_do_not_overlap_and_fit():
    r = board.calculate(design(), mats())
    for sh in r["sheets"]["MDF-18"]["layout"]["sheets"]:
        pl = sh["placements"]
        for p in pl:
            assert p["x"] + p["w"] <= 2440 + 1e-6 and p["y"] + p["h"] <= 1220 + 1e-6
        for i, a in enumerate(pl):
            for b in pl[i + 1:]:
                assert a["x"] + a["w"] <= b["x"] + 1e-6 or b["x"] + b["w"] <= a["x"] + 1e-6 \
                    or a["y"] + a["h"] <= b["y"] + 1e-6 or b["y"] + b["h"] <= a["y"] + 1e-6

def test_oversize_component_error_and_finishing_lines():
    d = {"unit": "mm", "overall": {"W": 0, "H": 0, "D": 0},
         "components": [{"name": "Huge", "qty": 1, "length": 3000, "width": 1500, "material_code": "MDF-18"}]}
    with pytest.raises(cutting.CuttingError):
        board.calculate(d, mats())
    d = design()
    d["components"][0].update(finish="paint", finish_sides=2)
    r = board.calculate(d, mats())
    assert any(l["category"] == "finishing" and l["code"] == "FIN-PAINT" for l in r["lines"])
    assert any(l["code"] == "EDGE-PVC" for l in r["lines"])

def test_formula_components_follow_overall_size():
    small = board.calculate(design(overall={"W": 600, "H": 1200, "D": 400}), mats())
    big = board.calculate(design(overall={"W": 1200, "H": 2100, "D": 600}), mats())
    assert big["total_board_area_sqm"] > small["total_board_area_sqm"]


# ---- costing
def test_costing_summary_and_modes():
    lines = [costing.make_line("raw_materials", "A", "a", 2, "m", 100.0),
             costing.make_line("glass", "G", "g", 1.5, "m2", 1000.0)]
    s = costing.summarise(lines, 2.0, {"labour_per_sqm": 500, "labour_fixed": 100, "transport": 50,
                                       "overhead_pct": 10, "profit_mode": "percent", "profit_value": 20})
    assert s["materials_total"] == 1700
    assert s["labour"] == 1100
    assert s["overhead"] == pytest.approx(280)
    assert s["production_cost"] == pytest.approx(1700 + 1100 + 50 + 280)
    assert s["selling_price"] == pytest.approx(s["production_cost"] * 1.2)
    f = costing.summarise(lines, 2.0, {"profit_mode": "fixed", "profit_value": 999})
    assert f["profit"] == 999
    with pytest.raises(costing.CostingError):
        costing.summarise(lines, 1, {"profit_mode": "bogus"})

def test_quotation_totals():
    t = costing.quotation_totals([1000, 500.55], "percent", 10, 8)
    assert t == {"subtotal": 1500.55, "discount": 150.06, "tax": pytest.approx(108.04, abs=0.01), "total": pytest.approx(1458.53, abs=0.02)}
    assert costing.quotation_totals([100], "fixed", 30, 0)["total"] == 70
    with pytest.raises(costing.CostingError):
        costing.quotation_totals([100], "fixed", 300, 0)
