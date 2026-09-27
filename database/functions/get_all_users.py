"""get_all_users 函数。"""

from ..models.user import User
from .._base import get_session

def get_all_users(limit: int = None) -> list:
    session = get_session()
    try:
        query = session.query(User)
        if limit is not None:
            query = query.limit(limit)
        return query.all()
    finally:
        session.close()

