"""Linear stock (aluminium bar) cutting optimiser - best-fit decreasing."""
from typing import Iterable


class CuttingError(ValueError):
    pass


def optimize_cuts(pieces: Iterable[dict], stock_length: float, kerf: float = 3.0,
                  allowance: float = 0.0) -> dict:
    """pieces: [{label, length, qty}] in mm.

    allowance: extra mm added to every piece (cutting allowance).
    kerf: blade width lost at each cut. A bar holds pieces while
    sum(piece + allowance) + kerf*(n-1) <= stock (the last cut is the bar end).
    """
    if stock_length <= 0:
        raise CuttingError("Stock bar length must be greater than zero")
    if kerf < 0 or allowance < 0:
        raise CuttingError("Kerf and allowance cannot be negative")

    items = []
    for p in pieces:
        qty = int(round(p.get("qty", 1)))
        length = float(p["length"])
        if length <= 0:
            raise CuttingError(f"Piece '{p.get('label', '')}' has non-positive length")
        if length + allowance > stock_length:
            raise CuttingError(
                f"Piece '{p.get('label', '')}' ({length + allowance:.0f} mm incl. allowance) "
                f"is longer than the stock bar ({stock_length:.0f} mm)")
        items += [(length, p.get("label", ""))] * qty

    items.sort(key=lambda x: -x[0])
    bars: list[dict] = []
    cap = stock_length + kerf  # each piece is charged a kerf; the last one is free
    for length, label in items:
        need = length + allowance + kerf
        best = None
        for b in bars:
            rem = cap - b["_used"]
            if rem >= need and (best is None or rem < cap - best["_used"]):
                best = b
        if best is None:
            best = {"cuts": [], "_used": 0.0}
            bars.append(best)
        best["cuts"].append({"label": label, "length": length})
        best["_used"] += need

    net = sum(l for l, _ in items)
    out_bars = []
    for i, b in enumerate(bars, 1):
        net_b = sum(c["length"] for c in b["cuts"])
        out_bars.append({"index": i, "cuts": b["cuts"], "pieces": len(b["cuts"]),
                         "net_cut_mm": round(net_b, 2),
                         "offcut_mm": round(max(0.0, stock_length - b["_used"]), 2),
                         "waste_mm": round(stock_length - net_b, 2)})
    total_stock = stock_length * len(bars)
    return {
        "stock_length": stock_length, "kerf": kerf, "allowance": allowance,
        "bars_needed": len(bars), "total_stock_mm": total_stock,
        "net_cut_mm": round(net, 2),
        "consumed_mm": round(sum(l + allowance + kerf for l, _ in items), 2),
        "waste_mm": round(total_stock - net, 2),
        "waste_pct": round((total_stock - net) / total_stock * 100, 2) if total_stock else 0.0,
        "remaining_offcuts_mm": round(sum(b["offcut_mm"] for b in out_bars), 2),
        "bars": out_bars,
    }
