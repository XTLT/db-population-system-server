from flask import jsonify
from sqlalchemy import distinct

from utils.security import require_auth
from database import get_session, ElderlyAllowance
from . import bp


@bp.route('/elderly_allowance/periods')
@require_auth
def get_elderly_allowance_periods():
    session = get_session()
    try:
        periods = session.query(distinct(ElderlyAllowance.period)).all()
        period_list = sorted(set(p[0] for p in periods if p[0]), reverse=True)
        return jsonify({'periods': period_list})
    finally:
        session.close()
