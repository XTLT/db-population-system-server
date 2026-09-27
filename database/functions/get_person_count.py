"""get_person_count 函数。"""

from ..models.person import Person
from .._base import get_session

def get_person_count() -> int:
    session = get_session()
    try:
        return session.query(Person).count()
    finally:
        session.close()

