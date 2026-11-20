"""GET /api/persons/data-health：村级数据体检（只读）。"""

from datetime import datetime

from flask import jsonify
from sqlalchemy import or_
from utils.security import require_auth

from database import get_session, Person
from database import StudentEducation as _StudentEducation
from utils import validate_id_card
from .add_health_item import add_health_item
from .subsidy_modules import DATA_HEALTH_MAX_ITEMS


def _build_buckets() -> dict:
    return {
        'id_card_empty': {'label': '缺身份证号', 'severity': 'high', 'items': []},
        'id_card_invalid': {'label': '身份证格式不对', 'severity': 'high', 'items': []},
        'phone_empty': {'label': '电话为空', 'severity': 'medium', 'items': []},
        'hu_hao_empty': {'label': '户号为空', 'severity': 'high', 'items': []},
        'no_head': {'label': '本户没有户主', 'severity': 'high', 'items': []},
        'idcard_multi_house': {'label': '同一身份证挂多个户号', 'severity': 'high', 'items': []},
        # 参考项：监护人电话不是必填，只展示不催办
        'student_no_guardian_phone': {
            'label': '学生缺监护人电话', 'severity': 'info', 'items': [], 'required': False,
        },
    }


@require_auth
def api_data_health():
    """只读接口，不修改任何数据；只检查在世人员（死亡/迁出不在体检范围）。

    检查项：缺身份证、身份证格式错、缺电话、缺户号、本户无户主、
            同一身份证挂多个户号；学生缺监护人电话为参考项（非必填，不计入待补录合计）。
    """
    session = get_session()
    try:
        persons = (
            session.query(Person)
            .filter(or_(Person.is_dead != '是', Person.is_dead.is_(None)))
            .all()
        )

        buckets = _build_buckets()

        by_house = {}
        by_card = {}
        person_by_id = {p.id: p for p in persons}

        for p in persons:
            card = (p.id_card or '').strip()
            hu = (p.hu_hao or '').strip()
            phone = (p.phone or '').strip()

            if not card:
                add_health_item(buckets, 'id_card_empty', p, '身份证号为空')
            else:
                ok, msg = validate_id_card(card)
                if not ok:
                    add_health_item(buckets, 'id_card_invalid', p, msg)

            if not phone:
                add_health_item(buckets, 'phone_empty', p, '电话为空')

            if not hu:
                add_health_item(buckets, 'hu_hao_empty', p, '户号为空')
            else:
                by_house.setdefault(hu, []).append(p)

            if card:
                slot = by_card.setdefault(card, {'hu_list': set(), 'persons': []})
                if hu:
                    slot['hu_list'].add(hu)
                slot['persons'].append(p)

        # 本户没有户主
        for hu, members in by_house.items():
            if not any((m.relation or '').strip() == '户主' for m in members):
                for m in members:
                    add_health_item(
                        buckets, 'no_head', m,
                        f'户号 {hu} 全户无户主（{len(members)} 人）',
                    )

        # 同一身份证挂多个户号
        for card, info in by_card.items():
            hu_set = info['hu_list']
            if len(hu_set) > 1:
                hu_text = '、'.join(sorted(hu_set))
                for m in info['persons']:
                    add_health_item(
                        buckets, 'idcard_multi_house', m,
                        f'同一身份证出现在 {len(hu_set)} 个户号：{hu_text}',
                    )

        # 学生缺监护人电话（学生表异常不影响其他体检项）
        try:
            students = (
                session.query(_StudentEducation)
                .filter(or_(
                    _StudentEducation.guardian_phone == '',
                    _StudentEducation.guardian_phone.is_(None),
                ))
                .all()
            )
            seen_students = set()
            for s in students:
                pid = s.person_id
                if pid in seen_students:
                    continue
                p = person_by_id.get(pid)
                if p is None:
                    continue
                seen_students.add(pid)
                add_health_item(
                    buckets, 'student_no_guardian_phone', p,
                    f'学生（{s.school_name or "学校未填"}）缺监护人电话',
                )
        except Exception:
            pass

        checks = []
        for key, info in buckets.items():
            items = info['items']
            checks.append({
                'key': key,
                'label': info['label'],
                'severity': info['severity'],
                'required': info.get('required', True),
                'count': len(items),
                'items': items[:DATA_HEALTH_MAX_ITEMS],
                'truncated': len(items) > DATA_HEALTH_MAX_ITEMS,
            })

        checks.sort(key=lambda x: (-x['count'], x['key']))

        # 只有必填项计入"待补录"合计，非必填项（如学生监护人电话）仅作参考
        required_checks = [c for c in checks if c.get('required', True)]
        issue_ids = set()
        for c in required_checks:
            for it in c['items']:
                issue_ids.add(it['person_id'])

        return jsonify({
            'checked_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_alive': len(persons),
            'total_issue_persons': len(issue_ids),
            'total_issue_count': sum(c['count'] for c in required_checks),
            'checks': checks,
        })
    finally:
        session.close()
