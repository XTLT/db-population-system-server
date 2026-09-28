from flask import request, jsonify
from sqlalchemy import distinct

from utils.security import require_auth
from database import get_session, DisabilityCarePayment
from . import bp


@bp.route('/disability_care_payment/years')
@require_auth
def get_disability_care_payment_years():
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403

    session = get_session()
    try:
        periods = session.query(distinct(DisabilityCarePayment.period)).all()
        years = sorted(set(p[0][:4] for p in periods if p[0] and len(p[0]) >= 4), reverse=True)
        return jsonify({'years': years})
    finally:
        session.close()
