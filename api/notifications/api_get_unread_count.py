from flask import request, jsonify

from database import get_unread_count
from utils.security import require_auth
from . import bp


@bp.route('/unread-count')
@require_auth
def api_get_unread_count():
    """获取未读消息数量"""
    user = request.current_user
    username = user.get('username', '')

    count = get_unread_count(username)
    return jsonify({'count': count})
