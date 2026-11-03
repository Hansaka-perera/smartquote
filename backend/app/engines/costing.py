"""Central costing engine. Money maths uses Decimal, results are plain floats.

Keeps three things apart:
  * consumption  - quantity of material the job uses (cost lines: quantity)
  * purchase     - what must be bought (sheets / bars, shown in engine output)
  * selling      - cost + overhead + profit (summary)
"""
from decimal import Decimal, ROUND_HALF_UP

CATEGORIES = ["raw_materials", "accessories", "glass", "finishing", "wastage"]
DEFAULT_COST = {
    "labour_per_sqm": 0.0, "labour_fixed": 0.0, "transport": 0.0, "installation": 0.0,
    "other": 0.0, "overhead_pct": 0.0, "profit_mode": "percent", "profit_value": 0.0,
}


class CostingError(ValueError):
    pass


def D(x) -> Decimal:
    return Decimal(str(x))


def q2(x: Decimal) -> Decimal:
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def make_line(category, code, description, quantity, unit, unit_price, wastage_pct=0.0) -> dict:
    amount = q2(D(quantity) * D(unit_price))
    return {"category": category, "code": code, "description": description,
            "quantity": round(float(quantity), 4), "unit": unit,
            "unit_price": float(unit_price), "wastage_pct": wastage_pct, "amount": float(amount)}


def add_wastage(lines: list[dict], skip_codes: set | None = None) -> list[dict]:
    """Append a 'wastage' line for every material line with wastage_pct > 0."""
    skip_codes = skip_codes or set()
    extra = []
    for l in lines:
        pct = l.get("wastage_pct") or 0
        if pct > 0 and l["code"] not in skip_codes and l["category"] != "wastage":
            extra.append(make_line("wastage", l["code"], f"Wastage {pct:g}% - {l['description']}",
                                   1, "lot", float(q2(D(l["amount"]) * D(pct) / 100))))
    return lines + extra


def summarise(lines: list[dict], area_sqm: float, cfg: dict | None = None) -> dict:
    c = {**DEFAULT_COST, **(cfg or {})}
    for k in ("labour_per_sqm", "labour_fixed", "transport", "installation", "other",
              "overhead_pct", "profit_value"):
        if float(c[k]) < 0:
            raise CostingError(f"'{k}' cannot be negative")
    if c["profit_mode"] not in ("percent", "fixed"):
        raise CostingError("profit_mode must be 'percent' or 'fixed'")

    by_cat = {k: Decimal(0) for k in CATEGORIES}
    for l in lines:
        by_cat[l["category"]] = by_cat.get(l["category"], Decimal(0)) + D(l["amount"])

    materials = sum(by_cat.values(), Decimal(0))
    labour = q2(D(c["labour_per_sqm"]) * D(area_sqm) + D(c["labour_fixed"]))
    transport, install, other = q2(D(c["transport"])), q2(D(c["installation"])), q2(D(c["other"]))
    overhead = q2((materials + labour) * D(c["overhead_pct"]) / 100)
    production = materials + labour + transport + install + other + overhead
    profit = q2(production * D(c["profit_value"]) / 100) if c["profit_mode"] == "percent" \
        else q2(D(c["profit_value"]))
    selling = production + profit
    f = lambda d: float(q2(d))
    return {
        "by_category": {k: f(v) for k, v in by_cat.items()},
        "materials_total": f(materials), "labour": f(labour), "transport": f(transport),
        "installation": f(install), "other": f(other), "overhead": f(overhead),
        "production_cost": f(production), "profit": f(profit), "selling_price": f(selling),
        "config": c,
    }


def quotation_totals(item_totals: list[float], discount_mode="percent", discount_value=0.0,
                     tax_percent=0.0) -> dict:
    sub = sum((D(x) for x in item_totals), Decimal(0))
    if discount_value < 0 or tax_percent < 0:
        raise CostingError("Discount and tax cannot be negative")
    disc = q2(sub * D(discount_value) / 100) if discount_mode == "percent" else q2(D(discount_value))
    if disc > sub:
        raise CostingError("Discount cannot exceed the subtotal")
    taxable = sub - disc
    tax = q2(taxable * D(tax_percent) / 100)
    return {"subtotal": float(q2(sub)), "discount": float(disc), "tax": float(tax),
            "total": float(q2(taxable + tax))}
