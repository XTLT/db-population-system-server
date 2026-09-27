"""get_notifications 函数。"""

from ..models.notification import Notification
from .._base import get_session

def get_notifications(username: str = "", limit: int = 50) -> list:
    session = get_session()
    try:
        query = session.query(Notification)
        if username:
            # 获取发给所有人的和发给特定用户的
            query = query.filter(
                (Notification.target_user == "") | (Notification.target_user == username)
            )
        notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
        return [
            {
                "id": n.id,
                "title": n.title,
                "content": n.content,
                "notification_type": n.notification_type,
                "target_user": n.target_user,
                "sender_name": n.sender_name,
                "is_read": n.is_read,
                "created_at": n.created_at,
                "read_at": n.read_at
            }
            for n in notifications
        ]
    finally:
        session.close()

