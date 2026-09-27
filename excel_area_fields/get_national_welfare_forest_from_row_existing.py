from utils import safe_str


def get_national_welfare_forest_from_row_existing(row, person):
    val = row.get("国家公益林")
    if val is None:
        val = row.get("国家公益林（亩）", person.national_welfare_forest_area)
    return safe_str(val)
