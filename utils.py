from datetime import date, datetime
import os
import re
import uuid

from config import PHOTO_EXTENSIONS


def escape_like(value: str) -> str:
    if not value:
        return value
    value = value.replace('\\', '\\\\')
    value = value.replace('%', '\\%')
    value = value.replace('_', '\\_')
    return value


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


def calculate_age(id_card: str) -> str:
    id_card = id_card.strip()
    if len(id_card) != 18:
        return ""
    if not id_card[:17].isdigit():
        return ""
    last = id_card[17].upper()
    if not (last.isdigit() or last == "X"):
        return ""
    try:
        year = int(id_card[6:10])
        month = int(id_card[10:12])
        day = int(id_card[12:14])
        birth = date(year, month, day)
        today = date.today()
        age = today.year - birth.year
        if (today.month, today.day) < (birth.month, birth.day):
            age -= 1
        return str(age)
    except (ValueError, IndexError):
        return ""


def clean_filename(name: str, max_length: int = 100) -> str:
    if not name:
        return ""
    
    safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    safe_name = re.sub(r'_+', '_', safe_name)
    safe_name = safe_name.strip('_')
    
    if len(safe_name) > max_length:
        safe_name = safe_name[:max_length]
    
    if not safe_name:
        safe_name = uuid.uuid4().hex[:16]
    
    return safe_name


def validate_photo_filename(filename: str) -> tuple:
    if not filename:
        return False, "文件名不能为空"
    
    if '..' in filename or '/' in filename or '\\' in filename:
        return False, "文件名包含非法字符"
    
    ext = os.path.splitext(filename)[1].lower()
    if ext not in PHOTO_EXTENSIONS:
        return False, f"不支持的文件类型: {ext}"
    
    if len(filename) > 255:
        return False, "文件名过长"
    
    return True, ""


def find_existing_photo(base_name: str, photos_dir: str) -> str:
    if not base_name or base_name == "无":
        return ""
    cleaned = clean_filename(base_name)
    for ext in PHOTO_EXTENSIONS:
        path = os.path.join(photos_dir, cleaned + ext)
        if os.path.exists(path):
            return path
    return ""


def has_any_photo(id_card: str, social1: str, social2: str, social3: str, photos_dir: str) -> bool:
    for card in [id_card, social1, social2, social3]:
        if find_existing_photo(card, photos_dir):
            return True
    return False


def get_photo_base_name(photo_type: str, id_card: str, social1: str, social2: str, social3: str) -> str:
    mapping = {
        "身份证": id_card,
        "社保卡1": social1,
        "社保卡2": social2,
        "社保卡3": social3,
    }
    return mapping.get(photo_type, "")


def safe_str(val) -> str:
    if val is None:
        return ""
    return str(val).strip()


def calculate_enrollment_date(grade: str, birth_date_str: str = None) -> str:
    today = date.today()
    current_year = today.year

    if grade == "GRADUATED":
        return ""

    grade_levels = {
        "T1": 0,
        "K1": 1, "K2": 2, "K3": 3,
        "G1": 4, "G2": 5, "G3": 6, "G4": 7, "G5": 8, "G6": 9,
        "G7": 10, "G8": 11, "G9": 12,
        "G10": 13, "G11": 14, "G12": 15,
        "V1": 13, "V2": 14, "V3": 15,
        "J1": 13, "J2": 14, "J3": 15,
        "C1": 16, "C2": 17, "C3": 18,
        "Z1": 16, "Z2": 17, "Z3": 18,
        "U1": 19, "U2": 20, "U3": 21, "U4": 22, "U5": 23,
        "M1": 24, "M2": 25, "M3": 26,
        "D1": 27, "D2": 28, "D3": 29, "D4": 30
    }

    start_levels = {
        "T": 0, "K": 1, "G": 4, "V": 13, "J": 13, "C": 16, "Z": 16, "U": 19, "M": 24, "D": 27
    }

    level = grade_levels.get(grade, 0)
    prefix = grade[0] if grade else "G"
    start_level = start_levels.get(prefix, 4)

    years_in_grade = level - start_level
    enrollment_year = current_year - years_in_grade

    if today.month < 9:
        enrollment_year -= 1

    return f"{enrollment_year}-09-01"


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


def validate_year(year_str: str) -> tuple[bool, str]:
    if not year_str:
        return True, ""
    
    year_str = year_str.strip()
    
    if not year_str.isdigit():
        return False, "年份必须是数字"
    
    year = int(year_str)
    current_year = date.today().year
    
    if year < 2000:
        return False, "年份不能早于2000年"
    if year > current_year + 1:
        return False, f"年份不能晚于{current_year + 1}年"
    
    return True, ""


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
