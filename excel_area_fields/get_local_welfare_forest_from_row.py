from utils import safe_str


def get_local_welfare_forest_from_row(row):
    val = row.get("地方公益林")
    if val is None:
        val = row.get("地方公益林（亩）", "")
    return safe_str(val)
