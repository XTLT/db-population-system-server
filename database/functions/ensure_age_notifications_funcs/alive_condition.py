"""在世条件（未标记死亡）。"""

from sqlalchemy import or_

from ...models.person import Person


def alive_condition():
    return or_(Person.is_dead.is_(None), Person.is_dead != "是")
