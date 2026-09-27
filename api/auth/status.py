from flask import jsonify

from database import get_all_users
from . import bp
from ._ensure_default_admin import _ensure_default_admin


@bp.route('/status')
def api_status():
    """系统状态检查（公开端点，不暴露敏感信息）"""
    _ensure_default_admin()
    users = get_all_users()
    has_default = any(u.is_default == "是" for u in users)
    has_real_admin = any(u.is_default != "是" and u.role == "admin" for u in users)
    return jsonify({
        'initialized': len(users) > 0,
        'has_default_admin': has_default,
        'need_create_admin': has_default and not has_real_admin
    })
