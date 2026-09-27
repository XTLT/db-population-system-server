"""batch_set_left_behind 函数。"""

from ..models.student_education import StudentEducation
from .._base import get_session

def batch_set_left_behind(person_ids: list, is_left_behind: str):
    session = get_session()
    try:
        for pid in person_ids:
            edu = session.query(StudentEducation).filter(StudentEducation.person_id == pid).first()
            if edu:
                edu.is_left_behind = is_left_behind
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

