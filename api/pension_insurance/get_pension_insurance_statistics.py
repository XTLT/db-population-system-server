from flask import request, jsonify
from sqlalchemy import distinct

from utils.security import require_auth
from database import get_session, PensionInsurance
from . import bp


@bp.route('/pension_insurance/statistics')
@require_auth
def get_pension_insurance_statistics():
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403

    session = get_session()
    try:
        periods = session.query(distinct(PensionInsurance.period)).all()
        years = sorted(set(p[0][:4] for p in periods if p[0] and len(p[0]) >= 4), reverse=True)

        by_year = []
        total_amount = 0.0
        total_count = 0

        for year in years:
            records = session.query(PensionInsurance).filter(
                PensionInsurance.period.like(f'{year}%')
            ).all()

            count = len(records)
            amount = sum(float(p.amount or 0) for p in records)

            by_year.append({
                'year': year,
                'count': count,
                'amount': amount
            })

            total_count += count
            total_amount += amount

        return jsonify({
            'by_year': by_year,
            'total_amount': total_amount,
            'total_count': total_count
        })
    finally:
        session.close()
