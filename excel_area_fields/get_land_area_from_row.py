from utils import safe_str


def get_land_area_from_row(row):
    return safe_str(row.get("土地面积", ""))
