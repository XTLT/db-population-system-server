"""按人员年龄字段与身份证统一取年龄。

优先使用库里的 age（兼容历史数据），为空或非法时用身份证第 7-14 位推导。
推不出来返回 None，调用方应跳过，不能把空值当成 0 岁。
"""

from .calculate_age import calculate_age


def person_age(age, id_card) -> int | None:
    text = '' if age is None else str(age).strip()
    if text:
        try:
            value = int(text)
            if 0 <= value <= 150:
                return value
        except (TypeError, ValueError):
            pass

    calculated = calculate_age('' if id_card is None else str(id_card).strip().upper())
    if calculated:
        try:
            value = int(calculated)
            if 0 <= value <= 150:
                return value
        except (TypeError, ValueError):
            pass
    return None
