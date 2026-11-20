"""POST /api/persons/deleted/purge：物理清理已删除记录（管理员）。"""

from flask import request, jsonify
from utils.security import get_client_ip, require_auth

from database import purge_deleted_persons, add_operation_log


@require_auth
def api_purge_deleted():
    if request.current_user.get('role') != 'admin':
        return jsonify({'success': False, 'error': '权限不足'}), 403
    body = request.get_json(silent=True) or {}
    try:
        days = int(body.get('days', 90) or 90)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'error': 'days 必须为正整数'}), 400
    if days < 1:
        return jsonify({'success': False, 'error': 'days 必须为正整数'}), 400
    try:
        count = purge_deleted_persons(days=days)
    except Exception as e:
        return jsonify({'success': False, 'error': f'清理失败: {e}'}), 500
    add_operation_log(
        request.current_user['id'],
        request.current_user['username'],
        "清理删除记录",
        f"物理清理{count}条（保留{days}天内）",
        get_client_ip(),
        "Web",
        "是"
    )
    return jsonify({'success': True, 'purged': count})
