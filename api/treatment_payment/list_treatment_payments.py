from flask import request, jsonify

from utils.security import require_auth
from utils import escape_like
from database import get_session, Person, TreatmentPayment
from . import bp


@bp.route('/treatment_payment')
@require_auth
def list_treatment_payments():
    if request.current_user.get('role') not in ['admin', 'user']:
        return jsonify({'error': '权限不足'}), 403

    period = request.args.get('period', '')
    id_card = request.args.get('id_card', '')
    name = request.args.get('name', '')
    subsidy_type = request.args.get('subsidy_type', '')

    session = get_session()
    try:
        query = session.query(TreatmentPayment)

        if period:
            query = query.filter(TreatmentPayment.period == period)
        if id_card:
            safe_id_card = escape_like(id_card)
            query = query.filter(TreatmentPayment.id_card.like(f'%{safe_id_card}%', escape='\\'))
        if name:
            safe_name = escape_like(name)
            query = query.filter(TreatmentPayment.name.like(f'%{safe_name}%', escape='\\'))
        if subsidy_type:
            query = query.filter(TreatmentPayment.subsidy_type == subsidy_type)

        payments = query.order_by(TreatmentPayment.period.desc()).limit(500).all()

        person_map = {p.id_card: p.dis_level for p in session.query(Person).all()}

        return jsonify({
            'payments': [{
                'id': p.id,
                'name': p.name,
                'id_card': p.id_card,
                'dis_level': person_map.get(p.id_card, ''),
                'town': p.town,
                'village': p.village,
                'period': p.period,
                'payment_status': p.payment_status,
                'bank_account': p.bank_account,
                'amount': p.amount,
                'subsidy_type': p.subsidy_type,
                'relation': p.relation,
                'fail_reason': p.fail_reason,
                'import_source': p.import_source,
                'import_time': p.import_time
            } for p in payments]
        })
    finally:
        session.close()
