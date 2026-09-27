"""create_notification 函数。"""

import secrets
from ..models.notification import Notification
from .._base import get_session

def create_notification(title: str, content: str, notification_type: str = "system",
                        target_user: str = "", sender_id: str = "", sender_name: str = "") -> dict:
    from datetime import datetime
    session = get_session()
    try:
        notification = Notification(
            id=f"notif_{secrets.token_hex(8)}",
            title=title,
            content=content,
            notification_type=notification_type,
            target_user=target_user,
            sender_id=sender_id,
            sender_name=sender_name,
            is_read="否",
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            read_at=""
        )
        session.add(notification)
        session.commit()
        return {
            "id": notification.id,
            "title": notification.title,
            "content": notification.content,
            "notification_type": notification.notification_type,
            "target_user": notification.target_user,
            "sender_name": notification.sender_name,
            "is_read": notification.is_read,
            "created_at": notification.created_at
        }
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

