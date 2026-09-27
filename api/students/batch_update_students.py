from flask import request, jsonify

from utils.security import require_auth
from utils.response import safe_error
from database import get_session, StudentEducation, add_operation_log
from . import bp
from ._constants import STUDENT_BATCH_UPDATE_ALLOWED_FIELDS


@bp.route('/students/batch-update', methods=['POST'])
@require_auth
def batch_update_students():
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403
    
    data = request.get_json()
    student_ids = data.get('ids', [])
    updates = data.get('updates', {})
    
    if not student_ids:
        return jsonify({'error': '未选择学生'}), 400
    
    if not updates:
        return jsonify({'error': '未提供更新内容'}), 400
    
    if len(student_ids) > 200:
        return jsonify({
            'error': f'单次最多更新 200 条记录，当前选择了 {len(student_ids)} 条'
        }), 400
    
    filtered_updates = {
        k: v for k, v in updates.items() 
        if k in STUDENT_BATCH_UPDATE_ALLOWED_FIELDS
    }
    
    if not filtered_updates:
        return jsonify({'error': '没有有效的更新字段'}), 400
    
    session = get_session()
    try:
        students = session.query(StudentEducation).filter(
            StudentEducation.id.in_(student_ids)
        ).all()
        updated_count = 0
        
        for student in students:
            for key, value in filtered_updates.items():
                setattr(student, key, value)
            updated_count += 1
        
        session.commit()
        
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "批量更新学生",
            f"更新{updated_count}条记录",
            request.remote_addr,
            request.headers.get('X-Client-Type', 'Web')
        )
        
        return jsonify({'success': True, 'updated': updated_count})
    except Exception as e:
        session.rollback()
        return safe_error(str(e), 500)
    finally:
        session.close()
