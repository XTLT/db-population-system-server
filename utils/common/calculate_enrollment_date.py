from datetime import datetime


def calculate_enrollment_date(grade: str, _birth_date_str: str = None) -> str:
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
