from utils import safe_str


def get_national_welfare_forest_from_row(row):
    val = row.get("国家公益林")
    if val is None:
        val = row.get("国家公益林（亩）", "")
    return safe_str(val)
