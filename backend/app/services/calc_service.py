"""Glue between database (materials, systems, settings) and pure engines."""
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import Material, AluminiumSystem
from ..engines import aluminium, board, costing
from ..engines.units import to_mm
from ..engines.safe_eval import FormulaError
from ..engines.cutting import CuttingError
from .settings_service import get_setting


class CalcError(ValueError):
    pass


def load_materials(db: Session) -> dict:
    out = {}
    for m in db.scalars(select(Material)):
        out[m.code] = {"code": m.code, "name": m.name, "unit": m.unit, "category": m.category.name,
                       "purchase_price": m.purchase_price, "selling_price": m.selling_price,
                       "wastage_pct": m.wastage_pct, "active": m.active, "bar_length_mm": m.bar_length_mm,
                       "cutting_allowance_mm": m.cutting_allowance_mm, "sheet_length_mm": m.sheet_length_mm,
                       "sheet_width_mm": m.sheet_width_mm, "thickness_mm": m.thickness_mm}
    return out


def compute(db: Session, kind: str, params: dict, system_code: str | None, cost_cfg: dict | None,
            quantity: int = 1) -> dict:
    """Return engine output + cost summary + price snapshot for ONE unit."""
    gen = get_setting(db, "general")
    materials = load_materials(db)
    try:
        if kind == "aluminium":
            system = db.scalar(select(AluminiumSystem).where(AluminiumSystem.code == system_code))
            if not system or not system.active:
                raise CalcError(f"Aluminium system '{system_code}' not found or inactive")
            p = dict(params)
            unit = p.get("unit", "mm")
            p["width"], p["height"] = to_mm(p["width"], unit), to_mm(p["height"], unit)
            calc = aluminium.calculate(p, system.config, materials, quantity, float(gen["kerf_mm"]),
                                       gen["aluminium_charge_mode"])
            base = get_setting(db, "cost_aluminium")
        elif kind == "board":
            calc = board.calculate(params, materials, quantity, float(gen["kerf_mm"]),
                                   gen["board_charge_mode"], bool(gen["allow_rotation"]))
            base = get_setting(db, "cost_board")
        else:
            raise CalcError("kind must be 'aluminium' or 'board'")
    except aluminium.MissingMaterial as e:
        raise CalcError(str(e)) from e
    except (FormulaError, CuttingError, KeyError, ValueError, TypeError) as e:
        raise CalcError(str(e) if not isinstance(e, KeyError) else f"Missing input: {e}") from e
    cfg = {**base, **(cost_cfg or {})}
    try:
        summary = costing.summarise(calc["lines"], calc["area_sqm"], cfg)
    except costing.CostingError as e:
        raise CalcError(str(e)) from e
    snapshot = {l["code"]: {"purchase_price": materials[l["code"]]["purchase_price"],
                            "selling_price": materials[l["code"]]["selling_price"],
                            "unit": materials[l["code"]]["unit"]}
                for l in calc["lines"] if l["code"] in materials}
    return {"calc": calc, "summary": summary, "price_snapshot": snapshot, "cost_cfg": cfg}
