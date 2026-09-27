"""check_duplicate_id_card 函数。"""

from ..models.person import Person
from .._base import get_session

def check_duplicate_id_card(hu_hao: str, id_card: str, exclude_id: str = None) -> bool:
    session = get_session()
    try:
        q = session.query(Person).filter(Person.hu_hao == hu_hao, Person.id_card == id_card)
        if exclude_id:
            q = q.filter(Person.id != exclude_id)
        return q.first() is not None
    finally:
        session.close()

