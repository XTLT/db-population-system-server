from flask import request, jsonify

from utils.security import require_auth
from database import get_session, TreatmentPayment
from . import bp


@bp.route('/treatment_payment/years')
@require_auth
def get_treatment_payment_years():
    """获取所有待遇发放年份"""
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403

    session = get_session()
    try:
        from sqlalchemy import distinct
        periods = session.query(distinct(TreatmentPayment.period)).all()
        years = sorted(set(p[0][:4] for p in periods if p[0] and len(p[0]) >= 4), reverse=True)
        return jsonify({'years': years})
    finally:
        session.close()
