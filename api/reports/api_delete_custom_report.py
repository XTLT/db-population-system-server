from flask import request, jsonify

from database import get_custom_report, delete_custom_report, add_operation_log
from utils.security import require_auth
from . import bp


@bp.route('/custom/<report_id>', methods=['DELETE'])
@require_auth
def api_delete_custom_report(report_id):
    """删除报表"""
    user = request.current_user

    try:
        # 先检查报表是否存在及权限
        existing = get_custom_report(report_id)
        if not existing:
            return jsonify({'error': '报表不存在'}), 404

        if user.get('role') != 'admin' and existing['user_id'] != user['id']:
            return jsonify({'error': '权限不足'}), 403

        deleted = delete_custom_report(report_id)

        if deleted:
            add_operation_log(
                user['id'],
                user['username'],
                "删除自定义报表",
                f"ID:{report_id}, 标题:{existing['title']}",
                request.remote_addr,
                "Web"
            )
            return jsonify({'success': True})
        else:
            return jsonify({'error': '删除失败'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
