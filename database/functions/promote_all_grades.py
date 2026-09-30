"""promote_all_grades 函数。"""

from ..models.student_education import StudentEducation
from ..models.education_history import EducationHistory
from .._base import get_session

def promote_all_grades(id_cards=None):
    """升级在读/跳级学生。id_cards: 可选，仅升级指定身份证号；None 则全量。"""
    from config import GRADE_PROMOTION_MAP, GRADUATION_GRADES, BLOCKED_PROMOTION_STATUSES
    from datetime import datetime
    session = get_session()
    try:
        students = session.query(StudentEducation).filter(
            StudentEducation.student_status.in_(["在读", "跳级"])
        )
        if id_cards:
            students = students.filter(StudentEducation.id_card.in_(id_cards))
        students = students.all()
        count = 0
        for s in students:
            if s.student_status in BLOCKED_PROMOTION_STATUSES:
                continue
            new_grade = GRADE_PROMOTION_MAP.get(s.grade)
            if new_grade:
                history = EducationHistory(
                    id=f"hist_{datetime.now().strftime('%Y%m%d%H%M%S')}_{s.person_id}",
                    person_id=s.person_id,
                    id_card=s.id_card,
                    school_name=s.school_name,
                    grade=s.grade,
                    class_name=s.class_name,
                    student_status=s.student_status,
                    change_date=datetime.now().strftime("%Y-%m-%d"),
                    change_reason="自动升年级"
                )
                session.add(history)
                s.grade = new_grade
                if new_grade == "GRADUATED" or new_grade in GRADUATION_GRADES:
                    s.student_status = "毕业"
                count += 1
        session.commit()
        return count
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

