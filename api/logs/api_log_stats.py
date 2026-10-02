from flask import request, jsonify

from database import get_operation_log_stats
from utils.security import require_auth
from . import bp


@bp.route('/stats')
@require_auth
def api_log_stats():
    """获取操作日志统计信息（仅管理员）"""
    user = request.current_user
    is_admin = user.get('role') == 'admin'

    if not is_admin:
        return jsonify({'error': '权限不足'}), 403

    stats = get_operation_log_stats()
    return jsonify(stats)
