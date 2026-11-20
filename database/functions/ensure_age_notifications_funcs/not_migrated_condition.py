"""未迁出条件。"""

from sqlalchemy import or_

from ...models.person import Person


def not_migrated_condition():
    return or_(Person.is_migrated.is_(None), Person.is_migrated != "是")
