from flask import request, jsonify

from utils.security import require_auth
from utils.response import safe_error
from database import get_session, StudentEducation, add_operation_log
from . import bp


@bp.route('/students/batch-delete', methods=['POST'])
@require_auth
def batch_delete_students():
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403
    
    data = request.get_json()
    student_ids = data.get('ids', [])
    
    if not student_ids:
        return jsonify({'error': '未选择学生'}), 400
    
    if len(student_ids) > 100:
        return jsonify({
            'error': f'单次最多删除 100 条记录，当前选择了 {len(student_ids)} 条'
        }), 400
    
    confirm = data.get('confirm', False)
    if not confirm:
        return jsonify({
            'error': '需要确认',
            'require_confirm': True,
            'count': len(student_ids)
        }), 400
    
    session = get_session()
    try:
        deleted_count = session.query(StudentEducation).filter(
            StudentEducation.id.in_(student_ids)
        ).delete(synchronize_session='fetch')
        
        session.commit()
        
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "批量删除学生",
            f"删除{deleted_count}条记录",
            request.remote_addr,
            request.headers.get('X-Client-Type', 'Web')
        )
        
        return jsonify({'success': True, 'deleted': deleted_count})
    except Exception as e:
        session.rollback()
        return safe_error(str(e), 500)
    finally:
        session.close()
