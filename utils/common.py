"""
通用工具函数 - 年龄计算、文件名处理、照片查找等
"""
import os
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


def clean_filename(name: str, max_length: int = 100) -> str:
    """清理文件名，移除非法字符"""
    import re
    # 移除非法字符
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # 限制长度
    if len(name) > max_length:
        name = name[:max_length]
    return name


def validate_photo_filename(filename: str) -> tuple:
    """验证照片文件名格式
    
    Returns:
        (is_valid, id_card, photo_type, extension)
    """
    if not filename:
        return False, None, None, None
    
    # 支持的扩展名
    valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    
    # 分离扩展名
    name, ext = os.path.splitext(filename.lower())
    if ext not in valid_extensions:
        return False, None, None, None
    
    # 解析文件名格式: {身份证号}_{照片类型}
    parts = name.split('_')
    if len(parts) != 2:
        return False, None, None, None
    
    id_card, photo_type = parts
    
    # 验证身份证号格式
    if not (id_card[:-1].isdigit() and id_card[-1] in '0123456789xX') or len(id_card) != 18:
        return False, None, None, None
    
    return True, id_card, photo_type, ext


def find_existing_photo(base_name: str, photos_dir: str) -> str:
    """查找已存在的照片文件"""
    if not os.path.isdir(photos_dir):
        return ""
    
    extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    for ext in extensions:
        photo_path = os.path.join(photos_dir, base_name + ext)
        if os.path.exists(photo_path):
            return photo_path
    return ""


def has_any_photo(id_card: str, social1: str, social2: str, social3: str, photos_dir: str) -> bool:
    """检查是否有任何照片"""
    from config import PHOTO_EXTENSIONS
    
    if not os.path.isdir(photos_dir):
        return False
    
    base_name = id_card
    for ext in PHOTO_EXTENSIONS:
        # 身份证照片
        if os.path.exists(os.path.join(photos_dir, f"{base_name}_身份证{ext}")):
            return True
        # 社保卡照片
        if social1 and os.path.exists(os.path.join(photos_dir, f"{base_name}_社保卡1{ext}")):
            return True
        if social2 and os.path.exists(os.path.join(photos_dir, f"{base_name}_社保卡2{ext}")):
            return True
        if social3 and os.path.exists(os.path.join(photos_dir, f"{base_name}_社保卡3{ext}")):
            return True
    return False


def get_photo_base_name(photo_type: str, id_card: str, social1: str, social2: str, social3: str) -> str:
    """获取照片基础文件名"""
    if photo_type == "身份证":
        return f"{id_card}_身份证"
    elif photo_type == "社保卡1":
        return f"{id_card}_社保卡1"
    elif photo_type == "社保卡2":
        return f"{id_card}_社保卡2"
    elif photo_type == "社保卡3":
        return f"{id_card}_社保卡3"
    return ""


def safe_str(val) -> str:
    """安全转换为字符串"""
    if val is None:
        return ""
    return str(val)


def calculate_enrollment_date(grade: str, birth_date_str: str = None) -> str:
    """计算入学日期"""
    from config import GRADE_DISPLAY
    
    if not grade:
        return ""
    
    # 从年级反推入学年份
    grade_order = GRADE_DISPLAY.get(grade, 0)
    if grade_order <= 0:
        return ""
    
    # 假设一年级入学年龄为6岁
    current_year = datetime.now().year
    
    # 找到当前年级对应的最大年级
    max_grade_order = max(GRADE_DISPLAY.values())
    
    # 计算入学年份
    enrollment_year = current_year - (max_grade_order - grade_order)
    
    return f"{enrollment_year}-09-01"
