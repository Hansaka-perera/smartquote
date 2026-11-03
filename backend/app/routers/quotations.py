from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Quotation, QuotationItem, Customer, Product, ProductDesign, DesignComponent
from ..services import quotation_service as qs
from ..services.calc_service import CalcError
from ..services.pdf_service import build_pdf
from ..services.excel_service import build_xlsx
from ..engines import costing

router = APIRouter(prefix="/api")


class QuotationIn(BaseModel):
    customer_id: int | None = None
    customer_name: str | None = None
    company: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    project_name: str | None = None
    delivery_location: str | None = None
    notes: str | None = None
    terms: str | None = None
    quote_date: date | None = None
    expiry_date: date | None = None
    status: str | None = None
    discount_mode: str = "percent"
    discount_value: float = Field(0, ge=0)
    tax_percent: float | None = Field(None, ge=0, le=100)


def _get(db, qid) -> Quotation:
    q = db.get(Quotation, qid)
    if not q:
        raise HTTPException(404, "Quotation not found")
    return q


def _fill_customer(db, data: dict) -> dict:
    cid = data.get("customer_id")
    if cid:
        c = db.get(Customer, cid)
        if not c:
            raise HTTPException(404, "Customer not found")
        for k in ("company", "address", "phone", "email"):
            data[k] = data.get(k) or getattr(c, k)
        data["customer_name"] = data.get("customer_name") or c.name
    if not data.get("customer_name"):
        raise HTTPException(422, "Customer name is required")
    return data


@router.get("/quotations")
def list_quotations(q: str | None = None, status: str | None = None, customer_id: int | None = None,
                    date_from: date | None = None, date_to: date | None = None, db: Session = Depends(get_db)):
    qs.expire_overdue(db)
    stmt = select(Quotation).order_by(Quotation.id.desc())
    if status:
        stmt = stmt.where(Quotation.status == status)
    if customer_id:
        stmt = stmt.where(Quotation.customer_id == customer_id)
    if date_from:
        stmt = stmt.where(Quotation.quote_date >= date_from)
    if date_to:
        stmt = stmt.where(Quotation.quote_date <= date_to)
    rows = [qs.serialize(x, full=False) for x in db.scalars(stmt)]
    if q:
        ql = q.lower()
        rows = [r for r in rows if ql in " ".join(str(r.get(k) or "") for k in ("number", "customer_name", "company", "project_name")).lower()]
    return rows


@router.post("/quotations", status_code=201)
def create_quotation(d: QuotationIn, db: Session = Depends(get_db)):
    data = _fill_customer(db, d.model_dump(exclude_none=True, exclude={"status"}))
    return qs.serialize(qs.new_quotation(db, data))


@router.get("/quotations/{qid}")
def get_quotation(qid: int, db: Session = Depends(get_db)):
    return qs.serialize(_get(db, qid))


@router.put("/quotations/{qid}")
def update_quotation(qid: int, d: QuotationIn, db: Session = Depends(get_db)):
    q = _get(db, qid)
    data = d.model_dump(exclude_none=True)
    if data.get("status") and data["status"] not in qs.STATUSES:
        raise HTTPException(422, f"Status must be one of {qs.STATUSES}")
    if data.get("discount_mode") not in ("percent", "fixed"):
        raise HTTPException(422, "discount_mode must be percent or fixed")
    for k, v in data.items():
        setattr(q, k, v)
    try:
        qs.recalc_totals(q)
    except costing.CostingError as e:
        raise HTTPException(422, str(e))
    qs.snapshot_version(db, q, "Edited details" + (f" (status {q.status})" if data.get("status") else ""))
    db.commit()
    return qs.serialize(q)


@router.delete("/quotations/{qid}", status_code=204)
def delete_quotation(qid: int, db: Session = Depends(get_db)):
    db.delete(_get(db, qid))
    db.commit()


@router.post("/quotations/{qid}/duplicate", status_code=201)
def duplicate(qid: int, db: Session = Depends(get_db)):
    return qs.serialize(qs.duplicate(db, _get(db, qid)))


