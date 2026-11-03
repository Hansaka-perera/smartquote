from sqlalchemy.orm import Session
from ..models import Setting

DEFAULTS = {
    "company": {"name": "Your Company (Pvt) Ltd", "address": "No. 1, Main Street, Colombo", "phone": "+94 11 000 0000",
                "email": "info@example.com", "logo": None},
    "general": {"currency": "LKR", "tax_percent": 0.0, "tax_label": "VAT", "quote_prefix": "QT",
                "validity_days": 30, "kerf_mm": 3.0, "aluminium_charge_mode": "consumed",
                "board_charge_mode": "sheets", "allow_rotation": True,
                "terms": "1. Prices are valid until the expiry date shown.\n2. 50% advance payment with order; balance on delivery/installation.\n"
                         "3. Delivery time to be confirmed on order.\n4. Variations to the agreed design may change the price.\n"
                         "5. Glass breakage after handover is not covered."},
    "cost_aluminium": {"labour_per_sqm": 3500, "labour_fixed": 0, "transport": 0, "installation": 0, "other": 0,
                       "overhead_pct": 8, "profit_mode": "percent", "profit_value": 25},
    "cost_board": {"labour_per_sqm": 4500, "labour_fixed": 0, "transport": 0, "installation": 0, "other": 0,
                   "overhead_pct": 8, "profit_mode": "percent", "profit_value": 25},
}


def get_setting(db: Session, key: str) -> dict:
    row = db.get(Setting, key)
    return {**DEFAULTS.get(key, {}), **(row.value if row else {})}


def set_setting(db: Session, key: str, value: dict) -> dict:
    row = db.get(Setting, key)
    merged = {**DEFAULTS.get(key, {}), **value}
    if row:
        row.value = merged
    else:
        db.add(Setting(key=key, value=merged))
    db.commit()
    return merged
