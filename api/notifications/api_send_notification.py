from flask import request, jsonify

from database import create_notification
from utils.security import require_auth
from utils.response import get_json_data
from . import bp


@bp.route('/send', methods=['POST'])
@require_auth
def api_send_notification():
    """发送通知（仅管理员）"""
    user = request.current_user
    is_admin = user.get('role') == 'admin'

    if not is_admin:
        return jsonify({'error': '权限不足'}), 403

    data, err = get_json_data()
    if err:
        return err

    if not data:
        return jsonify({'error': '无效请求数据'}), 400

    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    notification_type = data.get('notification_type', 'system')
    target_user = data.get('target_user', '').strip()

    if not title or not content:
        return jsonify({'error': '标题和内容不能为空'}), 400

    if notification_type not in ['system', 'business']:
        notification_type = 'system'

    sender_id = user.get('user_id', '')
    sender_name = user.get('real_name', user.get('username', ''))

    notification = create_notification(
        title=title,
        content=content,
        notification_type=notification_type,
        target_user=target_user,
        sender_id=sender_id,
        sender_name=sender_name
    )

    return jsonify({'success': True, 'notification': notification})
