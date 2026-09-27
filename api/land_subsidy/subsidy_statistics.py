from flask import jsonify

from utils.security import require_auth
from database import get_session, LandSubsidy
from . import bp


@bp.route('/land_subsidy/statistics')
@require_auth
def subsidy_statistics():
    session = get_session()
    try:
        total_count = session.query(LandSubsidy).count()
        # subsidy_amount 是字符串，需要在 Python 中计算
        subsidies = session.query(LandSubsidy).all()
        total_amount = 0.0
        for s in subsidies:
            try:
                total_amount += float(s.subsidy_amount) if s.subsidy_amount else 0
            except (ValueError, TypeError):
                pass

        by_year = {}
        for s in subsidies:
            year = s.year or "未知"
            if year not in by_year:
                by_year[year] = {'count': 0, 'amount': 0.0}
            by_year[year]['count'] += 1
            try:
                by_year[year]['amount'] += float(s.subsidy_amount) if s.subsidy_amount else 0
            except (ValueError, TypeError):
                pass

        return jsonify({
            'total_count': total_count,
            'total_amount': total_amount,
            'by_year': [{
                'year': y,
                'count': by_year[y]['count'],
                'amount': by_year[y]['amount']
            } for y in sorted(by_year.keys(), reverse=True)]
        })
    finally:
        session.close()
