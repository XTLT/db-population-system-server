"""mark_notification_read 函数。"""

from ..models.notification import Notification
from .._base import get_session

def mark_notification_read(notification_id: str) -> bool:
    from datetime import datetime
    session = get_session()
    try:
        notification = session.query(Notification).filter(Notification.id == notification_id).first()
        if notification:
            notification.is_read = "是"
            notification.read_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            session.commit()
            return True
        return False
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

