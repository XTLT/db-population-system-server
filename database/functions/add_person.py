"""add_person 函数。"""

from ..models.person import Person
from .._base import get_session

def add_person(person: Person):
    session = get_session()
    try:
        session.add(person)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

