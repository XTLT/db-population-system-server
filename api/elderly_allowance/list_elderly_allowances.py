from flask import request, jsonify

from utils.security import require_auth
from utils import escape_like
from database import get_session, Person, ElderlyAllowance
from . import bp


@bp.route('/elderly_allowance')
@require_auth
def list_elderly_allowances():
    if request.current_user.get('role') not in ['admin', 'user']:
        return jsonify({'error': '权限不足'}), 403

    period = request.args.get('period', '')
    id_card = request.args.get('id_card', '')
    name = request.args.get('name', '')

    session = get_session()
    try:
        query = session.query(ElderlyAllowance)

        if period:
            query = query.filter(ElderlyAllowance.period == period)
        if id_card:
            safe_id_card = escape_like(id_card)
            query = query.filter(ElderlyAllowance.id_card.like(f'%{safe_id_card}%', escape='\\'))
        if name:
            safe_name = escape_like(name)
            query = query.filter(ElderlyAllowance.name.like(f'%{safe_name}%', escape='\\'))

        records = query.order_by(ElderlyAllowance.period.desc()).limit(500).all()

        person_map = {p.id_card: p.dis_level for p in session.query(Person).all()}

        return jsonify({
            'records': [{
                'id': p.id,
                'name': p.name,
                'id_card': p.id_card,
                'dis_level': person_map.get(p.id_card, ''),
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
