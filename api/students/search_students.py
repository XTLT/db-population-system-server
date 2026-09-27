from flask import request, jsonify

from database import get_session, Person, StudentEducation
from utils.security import require_auth
from config import GRADE_DISPLAY
from . import bp


@bp.route('/students/search')
@require_auth
def search_students_api():
    name = request.args.get('name')
    school = request.args.get('school')
    grade = request.args.get('grade')
    class_name = request.args.get('class_name')
    is_left_behind = request.args.get('is_left_behind')

    session = get_session()
    try:
        query = session.query(StudentEducation).join(
            Person, StudentEducation.person_id == Person.id
        )

        if name and name.strip():
            safe_name = name.strip().replace('%', '\%').replace('_', '\_')
            query = query.filter(Person.name.like(f'%{safe_name}%', escape='\\'))

        if school and school.strip():
            safe_school = school.strip().replace('%', '\%').replace('_', '\_')
            query = query.filter(StudentEducation.school_name.like(f'%{safe_school}%', escape='\\'))

        if grade and grade.strip():
            query = query.filter(StudentEducation.grade == grade.strip())

        if class_name and class_name.strip():
            safe_class = class_name.strip().replace('%', '\%').replace('_', '\_')
            query = query.filter(StudentEducation.class_name.like(f'%{safe_class}%', escape='\\'))

        if is_left_behind and is_left_behind.strip():
            query = query.filter(StudentEducation.is_left_behind == is_left_behind.strip())

        students = query.limit(100).all()

        result = []
        for s in students:
            p = session.query(Person).filter(Person.id == s.person_id).first()
            result.append({
                'id': s.id,
                'person_id': s.person_id,
                'name': p.name if p else '',
                'id_card': s.id_card,
                'school_name': s.school_name,
                'grade': s.grade,
                'grade_display': GRADE_DISPLAY.get(s.grade, s.grade),
                'class_name': s.class_name,
                'guardian': s.guardian,
                'guardian_phone': s.guardian_phone,
                'is_left_behind': s.is_left_behind,
                'student_status': s.student_status,
                'enrollment_date': s.enrollment_date,
                'graduation_date': s.graduation_date
            })
        return jsonify({'results': result})
    finally:
        session.close()