class ItemIn(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    kind: str
    params: dict
    system_code: str | None = None
    quantity: int = Field(1, ge=1, le=10000)
    cost: dict | None = None


@router.post("/quotations/{qid}/items", status_code=201)
def add_item(qid: int, d: ItemIn, db: Session = Depends(get_db)):
    q = _get(db, qid)
    try:
        qs.add_item(db, q, d.name, d.kind, d.params, d.system_code, d.quantity, d.cost)
    except (CalcError, costing.CostingError) as e:
        db.rollback()
        raise HTTPException(422, str(e))
    return qs.serialize(q)


@router.delete("/quotations/{qid}/items/{iid}")
def delete_item(qid: int, iid: int, db: Session = Depends(get_db)):
    q = _get(db, qid)
    it = db.get(QuotationItem, iid)
    if not it or it.quotation_id != qid:
        raise HTTPException(404, "Item not found")
    q.items.remove(it)
    for n, i in enumerate(q.items, 1):
        i.position = n
    qs.recalc_totals(q)
    qs.snapshot_version(db, q, f"Removed item '{it.name}'")
    db.commit()
    return qs.serialize(q)


@router.post("/quotations/{qid}/items/{iid}/reprice")
def reprice(qid: int, iid: int, db: Session = Depends(get_db)):
    q = _get(db, qid)
    it = db.get(QuotationItem, iid)
    if not it or it.quotation_id != qid:
        raise HTTPException(404, "Item not found")
    try:
        qs.reprice_item(db, q, it)
    except CalcError as e:
        db.rollback()
        raise HTTPException(422, str(e))
    return qs.serialize(q)


@router.get("/quotations/{qid}/versions")
def versions(qid: int, db: Session = Depends(get_db)):
    q = _get(db, qid)
    return [{"version_no": v.version_no, "note": v.note, "created_at": v.created_at.isoformat(),
             "total": v.snapshot.get("total"), "status": v.snapshot.get("status")} for v in q.versions]


@router.get("/quotations/{qid}/versions/compare")
def compare(qid: int, a: int, b: int, db: Session = Depends(get_db)):
    q = _get(db, qid)
    vs = {v.version_no: v.snapshot for v in q.versions}
    if a not in vs or b not in vs:
        raise HTTPException(404, "Version not found")
    A, B = vs[a], vs[b]
    fields = ["customer_name", "project_name", "status", "discount_value", "tax_percent", "subtotal", "discount_amount", "tax_amount", "total"]
    diff = [{"field": f, "from": A.get(f), "to": B.get(f)} for f in fields if A.get(f) != B.get(f)]
    ia = {i["name"]: i for i in A["items"]}
    ib = {i["name"]: i for i in B["items"]}
    items = []
    for n in sorted(set(ia) | set(ib)):
        x, y = ia.get(n), ib.get(n)
        if not x:
            items.append({"item": n, "change": "added", "to": y["total_price"]})
        elif not y:
            items.append({"item": n, "change": "removed", "from": x["total_price"]})
        elif x["total_price"] != y["total_price"] or x["quantity"] != y["quantity"]:
            items.append({"item": n, "change": "changed", "from": x["total_price"], "to": y["total_price"]})
    return {"a": a, "b": b, "fields": diff, "items": items}


@router.get("/quotations/{qid}/pdf")
def pdf(qid: int, download: bool = False, db: Session = Depends(get_db)):
    q = _get(db, qid)
    disp = "attachment" if download else "inline"
    return Response(build_pdf(db, q), media_type="application/pdf",
                    headers={"Content-Disposition": f'{disp}; filename="{q.number}.pdf"'})


@router.get("/quotations/{qid}/xlsx")
def xlsx(qid: int, db: Session = Depends(get_db)):
    q = _get(db, qid)
    return Response(build_xlsx(q), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f'attachment; filename="{q.number}.xlsx"'})


# ---------------- saved products / designs
class ProductIn(BaseModel):
    name: str = Field(min_length=1)
    kind: str
    description: str | None = None
    params: dict
    system_code: str | None = None
    cost: dict | None = None
    is_template: bool = False


@router.get("/products")
def products(kind: str | None = None, db: Session = Depends(get_db)):
    out = []
    for p in db.scalars(select(Product).order_by(Product.id.desc())):
        if kind and p.kind != kind:
            continue
        d = p.designs[0] if p.designs else None
        out.append({"id": p.id, "name": p.name, "kind": p.kind, "description": p.description,
                    "is_template": bool(d and d.is_template), "system_code": d.system_code if d else None,
                    "params": d.params if d else {}, "cost": d.cost_cfg if d else None,
                    "updated_at": (d.updated_at if d else p.created_at).isoformat()})
    return out


@router.post("/products", status_code=201)
def save_product(d: ProductIn, db: Session = Depends(get_db)):
    p = Product(name=d.name, kind=d.kind, description=d.description)
    des = ProductDesign(name=d.name, system_code=d.system_code, params=d.params, cost_cfg=d.cost, is_template=d.is_template)
    for n, c in enumerate(d.params.get("components", []) if d.kind == "board" else []):
        des.components.append(DesignComponent(position=n, data=c))
    p.designs.append(des)
    db.add(p)
    db.commit()
    return {"id": p.id}


@router.put("/products/{pid}")
def update_product(pid: int, d: ProductIn, db: Session = Depends(get_db)):
    p = db.get(Product, pid)
    if not p:
        raise HTTPException(404, "Product not found")
    p.name, p.description, p.kind = d.name, d.description, d.kind
    des = p.designs[0]
    des.name, des.params, des.system_code, des.cost_cfg, des.is_template = d.name, d.params, d.system_code, d.cost, d.is_template
    des.components.clear()
    for n, c in enumerate(d.params.get("components", []) if d.kind == "board" else []):
        des.components.append(DesignComponent(position=n, data=c))
    db.commit()
    return {"id": p.id}


@router.delete("/products/{pid}", status_code=204)
def delete_product(pid: int, db: Session = Depends(get_db)):
    p = db.get(Product, pid)
    if not p:
        raise HTTPException(404, "Product not found")
    db.delete(p)
    db.commit()
