import secrets
from flask import request, jsonify

from utils.security import require_auth
from utils.response import get_json_data, safe_error
from utils import validate_id_card, validate_phone
from database import get_session, Person, StudentEducation, add_operation_log
from . import bp


@bp.route('/student', methods=['POST'])
@require_auth
def create_student():
    if request.current_user.get('role') not in ['admin', 'user']:
        return jsonify({'error': '权限不足'}), 403
    
    data, err = get_json_data()
    if err:
        return err
    
    id_card = data.get('id_card', '')
    if not id_card:
        return jsonify({'error': '身份证号不能为空'}), 400
    
    valid, msg = validate_id_card(id_card)
    if not valid:
        return jsonify({'error': msg}), 400
    
    guardian_phone = data.get('guardian_phone', '')
    if guardian_phone:
        valid, msg = validate_phone(guardian_phone)
        if not valid:
            return jsonify({'error': f'监护人电话: {msg}'}), 400
    
    session = get_session()
    try:
        existing = session.query(StudentEducation).filter(
            StudentEducation.id_card == id_card
        ).first()
        if existing:
            return jsonify({'error': '该身份证号的学生已存在'}), 400
        
        person = session.query(Person).filter(Person.id_card == id_card).first()
        person_id = person.id if person else ''
        
        student = StudentEducation(
            id=f"edu_{secrets.token_hex(8)}",
            person_id=person_id,
            id_card=id_card,
            school_name=data.get('school_name', ''),
            grade=data.get('grade', ''),
            class_name=data.get('class_name', ''),
            guardian=data.get('guardian', ''),
            guardian_phone=data.get('guardian_phone', ''),
            is_left_behind=data.get('is_left_behind', '否'),
            student_status=data.get('student_status', ''),
            enrollment_date=data.get('enrollment_date', '')
        )
        
        session.add(student)
        session.commit()
        
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "添加学生",
            id_card,
            request.remote_addr,
            request.headers.get('X-Client-Type', 'Mobile')
        )
        
        return jsonify({'success': True, 'id': student.id})
    except Exception as e:
        session.rollback()
        return safe_error(str(e), 500)
    finally:
        session.close()
