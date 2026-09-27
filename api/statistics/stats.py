from flask import jsonify

from database import get_person_count
from utils.security import require_auth
from . import bp


@bp.route('/stats')
@require_auth
def api_stats():
    return jsonify({
        'total_persons': get_person_count()
    })
