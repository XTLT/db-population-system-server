"""get_student_education 函数。"""

from ..models.student_education import StudentEducation
from .._base import get_session

def get_student_education(person_id: str) -> 'StudentEducation | None':
    session = get_session()
    try:
        return session.query(StudentEducation).filter(StudentEducation.person_id == person_id).first()
    finally:
        session.close()

