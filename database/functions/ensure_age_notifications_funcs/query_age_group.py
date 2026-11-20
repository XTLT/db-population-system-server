"""查出下月过生日、届时满 age 周岁的人员。"""

from sqlalchemy import func

from ...models.person import Person
from .alive_condition import alive_condition
from .not_migrated_condition import not_migrated_condition


def query_age_group(session, age, target_year, target_month):
    birth_year = str(target_year - age)
    birth_month = "%02d" % target_month
    return (
        session.query(Person)
        .filter(
            func.length(Person.id_card) == 18,
            func.substr(Person.id_card, 7, 4) == birth_year,
            func.substr(Person.id_card, 11, 2) == birth_month,
            alive_condition(),
            not_migrated_condition(),
        )
        .order_by(Person.address, Person.group_name, Person.name)
        .all()
    )
