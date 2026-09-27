import re


def validate_phone(phone: str) -> tuple[bool, str]:
    if not phone:
        return True, ""

    phone = phone.strip()
    cleaned = re.sub(r'[-\s]', '', phone)

    if cleaned.isdigit() and len(cleaned) == 11 and cleaned[0] == '1':
        return True, ""

    if re.match(r'^0\d{2,3}-?\d{7,8}$', phone):
        return True, ""

    if re.match(r'^0\d{2,3}-?\d{7,8}-?\d{1,4}$', phone):
        return True, ""

    return False, "电话号码格式无效，请输入11位手机号或座机号码"
