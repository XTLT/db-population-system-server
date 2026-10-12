"""delete_person 函数。"""

from ..models.person import Person
from ..models.student_education import StudentEducation
from ..models.deleted_person import DeletedPerson
from .._base import get_session

def delete_person(person_id: str):
    from datetime import datetime
    import uuid
    session = get_session()
    try:
        person = session.query(Person).filter(Person.id == person_id).first()
        if person:
            # 先删除关联的就读信息
            session.query(StudentEducation).filter(
                StudentEducation.person_id == person.id
            ).delete()

            deleted = DeletedPerson(
                id=f"del_{uuid.uuid4().hex[:8]}",
                original_id=person.id,
                hu_hao=person.hu_hao,
                id_card=person.id_card,
                name=person.name,
                age=person.age,
                address=person.address,
                relation=person.relation,
                is_dead=person.is_dead,
                phone=person.phone,
                remark=person.remark,
                poor_type=person.poor_type,
                disability=person.disability,
                disability_type=person.disability_type,
                dis_level=person.dis_level,
                dibao=person.dibao,
                tekun=person.tekun,
                tekun_type=person.tekun_type,
                jisheng=person.jisheng,
                social_card1=person.social_card1,
                social_card2=person.social_card2,
                social_card3=person.social_card3,
                social_card2_source=person.social_card2_source,
                social_card3_source=person.social_card3_source,
                is_migrated=person.is_migrated,
                migration_date=person.migration_date,
                migration_place=person.migration_place,
                migration_reason=person.migration_reason,
                deleted_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            session.add(deleted)
            session.delete(person)
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

