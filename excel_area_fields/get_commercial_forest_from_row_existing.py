from utils import safe_str


def get_commercial_forest_from_row_existing(row, person):
    val = row.get("非国有天然商品林")
    if val is None or (isinstance(val, str) and not val.strip()):
        val = row.get("非国有天然商品林（亩）", person.commercial_forest_area)
    if val is None:
        return person.commercial_forest_area
    s = safe_str(val)
    return person.commercial_forest_area if not s.strip() else s
