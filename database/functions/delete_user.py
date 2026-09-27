"""delete_user 函数。"""

from ..models.user import User
from .._base import get_session

def delete_user(user_id: str):
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            session.delete(user)
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

