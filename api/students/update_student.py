from flask import request, jsonify

from utils.security import require_auth
from utils.response import get_json_data, safe_error
from database import get_session, StudentEducation, add_operation_log
from . import bp


@bp.route('/student/<id_card>', methods=['PUT'])
@require_auth
def update_student(id_card):
    if request.current_user.get('role') not in ['admin', 'user']:
        return jsonify({'error': '权限不足'}), 403
    
    data, err = get_json_data()
    if err:
        return err
    
    session = get_session()
    try:
        student = session.query(StudentEducation).filter(
            StudentEducation.id_card == id_card
        ).first()
        
        if not student:
            return jsonify({'error': '学生不存在'}), 404
        
        updatable_fields = [
            'school_name', 'grade', 'class_name', 
            'guardian', 'guardian_phone', 
            'is_left_behind', 'student_status', 'enrollment_date'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(student, field, data[field])
        
        session.commit()
        
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "更新学生信息",
            id_card,
            request.remote_addr,
            request.headers.get('X-Client-Type', 'Mobile')
        )
        
        return jsonify({'success': True})
    except Exception as e:
        session.rollback()
        return safe_error(str(e), 500)
    finally:
        session.close()
