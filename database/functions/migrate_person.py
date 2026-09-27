"""migrate_person 函数。"""

from ..models.person import Person
from .._base import get_session

def migrate_person(person_id: str, migration_date: str, migration_place: str, migration_reason: str):
    session = get_session()
    try:
        person = session.query(Person).filter(Person.id == person_id).first()
        if person:
            person.is_migrated = "是"
            person.migration_date = migration_date
            person.migration_place = migration_place
            person.migration_reason = migration_reason
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

