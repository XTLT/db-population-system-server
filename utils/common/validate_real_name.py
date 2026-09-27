import re


def validate_real_name(real_name: str) -> tuple[bool, str]:
    if not real_name:
        return True, ""

    real_name = real_name.strip()

    if len(real_name) < 1:
        return False, "姓名不能为空"
    if len(real_name) > 20:
        return False, "姓名不能超过20个字符"

    if not re.match(r'^[\u4e00-\u9fa5a-zA-Z·.]+$', real_name):
        return False, "姓名只能包含中文、字母和圆点"

    return True, ""
