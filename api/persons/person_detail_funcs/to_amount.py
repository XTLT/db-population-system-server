"""把库里的金额字符串转成 float，非法值按 0 处理。"""


def to_amount(value) -> float:
    try:
        return float(str(value or "").replace(",", "").strip())
    except (TypeError, ValueError):
        return 0.0
