from datetime import date


def validate_id_card(id_card: str) -> tuple[bool, str]:
    if not id_card:
        return False, "身份证号不能为空"

    id_card = id_card.strip().upper()

    if len(id_card) != 18:
        return False, "身份证号必须为18位"

    if not id_card[:17].isdigit():
        return False, "身份证号前17位必须为数字"

    last_char = id_card[17]
    if not (last_char.isdigit() or last_char == 'X'):
        return False, "身份证号最后一位必须为数字或X"

    weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    check_codes = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']

    try:
        total = sum(int(id_card[i]) * weights[i] for i in range(17))
        check_char = check_codes[total % 11]
        if id_card[17] != check_char:
            return False, "身份证号校验位错误"
    except Exception:
        return False, "身份证号格式错误"

    try:
        year = int(id_card[6:10])
        month = int(id_card[10:12])
        day = int(id_card[12:14])

        if year < 1900 or year > date.today().year:
            return False, "身份证号出生年份无效"

        if month < 1 or month > 12:
            return False, "身份证号出生月份无效"

        if day < 1 or day > 31:
            return False, "身份证号出生日期无效"

        if month in [4, 6, 9, 11] and day > 30:
            return False, "身份证号出生日期无效"

        if month == 2:
            is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
            max_day = 29 if is_leap else 28
            if day > max_day:
                return False, "身份证号出生日期无效"
    except Exception:
        return False, "身份证号日期格式错误"

    return True, ""
