from flask import request, jsonify

from database import get_session, Person, search_students
from utils.security import require_auth
from config import GRADE_DISPLAY
from . import bp


@bp.route('/students')
@require_auth
def api_students():
    school = request.args.get('school')
    grade = request.args.get('grade')
    class_name = request.args.get('class_name')
    is_left_behind = request.args.get('is_left_behind')
    students = search_students(school, grade, class_name, is_left_behind)
    session = get_session()
    try:
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
                'is_left_behind': s.is_left_behind,
                'student_status': s.student_status
            })
        return jsonify({'students': result})
    finally:
        session.close()
