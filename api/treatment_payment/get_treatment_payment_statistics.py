from flask import request, jsonify

from utils.security import require_auth
from database import get_session, TreatmentPayment
from . import bp


@bp.route('/treatment_payment/statistics')
@require_auth
def get_treatment_payment_statistics():
    """获取待遇发放统计信息"""
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403

    session = get_session()
    try:
        from sqlalchemy import distinct
        periods = session.query(distinct(TreatmentPayment.period)).all()
        years = sorted(set(p[0][:4] for p in periods if p[0] and len(p[0]) >= 4), reverse=True)

        by_year = []
        total_amount = 0.0
        total_count = 0

        for year in years:
            payments = session.query(TreatmentPayment).filter(
                TreatmentPayment.period.like(f'{year}%')
            ).all()

            count = len(payments)
            amount = sum(float(p.amount or 0) for p in payments)

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
