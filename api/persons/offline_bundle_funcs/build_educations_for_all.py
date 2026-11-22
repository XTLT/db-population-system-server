"""离线全量包：把全部就读信息按身份证聚合，供移动端离线详情直接使用。"""

from config import GRADE_DISPLAY
from database import StudentEducation


def build_educations_for_all(session):
    result = {}
    rows = session.query(StudentEducation).all()
    for row in rows:
        id_card = (row.id_card or "").strip()
        if not id_card:
            continue
        result[id_card] = {
            "school_name": row.school_name or "",
            "grade": GRADE_DISPLAY.get(row.grade, row.grade) if row.grade else "",
            "class_name": row.class_name or "",
            "guardian": row.guardian or "",
            "guardian_phone": row.guardian_phone or "",
            "is_left_behind": row.is_left_behind or "",
            "student_status": row.student_status or "",
            "enrollment_date": row.enrollment_date or "",
            "graduation_date": row.graduation_date or "",
        }
    return result
