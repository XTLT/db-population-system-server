"""GET /api/person/<person_id>/subsidies：按人聚合 6 类补贴发放记录。"""

from flask import jsonify
from utils.security import require_auth

from database import get_session
from .._helpers import safe_id_card_query
from .subsidy_modules import SUBSIDY_MODULES, MAX_RECORDS
from .to_amount import to_amount


@require_auth
def api_person_subsidies(person_id):
    """person_id 可以是人员 id 或身份证号，与 /api/person/<person_id> 口径一致。"""
    session = get_session()
    try:
        p, error = safe_id_card_query(session, person_id)
        if error:
            return error

        id_card = (p.id_card or "").strip()
        if not id_card:
            return jsonify({
                'id_card': '',
                'person_name': p.name or '',
                'total_count': 0,
                'truncated': False,
                'by_module': [],
                'records': [],
            })

        records = []
        by_module = []
        for module, label, model, period_attr, amount_attr in SUBSIDY_MODULES:
            rows = (
                session.query(model)
                .filter(getattr(model, "id_card") == id_card)
                .all()
            )
            total = 0.0
            for r in rows:
                period = getattr(r, period_attr, '') or ''
                amount = getattr(r, amount_attr, '') or ''
                total += to_amount(amount)
                records.append({
                    'module': module,
                    'label': label,
                    'period': period,
                    'amount': amount,
                    'payment_status': getattr(r, 'payment_status', '') or '',
                    'fail_reason': getattr(r, 'fail_reason', '') or '',
                    'village': getattr(r, 'village', '') or '',
                    'town': getattr(r, 'town', '') or '',
                    'bank_account': getattr(r, 'bank_account', '') or '',
                })
            by_module.append({
                'module': module,
                'label': label,
                'count': len(rows),
                'total_amount': f"{total:.2f}" if total else '',
            })

        total_records = len(records)
        records.sort(key=lambda x: (x['period'] or ''), reverse=True)

        return jsonify({
            'id_card': id_card,
            'person_name': p.name or '',
            'total_count': total_records,
            'truncated': total_records > MAX_RECORDS,
            'by_module': by_module,
            'records': records[:MAX_RECORDS],
        })
    finally:
        session.close()
