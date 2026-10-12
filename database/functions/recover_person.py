"""recover_person 函数。"""

from ..models.person import Person
from ..models.deleted_person import DeletedPerson
from .._base import get_session

def recover_person(deleted_id: str):
    session = get_session()
    try:
        deleted = session.query(DeletedPerson).filter(DeletedPerson.id == deleted_id).first()
        if deleted:
            person = Person(
                id=deleted.original_id,
                hu_hao=deleted.hu_hao,
                id_card=deleted.id_card,
                name=deleted.name,
                age=deleted.age,
                address=deleted.address,
                relation=deleted.relation,
                is_dead=deleted.is_dead,
                phone=deleted.phone,
                remark=deleted.remark,
                poor_type=deleted.poor_type,
                disability=deleted.disability,
                disability_type=deleted.disability_type,
                dis_level=deleted.dis_level,
                dibao=deleted.dibao,
                tekun=deleted.tekun,
                tekun_type=deleted.tekun_type,
                jisheng=deleted.jisheng,
                social_card1=deleted.social_card1,
                social_card2=deleted.social_card2,
                social_card3=deleted.social_card3,
                social_card2_source=deleted.social_card2_source,
                social_card3_source=deleted.social_card3_source,
                is_migrated=deleted.is_migrated,
                migration_date=deleted.migration_date,
                migration_place=deleted.migration_place,
                migration_reason=deleted.migration_reason
            )
            session.add(person)
            session.delete(deleted)
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

