"""Starter component lists for common furniture. Dimensions are formulas in the
overall W (width), H (height), D (depth) and t (board thickness), all in mm, so
changing the overall size re-computes every component. Edit freely afterwards."""


def _c(name, qty, length, width, material, basis="LW", height=None, finish="none", edge_l=0, edge_w=0, **kw):
    d = {"name": name, "qty": qty, "length": length, "width": width, "material_code": material,
         "area_basis": basis, "finish": finish, "finish_sides": 1,
         "edges_length": edge_l, "edges_width": edge_w, "rotatable": True}
    if height is not None:
        d["height"] = height
    d.update(kw)
    return d


def carcass(m, back, shelves=2, doors=0, drawers=0, dividers=0, toe=False):
    c = [_c("Top", 1, "W", "D", m, edge_l=1),
         _c("Bottom", 1, "W-2*t", "D", m, edge_l=1),
         _c("Left side", 1, "D", None, m, "LH", height="H-t", edge_l=1),
         _c("Right side", 1, "D", None, m, "LH", height="H-t", edge_l=1)]
    c[2]["width"] = c[3]["width"] = 0
    c.append(_c("Back", 1, "W-4", None, back, "LH", height="H-4"))
    c[-1]["width"] = 0
    if shelves:
        c.append(_c("Shelf", shelves, "W-2*t-2", "D-20", m, edge_l=1))
    if dividers:
        d = _c("Divider", dividers, "D-20", None, m, "LH", height="H-2*t")
        d["width"] = 0
        c.append(d)
    if doors:
        d = _c("Door", doors, f"W/{doors}-3", None, m, "LH", height="H-6", edge_l=2, edge_w=2)
        d["width"] = 0
        c.append(d)
    if drawers:
        c.append(_c("Drawer front", drawers, "W-6", f"(H-2*t)/{drawers}-4", m, edge_l=2, edge_w=2))
        c.append(_c("Drawer side", drawers * 2, "D-60", "120", m))
        c.append(_c("Drawer back/front inner", drawers * 2, "W-2*t-50", "120", m))
        c.append(_c("Drawer bottom", drawers, "W-2*t-40", "D-70", back))
    if toe:
        c.append(_c("Toe kick", 1, "W", "100", m))
    return c


def generate(kind: str, opts: dict | None = None) -> list[dict]:
    o = opts or {}
    m = o.get("material_code", "MDF-18")
    back = o.get("back_material_code", "MDF-6")
    if kind == "cupboard":
        return carcass(m, back, o.get("shelves", 2), o.get("doors", 2))
    if kind == "wardrobe":
        return carcass(m, back, o.get("shelves", 2), o.get("doors", 2), dividers=o.get("dividers", 1))
    if kind == "kitchen_cabinet":
        return carcass(m, back, o.get("shelves", 1), o.get("doors", 2), toe=True)
    if kind == "bookshelf":
        return carcass(m, back, o.get("shelves", 4), 0)
    if kind == "drawer":
        return [_c("Front", 1, "W", "H", m, edge_l=2, edge_w=2),
                _c("Side", 2, "D", "H-20", m), _c("Back", 1, "W-2*t*2", "H-20", m),
                _c("Bottom", 1, "W-2*t*2", "D-t", back)]
    if kind == "table":
        return [_c("Table top", 1, "W", "D", m, edge_l=2, edge_w=2),
                _c("Leg", 4, "H-t", "60", m), _c("Long apron", 2, "W-160", "80", m),
                _c("Short apron", 2, "D-160", "80", m)]
    if kind == "stool":
        return [_c("Seat", 1, "W", "D", m, edge_l=2, edge_w=2),
                _c("Leg", 4, "H-t", "50", m), _c("Rail", 4, "W-100", "50", m)]
    return []


KINDS = ["stool", "table", "drawer", "cupboard", "wardrobe", "kitchen_cabinet", "bookshelf", "custom"]
