"""返回下个月的 (年, 月)。"""

from datetime import date


def next_month(today=None):
    today = today or date.today()
    if today.month == 12:
        return today.year + 1, 1
    return today.year, today.month + 1
