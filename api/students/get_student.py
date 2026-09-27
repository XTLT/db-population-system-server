from flask import request, jsonify

from database import get_session, Person, StudentEducation
from utils.security import require_auth
from config import GRADE_DISPLAY
from . import bp


@bp.route('/student/<id_card>')
@require_auth
def get_student(id_card):
    session = get_session()
    try:
        student = session.query(StudentEducation).filter(
            StudentEducation.id_card == id_card
        ).first()
        
        if not student:
            return jsonify({'error': '学生不存在'}), 404
        
        person = session.query(Person).filter(Person.id == student.person_id).first()
        
        return jsonify({
            'student': {
                'id': student.id,
                'person_id': student.person_id,
                'id_card': student.id_card,
                'name': person.name if person else '',
                'school_name': student.school_name,
                'grade': student.grade,
                'grade_display': GRADE_DISPLAY.get(student.grade, student.grade),
                'class_name': student.class_name,
                'guardian': student.guardian,
                'guardian_phone': student.guardian_phone,
                'is_left_behind': student.is_left_behind,
                'student_status': student.student_status,
                'enrollment_date': student.enrollment_date,
                'graduation_date': student.graduation_date
            }
        })
    finally:
        session.close()
