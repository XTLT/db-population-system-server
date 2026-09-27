"""get_deleted_persons 函数。"""

from ..models.deleted_person import DeletedPerson
from .._base import get_session

def get_deleted_persons(limit: int = None) -> list:
    session = get_session()
    try:
        query = session.query(DeletedPerson)
        if limit is not None:
            query = query.limit(limit)
        return query.all()
    finally:
        session.close()

