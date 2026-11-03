import pytest
from fastapi.testclient import TestClient
from app.main import app, init_db
from app import seed

ALU = {"width": 1800, "height": 1200, "unit": "mm", "glass_thickness": 6,
       "panels": [{"type": "sliding", "direction": "left"}, {"type": "sliding", "direction": "right"}]}


@pytest.fixture(scope="module")
def c():
    seed.run()
    with TestClient(app) as cl:
        yield cl


def cupboard(c):
    comps = c.get("/api/calc/furniture-template/cupboard").json()
    return {"unit": "mm", "overall": {"W": 900, "H": 1800, "D": 450}, "thickness_mm": 18,
            "components": comps, "hardware": [{"code": "HNG-CAB", "qty": 4}]}


def test_full_workflow_and_price_snapshot(c):
    # calc: window dimensions drive result
    r = c.post("/api/calc/item", json={"kind": "aluminium", "params": ALU, "system_code": "SLIDING-WIN-2T"}).json()
    assert r["glass"]["area_sqm"] > 0 and r["summary"]["selling_price"] > 0
    r2 = c.post("/api/calc/item", json={"kind": "aluminium", "params": {**ALU, "width": 2400}, "system_code": "SLIDING-WIN-2T"}).json()
    assert r2["summary"]["selling_price"] > r["summary"]["selling_price"]

    q = c.post("/api/quotations", json={"customer_name": "Test Customer", "project_name": "Villa"}).json()
    qid = q["id"]
    c.post(f"/api/quotations/{qid}/items", json={"name": "Living room window", "kind": "aluminium", "params": ALU,
                                                  "system_code": "SLIDING-WIN-2T", "quantity": 2})
    q = c.post(f"/api/quotations/{qid}/items", json={"name": "Cupboard", "kind": "board", "params": cupboard(c), "quantity": 1}).json()
    assert len(q["items"]) == 2 and q["total"] > 0
    before = {i["id"]: (i["unit_price"], i["total_price"]) for i in q["items"]}
    total_before = q["total"]

    # change a price -> existing quotation must not change
    mats = c.get("/api/materials").json()
    glass = next(m for m in mats if m["code"] == "GLASS-6")
    c.put(f"/api/materials/{glass['id']}", json={**glass, "purchase_price": glass["purchase_price"] * 3})
    c.post("/api/materials/prices", json=[{"id": next(m for m in mats if m["code"] == "MDF-18")["id"], "purchase_price": 99999, "selling_price": 99999}])
    q2 = c.get(f"/api/quotations/{qid}").json()
    assert q2["total"] == total_before
    assert {i["id"]: (i["unit_price"], i["total_price"]) for i in q2["items"]} == before
    # new calc uses new prices; explicit reprice changes only that item
    r3 = c.post("/api/calc/item", json={"kind": "aluminium", "params": ALU, "system_code": "SLIDING-WIN-2T"}).json()
    assert r3["summary"]["selling_price"] > r["summary"]["selling_price"]
    # duplicate keeps frozen prices
    dup = c.post(f"/api/quotations/{qid}/duplicate").json()
    assert dup["total"] == total_before and dup["number"] != q2["number"]
    # reprice
    iid = q2["items"][0]["id"]
    q3 = c.post(f"/api/quotations/{qid}/items/{iid}/reprice").json()
    assert q3["total"] > total_before

    # discount/tax/status/versions
    q4 = c.put(f"/api/quotations/{qid}", json={"customer_name": "Test Customer", "discount_mode": "percent", "discount_value": 10, "tax_percent": 8, "status": "Approved"}).json()
    assert q4["discount_amount"] > 0 and q4["tax_amount"] > 0 and q4["status"] == "Approved"
    vs = c.get(f"/api/quotations/{qid}/versions").json()
    assert len(vs) >= 4
    cmp = c.get(f"/api/quotations/{qid}/versions/compare", params={"a": vs[0]["version_no"], "b": vs[-1]["version_no"]}).json()
    assert cmp["fields"] and cmp["items"]

    # exports
    pdf = c.get(f"/api/quotations/{qid}/pdf")
    assert pdf.status_code == 200 and pdf.content[:5] == b"%PDF-" and len(pdf.content) > 5000
    xl = c.get(f"/api/quotations/{qid}/xlsx")
    assert xl.status_code == 200 and xl.content[:2] == b"PK"

    d = c.get("/api/dashboard").json()
    assert d["total_quotations"] >= 2 and d["approved_quotations"] >= 1


def test_validation_errors(c):
    bad = c.post("/api/calc/item", json={"kind": "aluminium", "params": {**ALU, "width": 50}, "system_code": "SLIDING-WIN-2T"})
    assert bad.status_code == 422
    assert c.post("/api/calc/item", json={"kind": "aluminium", "params": ALU, "system_code": "NOPE"}).status_code == 422
    assert c.post("/api/materials", json={"code": "X Y", "name": "n", "category": "Glass", "unit": "m2", "purchase_price": -1, "selling_price": 1}).status_code == 422
    assert c.post("/api/quotations", json={}).status_code == 422
    assert c.get("/api/quotations/99999").status_code == 404


def test_material_crud_and_cutting_endpoint(c):
    m = c.post("/api/materials", json={"code": "TEST-1", "name": "Test", "category": "Hardware", "unit": "pcs", "purchase_price": 1, "selling_price": 2}).json()
    assert c.post("/api/materials", json={"code": "TEST-1", "name": "Dup", "category": "Hardware", "unit": "pcs", "purchase_price": 1, "selling_price": 2}).status_code == 409
    assert len(c.get(f"/api/materials/{m['id']}/prices").json()) == 1
    assert c.delete(f"/api/materials/{m['id']}").status_code == 204
    r = c.post("/api/calc/cutting", json={"pieces": [{"label": "a", "length": 2500, "qty": 5}], "stock_length": 6000, "kerf": 3}).json()
    assert r["bars_needed"] == 3


def test_create_quotation_with_custom_tax_terms_and_discount(c):
    q = c.post("/api/quotations", json={"customer_name": "X", "tax_percent": 8, "terms": "Custom terms", "discount_value": 5}).json()
    assert q["tax_percent"] == 8 and q["terms"] == "Custom terms" and q["discount_value"] == 5
