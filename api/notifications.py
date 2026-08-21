from flask import Blueprint, request, jsonify

from database import (
    create_notification, get_notifications, 
    mark_notification_read, get_unread_count
)
from utils.security import require_auth
from utils.response import safe_error, get_json_data


bp = Blueprint('notifications', __name__)


@bp.route('/', methods=['GET'])
@require_auth
def api_get_notifications():
    """获取通知列表"""
    user = request.current_user
    username = user.get('username', '')
    limit = request.args.get('limit', 50, type=int)
    
    notifications = get_notifications(username=username, limit=limit)
    return jsonify({'notifications': notifications})


@bp.route('/unread-count')
@require_auth
def api_get_unread_count():
    """获取未读消息数量"""
    user = request.current_user
    username = user.get('username', '')
    
    count = get_unread_count(username)
    return jsonify({'count': count})


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
