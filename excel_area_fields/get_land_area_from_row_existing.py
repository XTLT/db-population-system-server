from utils import safe_str


def get_land_area_from_row_existing(row, person):
    val = row.get("土地面积")
    if val is None or (isinstance(val, str) and not val.strip()):
        return person.land_area
    s = safe_str(val)
    return person.land_area if not s.strip() else s
