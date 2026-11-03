"""Shelf (guillotine-style) 2D sheet packer for board cutting layouts."""
from .cutting import CuttingError


def pack_sheets(pieces: list[dict], sheet_l: float, sheet_w: float, kerf: float = 3.0,
                allow_rotation: bool = True, trim: float = 0.0) -> dict:
    """pieces: [{label, l, w, qty, rotatable(optional)}] in mm.
    l runs along the sheet length unless the piece is rotated."""
    ul, uw = sheet_l - 2 * trim, sheet_w - 2 * trim
    if ul <= 0 or uw <= 0:
        raise CuttingError("Sheet size must be positive")
    items = []
    for p in pieces:
        for _ in range(int(round(p.get("qty", 1)))):
            items.append({"label": p["label"], "l": float(p["l"]), "w": float(p["w"]),
                          "rot": bool(allow_rotation and p.get("rotatable", True))})
    items.sort(key=lambda p: -max(p["l"], p["w"]))

    sheets: list[dict] = []

    def orients(p):
        o = [(p["l"], p["w"])]
        if p["rot"] and p["l"] != p["w"]:
            o.append((p["w"], p["l"]))
        return sorted(o, key=lambda t: -t[0]) if p["rot"] else o

    def try_place(s, p):
        for sh in s["shelves"]:
            for a, b in orients(p):
                if b <= sh["h"] and sh["x"] + a <= ul:
                    s["pl"].append({"label": p["label"], "x": trim + sh["x"],
                                    "y": trim + sh["y"], "w": a, "h": b})
                    sh["x"] += a + kerf
                    return True
        y = (s["shelves"][-1]["y"] + s["shelves"][-1]["h"] + kerf) if s["shelves"] else 0.0
        for a, b in orients(p):
            if a <= ul and y + b <= uw:
                s["shelves"].append({"y": y, "h": b, "x": a + kerf})
                s["pl"].append({"label": p["label"], "x": trim, "y": trim + y, "w": a, "h": b})
                return True
        return False

    for p in items:
        if not any(a <= ul and b <= uw for a, b in orients(p)):
            raise CuttingError(f"Component '{p['label']}' ({p['l']:.0f} x {p['w']:.0f} mm) "
                               f"does not fit on a {sheet_l:.0f} x {sheet_w:.0f} mm sheet")
        if not any(try_place(s, p) for s in sheets):
            s = {"shelves": [], "pl": []}
            sheets.append(s)
            if not try_place(s, p):
                raise CuttingError(f"Cannot place '{p['label']}'")

    piece_area = sum(p["l"] * p["w"] for p in items)
    sheet_area = sheet_l * sheet_w
    out = []
    for i, s in enumerate(sheets, 1):
        used = sum(q["w"] * q["h"] for q in s["pl"])
        out.append({"index": i, "placements": s["pl"],
                    "utilisation_pct": round(used / sheet_area * 100, 1)})
    return {"sheet_length": sheet_l, "sheet_width": sheet_w, "kerf": kerf,
            "sheets_needed": len(sheets),
            "utilisation_pct": round(piece_area / (sheet_area * len(sheets)) * 100, 1) if sheets else 0.0,
            "sheets": out}
