from flask import request, jsonify

from utils.security import require_auth
from utils import escape_like
from database import get_session, DibaoPayment
from . import bp


@bp.route('/dibao_payment')
@require_auth
def list_dibao_payments():
    if request.current_user.get('role') not in ['admin', 'user']:
        return jsonify({'error': '权限不足'}), 403

    period = request.args.get('period', '')
    id_card = request.args.get('id_card', '')
    name = request.args.get('name', '')

    session = get_session()
    try:
        query = session.query(DibaoPayment)

        if period:
            query = query.filter(DibaoPayment.period == period)
        if id_card:
            safe_id_card = escape_like(id_card)
            query = query.filter(DibaoPayment.id_card.like(f'%{safe_id_card}%', escape='\\'))
        if name:
            safe_name = escape_like(name)
            query = query.filter(DibaoPayment.name.like(f'%{safe_name}%', escape='\\'))

        records = query.order_by(DibaoPayment.period.desc()).limit(500).all()

        return jsonify({
            'records': [{
                'id': p.id,
                'name': p.name,
                'id_card': p.id_card,
                'town': p.town,
                'village': p.village,
                'period': p.period,
                'payment_status': p.payment_status,
                'personal_code': p.personal_code,
                'bank_account': p.bank_account,
                'amount': p.amount,
                'relation': p.relation,
                'fail_reason': p.fail_reason,
                'import_source': p.import_source,
                'import_time': p.import_time
            } for p in records]
        })
    finally:
        session.close()
