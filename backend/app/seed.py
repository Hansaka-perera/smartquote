"""Load SAMPLE materials, prices and a demo customer (for testing only).
Usage:  python -m app.seed          (safe to run repeatedly)"""
from sqlalchemy import select
from .main import init_db
from .database import SessionLocal
from . import models
from .sample_data import MATERIALS


def run():
    init_db()
    with SessionLocal() as db:
        added = 0
        for d in MATERIALS:
            if db.scalar(select(models.Material).where(models.Material.code == d["code"])):
                continue
            d = dict(d)
            cat = db.scalar(select(models.MaterialCategory).where(models.MaterialCategory.name == d.pop("category")))
            sup_name = d.pop("supplier", None)
            sup = None
            if sup_name:
                sup = db.scalar(select(models.Supplier).where(models.Supplier.name == sup_name))
                if not sup:
                    sup = models.Supplier(name=sup_name)
                    db.add(sup)
                    db.flush()
            m = models.Material(category_id=cat.id, supplier_id=sup.id if sup else None, is_sample=True, **d)
            db.add(m)
            db.flush()
            db.add(models.MaterialPrice(material_id=m.id, purchase_price=m.purchase_price,
                                        selling_price=m.selling_price, note="Sample price"))
            added += 1
        if not db.scalar(select(models.Customer)):
            db.add(models.Customer(name="Sample Customer", company="Sample Builders (Pvt) Ltd",
                                   address="12 Galle Road, Mount Lavinia", phone="+94 77 000 0000",
                                   email="customer@example.com"))
        db.commit()
    print(f"Seeded {added} sample materials.")


if __name__ == "__main__":
    run()
