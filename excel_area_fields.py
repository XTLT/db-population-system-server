"""面积字段独立模块（land_area + 三类林地）

按最高级别指令"功能模块单独写、最后统一调用"，将土地面积和三类林地的
Excel 导入导出逻辑从 excel_importer.py 中提取为独立函数，由统一入口调用。
后续新增面积类字段在此模块追加同模式函数即可。
"""
from utils import safe_str


def apply_land_area_filter(query, filter_value, Person):
    if filter_value == "不为0":
        return query.filter(Person.land_area != "", Person.land_area.isnot(None))
    elif filter_value == "空白":
        return query.filter(
            (Person.land_area == "") | (Person.land_area.is_(None))
        )
    return query


def apply_local_welfare_forest_filter(query, filter_value, Person):
    if filter_value == "不为0":
        return query.filter(Person.local_welfare_forest_area != "", Person.local_welfare_forest_area.isnot(None))
    elif filter_value == "空白":
        return query.filter(
            (Person.local_welfare_forest_area == "") | (Person.local_welfare_forest_area.is_(None))
        )
    return query


def apply_national_welfare_forest_filter(query, filter_value, Person):
    if filter_value == "不为0":
        return query.filter(Person.national_welfare_forest_area != "", Person.national_welfare_forest_area.isnot(None))
    elif filter_value == "空白":
        return query.filter(
            (Person.national_welfare_forest_area == "") | (Person.national_welfare_forest_area.is_(None))
        )
    return query


def apply_commercial_forest_filter(query, filter_value, Person):
    if filter_value == "不为0":
        return query.filter(Person.commercial_forest_area != "", Person.commercial_forest_area.isnot(None))
    elif filter_value == "空白":
        return query.filter(
            (Person.commercial_forest_area == "") | (Person.commercial_forest_area.is_(None))
        )
    return query


def get_land_area_export_value(person):
    return person.land_area or ""


def get_local_welfare_forest_export_value(person):
    return person.local_welfare_forest_area or ""


def get_national_welfare_forest_export_value(person):
    return person.national_welfare_forest_area or ""


def get_commercial_forest_export_value(person):
    return person.commercial_forest_area or ""


def get_land_area_from_row(row):
    return safe_str(row.get("土地面积", ""))


def get_local_welfare_forest_from_row(row):
    val = row.get("地方公益林")
    if val is None:
        val = row.get("地方公益林（亩）", "")
    return safe_str(val)


def get_national_welfare_forest_from_row(row):
    val = row.get("国家公益林")
    if val is None:
        val = row.get("国家公益林（亩）", "")
    return safe_str(val)


def get_commercial_forest_from_row(row):
    val = row.get("非国有天然商品林")
    if val is None:
        val = row.get("非国有天然商品林（亩）", "")
    return safe_str(val)


def get_land_area_from_row_existing(row, person):
    return safe_str(row.get("土地面积", person.land_area))


def get_local_welfare_forest_from_row_existing(row, person):
    val = row.get("地方公益林")
    if val is None:
        val = row.get("地方公益林（亩）", person.local_welfare_forest_area)
    return safe_str(val)


def get_national_welfare_forest_from_row_existing(row, person):
    val = row.get("国家公益林")
    if val is None:
        val = row.get("国家公益林（亩）", person.national_welfare_forest_area)
    return safe_str(val)


def get_commercial_forest_from_row_existing(row, person):
    val = row.get("非国有天然商品林")
    if val is None:
        val = row.get("非国有天然商品林（亩）", person.commercial_forest_area)
    return safe_str(val)
