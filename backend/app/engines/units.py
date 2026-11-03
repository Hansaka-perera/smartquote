import re

UNIT_TO_MM = {"mm": 1.0, "cm": 10.0, "m": 1000.0, "in": 25.4, "ft": 304.8}
M2_TO_FT2 = 10.7639104


def to_mm(value: float, unit: str = "mm") -> float:
    if unit not in UNIT_TO_MM:
        raise ValueError(f"Unsupported unit '{unit}'. Use one of {sorted(UNIT_TO_MM)}")
    return float(value) * UNIT_TO_MM[unit]


def from_mm(value_mm: float, unit: str = "mm") -> float:
    return float(value_mm) / UNIT_TO_MM[unit]


def mm2_to_m2(a: float) -> float:
    return a / 1_000_000.0


def parse_length(text: str, default_unit: str = "mm") -> float:
    """Parse '1800', '5ft', '5\'6"', '3 1/2 in' ... into millimetres."""
    t = str(text).strip().lower().replace("”", '"').replace("’", "'")
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*'\s*(?:(\d+(?:\.\d+)?)\s*\"?)?", t)
    if m:
        return float(m.group(1)) * 304.8 + float(m.group(2) or 0) * 25.4
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(?:(\d+)/(\d+))?\s*(mm|cm|m|in|ft|\")?", t)
    if not m:
        raise ValueError(f"Cannot parse length '{text}'")
    val = float(m.group(1))
    if m.group(2):
        val += int(m.group(2)) / int(m.group(3))
    unit = m.group(4) or default_unit
    return to_mm(val, "in" if unit == '"' else unit)
