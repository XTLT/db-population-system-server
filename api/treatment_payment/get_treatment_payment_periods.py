from flask import jsonify

from utils.security import require_auth
from database import get_session, TreatmentPayment
from . import bp


@bp.route('/treatment_payment/periods')
@require_auth
def get_treatment_payment_periods():
    """获取所有可用的费款所属期（按月）"""
    session = get_session()
    try:
        from sqlalchemy import distinct
        periods = session.query(distinct(TreatmentPayment.period)).all()
        period_list = sorted(set(p[0] for p in periods if p[0]), reverse=True)
        return jsonify({'periods': period_list})
    finally:
        session.close()
