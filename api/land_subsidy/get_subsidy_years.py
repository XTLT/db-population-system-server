from flask import jsonify

from utils.security import require_auth
from database import get_session, LandSubsidy
from . import bp


@bp.route('/land_subsidy/years')
@require_auth
def get_subsidy_years():
    session = get_session()
    try:
        years = session.query(LandSubsidy.year).distinct().order_by(LandSubsidy.year.desc()).all()
        return jsonify({
            'years': [y[0] for y in years if y[0]]
        })
    finally:
        session.close()
