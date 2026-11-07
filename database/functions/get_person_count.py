"""get_person_count 函数。"""

from ..models.person import Person
from .._base import get_session
from ._alive_filter import alive_filter

def get_person_count() -> int:
    session = get_session()
    try:
        return session.query(Person).filter(alive_filter()).count()
    finally:
        session.close()

