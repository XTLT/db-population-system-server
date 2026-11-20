"""金额字符串转 float，兼容千分位、全角逗号、货币符号与空值。"""


def to_amount(value):
    """把金额转成 float；无法解析时返回 0.0，不抛异常。"""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return 0.0
    for ch in (",", "，", " ", "\u00a0", "¥", "￥", "元", "人民币"):
        text = text.replace(ch, "")
    try:
        return float(text)
    except (ValueError, TypeError):
        return 0.0
