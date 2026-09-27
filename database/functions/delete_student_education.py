"""delete_student_education 函数。"""

from ..models.student_education import StudentEducation
from .._base import get_session

def delete_student_education(person_id: str):
    session = get_session()
    try:
        edu = session.query(StudentEducation).filter(StudentEducation.person_id == person_id).first()
        if edu:
            session.delete(edu)
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

