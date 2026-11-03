"""Materials, price history, suppliers, customers, aluminium systems."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import (Material, MaterialCategory, Supplier, MaterialPrice, Customer, AluminiumSystem)
from ..engines.safe_eval import evaluate, FormulaError

router = APIRouter(prefix="/api")


# ---------------- materials
class MaterialIn(BaseModel):
    code: str = Field(min_length=1, max_length=40, pattern=r"^[A-Za-z0-9._\-]+$")
    name: str = Field(min_length=1, max_length=160)
    category: str = Field(min_length=1)
    unit: str = Field(min_length=1, max_length=20)
    purchase_price: float = Field(ge=0)
    selling_price: float = Field(ge=0)
    supplier: str | None = None
    wastage_pct: float = Field(0, ge=0, le=100)
    min_stock: float | None = Field(None, ge=0)
    active: bool = True
    profile_type: str | None = None
    bar_length_mm: float | None = Field(None, gt=0)
    cutting_allowance_mm: float | None = Field(None, ge=0)
    weight_per_m: float | None = Field(None, ge=0)
    sheet_length_mm: float | None = Field(None, gt=0)
    sheet_width_mm: float | None = Field(None, gt=0)
    thickness_mm: float | None = Field(None, gt=0)


def mat_out(m: Material) -> dict:
    d = {c: getattr(m, c) for c in ("id", "code", "name", "unit", "purchase_price", "selling_price", "wastage_pct",
                                    "min_stock", "active", "profile_type", "bar_length_mm", "cutting_allowance_mm",
                                    "weight_per_m", "sheet_length_mm", "sheet_width_mm", "thickness_mm", "is_sample")}
    d["category"] = m.category.name
    d["supplier"] = m.supplier.name if m.supplier else None
    d["updated_at"] = m.updated_at.isoformat()
    return d


def _cat(db, name):
    c = db.scalar(select(MaterialCategory).where(MaterialCategory.name == name))
    if not c:
        c = MaterialCategory(name=name)
        db.add(c)
        db.flush()
    return c


def _sup(db, name):
    if not name:
        return None
    s = db.scalar(select(Supplier).where(Supplier.name == name))
    if not s:
        s = Supplier(name=name)
        db.add(s)
        db.flush()
    return s


@router.get("/categories")
def categories(db: Session = Depends(get_db)):
    return [c.name for c in db.scalars(select(MaterialCategory).order_by(MaterialCategory.name))]


@router.get("/suppliers")
def suppliers(db: Session = Depends(get_db)):
    return [s.name for s in db.scalars(select(Supplier).order_by(Supplier.name))]


@router.get("/materials")
def list_materials(category: str | None = None, q: str | None = None, db: Session = Depends(get_db)):
    stmt = select(Material).order_by(Material.code)
    out = [mat_out(m) for m in db.scalars(stmt)]
    if category:
        out = [m for m in out if m["category"] == category]
    if q:
        out = [m for m in out if q.lower() in (m["code"] + m["name"]).lower()]
    return out


def _apply(db, m: Material, d: MaterialIn):
    data = d.model_dump(exclude={"category", "supplier"})
    for k, v in data.items():
        setattr(m, k, v)
    m.category_id = _cat(db, d.category).id
    s = _sup(db, d.supplier)
    m.supplier_id = s.id if s else None


@router.post("/materials", status_code=201)
def create_material(d: MaterialIn, db: Session = Depends(get_db)):
    if db.scalar(select(Material).where(Material.code == d.code)):
        raise HTTPException(409, f"Material code '{d.code}' already exists")
    m = Material()
    _apply(db, m, d)
    db.add(m)
    db.flush()
    db.add(MaterialPrice(material_id=m.id, purchase_price=m.purchase_price, selling_price=m.selling_price, note="Initial price"))
    db.commit()
    db.refresh(m)
    return mat_out(m)


@router.put("/materials/{mid}")
def update_material(mid: int, d: MaterialIn, db: Session = Depends(get_db)):
    m = db.get(Material, mid)
    if not m:
        raise HTTPException(404, "Material not found")
    if d.code != m.code and db.scalar(select(Material).where(Material.code == d.code)):
        raise HTTPException(409, f"Material code '{d.code}' already exists")
    changed = (m.purchase_price, m.selling_price) != (d.purchase_price, d.selling_price)
    _apply(db, m, d)
    if changed:
        db.add(MaterialPrice(material_id=m.id, purchase_price=d.purchase_price, selling_price=d.selling_price, note="Edited"))
    db.commit()
    db.refresh(m)
    return mat_out(m)


@router.delete("/materials/{mid}", status_code=204)
def delete_material(mid: int, db: Session = Depends(get_db)):
    m = db.get(Material, mid)
    if not m:
        raise HTTPException(404, "Material not found")
    db.query(MaterialPrice).filter_by(material_id=mid).delete()
    db.delete(m)
    db.commit()


class PriceUpdate(BaseModel):
    id: int
    purchase_price: float = Field(ge=0)
    selling_price: float = Field(ge=0)


@router.post("/materials/prices")
def bulk_prices(updates: list[PriceUpdate], db: Session = Depends(get_db)):
    n = 0
    for u in updates:
        m = db.get(Material, u.id)
        if m and (m.purchase_price, m.selling_price) != (u.purchase_price, u.selling_price):
            m.purchase_price, m.selling_price = u.purchase_price, u.selling_price
            db.add(MaterialPrice(material_id=m.id, purchase_price=u.purchase_price, selling_price=u.selling_price, note="Price update"))
            n += 1
    db.commit()
    return {"updated": n}


@router.get("/materials/{mid}/prices")
def price_history(mid: int, db: Session = Depends(get_db)):
    rows = db.scalars(select(MaterialPrice).where(MaterialPrice.material_id == mid).order_by(MaterialPrice.effective_at.desc(), MaterialPrice.id.desc()))
    return [{"purchase_price": r.purchase_price, "selling_price": r.selling_price, "effective_at": r.effective_at.isoformat(), "note": r.note} for r in rows]


# ---------------- customers
class CustomerIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    company: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None


def cust_out(c: Customer):
    return {"id": c.id, "name": c.name, "company": c.company, "address": c.address, "phone": c.phone,
            "email": c.email, "created_at": c.created_at.isoformat()}


@router.get("/customers")
def customers(q: str | None = None, db: Session = Depends(get_db)):
    rows = [cust_out(c) for c in db.scalars(select(Customer).order_by(Customer.name))]
    return [r for r in rows if not q or q.lower() in (r["name"] + (r["company"] or "")).lower()]


@router.post("/customers", status_code=201)
def create_customer(d: CustomerIn, db: Session = Depends(get_db)):
    c = Customer(**d.model_dump())
    db.add(c)
    db.commit()
    return cust_out(c)


@router.put("/customers/{cid}")
def update_customer(cid: int, d: CustomerIn, db: Session = Depends(get_db)):
    c = db.get(Customer, cid)
    if not c:
        raise HTTPException(404, "Customer not found")
    for k, v in d.model_dump().items():
        setattr(c, k, v)
    db.commit()
    return cust_out(c)


@router.delete("/customers/{cid}", status_code=204)
def delete_customer(cid: int, db: Session = Depends(get_db)):
    c = db.get(Customer, cid)
    if not c:
        raise HTTPException(404, "Customer not found")
    db.delete(c)  # quotations keep their own copy of the customer details
    db.commit()


# ---------------- aluminium systems (formula configuration)
class SystemIn(BaseModel):
    code: str = Field(min_length=1, max_length=40)
    name: str
    kind: str = "window"
    config: dict
    active: bool = True


def validate_system(cfg: dict):
    for key in ("constants", "cuts", "glass", "accessories"):
        if key not in cfg:
            raise HTTPException(422, f"System config needs '{key}'")
    var = {k: 1000.0 for k in cfg["constants"]}
    var.update({k: 1.0 for k in ("W", "H", "panels", "sliding", "fixed", "casement", "transoms", "rows",
                                 "glass_thk", "frame", "mullion", "glass_perimeter", "glass_area")})
    var.update({"W": 1800.0, "H": 1200.0, "panels": 2.0})
    try:
        for c in cfg["cuts"]:
            evaluate(c["qty"], var), evaluate(c["length"], var)
            if c.get("when"):
                evaluate(c["when"], var)
        for k in ("qty", "w", "h"):
            evaluate(cfg["glass"][k], var)
        for a in cfg["accessories"]:
            evaluate(a["qty"], var)
    except (FormulaError, KeyError) as e:
        raise HTTPException(422, f"Invalid formula: {e}")


@router.get("/systems")
def systems(db: Session = Depends(get_db)):
    return [{"id": s.id, "code": s.code, "name": s.name, "kind": s.kind, "config": s.config, "active": s.active}
            for s in db.scalars(select(AluminiumSystem).order_by(AluminiumSystem.id))]


@router.post("/systems", status_code=201)
def create_system(d: SystemIn, db: Session = Depends(get_db)):
    validate_system(d.config)
    if db.scalar(select(AluminiumSystem).where(AluminiumSystem.code == d.code)):
        raise HTTPException(409, "System code already exists")
    s = AluminiumSystem(**d.model_dump())
    db.add(s)
    db.commit()
    return {"id": s.id}


@router.put("/systems/{sid}")
def update_system(sid: int, d: SystemIn, db: Session = Depends(get_db)):
    s = db.get(AluminiumSystem, sid)
    if not s:
        raise HTTPException(404, "System not found")
    validate_system(d.config)
    for k, v in d.model_dump().items():
        setattr(s, k, v)
    db.commit()
    return {"id": s.id}
