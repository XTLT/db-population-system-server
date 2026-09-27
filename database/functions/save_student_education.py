"""save_student_education 函数。"""

from ..models.student_education import StudentEducation
from ..models.education_history import EducationHistory
from .._base import get_session

def save_student_education(education: StudentEducation):
    session = get_session()
    try:
        existing = session.query(StudentEducation).filter(
            StudentEducation.person_id == education.person_id
        ).first()
        if existing:
            changed = (
                existing.school_name != education.school_name or
                existing.grade != education.grade or
                existing.class_name != education.class_name or
                existing.student_status != education.student_status
            )
            if changed:
                from datetime import datetime
                import uuid
                history = EducationHistory(
                    id=str(uuid.uuid4()),
                    person_id=education.person_id,
                    id_card=existing.id_card,
                    school_name=existing.school_name,
                    grade=existing.grade,
                    class_name=existing.class_name,
                    student_status=existing.student_status,
                    change_date=datetime.now().strftime("%Y-%m-%d"),
                    change_reason="编辑更新"
                )
                session.add(history)
            existing.school_name = education.school_name
            existing.grade = education.grade
            existing.class_name = education.class_name
            existing.guardian = education.guardian
            existing.guardian_phone = education.guardian_phone
            existing.is_left_behind = education.is_left_behind
            existing.student_status = education.student_status
            existing.enrollment_date = education.enrollment_date
        else:
            session.add(education)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

