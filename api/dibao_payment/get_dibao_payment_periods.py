from flask import jsonify
from sqlalchemy import distinct

from utils.security import require_auth
from database import get_session, DibaoPayment
from . import bp


@bp.route('/dibao_payment/periods')
@require_auth
def get_dibao_payment_periods():
    session = get_session()
    try:
        periods = session.query(distinct(DibaoPayment.period)).all()
        period_list = sorted(set(p[0] for p in periods if p[0]), reverse=True)
        return jsonify({'periods': period_list})
    finally:
        session.close()
