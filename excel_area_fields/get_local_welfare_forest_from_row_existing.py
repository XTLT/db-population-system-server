from utils import safe_str


def get_local_welfare_forest_from_row_existing(row, person):
    val = row.get("地方公益林")
    if val is None or (isinstance(val, str) and not val.strip()):
        val = row.get("地方公益林（亩）", person.local_welfare_forest_area)
    if val is None:
        return person.local_welfare_forest_area
    s = safe_str(val)
    return person.local_welfare_forest_area if not s.strip() else s
