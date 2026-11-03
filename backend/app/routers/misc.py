import io
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from PIL import Image
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from ..database import get_db, DATA_DIR
from ..models import Quotation, Customer
from ..services import quotation_service as qs
from ..services.settings_service import get_setting, set_setting, DEFAULTS

router = APIRouter(prefix="/api")


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    qs.expire_overdue(db)
    count = lambda *c: db.scalar(select(func.count(Quotation.id)).where(*c)) or 0
    total = lambda *c: float(db.scalar(select(func.coalesce(func.sum(Quotation.total), 0)).where(*c)) or 0)
    gen = get_setting(db, "general")
    return {
        "currency": gen["currency"],
        "total_quotations": count(),
        "pending_quotations": count(Quotation.status.in_(["Sent", "Pending"])),
        "approved_quotations": count(Quotation.status == "Approved"),
        "total_value": total(),
        "approved_value": total(Quotation.status == "Approved"),
        "recent_customers": [{"id": c.id, "name": c.name, "company": c.company} for c in db.scalars(select(Customer).order_by(Customer.id.desc()).limit(5))],
        "recent_quotations": [qs.serialize(q, full=False) for q in db.scalars(select(Quotation).order_by(Quotation.id.desc()).limit(6))],
    }


@router.get("/settings")
def all_settings(db: Session = Depends(get_db)):
    return {k: get_setting(db, k) for k in DEFAULTS}


class SettingIn(BaseModel):
    value: dict


@router.put("/settings/{key}")
def put_setting(key: str, d: SettingIn, db: Session = Depends(get_db)):
    if key not in DEFAULTS:
        raise HTTPException(404, "Unknown settings group")
    v = d.value
    if key == "general":
        if v.get("aluminium_charge_mode", "consumed") not in ("consumed", "bars"):
            raise HTTPException(422, "aluminium_charge_mode must be 'consumed' or 'bars'")
        if v.get("board_charge_mode", "sheets") not in ("sheets", "area"):
            raise HTTPException(422, "board_charge_mode must be 'sheets' or 'area'")
        if float(v.get("kerf_mm", 3)) < 0:
            raise HTTPException(422, "Kerf cannot be negative")
    return set_setting(db, key, v)


@router.post("/settings/logo")
async def upload_logo(file: UploadFile = File(...), db: Session = Depends(get_db)):
    raw = await file.read()
    if len(raw) > 4_000_000:
        raise HTTPException(413, "Logo must be smaller than 4 MB")
    try:
        img = Image.open(io.BytesIO(raw))
        img.thumbnail((600, 600))
        img = img.convert("RGBA")
    except Exception:
        raise HTTPException(422, "That file is not a valid image (use PNG or JPG)")
    img.save(DATA_DIR / "logo.png")
    set_setting(db, "company", {**get_setting(db, "company"), "logo": "logo.png"})
    return {"logo": "logo.png"}


@router.get("/logo")
def logo():
    from fastapi.responses import FileResponse
    p = DATA_DIR / "logo.png"
    if not p.exists():
        raise HTTPException(404, "No logo")
    return FileResponse(p)
