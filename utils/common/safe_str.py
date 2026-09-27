def safe_str(val) -> str:
    """安全转换为字符串"""
    if val is None:
        return ""
    return str(val)
