"""身份证出生日期字符串（用于比较长幼），取不到返回空。"""


def birth_key(id_card):
    c = (id_card or '').strip()
    if len(c) == 18:
        return c[6:14]
    if len(c) == 15:
        return '19' + c[6:12]
    return ''
