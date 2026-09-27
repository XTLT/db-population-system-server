from utils import safe_str


def get_land_area_from_row_existing(row, person):
    return safe_str(row.get("土地面积", person.land_area))
