import re


def validate_username(username: str) -> tuple[bool, str]:
    if not username:
        return False, "用户名不能为空"

    username = username.strip()

    if len(username) < 3:
        return False, "用户名至少需要3个字符"
    if len(username) > 32:
        return False, "用户名不能超过32个字符"

    if not re.match(r'^[\w\u4e00-\u9fa5]+$', username):
        return False, "用户名只能包含字母、数字、下划线和中文"

    if username[0].isdigit():
        return False, "用户名不能以数字开头"

    return True, ""
