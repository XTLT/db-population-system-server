"""update_person 函数。"""

from ..models.person import Person
from .._base import get_session

def update_person(person: Person):
    from datetime import datetime
    session = get_session()
    try:
        person.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session.merge(person)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

