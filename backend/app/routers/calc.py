from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.calc_service import compute, CalcError
from ..engines.cutting import optimize_cuts, CuttingError
from ..engines import furniture_templates

router = APIRouter(prefix="/api/calc")


class CalcIn(BaseModel):
    kind: str
    params: dict
    system_code: str | None = None
    cost: dict | None = None
    quantity: int = Field(1, ge=1, le=10000)


@router.post("/item")
def calc_item(d: CalcIn, db: Session = Depends(get_db)):
    try:
        r = compute(db, d.kind, d.params, d.system_code, d.cost, d.quantity)
    except CalcError as e:
        raise HTTPException(422, str(e))
    return {**r["calc"], "summary": r["summary"]}


class CutIn(BaseModel):
    pieces: list[dict]
    stock_length: float = Field(gt=0)
    kerf: float = Field(3.0, ge=0)
    allowance: float = Field(0.0, ge=0)


@router.post("/cutting")
def calc_cutting(d: CutIn):
    """Stand-alone aluminium bar cutting optimiser."""
    try:
        return optimize_cuts(d.pieces, d.stock_length, d.kerf, d.allowance)
    except (CuttingError, KeyError, ValueError) as e:
        raise HTTPException(422, str(e))


@router.get("/furniture-template/{kind}")
def furniture_template(kind: str, shelves: int = 2, doors: int = 2):
    if kind not in furniture_templates.KINDS:
        raise HTTPException(404, "Unknown furniture type")
    return furniture_templates.generate(kind, {"shelves": shelves, "doors": doors})
