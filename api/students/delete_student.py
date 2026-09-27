from flask import request, jsonify

from utils.security import require_auth
from utils.response import safe_error
from database import get_session, StudentEducation, add_operation_log
from . import bp


@bp.route('/student/<id_card>', methods=['DELETE'])
@require_auth
def delete_student(id_card):
    if request.current_user.get('role') not in ['admin', 'user']:
        return jsonify({'error': '权限不足'}), 403
    
    session = get_session()
    try:
        student = session.query(StudentEducation).filter(
            StudentEducation.id_card == id_card
        ).first()
        
        if not student:
            return jsonify({'error': '学生不存在'}), 404
        
        session.delete(student)
        session.commit()
        
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "删除学生",
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
