from utils import safe_str


def get_national_welfare_forest_from_row_existing(row, person):
    val = row.get("国家公益林")
    if val is None or (isinstance(val, str) and not val.strip()):
        val = row.get("国家公益林（亩）", person.national_welfare_forest_area)
    if val is None:
        return person.national_welfare_forest_area
    s = safe_str(val)
    return person.national_welfare_forest_area if not s.strip() else s
