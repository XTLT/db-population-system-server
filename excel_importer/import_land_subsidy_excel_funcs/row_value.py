"""按列名取单元格字符串，列名为空时返回空串。"""

from utils import safe_str


def row_value(row, col):
    return safe_str(row.get(col, "")) if col else ""
