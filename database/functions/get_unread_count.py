"""get_unread_count 函数。"""

from ..models.notification import Notification
from .._base import get_session

def get_unread_count(username: str) -> int:
    session = get_session()
    try:
        count = session.query(Notification).filter(
            Notification.is_read == "否",
            ((Notification.target_user == "") | (Notification.target_user == username))
        ).count()
        return count
    finally:
        session.close()

