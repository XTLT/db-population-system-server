from flask import request, jsonify

from database import mark_notification_read
from utils.security import require_auth
from . import bp


@bp.route('/<notification_id>/read', methods=['POST'])
@require_auth
def api_mark_notification_read(notification_id):
    """标记通知为已读"""
    user = request.current_user
    username = user.get('username', '')

    # IDOR 防护：验证通知是否属于当前用户
    from database import get_session, Notification
    session = get_session()
    try:
        notification = session.query(Notification).filter(
            Notification.id == notification_id
        ).first()

        if not notification:
            return jsonify({'error': '通知不存在'}), 404

        # 检查通知是否属于当前用户（目标用户为空表示全体通知）
        if notification.target_user and notification.target_user != username:
            return jsonify({'error': '无权操作此通知'}), 403

        success = mark_notification_read(notification_id)
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': '标记失败'}), 500
    finally:
        session.close()
