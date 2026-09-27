from flask import request, jsonify

from utils.security import require_auth
from database import add_operation_log
from . import bp


@bp.route('/students/promote', methods=['POST'])
@require_auth
def promote_grades():
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403
    
    from database import promote_all_grades
    try:
        count = promote_all_grades()
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "年级升级",
            f"升级{count}名学生",
            request.remote_addr,
            request.headers.get('X-Client-Type', 'Web')
        )
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
