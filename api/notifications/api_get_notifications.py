from flask import request, jsonify

from database import get_notifications
from utils.security import require_auth
from . import bp


@bp.route('/', methods=['GET'])
@require_auth
def api_get_notifications():
    """获取通知列表"""
    user = request.current_user
    username = user.get('username', '')
    limit = request.args.get('limit', 50, type=int)

    notifications = get_notifications(username=username, limit=limit)
    return jsonify({'notifications': notifications})
