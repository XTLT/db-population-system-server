from utils import safe_str


def get_commercial_forest_from_row_existing(row, person):
    val = row.get("非国有天然商品林")
    if val is None:
        val = row.get("非国有天然商品林（亩）", person.commercial_forest_area)
    return safe_str(val)
