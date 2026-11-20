"""GET /api/persons/pending-correction：死亡/迁出但仍有补贴记录的人员清单。"""

from flask import jsonify
from sqlalchemy import or_
from utils.security import require_auth

from database import get_session, Person
from .subsidy_modules import SUBSIDY_MODULES
from .to_amount import to_amount


@require_auth
def api_pending_correction():
    """只读排查清单，不修改任何数据。

    没有补贴记录的人不会进入本清单（说明已经干净）。
    """
    session = get_session()
    try:
        persons = (
            session.query(Person)
            .filter(or_(Person.is_dead == '是', Person.is_migrated == '是'))
            .all()
        )
        if not persons:
            return jsonify({'total': 0, 'items': []})

        id_cards = {
            (p.id_card or '').strip() for p in persons if (p.id_card or '').strip()
        }
        if not id_cards:
            return jsonify({'total': 0, 'items': []})

        # 一次 in_() 汇总各模块，避免逐人逐表查询
        agg = {}
        for module, label, model, period_attr, amount_attr in SUBSIDY_MODULES:
            rows = (
                session.query(model)
                .filter(getattr(model, 'id_card').in_(list(id_cards)))
                .all()
            )
            for r in rows:
                card = (getattr(r, 'id_card', '') or '').strip()
                if not card:
                    continue
                slot = agg.setdefault(card, {})
                period = (getattr(r, period_attr, '') or '').strip()
                amount = (getattr(r, amount_attr, '') or '').strip()
                info = slot.get(module)
                if info is None:
                    info = {
                        'module': module,
                        'label': label,
                        'count': 0,
                        'total_amount_value': 0.0,
                        'latest_period': period,
                        'last_amount': amount,
                    }
                    slot[module] = info
                info['count'] += 1
                info['total_amount_value'] += to_amount(amount)
                if period and (not info['latest_period'] or period > info['latest_period']):
                    info['latest_period'] = period
                    info['last_amount'] = amount

        items = []
        for p in persons:
            card = (p.id_card or '').strip()
            mods = agg.get(card) or {}
            if not mods:
                continue
            module_list = []
            for m in sorted(mods.values(), key=lambda x: x['label']):
                total = m['total_amount_value']
                module_list.append({
                    'module': m['module'],
                    'label': m['label'],
                    'count': m['count'],
                    'total_amount': f"{total:.2f}" if total else '',
                    'latest_period': m['latest_period'],
                    'last_amount': m['last_amount'],
                })
            items.append({
                'person_id': p.id,
                'name': p.name or '',
                'id_card': card,
                'hu_hao': p.hu_hao or '',
                'group_name': p.group_name or '',
                'is_dead': p.is_dead or '',
                'death_date': p.death_date or '',
                'is_migrated': p.is_migrated or '',
                'modules': module_list,
                'module_count': len(module_list),
            })

        items.sort(key=lambda x: (-x['module_count'], x['name']))
        return jsonify({'total': len(items), 'items': items})
    finally:
        session.close()
