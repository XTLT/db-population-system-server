"""GET /api/persons/pending-correction：死亡/迁出但仍有补贴记录的人员清单。

已核销的人默认不再出现；但如果核销之后又新增/补发了补贴（签名变了），
会重新回到清单，并带 reopened=True 提示"核销后又有了新补贴"。
"""

from flask import jsonify
from sqlalchemy import or_
from utils.security import require_auth

from database import get_session, Person
from database.models.pending_correction_handled import PendingCorrectionHandled
from .subsidy_snapshot import build_module_list, collect_modules, sign_module_list


@require_auth
def api_pending_correction():
    session = get_session()
    try:
        handled_map = {
            row.person_id: (row.snapshot or '')
            for row in session.query(PendingCorrectionHandled).all()
        }
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
        agg = collect_modules(session, list(id_cards))

        items = []
        for p in persons:
            card = (p.id_card or '').strip()
            mods = agg.get(card) or {}
            if not mods:
                continue
            module_list = build_module_list(mods)
            snapshot = sign_module_list(module_list)

            handled_snapshot = handled_map.get(p.id)
            # 已核销且补贴记录没变化 -> 继续隐藏
            if handled_snapshot is not None and handled_snapshot == snapshot:
                continue

            item = {
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
                'snapshot': snapshot,
            }
            if handled_snapshot is not None:
                item['reopened'] = True
            items.append(item)

        items.sort(key=lambda x: (-x['module_count'], x['name']))
        return jsonify({'total': len(items), 'items': items})
    finally:
        session.close()
