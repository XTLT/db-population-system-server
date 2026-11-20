"""按第 17 位（索引 16）奇偶推算性别；仅对合法 18 位号有效。"""

import re


def gender_from_id(clean_id):
    if len(clean_id) != 18:
        return ""
    ch = clean_id[16]
    if not re.fullmatch(r"[0-9]", ch):
        return ""
    return "男" if int(ch) % 2 == 1 else "女"
