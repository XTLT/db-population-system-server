from flask import jsonify
from sqlalchemy import func

from database import get_session, Person
from utils.security import require_auth
from . import bp


@bp.route('/statistics/by_village')
@require_auth
def api_statistics_by_village():
    session = get_session()
    try:
        villages = session.query(Person.address, func.count(Person.id)).group_by(
            Person.address
        ).all()
        
        village_stats = []
        for address, count in villages:
            if address:
                village_stats.append({
                    'village': address,
                    'count': count
                })
        
        return jsonify({'villages': village_stats[:50]})
    finally:
        session.close()
