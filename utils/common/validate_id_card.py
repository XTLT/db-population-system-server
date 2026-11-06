# -*- coding: utf-8 -*-
"""身份证号校验（三端统一口径的基准实现）。

规则（desktop / mobile 必须与此一致）：
    1. 去掉所有空白（空格、制表符、换行等），字母转大写
    2. 清洗后为空 -> 拒绝
    3. 必须 18 位，前 17 位全数字，末位为数字或 X
    4. 校验位按加权模 11 计算
    5. 出生日期：年份 1900 ~ 今年、月份 1-12、日按大小月与闰年

返回 (ok, msg)。本文件的提示文案是全项目基准。
"""

import re
from datetime import date

_WEIGHTS = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
_CHECK_CODES = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']


def validate_id_card(id_card: str) -> tuple[bool, str]:
    id_card = re.sub(r'\s+', '', id_card or '').upper()

    if not id_card:
        return False, "身份证号不能为空"

    if len(id_card) != 18:
        return False, "身份证号必须为18位"

    # 用 ASCII [0-9] 而不是 str.isdigit()：isdigit() 会把全角数字也算成数字，
    # 而 Dart 端的 \d 只认 ASCII，两边会分叉（2026-11-06 由共享向量发现）。
    if not re.fullmatch(r'[0-9]{17}', id_card[:17]):
        return False, "身份证号前17位必须为数字"

    last_char = id_card[17]
    if not (re.fullmatch(r'[0-9]', last_char) or last_char == 'X'):
        return False, "身份证号最后一位必须为数字或X"

    total = sum(int(id_card[i]) * _WEIGHTS[i] for i in range(17))
    if last_char != _CHECK_CODES[total % 11]:
        return False, "身份证号校验位错误"

    year = int(id_card[6:10])
    month = int(id_card[10:12])
    day = int(id_card[12:14])

    if year < 1900 or year > date.today().year:
        return False, "身份证号出生年份无效"

    if month < 1 or month > 12:
        return False, "身份证号出生月份无效"

    if day < 1 or day > 31:
        return False, "身份证号出生日期无效"

    if month in (4, 6, 9, 11) and day > 30:
        return False, "身份证号出生日期无效"

    if month == 2:
        is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
        if day > (29 if is_leap else 28):
            return False, "身份证号出生日期无效"

    return True, ""
