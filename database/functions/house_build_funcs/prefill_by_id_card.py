"""按身份证从人口库带出申请人信息、同户成员和该户历史申请。"""

from ..._base import get_session
from ...models.house_build_app import HouseBuildApp
from ...models.person import Person
from ..head_guard_funcs.infer_gender import infer_gender
from utils import person_age


def _clean(value):
    return '' if value is None else str(value).strip()


def prefill_by_id_card(id_card):
    id_card = _clean(id_card).upper()
    if not id_card:
        return {'found': False, 'message': '身份证号为空'}

    session = get_session()
    try:
        person = (
            session.query(Person)
            .filter(Person.id_card == id_card)
            .first()
        )
        if person is None:
            return {'found': False, 'message': '人口库中没有该身份证号'}

        members = []
        history = []
        if person.hu_hao:
            rows = (
                session.query(Person)
                .filter(Person.hu_hao == person.hu_hao)
                .filter(Person.id_card != id_card)
                .all()
            )
            rows = [r for r in rows if _clean(r.is_dead) != '是' and _clean(r.is_migrated) != '是']
            rows.sort(key=lambda r: (0 if _clean(r.relation) == '户主' else 1, _clean(r.relation)))
            for index, row in enumerate(rows, start=1):
                members.append({
                    'seq': str(index),
                    'name': _clean(row.name),
                    'age': str(person_age(row.age, row.id_card) or ''),
                    'relation': _clean(row.relation),
                    'id_card': _clean(row.id_card),
                    'hukou': _clean(row.address),
                })

            history = [
                {
                    'id': h.id,
                    'app_no': h.app_no or '',
                    'created_at': h.created_at or '',
                    'apply_land_area': h.apply_land_area or '',
                    'apply_area_num': h.apply_area_num or 0.0,
                    'status': h.status or 'draft',
                }
                for h in (
                    session.query(HouseBuildApp)
                    .filter(HouseBuildApp.hu_hao == person.hu_hao)
                    .order_by(HouseBuildApp.created_at.desc())
                    .limit(20)
                    .all()
                )
            ]

        return {
            'found': True,
            'person_id': person.id,
            'owner_name': _clean(person.name),
            'owner_gender': infer_gender(id_card),
            'owner_age': str(person_age(person.age, person.id_card) or ''),
            'owner_phone': _clean(person.phone),
            'owner_id_card': id_card,
            'owner_hukou': _clean(person.address),
            'address': _clean(person.address),
            'hu_hao': _clean(person.hu_hao),
            'group_name': _clean(person.group_name),
            'members': members,
            'history': history,
        }
    finally:
        session.close()
