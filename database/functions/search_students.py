"""search_students 函数。"""

from ..models.student_education import StudentEducation
from .._base import get_session

def search_students(school: str = None, grade: str = None, class_name: str = None, is_left_behind: str = None) -> list:
    session = get_session()
    try:
        q = session.query(StudentEducation)
        if school:
            q = q.filter(StudentEducation.school_name == school)
        if grade:
            q = q.filter(StudentEducation.grade == grade)
        if class_name:
            q = q.filter(StudentEducation.class_name == class_name)
        if is_left_behind:
            q = q.filter(StudentEducation.is_left_behind == is_left_behind)
        return q.all()
    finally:
        session.close()

