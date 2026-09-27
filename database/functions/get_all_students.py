"""get_all_students 函数。"""

from ..models.student_education import StudentEducation
from .._base import get_session

def get_all_students() -> list:
    session = get_session()
    try:
        return session.query(StudentEducation).filter(
            StudentEducation.student_status.in_(["在读", "留级", "跳级"])
        ).all()
    finally:
        session.close()

