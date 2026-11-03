from datetime import date, timedelta, datetime
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from ..models import Quotation, QuotationItem, CostBreakdown, CuttingList, QuotationVersion
from ..engines import costing
from .calc_service import compute, CalcError
from .settings_service import get_setting

STATUSES = ["Draft", "Sent", "Pending", "Approved", "Rejected", "Expired"]


def next_number(db: Session) -> str:
    gen = get_setting(db, "general")
    year = date.today().year
    n = (db.scalar(select(func.max(Quotation.id))) or 0) + 1
    while True:
        num = f"{gen['quote_prefix']}-{year}-{n:04d}"
        if not db.scalar(select(Quotation.id).where(Quotation.number == num)):
            return num
        n += 1


def new_quotation(db: Session, data: dict) -> Quotation:
    gen = get_setting(db, "general")
    defaults = {"currency": gen["currency"], "tax_percent": gen["tax_percent"], "terms": gen["terms"]}
    q = Quotation(number=next_number(db), **{**defaults, **data})
    costing.quotation_totals([], q.discount_mode, q.discount_value, q.tax_percent)  # validates
    q.expiry_date = q.expiry_date or (q.quote_date or date.today()) + timedelta(days=int(gen["validity_days"]))
    db.add(q)
    db.flush()
    snapshot_version(db, q, "Created")
    db.commit()
    return q


def _fill_item(db: Session, item: QuotationItem) -> None:
    r = compute(db, item.kind, item.params, item.system_code, item.cost_cfg, item.quantity)
    item.calc, item.price_snapshot, item.cost_cfg = r["calc"], r["price_snapshot"], r["cost_cfg"]
    item.unit_price = r["summary"]["selling_price"]
    item.total_price = float(round(item.unit_price * item.quantity, 2))
    item.calc = {**r["calc"], "summary": r["summary"]}
    item.priced_at = datetime.utcnow()
    item.breakdown.clear()
    item.cutting_lists.clear()
    for l in r["calc"]["lines"]:
        item.breakdown.append(CostBreakdown(category=l["category"], code=l["code"], description=l["description"],
                                            quantity=l["quantity"], unit=l["unit"], unit_price=l["unit_price"],
                                            amount=l["amount"]))
    for code, plan in (r["calc"].get("cutting") or {}).items():
        item.cutting_lists.append(CuttingList(material_code=code, data=plan))
    for code, s in (r["calc"].get("sheets") or {}).items():
        item.cutting_lists.append(CuttingList(material_code=code, data=s["layout"]))


def add_item(db: Session, q: Quotation, name: str, kind: str, params: dict, system_code: str | None,
             quantity: int, cost_cfg: dict | None) -> QuotationItem:
    if quantity < 1:
        raise CalcError("Quantity must be at least 1")
    item = QuotationItem(quotation_id=q.id, position=len(q.items) + 1, name=name, kind=kind, params=params,
                         system_code=system_code, quantity=quantity, cost_cfg=cost_cfg or {}, calc={},
                         price_snapshot={})
    _fill_item(db, item)   # raises CalcError before anything is stored
    q.items.append(item)
    recalc_totals(q)
    snapshot_version(db, q, f"Added item '{name}'")
    db.commit()
    return item


def reprice_item(db: Session, q: Quotation, item: QuotationItem) -> None:
    """Explicit user action: recompute one item with CURRENT material prices."""
    _fill_item(db, item)
    recalc_totals(q)
    snapshot_version(db, q, f"Re-priced '{item.name}' with current material prices")
    db.commit()


def recalc_totals(q: Quotation) -> None:
    t = costing.quotation_totals([i.total_price for i in q.items], q.discount_mode, q.discount_value, q.tax_percent)
    q.subtotal, q.discount_amount, q.tax_amount, q.total = t["subtotal"], t["discount"], t["tax"], t["total"]


def serialize(q: Quotation, full: bool = True) -> dict:
    d = {c: getattr(q, c) for c in ("id", "number", "customer_id", "customer_name", "company", "address", "phone",
                                    "email", "project_name", "delivery_location", "notes", "terms", "status",
                                    "currency", "discount_mode", "discount_value", "tax_percent", "subtotal",
                                    "discount_amount", "tax_amount", "total", "version")}
    d["quote_date"] = q.quote_date.isoformat() if q.quote_date else None
    d["expiry_date"] = q.expiry_date.isoformat() if q.expiry_date else None
    d["created_at"] = q.created_at.isoformat()
    d["item_count"] = len(q.items)
    if full:
        d["items"] = [{"id": i.id, "position": i.position, "name": i.name, "kind": i.kind,
                       "system_code": i.system_code, "quantity": i.quantity, "params": i.params,
                       "cost_cfg": i.cost_cfg, "calc": i.calc, "unit_price": i.unit_price,
                       "total_price": i.total_price, "priced_at": i.priced_at.isoformat()} for i in q.items]
    return d


def snapshot_version(db: Session, q: Quotation, note: str) -> None:
    last = max([v.version_no for v in q.versions], default=0)
    q.version = last + 1
    snap = serialize(q)
    for it in snap["items"]:  # keep versions light: drop the bulky engine output
        it["calc"] = {"summary": it["calc"].get("summary")}
    q.versions.append(QuotationVersion(version_no=q.version, note=note, snapshot=snap))


def expire_overdue(db: Session) -> None:
    rows = db.scalars(select(Quotation).where(Quotation.expiry_date < date.today(),
                                              Quotation.status.in_(["Draft", "Sent", "Pending"])))
    changed = False
    for q in rows:
        q.status = "Expired"
        changed = True
    if changed:
        db.commit()


def duplicate(db: Session, q: Quotation) -> Quotation:
    n = Quotation(number=next_number(db), customer_id=q.customer_id, customer_name=q.customer_name,
                  company=q.company, address=q.address, phone=q.phone, email=q.email,
                  project_name=q.project_name, delivery_location=q.delivery_location, notes=q.notes,
                  terms=q.terms, currency=q.currency, discount_mode=q.discount_mode,
                  discount_value=q.discount_value, tax_percent=q.tax_percent, status="Draft",
                  quote_date=date.today(), expiry_date=date.today() + timedelta(days=30))
    db.add(n)
    db.flush()
    for i in q.items:  # copy frozen calculations: prices are NOT refreshed
        c = QuotationItem(position=i.position, name=i.name, kind=i.kind, system_code=i.system_code,
                          quantity=i.quantity, params=i.params, cost_cfg=i.cost_cfg, calc=i.calc,
                          price_snapshot=i.price_snapshot, unit_price=i.unit_price, total_price=i.total_price,
                          priced_at=i.priced_at)
        for b in i.breakdown:
            c.breakdown.append(CostBreakdown(category=b.category, code=b.code, description=b.description,
                                             quantity=b.quantity, unit=b.unit, unit_price=b.unit_price,
                                             amount=b.amount))
        n.items.append(c)
    recalc_totals(n)
    snapshot_version(db, n, f"Duplicated from {q.number}")
    db.commit()
    return n
