from flask import jsonify
from sqlalchemy import distinct

from utils.security import require_auth
from database import get_session, PensionInsurance
from . import bp


@bp.route('/pension_insurance/periods')
@require_auth
def get_pension_insurance_periods():
    """获取所有可用的费款所属期（按月）"""
    session = get_session()
    try:
        periods = session.query(distinct(PensionInsurance.period)).all()
        period_list = sorted(set(p[0] for p in periods if p[0]), reverse=True)
        return jsonify({'periods': period_list})
    finally:
        session.close()
