from datetime import datetime


def validate_date(date_str):
    """验证日期格式是否为 YYYY-MM-DD"""
    if not date_str:
        return True
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False
