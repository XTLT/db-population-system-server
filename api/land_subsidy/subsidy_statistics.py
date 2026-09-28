from flask import jsonify

from utils.security import require_auth
from database import get_session, LandSubsidy
from . import bp


def _to_float(value):
    """字符串转浮点数，失败返回 0。"""
    try:
        return float(value) if value else 0.0
    except (ValueError, TypeError):
        return 0.0


@bp.route('/land_subsidy/statistics')
@require_auth
def subsidy_statistics():
    session = get_session()
    try:
        total_count = session.query(LandSubsidy).count()
        # 字段多为字符串，需在 Python 中计算
        subsidies = session.query(LandSubsidy).all()
        total_amount = 0.0
        total_certified_area = 0.0
        total_subsidy_area = 0.0
        for s in subsidies:
            total_amount += _to_float(s.subsidy_amount)
            total_certified_area += _to_float(s.certified_area)
            total_subsidy_area += _to_float(s.subsidy_area)

        avg_subsidy_amount = round(total_amount / total_count, 2) if total_count else 0.0

        by_year = {}
        for s in subsidies:
            year = s.year or "未知"
            if year not in by_year:
                by_year[year] = {'count': 0, 'amount': 0.0, 'certified_area': 0.0, 'subsidy_area': 0.0}
            by_year[year]['count'] += 1
            by_year[year]['amount'] += _to_float(s.subsidy_amount)
            by_year[year]['certified_area'] += _to_float(s.certified_area)
            by_year[year]['subsidy_area'] += _to_float(s.subsidy_area)

        return jsonify({
            'total_count': total_count,
            'total_amount': round(total_amount, 2),
            'total_certified_area': round(total_certified_area, 2),
            'total_subsidy_area': round(total_subsidy_area, 2),
            'avg_subsidy_amount': avg_subsidy_amount,
            'by_year': [{
                'year': y,
                'count': by_year[y]['count'],
                'amount': round(by_year[y]['amount'], 2),
                'certified_area': round(by_year[y]['certified_area'], 2),
                'subsidy_area': round(by_year[y]['subsidy_area'], 2)
            } for y in sorted(by_year.keys(), reverse=True)]
        })
    finally:
        session.close()
