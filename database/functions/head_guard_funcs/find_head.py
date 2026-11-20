"""查该户现有户主（可排除指定 id），无则返回 None。"""

from ...models.person import Person


def find_head(session, hu_hao, exclude_id=None):
    if not hu_hao:
        return None
    q = session.query(Person).filter_by(hu_hao=hu_hao, relation='户主')
    if exclude_id:
        q = q.filter(Person.id != exclude_id)
    return q.first()
