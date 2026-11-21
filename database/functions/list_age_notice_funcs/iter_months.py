"""按 YYYYMM 整数顺序逐月迭代，闭区间 [start_ym, end_ym]。"""


def iter_months(start_ym, end_ym):
    year, month = divmod(start_ym, 100)
    end_year, end_month = divmod(end_ym, 100)
    while (year, month) <= (end_year, end_month):
        yield year, month
        month += 1
        if month > 12:
            year += 1
            month = 1
