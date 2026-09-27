"""get_family_members 函数。"""

from ..models.person import Person
from .._base import get_session

def get_family_members(hu_hao: str) -> list[Person]:
    session = get_session()
    try:
        return session.query(Person).filter(Person.hu_hao == hu_hao).all()
    finally:
        session.close()

