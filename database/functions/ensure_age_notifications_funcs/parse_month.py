"""把 YYYY-MM 字符串解析成 (年, 月)；空值或格式不对时退回"下个月"。"""

from .next_month import next_month


def parse_month(month):
    if month:
        try:
            year_str, month_str = str(month).split("-")
            year = int(year_str)
            m = int(month_str)
            if 1 <= m <= 12:
                return year, m
        except (ValueError, AttributeError):
            pass
    return next_month()
