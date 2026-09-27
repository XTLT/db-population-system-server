from datetime import datetime


def calculate_age(id_card: str) -> str:
    """根据身份证号计算年龄"""
    if not id_card or len(id_card) < 14:
        return ""
    try:
        birth_year = int(id_card[6:10])
        birth_month = int(id_card[10:12])
        birth_day = int(id_card[12:14])
        today = datetime.now()
        age = today.year - birth_year
        if (today.month, today.day) < (birth_month, birth_day):
            age -= 1
        return str(age)
    except (ValueError, TypeError):
        return ""
