from flask import request, jsonify

from database import get_all_users
from utils.security import require_auth
from . import bp
from ._helpers import _require_admin


@bp.route('/')
@require_auth
def api_users():
    """获取用户列表（仅管理员）"""
    if not _require_admin():
        return jsonify({'error': '权限不足'}), 403
    users = get_all_users()
    return jsonify({
        'users': [{
            'id': u.id,
            'username': u.username,
            'real_name': u.real_name,
            'role': u.role,
            'is_active': u.is_active,
            'is_default': u.is_default,
            'created_at': u.created_at or '',
            'last_login': u.last_login or '',
            'login_attempts': u.login_attempts or 0
        } for u in users]
    })
