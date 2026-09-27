from utils import safe_str


def get_local_welfare_forest_from_row_existing(row, person):
    val = row.get("地方公益林")
    if val is None:
        val = row.get("地方公益林（亩）", person.local_welfare_forest_area)
    return safe_str(val)
