from flask import request, jsonify

from utils.security import require_auth
from utils import escape_like, validate_year
from database import get_session, LandSubsidy
from . import bp


@bp.route('/land_subsidy')
@require_auth
def list_land_subsidies():
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403

    year = request.args.get('year', '')
    id_card = request.args.get('id_card', '')
    search = request.args.get('search', '')

    if year:
        valid, msg = validate_year(year)
        if not valid:
            return jsonify({'error': f'年份: {msg}'}), 400

    session = get_session()
    try:
        query = session.query(LandSubsidy)

        if year:
            query = query.filter(LandSubsidy.year == year)
        if id_card:
            safe_id_card = escape_like(id_card)
            query = query.filter(LandSubsidy.id_card.like(f'%{safe_id_card}%', escape='\\'))
        if search:
            safe_search = escape_like(search)
            query = query.filter(LandSubsidy.name.like(f'%{safe_search}%', escape='\\'))

        subsidies = query.order_by(LandSubsidy.year.desc()).limit(500).all()


        return jsonify({
            'subsidies': [{
                'id': s.id,
                'person_id': s.person_id,
                'id_card': s.id_card,
                'name': s.name,
                'year': s.year,
                'certified_area': s.certified_area,
                'subsidy_area': s.subsidy_area,
                'base_standard': s.base_standard,
                'rape_area': s.rape_area,
                'rape_amount': s.rape_amount,
                'total_amount': s.total_amount,
                'phone': s.phone or '',
                'bank_account': s.bank_account or '',
                'bank_name': s.bank_name or '',
                'land_time': s.land_time or '',
                'rape_standard': s.rape_standard or '',
                'import_time': s.import_time or s.created_at
            } for s in subsidies]
        })
    finally:
        session.close()
