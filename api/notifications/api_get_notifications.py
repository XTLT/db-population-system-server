from flask import request, jsonify, current_app

from database import get_notifications, ensure_age_notifications
from utils.security import require_auth
from . import bp


@bp.route('/', methods=['GET'])
@require_auth
def api_get_notifications():
    """获取通知列表"""
    user = request.current_user
    username = user.get('username', '')
    limit = request.args.get('limit', 50, type=int)

    # 懒生成"下月满 60/80 周岁"提醒：幂等，失败不影响正常通知列表
    try:
        ensure_age_notifications()
    except Exception as e:
        current_app.logger.warning(f"生成到龄提醒通知失败: {e}")

    notifications = get_notifications(username=username, limit=limit)
    return jsonify({'notifications': notifications})
